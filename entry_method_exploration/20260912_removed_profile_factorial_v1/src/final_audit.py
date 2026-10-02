from shared import *
import re,ast
threads(8);resources();start=time.monotonic()
for name in ['protected.json','native_dependencies.json','prequery_freeze.json']:check(O/'reviews'/name)
old_roots=[E37,E38,E39,E40,E41];protected=read(O/'reviews/protected.json')['files']
assert {x['path'] for x in protected}=={str(p) for root in old_roots for p in files(root)}
locked=read(O/'config.locked.json');jobs=read(O/'logs/jobs.json');d=read(O/'results/diagnosis.json')
v=read(O/'reviews/independent_verification.json');a=read(O/'reviews/attribution_verification.json')
assert len(jobs)==2 and [j['dataset'] for j in jobs]==DS
assert all(j['status']=='COMPLETE' and j['actual']==4288 and j['native']['actual_threads']==1 for j in jobs)
assert jobs[0]['completed_at']<jobs[1]['started_at']
assert sum(j['actual'] for j in jobs)==sum(j['reserved'] for j in jobs)==locked['expected_NSG']==8576
assert locked['hard_NSG_cap']==10000 and sum(j['reserved'] for j in jobs)<=10000
assert sum(j['native']['HNSW_calls'] for j in jobs)==8448 and sum(j['native']['builds'] for j in jobs)==8
for j in jobs:
 p=Path('/proc')/str(j['pid'])/'cmdline'
 if p.exists():assert str(O/'src/run.py').encode() not in p.read_bytes()
assert v['status']=='PASS' and v['set_scored']==8192 and v['old_full_regression']==4096
assert v['parity_rows']==128 and v['W_constructions']==8 and v['interaction_queries']==2048
assert a['status']=='PASS' and a['credit_queries_all_three_channels']==2048 and a['metrics_checked']==8 and a['E41_CF_regression']==4096
assert read(O/'reviews/credit_verification.json')['status']=='PASS'
assert read(O/'reviews/visual_review.json')['status']=='PASS'
assert d['actual_NSG']==8576 and d['optimizer_updates']==locked['optimizer_updates']==0
original_cases=read(E40/'results/attribution_cases.json')['cases']
for ds in DS:
 ca=case(ds);old=next(x for x in original_cases if x['dataset']==ds)
 assert ca['observations']==old['observations'] and ca['context']==old['context'] and ca['action']==old['action']
 assert ca['original_added_hub']==old['hub'] and ca['target_selection']=='unique_removed_hub_in_frozen_negative'
 neg=next(x for x in old['observations'] if int(x['delta_hits'])<0)
 removed=set(map(int,neg['center_entries'].split(';')))-set(map(int,neg['action_entries'].split(';')))
 assert removed=={ca['hub']} and ca['hub']==dict(zip(DS,[1627796,8309868]))[ds]
 c=cfg(ds);assert c['threads']==1 and c['query_cpu']==15 and c['native_call_cap']==4288
 original_cfg=read(E39/'inputs'/ds/'config.json')
 assert all(value==original_cfg[key] for key,value in c.items() if key!='native_call_cap')
 for cell in CELLS:
  p=O/'models'/ds/cell;ident=read(p/'identity.json');construction=read(p/'construction.json')
  assert ident['original_parity']=='PASS' and sha(p/'W.f32')==ident['W_sha']==construction['W_sha']
  assert sha(p/'graph.hnsw')==ident['graph_file_sha'] and (p/'parity.npz').exists()
  if cell in ['C','F']:
   assert ident['E39_regression']=='PASS' and ident['topology_sha']==construction['expected_topology_sha']
   assert ident['graph_file_sha']==construction['expected_graph_sha']
  assert (O/'results'/ds/(cell+'.npz')).exists()
 for j,expected in enumerate(['C','F','S','R']):
  m=next(x for x in d['metrics'] if x['dataset']==ds and x['cell']==expected)
  raw=dict(np.load(O/'results'/ds/(expected+'.npz')))
  assert len(raw['rows'])==1024
# Assert the report's central findings directly from independently scored raw results.
expected_hits=[[9,0,9,9],[10,0,0,0]]
expected_gl=[[(0,0),(22,52),(0,1),(22,42)],[(0,0),(20,23),(0,10),(20,23)]]
for di,ds in enumerate(DS):
 ca=case(ds);neg=next(x for x in ca['observations'] if int(x['delta_hits'])<0);qi=int(neg['qi'])
 der=dict(np.load(O/'results'/ds/'derived.npz'))
 assert list(map(int,der['hits'][:,qi]))==expected_hits[di]
 assert int(np.count_nonzero(der['interaction']))==1 and int(der['interaction'][qi])==[-9,10][di]
 for ci,cell in enumerate(CELLS):
  m=next(x for x in d['metrics'] if x['dataset']==ds and x['cell']==cell)
  assert (m['gain_hits'],m['loss_hits'])==expected_gl[di][ci]
 assert a['cases'][di]['target_row_change_sufficient']==[False,True][di]
 assert a['cases'][di]['target_row_change_necessary_in_full_background']==[True,False][di]
 assert a['cases'][di]['R_never_worse_than_F'] and a['cases'][di]['R_preserves_all_F_gains']
assert a['cases'][0]['S_C_same_output_bits'] and a['cases'][0]['target_removed_in_S']
docs=[R/p for p in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md',
 'experiment_history/README.md','experiment_history/31_removed_profile_factorial.md']]+list(O.glob('*.md'))
