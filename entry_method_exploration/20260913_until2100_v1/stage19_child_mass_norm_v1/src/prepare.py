from common import *
from graph_reader import inspect_serialized
import math,struct
threads();resources();assert not (O/'config.locked.json').exists();E73=C/'stage14_compact_modes_v1';E77=C/'stage18_child_shrink_factorial_v1';paths=[O/'protocol.md',E77/'reviews/final_artifact_freeze.json'];models={};records=[]
def scale(W,rho,d):
 assert len(W)==len(rho) and np.isfinite(W).all() and np.isfinite(rho).all() and np.all((rho>0)&(rho<=1))
 a=np.exp(np.log(rho)/d);return (W.astype(float)*a[:,None]).astype(np.float32),a
rejected=0
for w,r in [(np.ones((1,2)),np.ones(2)),(np.array([[np.nan,0]]),np.ones(1)),(np.ones((1,2)),np.array([0.])),(np.ones((1,2)),np.array([1.1]))]:
 try:scale(w,r,2)
 except AssertionError:rejected+=1
assert rejected==4
def install(source,W,oldW,dest):
 start=time.monotonic();assert not dest.exists();data=bytearray(Path(source).read_bytes());before=bytes(data);h=struct.unpack_from('<6QiI3QdQ',data);n,size,label,coord=h[2:6];assert n==len(W) and W.shape==oldW.shape and label-coord==W.shape[1]*4
 for i in range(n):
  at=96+i*size;assert struct.unpack_from('<Q',data,at+label)[0]==i and data[at+coord:at+label]==oldW[i].tobytes();data[at+coord:at+label]=W[i].tobytes()
 restored=bytearray(data)
 for i in range(n):restored[96+i*size+coord:96+i*size+label]=oldW[i].tobytes()
 assert bytes(restored)==before;dest.write_bytes(data);inspect_serialized(dest,W,np.arange(n));return dict(seconds=time.monotonic()-start,all_nonvector_bytes_identical=True,patch_roundtrip_exact=True,graph=identity(dest))
for x in read(E73/'reviews/base_graph_identity.json')['sources']:
 s=Path(x['path']).stat();assert (s.st_size,s.st_mtime_ns)==(x['bytes'],x['mtime_ns'])
