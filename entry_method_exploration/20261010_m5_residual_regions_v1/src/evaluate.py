#!/usr/bin/env python3
"""Evaluate frozen E174 packets only, after all four native jobs finish."""
import argparse
import csv
import hashlib
import json
import struct
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

def require(ok, message):
    if not ok:
        raise ValueError(message)

def read_json(p):
    return json.loads(Path(p).read_text())

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()

def raw(p, dtype, shape):
    a = np.fromfile(p, dtype=dtype)
    require(a.size == int(np.prod(shape)), f'shape: {p}')
    return a.reshape(shape)

def csv_write(p, rows):
    if not rows:
        p.write_text('')
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with p.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in row.items()})

def ci(delta, K, key):
    values, counts = np.unique(delta, return_counts=True)
    seed = (20261010 + int.from_bytes(hashlib.sha256(key.encode()).digest()[:4], 'little')) % 2**32
    rng = np.random.default_rng(seed)
    draws = rng.multinomial(len(delta), counts / len(delta), size=2000)
    means = draws @ values.astype(float) / (len(delta) * K) * 100
    lo, hi = np.quantile(means, [.025, .975])
    return {'low_pp': float(lo), 'high_pp': float(hi), 'seed': seed, 'repeats': 2000,
            'scope': 'descriptive paired query bootstrap, no semantic IID or simultaneous comparison guarantee'}

def compare(a, b):
    p, r = a['point'], b['point']
    delta = a['hits'].astype(int) - b['hits'].astype(int)
    rescue = (a['members'] & ~b['members']).sum(axis=1)
    damage = (b['members'] & ~a['members']).sum(axis=1)
    require(np.array_equal(delta, rescue.astype(int) - damage.astype(int)), 'member delta identity')
    ratios = np.asarray(p['qps_rounds']) / np.asarray(r['qps_rounds'])
    key = f"{p['role']}|{p['dataset']}|{p['K']}|{p['L']}|{p['method']}|{r['L']}|{r['method']}"
    return {'role': p['role'], 'dataset': p['dataset'], 'K': p['K'], 'L': p['L'],
            'method': p['method'], 'reference_L': r['L'], 'reference': r['method'],
            'n': p['n'], 'recall_delta_pp': float(delta.sum() / (p['n'] * p['K']) * 100),
            'rescue_members': int(rescue.sum()), 'damage_members': int(damage.sum()),
            'queries_net_improved': int((delta > 0).sum()), 'queries_net_damaged': int((delta < 0).sum()),
            'paired_qps_ratio_rounds': ratios.tolist(), 'paired_qps_ratio_median': float(np.median(ratios)),
            'paired_qps_change_pct': float((np.median(ratios) - 1) * 100),
            'qps_ratio_pairing_scope': 'same KL round matched sequential methods' if p['L'] == r['L'] else 'cross L round index only, descriptive, not simultaneous or randomized pairing',
            'speed_ranges_separated': bool(min(p['qps_rounds']) > max(r['qps_rounds'])),
            'all_rounds_faster': bool(np.all(ratios > 1)),
            'observed_joint_gain': bool(delta.sum() > 0 and np.median(ratios) > 1),
            'delta_ci': ci(delta, p['K'], key)}

