from common import *
from graph_reader import inspect_serialized
import subprocess,struct
threads();resources();assert not (O/'config.locked.json').exists();E73=C/'stage14_compact_modes_v1';E76=C/'stage17_child_support_diagnosis_v1';paths=[O/'protocol.md',E76/'reviews/final_artifact_freeze.json'];models={};construction=[]
def shrink(P,U):
 assert P.shape==U.shape and np.isfinite(P).all() and np.isfinite(U).all()
 x=P.astype(float)+U.astype(float);norm=np.linalg.norm(x,axis=1);assert np.all(norm>1e-12);return (x/norm[:,None]).astype(np.float32)
assert np.allclose(shrink(np.array([[1,0]],np.float32),np.array([[0,1]],np.float32)),np.sqrt(.5),atol=3e-8)
rejected=0
for P,U in [(np.ones((1,2)),np.ones((2,2))),(np.array([[1.,0]]),np.array([[-1.,0]])),(np.array([[float('nan'),0]]),np.ones((1,2)))]:
 try:shrink(P,U)
 except AssertionError:rejected+=1
assert rejected==3
def patch_graph(source,W,expected_source_W,dest):
 assert not dest.exists() and W.shape==expected_source_W.shape and np.isfinite(W).all();data=bytearray(Path(source).read_bytes());head=struct.unpack_from('<6QiI3QdQ',data);n,size,label,coord=head[2:6];assert n==len(W) and label-coord==W.shape[1]*4;before=bytes(data)
 for i in range(n):
  at=96+i*size;assert struct.unpack_from('<Q',data,at+label)[0]==i and data[at+coord:at+label]==expected_source_W[i].tobytes();data[at+coord:at+label]=W[i].tobytes()
 # Replacing the vectors back must restore every source byte, including padding.
 restored=bytearray(data)
 for i in range(n):restored[96+i*size+coord:96+i*size+label]=expected_source_W[i].tobytes()
 assert bytes(restored)==before;dest.write_bytes(data);inspect_serialized(dest,W,np.arange(n));return dict(source=identity(source),output=identity(dest),all_nonvector_bytes_identical=True,patch_roundtrip_exact=True)
for item in read(E73/'reviews/base_graph_identity.json')['sources']:
 s=Path(item['path']).stat();assert (s.st_size,s.st_mtime_ns)==(item['bytes'],item['mtime_ns'])
