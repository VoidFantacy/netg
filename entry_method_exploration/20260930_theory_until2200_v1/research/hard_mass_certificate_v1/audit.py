"""Independent all-subsets/endpoint reference. Does not import main checker."""
import hashlib
import itertools
import json
import os
import time
from pathlib import Path

R = Path(__file__).resolve().parent

def possible_sets(intervals, k, mode):
    # A subset is realizable iff selected upper endpoints dominate excluded lower endpoints.
    ans = []
    for subset in itertools.combinations(range(len(intervals)), k):
        outside = set(range(len(intervals))) - set(subset)
        if mode == 'all_ties':
            feasible = all(intervals[i][1] >= intervals[j][0] for i in subset for j in outside)
        else:
            feasible = all((intervals[i][1], -i) > (intervals[j][0], -j) for i in subset for j in outside)
        if feasible:
            ans.append(subset)
    return ans

def independent_record(intervals, labels, k, mode):
    members = possible_sets(intervals, k, mode)
    counts = sorted({tuple(sum(labels[i] == h for i in s) for h in range(max(labels)+1)) for s in members})
    certified = counts if len(counts) == 1 else []
    return [intervals, labels, k, members, counts, certified]

def main():
    os.sched_setaffinity(0, {0})
    started = time.perf_counter()
    result = json.loads((R/'results.json').read_text())
    frozen = json.loads((R/'frozen.json').read_text())
    assert time.time() < frozen['deadline_unix']
    for name, expected in frozen['source_sha256'].items():
        assert hashlib.sha256((R/name).read_bytes()).hexdigest() == expected
    assert result['affinity'] == [0] and result['status'] == 'FINITE_ENUMERATION_PASS_PENDING_INDEPENDENT_AUDIT'
    sha = {mode: hashlib.sha256() for mode in result['modes']}
    counts = {mode: 0 for mode in sha}
    intervals = [(lo, hi) for lo in (0,1,2) for hi in (0,1,2) if lo <= hi]
    for bounds in itertools.product(intervals, repeat=4):
        assert time.perf_counter()-started < 120 and time.time() < frozen['deadline_unix']
        for labels in itertools.product((0,1), repeat=4):
            for mode in sha:
                for k in (1,2,3,4):
                    row = independent_record(bounds, labels, k, mode)
                    raw = (json.dumps(row, sort_keys=True, separators=(',', ':'))+'\n').encode()
                    sha[mode].update(raw)
                    counts[mode] += 1
    for mode in sha:
        assert counts[mode] == result['modes'][mode]['k_problems'] == 82944
        assert sha[mode].hexdigest() == result['modes'][mode]['records_sha256'], mode
        assert result['modes'][mode]['stable_histogram_uncertain_members'] > 0
        assert result['modes'][mode]['stable_majority_uncertain_histogram'] > 0
    for example in result['examples']:
        bounds, labels, k = example['record'][:3]
        actual = independent_record(bounds, tuple(labels), k, example['mode'])
        assert json.dumps(actual) == json.dumps(example['record'])
    assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file()) < 256*1024
    assert time.time() < frozen['deadline_unix'] and time.perf_counter()-started < 120
    audit = {'status': 'PASS', 'seconds': time.perf_counter()-started, 'affinity': sorted(os.sched_getaffinity(0)),
             'scope': 'same agent; separate subset feasibility implementation; all endpoint-realizable continuous-box subsets',
             'k_problems_per_mode': counts, 'matching_record_sha256': {m: d.hexdigest() for m, d in sha.items()},
             'real_GT': 0, 'NSG': 0, 'ANN': 0, 'models': 0}
    with (R/'independent_audit.json').open('x') as f:
        json.dump(audit, f, indent=2); f.write('\n')
    print(json.dumps(audit), flush=True)

if __name__ == '__main__':
    main()
