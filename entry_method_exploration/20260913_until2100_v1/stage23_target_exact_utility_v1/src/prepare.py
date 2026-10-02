from common import *
threads();resources();assert not (O/'reviews/prequery_freeze.json').exists();started=time.monotonic()
paths=list((O/'src').glob('*.py'))+[O/'protocol.md',C/'session8_resource_protocol.json',E69/'bin/inject.so',E69/'src/inject.cpp',E69/'src/native.py'];sources=[];coverage=[];rankchecks=[]
dep=read(C/'stage7_multimode_index_v1/reviews/dependency_stat_verification.json')
for x in dep['sources']:
 st=Path(x['path']).stat();assert (st.st_size,st.st_mtime_ns)==(x['bytes'],x['mtime_ns'])
dump(O/'reviews/base_graph_identity.json',dep)
configs={}
for ds in DS:
 sc=read(E81/'inputs'/ds/'aux.json');old=read(E69/'inputs'/ds/'native.json');pro=read(E69/'inputs'/ds/'provenance.json');n=sc['num_queries'];d=sc['dim'];assert n==7952
 assert (sc['queries_file'],sc['index_path'],sc['dim'])==(old['queries_file'],old['index_path'],old['dim'])
 assert (sc['gt_file'],sc['row_ids'])==(pro['gt_file'],pro['row_ids'])
 for st in [E79,E80,E81]:
  cc=read(st/'inputs'/ds/'aux.json')
  for key in ['queries_file','gt_file','row_ids','index_path','num_queries','dim']:assert cc[key]==sc[key]
  paths.append(st/'inputs'/ds/'aux.json')
 configs[ds]=(sc,old,pro)
 for m in MODELS:
  p=source(ds,m);paths.extend([p] if p.suffix=='.npz' else [p/v[0] for v in FIELDS.values()])
 paths += [Path(sc[k]) for k in ['queries_file','gt_file','row_ids']]+[Path(old['hub_ids'])]
 for bank in BANKS:
  st=E79 if bank=='target10' else E81
  mc=next(x for x in read(st/'inputs'/ds/'aux.json')['methods'] if x['model_name']==bank)
  paths += [Path(mc[k]) for k in ['W','mapping','tie_ids','graph_file']]
 # Source-final seals verify only actually used artifacts, not repeated entire stage scans.
 for stage in [E69,E79,E80,E81]:
  seal=stage/'reviews/final_artifact_freeze.json';records={x['path']:x for x in read(seal)['files']}
  for p in set(paths):
   if str(p) in records:assert sha(p)==records[str(p)]['sha256'],p
  paths.append(seal)
