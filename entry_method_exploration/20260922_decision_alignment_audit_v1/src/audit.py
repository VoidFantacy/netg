"""Independent cache reconstruction; no imports from the analysis implementation."""
import os
for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[name] = '1'
import hashlib
import csv
import json
import math
import time
from pathlib import Path
import numpy as np

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]
OLD = ROOT / 'entry_method_exploration/20260922_service_capability_v1'
E118 = ROOT / 'entry_method_exploration/20260921_comparison_direction_pilot_v1'

def read(path):
    return json.loads(path.read_text())

def independent_choice(scores, ids):
    maxima = np.max(scores, axis=1)
    chosen_id = np.min(np.where(scores == maxima[:,None], ids[None,:], np.iinfo(np.int64).max), axis=1)
    index = {int(value):i+1 for i, value in enumerate(ids)}
    forced = np.array([index[int(value)] for value in chosen_id])
    return forced, np.where(maxima > 0, forced, 0)

start = time.monotonic()
report = read(RUN / 'analysis/results.json')
original = read(OLD / 'analysis/results.json')['results']
upstream = read(E118 / 'config.locked.json')['datasets']
checked_actions = 0
checked_bins = 0
gates = {}
for ds, methods in report['results'].items():
    hubs = np.fromfile(upstream[ds]['anchor']['ids'], '<i4').astype('i8')
    gates[ds] = {}
    for method, summary in methods.items():
        saved = np.load(RUN / 'analysis' / ds / f'{method}.npz')
        previous = np.load(OLD / 'analysis' / ds / f'{method}.npz')
        assert abs(summary['actual_selected_u'] - original[ds][method]['mean_utility']) < 1e-10
        assert np.allclose(saved['forced_u'], saved['forced_dr']-.1*saved['forced_dt'], atol=1e-7, rtol=0)
        for fold in range(4):
            path = OLD / 'results' / ds / f'fold_{fold}'
            labels = np.load(path / 'labels.npz')
            scores = np.load(path / f'{method}.npy')
            rows = labels['rows']
            for k, K in enumerate([1,100]):
                forced, action = independent_choice(scores[:,:,k], hubs)
                assert np.array_equal(forced, saved['forced_actions'][rows,k])
                assert np.array_equal(action, previous['actions'][rows,k])
                assert np.array_equal(saved['forced_u'][rows,k], labels['utility'][np.arange(len(rows)),forced,k])
                ordered = sorted(range(len(rows)), key=lambda i:(float(scores[i,forced[i]-1,k]), int(labels['source_rows'][i])))
                lengths = [len(rows)//5+(b < len(rows)%5) for b in range(5)]
                start_index = 0
                for b, length in enumerate(lengths):
                    members = np.array(ordered[start_index:start_index+length])
                    assert np.all(saved['bins'][rows[members],k] == b)
                    start_index += length
                    checked_bins += 1
                checked_actions += len(rows)
        top = []
        rest = []
        recall = []
        for k in range(2):
            means = np.bincount(saved['bins'][:,k], weights=saved['forced_u'][:,k]) / np.bincount(saved['bins'][:,k])
            top.append(float(means[4]))
            rest.append(float(saved['forced_u'][saved['bins'][:,k] < 4,k].mean()))
            recall.append(float(saved['forced_dr'][saved['bins'][:,k] == 4,k].mean()))
            for b, mean in enumerate(means):
                assert abs(mean-summary['K'][str([1,100][k])]['bins'][b]['mean_u']) < 1e-12
        assert abs(np.mean(top)-summary['top_mean_u']) < 1e-12
        assert abs(np.mean(top)-np.mean(rest)-summary['top_minus_rest']) < 1e-12
        fold_contrasts = []
        for fold in range(4):
            u = saved['forced_u'][saved['folds'] == fold]
            bins = saved['bins'][saved['folds'] == fold]
            fold_contrasts.append(float(np.mean([u[bins[:,k] == 4,k].mean()-u[bins[:,k] != 4,k].mean() for k in range(2)])))
        gate = np.mean(top)>0 and summary['contrast_CI95'][0]>0 and sum(x>0 for x in fold_contrasts)>=3 and min(recall)>=-.001
        assert bool(gate) == summary['passes']
        gates[ds][method] = bool(gate)
assert report['calibration_eligible'] == all(gates[ds]['GBDT'] for ds in gates)

curve_path = ROOT / 'entry_method_exploration/20260916_optimized_five_dataset_r1_r100_v1/results/metrics.csv'
with curve_path.open() as handle:
    curves = list(csv.DictReader(handle))
for bracket in report['brackets']:
    points = {int(row['L']):row for row in curves if row['dataset'] == bracket['dataset'] and
              row['method'] == bracket['method'] and int(row['K']) == bracket['K']}
    lo, hi = [points[int(bracket[key]['L'])] for key in ['low','high']]
    assert float(lo['recall']) < .90 <= float(hi['recall'])
    assert not any(int(lo['L']) < L < int(hi['L']) for L in points)
    low_time = sum(float(lo[f'wall_round{i}']) for i in [1,2,3])/3/int(lo['queries'])
    high_time = sum(float(hi[f'wall_round{i}']) for i in [1,2,3])/3/int(hi['queries'])
    slope = (float(hi['recall'])-float(lo['recall'])) / math.log(high_time/low_time)
    assert abs(slope-bracket['slope']) < 1e-12

rng = np.random.default_rng(20260922)
for actions in [1,2,10,821]:
    means = np.column_stack([np.zeros(100), rng.normal(size=(100,actions))])
    scores = means + np.column_stack([np.zeros(100), rng.normal(size=(100,actions))])
    regret = means.max(1)-means[np.arange(100), scores.argmax(1)]
    error = scores-means
    assert np.all(regret <= 2*np.abs(error).max(1)+1e-12)
    assert np.all(regret <= 2*np.sqrt(actions*(error[:,1:]**2).mean(1))+1e-12)

forced, policy = independent_choice(np.array([[1.,1.,0.],[0.,0.,0.],[-1.,-2.,-1.]]), np.array([90,3,8]))
assert forced.tolist() == [2,2,3] and policy.tolist() == [2,0,0]
for record in read(RUN / 'reviews/before.json')['inputs'] + read(RUN / 'reviews/before.json')['frozen_analysis']:
    path = Path(record['path'])
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda:handle.read(8<<20), b''):
            h.update(chunk)
    assert h.hexdigest() == record['sha256'] and path.stat().st_size == record['bytes'], str(path)
result = dict(status='PASS', independent_implementation=True, independent_person=False,
    action_K_pairs=checked_actions, fold_K_bins=checked_bins, synthetic_tie_default_tests=3,
    curve_brackets_and_wall_slope_checks=4, synthetic_regret_bound_checks=400,
    gate_reconstructed=gates, input_and_frozen_analysis_identity='PASS',
    bootstrap_scope='Intervals produced by frozen analysis; audit verifies partitions and estimands, not independent statistical validity',
    seconds=time.monotonic()-start)
(RUN / 'reviews/independent_audit.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
