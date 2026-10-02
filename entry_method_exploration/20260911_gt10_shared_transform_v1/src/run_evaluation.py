from build_prepare import *
import copy,os
def variants(ds):return [policy(ds,f'{f}_r{l}',O/'models'/ds/f'{f}_r{l}'/'W.f32') for f in ['linear','mlp','free'] for l in [10,100]]
def points(models,Ls,exact=False,component=False):
 out=[]
 for L in Ls:
  for m in models:
   x=copy.deepcopy(m);x.update(L=L,exact=exact,name=m['model_name']+('_exact' if exact else '_hnsw')+f'_L{L}',component_wall=component and L==128 and m['model_name'] in ['gt10_hard','linear','mlp','free']);out.append(x)
 return out
def check_freeze(path):
 c=json.loads(path.read_text())
 for x in c['files']:assert identity(x['path'])==x,x['path']
def freeze(path,files):
 assert not path.exists();dump(path,dict(timestamp=time.time(),files=[identity(p) for p in files],heldout_access=False));check_freeze(path)
def run(ds,stage,methods,split,reps=0):
 assert shutil.disk_usage(O).free>10*(1<<30)
 used=sum(p.stat().st_size for p in O.rglob('*') if p.is_file());assert used+(64<<20)<2*(1<<30),'directory reservation exceeds 2GiB'
 c=json.loads((O/'inputs'/ds/split/'config.json').read_text());c.update(methods=methods,timing_repeats=reps,dataset_order=DS.index(ds),threads=1,query_cpu=15)
 n=c['num_queries'];cap=sum((7 if reps else 2)*n+16+(2*n if m.get('component_wall') else 0) for m in methods);c['real_call_cap']=cap
 dest=O/'results'/f'{stage}_{ds}';cfg=O/'inputs'/ds/f'eval_{stage}.json';dump(cfg,c)
 jobs=json.loads((O/'logs/evaluation_jobs.json').read_text()) if (O/'logs/evaluation_jobs.json').exists() else []
 labels=sum(json.loads((O/'labels'/s/'complete.json').read_text())[k] for s in DS for k in ['physical_calls','parity_calls'])
 assert labels+sum(j['reserved_calls'] for j in jobs)+cap<=3655504
 argv=['taskset','-c','15',str(O/'bin/evaluate'),str(cfg),str(dest)];env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
 rec=dict(dataset=ds,stage=stage,argv=argv,reserved_calls=cap,status='RUNNING',start=time.time(),config=identity(cfg));jobs.append(rec);dump(O/'logs/evaluation_jobs.json',jobs)
 with (O/'logs'/f'{ds}.{stage}.log').open('w') as f:
  proc=subprocess.Popen(argv,stdout=f,stderr=subprocess.STDOUT,env=env);dump(O/'state.json',dict(status=stage.upper()+'_RUNNING',dataset=ds,pid=proc.pid,heldout_access=False));rc=proc.wait()
 rec.update(exit_code=rc,seconds=time.time()-rec['start'],status='COMPLETE' if rc==0 else 'FAILED');dump(O/'logs/evaluation_jobs.json',jobs);assert rc==0,(ds,stage)
 result=json.loads((dest/'results.json').read_text());assert result['physical_graph_calls']==cap
 gt=np.fromfile(c['gt_file'],np.int64).reshape(n,100)[:,:10]
 for m in result['methods']:
  ids=np.fromfile(dest/m['name']/'ids.i32',np.int32).reshape(n,10);hits=(ids[:,:,None]==gt[:,None,:]).any(1).sum(1)
  assert np.array_equal(hits,np.fromfile(dest/m['name']/'hits.u8',np.uint8)) and int(hits.sum())==m['total_hits']
 dump(dest/'independent_score_before_selection.json',dict(status='PASS',points=len(result['methods']),query_outputs=n*len(result['methods'])))
 assert sum(p.stat().st_size for p in O.rglob('*') if p.is_file())<2*(1<<30)
 print(ds,stage,'COMPLETE',cap,flush=True);return result
