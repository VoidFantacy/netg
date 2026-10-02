"""Complete OOF accounting; never changes a trained model or a selection rule."""
from common import *
import csv

METHODS = ['GT10', 'BestFixed', 'ClusterMean', 'E118Additive', 'GeomMSE', 'CapMSE', 'GeomRank', 'CapRank', 'GBDT', 'TabM']

def intervals(values, seed=20260922):
    values = np.asarray(values, dtype='f8')
    rng = np.random.default_rng(seed)
    boot = np.concatenate([values[rng.integers(0, len(values), size=(100, len(values)))].mean(1) for _ in range(100)])
    return np.quantile(boot, [0.025, 0.975], axis=0)

def collect(ds):
    lock = read(RUN / 'config.locked.json')
    data = load_data(ds)
    n = len(data['q'])
    aligned = {name: {key:np.zeros((n, 2), dtype='i4' if key == 'actions' else 'f8')
               for key in ['actions', 'recall_delta', 'time_delta', 'utility', 'oracle_regret', 'response_mse']}
               for name in METHODS}
    fold_ids = np.empty(n, 'i4')
    oracle = np.empty((n, 2))
    for fold, roles in enumerate(lock['roles'][ds]):
        p = RUN / 'results' / ds / f'fold_{fold}'
        labels = np.load(p / 'labels.npz')
        rows = labels['rows']
        assert np.array_equal(rows, roles['outer'])
        fold_ids[rows] = fold
        oracle[rows] = labels['utility'].max(1)
        for name in METHODS:
            pred = np.zeros((len(rows), len(data['hubs']), 2), 'f4') if name == 'GT10' else np.load(p / f'{name}.npy')
            assert np.isfinite(pred).all()
            for k in range(2):
                a = actions(pred[:, :, k], data['hubs'])
                out = aligned[name]
                out['actions'][rows, k] = a
                for key in ['recall_delta', 'time_delta', 'utility']:
                    out[key][rows, k] = selected(labels[key][:, :, k], a)
                out['oracle_regret'][rows, k] = oracle[rows, k] - out['utility'][rows, k]
                out['response_mse'][rows, k] = ((pred[:, :, k] - labels['utility'][:, 1:, k]) ** 2).mean(1)
                assert np.allclose(out['utility'][rows, k], out['recall_delta'][rows, k] - 0.1*out['time_delta'][rows, k], atol=1e-7)
                assert (out['oracle_regret'][rows, k] >= -1e-7).all()
    results, table = {}, []
    dest = RUN / 'analysis' / ds
    dest.mkdir(parents=True)
    for name, vals in aligned.items():
        np.savez_compressed(dest / f'{name}.npz', source_rows=data['rows'], folds=fold_ids, **vals)
        utility = vals['utility'].mean(1)
        confidence = intervals(utility).tolist()
        results[name] = dict(mean_utility=float(utility.mean()), utility_CI95=confidence,
            fold_utility=[float(utility[fold_ids == f].mean()) for f in range(4)], K={})
        for k, K in enumerate([1, 100]):
            dr, dt, u = [vals[key][:, k] for key in ['recall_delta', 'time_delta', 'utility']]
            recall_ci = (100 * intervals(dr)).tolist()
            counts = np.rint(dr * K).astype('i4')
            result = dict(recall_delta_pp=float(100 * dr.mean()), recall_CI95_pp=recall_ci,
                cached_time_delta_pct=float(100 * dt.mean()), utility=float(u.mean()),
                rescue_queries=int((counts > 0).sum()), harmed_queries=int((counts < 0).sum()),
                gained_hits=int(np.maximum(counts, 0).sum()), lost_hits=int(-np.minimum(counts, 0).sum()),
                switches=int((vals['actions'][:, k] != 0).sum()), mean_oracle_regret=float(vals['oracle_regret'][:, k].mean()),
                utility_MSE=float(vals['response_mse'][:, k].mean()))
            results[name]['K'][str(K)] = result
            table.append(dict(dataset=ds, method=name, K=K, **{key:v for key,v in result.items() if not isinstance(v, list)}))
    contrasts = {}
    for cap, control in [('CapMSE','GeomMSE'), ('CapRank','GeomRank'), ('CapMSE','E118Additive'), ('CapRank','E118Additive')]:
        diff = (aligned[cap]['utility'] - aligned[control]['utility']).mean(1)
        contrasts[f'{cap}-{control}'] = dict(mean=float(diff.mean()), CI95=intervals(diff).tolist(),
            fold_means=[float(diff[fold_ids == f].mean()) for f in range(4)])
    return results, contrasts, table, dict(mean_utility=oracle.mean(0).tolist(),
        oracle_recall_delta_pp=(100*(data['recall'].max(1)-data['recall'][:,0]).mean(0)).tolist(),
        utility_oracle_scope='ex-post noisy timing labels, not expected population value',
        baseline_recall=data['recall'][:, 0].mean(0).tolist())

