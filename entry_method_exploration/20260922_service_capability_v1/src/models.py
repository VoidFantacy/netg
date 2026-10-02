from common import *
import torch
from torch import nn
from torch.nn import functional as F

torch.set_num_threads(8)
torch.set_num_interop_threads(1)

class SharedInteraction(nn.Module):
    def __init__(self, dimension, bank_dimension, capability=True):
        super().__init__()
        self.query = nn.Linear(dimension, 32)
        self.entry = nn.Linear(bank_dimension, 32)
        self.output = nn.Linear(32, 2, bias=False)
        self.cosine = nn.Linear(2, 2, bias=False)
        self.capability = capability
        for mod in [self.query, self.entry]:
            nn.init.normal_(mod.weight, std=0.02)
            nn.init.zeros_(mod.bias)
        nn.init.zeros_(self.output.weight)
        nn.init.zeros_(self.cosine.weight)

    def forward(self, q, bank, cosine, prior):
        if not self.capability:
            bank = torch.cat([bank[:, :-64], torch.zeros_like(bank[:, -64:])], dim=1)
        u = self.query(q)[:, None, :]
        v = self.entry(bank)[None, :, :]
        z = F.relu(u + v + u * v)
        return self.output(z) + self.cosine(cosine) + prior[None, :, :]

def objective(pred, target, rank=False):
    mse = (pred - target).square().mean()
    if not rank:
        return mse
    zero = torch.zeros_like(pred[:, :1])
    score = torch.cat([zero, pred], 1)
    truth = torch.cat([zero, target], 1)
    best = truth.argmax(1, keepdim=True)
    gap = truth.gather(1, best) - truth
    losses = gap * F.softplus(-(score.gather(1, best) - score) / 0.1)
    normalized = losses.sum(1) / gap.sum(1).clamp_min(1e-12)
    return normalized.mean() + 0.1 * mse

def torch_inputs(rep):
    return {k: torch.from_numpy(rep[k]) for k in ['q', 'bank', 'cosine', 'prior']}

@torch.no_grad()
def predict(model, inputs, rows, batch=64):
    model.eval()
    return np.concatenate([model(inputs['q'][r], inputs['bank'], inputs['cosine'][r], inputs['prior']).numpy()
                           for r in np.array_split(np.asarray(rows), max(1, (len(rows) + batch - 1) // batch))])

def policy_value(pred, utility, hubs):
    return float(np.mean([selected(utility[:, :, k], actions(pred[:, :, k], hubs)).mean() for k in range(2)]))

def train_primary(rep, roles, name, hubs, output):
    import copy
    start = time.monotonic()
    torch.manual_seed(20260922)
    model = SharedInteraction(rep['q'].shape[1], rep['bank'].shape[1], name.startswith('Cap'))
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.002, weight_decay=0.0003)
    tensors = torch_inputs(rep)
    target = torch.from_numpy(rep['utility'][:, 1:])
    fit, monitor = np.asarray(roles['fit']), np.asarray(roles['monitor'])
    history, best, state, stale = [], -float('inf'), None, 0
    rng = np.random.default_rng(20260922)
    for epoch in range(1, 65):
        model.train()
        losses = []
        for rows in np.array_split(rng.permutation(fit), (len(fit) + 63) // 64):
            pred = model(tensors['q'][rows], tensors['bank'], tensors['cosine'][rows], tensors['prior'])
            loss = objective(pred, target[rows], name.endswith('Rank'))
            assert torch.isfinite(loss)
            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 10)
            optimizer.step()
            losses.append(float(loss.detach()))
        if epoch % 4 == 0:
            pm = predict(model, tensors, monitor)
            pf = predict(model, tensors, fit)
            value = policy_value(pm, rep['utility'][monitor], hubs)
            record = dict(epoch=epoch, loss=float(np.mean(losses)), monitor_utility=value,
                          fit_utility=policy_value(pf, rep['utility'][fit], hubs),
                          fit_mse=float(np.mean((pf - rep['utility'][fit, 1:]) ** 2)),
                          monitor_mse=float(np.mean((pm - rep['utility'][monitor, 1:]) ** 2)))
            history.append(record)
            if value > best:
                best, state, stale = value, copy.deepcopy(model.state_dict()), 0
            else:
                stale += 1
            print('CHECKPOINT', name, record, flush=True)
            if stale >= 4:
                break
    model.load_state_dict(state)
    output.mkdir(parents=True)
    torch.save(model.state_dict(), output / 'model.pt')
    dump(output / 'training.json', dict(history=history, best_monitor_utility=best, seconds=time.monotonic() - start,
         parameter_count=sum(p.numel() for p in model.parameters()), gradient_clip_norm=10))
    return predict(model, tensors, roles['outer'])
