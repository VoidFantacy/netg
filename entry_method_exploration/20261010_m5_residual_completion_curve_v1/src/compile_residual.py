"""Compile TRAIN-only post-M5 residual completion; charged additional fitting.

CLI: compile_residual.py JOB.json --max-seconds REMAINING
REMAINING is the dataset-wide 900s allowance left after response generation and
all other charged stages. It is not another independent 900s allowance.
No public-test/CAL/confirmation input is used. No base graph or GT is built.
"""
import time
PROGRAM_STARTED = time.perf_counter()
import argparse
from array import array
from collections import Counter
import hashlib
import heapq
import json
import os
from pathlib import Path
import resource
import struct
import sys
import numpy as np

KS = (1, 100)
LS = (200, 400, 800, 1000, 1200)
SUPPORT = 2
CAP = 4
TOTAL_RUNTIME_CANDIDATE_CAP = 12
RAW_CAP_BYTES = 100000000


def stat4(path):
    s = Path(path).stat()
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns]


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(data, f, indent=2, allow_nan=False)
        f.write('\n')


class Guard:
    def __init__(self, seconds, config, output):
        if not (0 < seconds <= 900):
            raise ValueError('remaining dataset fitting budget must be >0 and <=900s')
        self.limit = seconds
        self.config = config
        self.output = Path(output)

    def deadline(self):
        if time.perf_counter() - PROGRAM_STARTED >= self.limit:
            raise TimeoutError('dataset fitting time remainder exhausted; partial models ineligible')

    def full(self):
        self.deadline()
        if os.sched_getaffinity(0) != {15}:
            raise ValueError('CPU15 only required')
        for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
            if os.environ.get(key) != '1':
                raise ValueError(key + '=1 required')
        for line in Path('/proc/self/status').read_text().splitlines():
            if line.startswith('Threads:') and int(line.split(':', 1)[1]) != 1:
                raise ValueError('actual single thread required')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024 > self.config['maxrss_bytes']:
            raise MemoryError('compiler RSS cap')
        st = os.statvfs(self.output)
        if st.f_bavail * st.f_frsize < self.config['min_free_bytes']:
            raise OSError('compiler free-space reserve')


def sha(path, guard):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        while True:
            guard.deadline()
            block = f.read(8 * 1024 * 1024)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def read_array(path, dtype, shape):
    expected = int(np.prod(shape)) * np.dtype(dtype).itemsize
    if Path(path).stat().st_size != expected:
        raise ValueError('shape/size mismatch: ' + str(path))
    return np.fromfile(path, dtype=dtype).reshape(shape)


def read_original_posting(path, base_n):
    data = Path(path).read_bytes()
    if len(data) < 40 or data[:8] != b'M5POST1\0':
        raise ValueError('original M5 posting format')
    version, H, b, hn, pairs, bn, unused0, unused1 = struct.unpack_from('<8I', data, 8)
    if version != 1 or b != 8 or bn != base_n or hn < 2 * H or hn & (hn - 1):
        raise ValueError('original M5 schema/domain')
    expected = 40 + H * 4 + H + H * 8 * 4 + hn * 8 + H * 8
    if len(data) != expected:
        raise ValueError('original M5 full bytes')
    labels = np.frombuffer(data, '<i4', H, 40)
    counts = np.frombuffer(data, 'u1', H, 40 + H * 4)
    targets = np.frombuffer(data, '<i4', H * 8, 40 + H * 5).reshape(H, 8)
    if len(set(map(int, labels))) != H or int(counts.sum()) != pairs:
        raise ValueError('original M5 labels/pairs')
    result = {}
    for label, count, row in zip(labels, counts, targets):
        valid = tuple(map(int, row[:int(count)]))
        if int(count) > 8 or len(set(valid)) != len(valid) or any(t < 0 or t >= base_n for t in valid):
            raise ValueError('original M5 row domain')
        if any(t != -1 for t in map(int, row[int(count):])):
            raise ValueError('original M5 padding')
        result[int(label)] = set(valid)
    return result


def keys_for_query(route, winners, pair):
    if pair:
        return sorted({(int(r), int(w)) for r, w in zip(route, winners) if int(w) >= 0})
    return sorted({(int(r), -1) for r in route})