if __name__ == '__main__':
    start = time.monotonic()
    assert read(RUN / 'reviews/training_complete.json')['status'] == 'COMPLETE'
    lock = read(RUN / 'config.locked.json')
    all_results, contrasts, oracles, rows = {}, {}, {}, []
    for ds in lock['datasets']:
        all_results[ds], contrasts[ds], table, oracles[ds] = collect(ds)
        rows.extend(table)
        print('ANALYZED', ds, flush=True)
    gates = {}
    for name in lock['primary'] + lock['strong']:
        per_ds = {}
        for ds in lock['datasets']:
            r = all_results[ds][name]
            per_ds[ds] = dict(positive_utility=r['mean_utility'] > 0,
                descriptive_lower_above_zero=r['utility_CI95'][0] > 0,
                mean_recall_noninferiority=all(v['recall_delta_pp'] >= -0.1 for v in r['K'].values()))
        gates[name] = dict(datasets=per_ds, pass_all=all(all(v.values()) for v in per_ds.values()))
    eligible = [name for name in lock['primary'] if gates[name]['pass_all']]
    strong_pass = [name for name in lock['strong'] if gates[name]['pass_all']]
    selected_name = sorted(eligible, key=lambda name:(-np.mean([all_results[ds][name]['mean_utility'] for ds in lock['datasets']]), name))[0] if eligible else None
    h1 = {}
    for name in ['CapMSE', 'CapRank']:
        control = name.replace('Cap', 'Geom')
        h1[name] = all(contrasts[ds][f'{name}-{control}']['mean'] > 0 and
            sum(v > 0 for v in contrasts[ds][f'{name}-{control}']['fold_means']) >= 3 for ds in lock['datasets'])
    h2 = {name: all(contrasts[ds][f'{name}-E118Additive']['mean'] > 0 for ds in lock['datasets']) for name in ['CapMSE','CapRank']}
    stage = 'GO_FROZEN_NATIVE_CANDIDATE' if selected_name else ('STRONG_ONLY_COMPRESSION_OPPORTUNITY' if strong_pass else 'STOP_CAPABILITY_PILOT')
    report = dict(status=stage, results=all_results, contrasts=contrasts, oracles=oracles, gates=gates,
        H1=h1, H2_mean_contrast=h2, selected=selected_name, strong_only=strong_pass,
        uncertainty_scope='descriptive query bootstrap on historically exposed OOF data; overlapping training folds',
        cost_scope='cached main-search-only time; excludes scorer and GT10 router; not QPS',
        default_changed=False, new_search_calls=0, seconds=time.monotonic() - start)
    dump(RUN / 'analysis/results.json', report)
    with (RUN / 'analysis/metrics.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    dump(RUN / 'state.json', dict(status=stage, selected=selected_name, default_changed=False,
        new_search_calls=0, pending=['independent_audit', 'report', 'documentation']))
    print(stage, selected_name, flush=True)
