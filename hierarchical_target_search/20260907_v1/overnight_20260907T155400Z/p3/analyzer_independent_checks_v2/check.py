from pathlib import Path
import copy, hashlib, importlib.util, json, sys
import numpy as np
sys.dont_write_bytecode = True
DEST = Path(__file__).resolve().parent
P3 = DEST.parent
SOURCE = P3 / 'analyze_p3.py'
EXPECTED_SHA = 'a840b060a61061df6e60ae6166cd9a090570ef6ec0002a3ec7c7deea14e4e03e'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED_SHA
spec = importlib.util.spec_from_file_location('independent_p3_review', SOURCE)
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
p2 = a.import_p2(); checks = []
def ok(name): checks.append({'name': name, 'status': 'PASS'})
def rejects(name, fn):
    try: fn()
    except (ValueError, KeyError) as e: checks.append({'name': name, 'status': 'PASS', 'error': str(e)})
    else: raise AssertionError(name + ' was not rejected')
artifacts, portals, n, d, nq, seed = a.synthetic_artifacts(p2)
a.verify_batches(artifacts['count'], artifacts['timing'], portals, n, d, seed, p2, nq=nq)
ok('valid_three_query_artifact_core')
rejects('default_requires_full10K_not_three_rows', lambda: a.verify_batches(artifacts['count'], artifacts['timing'], portals, n, d, seed, p2))
for name, mutate in [('query_order', lambda x: x['results'][0]['per_query'].reverse()),
                     ('missing_L_method', lambda x: x['results'].pop()),
                     ('duplicate_cell', lambda x: x['results'].append(copy.deepcopy(x['results'][0]))),
                     ('routing_MAC', lambda x: x['results'][0]['per_query'][0].update(routing_mac=123))]:
    bad = copy.deepcopy(artifacts['count']); mutate(bad)
    rejects(name, lambda: a.verify_batches(bad, artifacts['timing'], portals, n, d, seed, p2, nq=nq))
fixture = DEST / 'invocations'
execution = a.synthetic_invocations(fixture)
outputs = a.check_invocations(execution, fixture)
assert set(outputs) == {(model, kind) for model in a.MODELS for kind in ('count', 'timing')}
ok('all_eight_invocation_output_keys_after_shadow_fix')
for name, mutate in [('wrong_fast_ID_path', lambda x: x['invocations'][0]['command'].__setitem__(x['invocations'][0]['command'].index('--fast-ids') + 1, str(DEST / 'wrong_ids'))),
                     ('duplicate_flag', lambda x: x['invocations'][0]['command'].extend(['--threads', '16'])),
                     ('wrong_measurement_order', lambda x: x['invocations'].reverse())]:
    bad = copy.deepcopy(execution); mutate(bad)
    rejects(name, lambda: a.check_invocations(bad, fixture))
main = next(c for c in a.CONTRASTS if c[0] == 'structure_under_greedy3')
assert main[1:5] == ('lambda1_greedy3', 'oracle_probability', 'lambda0_greedy3', 'oracle_probability')
ok('fixed_main_direction')
assert len(a.CONTRASTS) == len({x[0] for x in a.CONTRASTS}) == 8
ok('exact_eight_contrast_family')
small = np.asarray([[0., .1, .2], [0., .1, .2], [.2, .1, 0.], [.2, .1, 0.], [.1, 0., .1], [.1, 0., .1], [.1, 0., .1], [.1, 0., .1]])
draws = p2.bootstrap_deltas(small, np.random.default_rng(a.SEED), 64)
indices = np.random.default_rng(a.SEED).integers(0, 3, size=(a.REPS, 3), dtype=np.int32)
manual = np.stack([row[indices].mean(axis=1) for row in small])
assert np.array_equal(draws, manual)
ok('all_eight_shared_draws_equal_independent_manual_indices')
records = {}
for model in a.MODELS:
    art, _, _, _, _, _ = a.synthetic_artifacts(p2)
    lam, greedy = int(model[6]), model.endswith('greedy3')
    for kind in ('count', 'timing'):
        for row in art[kind]['results']:
            method = row['method']
            recall = np.full(3, .9) if method == 'fast' else np.asarray([.1, .2, .3]) + lam * small[0] + int(greedy) * small[2] + int(method == 'oracle_probability') * small[4]
            row['mean_recall'] = float(recall.mean())
            if 'per_query' in row:
                for q, item in enumerate(row['per_query']): item['recall'] = float(recall[q])
        art[kind]['peak_rss_kib'] = 1; art[kind]['hnsw'] = {'build_seconds': .001}
    art['timing']['routing_only'] = [{'method': m, 'batch_wall_us': 100., 'num_queries': 3} for m in a.METHODS]
    records[model] = {'count': art['count'], 'timing': art['timing'], 'crows': a.cell_groups(art['count'], 'count'), 'trows': a.cell_groups(art['timing'], 'timing'), 'probe': {'cost_seconds': {}}}
summary = a.summarize('synthetic_three_queries', records, {}, DEST, np.random.default_rng(a.SEED), 64, p2)
assert len(summary['fixed_comparisons']) == 16
for row in summary['fixed_comparisons']:
    i = next(i for i, c in enumerate(a.CONTRASTS) if c[0] == row['contrast'])
    assert abs(row['recall_delta_pp'] - small[i].mean() * 100) < 1e-12
    if row['family'] == 'cross_model_2x2':
        assert row['QPS_comparison']['paired_round_ratios'] is None and row['QPS_comparison']['ratio_CI'] is None
    assert row['automatic_P3_GO'] is False and row['matched_cost_claim'] is False and row['oracle_diagnostic_only'] is True
ok('summarize_candidate_minus_reference_all16_cells')
ok('between_model_wall_descriptive_without_pairing_or_CI')
assert summary['stage_gate'] == 'REQUIRES_ROOT_STRUCTURE_AND_SEARCH_REVIEW' and summary['automatic_GO'] is False and summary['frontier_constructed'] is False and summary['online_performance_improvement_confirmed'] is False
ok('summary_no_automatic_gate_or_deployment_claim')
npz = np.load(DEST / 'bootstrap_synthetic_three_queries.npz')
for l in (64, 128):
    assert np.allclose(npz[f'L{l}_structure_under_frequency3'], npz[f'L{l}_structure_under_greedy3'], rtol=0, atol=1e-15)
    assert np.allclose(npz[f'L{l}_portals_under_lambda0'], npz[f'L{l}_portals_under_lambda1'], rtol=0, atol=1e-15)
    for model in a.MODELS[1:]:
        assert np.allclose(npz[f'L{l}_protection_{a.MODELS[0]}'], npz[f'L{l}_protection_{model}'], rtol=0, atol=1e-15)
ok('saved_npz_shared_draws_with_float_subtraction_tolerance')
report = {'status': 'PASS', 'checks': checks, 'check_count': len(checks), 'source_sha256': EXPECTED_SHA,
          'helper_sha256': hashlib.sha256(a.P2_HELPER.read_bytes()).hexdigest(), 'review_check_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'ANN_calls': 0, 'real_dataset_values_read': False, 'synthetic_query_count': 3, 'bootstrap_replicates': a.REPS,
          'scope': 'Independent pure artifact/contrast/shared-resampling checks; no full-dataset execution or performance result'}
with (DEST / 'report.json').open('x') as f: json.dump(report, f, indent=2); f.write('\n')
print(json.dumps({'status': 'PASS', 'checks': len(checks), 'report': str(DEST / 'report.json'), 'source': EXPECTED_SHA}))