shutil.copy2(E73/'reviews/base_graph_identity.json',O/'reviews/base_graph_identity.json');assert sha(O/'bin/evaluate')==sha(E73/'bin/evaluate')
dump(O/'bin/provenance.json',dict(compile_seconds=0,evaluator=identity(O/'bin/evaluate'),source=identity(E73/'bin/evaluate'),link_reuse=True))
for ds in DS:
 start=time.monotonic();c=read(E73/'inputs'/ds/'aux.json');old=next(m for m in c['methods'] if m['model_name']=='compact10');keep=np.fromfile(E73/'models'/ds/'original_slots.i32',np.int32);W=np.fromfile(old['W'],np.float32).reshape(-1,c['dim']);t=dict(np.load(E66/'models'/ds/'training.npz'));fractions=np.ones((old['unique_hub_count'],3));fractions[t['active'],1:]=t['child_mass']/t['parent_mass'][t['active'],None];rho=fractions[keep//3,keep%3];child=keep%3!=0;assert np.all((rho[child]>0)&(rho[child]<1)) and np.all(rho[~child]==1)
 uniform_rho=np.ones(len(keep));uniform_rho[child]=np.exp(np.log(rho[child]).mean());variants=[];dest=O/'models'/ds;dest.mkdir();weights={}
 for name,r in [('mass10',rho),('uniform10',uniform_rho)]:
  folder=dest/name;folder.mkdir();new,alpha=scale(W,r,c['dim']);new[~child]=W[~child];assert new[~child].tobytes()==W[~child].tobytes();assert np.all(alpha[child]<1)
  for i in range(len(W)):
   ref=np.array([float(x)*math.exp(math.log(float(r[i]))/c['dim']) for x in W[i]],np.float32);assert ref.tobytes()==new[i].tobytes()
  assert np.max(np.abs(np.linalg.norm(new.astype(float),axis=1)-alpha*np.linalg.norm(W.astype(float),axis=1)))<1e-7
  new.tofile(folder/'W.f32');alpha.tofile(folder/'alpha.f64');weights[name]=alpha
  m=dict(old,model_name=name,name=name+'_L128',W=str(folder/'W.f32'),graph_file=str(folder/'graph.hnsw'));dump(folder/'model.json',m);variants.append(m)
 assert abs(np.log(weights['mass10'][child]).sum()-np.log(weights['uniform10'][child]).sum())<2e-12
 rho.tofile(dest/'rho.f64');keep.tofile(dest/'source_slots.i32');models[ds]=variants
 rec=dict(dataset=ds,source_model=old,child_count=int(child.sum()),primary_count=int((~child).sum()),dim=c['dim'],formula='rho^(1/d), no renormalization',uniform_mean_log_scale=float(np.log(weights['uniform10'][child]).mean()),mass_scale_min=float(weights['mass10'][child].min()),mass_scale_max=float(weights['mass10'][child].max()),construction_seconds=time.monotonic()-start,independent_scalar_bytes=True,parent_bytes_unchanged=True);dump(dest/'manifest.json',rec);records.append(rec)
 paths += [E73/'inputs'/ds/'aux.json',E73/'models'/ds/'original_slots.i32',E66/'models'/ds/'training.npz']+[Path(c[k]) for k in ['queries_file','gt_file','row_ids']]
 for m in c['methods']:paths += [Path(m[k]) for k in ['W','mapping','tie_ids','graph_file']]
dump(O/'config.locked.json',dict(datasets=DS,threads=1,CPU=15,NSG_expected=129536,HNSW_expected=129280,builds=0,vector_installs=4,NSG_hard_cap=132000,output_cap_MiB=40,free_min_GiB=7,evening_reserve_MiB=32,latest_launch=1789282200,query_hard_stop=1789282800,per_job_seconds=600,quality_gate='mass vs P/compact full>0 halves>=0 failures<=0; vs uniform full>=0 halves>=0 failures<=0',wall_measurement='only if one dataset passes, separate E79'))
paths += list((O/'src').glob('*'))+list((O/'models').rglob('*.*'))+list((O/'bin').glob('*'))+[O/'config.locked.json'];freeze(O/'reviews/preinstall_freeze.json',paths)
installs=[]
for ds in DS:
 c=read(E73/'inputs'/ds/'aux.json');old=next(m for m in c['methods'] if m['model_name']=='compact10');W=np.fromfile(old['W'],np.float32).reshape(-1,c['dim'])
 for m in models[ds]:
  new=np.fromfile(m['W'],np.float32).reshape(W.shape);r=install(old['graph_file'],new,W,Path(m['graph_file']));r.update(dataset=ds,model=m['model_name']);installs.append(r)
for di,ds in enumerate(DS):
 old=read(E73/'inputs'/ds/'aux.json');inp=O/'inputs'/ds;inp.mkdir()
 for split,n in [('preflight',128),('aux',7952)]:
  methods=[dict(x) for x in old['methods'] if x['model_name'] in ['baseline10','compact10']]+models[ds];c=dict(old,methods=methods,split='E78_historical_aux_'+split,num_queries=n,input_total_rows=7952,dataset_order=di,real_call_cap=4*(2*n+16),timing_repeats=0);dump(inp/(split+'.json'),c)
dump(O/'results/construction.json',dict(status='PASS',datasets=records,installs=installs,invalid_input_rejections=4,builds=0,new_GT=0,gradient_updates=0));paths+=list((O/'inputs').rglob('*.json'))+list((O/'models').rglob('*.hnsw'))+[O/'results/construction.json'];freeze(O/'reviews/prequery_freeze.json',paths);dump(O/'logs/jobs.json',[]);dump(O/'state.json',dict(status='MASS_NORM_INSTALLED_UNQUERIED',NSG=0,HNSW=0,builds=0,vector_installs=4,day_goal_complete=False));resources();print('E78_PREPARED')
