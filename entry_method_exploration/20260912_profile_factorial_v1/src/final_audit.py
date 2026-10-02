from shared import *
import re
threads(8);resources();start=time.monotonic()
for file in ['protected.json','native_dependencies.json','prequery_freeze.json']:check(O/'reviews'/file)
protected=read(O/'reviews/protected.json')['files']
assert {x['path'] for x in protected}=={str(p) for root in [E37,E38,E39,E40] for p in files(root)}
locked=read(O/'config.locked.json');jobs=read(O/'logs/jobs.json');d=read(O/'results/diagnosis.json')
v=read(O/'reviews/independent_verification.json')
assert len(jobs)==2 and {j['dataset'] for j in jobs}==set(DS)
assert all(j['status']=='COMPLETE' and j['actual']==4288 and j['native']['actual_threads']==1 for j in jobs)
assert sum(j['actual'] for j in jobs)==locked['expected_NSG']==8576
assert sum(j['reserved'] for j in jobs)==8576<=locked['hard_NSG_cap']==10000
assert sum(j['native']['HNSW_calls'] for j in jobs)==8448
assert sum(j['native']['builds'] for j in jobs)==8
for job in jobs:
 process=Path('/proc')/str(job['pid'])/'cmdline'
 if process.exists():assert str(O/'src/run.py').encode() not in process.read_bytes(),'query process still live'
assert v['status']=='PASS' and v['set_scored']==8192 and v['old_full_regression']==4096
assert v['parity_rows']==128 and v['W_constructions']==8 and v['interaction_queries']==2048
assert len(d['metrics'])==8 and d['optimizer_updates']==0
assert read(O/'reviews/visual_review.json')['status']=='PASS'
old_cases=read(E40/'results/attribution_cases.json')['cases']
for ds in DS:
 ca=case(ds);old=next(x for x in old_cases if x['dataset']==ds)
 assert all(ca[k]==old[k] for k in old),ds
 assert cfg(ds)['threads']==1 and cfg(ds)['query_cpu']==15 and cfg(ds)['native_call_cap']==4288
 for cell in CELLS:
  p=O/'models'/ds/cell;ident=read(p/'identity.json');construction=read(p/'construction.json')
  assert ident['original_parity']=='PASS' and sha(p/'W.f32')==construction['W_sha']==ident['W_sha']
  assert sha(p/'graph.hnsw')==ident['graph_file_sha']
  if cell in ['C','F']:
   assert ident['E39_regression']=='PASS' and ident['topology_sha']==construction['expected_topology_sha']
   assert ident['graph_file_sha']==construction['expected_graph_sha']
  assert (O/'results'/ds/(cell+'.npz')).exists() and (p/'parity.npz').exists()
docs=[R/p for p in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md',
    'experiment_history/README.md','experiment_history/30_profile_factorial.md']]+list(O.glob('*.md'))
forward={O/'reviews/final_audit.json',O/'reviews/completion_audit.json'}
links=0;broken=[]
for doc in docs:
 for target in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
  if '://' in target or target.startswith('#'):continue
  p=(doc.parent/target.split('#')[0]).resolve()
  if not p.exists() and p not in forward:broken.append((str(doc),target))
  links+=1
assert not broken,broken
for name in ['metrics.csv','queries.csv','cases.csv']:
 with (O/'results'/name).open() as f:count=sum(1 for _ in csv.DictReader(f))
 assert count=={'metrics.csv':8,'queries.csv':2048,'cases.csv':16}[name]
checks=[
 ('same_two_frozen_cases','config.locked.json and E40 attribution_cases equality'),
 ('all_four_cells_both_datasets','8 W files, 8 physical graphs, 8 raw result arrays and identities'),
 ('exact_row_level_construction','independent_verification W_constructions=8'),
 ('original_1024_query_lists','prequery freeze and independent query identity checks'),
 ('ordinary_HNSW_original_NSG','native dependency SHA, serialized plain and original kernel verify'),
 ('C_F_full_regression','4096 outputs and 4 topology/physical graph identities'),
 ('S_R_real_new_search','native ledgers, raw arrays and 128 parity query results'),
 ('all_query_gain_loss_and_failures','8192 independent set scores, 8 metrics and 2048 query rows'),
 ('frozen_case_conditions_and_interaction','4 case queries, 16 case cells, 2048 independently reconstructed interactions'),
 ('bounded_serial_single_thread_execution','native 8576 NSG / 8448 HNSW / 8 builds, threads1, serial completed jobs'),
 ('no_optimizer_or_new_GT_evaluation_scope','fixed copied W rows and no training/update path; existing train4096 query/GT inputs'),
 ('old_artifacts_preserved','all E37 E38 E39 E40 file identities and native NSG dependencies match'),
 ('report_plots_and_document_sync','report, inspected PNGs and SVG/PDF, history30, root documents, local links'),
 ('no_remaining_active_query_jobs','both job process handles terminal and no matching live run.py PID')]
dump(O/'reviews/completion_audit.json',dict(status='PASS',objective='Execute the E40 target/rest 2x2 control',
     scope='two preselected datasets, four cells each, fixed 1024 queries and full analysis',
     requirements=[dict(requirement=req,status='PROVEN',evidence=evidence) for req,evidence in checks],
     unresolved_requirements=[],future_removed_profile_control='DESIGNED_UNRUN_NOT_PART_OF_THIS_EXECUTION'))
state='COMPLETE_TARGET_REST_FACTORIAL_WEBVID_LOCAL_SIGNAL_YANDEX_TARGET_NULL'
dump(O/'state.json',dict(status=state,completed_at=time.time(),NSG_calls=8576,HNSW_calls=8448,builds=8,
     optimizer_updates=0,new_GT=0,new_validation_heldout_raw_access=False,default_changed=False,queued_jobs=0,
     local_case_isolation_signal={s['dataset']:s['local_case_isolation_signal'] for s in d['datasets']},
     next_removed_profile_control='DESIGNED_UNRUN'))
audit=dict(status='PASS',protected_files=len(protected),protected_counts={p.name:len(files(p)) for p in [E37,E38,E39,E40]},
     NSG_calls=8576,HNSW_calls=8448,builds=8,optimizer_updates=0,independent_verification=v,
     completion_requirements=len(checks),local_links=links,artifact_bytes=sum(p.stat().st_size for p in files(O)),
     seconds=time.monotonic()-start)
dump(O/'reviews/final_audit.json',audit);freeze(O/'reviews/final_artifact_freeze.json',files(O)+docs)
print(json.dumps(audit,ensure_ascii=False,indent=2))
