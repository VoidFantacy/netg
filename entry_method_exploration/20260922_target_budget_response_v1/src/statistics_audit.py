"""Reconstruct information summaries and paired intervals from saved payoffs."""
from common import RUN, read, dump
import time
import numpy as np

start = time.monotonic()
info = read(RUN/'analysis/information.json')
checked = 0
for ds, result in info['results'].items():
    data = np.load(RUN/'analysis'/f'{ds}.information.npz')
    names = ['TargetKNN', 'LowKNN', 'TargetFixed', 'ShuffleKNN']
    values = []
    for name in names:
        delta = data[name+'_delta']
        mean = 100*delta.mean(axis=1)
        values.append(mean)
        record = result['methods'][name]
        assert np.isclose(mean.mean(), record['mean_gain_pp'], atol=1e-12)
        assert np.allclose(100*delta.mean(axis=0), record['K_mean_gain_pp'], atol=1e-12)
        assert np.array_equal((data[name+'_actions'] != 0).sum(axis=0), record['switches'])
        for fold in range(4):
            assert np.isclose(mean[data['folds'] == fold].mean(), record['fold_gain_pp'][fold], atol=1e-12)
    matrix = np.stack(values+[values[0]-v for v in values[1:]], axis=1)
    blocks = [np.flatnonzero(data['folds'] == fold) for fold in range(4)]
    rng = np.random.default_rng(20260922)
    draws = []
    for batch in range(50):
        sample = np.concatenate([block[rng.integers(1024, size=(100,1024))] for block in blocks], axis=1)
        draws.append(matrix[sample].mean(axis=1))
    limits = np.quantile(np.concatenate(draws), [.025,.975], axis=0)
    for j, name in enumerate(names):
        assert np.allclose(limits[:,j], result['methods'][name]['CI95_pp'], atol=1e-10)
        checked += 1
    for j, name in enumerate(names[1:], start=4):
        assert np.isclose(matrix[:,j].mean(), result['contrasts'][name]['gain_pp'], atol=1e-12)
        assert np.allclose(limits[:,j], result['contrasts'][name]['CI95_pp'], atol=1e-10)
        checked += 1
dump(RUN/'reviews/statistics_audit.json', dict(status='PASS', intervals=checked,
    paired_K=True, fold_stratified=True, bootstrap_draws=5000,
    seconds=time.monotonic()-start, independent_summary_implementation=True))
print('PASS', checked, flush=True)
