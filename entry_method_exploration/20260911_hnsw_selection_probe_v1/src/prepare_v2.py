from common import *
assert not (O/'reviews/before_queries.json').exists()
for f in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:
 shutil.copy2(R/f,O/'source_before'/f)
shutil.copy2(R/'experiment_history/README.md',O/'source_before/history_README.md')
for f in ['benchmark_with_nsg.cpp','legacy_reference.cpp']:shutil.copy2(E34/'src'/f,O/'src'/f)
upstream=[];verified=[]
for ds in DS:
 old=read(D/'inputs/prepared_v2'/ds/'runner_config.json');base=read(E33/'inputs'/ds/'config.json');dest=O/'inputs'/ds;dest.mkdir()
 h=base['hub_count'];n=old['num_queries'];d=base['dim']
 assert h==old['hub_count'] and old['index_path']==base['index_path'] and old['L']==[64,128]
 assert sha(base['hub_ids'])==sha(old['hub_ids'])
 identities=read(old['verified_identities']);g=identity(base['index_path']);assert g['sha256']==identities['graph']['sha256']
 upstream += [Path(base['index_path']),Path(old['verified_identities']),Path(old['sample_manifest']),Path(D/'inputs/prepared_v2'/ds/'runner_config.json'),Path(E33/'inputs'/ds/'config.json'),Path(base['policy']['W']),Path(base['graph_file']),Path(base['hub_ids'])]
 manifest=read(old['sample_manifest']);assert manifest['row_roles'][:128]==['pilot']*128
 for key,dtype,shape,name in [('queries_file',np.float32,(n,d),'queries.f32'),('gt_file',np.int64,(n,100),'gt.i64'),('row_ids',np.int64,(n,),'row_ids.i64')]:
  a=np.fromfile(old[key],dtype).reshape(shape);a[:128].tofile(dest/name);upstream.append(Path(old[key]))
 rows=np.fromfile(dest/'row_ids.i64',np.int64);assert len(set(rows.tolist()))==128 and (rows<10000).all()
 # Pilot rows precede current 20K fit. Verify original training query/GT at actual source row.
 fitrows=np.fromfile(base['row_ids'],np.int64);assert not np.isin(rows,fitrows).any()
 qsrc=Path(identities['query_train']['path']);gsrc=Path(identities['gt_train']['path'])
 assert sha(qsrc)==identities['query_train']['sha256'] and sha(gsrc)==identities['gt_train']['sha256']
 fq=np.memmap(qsrc,np.float32,'r').reshape(-1,d+1);fg=np.memmap(gsrc,np.int32,'r').reshape(-1,101)
 assert (fq[:,0].view(np.int32)==d).all() and (fg[:,0]==100).all()
 assert np.array_equal(fq[rows,1:],np.fromfile(dest/'queries.f32',np.float32).reshape(128,d))
 assert np.array_equal(fg[rows,1:],np.fromfile(dest/'gt.i64',np.int64).reshape(128,100))
 upstream += [Path(base['row_ids']),qsrc,gsrc]
 for name,dtype,tail in [('hitcount.u8',np.uint8,()),('hitmask.u16',np.uint16,()),('ndc.u32',np.uint32,()),('ids.i32',np.int32,(10,))]:
  p=D/'results/run_v1/main'/ds/'L128'/('all_single.'+name)
  a=np.memmap(p,dtype,'r',shape=(n,h)+tail);a[:128].tofile(dest/('single.'+name));upstream.append(p)
 c=dict(dataset=ds,dim=d,num_queries=128,hub_count=h,L=128,threads=1,query_cpu=15,index_path=base['index_path'],queries_file=str(dest/'queries.f32'),hub_ids=base['hub_ids'],W=base['policy']['W'],graph_file=base['graph_file'],policy=base['policy'])
 dump(dest/'config.json',c);verified.append(dict(dataset=ds,original_train_queries_GT_and_current_hubs_equal=True,current_20K_fit_disjoint=True,NSG_sha256=g['sha256'],old_cache_threads=16,current_threads=1,rows=rows.tolist()))
old=read(E33/'bin/evaluate.build.json')['argv'];argv=[x.replace(str(E33/'src/evaluate.cpp'),str(O/'src/probe.cpp')).replace(str(E33/'bin/evaluate'),str(O/'bin/probe')) for x in old]
with (O/'logs/build.log').open('x') as f:
 t=time.time();p=subprocess.run(argv,env=env(),stdout=f,stderr=subprocess.STDOUT)
dump(O/'bin/build.json',dict(argv=argv,seconds=time.time()-t,exit_code=p.returncode));assert p.returncode==0
deps=[Path(x[2:])/'hnswlib/hnswlib.h' for x in argv if x.startswith('-I') and (Path(x[2:])/'hnswlib/hnswlib.h').exists()]
upstream += [Path(x) for x in argv if x.startswith('/') and Path(x).is_file() and not x.startswith(str(O))]
upstream += list((R/'benches/hnswlib').glob('*.h'))
freeze(O/'reviews/upstream.json',upstream);dump(O/'reviews/input_verification.json',dict(status='PASS',datasets=verified))
freeze(O/'reviews/before_queries.json',list((O/'inputs').rglob('*.*'))+list((O/'src').glob('*'))+list((O/'bin').glob('*'))+[O/'protocol.md'])
dump(O/'state.json',dict(status='PREPARED',new_NSG_calls=0,training_calls=0,QPS_calls=0,validation_read=False,heldout_read=False))
print('PREPARED',flush=True)
