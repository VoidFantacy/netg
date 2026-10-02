from common import *
import struct
def graph_verify(path,W,labels):
    data=Path(path).read_bytes();head=struct.unpack_from('<6QiI3QdQ',data);off,mx,n,size,label,coord,level,entry,M,M0,m,mult,ef=head
    start=struct.calcsize('<6QiI3QdQ');assert off==0 and mx==n==len(W) and M==m==16 and M0==32 and ef==200 and label-coord==W.shape[1]*4
    cursor=start+n*size;uppers=[];levels=[]
    for i in range(n):
        nb=struct.unpack_from('<I',data,cursor)[0];cursor+=4;assert nb%(M*4+4)==0;levels.append(nb//(M*4+4));uppers.append(data[cursor:cursor+nb]);cursor+=nb
    assert cursor==len(data) and max(levels)==level
    for i in range(n):
        row=start+i*size;assert struct.unpack_from('<Q',data,row+label)[0]==int(labels[i]) and data[row+coord:row+label]==W[i].tobytes()
        blocks=[data[row:row+M0*4+4]]+[uppers[i][j*(M*4+4):(j+1)*(M*4+4)] for j in range(levels[i])]
        for lev,b in enumerate(blocks):
            count=struct.unpack_from('<H',b)[0];assert count<=(M0 if lev==0 else M)
            adj=np.frombuffer(b,'<u4',count=count,offset=4);assert (adj<n).all() and len(np.unique(adj))==count and i not in adj
    return dict(path=str(path),physical_profiles=n,sha256=sha(path),unique_external_labels=len(set(map(int,labels))))
def load_point(folder):
    return dict(ids=np.fromfile(folder/'ids.i32',np.int32).reshape(-1,10),distances=np.fromfile(folder/'distances.f32',np.float32).reshape(-1,10),
        entries=np.fromfile(folder/'entry_ids.i32',np.int32).reshape(-1,3),route_ndc=np.fromfile(folder/'route_ndc.u32',np.uint32),graph_ndc=np.fromfile(folder/'graph_ndc.u32',np.uint32),
        hits=np.fromfile(folder/'hits.u8',np.uint8),masks=np.fromfile(folder/'hitmask.u16',np.uint16))
def verify_point(ds,split,model):
    c=read(O/'inputs'/ds/(split+'.json'));m=next(x for x in c['methods'] if x['model_name']==model);n=c['num_queries'];d=c['dim'];out=O/'results'/ds/split
    rows=np.fromfile(c['row_ids'],np.int64)[:n];assert np.array_equal(rows,np.fromfile(out/'row_ids.i64',np.int64))
    point=load_point(out/m['name']);gt=np.fromfile(c['gt_file'],np.int64,count=n*100).reshape(n,100);q=np.fromfile(c['queries_file'],np.float32,count=n*d).reshape(n,d)
    hits=ihits(point['ids'],gt);masks=np.array([sum((1<<k) for k,v in enumerate(g[:10]) if int(v) in set(map(int,ids))) for ids,g in zip(point['ids'],gt)],np.uint16)
    assert np.array_equal(hits,point['hits']) and np.array_equal(masks,point['masks']);assert np.all(np.diff(point['entries'],axis=1)>0)
    ids=point['ids'];assert ids.min()>=0 and ids.max()<c['base_count'] and np.all(np.diff(np.sort(ids,axis=1),axis=1)>0)
    W=np.fromfile(m['W'],np.float32).reshape(m['hub_count'],d);mapping=np.fromfile(m['mapping'],np.int32)
    graph=graph_verify(out/(m['name']+'.hnsw'),W,np.arange(len(W)) if m.get('slot_labels') else mapping)
    if m.get('multi_profile'):
        slots=np.fromfile(out/m['name']/'candidate_slots.i32',np.int32).reshape(n,7);dist=np.fromfile(out/m['name']/'candidate_distances.f32',np.float32).reshape(n,7)
        labels=np.fromfile(out/m['name']/'router_labels.i32',np.int32).reshape(n,3);assert slots.min()>=0 and slots.max()<len(W)
        assert np.all(np.diff(np.sort(slots,axis=1),axis=1)>0)
        for i in range(n):
            ordered=sorted(zip(dist[i],slots[i]));assert [int(s) for _,s in ordered]==list(slots[i]);chosen=[];chosen_slots=[]
            for _,slot in ordered:
                hub=int(mapping[slot])
                if hub not in chosen:chosen.append(hub);chosen_slots.append(int(slot))
                if len(chosen)==3:break
            pairs=sorted(zip(chosen,chosen_slots));assert np.array_equal(point['entries'][i],[a for a,b in pairs]) and np.array_equal(labels[i],[b for a,b in pairs])
        # Float64 scalar reference checks all seven distances on a fixed 1/137 sample; native plain/count uses exact bits for all queries.
        for i in range(0,n,137):
            ref=1-W[slots[i]].astype(float)@q[i].astype(float);assert np.allclose(ref,dist[i],atol=2e-5,rtol=2e-5)
    record=next(x for x in read(out/'results.json')['methods'] if x['model_name']==model)
    assert record['total_hits']==int(hits.sum()) and record['failed_queries']==int((hits==0).sum())
    assert abs(record['mean_total_ndc']-np.mean(point['route_ndc'].astype(float)+point['graph_ndc']))<1e-10
    assert record['qps'] is None and record['full_plain_count_parity_queries']==n and record['original_kernel_parity_queries']==16
    return point,graph
def baseline_reference(ds,split,n):
    if split=='aux':return load_point(C/'stage5_frozen_pool_aux_v1/results'/ds/'baseline_L128')
    c=read(O/'inputs'/ds/'construction.json');raw=dict(np.load(c['supervision_source']));return {k:raw[k][:n] for k in FIELDS}
if __name__=='__main__':
    threads();resources();check(O/'reviews/prequery_freeze.json');jobs=read(O/'logs/jobs.json')
    assert len(jobs)==2 and all(j['split']=='preflight' and j['status']=='COMPLETE' for j in jobs)
    graphs=[];count=0
    for ds in DS:
        for m in ['baseline','duplicate3P','mode3P']:
            point,graph=verify_point(ds,'preflight',m);graphs.append(graph);count+=len(point['ids'])
            if m=='baseline':equal(point,baseline_reference(ds,'preflight',128))
    dump(O/'reviews/preflight_verification.json',dict(status='PASS',independent_query_sets=count,baseline_recovered_queries=256,graphs=graphs,source_and_raw_count_original_parity=True))
    dump(O/'reviews/preflight_graph_freeze.json',dict(epoch=time.time(),files=[identity(g['path']) for g in graphs]))
    print('PREFLIGHT_PASS',count,flush=True)
