from common import *
import numpy as np
import torch
from torch import nn

torch.set_num_threads(8)
torch.set_num_interop_threads(1)
torch.set_default_dtype(torch.float64)

def logz3(z):
    e1 = torch.logcumsumexp(z, dim=1)
    e2 = torch.logcumsumexp(z[:, 1:] + e1[:, :-1], dim=1)
    return torch.logsumexp(z[:, 2:] + e2[:, :-1], dim=1)

def supervised_loss(z, target, kind):
    teacher_score = z.gather(1, target).sum(1)
    if kind == 'ce':
        return logz3(z) - teacher_score
    bonus = torch.full_like(z, .1)
    bonus.scatter_(1, target, 0.)
    return (z + bonus).topk(3, dim=1).values.sum(1) - teacher_score

class Transform(nn.Module):
    def __init__(self, p):
        super().__init__()
        self.register_buffer('p', p.clone())
        self.fn = nn.Linear(p.shape[1], p.shape[1], bias=False)
        nn.init.zeros_(self.fn.weight)

    def forward(self):
        return nn.functional.normalize(self.p + self.fn(self.p), dim=1)

def load_fit(ds):
    c = read(O / 'inputs' / ds / 'fit/config.json')
    n, d, h = c['num_queries'], c['dim'], c['hub_count']
    p = np.fromfile(E24 / 'models' / ds / 'gt10_hard/W.f32', np.float32).reshape(h, d).astype(np.float64)
    q = np.fromfile(c['queries_file'], np.float32).reshape(n, d).astype(np.float64)
    td = O / 'inputs' / ds / 'teachers'
    targets = {key:np.fromfile(td / (key + '.i32'), np.int32).reshape(n, 3) for key in ['cost', 'keep', 'baseline']}
    gain = np.fromfile(td / 'headroom.u8', np.uint8).astype(bool)
    return q, p, targets, gain

@torch.no_grad()
def diagnose(q, w, targets, headroom):
    all_overlap = {key:[] for key in targets}
    all_gap = {key:[] for key in ['cost', 'keep']}
    for b in range(0, len(q), 1024):
        z = q[b:b+1024] @ w.T / .05
        predicted = torch.argsort(z, dim=1, descending=True, stable=True)[:, :3]
        for key, target in targets.items():
            t = target[b:b+1024]
            overlap = (predicted[:, :, None] == t[:, None, :]).any(2).sum(1)
            all_overlap[key].append(overlap.numpy())
            if key != 'baseline':
                negatives = z.clone()
                negatives.scatter_(1, t, -torch.inf)
                gap = z.gather(1, t).min(1).values - negatives.max(1).values
                all_gap[key].append(gap.numpy())
    result = {}
    for key in targets:
        overlap = np.concatenate(all_overlap[key])
        groups = {}
        for group, mask in [('all', np.ones(len(q), bool)), ('headroom', headroom), ('no_headroom', ~headroom)]:
            values = overlap[mask]
            groups[group] = dict(queries=int(mask.sum()), entry_overlap=float(values.mean()/3), set_match=float((values==3).mean()), missing_entries=int((3-values).sum()))
            if key != 'baseline':
                gap = np.concatenate(all_gap[key])[mask]
                groups[group].update(mean_margin=float(gap.mean()), margin_satisfied=float((gap >= .1 - 1e-12).mean()))
        result[key] = groups
    return result

def fit(ds, cell, q_np, p_np, targets_np, gain):
    dest = O / 'models' / ds / cell
    assert not dest.exists()
    dest.mkdir(parents=True)
    teacher, kind = cell.split('_')
    torch.manual_seed(20260911)
    p = torch.from_numpy(p_np)
    q = nn.functional.normalize(torch.from_numpy(q_np), dim=1)
    targets = {k:torch.from_numpy(t.astype(np.int64)) for k,t in targets_np.items()}
    target = targets[teacher]
    model = Transform(p)
    optimizer = torch.optim.Adam(model.parameters(), lr=.003)
    start = time.time()
    curve, diagnostics = [], []
    n = len(q)

    def loss_grad():
        exported = model()
        w = exported.detach().requires_grad_(True)
        data_sum = 0.
        for b in range(0, n, 1024):
            z = q[b:b+1024] @ w.T / .05
            loss = supervised_loss(z, target[b:b+1024], kind).sum()/n
            assert torch.isfinite(loss)
            loss.backward()
            data_sum += loss.item()
        drift = (w-p).square().sum(1).mean()
        (100*drift).backward()
        exported.backward(w.grad)
        gn = sum(v.grad.square().sum().item() for v in model.parameters())**.5
        assert np.isfinite(gn)
        return dict(data_loss=data_sum, drift=drift.item(), objective=data_sum+100*drift.item(), gradient_norm=gn)

    for epoch in range(81):
        optimizer.zero_grad()
        rec = loss_grad()
        rec.update(epoch=epoch, seconds=time.time()-start)
        curve.append(rec)
        if epoch % 10 == 0:
            diagnostics.append(dict(epoch=epoch, metrics=diagnose(q, model(), targets, gain)))
            dump(dest / 'training_curve.json', curve)
            dump(dest / 'alignment_curve.json', diagnostics)
            print(ds, cell, rec, flush=True)
        if epoch < 80:
            optimizer.step()
    wall = time.time()-start
    export_start = time.time()
    w = model().detach().numpy().astype(np.float32)
    assert np.isfinite(w).all()
    w.tofile(dest / 'W.f32')
    torch.save(model.state_dict(), dest / 'model.pt')
    report = dict(status='TRAINED_FIT_ONLY', dataset=ds, cell=cell, teacher=teacher,
                  loss=kind, lambda_anchor=100, temperature=.05, margin=.1,
                  seed=20260911, epochs=80, parameter_count=sum(v.numel() for v in model.parameters()),
                  first=curve[0], last=curve[-1], objective_decreased=curve[-1]['objective']<curve[0]['objective'],
                  training_seconds=wall, export_seconds=time.time()-export_start,
                  W=identity(dest / 'W.f32'), cal_used=False, audit_used=False, validation_used=False)
    if cell == 'cost_ce':
        old = E28 / 'models' / ds / 'linear_r100/W.f32'
        report['E28_recovery'] = dict(bit_equal=sha(old)==sha(dest / 'W.f32'), original=identity(old))
        assert report['E28_recovery']['bit_equal'], 'E28 CE recovery failed'
    dump(dest / 'model.json', report)
    return report

if __name__ == '__main__':
    assert read(O / 'reviews/teacher_verification.json')['status'] == 'PASS'
    assert read(O / 'reviews/objective_tests.json')['status'] == 'PASS'
    files = [O / 'protocol.md'] + [O / 'src' / s for s in ['common.py','train.py','test_objective.py','prepare.py']]
    files += [p for p in (O/'inputs').glob('*/teachers/*') if p.is_file()]
    freeze(O / 'reviews/frozen_before_training.json', files)
    records = []
    for ds in DS:
        data = load_fit(ds)
        for cell in CELLS:
            check_freeze(O / 'reviews/frozen_before_training.json')
            records.append(fit(ds, cell, *data))
            dump(O / 'models/training_runs.json', records)
    freeze(O / 'models/frozen_before_development.json', files + [p for p in (O / 'models').glob('*/*/*') if p.is_file()])
    dump(O / 'state.json', dict(status='TRAINING_COMPLETE_VERIFICATION_PENDING', training_runs=8, real_search_calls=0, heldout_access=False))
