from shared import *
import re,ast
threads(8);resources();started=time.monotonic()
for name in ['protected.json','native_dependencies.json','prequery_freeze.json']:check(O/'reviews'/name)
protected=read(O/'reviews/protected.json')['files']
assert {x['path'] for x in protected}=={str(p) for root in OLD for p in files(root)}
verification=read(O/'reviews/training_verification.json');assert verification['status']=='PASS'
cache=read(O/'reviews/environment_cache_relocation.json')
assert cache['status']=='PASS' and cache['experiment_artifacts_removed']==0 and cache['source_and_native_unchanged']
assert sha(cache['archive'])==cache['archive_sha256']
assert verification['updates']==1600 and verification['scored']==1978368 and verification['candidate_W_hashes']==12800
assert verification['checkpoints']==88 and verification['selected_last_models']==16
jobs=read(O/'logs/jobs.json');assert len(jobs)==10 and len({j['name'] for j in jobs})==10
assert all(j['status']=='COMPLETE' for j in jobs)
assert sum(j['actual'] for j in jobs)==1992256 and sum(j['reserved'] for j in jobs)==1993440<=CAP
assert sum(j['native']['HNSW_calls'] for j in jobs)==1991104
assert sum(j['native']['builds'] for j in jobs)==sum(j['reserved_builds'] for j in jobs)==14510<=15000
for i,j in enumerate(jobs):
 assert j.get('actual_threads',j['native'].get('actual_threads'))==1
 assert j['actual']==(5408 if j['name'].startswith('preflight_') else 247680)
 if i:assert jobs[i-1]['completed_at']<=j['started_at']
 path=Path('/proc')/str(j['pid'])/'cmdline'
 if path.exists():assert str(O/'src/train.py').encode() not in path.read_bytes() and str(O/'src/preflight.py').encode() not in path.read_bytes()
models=read(O/'results/training_analysis.json')['models'];gate=read(O/'results/method_gate.json')
assert len(models)==8 and {tuple(m[k] for k in ['dataset','arm','seed']) for m in models}=={(ds,arm,seed) for ds in DS for arm in ARMS for seed in SEEDS}
for ds in DS:
 config=read(O/'inputs'/ds/'config.json');old=read(E37/'inputs'/ds/'config.json')
 assert config['native_call_cap']==1000000 and all(v==old[k] for k,v in config.items() if k!='native_call_cap')
 done=read(O/'results'/ds/'training_complete.json');assert done['status']=='PASS' and done['runs']==4 and done['updates']==800
 assert done['native']['NSG_calls']==990720 and done['native']['builds']==7252 and done['native']['actual_threads']==1
 eligible={arm:[m['seed'] for m in models if m['dataset']==ds and m['arm']==arm and m['selected_monitor']['delta_recall_pp']>0 and m['selected_monitor']['mean_U']>0 and m['selected_monitor']['graph_NDC_change_pct']<=1] for arm in ARMS}
 got=next(x for x in gate['datasets'] if x['dataset']==ds);assert got['eligible_seeds']==eligible and got['pass_monitor_gate']==all(eligible.values())
 for arm in ARMS:
  for seed in SEEDS:
   path=O/'models'/ds/f'{arm}_{seed}';assert len(list((path/'trajectory').glob('*.npz')))==200 and len(list((path/'checkpoints').glob('*.npz')))==11
   for tag in ['selected','last']:
    folder=path/tag;ident=read(folder/'identity.json')
    assert sha(folder/'W.f32')==ident['W_sha'] and sha(folder/'graph.hnsw')==ident['graph_sha'] and sha(folder/'mu.f64')==ident['mu_sha']
    assert ident['parity']=='PASS' and (folder/'parity.npz').exists()
expected='GO_FREEZE_DEVELOPMENT_PROTOCOL' if all(x['pass_monitor_gate'] for x in gate['datasets']) else 'STOP_THIS_PARAMETERIZATION_BUDGET_EXPANSION'
assert gate['status']==expected and gate['new_development_queries']==0 and not gate['formal_performance_GO']
for name,count in [('steps.csv',1600),('training_models.csv',8),('feedback.csv',8),('quality.csv',32)]:
 with (O/'results'/name).open() as f:assert sum(1 for _ in csv.DictReader(f))==count
