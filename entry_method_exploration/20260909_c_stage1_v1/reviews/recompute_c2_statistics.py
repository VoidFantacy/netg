#!/usr/bin/env python3
"""Independent final C2 audit: no producer import, ANN call, or non-train GT access."""
import csv
import datetime
import hashlib
import json
from pathlib import Path
import struct
import numpy as np

V = Path(__file__).resolve().parents[1]
OUT = V / 'reviews/c2_statistics_final_review.json'
assert not OUT.exists(), 'preserve prior review'
def read(p): return json.loads(Path(p).read_text())
def digest(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''): h.update(block)
    return h.hexdigest()
def equal(x, y, name):
    assert np.allclose(np.asarray(x), np.asarray(y), rtol=1e-12, atol=1e-14), name
def summarize(x):
    a = np.asarray(x, dtype=np.float64)
    keys = ['min','p25','p50','p75','p90','p95','p99','max']
    result = dict(zip(keys, np.percentile(a, [0,25,50,75,90,95,99,100]).tolist()))
    result['mean'] = float(np.mean(a))
    return result
def check_summary(a, reported, name):
    got = summarize(a)
    assert set(got) == set(reported), name
    equal(list(got.values()), [reported[k] for k in got], name)

cfg = read(V/'config.locked.json')
lock = read(V/'protocol_lock.json')
report = read(V/'results/analysis_v1/report.json')
assert digest(V/'config.locked.json') == lock['config_sha256']
assert digest(V/'protocol.md') == lock['protocol_sha256']
assert digest(V/'protocol_lock.json') == report['protocol_lock_sha256']
assert digest(V/'src/score_c2.py') == report['scorer_sha256']
for rec in lock['bound_files']: assert digest(rec['path']) == rec['sha256']
names = ['continue'] + [f'natural_{i}' for i in range(4)] + [f'force_{i}' for i in range(4)]
datasets = [('webvid2_5m_light_v1','c2_main_webvid_v1'), ('yandex_t2i_official10M_ip_v1','c2_main_yandex_v1')]
raw_cache = {}
input_evidence = []
for ds, label in datasets:
    directory = V/'results'/label
    done, meta = read(directory/'complete.json'), read(directory/'metadata.json')
    assert done['status'] == meta['status'] == 'COMPLETE' and done['queries'] == 2000 and done['rows'] == 4000
    assert done['GT_accessed'] is False and meta['GT_accessed'] is False and meta['quality_scoring'] is False
    assert done['dataset'] == meta['dataset'] == ds and meta['locked_config'] == cfg
    raw = [json.loads(line) for line in (directory/'branches.jsonl').open()]
    assert len(raw) == 4000
    provenance = next(p for p in report['scoring_provenance'] if p['dataset'] == ds)
    assert digest(directory/'branches.jsonl') == provenance['raw_sha256']
    raw_cache[ds] = raw
    input_evidence.append({'dataset':ds, 'raw_sha256':provenance['raw_sha256'], 'raw_rows':4000})

