from pathlib import Path
import json,hashlib,time,sys
import numpy as np
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''):h.update(b)
 return h.hexdigest()
lock=read(R/'config.locked.json');execution=read(R/'reviews/execution_complete.json');assert execution['status']=='PASS'
for x in read(R/'reviews/source_frozen.json')['files']:assert sha(x['path'])==x['sha256'],x['path']
for name in ['candidates_frozen','models_frozen']:
 for x in read(R/f'reviews/{name}.json')['files']:assert sha(x['path'])==x['sha256']
records=[]
for ds,c in lock['datasets'].items():
 nbase=c['base_n'];d=c['dimension'];hubs=set(np.fromfile(c['anchor']['ids'],np.int32).tolist());roles={}
 for role in ['proposal','fit','audit']:
  q=np.fromfile(R/'inputs'/ds/role/'queries.f32',np.float32).reshape(-1,d);roles[role]=set(x.tobytes() for x in q);assert len(roles[role])==len(q)
 assert not roles['proposal']&roles['fit'] and not roles['proposal']&roles['audit'] and not roles['fit']&roles['audit']
 candidates={x['old_id']:set(x['candidates']) for x in read(R/'models'/ds/'candidates.json')['slots']}
 for old,values in candidates.items():assert old in hubs and len(values)==8 and not values&hubs and min(values)>=0 and max(values)<nbase
 p=R/'results'/ds/'labels';m=np.fromfile(p/'meta.i32',np.int32).reshape(-1,4);e=np.fromfile(p/'entries.i32',np.int32).reshape(-1,3);route=np.fromfile(R/'results'/ds/'route_fit/entries.i32',np.int32).reshape(-1,3);baseline=m[:,1]<0;assert np.array_equal(e[baseline],route)
 a=np.flatnonzero(~baseline);expected=route[m[a,0]].copy();mask=expected==m[a,1,None];assert np.all(mask.sum(1)==1);expected[mask]=m[a,2];expected.sort(axis=1);assert np.array_equal(expected,e[a])
 for old in np.unique(m[a,1]):assert set(m[m[:,1]==old,2]).issubset(candidates[int(old)])
 assert np.all(e[:,0]<e[:,1]) and np.all(e[:,1]<e[:,2]);assert np.all((e>=0)&(e<nbase))
 done=read(p/'complete.json');assert done['search_calls']==3*len(m)+2*done['linked_E99_and_actual_K1_checks'];assert done['linked_E99_and_actual_K1_checks']==32
 h=np.fromfile(p/'hits.u16',np.uint16).reshape(-1,2).astype(float);t=np.fromfile(p/'seconds.f64',np.float64).reshape(-1,2).mean(1);baseidx=np.flatnonzero(baseline);assert np.array_equal(m[baseidx,0],np.arange(len(route)))
 models=read(R/'models'/ds/'models.json');counts={}
 for model in models:
  edits=model['edits'];assert len(edits)<=16 and len({x[0] for x in edits})==len(edits)==len({x[1] for x in edits})
  for old,new in edits:
   assert new in candidates[old]
   for fold in [0,1]:
    ix=np.flatnonzero((m[:,1]==old)&(m[:,2]==new)&(m[:,3]==fold));bi=baseidx[m[ix,0]];diff=h[ix]-h[bi];diff[:,1]/=100;dr=diff.mean(0);assert len(ix)>=8 and np.all(dr>=0) and dr.sum()>0
    if model['name']=='Cost':assert (t[ix]-t[bi]).mean()<=0
  counts[model['name']]=len(edits)
  for K in [1,100]:
   p=R/'results'/ds/'audit';br=np.fromfile(p/f'GT10_K{K}_L128/entry_ids.i32',np.int32).reshape(-1,3);actual=np.fromfile(p/f'{model["name"]}_K{K}_L128/entry_ids.i32',np.int32).reshape(-1,3);expected=br.copy()
   for old,new in edits:expected[br==old]=new
   expected.sort(axis=1);assert np.array_equal(expected,actual)
   unchanged=np.all(br==actual,axis=1);bi=np.fromfile(p/f'GT10_K{K}_L128/ids.i32',np.int32).reshape(-1,K);ai=np.fromfile(p/f'{model["name"]}_K{K}_L128/ids.i32',np.int32).reshape(-1,K);assert np.array_equal(bi[unchanged],ai[unchanged])
 records.append(dict(dataset=ds,role_sizes={k:len(v) for k,v in roles.items()},candidate_slots=len(candidates),label_actions=len(m),label_calls=done['search_calls'],selected_edits=counts))
jobs=read(R/'reviews/jobs.json');total=sum(x['complete']['search_calls'] for x in jobs);assert total==execution['search_calls']<=lock['max_search_calls'] and all(x['exit_code']==0 for x in jobs)
guard=read(R/'reviews/resource_observations.json');assert not guard['breaches'];assert all(x['threads']==1 and x['cpu']=='15' and x['maxrss_kib']<=40*1024*1024 for x in guard['records'].values())
protected=read(R/'reviews/protected_before.json');code={p:sha(ROOT/p)==s for p,s in protected.items() if not p.endswith('.md')};assert all(code.values())
for ds,c in lock['datasets'].items():
 st=Path(c['index']).stat();assert st.st_size==c['index_stat']['bytes'] and st.st_mtime_ns==c['index_stat']['mtime_ns']
assert sha(R/'src/kernels.hpp')==sha(ROOT/'entry_method_exploration/20260920_wfree_frozen_replication_v1/src/kernels.hpp')
result=dict(status='PASS',created_unix=time.time(),datasets=records,search_calls=total,source_and_models_frozen=True,actual_three_entry_mapping_verified=True,unchanged_entries_restore_results=True,current_roles_byte_disjoint=True,main_search_source_unchanged=code,kernel_copy_byte_identical=True,maxrss_kib_observed=max(x['maxrss_kib'] for x in guard['records'].values()),audit_wall_rounds=sum(x['complete'].get('wall_rounds',0) for x in jobs),new_gt=0,new_graphs=0,primary_gate=read(R/'results/gate.json'))
(R/'reviews/completion_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
