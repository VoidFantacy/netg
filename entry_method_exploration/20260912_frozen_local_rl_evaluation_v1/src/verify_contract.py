from common import *
import sys,ast
assert os.sched_getaffinity(0)=={8};sys.dont_write_bytecode=True;started=time.monotonic();resources()
assert read(O/'reviews/independent_fit_deployment.json')['status']=='PASS';assert read(O/'reviews/output_verification.json')['status']=='PASS'
for name in ['prequery_freeze.json','upstream.json','protected.json','native_dependencies.json','selection_before_audit.json']:check(O/'reviews'/name)
jobs=read(O/'logs/jobs.json');assert len(jobs)==8 and all(j['status']=='COMPLETE' and j['actual']==j['reserved'] and j['peak_threads']==1 for j in jobs)
assert sum(j['actual'] for j in jobs)==423680 and sum(j['reserved'] for j in jobs)<=CAP
ordered=sorted(jobs,key=lambda x:x['started_at']);assert all(a['closed_at']<=b['started_at'] for a,b in zip(ordered,ordered[1:]))
selection=read(O/'results/cal_selection.json')['selection'];full_parity=original=points=0
for ds in DS:
 train=np.fromfile(read(O/'inputs'/ds/'config.json')['row_ids'],np.int64);cal=np.fromfile(O/'inputs'/ds/'cal/row_ids.i64',np.int64);audit=np.fromfile(O/'inputs'/ds/'audit/row_ids.i64',np.int64)
 assert len(train)==5120 and len(cal)==len(audit)==1024 and not np.intersect1d(train,cal).size and not np.intersect1d(train,audit).size and not np.intersect1d(cal,audit).size
 for arm in ARMS:
  scores=read(O/'results'/ds/'cal_selection_details.json');best=max([x for x in scores if x['model'].startswith(arm+'_')],key=lambda x:(x['mean_U'],-x['total_NDC'],-x['seed']));assert best==selection[ds][arm]
 for phase in ['fit_parity','cal','audit','frontier']:
  check(O/'reviews'/f'{phase}_{ds}_before.json');folder=O/'results'/f'{phase}_{ds}';c=read(folder/'config.json');r=read(folder/'results.json');tc=read(folder/'thread_contract.json')
  assert c['threads']==1 and c['query_cpu']==15 and tc['process_threads']==tc['actual_openmp_threads']==1
  assert r['GT_opened_after_all_raw_search'] and r['timing_repeats']==(5 if phase=='frontier' else 0)
  for m in r['methods']:
   assert m['full_plain_count_parity_queries']==c['num_queries'] and m['original_kernel_parity_queries']==16 and m['repeated_output_parity']
   assert m['physical_graph_calls']==(7 if phase=='frontier' else 2)*c['num_queries']+16+(2048 if m['configuration']['component_wall'] else 0)
   full_parity+=c['num_queries'];original+=16;points+=1
assert points==80 and full_parity==72960 and original==1280
for p in (O/'src').rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
dump(O/'reviews/contract_verification.json',dict(status='PASS',NSG_calls=423680,reserved_NSG=423680,points=points,full_plain_count_parity_rows=full_parity,original_kernel_parity_rows=original,
 fit_checkpoint_bit_parity_rows=1280,wall_repeats=250,actual_process_threads=1,serial_jobs=8,cal_audit_split_isolation=True,seed_selection_frozen_before_audit=True,
 protected_files=len(read(O/'reviews/protected.json')['files']),optimizer_updates=0,validation_heldout_query_GT_opened=False,seconds=time.monotonic()-started))
print('E49 contract verification PASS',flush=True)