assert read(O/'reviews/visual_review.json')['status']=='PASS'
for name in ['learning_curves','feedback_coverage']:
 for ext in ['png','svg','pdf']:assert (O/'figures'/(name+'.'+ext)).stat().st_size>1000
docs=[R/n for n in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/32_local_profile_rl.md']]+list(O.glob('*.md'))
links=0;forward={O/'reviews/final_audit.json',O/'reviews/completion_audit.json'}
for doc in docs:
 for target in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
  if '://' in target or target.startswith('#'):continue
  p=(doc.parent/target.split('#')[0]).resolve();assert p.exists() or p in forward,(str(doc),target)
  links+=1
for file in (O/'src').glob('*.py'):ast.parse(file.read_text(),filename=str(file))
assert 'E43' in (R/'s-target.md').read_text() and '训练正在运行' not in (R/'s-target.md').read_text()
requirements=[
 ('new_local_action_implemented','frozen single-row H x 16 parameterization, current-background native search and preflight'),
 ('GT_free_independent_matched_schedule','all 1600 schedule rows replayed from original seeds and independent baseline-entry draws'),
 ('RL_ES_same_budget_and_representation','two arms/two seeds/two datasets, each 200 updates/247680 calls/1813 builds'),
 ('full_eight_training_runs','8 terminal model.json and 1600 trajectory files, 88 checkpoints'),
 ('actual_whole_batch_counterfactual_feedback','1978368 complete outputs independently set-scored; native call ledger and before/current/candidate arrays'),
 ('correct_reward_and_mean_updates','all Delta J, gradient components, LOO/ES, row counters/Adam/state replayed'),
 ('preserve_baseline_cancellation_limit','preflight identity plus explicit protocol/report disclosure'),
 ('deterministic_export_and_model_selection','all monitor choices replayed,16 W/physical graphs and 1024-query three-way parity'),
 ('full_positive_negative_and_signal_diagnosis','32 quality rows,8 models,1600 step feedback records and derived plots'),
 ('preregistered_monitor_gate','both datasets/arms eligibility recomputed; no result-dependent threshold change'),
 ('single_thread_serial_bounded_execution','actual threads1,nonoverlapping complete ledger; NSG/build caps and deadline checks'),
 ('old_sources_and_artifacts_preserved','E37-E42 complete SHA/path sets and native/NSG dependencies unchanged'),
 ('no_unauthorized_scope_substitution','0 new GT/development/QPS/validation/held-out; unchanged default'),
 ('reviewable_delivery','report/history32/root docs, plots opened visually, all local links resolve'),
 ('ongoing_user_goal_preserved','stage closes separately from the persistent 20:00 campaign')]
dump(O/'reviews/completion_audit.json',dict(status='PASS',objective='E43 local-profile policy-search stage',requirements=[dict(requirement=k,status='PROVEN',evidence=v) for k,v in requirements],unresolved_requirements=[],campaign_complete=False))
state='COMPLETE_LOCAL_PROFILE_RL_'+('MONITOR_SIGNAL' if expected.startswith('GO_') else 'STOP_MONITOR_GATE')
dump(O/'state.json',dict(status=state,completed_at=time.time(),NSG_calls=1992256,HNSW_calls=1991104,builds=14510,optimizer_updates=1600,
 default_changed=False,new_GT=0,new_development=0,new_validation_heldout_raw_access=False,queued_jobs=0,monitor_gate=expected,campaign_complete=False))
sync=read(O/'reviews/document_sync.json');assert not sync['next_target_requires_update'];sync['status']='PASS';dump(O/'reviews/document_sync.json',sync)
audit=dict(status='PASS',NSG_calls=1992256,HNSW_calls=1991104,builds=14510,optimizer_updates=1600,training_verification=verification,
 protected_files=len(protected),requirements=len(requirements),local_links=links,regenerable_cache_archive='verified',artifact_bytes=sum(p.stat().st_size for p in files(O)),seconds=time.monotonic()-started)
dump(O/'reviews/final_audit.json',audit);freeze(O/'reviews/final_artifact_freeze.json',files(O)+docs)
print(json.dumps(audit,ensure_ascii=False,indent=2))
