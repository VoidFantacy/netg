"""Frozen diagnostic of existing IDs/slots/hit arrays; never opens vectors or GT."""
from pathlib import Path
import hashlib
import json
import time

import numpy as np

ROOT = Path('/data/netg/ACSG')
OUT = Path(__file__).resolve().parent
OLD = ROOT / 'entry_method_exploration/20260930_theory_until2200_v1/research'
TRANSFER = OLD / 'query_target_transfer_v1'
CURVE = OLD / 'target_bank_frozen_curve_v1'
READS = {}


def identity(path):
    p = Path(path)
    return {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}


def consume(path):
    p = Path(path)
    READS[str(p)] = identity(p)
    return p


def read_json(path):
    return json.loads(consume(path).read_text())


def ints(path, dtype, shape):
    return np.fromfile(consume(path), dtype=dtype).reshape(shape)


def put(path, obj):
    with Path(path).open('x') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def distribution(x):
    return {'mean': float(np.mean(x)), 'p50': float(np.quantile(x, .5)),
            'p90': float(np.quantile(x, .9)), 'p99': float(np.quantile(x, .99)),
            'min': int(np.min(x)), 'max': int(np.max(x))}


def grouped_delta(d, mask, k):
    a = d[mask]
    return {'n': len(a), 'delta_Recall_pp': None if not len(a) else float(a.mean() * 100 / k),
            'rescued_queries': int((a > 0).sum()), 'damaged_queries': int((a < 0).sum()),
            'query_net_positive_hits': int(a[a > 0].sum()),
            'query_net_negative_hits': int(-a[a < 0].sum()), 'net_hits': int(a.sum())}


