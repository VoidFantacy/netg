"""Read-only E119 cache diagnostics with an independently frozen analysis contract."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
import ast
import csv
import hashlib
import json
import shutil
import time
from pathlib import Path
import numpy as np
from scipy.optimize import brentq
from scipy.special import expit
from scipy.stats import rankdata, spearmanr

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]
OLD = ROOT / 'entry_method_exploration/20260922_service_capability_v1'
E118 = ROOT / 'entry_method_exploration/20260921_comparison_direction_pilot_v1'
CURVES = ROOT / 'entry_method_exploration/20260916_optimized_five_dataset_r1_r100_v1/results/metrics.csv'
METHODS = ['GeomMSE', 'CapMSE', 'GeomRank', 'CapRank', 'GBDT', 'TabM']

def read(path):
    return json.loads(path.read_text())

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')

def identity(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 << 20), b''):
            h.update(chunk)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=h.hexdigest())

def freeze():
    assert not (RUN / 'reviews/before.json').exists(), 'Refuse to overwrite this version'
    config = read(OLD / 'config.locked.json')
    upstream = read(E118 / 'config.locked.json')
    paths = [OLD / 'config.locked.json', OLD / 'reviews/final_identity.json',
             OLD / 'src/models.py', OLD / 'analysis/results.json', CURVES,
             E118 / 'config.locked.json']
    for ds in config['datasets']:
        paths.append(Path(upstream['datasets'][ds]['anchor']['ids']))
        for method in METHODS:
            paths.append(OLD / 'analysis' / ds / f'{method}.npz')
        for fold in range(4):
            p = OLD / 'results' / ds / f'fold_{fold}'
            paths.append(p / 'labels.npz')
            paths.extend(p / f'{method}.npy' for method in METHODS)
    for name in ['summary.md', 'spec.md', 's-target.md', 's-experiment.md', 'experiment_history/README.md']:
        dest = RUN / 'source_before' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, dest)
    dump(RUN / 'reviews/before.json', dict(inputs=[identity(p) for p in paths],
        frozen_analysis=[identity(RUN / p) for p in ['protocol.md', 'theory.md', 'src/analyze.py']],
        time_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())))

def synthetic():
    import torch
    from torch.nn import functional as F
    torch.set_num_threads(1)
    tree = ast.parse((OLD / 'src/models.py').read_text())
    fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'objective')
    scope = dict(torch=torch, F=F)
    exec(compile(ast.Module(body=[fn], type_ignores=[]), 'E119_objective_only', 'exec'), scope)
    derivative = lambda s: (expit(s / .1) - .1) / .1 + .2 * (s - .091)
    root = brentq(derivative, -1, 1, xtol=1e-14)
    checks = []
    for s in [0., root, .091]:
        scalar = .1*np.logaddexp(0, -s/.1) + .9*np.logaddexp(0, s/.1)
        scalar += .1*(.1*(s-1)**2 + .9*(s+.01)**2)
        value = torch.tensor(s, dtype=torch.float64, requires_grad=True)
        pred = value.expand(10, 1, 2)
        truth = torch.tensor([1.] + [-.01]*9, dtype=torch.float64)[:, None, None].expand(10, 1, 2)
        loss = scope['objective'](pred, truth, rank=True)
        loss.backward()
        assert abs(loss.item()-scalar) < 1e-12
        assert abs(value.grad.item()-derivative(s)) < 1e-12
        checks.append(dict(score=s, original_loss=loss.item(), scalar_loss=float(scalar),
                           original_derivative=value.grad.item(), derivative=float(derivative(s))))
    assert root < 0 and abs(derivative(root)) < 1e-10
    return dict(expected_utility=.091, optimizer=root, wrong_default=True, checks=checks)

def brackets():
    with CURVES.open() as f:
        rows = list(csv.DictReader(f))
    result = []
    for ds in read(OLD / 'config.locked.json')['datasets']:
        method = 'GT10-soft-t1' if ds.startswith('webvid') else 'GT10-hard'
        for K in [1, 100]:
            points = sorted([r for r in rows if r['dataset'] == ds and int(r['K']) == K and r['method'] == method], key=lambda r:int(r['L']))
            hi = next(i for i, r in enumerate(points) if float(r['recall']) >= .9)
            assert hi > 0
            low, high = points[hi-1:hi+1]
            slope = (float(high['recall'])-float(low['recall'])) / np.log(float(low['qps_from_mean_wall'])/float(high['qps_from_mean_wall']))
            result.append(dict(dataset=ds, K=K, method=method,
                recall_L128=float(next(r['recall'] for r in points if int(r['L']) == 128)),
                low={k:float(low[k]) for k in ['L','recall','qps_from_mean_wall']},
                high={k:float(high[k]) for k in ['L','recall','qps_from_mean_wall']}, slope=float(slope)))
    return result

def auc(score, positive):
    npos = int(positive.sum())
    nneg = len(score)-npos
    if not npos or not nneg:
        return None
    return float((rankdata(score)[positive].sum()-npos*(npos+1)/2)/(npos*nneg))

def top_statistics(u, bins):
    top = bins == 4
    high = (u*top).sum(0)/top.sum(0)
    rest = (u*~top).sum(0)/(~top).sum(0)
    return np.array([high.mean(), (high-rest).mean()])

def bootstrap(u, bins, folds):
    rng = np.random.default_rng(20260922)
    groups = [np.flatnonzero(folds == f) for f in range(4)]
    samples = []
    for _ in range(100):
        ids = np.concatenate([g[rng.integers(0, len(g), (50, len(g)))] for g in groups], axis=1)
        values, top = u[ids], bins[ids] == 4
        high = (values*top).sum(1)/top.sum(1)
        low = (values*~top).sum(1)/(~top).sum(1)
        samples.append(np.stack([high.mean(1), (high-low).mean(1)], axis=1))
    return np.quantile(np.concatenate(samples), [.025, .975], axis=0).T.tolist()

def analyze(ds, name):
    anchor = read(E118 / 'config.locked.json')['datasets'][ds]['anchor']
    hubs = np.fromfile(anchor['ids'], '<i4')
    hub_order = np.argsort(hubs, kind='stable')
    expected = np.load(OLD / 'analysis' / ds / f'{name}.npz')
    n = len(expected['source_rows'])
    keys = ['score', 'forced_u', 'forced_dr', 'forced_dt', 'percentile', 'above_row_mean',
            'oracle_regret', 'all_bias', 'all_mse', 'policy_pred', 'policy_u']
    out = {key:np.empty((n,2), 'f8') for key in keys}
    out['bins'] = np.empty((n,2), 'i4')
    out['forced_actions'] = np.empty((n,2), 'i4')
    for fold in range(4):
        p = OLD / 'results' / ds / f'fold_{fold}'
        labels = np.load(p / 'labels.npz')
        rows = labels['rows']
        pred = np.load(p / f'{name}.npy').astype('f8')
        truth = labels['utility'].astype('f8')
        assert np.isfinite(pred).all() and np.isfinite(truth).all()
        assert np.array_equal(labels['source_rows'], expected['source_rows'][rows])
        assert np.all(expected['folds'][rows] == fold)
        for k in range(2):
            best = hub_order[pred[:,hub_order,k].argmax(1)]+1
            scores = pred[np.arange(len(rows)),best-1,k]
            action = np.where(scores > 0, best, 0)
            assert np.array_equal(action, expected['actions'][rows,k])
            for key in ['utility','recall_delta','time_delta']:
                assert np.allclose(labels[key][np.arange(len(rows)),action,k], expected[key][rows,k], atol=1e-7, rtol=0)
            u = truth[np.arange(len(rows)),best,k]
            out['score'][rows,k] = scores
            out['forced_actions'][rows,k] = best
            out['forced_u'][rows,k] = u
            out['forced_dr'][rows,k] = labels['recall_delta'][np.arange(len(rows)),best,k]
            out['forced_dt'][rows,k] = labels['time_delta'][np.arange(len(rows)),best,k]
            v = truth[:,1:,k]
            out['percentile'][rows,k] = ((v < u[:,None]).sum(1)+.5*(v == u[:,None]).sum(1))/len(hubs)
            out['above_row_mean'][rows,k] = u-v.mean(1)
            out['oracle_regret'][rows,k] = truth[:,:,k].max(1)-u
            out['all_bias'][rows,k] = (pred[:,:,k]-v).mean(1)
            out['all_mse'][rows,k] = ((pred[:,:,k]-v)**2).mean(1)
            out['policy_pred'][rows,k] = np.maximum(scores, 0)
            out['policy_u'][rows,k] = truth[np.arange(len(rows)),action,k]
            order = np.lexsort((labels['source_rows'], scores))
            for b, members in enumerate(np.array_split(order, 5)):
                out['bins'][rows[members],k] = b
    u, bins, folds = out['forced_u'], out['bins'], expected['folds']
    stats = top_statistics(u, bins)
    fold_stats = [top_statistics(u[folds == f], bins[folds == f]).tolist() for f in range(4)]
    ci = bootstrap(u, bins, folds)
    per_k = {}
    for k, K in enumerate([1,100]):
        per_k[str(K)] = dict(spearman=float(spearmanr(out['score'][:,k], u[:,k]).statistic),
            positive_utility_auc=auc(out['score'][:,k], u[:,k] > 0),
            bins=[dict(bin=b, n=int((bins[:,k]==b).sum()),
                mean_score=float(out['score'][bins[:,k]==b,k].mean()),
                mean_u=float(u[bins[:,k]==b,k].mean()),
                recall_delta_pp=float(100*out['forced_dr'][bins[:,k]==b,k].mean())) for b in range(5)])
    gate = dict(top_mean_positive=bool(stats[0]>0), contrast_lower_positive=bool(ci[1][0]>0),
        three_positive_fold_contrasts=sum(s[1]>0 for s in fold_stats)>=3,
        each_K_top_recall_noninferior=all(per_k[str(K)]['bins'][4]['recall_delta_pp'] >= -.1 for K in [1,100]))
    result = dict(predicted_selected_u=float(out['policy_pred'].mean()), actual_selected_u=float(out['policy_u'].mean()),
        selected_optimism=float((out['policy_pred']-out['policy_u']).mean()),
        all_pair_bias=float(out['all_bias'].mean()), all_pair_rmse=float(np.sqrt(out['all_mse'].mean())),
        forced_actual_percentile=float(out['percentile'].mean()), forced_above_row_mean=float(out['above_row_mean'].mean()),
        top_mean_u=float(stats[0]), top_CI95=ci[0], top_minus_rest=float(stats[1]), contrast_CI95=ci[1],
        fold_top_and_contrast=fold_stats, K=per_k, descriptive_gate=gate, passes=all(gate.values()))
    dest = RUN / 'analysis' / ds
    dest.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(dest / f'{name}.npz', source_rows=expected['source_rows'], folds=folds, **out)
    return result

if __name__ == '__main__':
    start = time.monotonic()
    freeze()
    results = {}
    tests = synthetic()
    curve_points = brackets()
    for ds in read(OLD / 'config.locked.json')['datasets']:
        results[ds] = {}
        for name in METHODS:
            results[ds][name] = analyze(ds, name)
            r = results[ds][name]
            print(ds, name, 'top_U', r['top_mean_u'], 'contrast', r['top_minus_rest'], 'pass', r['passes'], flush=True)
    eligible = all(results[ds]['GBDT']['passes'] for ds in results)
    dump(RUN / 'analysis/results.json', dict(results=results, counterexample=tests, brackets=curve_points,
        calibration_eligible=eligible, nominated='GBDT', seconds=time.monotonic()-start,
        scope='retrospective exposed-development L128 search-only; not QPS or blind testing'))
    before = read(RUN / 'reviews/before.json')
    assert all(identity(Path(item['path'])) == item for item in before['inputs'])
    dump(RUN / 'state.json', dict(status='CALIBRATION_ELIGIBLE' if eligible else 'STOP_CALIBRATION_ONLY_REUSE',
        completed=False, pending=['independent_audit','report','documentation'] + (['minimal_calibration'] if eligible else []),
        new_search_calls=0, new_training=0, default_changed=False))
