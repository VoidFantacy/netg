"""Serial native full-fit/development comparison, exact unchanged-entry reuse."""
from shared import *
from native_cached import Native

ds=sys.argv[1];assert ds in DS;threads(15);resources();check(O/'reviews/models_before_queries.json')
assert time.time()<1789264200
resource.setrlimit(resource.RLIMIT_AS,(32*(1<<30),32*(1<<30)))
# Large immutable assets were freshly hashed in prepare; their cheap stat identity is checked again at use.
for x in read(O/'reviews/prebuild_freeze.json')['files']:
    if x['bytes']>64*(1<<20):
        st=Path(x['path']).stat();assert st.st_size==x['bytes'] and st.st_mtime_ns==x['mtime_ns']
jobs_path=O/'logs/jobs.json';jobs=read(jobs_path) if jobs_path.exists() else []
assert not any(x['dataset']==ds or x['status']=='RUNNING' for x in jobs)
assert sum(x['reserved_NSG'] for x in jobs)+45000<=90000
job=dict(dataset=ds,status='RUNNING',reserved_NSG=45000,pid=os.getpid(),started_at=time.time(),argv=sys.argv,
    affinity=sorted(os.sched_getaffinity(0)),proc_status=Path('/proc/self/status').read_text())
jobs.append(job);dump(jobs_path,jobs)
c=read(O/'inputs'/ds/'config.json');gt=np.fromfile(c['gt_file'],np.int64).reshape(22048,100)
anchor=dict(np.load(O/'inputs'/ds/'baseline.npz'));rows=np.arange(22048,dtype=np.int32);parity_rows=np.fromfile(c['parity_rows'],np.int32)
dest=O/'results'/ds;dest.mkdir();native=None;started=time.monotonic();records=[]
campaign=read(C/'state.json');campaign.update(status='E61_NATIVE_RUNNING',native_pids=[os.getpid()],dataset=ds,next_action='Wait for dataset completion and serial next dataset');dump(C/'state.json',campaign)
try:
    tick=time.monotonic();native=Native(c);load_seconds=time.monotonic()-tick
    for name in LABELS:
        assert time.time()<1789264800 and time.monotonic()-started<600
        threads(15);resources();folder=dest/name;folder.mkdir()
        W=np.fromfile(O/'models'/ds/name/'W.f32',np.float32).reshape(c['hub_count'],c['dim'])
        before=native.stats();top=native.build(W)
        t=time.monotonic();route=native.route(rows);route_seconds=time.monotonic()-t
        if name=='baseline':
            assert top==c['initial_topology_sha']
            assert route['entries'].tobytes()==anchor['entries'].tobytes() and route['route_ndc'].tobytes()==anchor['route_ndc'].tobytes()
        changed=np.flatnonzero((route['entries']!=anchor['entries']).any(1)).astype(np.int32)
        t=time.monotonic();patch=native.search_entries(changed,route['entries'][changed]);search_seconds=time.monotonic()-t
        t=time.monotonic();out={k:anchor[k].copy() for k in ['ids','distances','graph_ndc']};out.update(route)
        for k,v in patch.items():out[k][changed]=v
        cache_seconds=time.monotonic()-t
        t=time.monotonic();found=(out['ids'][:,:,None]==gt[:,None,:10]).any(1);out['hits']=found.sum(1).astype(np.uint8);out['hitmask']=(found*(1<<np.arange(10))).sum(1).astype(np.uint16)
        score_seconds=time.monotonic()-t
        t=time.monotonic();save(folder/'raw.npz',**out);save(folder/'patch.npz',changed_rows=changed,entries=out['entries'][changed],route_ndc=out['route_ndc'],parent_cache_sha=np.array(raw_digest(anchor)),cache_sha=np.array(raw_digest(out)),**patch)
        save(folder/'topology.npz',topology=native.data(5,np.int32));serialization_seconds=time.monotonic()-t
        t=time.monotonic();native.save(folder/'graph.hnsw');native.verify(folder/'graph.hnsw',parity_rows)
        pr={k:native.data(j,DTYPES[j]).reshape((-1,10) if j<2 else ((-1,3) if j==2 else (-1,))) for j,k in enumerate(FIELDS)}
        equal(pr,{k:out[k][parity_rows] for k in FIELDS});parity_seconds=time.monotonic()-t
        save(folder/'parity.npz',local_rows=parity_rows,**pr)
        after=native.stats();assert after['actual_threads']==1
        rec=dict(dataset=ds,model=name,new_NSG=len(changed),reused_NSG_rows=22048-len(changed),W_sha=digest(W),topology_sha=top,graph_sha=sha(folder/'graph.hnsw'),cache_sha=raw_digest(out),
            physical_NSG=after['NSG_calls']-before['NSG_calls'],physical_HNSW=after['HNSW_calls']-before['HNSW_calls'],build_seconds=after['build_seconds']-before['build_seconds'],
            route_seconds=route_seconds,new_NSG_seconds=search_seconds,cache_reconstruction_seconds=cache_seconds,score_seconds=score_seconds,serialization_seconds=serialization_seconds,parity_seconds=parity_seconds)
        assert rec['physical_NSG']==len(changed)+192 and rec['physical_HNSW']==66528//3
        dump(folder/'identity.json',rec);records.append(rec)
        dump(O/'state.json',dict(status='E61_QUERY_RUNNING',dataset=ds,model=name,native=native.stats(),pid=os.getpid()))
        print('MODEL_COMPLETE',ds,name,'new_NSG',len(changed),flush=True)
    stats=native.stats();assert stats['builds']==3 and stats['HNSW_calls']==66528 and stats['NSG_calls']==sum(x['new_NSG'] for x in records)+576<=44672
    result=dict(status='PASS_NATIVE_MISSING_TARGET_COMPARISON',dataset=ds,models=records,seconds=time.monotonic()-started,load_seconds=load_seconds,
        peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,gradient_updates=0,formal_QPS_points=0,**stats)
    dump(dest/'query_complete.json',result);job.update(status='COMPLETE',actual_NSG=stats['NSG_calls'],completed_at=time.time(),native=stats)
    print('DATASET_COMPLETE',json.dumps(result),flush=True)
except BaseException as exc:
    job.update(status='FAILED_RESERVED_RETAINED',error=repr(exc),completed_at=time.time(),native=native.stats() if native else None)
    raise
finally:
    if native is not None:native.close()
    dump(jobs_path,jobs);campaign=read(C/'state.json');campaign.update(status='E61_NATIVE_SAFE_BOUNDARY',native_pids=[],last_dataset=ds,last_native_status=job['status']);dump(C/'state.json',campaign)
