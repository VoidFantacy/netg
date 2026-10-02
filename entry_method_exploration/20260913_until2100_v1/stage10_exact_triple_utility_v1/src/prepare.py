from common import *
import subprocess
threads();resources();assert not (O/'config.locked.json').exists()
paths=[];coverage=[]
# Whole base and NSG hashes were already checked upstream; retain that identity.
dep=read(E66/'reviews/dependency_stat_verification.json')
for x in dep['sources']:
 s=Path(x['path']).stat();assert (s.st_size,s.st_mtime_ns)==(x['bytes'],x['mtime_ns'])
dump(O/'reviews/base_graph_identity.json',dep)
for old in [E66,E68]:
 check(old/'reviews/final_artifact_freeze.json');paths.append(old/'reviews/final_artifact_freeze.json')
for ds,expected in zip(DS,[2308,1227]):
 sc=read(E66/'inputs'/ds/'aux.json');cc=read(E66/'inputs'/ds/'construction.json');n=sc['num_queries'];assert n==7952
 rows=np.fromfile(sc['row_ids'],np.int64);assert np.array_equal(rows,np.arange(2048,10000))
 assert Path(sc['queries_file']).stat().st_size==n*sc['dim']*4
 assert Path(sc['gt_file']).stat().st_size==n*100*8
 rank=dict(np.load(E68/'results'/ds/'aux.npz'));assert np.array_equal(rank['source_rows'],rows)
 raw=[old_raw(ds,m) for m in MODELS];hubs=np.fromfile(cc['hub_ids'],np.int32)
 exact=np.sort(np.stack([rank['exact_P_hubs'],rank['exact_mode_hubs']]),axis=2)
 assert np.all(np.diff(exact,axis=2)>0) and np.isin(exact,hubs).all()
 cache={};collisions=0
 for mi,a in enumerate(raw):
  assert len(a['ids'])==n and np.all(np.diff(a['entries'],axis=1)>0)
  for i,e in enumerate(a['entries']):
   key=(i,*map(int,e))
   if key in cache:
    mj,j=cache[key]
    for k in ['ids','distances','graph_ndc','hits','mask']:assert a[k][i].tobytes()==raw[mj][k][j].tobytes(),(ds,key,k)
    collisions+=1
   else:cache[key]=(mi,i)
 src=np.empty((2,n),np.int32);ix=np.empty((2,n),np.int32);missing={};mr=[];me=[];reuse=0;alias=0;logical_missing=0
 for policy in range(2):
  for i,e in enumerate(exact[policy]):
   key=(i,*map(int,e))
   if key in cache:src[policy,i],ix[policy,i]=cache[key];reuse+=1
   else:
    logical_missing+=1;src[policy,i]=3
    if key not in missing:missing[key]=len(mr);mr.append(i);me.append(e)
    else:alias+=1
    ix[policy,i]=missing[key]
 assert len(mr)==expected
 inp=O/'inputs'/ds;inp.mkdir();save(inp/'routes.npz',source_rows=rows,exact_entries=exact,source_method=src,source_index=ix,missing_rows=np.array(mr,np.int32),missing_entries=np.array(me,np.int32))
 cfg=dict(dataset=ds,threads=1,query_cpu=15,L=128,dim=sc['dim'],hub_count=cc['hub_count'],hub_ids=cc['hub_ids'],num_queries=n,queries_file=sc['queries_file'],index_path=sc['index_path'],native_call_cap=2*(n+expected)+32,native_hnsw_cap=0)
 dump(inp/'native.json',cfg);dump(inp/'provenance.json',dict(namespace=cc['namespace'],source_rows='router_train[2048:10000]',source_config=str(E66/'inputs'/ds/'aux.json'),gt_file=sc['gt_file'],row_ids=sc['row_ids'],L=128,K=10,metric='raw inner product',entry_order='ascending unique real hub IDs',historically_exposed=True,feedback_role='auxiliary selection training',final_validation_used=False))
 coverage.append(dict(dataset=ds,logical_exact=2*n,old_reused=reuse,logical_missing=logical_missing,missing_unique=len(mr),new_aliases=alias,old_collisions=collisions,NSG_expected=cfg['native_call_cap']))
 paths += [E66/'inputs'/ds/'aux.json',E66/'inputs'/ds/'construction.json',E68/'results'/ds/'aux.npz',Path(sc['queries_file']),Path(sc['gt_file']),Path(sc['row_ids']),Path(cc['hub_ids'])]
 for m in sc['methods']:
  paths += [Path(m[k]) for k in ['W','mapping','tie_ids','graph_file']]
  paths += list((E66/'results'/ds/'aux'/m['name']).glob('*'))
assert sum(x['old_reused'] for x in coverage)==28102 and sum(x['NSG_expected'] for x in coverage)==38942
dump(O/'reviews/cache_coverage.json',dict(status='PASS',datasets=coverage))
argv=read(E37/'bin/environment.build.json')['argv'];argv=[str(O/'src/inject.cpp') if x==str(E37/'src/environment.cpp') else str(O/'bin/inject.so') if x==str(E37/'bin/environment.so') else x for x in argv]
tick=time.monotonic()
with (O/'logs/build.log').open('x') as f:p=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,timeout=180)
assert p.returncode==0
dump(O/'bin/build.json',dict(argv=argv,seconds=time.monotonic()-tick,exit_code=p.returncode,binary=identity(O/'bin/inject.so')))
# Freeze actual compilation sources, libraries and included local headers.
paths += [Path(x) for x in argv if Path(x).is_file()]
paths += list((E37/'src').glob('*.cpp'))+list((R/'ACSG').glob('*.h'))+list((R/'benches/hnswlib').glob('*.h'))+[E46/'src/cache_environment.cpp']
dump(O/'config.locked.json',dict(datasets=DS,threads=1,CPU=15,L=128,K=10,NSG_expected=38942,NSG_hard_cap=40000,HNSW=0,builds=0,output_cap_MiB=32,free_min_GiB=7,latest_launch=1789274400,query_hard_stop=1789275000,per_job_seconds=600,gate='exact mode beats both exact P and approx P in full hits; halves nonnegative; failures nonincrease; graph NDC <=1.01; exact mode >= approx mode hits'))
paths += [O/'protocol.md',O/'config.locked.json']+list((O/'src').glob('*'))+list((O/'bin').glob('*'))+list((O/'inputs').rglob('*'))
freeze(O/'reviews/prequery_freeze.json',[p for p in paths if p.is_file()]);dump(O/'logs/jobs.json',[])
dump(O/'state.json',dict(status='PREPARED_EXACT_TRIPLE_UTILITY',NSG=0,HNSW=0,builds=0,day_goal_complete=False))
print(json.dumps(coverage),flush=True);resources()
