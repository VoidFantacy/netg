"""Serial native replay of predetermined C and three E53 actions; no learner."""
from shared import *
from native_cached import Native

ds=sys.argv[1]; assert ds in DS
threads(); resources(); check_freeze(); assert time.time()<LATEST_LAUNCH
resource.setrlimit(resource.RLIMIT_AS,(32*(1<<30),32*(1<<30)))
ledger=O/'logs/jobs.json'; jobs=read(ledger) if ledger.exists() else []
assert not any(x['dataset']==ds or x['status']=='RUNNING' for x in jobs)
assert sum(x['reserved_NSG'] for x in jobs)+340000<=680000
job=dict(dataset=ds,status='RUNNING',reserved_NSG=340000,pid=os.getpid(),started_at=time.time(),
         proc_status=Path('/proc/self/status').read_text(),affinity=sorted(os.sched_getaffinity(0)))
jobs.append(job); dump(ledger,jobs)
campaign=read(C/'state.json'); campaign.update(status='STAGE1_NATIVE_RUNNING',native_pids=[os.getpid()],dataset=ds,
    pid_scope='Sandbox process namespace; tool session managed until process exit',next_action='Wait for serial dataset completion then run second dataset')
dump(C/'state.json',campaign)
c=read(O/'inputs'/ds/'config.json'); P=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim'])
gt=np.fromfile(c['gt_file'],np.int64).reshape(2064,100)
dest=O/'results'/ds; dest.mkdir(); contexts=[x for x in read(O/'inputs/contexts.json') if x['dataset']==ds]
qrows=np.arange(2048,dtype=np.int32); costs=dict(route_seconds=0.,new_NSG_seconds=0.,cache_reconstruction_seconds=0.,score_seconds=0.,serialization_seconds=0.,parity_seconds=0.)
started=time.monotonic(); load_started=time.monotonic(); native=None
normal_NSG=0; reused=0; parity_NSG=0; parity_HNSW=0; completed=[]

def guard():
    assert time.time()<QUERY_STOP and time.monotonic()-started<900, 'bounded query deadline'
    threads(); resources()

def write_raw(path, out, **extra):
    t=time.monotonic(); save(path,**out,**extra); costs['serialization_seconds']+=time.monotonic()-t

def evaluate_cached(parent, folder):
    global normal_NSG,reused
    guard(); t=time.monotonic(); route=native.route(qrows);costs['route_seconds']+=time.monotonic()-t
    t=time.monotonic(); changed=np.flatnonzero((route['entries']!=parent['entries']).any(1)).astype(np.int32)
    out={k:parent[k].copy() for k in ['ids','distances','graph_ndc']}; out.update(route)
    costs['cache_reconstruction_seconds']+=time.monotonic()-t
    t=time.monotonic(); patch=native.search_entries(changed,route['entries'][changed]);costs['new_NSG_seconds']+=time.monotonic()-t
    t=time.monotonic()
    for k,v in patch.items():out[k][changed]=v
    costs['cache_reconstruction_seconds']+=time.monotonic()-t
    t=time.monotonic();out['hits']=score(out['ids'],gt[:2048]);costs['score_seconds']+=time.monotonic()-t
    normal_NSG+=len(changed); reused+=2048-len(changed)
    write_raw(folder/'raw.npz',out)
    write_raw(folder/'patch.npz',patch,changed_rows=changed,entries=route['entries'][changed],route_ndc=route['route_ndc'],
              parent_cache_sha=np.array(raw_digest(parent)),cache_sha=np.array(raw_digest(out)))
    return out,len(changed)

def parity(folder, rows, expected):
    global parity_NSG,parity_HNSW
    t=time.monotonic();native.save(folder/'graph.hnsw');native.verify(folder/'graph.hnsw',rows)
    raw={k:native.data(j,DTYPES[j]).reshape((-1,10) if j<2 else ((-1,3) if j==2 else (-1,))) for j,k in enumerate(FIELDS)}
    equal(raw,expected); costs['parity_seconds']+=time.monotonic()-t
    write_raw(folder/'parity.npz',raw,local_rows=rows)
    parity_NSG+=3*len(rows);parity_HNSW+=2*len(rows)

