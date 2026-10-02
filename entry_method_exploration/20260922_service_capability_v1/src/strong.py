from common import *
from features import pair_matrix
from models import policy_value
import copy
import pickle
import sys
import torch
from sklearn.ensemble import HistGradientBoostingRegressor

sys.path.insert(0, str(RUN / 'vendor'))
from tabm import TabM

def train_gbdt(rep, roles, hubs, output):
    start = time.monotonic()
    fit, monitor, outer = [np.asarray(roles[r]) for r in ['fit', 'monitor', 'outer']]
    x = pair_matrix(rep, fit)
    y = rep['utility'][fit, 1:].reshape(-1, 2)
    output.mkdir(parents=True)
    predictions = {r: [] for r in ['fit', 'monitor', 'outer']}
    for k in range(2):
        model = HistGradientBoostingRegressor(max_iter=200, max_leaf_nodes=31,
            learning_rate=0.05, l2_regularization=1, min_samples_leaf=100,
            early_stopping=False, random_state=20260922)
        model.fit(x, y[:, k])
        with (output / f'K{k}.pickle').open('xb') as f:
            pickle.dump(model, f)
        predictions['fit'].append(model.predict(x).reshape(len(fit), -1))
        for role, rows in [('monitor', monitor), ('outer', outer)]:
            predictions[role].append(np.concatenate([model.predict(pair_matrix(rep, r)).reshape(len(r), -1)
                for r in np.array_split(rows, max(1, (len(rows) + 31) // 32))]))
        print('GBDT_HEAD', k, 'seconds', time.monotonic() - start, flush=True)
    predictions = {r: np.stack(p, -1).astype('f4') for r, p in predictions.items()}
    dump(output / 'training.json', dict(seconds=time.monotonic() - start,
        fit_utility=policy_value(predictions['fit'], rep['utility'][fit], hubs),
        monitor_utility=policy_value(predictions['monitor'], rep['utility'][monitor], hubs),
        fit_mse=float(np.mean((predictions['fit'] - rep['utility'][fit, 1:]) ** 2)),
        monitor_mse=float(np.mean((predictions['monitor'] - rep['utility'][monitor, 1:]) ** 2)),
        iterations=200, pair_validation_split=False))
    return predictions['outer']

def pair_batch(tensors, rows, entries):
    return torch.cat([tensors['q'][rows], tensors['bank'][entries], tensors['cosine'][rows, entries]], -1)

@torch.no_grad()
def tabm_predict(model, tensors, rows):
    model.eval()
    h = len(tensors['bank'])
    output = []
    for rr in np.array_split(np.asarray(rows), max(1, (len(rows) + 1) // 2)):
        qidx, eidx = np.repeat(rr, h), np.tile(np.arange(h), len(rr))
        output.append(model(pair_batch(tensors, qidx, eidx)).mean(1).numpy().reshape(len(rr), h, 2))
    return np.concatenate(output)

def train_tabm(rep, roles, hubs, output):
    start = time.monotonic()
    torch.manual_seed(20260922)
    model = TabM.make(n_num_features=rep['q'].shape[1] + rep['bank'].shape[1] + 2,
                     d_out=2, k=16, n_blocks=2, d_block=128, dropout=0.1)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.002, weight_decay=0.0003)
    tensors = {k: torch.from_numpy(rep[k]) for k in ['q', 'bank', 'cosine']}
    target = torch.from_numpy(rep['utility'][:, 1:])
    fit, monitor = np.asarray(roles['fit']), np.asarray(roles['monitor'])
    h = len(rep['bank'])
    rng = np.random.default_rng(20260922)
    history, best, state, stale = [], -float('inf'), None, 0
    for epoch in range(1, 17):
        model.train()
        losses = []
        order = rng.permutation(len(fit) * h)
        for batch in np.array_split(order, (len(order) + 2047) // 2048):
            rows, entries = fit[batch // h], batch % h
            pred = model(pair_batch(tensors, rows, entries))
            loss = (pred - target[rows, entries, None, :]).square().mean()
            assert torch.isfinite(loss)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach()))
        pm = tabm_predict(model, tensors, monitor)
        value = policy_value(pm, rep['utility'][monitor], hubs)
        record = dict(epoch=epoch, loss=float(np.mean(losses)), monitor_utility=value,
            monitor_mse=float(np.mean((pm - rep['utility'][monitor, 1:]) ** 2)))
        history.append(record)
        print('CHECKPOINT TabM', record, 'seconds', time.monotonic() - start, flush=True)
        if value > best:
            best, state, stale = value, copy.deepcopy(model.state_dict()), 0
        else:
            stale += 1
        if stale >= 3:
            break
    model.load_state_dict(state)
    output.mkdir(parents=True)
    torch.save(model.state_dict(), output / 'model.pt')
    pf = tabm_predict(model, tensors, fit)
    dump(output / 'training.json', dict(history=history, best_monitor_utility=best,
        fit_utility=policy_value(pf, rep['utility'][fit], hubs),
        fit_mse=float(np.mean((pf - rep['utility'][fit, 1:]) ** 2)),
        seconds=time.monotonic() - start, parameters=sum(p.numel() for p in model.parameters()),
        tabm_version='0.0.3', rtdl_num_embeddings_version='0.0.12', numerical_embeddings=False))
    return tabm_predict(model, tensors, roles['outer'])