# Both complete raw datasets have been checked before the first GT seek/read.
points = []
logical_branches = prefix_states = returned_ids = 0
total_physical = 0
for ds, label in datasets:
    c = read(V/'inputs'/ds/'config.json')
    row_ids = np.fromfile(V/'inputs'/ds/'row_ids.i64', dtype='<i8')
    expected = np.random.Generator(np.random.PCG64(20260909)).permutation(10000)[:2000]
    assert np.array_equal(row_ids, expected) and len(set(row_ids)) == 2000
    path = Path(c['gt_train_path'])
    assert 'router_train' in path.name and all(x not in path.name.lower() for x in ['validation','held','test'])
    targets = []
    gt_digest = hashlib.sha256()
    # Read only dimension header and exact top10 IDs for the authorized 2000 rows.
    with path.open('rb') as gt:
        for qid in row_ids:
            gt.seek(int(qid)*101*4)
            row = gt.read(44)
            width, *ids = struct.unpack('<11i', row)
            assert width == 100 and len(set(ids)) == 10 and min(ids) >= 0 and max(ids) < c['base_count']
            targets.append(set(ids)); gt_digest.update(struct.pack('<q', int(qid)) + row)
    saved = np.load(V/'results/analysis_v1'/(ds+'_aligned.npz'), allow_pickle=False)
    csv_rows = list(csv.DictReader((V/'results/analysis_v1'/(ds+'_per_query.csv')).open()))
    assert len(csv_rows) == 4000
    raw = raw_cache.pop(ds)
    physical = 0
    for L in [64,128]:
        rows = [r for r in raw if r['L'] == L]
        assert len(rows) == 2000
        published = next(p for p in report['points'] if p['dataset'] == ds and p['L'] == L)
        hit = np.empty((2000,9), dtype=np.int16)
        ndc = np.empty((2000,9), dtype=np.int64)
        suffix = np.empty_like(ndc)
        for i, r in enumerate(rows):
            assert r['sample_index'] == i and r['row_id'] == int(row_ids[i]) and r['K'] == 10 and r['B'] == cfg['B']
            assert r['checkpoint'] == cfg['checkpoint_completed_expansions'][str(L)]
            assert len(r['branches']) == 9 and [b['action'] for b in r['branches']] == names
            state = read(V/'results'/label/r['prefix_state']); prefix_states += 1
            assert state['L'] == L and state['K'] == 10 and state['query_id'] == int(row_ids[i])
            assert state['ndc'] == r['prefix_ndc'] and state['completed_expansions'] == r['prefix_completed_expansions']
            assert state['natural_finished'] == r['early_finished'] and state['row_active'] is False
            assert state['initial_entries'] == r['initial_entries']
            visited, expanded = set(state['visited']), set(state['expanded'])
            assert len(visited) == len(state['visited']) and len(expanded) == len(state['expanded'])
            candidates = r['candidate_ids']; assert len(candidates) == 4
            valid_candidates = [e for e in candidates if e >= 0]
            assert len(set(valid_candidates)) == len(valid_candidates)
            assert not (set(valid_candidates) & set(r['initial_entries']))
            physical += 2  # counted and plain prefix
            for a, b in enumerate(r['branches']):
                logical_branches += 1; returned_ids += len(b['ids'])
                assert len(b['ids']) == len(b['distances']) == 10
                assert len(set(b['ids'])) == 10 and min(b['ids']) >= 0 and max(b['ids']) < c['base_count']
                assert np.isfinite(b['distances']).all() and np.all(np.diff(b['distances']) >= 0)
                hit[i,a] = sum(node in targets[i] for node in b['ids'])
                ndc[i,a], suffix[i,a] = b['graph_ndc'], b['suffix_graph_ndc']
                assert ndc[i,a] == r['prefix_ndc'] + suffix[i,a]
                assert 0 <= suffix[i,a] <= cfg['B'] and b['remaining'] == cfg['B'] - suffix[i,a]
                assert b['limit'] == r['prefix_ndc'] + cfg['B'] and b['natural_finished'] != b['cap_exhausted']
                assert len(b['expanded_suffix']) == len(set(b['expanded_suffix']))
                assert b['expanded_count'] == state['started_expansions'] + len(b['expanded_suffix'])
                assert not (expanded & set(b['expanded_suffix']))
                if a:
                    slot = (a-1)%4; e = candidates[slot]
                    why = ('early_finished' if state['natural_finished'] else 'invalid_or_empty' if e < 0 or e >= c['base_count'] else 'visited' if e in visited else 'expanded' if e in expanded else 'eligible')
                    assert b['slot'] == slot and b['candidate'] == e and b['eligibility'] == why
                    if why != 'eligible':
                        for key in ['ids','distances','graph_ndc','suffix_graph_ndc','expanded_suffix','natural_finished','cap_exhausted']:
                            assert b[key] == r['branches'][0][key]
                        assert not b['effective_action'] and not b['physical_branch_executed']
                    else:
                        assert b['physical_branch_executed'] and suffix[i,a] >= 1
                        if a >= 5: assert b['expanded_suffix'].count(e) == 1
                if b['physical_branch_executed']: physical += 2
                if r['early_finished']: assert suffix[i,a] == 0 and b['natural_finished']

        # Reconstruct quality choices independently as ordered Python max operations.
        choice = np.array([max([0,5,6,7,8], key=lambda a: int(h[a])) for h in hit])
        natural_choice = np.array([max([0,1,2,3,4], key=lambda a: int(h[a])) for h in hit])
        index = np.arange(2000); delta_hits = hit[index,choice] - hit[:,0]
        assert np.all(delta_hits >= 0) and np.all(choice[delta_hits == 0] == 0)
        delta = delta_hits.astype(float)/10
        mean = float(np.sum(delta_hits)/(2000*10))
        # Different batch size from the producer; same frozen PCG64 stream.
        rng = np.random.Generator(np.random.PCG64(20260909)); boot = np.empty(20000)
        for off in range(0,20000,500):
            draws = rng.integers(0,2000,size=(500,2000))
            boot[off:off+500] = delta[draws].mean(axis=1)
        ci = np.percentile(boot,[0.625,99.375]); ordinary = np.percentile(boot,[2.5,97.5])
        assert np.array_equal(hit, saved[f'L{L}_hitcount'])
        assert np.array_equal(ndc, saved[f'L{L}_ndc'])
        assert np.array_equal(choice, saved[f'L{L}_oracle_action'])
        assert np.array_equal(boot, saved[f'L{L}_bootstrap'])
        equal(mean,published['primary']['mean'],'primary mean')
        equal(ci,published['primary']['ci_bonferroni4_family95'],'corrected CI')
        equal(ordinary,published['primary']['ci95'],'ordinary CI')
        assert int(delta_hits.sum()) == published['integer_gain_hits'] and published['gate_required_gain_hits'] == '100'
        equal(hit[:,0].mean()/10,published['continue_recall'],'continue recall')
        equal(hit[index,choice].mean()/10,published['oracle_recall'],'oracle recall')
        fractions = {names[a]:float(np.mean(choice == a)) for a in [0,5,6,7,8]}
        equal(list(fractions.values()), [published['oracle_action_fractions'][k] for k in fractions], 'choice fractions')
        for a,name in enumerate(names):
            equal(hit[:,a].mean()/10,published['all_actions_recall'][a]['mean'],name+' recall')
            equal((hit[:,a]-hit[:,0]).mean()/10,published['all_actions_recall'][a]['delta_vs_continue'],name+' delta')
            cost = published['ndc']['branches'][name]
            check_summary(ndc[:,a],cost['graph_ndc'],name+' NDC')
            check_summary(suffix[:,a],cost['suffix_graph_ndc'],name+' suffix NDC')
            check_summary([r['branches'][a]['plain_wall_seconds'] for r in rows],cost['plain_branch_seconds'],name+' wall')
            equal(np.mean([r['branches'][a]['natural_finished'] for r in rows]),cost['natural_finished_fraction'],name+' terminal')
            equal(np.mean([not r['branches'][a]['physical_branch_executed'] for r in rows]),cost['plain_wall_alias_fraction'],name+' alias')
        mechanism = {
            'per_slot_force_minus_same_natural_mean':((hit[:,5:9]-hit[:,1:5]).mean(axis=0)/10).tolist(),
            'natural_oracle_delta_vs_continue':float((hit[index,natural_choice]-hit[:,0]).mean()/10),
            'force_oracle_minus_natural_oracle':float((hit[index,choice]-hit[index,natural_choice]).mean()/10),
            'force_oracle_winner_minus_its_same_candidate_natural':float((hit[index,choice]-hit[index,np.where(choice == 0,0,choice-4)]).mean()/10)}
        for key,value in mechanism.items(): equal(value,published['mechanism'][key],key)
        oracle_ndc = ndc[index,choice]
        for value,key in [(oracle_ndc,'oracle_graph_ndc'), (suffix[index,choice],'oracle_suffix_graph_ndc'), (ndc.min(axis=1),'per_query_envelope_min'), (ndc.max(axis=1),'per_query_envelope_max')]:
            check_summary(value,published['ndc'][key],key)
        cost_ratio = float(oracle_ndc.mean()/ndc[:,0].mean()-1)
        equal(cost_ratio,published['ndc']['oracle_vs_continue_ratio_of_means_minus_one'],'NDC ratio')
        eligible = np.array([[b['eligibility']=='eligible' for b in r['branches'][5:9]] for r in rows])
        effective = np.array([[b['effective_action'] for b in r['branches'][5:9]] for r in rows])
        early = np.array([r['early_finished'] for r in rows]); noeligible = ~eligible.any(axis=1)
        selected_effective = np.array([r['branches'][a]['effective_action'] for r,a in zip(rows,choice)])
        coverage = {'denominator':2000,'early_finished_fraction':float(early.mean()),'no_eligible_fraction':float(noeligible.mean()),
            'no_eligible_among_non_early_fraction_of_all':float((noeligible & ~early).mean()),'any_eligible_fraction':float(eligible.any(axis=1).mean()),
            'any_effective_force_fraction':float(effective.any(axis=1).mean()),'all_force_no_op_fraction':float((~effective.any(axis=1)).mean()),
            'oracle_strict_quality_gain_fraction':float((delta_hits>0).mean()),'oracle_selected_effective_fraction':float(selected_effective.mean()),
            'per_slot_eligible_fraction':eligible.mean(axis=0).tolist(),
            'per_slot_visited_fraction':[float(np.mean([r['branches'][a]['eligibility']=='visited' for r in rows])) for a in range(5,9)],
            'per_slot_no_op_fraction':(~effective).mean(axis=0).tolist()}
        for key,value in coverage.items(): equal(value,published['coverage'][key],key)
        for key in published['bookkeeping']: check_summary([r[key] for r in rows],published['bookkeeping'][key],key)
        check_summary([b['clone_seconds'] for r in rows for b in r['branches'] if b['physical_branch_executed']],published['clone_seconds_physical_branches'],'clone')
        check_summary([sum(b['alias_materialization_seconds'] for b in r['branches']) for r in rows],published['alias_materialization_seconds_per_query'],'alias materialization')
        for key,field in [('Fast3_NDC','route3_ndc'),('candidate_top7_NDC','route7_candidate_ndc'),('Fast3_wall_seconds','route3_wall_seconds'),('candidate_wall_seconds','route7_wall_seconds')]:
            check_summary([r[field] for r in rows],published['routing'][key],key)
        assert sum(not r['direct_top3_equals_top7_prefix'] for r in rows) == published['routing']['top3_top7_prefix_mismatch_count']
        selected_csv = [r for r in csv_rows if int(r['L']) == L]
        assert len(selected_csv) == 2000
        for i,row in enumerate(selected_csv):
            assert int(row['sample_index']) == i and int(row['row_id']) == row_ids[i] and row['oracle_action'] == names[choice[i]]
            for key,value in [('continue_recall',hit[i,0]/10),('oracle_recall',hit[i,choice[i]]/10),('delta',delta[i]),('oracle_ndc',oracle_ndc[i]),('continue_ndc',ndc[i,0]),('envelope_min',ndc[i].min()),('envelope_max',ndc[i].max())]:
                equal(float(row[key]),value,'CSV '+key)
            assert row['early_finished'] == str(bool(early[i])) and row['no_eligible'] == str(bool(noeligible[i]))
        passed = bool(delta_hits.sum() >= 100 and ci[0] > 0 and selected_effective.any() and np.all(suffix <= cfg['B']))
        assert passed == published['gate_pass'] and published['N'] == 2000
        points.append({'dataset':ds,'L':L,'N':2000,'gain_hits':int(delta_hits.sum()),'mean_delta_pp':mean*100,
            'corrected_ci_pp':(ci*100).tolist(),'gate_pass':passed,'coverage':coverage,'oracle_action_fractions':fractions,
            'mechanism':mechanism,'continue_graph_ndc_mean':float(ndc[:,0].mean()),'oracle_graph_ndc_mean':float(oracle_ndc.mean()),
            'oracle_vs_continue_NDC_ratio_minus_one':cost_ratio,'all_branch_suffix_NDC_min_max':[int(suffix.min()),int(suffix.max())],
            'actual_total_NDC_envelope_min_max':[int(ndc.min()),int(ndc.max())],
            'queries_with_unequal_branch_NDC':int(np.sum(np.ptp(ndc,axis=1)>0)),
            'continue_cap_exhausted_count':sum(r['branches'][0]['cap_exhausted'] for r in rows),
            'all_20000_bootstrap_values_exactly_reproduced':True})
    done = read(V/'results'/label/'complete.json')
    assert physical == done['physical_search_executions']; total_physical += physical
    next(e for e in input_evidence if e['dataset']==ds).update({'authorized_train_GT_top10_rows_read':2000,
        'sampled_GT_records_sha256':gt_digest.hexdigest(),'physical_prefix_and_branch_executions':physical})