def posting_U(p):
    b = Path(p).read_bytes()
    require(b[:8] == b'M5POST1\0', 'posting magic')
    h = struct.unpack_from('<8I', b, 8)
    require(h[0] == 1 and h[2] == 8, 'posting header')
    H = h[1]
    counts = np.frombuffer(b, dtype='u1', count=H, offset=40 + 4 * H)
    ids = np.frombuffer(b, dtype='<i4', count=H * 8, offset=40 + 5 * H).reshape(H, 8)
    return set(int(ids[i, j]) for i in range(H) for j in range(int(counts[i])))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=ROOT / 'analysis' / 'final_v1')
    args = parser.parse_args()
    require(not args.out.exists(), 'preserve analysis')
    lock = read_json(ROOT / 'parameter_lock.json')
    require(sha(ROOT / 'protocol.md') == lock['protocol_sha256'], 'protocol changed')
    require(len(lock['jobs']) == 4, 'all four frozen roles/datasets')
    run_state = read_json(ROOT / 'run_state.json')
    require(run_state['status'] == 'NATIVE_COMPLETE_PENDING_INDEPENDENT_GT_EVALUATION' and run_state.get('active') is None,
            'all native work must finish before analysis')
    require(len(run_state['completed']) == 4 and all(x['exit_code'] == 0 for x in run_state['completed']), 'four successful native jobs')
    # Read all completion receipts before any role GT is decoded.
    configs = []
    for job, expected in lock['jobs'].items():
        require(sha(job) == expected, 'frozen job changed')
        c = read_json(job)
        complete = read_json(Path(c['out']) / 'complete.json')
        require('PASS' in complete['status'], 'native completion')
        require(read_json(Path(c['out']) / 'job.json') == c, 'actual config changed')
        for K in c['K_values']:
            for L in c['L']:
                for method in c['methods']:
                    point = read_json(Path(c['out']) / f'k{K}' / f'{method["name"]}_L{L}' / 'complete.json')
                    require(point['n'] == 4096 and point['plain_count_bits_equal'] and len(point['timing_seconds']) == 3,
                            'all point receipts before GT')
        configs.append(c)
    points, comparisons, sources, mechanisms = [], [], {}, []
    packets = {}
    inventory = read_json(ROOT / 'reviews/inventory.json')
    supports = {}
    for ds, data in inventory['datasets'].items():
        require(sha(data['m5']['path']) == data['m5']['sha256'], 'original M5 U identity')
        sources[data['m5']['path']] = data['m5']['sha256']
        manifest = read_json(data['compile_manifest'])
        p = next(p for p in manifest['input_sha256'] if p.endswith('/fit/gt.i64'))
        require(sha(p) == manifest['input_sha256'][p], 'original TRAIN GT support identity')
        values = raw(p, '<i8', (20000, 100))
        supports[ds] = (posting_U(data['m5']['path']), set(int(x) for x in np.unique(values)))
        sources[p] = manifest['input_sha256'][p]
    for c in configs:
        n, base_n = c['n'], c['base_n']
        require(n == 4096 and c['cpu'] == 15 and c['threads'] == 1 and c['no_training'], 'frozen full scope')
        for key, hk in [('queries', 'query_sha256'), ('GT', 'GT_sha256'), ('rows', 'rows_sha256')]:
            sources[c[key]] = sha(c[key])
            require(sources[c[key]] == c[hk], 'role identity')
        gt = raw(c['GT'], '<i4', (n, 100))
        require(np.all((gt >= 0) & (gt < base_n)), 'GT domain')
        require(all(len(set(row)) == 100 for row in gt), 'GT unique')
        root = Path(c['out'])
        env = read_json(root / 'native_environment.json')
        require(env['threads'] == 1 and env['no_GT_read'], 'native single thread, GT free')
        audit_n = 256
        audit_ids = np.arange(audit_n) * (n - 1) // (audit_n - 1)
        ds, role = c['dataset'], c['role']
        for K in c['K_values']:
            for L in c['L']:
                for method in c['methods']:
                    name = method['name']
                    folder = root / f'k{K}' / f'{name}_L{L}'
                    receipt = read_json(folder / 'complete.json')
                    require(receipt['n'] == n and receipt['K'] == K and receipt['L'] == L and receipt['method'] == name, 'point identity')
                    require(receipt['threads'] == 1 and receipt['cpu'] == 15 and receipt['plain_count_bits_equal'], 'point parity/thread')
                    require(receipt['normal_output_release_before_stop'] and not receipt['timed_output_retained'], 'complete lifetime wall')
                    wall = np.asarray(receipt['timing_seconds'])
                    require(len(wall) == 3 and np.all(np.isfinite(wall) & (wall > 0)), 'three full wall rounds')
                    ids = raw(folder / 'raw/ids.i32', '<i4', (n, K))
                    distances = raw(folder / 'raw/distances.f32', '<f4', (n, K))
                    entries = raw(folder / 'raw/entry_ids.i32', '<i4', (n, 3))
                    profiles = raw(folder / 'raw/profile_distances.f32', '<u4', (n, 3))
                    require(np.all(np.isfinite(distances)), 'finite distances')
                    require(np.all((ids == -1) | ((ids >= 0) & (ids < base_n))), 'returned ID domain')
                    require(np.all(distances[ids == -1] == np.finfo(np.float32).max), 'padding words')
                    require(np.array_equal(raw(folder / 'raw/audit_query_ids.i32', '<i4', (audit_n,)), audit_ids), 'count query alignment')
                    graph = raw(folder / 'raw/graph_ndc.u64', '<u8', (audit_n,))
                    route = raw(folder / 'raw/route_ndc.u64', '<u8', (audit_n,))
                    hits = np.empty(n, dtype=np.int16)
                    members = np.zeros((n, K), dtype=bool)
                    for i in range(n):
                        valid = ids[i][ids[i] >= 0]
                        returned = set(valid)
                        require(len(returned) == len(valid), 'returned uniqueness')
                        members[i] = [target in returned for target in gt[i, :K]]
                        hits[i] = len(returned & set(gt[i, :K]))
                    require(np.array_equal(hits, members.sum(axis=1)), 'set/member count cross-check')
                    qps = n / wall
                    p = {'role': role, 'dataset': ds, 'K': K, 'L': L, 'method': name, 'n': n,
                         'recall_pct': float(hits.sum() / (n * K) * 100), 'matched_GT_members': int(hits.sum()),
                         'qps_rounds': qps.tolist(), 'qps_median': float(np.median(qps)),
                         'qps_min': float(qps.min()), 'qps_max': float(qps.max()), 'wall_seconds': wall.tolist(),
                         'graph_ndc_sample_mean': float(graph.mean()), 'route_ndc_sample_mean': float(route.mean()),
                         'count_audit_n': audit_n, 'count_scope': 'fixed 256 only; post included in graph_ndc',
                         'stats': receipt['stats'], 'source_complete': str(folder / 'complete.json')}
                    points.append(p)
                    packets[(role, ds, K, L, name)] = {'point': p, 'hits': hits, 'members': members,
                                                       'ids': ids, 'entries': entries, 'profiles': profiles, 'graph': graph, 'route': route}
                    for f in (folder / 'raw').iterdir():
                        if f.is_file(): sources[str(f)] = sha(f)
                    sources[str(folder / 'complete.json')] = sha(folder / 'complete.json')
                ref = packets[(role, ds, K, L, 'GT')]
                for method in c['methods']:
                    name = method['name']
                    a = packets[(role, ds, K, L, name)]
                    require(np.array_equal(a['entries'], ref['entries']) and np.array_equal(a['profiles'], ref['profiles']) and np.array_equal(a['route'], ref['route']), 'post preserves route packet/count')
                    require(np.all(a['graph'] >= ref['graph']), 'main search counts retained')
                    sampled_fee = a['point']['stats']['post_dots'] + a['point']['stats']['new_distances']
                    require(sum(map(int, a['graph'])) - sum(map(int, ref['graph'])) == sampled_fee,
                            'sampled physical main/post/X score count accounting')
                    if method['extra_cap']:
                        folder = root / f'k{K}' / f'{name}_L{L}'
                        trace = raw(folder / 'raw/region_trace.i32', '<i4', (n, 128))
                        # meta: seeds3, nC, nX, nSeeds, m5_committed, X_aborted.
                        require(np.all((trace[:, 3] >= 0) & (trace[:, 3] <= 24)), 'C cap')
                        require(np.all((trace[:, 4] >= 0) & (trace[:, 4] <= method['extra_cap'])), 'X cap')
                        require(np.all((trace[:, 5] >= 0) & (trace[:, 5] <= 3)), 'seed cap')
                        U, teacher_U = supports[ds]
                        m = {'role': role, 'dataset': ds, 'K': K, 'L': L, 'method': name, 'n': n,
                             'C_total': 0, 'X_total': 0, 'selected_seeds_total': 0, 'queries_with_X': 0,
                             'X_outside_original_M5_U': 0, 'X_outside_original_TRAIN_GT100_U': 0,
                             'new_rescues_vs_M5': 0, 'new_rescues_outside_original_M5_U': 0,
                             'new_rescues_outside_original_TRAIN_GT100_U': 0, 'extension_aborted': int(trace[:, 7].sum())}
                        for i in range(n):
                            nc, nx, ns = map(int, trace[i, 3:6])
                            C = trace[i, 8:8 + nc].tolist()
                            X = trace[i, 32:32 + nx].tolist()
                            S = trace[i, :ns].tolist()
                            require(len(set(C)) == nc and len(set(X)) == nx and len(set(S)) == ns, 'trace uniqueness')
                            require(all(0 <= x < base_n for x in C + X + S), 'trace domain')
                            require(set(S) <= set(C), 'seed from original C')
                            require(not (set(C) & set(ref['ids'][i])) and not (set(X) & (set(C) | set(ref['ids'][i]))), 'trace candidate disjointness')
                            require(set(a['ids'][i][a['ids'][i] >= 0]) <= set(ref['ids'][i]) | set(C) | set(X), 'return from original/candidate domain')
                            m['C_total'] += nc
                            m['X_total'] += nx
                            m['selected_seeds_total'] += ns
                            m['queries_with_X'] += int(nx > 0)
                            m['X_outside_original_M5_U'] += len(set(X) - U)
                            m['X_outside_original_TRAIN_GT100_U'] += len(set(X) - teacher_U)
                            if name.startswith('M5') and name not in ('M5',):
                                original = packets[(role, ds, K, L, 'M5')]
                                new_true = (set(a['ids'][i]) - set(original['ids'][i])) & set(gt[i, :K])
                                require(new_true <= set(X), 'M5 extension rescue attributed to new X')
                                m['new_rescues_vs_M5'] += len(new_true)
                                m['new_rescues_outside_original_M5_U'] += len(new_true - U)
                                m['new_rescues_outside_original_TRAIN_GT100_U'] += len(new_true - teacher_U)
                        m['C_mean'] = m['C_total'] / n
                        m['X_mean'] = m['X_total'] / n
                        m['selected_seeds_mean'] = m['selected_seeds_total'] / n
                        mechanisms.append(m)
                    if name != 'GT': comparisons.append(compare(a, ref))
                    if name not in ('GT', 'M5'): comparisons.append(compare(a, packets[(role, ds, K, L, 'M5')]))
                for name, reference in [('MFREG96', 'MFDIRECT'), ('GEOREG96', 'GEODIRECT'), ('M5REG96', 'M5FIRST96'), ('M5REG96', 'M5REG24'), ('M5REG96', 'MFREG96'), ('M5REG96', 'GEOREG96')]:
                    if any(m['name'] == reference for m in c['methods']):
                        comparisons.append(compare(packets[(role, ds, K, L, name)], packets[(role, ds, K, L, reference)]))
            small, big = c['L']
            for method in c['methods']:
                if method['name'] != 'GT':
                    comparisons.append(compare(packets[(role, ds, K, small, method['name'])], packets[(role, ds, K, big, 'GT')]))
    require(len(points) == 112, 'all 112 points')
    args.out.mkdir(parents=True)
    result = {'status': 'COMPLETE_E174_FROZEN_112_POINT_EVALUATION', 'points': points, 'comparisons': comparisons,
              'mechanisms': mechanisms, 'source_sha256': sources, 'training_increment_seconds': 0,
              'default_replacement': False, 'primary_method': 'M5REG96',
              'limits': ['two frozen L per dataset', '4096 queries per role', 'role disjointness is not semantic IID',
                         'descriptive bootstrap across many comparisons', '256 count audit, full saved plain returns, no timed packet retention']}
    (args.out / 'metrics.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    csv_write(args.out / 'points.csv', points)
    csv_write(args.out / 'comparisons.csv', comparisons)
    csv_write(args.out / 'mechanisms.csv', mechanisms)
    (args.out / 'scored').mkdir()
    for key, packet in packets.items():
        role, ds, K, L, name = key
        np.savez_compressed(args.out / 'scored' / f'{role}.{ds}.k{K}.{name}.L{L}.npz', hits=packet['hits'], GT_member_bits=np.packbits(packet['members'], axis=1))
    print(json.dumps({'status': result['status'], 'points': len(points), 'comparisons': len(comparisons)}))

if __name__ == '__main__':
    main()