def main():
    started = time.perf_counter()
    config = read_json(CURVE / 'config.locked.json')
    prior = read_json(TRANSFER / 'config.locked.json')
    analysis = read_json(CURVE / 'results/analysis.json')
    result = {}
    for ds, cfg in config['datasets'].items():
        n, nt = cfg['n'], cfg['train_n']
        target = ints(cfg['targets'], '<i4', (nt,))
        hub = ints(prior['datasets'][ds]['hub_mapping'], '<i4', (nt,))
        hids = ints(cfg['anchor']['ids'], '<i4', (cfg['H'],))
        assert len(np.unique(hids)) == cfg['H'] and (hids >= 0).all()
        assert np.isin(hub, hids).all()
        unique_target, representative, inv = np.unique(target, return_index=True, return_inverse=True)
        assert np.array_equal(hub, hub[representative][inv]), 'duplicate target has inconsistent bucket'
        position = {int(h): i for i, h in enumerate(hids)}
        b = np.array([position[int(h)] for h in hub], dtype=np.int32)
        physical = np.bincount(b, minlength=cfg['H'])
        unique = np.bincount(b[representative], minlength=cfg['H'])
        assert physical.sum() == nt and unique.sum() == len(unique_target)
        with np.load(consume(CURVE / 'results' / ds / 'score_arrays.npz'), allow_pickle=False) as z:
            hits = z['hits'].copy()
        assert hits.shape == (n, 6, 3)
        initial = None
        rows = []
        for pi, point in enumerate(cfg['points']):
            k, l = point['K'], point['L']
            loc = CURVE / 'results' / ds / f'k{k}_L{l}'
            entries = ints(loc / 'Default3/entry_ids.i32', '<i4', (n, 3))
            slots = ints(loc / 'TargetBank1/route_slots.i32', '<i4', (n,))
            chosen = ints(loc / 'TargetBank1/entry_ids.i32', '<i4', (n, 3))
            droute = ints(loc / 'Default3/route_ndc.u64', '<u8', (n,))
            troute = ints(loc / 'TargetBank1/route_ndc.u64', '<u8', (n,))
            dg = ints(loc / 'Default3/graph_ndc.u64', '<u8', (n,))
            tg = ints(loc / 'TargetBank1/graph_ndc.u64', '<u8', (n,))
            assert np.isin(entries, hids).all()
            assert all(len(set(x.tolist())) == 3 for x in entries)
            assert ((slots >= 0) & (slots < nt)).all()
            assert np.array_equal(chosen[:, 0], target[slots]) and (chosen[:, 1:] == -1).all()
            current = [entries, slots, droute, troute]
            if initial is None:
                initial = [x.copy() for x in current]
            else:
                assert all(np.array_equal(x, y) for x, y in zip(initial, current)), 'route changes across K/L'
            ep = np.array([[position[int(h)] for h in r] for r in entries], dtype=np.int32)
            m = physical[ep].sum(axis=1)
            mu = unique[ep].sum(axis=1)
            covered = (entries == hub[slots, None]).any(axis=1)
            delta = hits[:, pi, 2].astype(np.int64) - hits[:, pi, 0]
            old = analysis['datasets'][ds]['points'][f'k{k}_L{l}']['methods']
            assert int(hits[:, pi, 0].sum()) == old['Default3']['hits']
            assert int(hits[:, pi, 2].sum()) == old['TargetBank1']['hits']
            assert int(delta.sum()) == old['TargetBank1']['vs_Default3']['net_positive_hits'] - old['TargetBank1']['vs_Default3']['net_negative_hits']
            rows.append({'K': k, 'L': l,
                         'all': grouped_delta(delta, np.ones(n, dtype=bool), k),
                         'old_slot_covered': grouped_delta(delta, covered, k),
                         'old_slot_not_covered': grouped_delta(delta, ~covered, k),
                         'old_graph_NDC_saving_mean': float(dg.astype(np.int64).mean() - tg.mean()),
                         'old_full_wall_extra_us_per_query': old['TargetBank1']['vs_Default3']['extra_us_per_query']})
        np.savez(OUT / f'{ds}.bucket_alignment.npz', default_entries=initial[0], target_slots=initial[1],
                 physical_candidate_count=m, unique_candidate_count=mu,
                 old_slot_covered=covered, old_hits=hits, source_bucket_ids=hub,
                 training_target_ids=target)
        pmean, umean = float(m.mean()), float(mu.mean())
        result[ds] = {'n': n, 'physical_targets': nt, 'unique_real_targets': len(unique_target),
                      'physical_bucket_distribution': distribution(physical),
                      'unique_bucket_distribution': distribution(unique),
                      'M_physical': distribution(m), 'M_unique': distribution(mu),
                      'old_TargetBank_slot_covered_count': int(covered.sum()),
                      'old_TargetBank_slot_covered_pct': float(covered.mean() * 100),
                      'Default3_route_NDC_mean': float(initial[2].mean()),
                      'TargetBank_route_NDC_mean': float(initial[3].mean()),
                      'GT10_plus_physical_scan_request_count_mean': float(initial[2].mean()) + pmean,
                      'GT10_plus_unique_scan_request_count_mean': float(initial[2].mean()) + umean,
                      'physical_scan_request_difference_vs_TargetBank': float(initial[2].mean()) + pmean - float(initial[3].mean()),
                      'unique_scan_request_difference_vs_TargetBank': float(initial[2].mean()) + umean - float(initial[3].mean()),
                      'points': rows}
    for path, value in READS.items():
        assert identity(path) == value, 'consumed source changed'
    put(OUT / 'bucket_input_identity.json', READS)
    put(OUT / 'bucket_feasibility.json', {'status': 'FROZEN_OLD_ID_ARRAY_DIAGNOSTIC_COMPLETE',
         'datasets': result, 'seconds': time.perf_counter() - started,
         'new_vector_scores': 0, 'new_ANN_NSG_GT_calls': 0, 'new_models_graphs': 0,
         'query_or_base_vectors_opened': False,
         'interpretation': 'M and old approximate-slot coverage only; no new selection, Recall, or QPS prediction',
         'K100_positive_negative_definition': 'query-wise net hit differences; not true member added/lost'})
    for ds, v in result.items():
        print(ds, json.dumps({k: v[k] for k in ('M_physical', 'M_unique', 'old_TargetBank_slot_covered_pct',
              'Default3_route_NDC_mean', 'TargetBank_route_NDC_mean',
              'GT10_plus_unique_scan_request_count_mean')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