try:
    native=Native(c);costs['load_seconds']=time.monotonic()-load_started
    top=native.build(P); t=time.monotonic();full=native.run(np.arange(2064,dtype=np.int32));costs['anchor_combined_search_seconds']=time.monotonic()-t;normal_NSG+=2064
    full['hits']=score(full['ids'],gt)
    old=dict(np.load(E37/'results'/ds/'baseline.npz'))
    equal({k:full[k][2048:] for k in FIELDS},{k:old[k][:16] for k in FIELDS})
    assert np.array_equal(full['hits'][2048:],old['hits'][:16])
    base={k:full[k][:2048].copy() for k in FIELDS+['hits']}
    anchor=dest/'anchor';anchor.mkdir();write_raw(anchor/'raw.npz',full)
    rows=np.r_[np.arange(8),np.arange(1024,1032),np.arange(2048,2064)].astype(np.int32)
    parity(anchor,rows,{k:full[k][rows] for k in FIELDS})
    dump(anchor/'identity.json',dict(W_sha=digest(P),topology_sha=top,graph_sha=sha(anchor/'graph.hnsw'),cache_sha=raw_digest(full)))
    for rec in contexts:
        guard(); src=Path(rec['source']);step=rec['step'];cpstep=((step-1)//20)*20
        with np.load(src/'checkpoints'/f'{cpstep:04}.npz') as cp: W=cp['W'].copy()
        for st in range(cpstep+1,step):
            with np.load(src/'trajectory'/f'{st:04}.npz') as t: W[int(t['slot'])]=t['next_row']
        assert digest(W)==rec['current_W_sha']; slot=rec['slot'];current_row=W[slot].copy()
        frozen=dict(np.load(O/'inputs'/ds/'contexts'/f"{rec['name']}.npz"))
        assert current_row.tobytes()==frozen['current_row'].tobytes()
        current=None
        for i,label in enumerate(['C','D25','D50','D100']):
            guard();W[slot]=current_row if i==0 else frozen['d_rows'][i-1]
            expectedW=rec['current_W_sha'] if i==0 else rec['d_W_sha'][i-1]
            expectedTop=rec['current_topology_sha'] if i==0 else rec['d_topology_sha'][i-1]
            assert digest(W)==expectedW
            topology=native.build(W);assert topology==expectedTop
            folder=dest/rec['name']/label;folder.mkdir(parents=True)
            out,nnew=evaluate_cached(base if i==0 else current,folder)
            write_raw(folder/'topology.npz',dict(topology=native.data(5,np.int32)))
            # e46 route/search preserve topology; native data field5 remains build topology.
            if rec['physical_parity']:
                rows=np.r_[np.arange(8),np.arange(1024,1032)].astype(np.int32)
                parity(folder,rows,{k:out[k][rows] for k in FIELDS})
            dump(folder/'identity.json',dict(W_sha=expectedW,topology_sha=topology,cache_sha=raw_digest(out),new_NSG=nnew,
                 graph_sha=sha(folder/'graph.hnsw') if rec['physical_parity'] else None,source_context=rec['name'],point=label))
            if i==0:current=out
        completed.append(rec['name'])
        dump(O/'state.json',dict(status='FIXED_ACTION_QUERY_RUNNING',dataset=ds,completed_contexts=len(completed),pid=os.getpid(),native=native.stats(),next_context=None if len(completed)==40 else contexts[len(completed)]['name']))
        print('CONTEXT',ds,rec['name'],native.stats()['NSG_calls'],flush=True)
    stat=native.stats(); assert stat['actual_threads']==1 and stat['builds']==161 and stat['HNSW_calls']==330320
    assert stat['NSG_calls']==normal_NSG+parity_NSG<=330608 and parity_NSG==864 and parity_HNSW==576
    assert reused+(normal_NSG-2064)==160*2048
    result=dict(status='PASS_NATIVE_FIXED_ACTION_REPLAY',dataset=ds,contexts=len(completed),points=160,normal_NSG=normal_NSG,
        parity_NSG=parity_NSG,reused_NSG_outputs=reused,logical_development_rows=327680,original_train_parity_rows=16,
        optimizer_updates=0,formal_QPS_points=0,seconds=time.monotonic()-started,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        component_costs=costs,**stat)
    dump(dest/'query_complete.json',result);job.update(status='COMPLETE',actual_NSG=stat['NSG_calls'],completed_at=time.time(),native=stat)
    print('DATASET_COMPLETE',json.dumps(result),flush=True)
except BaseException as exc:
    job.update(status='FAILED_RESERVED_RETAINED',error=repr(exc),completed_at=time.time(),native=native.stats() if native else None)
    raise
finally:
    if native is not None:native.close()
    dump(ledger,jobs)
    campaign=read(C/'state.json');campaign.update(native_pids=[],status='STAGE1_NATIVE_SAFE_BOUNDARY',last_dataset=ds,last_native_status=job['status'],next_action='Second dataset or independent verification; inspect stage logs/jobs.json')
    dump(C/'state.json',campaign)