shutil.copy2(E73/'reviews/base_graph_identity.json',O/'reviews/base_graph_identity.json')
for b in ['evaluate','build_graph']:assert sha(O/'bin'/b)==sha(E73/'bin'/b)
dump(O/'bin/provenance.json',dict(compile_seconds=0,binaries=[dict(source=identity(E73/'bin'/b),copied=identity(O/'bin'/b)) for b in ['evaluate','build_graph']]))
for ds in DS:
 tick=time.monotonic();c=read(E73/'inputs'/ds/'aux.json');old=next(m for m in c['methods'] if m['model_name']=='compact10');src=read(E73/'models'/ds/'manifest.json')['source'];full=np.fromfile(src['W'],np.float32).reshape(-1,3,c['dim']);keep=np.fromfile(E73/'models'/ds/'original_slots.i32',np.int32);W=np.fromfile(old['W'],np.float32).reshape(-1,c['dim']);P=full[keep//3,0];assert W.tobytes()==full.reshape(-1,c['dim'])[keep].tobytes();child=keep%3!=0;Ws=W.copy();Ws[child]=shrink(P[child],W[child]);assert Ws[~child].tobytes()==W[~child].tobytes()
 # Independent scalar construction for every changed row.
 import math
 for i in np.flatnonzero(child):
  x=[float(p)+float(u) for p,u in zip(P[i],W[i])];den=math.sqrt(math.fsum(z*z for z in x));ref=np.array([z/den for z in x],np.float32);assert np.allclose(ref,Ws[i],rtol=0,atol=1.5e-8)
 assert np.isfinite(Ws).all() and np.max(np.abs(np.linalg.norm(Ws.astype(float),axis=1)-1))<2e-7
 dest=O/'models'/ds;dest.mkdir();Ws.tofile(dest/'W.f32');variants=[]
 for name in ['shrink10','score10','topology10']:
  folder=dest/name;folder.mkdir();m=dict(old,model_name=name,name=name+'_L128',W=str(dest/'W.f32') if name!='topology10' else old['W'],graph_file=str(folder/'graph.hnsw'));dump(folder/'model.json',m);variants.append(m)
 models[ds]=variants;rec=dict(dataset=ds,source_model=old,source_full=src,kept_profiles=len(W),children_shrunk=int(child.sum()),primary_rows_unchanged=int((~child).sum()),alpha=.5,construction_seconds=time.monotonic()-tick,source_original_slots=identity(E73/'models'/ds/'original_slots.i32'),W=identity(dest/'W.f32'),independent_scalar_reference=True);dump(dest/'manifest.json',rec);construction.append(rec)
 paths += [E73/'inputs'/ds/'aux.json',E73/'models'/ds/'original_slots.i32',Path(src['W'])]+[Path(c[k]) for k in ['queries_file','gt_file','row_ids']]
 for m in c['methods']:paths += [Path(m[k]) for k in ['W','mapping','tie_ids','graph_file']]
dump(O/'config.locked.json',dict(datasets=DS,threads=1,CPU=15,NSG_expected=161920,HNSW_expected=161600,builds=2,vector_installs=4,NSG_hard_cap=165000,output_cap_MiB=64,free_min_GiB=7,evening_reserve_MiB=32,latest_launch=1789281900,query_hard_stop=1789282500,per_job_seconds=600,quality_gate='A vs P and compact: full net hits >0, halves >=0, failures not increased',wall_measurement='only A, only if at least one dataset passes, separate E78 with both datasets migration control'))
paths+=list((O/'src').glob('*'))+list((O/'bin').glob('*'))+list((O/'models').rglob('*.json'))+list((O/'models').rglob('*.f32'))+[O/'config.locked.json'];freeze(O/'reviews/prebuild_freeze.json',paths)
installs=[]
for ds in DS:
 c=read(E73/'inputs'/ds/'aux.json');old=next(m for m in c['methods'] if m['model_name']=='compact10');A,S,T=models[ds];p=subprocess.run([str(O/'bin/build_graph'),str(Path(A['graph_file']).parent/'model.json'),A['graph_file']],capture_output=True,text=True,timeout=180);(O/'logs'/('build_'+ds+'.log')).write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr;dump(O/'models'/ds/'build.json',json.loads(p.stdout))
 Ws=np.fromfile(A['W'],np.float32).reshape(-1,c['dim']);W=np.fromfile(old['W'],np.float32).reshape(-1,c['dim']);inspect_serialized(A['graph_file'],Ws,np.arange(len(W)))
 installs += [patch_graph(old['graph_file'],Ws,W,Path(S['graph_file'])),patch_graph(A['graph_file'],W,Ws,Path(T['graph_file']))]
for di,ds in enumerate(DS):
 old=read(E73/'inputs'/ds/'aux.json');inp=O/'inputs'/ds;inp.mkdir()
 for split,n in [('preflight',128),('aux',7952)]:
  methods=[dict(x) for x in old['methods'] if x['model_name'] in ['baseline10','compact10']]+models[ds];c=dict(old,methods=methods,split='E77_historical_aux_'+split,num_queries=n,input_total_rows=7952,dataset_order=di,real_call_cap=5*(2*n+16),timing_repeats=0);dump(inp/(split+'.json'),c)
dump(O/'results/construction.json',dict(status='PASS',datasets=construction,vector_installs=installs,mathematical_rejections=3,new_GT=0,new_optimizer=0))
paths+=list((O/'inputs').rglob('*.json'))+list((O/'models').rglob('*.hnsw'))+[O/'results/construction.json'];freeze(O/'reviews/prequery_freeze.json',paths);dump(O/'logs/jobs.json',[]);dump(O/'state.json',dict(status='SHRINK_FACTORIAL_BUILT_UNQUERIED',NSG=0,HNSW=0,builds=2,vector_installs=4,day_goal_complete=False));resources();print('E77_PREPARED')