forward={O/'reviews/final_audit.json',O/'reviews/completion_audit.json'};links=0
for doc in docs:
 text=doc.read_text();assert all(line.rstrip()==line for line in text.splitlines()),doc
 for target in re.findall(r'\]\(([^)]+)\)',text):
  if '://' in target or target.startswith('#'):continue
  p=(doc.parent/target.split('#')[0]).resolve();assert p.exists() or p in forward,(doc,target)
  links+=1
for file in (O/'src').glob('*.py'):ast.parse(file.read_text(),filename=str(file))
for name,count in [('metrics.csv',8),('queries.csv',2048),('cases.csv',16),('credit.csv',2048)]:
 with (O/'results'/name).open() as f:assert sum(1 for _ in csv.DictReader(f))==count
for prefix in ['whole_pool','frozen_cases']:
 for ext in ['png','svg','pdf']:assert (O/'figures'/(prefix+'.'+ext)).stat().st_size>1000
decision=(O/'reward_decision.md').read_text()
for required in ['r_B(W→W\')','NDC_anchor','D(W\')−D(W)','完整同批查询','单独不充分','恢复目标并不能救回','未实施']:
 assert required in decision,required
for doc in ['summary.md','spec.md','s-target.md','s-experiment.md']:
 assert 'E42' in (R/doc).read_text()
assert '三十一份详细卡片' in (R/'s-experiment.md').read_text()
requirements=[
 ('locked_removed_profile_identity','config.locked; original E40 negative-entry set difference and unchanged observations'),
 ('same_full_query_pool_and_C_F','original E39 configs/1024 rows; 4096 E39 and 4096 E41 bit regressions'),
 ('actual_four_cells_two_datasets','8 W/physical HNSW graphs, raw arrays and bytewise row construction verification'),
 ('sufficiency_and_necessity_separate','independent negative-case 9/0/9/9 and 10/0/0/0; four boolean conditions checked'),
 ('actual_entry_and_output_mechanism','case entries and raw bits; WebVid removal without hit loss and Yandex duplicate bad routes'),
 ('all_query_gain_and_damage','8192 independently scored outputs, all 8 G/L/zero-event/NDC tables verified'),
 ('conditional_credit_and_interactions','2048 hits/U/J marginals and accounting identities; nonzero interactions checked'),
 ('concrete_RL_reward_decision','reward_decision.md exact original-objective paired Delta J, batch/background and action-parameterization limits'),
 ('honest_causal_limits','report distinguishes conditional necessity/sufficiency, overlapping harm, partition limits; no unique all-H cause or generalization claim'),
 ('ordinary_native_and_parity','unchanged native dependencies; 128-query serialized/plain/original-kernel parity'),
 ('bounded_serial_single_thread_cost','8576 NSG / 8448 HNSW / 8 builds, reserved cap10000, actual threads1 and nonoverlapping jobs'),
 ('no_new_training_or_evaluation_scope','copied W rows; no optimizer/GT path; original train-only native query configs'),
 ('old_artifacts_preserved','SHA and exact pathname sets for E37-E41 and native/NSG dependencies'),
 ('report_figures_and_document_sync','report/reward document, 2 visually inspected figures in 3 formats, history31/four root docs and links'),
 ('terminal_execution','both process handles collected exit0; saved job PIDs no live runner; no queued jobs')]
dump(O/'reviews/completion_audit.json',dict(status='PASS',objective='Determine responsibility of the removed-entry profiles in the frozen negative cases and decide RL credit allocation',
 scope='two specified removed-profile controls, all queries, contextual attribution and concrete reward design',
 requirements=[dict(requirement=k,status='PROVEN',evidence=e) for k,e in requirements],unresolved_requirements=[],
 acknowledged_unmeasured=['individual hubs inside the rest block','score versus rebuilt adjacency','new learner and generalization'],new_training='NOT_PART_OF_THIS_DIAGNOSTIC_AND_DESIGN_GOAL'))
state='COMPLETE_REMOVED_PROFILE_ATTRIBUTION_CONTEXT_DEPENDENT_CREDIT'
dump(O/'state.json',dict(status=state,completed_at=time.time(),NSG_calls=8576,HNSW_calls=8448,builds=8,
 optimizer_updates=0,new_GT=0,new_validation_heldout_raw_access=False,default_changed=False,queued_jobs=0,
 diagnosis='WEBVID_NECESSARY_NOT_SUFFICIENT_YANDEX_SUFFICIENT_NOT_NECESSARY',
 reward_decision='CONTEXTUAL_PAIRED_LOCAL_DELTA_J_DESIGNED_NOT_TRAINED'))
sync=read(O/'reviews/document_sync.json');sync['status']='PASS';dump(O/'reviews/document_sync.json',sync)
audit=dict(status='PASS',protected_files=len(protected),protected_counts={p.name:len(files(p)) for p in old_roots},
 NSG_calls=8576,HNSW_calls=8448,builds=8,optimizer_updates=0,independent_verification=v,
 contextual_credit_verification=a,completion_requirements=len(requirements),local_links=links,
 artifact_bytes=sum(p.stat().st_size for p in files(O)),seconds=time.monotonic()-start)
dump(O/'reviews/final_audit.json',audit);freeze(O/'reviews/final_artifact_freeze.json',files(O)+docs)
print(json.dumps({k:v for k,v in audit.items() if k!='contextual_credit_verification'},ensure_ascii=False,indent=2))