assert logical_branches == 72000 and prefix_states == 8000 and returned_ids == 720000
assert not all(p['gate_pass'] for p in points) and report['decision'] == 'NO_GO_UNCONDITIONAL_HEADROOM_STOP_C'
score_command = read(V/'logs/c2_offline_score_v1.command.json')
for ds,label in datasets:
    command = read(V/'logs'/(label+'.command.json'))
    assert command['finished_utc'] < score_command['started_utc'] and command['exit_code'] == 0
c2_logs = [read(p) for p in (V/'logs').glob('c2_*.command.json')]
wall = sum(r['wall_seconds'] for r in c2_logs)
peak = max(r.get('peak_rss_bytes',0) for r in c2_logs)
disk = sum(p.stat().st_size for p in V.rglob('*') if p.is_file())
assert wall < 7200 and peak <= 32*1024**3 and disk < 5*1024**3
result = {'status':'PASS','decision':'C2_STATISTICS_FINAL_REVIEW_PASS_ACCEPT_STOP_C','reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'method_decision':report['decision'],'primary_all_four_pass':False,'points':points,
    'verification':{'raw_rows':8000,'logical_branches':logical_branches,'returned_ID_memberships_recomputed':returned_ids,
        'saved_prefix_states_checked':prefix_states,'physical_main_prefix_and_branch_executions':total_physical,
        'all_GT_hitcounts_equal_NPZ':True,'all_oracle_choices_equal_NPZ':True,'all_CSV_values_match':True,
        'all_cost_coverage_mechanism_bookkeeping_summaries_match':True,'both_raw_complete_before_scoring':True,
        'validation_or_heldout_accessed':False,'new_ANN_or_model_runs':0,'GT_rows_accessed_per_dataset':2000},
    'resource_observations':{'all_recorded_C2_command_wall_seconds':wall,'max_recorded_C2_RSS_bytes':peak,'artifact_bytes_at_review':disk},
    'inputs':input_evidence,'report_sha256':digest(V/'results/analysis_v1/report.json'),'audit_script_sha256':digest(__file__),
    'limitations':['2000 historical training-development queries per dataset, retained unconditionally','one fixed paired build, not build-level uncertainty',
        'GT-privileged finite-action headroom, not a learned policy','common cap differs from actual equal work','natural-winner comparisons remain descriptive',
        'bookkeeping/branch wall is not formal method QPS','C3/C4 remain unrun; no expansion or retuning follows this failure']}
OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'status':result['status'],'decision':result['method_decision'],'points':[{k:p[k] for k in ['dataset','L','gain_hits','mean_delta_pp','corrected_ci_pp','gate_pass']} for p in points],
    'verified_branches':logical_branches,'physical_main_calls':total_physical},indent=2))
