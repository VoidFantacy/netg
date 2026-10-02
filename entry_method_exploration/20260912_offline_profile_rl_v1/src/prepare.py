from common import *
assert not (O/'state.json').exists(),'refuse repeated prepare'
for name in ['inputs','bin','models','results','logs','reviews','source_before','figures']:(O/name).mkdir(exist_ok=True)
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:shutil.copy2(R/name,O/'source_before'/name)
shutil.copy2(R/'experiment_history/README.md',O/'source_before/history_README.md')
for name in ['benchmark_with_nsg.cpp','legacy_reference.cpp']:shutil.copy2(E36/'src'/name,O/'src'/name)
for name in ['evaluate.cpp','benchmark_with_nsg.cpp','legacy_reference.cpp']:
 (O/'src/evaluation_reference').mkdir(exist_ok=True);shutil.copy2(E34/'src'/name,O/'src/evaluation_reference'/name)
shutil.copy2(E34/'bin/evaluate',O/'bin/evaluate')
dump(O/'bin/evaluate.provenance.json',dict(source=identity(E34/'bin/evaluate'),copied=identity(O/'bin/evaluate'),build=read(E34/'bin/provenance.json')))
freeze(O/'reviews/E36_preserved.json',[p for p in E36.rglob('*') if p.is_file()])
old=[]
for folder in (R/'entry_method_exploration').iterdir():
 if folder==O or not folder.is_dir():continue
 for p in folder.rglob('*'):
  if p.is_file():
   s=p.stat();old.append(dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns))
dump(O/'reviews/old_artifacts_stat.json',old)
expected={x['path']:x for x in read(E36/'reviews/upstream.json')['files']};upstream=set()
for ds in DS:
 base=read(E33/'inputs'/ds/'config.json');fit=read(E24/'inputs'/ds/'fit/config.json');d=base['dim'];h=base['hub_count']
 dest=O/'inputs'/ds;dest.mkdir();ind=np.random.default_rng(20260912).permutation(20000)[:5120].astype(np.int32);ind.tofile(dest/'source_local.i32')
 for key,dt,shape,name in [('queries_file',np.float32,(20000,d),'queries.f32'),('gt_file',np.int64,(20000,100),'gt.i64'),('row_ids',np.int64,(20000,),'row_ids.i64')]:
  src=Path(fit[key]);upstream.add(src);a=np.fromfile(src,dt).reshape(shape);a[ind].tofile(dest/name)
 q=np.fromfile(dest/'queries.f32',np.float32).reshape(5120,d)[:4096].astype(float);q/=np.linalg.norm(q,axis=1,keepdims=True)
 eigen,b=np.linalg.eigh(q.T@q/len(q));b=b[:,-RANK:][:,::-1].copy()
 for j in range(RANK):
  if b[np.argmax(np.abs(b[:,j])),j]<0:b[:,j]*=-1
 assert np.max(np.abs(b.T@b-np.eye(RANK)))<1e-12;b.tofile(dest/'basis.f64')
 p=Path(base['policy']['W']);shutil.copy2(p,dest/'P.f32');shutil.copy2(base['hub_ids'],dest/'hub_ids.i32')
 c=dict(dataset=ds,dim=d,hub_count=h,num_queries=5120,train=4096,monitor=1024,gt_k=100,threads=1,query_cpu=15,L=128,
  index_path=base['index_path'],queries_file=str(dest/'queries.f32'),gt_file=str(dest/'gt.i64'),row_ids=str(dest/'row_ids.i64'),hub_ids=str(dest/'hub_ids.i32'),native_call_cap=1200000,
  original_graph=base['graph_file'],original_policy=base['policy'],basis=str(dest/'basis.f64'),P=str(dest/'P.f32'))
 dump(dest/'config.json',c);dump(dest/'selection.json',dict(train=4096,monitor=1024,seed=20260912,source=fit,source_local_sha=sha(dest/'source_local.i32'),basis_top_eigenvalues=eigen[-RANK:][::-1].tolist(),historical_data=True,cal_audit_prepared=False))
 upstream.update([p,Path(base['hub_ids']),Path(base['graph_file']),Path(base['index_path']),Path(base['index_path']+'.info'),E33/'inputs'/ds/'config.json',E24/'inputs'/ds/'fit/config.json'])
argv=['c++','-shared','-std=c++17','-O3','-march=native','-fopenmp','-fPIC','-Wall','-Wextra',f'-I{R}',f'-I{R}/faiss',f'-I{R}/benches',f'-I{R}/build/_deps/json-src/include',str(O/'src/environment.cpp'),str(R/'ACSG/ACSG.cpp'),str(R/'build/faiss/faiss/libfaiss.a'),str(R/'build/ACSG/libACSG.a'),str(R/'build/MRNN_Descent/libmrnndescent.a'),str(R/'build/faiss/faiss/libfaiss.a'),'/usr/lib/x86_64-linux-gnu/libopenblas.so','-lm','-ldl','-lpthread','-o',str(O/'bin/environment.so')]
with (O/'logs/build.log').open('x') as f:
 t=time.time();p=subprocess.run(argv,env=env(),stdout=f,stderr=subprocess.STDOUT)
dump(O/'bin/environment.build.json',dict(argv=argv,seconds=time.time()-t,exit_code=p.returncode));assert p.returncode==0,'see build.log'
upstream.update(Path(x) for x in argv if x.startswith('/') and Path(x).is_file() and not x.startswith(str(O)))
upstream.update((R/'benches/hnswlib').glob('*.h'));upstream.update((R/'ACSG').glob('*.h'));upstream.add(E34/'bin/evaluate')
for p in sorted(upstream):
 if str(p) in expected:assert identity(p)==expected[str(p)],p
freeze(O/'reviews/upstream.json',upstream)
dump(O/'config.locked.json',dict(datasets=DS,arms=ARMS,seeds=SEEDS,steps=STEPS,population=POP,batch=BATCH,rank=RANK,sigma=SIGMA,NSG_hard_cap=CAP,HNSW_build_hard_cap=15000,threads=1,training_L=128,curve_L=LS,protocol=identity(O/'protocol.md')))
resources();dump(O/'state.json',dict(status='PREPARED_PREFLIGHT_PENDING',new_NSG_calls=0,optimizer_updates=0,validation_heldout_access=False))
print('PREPARED',len(upstream),'upstream files,',len(old),'old stat records',flush=True)
