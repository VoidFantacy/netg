"""Read-only verification of cached findings; no search or model training."""
from pathlib import Path
import csv
import hashlib
import json
import numpy as np

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]
OLD = ROOT / 'entry_method_exploration/20260920_entry_id_pilot_v1'
def read(p):
    return json.loads(p.read_text())
def dump(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

details = read(RUN / 'results/selected_edit_details.json')
summary = read(RUN / 'results/summary.json')
overlap = read(RUN / 'results/audit_overlap.json')
hits = read(OLD / 'results/hits.json')
paired = list(csv.DictReader((OLD / 'results/paired.csv').open()))
inputs = {OLD / 'results/hits.json', OLD / 'results/paired.csv', OLD / 'config.locked.json'}
checks = []
timing = []
for s in summary:
    ds = s['dataset']
    lab = OLD / 'results' / ds / 'labels'
    meta = np.fromfile(lab / 'meta.i32', np.int32).reshape(-1, 4)
    rawhit = np.fromfile(lab / 'hits.u16', np.uint16).reshape(-1, 2).astype(np.int64)
    seconds = np.fromfile(lab / 'seconds.f64', np.float64).reshape(-1, 2)
    bases = {int(m[0]): j for j, m in enumerate(meta) if m[1] == -1}
    assert len(bases) == s['fit_queries'] == 10000
    assert sorted(bases) == list(range(10000))
    groups = {}
    for j, m in enumerate(meta):
        if m[1] >= 0:
            groups.setdefault((int(m[1]), int(m[2])), []).append(j)
    assert len(groups) == s['candidates']
    support = []
    events = []
    for ix in groups.values():
        diff = np.array([rawhit[j] - rawhit[bases[int(meta[j, 0])]] for j in ix])
        support.append(len(ix))
        events.append(np.count_nonzero(diff, axis=0))
    events = np.array(events)
    assert np.median(support) == s['all_candidates']['support']['median']
    assert np.median(events[:, 0]) == s['all_candidates']['nonzero_r1_events']['median']
    assert int((events[:, 0] == 0).sum()) == s['all_candidates']['no_r1_effect_candidates']
    for method in ['Cost', 'RecallControl']:
        rows = [r for r in details if r['dataset'] == ds and r['method'] == method]
        assert len(rows) == 16
        for r in rows:
            ix = groups[r['old_id'], r['new_id']]
            diff = np.array([rawhit[j] - rawhit[bases[int(meta[j, 0])]] for j in ix])
            for k, name in enumerate(['fit_r1', 'fit_r100']):
                assert diff[:, k].sum() == r[name]['net']
                assert int(np.count_nonzero(diff[:, k])) == r[name]['nonzero']
            for f, record in enumerate(r['folds']):
                ix2 = [j for j in ix if meta[j, 3] == f]
                dt = np.array([seconds[j] - seconds[bases[int(meta[j, 0])]] for j in ix2])
                assert np.allclose(dt.mean(0), record['replicate_dt_seconds'], rtol=1e-12, atol=1e-15)
        aa = np.array([f['replicate_dt_seconds'] for r in rows for f in r['folds']])
        timing.append(dict(dataset=ds, method=method, fold_count=len(aa),
                           nonpositive_per_repeat=(aa <= 0).sum(0).tolist(),
                           opposite_sign_folds=int((aa[:, 0] * aa[:, 1] < 0).sum()),
                           mean_delta_microseconds=(aa.mean(0) * 1e6).tolist(),
                           median_delta_microseconds=(np.median(aa, axis=0) * 1e6).tolist(),
                           edits_with_all_four_nonpositive=sum(r['all_four_timing_signs_nonpositive'] for r in rows)))
        groups_a = [r for r in overlap if r['dataset'] == ds and r['method'] == method]
        assert sum(r['n'] for r in groups_a) == 4096
        for k in [1, 100]:
            dh = np.array(hits[ds][f'{method}_K{k}']) - np.array(hits[ds][f'GT10_K{k}'])
            assert sum(r[f'k{k}']['net'] for r in groups_a) == dh.sum()
            assert sum(r[f'k{k}']['positive'] for r in groups_a) == int((dh > 0).sum())
            assert sum(r[f'k{k}']['negative'] for r in groups_a) == int((dh < 0).sum())
            original = next(r for r in paired if r['dataset'] == ds and r['method'] == method and int(r['K']) == k)
            assert abs(float(original['delta_recall_pp']) - 100 * dh.sum() / (4096 * k)) < 1e-12
            assert sum(r['n'] for r in groups_a if r['edits_in_query']) == int(original['entry_changed_queries'])
            for r in [x for x in groups_a if x['edits_in_query'] == 0]:
                assert r[f'k{k}']['nonzero'] == 0
        # Independently count actual set differences, rather than selected old-slot membership.
        audit = OLD / 'results' / ds / 'audit'
        bpath = audit / 'GT10_K1_L128/entry_ids.i32'
        epath = audit / f'{method}_K1_L128/entry_ids.i32'
        be = np.fromfile(bpath, np.int32).reshape(-1, 3)
        ee = np.fromfile(epath, np.int32).reshape(-1, 3)
        changed = np.array([len(set(a) - set(b)) for a, b in zip(be, ee)])
        for r in groups_a:
            assert int((changed == r['edits_in_query']).sum()) == r['n']
        inputs.update([bpath, epath])
    inputs.update(lab / n for n in ['meta.i32', 'hits.u16', 'seconds.f64', 'ndc.u64'])
    inputs.update(OLD / 'models' / ds / n for n in ['models.json', 'selection_details.json'])
    inputs.add(OLD / 'results' / ds / 'route_fit/entries.i32')
    checks.append(dict(dataset=ds, all_candidates_checked=len(groups), selected_models_checked=2, audit_queries=4096))

before = read(RUN / 'reviews/protected_before.json')
root_docs = {str(ROOT / n) for n in ['summary.md', 'spec.md', 's-target.md', 's-experiment.md', 'experiment_history/README.md']}
protected = []
for name, sha in before.items():
    if name not in root_docs:
        assert digest(Path(name)) == sha, name
        protected.append(name)
dump(RUN / 'results/timing_repeat_stability.json', timing)
dump(RUN / 'reviews/input_manifest.json', [dict(path=str(p), sha256=digest(p)) for p in sorted(inputs)])
dump(RUN / 'reviews/numeric_verification.json', dict(status='PASS', checks=checks,
     protected_files_unchanged=protected, input_files=len(inputs), new_search=0, new_training=0,
     new_gt=0, new_graph=0, timing_is_inherited_not_new_qps=True, descriptive_posthoc=True))
print(json.dumps(dict(status='PASS', checks=checks, timing=timing, protected_count=len(protected)), ensure_ascii=False, indent=2))