if __name__=='__main__':
 assert (O/'models/frozen_before_cal.json').exists()
 files=[O/'bin/evaluate',O/'protocol.md',O/'src/run_evaluation.py',O/'reviews/analysis_conventions_before_cal.json']+[p for p in (O/'models').glob('*/*/W.f32')]
 freeze(O/'reviews/evaluation_start_freeze.json',files)
 for ds in DS:
  check_freeze(O/'reviews/evaluation_start_freeze.json');res=run(ds,'cal',points([policy(ds,'gt10_hard')]+variants(ds),[64,128]),'cal')
  selected=[];candidates=[]
  for family in ['linear','mlp','free']:
   rows=[]
   for lam in [10,100]:
    name=f'{family}_r{lam}';ms=[m for m in res['methods'] if m['model_name']==name]
    rows.append(dict(name=name,lambda_anchor=lam,total_hits=sum(m['total_hits'] for m in ms),mean_total_ndc=sum(m['mean_total_ndc'] for m in ms)/2))
   winner=sorted(rows,key=lambda x:(-x['total_hits'],x['mean_total_ndc'],-x['lambda_anchor']))[0]
   p=policy(ds,family,O/'models'/ds/winner['name']/'W.f32');p['selected_variant']=winner['name'];selected.append(p);candidates.extend(rows)
  dump(O/'models'/ds/'selection.json',dict(timestamp=time.time(),selected=selected,candidates=candidates,rule='sum hits L64+L128 desc; mean total NDC asc; lambda desc',audit_used=False,validation_used=False))
 freeze(O/'models/frozen_before_audit.json',files+[O/'models'/ds/'selection.json' for ds in DS])
 for ds in DS:
  check_freeze(O/'models/frozen_before_audit.json');mods=[policy(ds,'gt10_hard')]+json.loads((O/'models'/ds/'selection.json').read_text())['selected']
  run(ds,'audit',points(mods,[64,128])+points(mods,[128],exact=True),'audit')
  c=json.loads((O/'inputs'/ds/'fit/config.json').read_text());dest=O/'inputs'/ds/'fit_probe';dest.mkdir()
  for key,name,dtype,width in [('queries_file','queries.f32',np.float32,c['dim']),('gt_file','gt.i64',np.int64,100),('row_ids','row_ids.i64',np.int64,1)]:
   a=np.fromfile(c[key],dtype).reshape(-1,width)[:256];a.tofile(dest/name);c[key]=str(dest/name)
  c.update(num_queries=256,split='fit_probe');dump(dest/'config.json',c);run(ds,'fit_probe',points(mods,[128]),'fit_probe')
 freeze(O/'models/frozen_before_validation.json',files+[O/'models'/ds/'selection.json' for ds in DS])
 for ds in DS:
  check_freeze(O/'models/frozen_before_validation.json');old=json.loads((E23/'inputs'/ds/'validation/config.json').read_text())
  fast=copy.deepcopy(next(m for m in old['methods'] if m['family']=='fast30k_3'));assert fast['hnsw_seed']==100 and fast['legacy_heap_order'] and not fast['canonical_entry_order'];fast.update(model_name='fast30k',component_wall=False)
  previous=json.loads((E24/'models'/ds/'selection.json').read_text())['selected_families']
  mods=[dict(name='nsg',model_name='nsg',family='nsg',seed=20260828,k=1),fast,policy(ds,'gt1_hard'),policy(ds,'gt10_hard')]
  mods.extend(policy(ds,f,previous[f]['W']) for f in ['gt1_soft','gt10_soft']);mods.extend(json.loads((O/'models'/ds/'selection.json').read_text())['selected'])
  run(ds,'validation',points(mods,[64,128,256,400,800],component=True),'validation',reps=3)
 dump(O/'state.json',dict(status='EVALUATION_COMPLETE_ANALYSIS_PENDING',heldout_access=False))