freeze(O/'reviews/preanalysis_freeze.json',paths)
for ds in DS:
 sc,old,pro=configs[ds];n=sc['num_queries'];d=sc['dim'];q=np.fromfile(sc['queries_file'],np.float32).reshape(n,d);rows=np.fromfile(sc['row_ids'],np.int64);assert np.array_equal(rows,np.arange(2048,10000));hubs=np.fromfile(old['hub_ids'],np.int32)
 raw=[old_raw(ds,m) for m in MODELS];cache={};collisions=0
 for mi,a in enumerate(raw):
  for i,e in enumerate(a['entries']):
   assert np.all(np.diff(e)>0);key=(i,*map(int,e))
   if key in cache:
    mj,j=cache[key]
    for k in ['ids','distances','graph_ndc','hits','mask']:assert a[k][i].tobytes()==raw[mj][k][j].tobytes(),(ds,key,k)
    collisions+=1
   else:cache[key]=(mi,i)
 exact=np.empty((3,n,3),np.int32);nears=[];agrees=[];regrets=[]
 for bi,bank in enumerate(BANKS):
  st=E79 if bank=='target10' else E81;mc=next(x for x in read(st/'inputs'/ds/'aux.json')['methods'] if x['model_name']==bank)
  w=np.fromfile(mc['W'],np.float32).reshape(-1,d).astype(float);mapping=np.fromfile(mc['mapping'],np.int32);un,starts,counts=np.unique(mapping,return_index=True,return_counts=True);assert np.array_equal(un,hubs) and np.all(np.diff(mapping)>=0) and counts.max()<=3
  near=np.empty(n,bool);agree=np.empty(n,np.uint8);regret=np.empty(n);scalarrows=[];a=raw[MODELS.index(bank)];tick=time.monotonic()
  for start in range(0,n,512):
   end=min(n,start+512);qq=q[start:end].astype(float);ss=qq@w.T;ss=np.maximum.reduceat(ss,starts,axis=1);order=np.argsort(-ss,axis=1,kind='stable')[:,:4];exact[bi,start:end]=np.sort(hubs[order[:,:3]],axis=1)
   ii=np.arange(end-start);near[start:end]=ss[ii,order[:,2]]-ss[ii,order[:,3]]<=1e-5*np.maximum(1,np.linalg.norm(qq,axis=1))
   actual=np.searchsorted(hubs,a['entries'][start:end]);agree[start:end]=np.any(actual[:,:,None]==order[:,None,:3],axis=2).sum(1);regret[start:end]=np.take_along_axis(ss,order[:,:3],axis=1).sum(1)-np.take_along_axis(ss,actual,axis=1).sum(1);assert regret[start:end].min()>-1e-10
   if start in [0,4096]:
    scalar=np.array([sum(float(x)*float(y) for x,y in zip(q[start],v)) for v in w]);scalar=np.maximum.reduceat(scalar,starts)
    assert np.allclose(scalar,ss[0],atol=1e-12,rtol=1e-12)
    assert np.array_equal(np.sort(hubs[np.argsort(-scalar,kind='stable')[:3]]),exact[bi,start]);scalarrows.append(start)
  nears.append(near);agrees.append(agree);regrets.append(regret);rankchecks.append(dict(dataset=ds,bank=bank,physical_profiles=len(w),n=n,near_ties=int(near.sum()),exact_agreement=float((agree==3).mean()),mean_score_regret=float(regret.mean()),scalar_rows=scalarrows,ranking_seconds=time.monotonic()-tick))
 src=np.empty((3,n),np.int32);ix=np.empty((3,n),np.int32);missing={};mr=[];me=[];reuse=0;alias=0
 for bi in range(3):
  for i,e in enumerate(exact[bi]):
   key=(i,*map(int,e))
   if key in cache:src[bi,i],ix[bi,i]=cache[key];reuse+=1
   else:
    src[bi,i]=len(MODELS)
    if key not in missing:missing[key]=len(mr);mr.append(i);me.append(e)
    else:alias+=1
    ix[bi,i]=missing[key]
 inp=O/'inputs'/ds;inp.mkdir();save(inp/'routes.npz',source_rows=rows,exact_entries=exact,source_method=src,source_index=ix,missing_rows=np.array(mr,np.int32),missing_entries=np.array(me,np.int32).reshape(-1,3),near_ties=np.array(nears),agreements=np.array(agrees),regrets=np.array(regrets))
 cfg=dict(old);cfg.update(native_call_cap=2*(128+len(mr))+16+min(16,len(mr)),native_hnsw_cap=0)
 dump(inp/'native.json',cfg);dump(inp/'provenance.json',pro)
 coverage.append(dict(dataset=ds,logical_exact=3*n,old_reused=reuse,missing_unique=len(mr),new_aliases=alias,old_collisions=collisions,NSG_expected=cfg['native_call_cap']))
 paths += list(inp.glob('*'))
limit=dict(NSG_expected=sum(x['NSG_expected'] for x in coverage),NSG_hard_cap=96192,latest_launch=1789288500,query_hard_stop=1789289100,per_job_seconds=600,threads=1,CPU=15,output_cap_MiB=32,free_min_GiB=6.65)
assert limit['NSG_expected']<=limit['NSG_hard_cap'];dump(O/'config.locked.json',limit);dump(O/'reviews/cache_coverage.json',dict(status='PASS',datasets=coverage));dump(O/'reviews/ranking_verification.json',dict(status='PASS',records=rankchecks,seconds=time.monotonic()-started,full_score_queries=47712,native_bit_parity_claim=False))
freeze(O/'reviews/prequery_freeze.json',paths+[O/'config.locked.json',O/'reviews/cache_coverage.json',O/'reviews/ranking_verification.json']);dump(O/'logs/jobs.json',[]);dump(O/'state.json',dict(status='PREPARED_EXACT_TARGET_BANKS',day_goal_complete=False));print(json.dumps(coverage),flush=True);print(json.dumps(rankchecks),flush=True);resources()