def compile_joint(routes, winners, final_ids, truth, statuses, pair, guard):
    """Same unit query/target residual token and exact joint greedy for both models.

    A selected target covers that token once across all of the query's actual
    3 route keys. Coverage is global/shared, not per-row frequency. Each key's
    support is distinct eligible TRAIN queries, including zero-residual queries.
    No quality feedback changes support/caps/order, and no fallback table exists.
    """
    support = Counter()
    for i, (route, winner) in enumerate(zip(routes, winners)):
        if i % 256 == 0:
            guard.deadline()
        if int(statuses[i]) == 2:
            support.update(keys_for_query(route, winner, pair))
    keys = sorted(k for k, count in support.items() if count >= SUPPORT)
    slots = {key: i for i, key in enumerate(keys)}
    edges = {}
    token_count = 0
    residual_members = 0
    residual_queries = 0
    for i in range(len(routes)):
        if i % 128 == 0:
            guard.deadline()
        if int(statuses[i]) != 2:
            continue
        missing = sorted(set(map(int, truth[i])) - {int(t) for t in final_ids[i] if t >= 0})
        residual_members += len(missing)
        residual_queries += bool(missing)
        query_slots = [slots[k] for k in keys_for_query(routes[i], winners[i], pair) if k in slots]
        for target in missing:
            for slot in query_slots:
                edges.setdefault((slot, target), array('I')).append(token_count)
            token_count += 1
    guard.full()
    heap = [(-len(inc), slot, target) for (slot, target), inc in edges.items()]
    heapq.heapify(heap)
    covered = bytearray(token_count)
    rows = [[] for _ in keys]
    selected = []
    pops = 0
    covered_total = 0
    while heap:
        if pops % 256 == 0:
            guard.deadline()
        pops += 1
        upper, slot, target = heapq.heappop(heap)
        if len(rows[slot]) >= CAP:
            continue
        inc = edges[(slot, target)]
        gain = sum(1 for token in inc if not covered[token])
        if gain <= 0:
            continue
        if gain != -upper:
            heapq.heappush(heap, (-gain, slot, target))
            continue
        rows[slot].append(target)
        selected.append({'route': keys[slot][0], 'winner': keys[slot][1], 'target': target, 'gain': gain})
        for token in inc:
            covered[token] = 1
        covered_total += gain
    guard.full()
    # Empty eligible rows are omitted: their runtime lookup is the same pure
    # empty result, and the eligibility/support totals remain in the manifest.
    populated = [(key, row) for key, row in zip(keys, rows) if row]
    payload = np.full((len(populated), 7), -1, dtype='<i4')
    for j, (key, row) in enumerate(populated):
        payload[j, :3] = [key[0], key[1], len(row)]
        payload[j, 3:3 + len(row)] = row
    return payload, selected, {
        'eligible_key_count': len(keys), 'populated_key_count': len(populated),
        'observed_key_count': len(support), 'support_min_distinct_queries': SUPPORT,
        'eligible_query_count': int(np.count_nonzero(statuses == 2)),
        'residual_members': residual_members, 'residual_queries': residual_queries,
        'residual_query_target_tokens': token_count, 'candidate_key_target_edges': len(edges),
        'selected_key_target_pairs': len(selected), 'covered_residual_tokens': covered_total,
        'heap_pops': pops, 'integer_objective': 'one unit per missing (TRAIN query,GT_K target), globally covered once across that query\'s actual three keys',
        'greedy_tie': 'largest actual marginal uncovered token count; then lexicographically smaller(route,winner,target)',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('job', type=Path)
    parser.add_argument('--max-seconds', type=float, required=True)
    args = parser.parse_args()
    config = json.loads(args.job.read_text())
    if config['role'] != 'fit' or config['n'] != 20000 or tuple(config['K_values']) != KS or tuple(config['L']) != LS:
        raise ValueError('only locked historical FIT20K, actual K1/K100 and five L values')
    if config.get('GT_format', 'raw') != 'raw' or config['GT_dtype'] != '<i8' or config['GT_width'] != 100:
        raise ValueError('existing historical raw GT100 int64 only')
    fit = Path(config['out'])
    out = Path(config['models_out'])
    if out.exists():
        raise FileExistsError('preserve compiler output ' + str(out))
    out.mkdir(parents=True)
    guard = Guard(args.max_seconds, config, out)
    point_records = []
    try:
        guard.full()
        fit_receipt = json.loads((fit / 'complete.json').read_text())
        if fit_receipt['status'] != 'PASS_FIT_ORIGINAL_M5_ALL_10_POINTS' or fit_receipt['point_count'] != 10:
            raise ValueError('full original-M5 TRAIN response generation not complete')
        if fit_receipt['dataset'] != config['dataset'] or fit_receipt['n'] != config['n']:
            raise ValueError('fit receipt dataset/n')
        if not fit_receipt['original_m5_unmodified'] or fit_receipt['optimized_or_region_used'] or fit_receipt['ground_truth_read']:
            raise ValueError('FIT original-M5 teacher contract')
        if fit_receipt['raw_artifact_bytes'] > RAW_CAP_BYTES:
            raise ValueError('FIT artifact cap')
        for p, expected in fit_receipt['source_stats_before_after'].items():
            if stat4(p) != expected:
                raise ValueError('fit source identity changed ' + p)
        n = config['n']; base_n = config['base_n']
        source_paths = [args.job.resolve(), fit / 'complete.json', Path(config['GT']),
                        Path(config['rows']), Path(config['queries']), Path(config['original_m5_table'])]
        for K in KS:
            for L in LS:
                point = fit / f'k{K}_L{L}'
                source_paths += [point / name for name in ('complete.json', 'gt_ids.i32', 'm5_ids.i32',
                                                          'entry_ids.i32', 'c_winners.i32', 'fit_status.u8')]
        before = {str(p.resolve()): stat4(p) for p in source_paths}
        t = time.perf_counter()
        hashes = {str(p.resolve()): sha(p, guard) for p in source_paths}
        source_hash_seconds = time.perf_counter() - t
        t = time.perf_counter()
        truth = read_array(config['GT'], '<i8', (n, 100))
        if np.any(truth < 0) or np.any(truth >= base_n):
            raise ValueError('existing GT target domain')
        rows = read_array(config['rows'], '<i8', (n,))
        if len(set(map(int, rows))) != n:
            raise ValueError('distinct original source rows')
        original_posting = read_original_posting(config['original_m5_table'], base_n)
        label_decode_seconds = time.perf_counter() - t
        models = {}
        original_routes = None
        for K in KS:
            for L in LS:
                guard.full(); point_started = time.perf_counter()
                point = fit / f'k{K}_L{L}'
                pr = json.loads((point / 'complete.json').read_text())
                if pr['status'] != 'PASS_FIT_ORIGINAL_M5_RESPONSES' or (pr['K'], pr['L'], pr['n']) != (K, L, n):
                    raise ValueError('point original-M5 response identity')
                final = read_array(point / 'm5_ids.i32', '<i4', (n, K))
                baseline = read_array(point / 'gt_ids.i32', '<i4', (n, K))
                routes = read_array(point / 'entry_ids.i32', '<i4', (n, 3))
                winners = read_array(point / 'c_winners.i32', '<i4', (n, 3))
                statuses = read_array(point / 'fit_status.u8', 'u1', (n,))
                if np.any(final < -1) or np.any(final >= base_n) or np.any(baseline < -1) or np.any(baseline >= base_n):
                    raise ValueError('actual TRAIN response target domain')
                if np.any(statuses > 3):
                    raise ValueError('fit status domain')
                if original_routes is None:
                    original_routes = routes.copy()
                elif not np.array_equal(routes, original_routes):
                    raise ValueError('actual GT10 routes changed across K/L')
                for i in range(n):
                    if i % 256 == 0:
                        guard.deadline()
                    for label, winner in zip(routes[i], winners[i]):
                        if int(label) not in original_posting:
                            raise ValueError('actual TRAIN route missing frozen M5 row')
                        if int(winner) != -1 and (int(statuses[i]) != 2 or int(winner) not in original_posting[int(label)] or int(winner) in baseline[i]):
                            raise ValueError('winner must be successful original scored C, never original R')
                    if int(statuses[i]) != 2 and np.any(final[i] != baseline[i]):
                        raise ValueError('fallback actual original M5 IDs')
                pmodels = {}
                for name, pair in [('pair', True), ('route', False)]:
                    model_started = time.perf_counter()
                    payload, log, stats = compile_joint(routes, winners, final, truth[:, :K], statuses, pair, guard)
                    model_path = out / f'{name}.k{K}_L{L}.i32'
                    with model_path.open('xb') as f:
                        f.write(payload.tobytes())
                    log_path = out / f'{name}.k{K}_L{L}.selection_log.json'
                    write_json(log_path, log)
                    pmodels[name] = {'path': str(model_path.resolve()), 'sha256': sha(model_path, guard),
                        'dtype': '<i4', 'shape': list(payload.shape), 'bytes': model_path.stat().st_size,
                        'selection_log': str(log_path.resolve()), 'selection_log_sha256': sha(log_path, guard),
                        'K': K, 'L': L, 'base_n': base_n, 'seconds_including_model_serialization_hash': time.perf_counter() - model_started,
                        **stats}
                models[f'k{K}_L{L}'] = pmodels
                point_records.append({'K': K, 'L': L, 'elapsed_seconds': time.perf_counter() - point_started})
        guard.full()
        for p, expected in before.items():
            if stat4(p) != expected:
                raise ValueError('read-only compiler source changed ' + p)
        manifest = {'status': 'FROZEN_TRAIN_ONLY_POST_M5_RESIDUAL_COMPLETION_ALL_10_POINTS',
            'dataset': config['dataset'], 'n': n, 'role': 'fit', 'point_count': 10, 'models': models,
            'format': {'dtype': '<i4', 'row_words': 7, 'columns': ['route_id', 'winner_id', 'count', 'target0', 'target1', 'target2', 'target3'],
                       'row_order': 'strict lexicographic(route_id,winner_id)', 'padding': -1, 'count_max': CAP,
                       'route_only_winner': -1, 'lookup_miss': 'empty; no route-only fallback', 'overall_extra_candidate_cap': TOTAL_RUNTIME_CANDIDATE_CAP},
            'supervision': 'D(query,K,L) = existing GT_K - actual final original M5(query,K,L); no old baseline-only residuals',
            'same_supervision_control': 'route-only post-M5 residual table, same support>=2/b4/unit-token joint-union greedy; not widened original-M5 supervision',
            'eligible_query_statuses': [2], 'ignored_statuses': {'0': 'unsupported raw query',
                '1': 'empty original C or original-M5 fallback; no online completion', '3': 'nonfinite original-M5 fallback'},
            'source_sha256_and_stat4': {p: {'sha256': hashes[p], 'stat4': s} for p, s in before.items()},
            'source_hash_seconds': source_hash_seconds, 'label_decode_seconds': label_decode_seconds,
            'point_stages': point_records, 'compiler_elapsed_seconds': time.perf_counter() - PROGRAM_STARTED,
            'native_response_generation_elapsed_seconds': fit_receipt['elapsed_seconds'], 'compiler_max_seconds_remainder': args.max_seconds,
            'charged_scope': 'all response generation/loading/main/M5/teacher verification/hashes/GT label decode/joint greedy/serialization are additional fitting; external receipt provides whole shared dataset<=900s budget and process startup/closing overhead',
            'train_budget_is_not_zero': True, 'old_train_debt_reset': False, 'public_test_read': False,
            'cal_read': False, 'confirm_read': False, 'new_base_graph': False, 'new_ground_truth_teacher': False,
            'runtime_oracles_and_quality_pending': True}
        write_json(out / 'compile_manifest.json', manifest)
        try:
            guard.full()
        except Exception:
            (out / 'compile_manifest.json').unlink()
            raise
        print('FROZEN_TRAIN_ONLY_POST_M5_RESIDUAL_COMPLETION_ALL_10_POINTS', config['dataset'],
              time.perf_counter() - PROGRAM_STARTED, flush=True)
    except Exception as e:
        write_json(out / 'failure.json', {'status': 'FAIL_RESIDUAL_COMPILATION_INELIGIBLE',
            'error': str(e), 'completed_point_stages': point_records,
            'elapsed_seconds': time.perf_counter() - PROGRAM_STARTED, 'partial_is_model_eligible': False})
        raise


if __name__ == '__main__':
    main()
