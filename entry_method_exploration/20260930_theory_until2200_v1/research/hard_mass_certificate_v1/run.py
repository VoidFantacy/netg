"""Exhaustive finite-box check; no real data or search libraries."""
import hashlib
import itertools as it
import json
import os
import shutil
import time
from pathlib import Path

R = Path(__file__).resolve().parent
INTERVALS = tuple((a, b) for a in range(3) for b in range(a, 3))
MODES = ('all_ties', 'id_ascending')
EXAMPLES = (
    ('identity_uncertain_mass_fixed', ((9,11),(8,10),(8,10),(7,7)), (0,0,0,1), (2,)),
    ('majority_fixed_mass_uncertain', ((10,10),(9,9),(0,8),(7,7)), (0,0,0,1), (3,)),
    ('three_groups', ((2,3),(1,2),(0,3)), (0,1,2), (1,2,3)),
)

def encode(x):
    return (json.dumps(x, separators=(',', ':'), sort_keys=True) + '\n').encode()

def histogram(ids, labels, classes):
    return tuple(sum(labels[i] == h for i in ids) for h in range(classes))

def certificate(bounds, labels, count, mode):
    classes = len(count)
    low, high = [], []
    for h in range(classes):
        ids = [i for i, label in enumerate(labels) if label == h]
        key = lambda i, e: bounds[i][e] if mode == 'all_ties' else (bounds[i][e], -i)
        low.append(sorted((key(i, 0) for i in ids), reverse=True))
        high.append(sorted((key(i, 1) for i in ids), reverse=True))
    return all(low[h][count[h]-1] > high[g][count[g]]
               for h in range(classes) if count[h] > 0
               for g in range(classes) if g != h and count[g] < len(high[g]))

def enumerate_scores(bounds, k_values):
    out = {mode: {k: set() for k in k_values} for mode in MODES}
    completions = 0
    for scores in it.product(*(range(a, b+1) for a, b in bounds)):
        completions += 1
        order = sorted(range(len(bounds)), key=lambda i: (-scores[i], i))
        for k in k_values:
            out['id_ascending'][k].add(tuple(sorted(order[:k])))
            boundary = scores[order[k-1]]
            above = tuple(i for i, score in enumerate(scores) if score > boundary)
            equal = tuple(i for i, score in enumerate(scores) if score == boundary)
            for chosen in it.combinations(equal, k-len(above)):
                out['all_ties'][k].add(tuple(sorted(above + chosen)))
    return out, completions

def row(bounds, labels, k, mode, members):
    classes = max(labels)+1
    counts = sorted({histogram(s, labels, classes) for s in members})
    capacity = [labels.count(h) for h in range(classes)]
    candidates = [c for c in it.product(*(range(n+1) for n in capacity)) if sum(c) == k]
    certified = [c for c in candidates if certificate(bounds, labels, c, mode)]
    expected = counts if len(counts) == 1 else []
    record = [bounds, labels, k, sorted(members), counts, certified]
    if certified != expected:
        raise AssertionError({'mode': mode, 'counterexample': record, 'expected': expected})
    return record, len(candidates)

def main():
    os.sched_setaffinity(0, {0})
    started = time.perf_counter()
    frozen = json.loads((R/'frozen.json').read_text())
    assert time.time() < frozen['deadline_unix']
    assert shutil.disk_usage(R).free >= 6*1024**3
    assert sum(p.stat().st_size for p in R.parents[1].rglob('*') if p.is_file()) < 1024**3
    for name, sha in frozen['source_sha256'].items():
        assert hashlib.sha256((R/name).read_bytes()).hexdigest() == sha, name
    totals = {m: {'k_problems': 0, 'candidate_counts_checked': 0, 'stable_histogram': 0,
                  'stable_histogram_uncertain_members': 0, 'stable_majority_uncertain_histogram': 0} for m in MODES}
    digests = {m: hashlib.sha256() for m in MODES}
    instances = completions = 0
    for bounds in it.product(INTERVALS, repeat=4):
        assert time.perf_counter()-started < 120 and time.time() < frozen['deadline_unix']
        members, n = enumerate_scores(bounds, range(1,5))
        for labels in it.product(range(2), repeat=4):
            instances += 1
            completions += n
            for mode in MODES:
                for k in range(1,5):
                    record, checks = row(bounds, labels, k, mode, members[mode][k])
                    counts = record[4]
                    winners = {tuple(i for i, x in enumerate(c) if x == max(c)) for c in counts}
                    t = totals[mode]
                    t['k_problems'] += 1
                    t['candidate_counts_checked'] += checks
                    t['stable_histogram'] += len(counts) == 1
                    t['stable_histogram_uncertain_members'] += len(counts) == 1 and len(record[3]) > 1
                    t['stable_majority_uncertain_histogram'] += len(counts) > 1 and len(winners) == 1 and len(next(iter(winners))) == 1
                    digests[mode].update(encode(record))
    assert (instances, completions) == (20736, 160000)
    examples = []
    for name, bounds, labels, k_values in EXAMPLES:
        members, n = enumerate_scores(bounds, k_values)
        for mode in MODES:
            for k in k_values:
                record, checks = row(bounds, labels, k, mode, members[mode][k])
                examples.append({'name': name, 'mode': mode, 'record': record, 'completions': n})
    result = {'status': 'FINITE_ENUMERATION_PASS_PENDING_INDEPENDENT_AUDIT', 'seconds': time.perf_counter()-started,
              'affinity': sorted(os.sched_getaffinity(0)), 'instances': instances, 'score_completions': completions,
              'modes': {m: {**totals[m], 'records_sha256': digests[m].hexdigest()} for m in MODES},
              'examples': examples, 'real_GT': 0, 'NSG': 0, 'ANN': 0, 'models': 0, 'default_changed': False}
    assert time.time() < frozen['deadline_unix'] and time.perf_counter()-started < 120
    assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())+len(encode(result)) < 256*1024
    with (R/'results.json').open('x') as f:
        json.dump(result, f, indent=2); f.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'examples'}), flush=True)

if __name__ == '__main__':
    main()
