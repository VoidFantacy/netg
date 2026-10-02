from common import *
import numpy as np

def protect():
    assert read(E29/'state.json')['status']=='COMPLETE'
    assert read(E29/'reviews/final_audit.json')['status']=='PASS'
    old=read(E29/'reviews/protected_before.json')+read(E29/'reviews/protected_additional_before.json')
    protected={x['path']:x for x in old}
    for p in E29.rglob('*'):
        if p.is_file():protected[str(p)]=identity(p)
    for x in protected.values():assert identity(x['path'])==x,x['path']
    dump(O/'reviews/protected_before.json',list(protected.values()))
    for ds in DS:
        for split in ['fit','cal','audit','validation']:
            c=read(E29/'inputs'/ds/split/'config.json')
            c.update(protocol_sha256=sha(O/'protocol.md'),query_cpu=15,threads=1)
            dump(O/'inputs'/ds/split/'config.json',c)
    dump(O/'reviews/preflight.json',dict(status='PASS',protected_files=len(protected),free_bytes=shutil.disk_usage(O).free))

def teachers(ds):
    c=read(O/'inputs'/ds/'fit/config.json');n=c['num_queries']
    labels=E28/'labels'/ds;proposals=E28/'inputs'/ds/'proposals'
    gt=np.fromfile(c['gt_file'],np.int64).reshape(n,100)[:,:10]
    ids=np.memmap(labels/'ids.i32',np.int32,mode='r',shape=(n,56,10))
    hits=np.fromfile(labels/'hits.u8',np.uint8).reshape(n,56)
    masks=np.fromfile(labels/'masks.u16',np.uint16).reshape(n,56)
    ndc=np.fromfile(labels/'graph_ndc.u32',np.uint32).reshape(n,56)
    for b in range(0,n,256):
        found=(ids[b:b+256,:,:,None]==gt[b:b+256,None,None,:]).any(2)
        assert np.array_equal(found.sum(2),hits[b:b+256])
        assert np.array_equal((found*(1<<np.arange(10))).sum(2),masks[b:b+256])
        assert (np.diff(np.sort(ids[b:b+256],axis=2),axis=2)!=0).all()
    ts=np.fromfile(proposals/'triples.i32',np.int32).reshape(n,56,3)
    bs=np.fromfile(E29/'inputs'/ds/'teachers/baseline_slot.i32',np.int32)
    t0=np.fromfile(labels/'teacher_slot.i32',np.int32);rr=np.arange(n)
    top=hits==hits.max(1,keepdims=True)
    mincost=np.where(top,ndc,np.iinfo(np.uint32).max).min(1)
    good=top&(ndc==mincost[:,None]);single=np.zeros_like(good);single[rr,t0]=True
    assert good[rr,t0].all() and good.any(1).all()
    assert np.array_equal(ts[rr,t0],np.fromfile(labels/'teacher.i32',np.int32).reshape(n,3))
    base=np.fromfile(E29/'inputs'/ds/'teachers/baseline.i32',np.int32).reshape(n,3)
    assert np.array_equal(ts[rr,bs],base)
    gain=hits.max(1)>hits[rr,bs]
    assert np.array_equal(gain,np.fromfile(E29/'inputs'/ds/'teachers/headroom.u8',np.uint8).astype(bool))
    dest=O/'inputs'/ds/'teachers';dest.mkdir()
    for name,array,dtype in [('single.u8',single,np.uint8),('multi.u8',good,np.uint8),('headroom.u8',gain,np.uint8),('teacher_slot.i32',t0,np.int32),('baseline_slot.i32',bs,np.int32)]:
        array.astype(dtype).tofile(dest/name)
    stats=[]
    for group,mask in [('all',np.ones(n,bool)),('headroom',gain),('no_headroom',~gain)]:
        nums=good.sum(1)[mask];highest=top.sum(1)[mask]
        stats.append(dict(dataset=ds,group=group,queries=int(mask.sum()),maxhit_ties_mean=float(highest.mean()),maxhit_ties_median=float(np.median(highest)),
             equivalent_mean=float(nums.mean()),equivalent_median=float(np.median(nums)),multiple_fraction=float((nums>1).mean()),all56_fraction=float((nums==56).mean()),
             baseline_recall_pct=float(hits[rr,bs][mask].mean()*10),teacher_recall_pct=float(hits.max(1)[mask].mean()*10),
             baseline_graph_ndc=float(ndc[rr,bs][mask].mean()),teacher_graph_ndc=float(mincost[mask].mean())))
    report=dict(status='PASS',dataset=ds,logical_labels_verified=n*56,new_label_calls=0,statistics=stats,
        source_files=[identity(labels/name) for name in ['ids.i32','hits.u8','masks.u16','graph_ndc.u32','teacher_slot.i32','teacher.i32']]+[identity(proposals/'triples.i32')],
        teacher_files=[identity(p) for p in dest.iterdir()])
    dump(dest/'verification.json',report)
    print(json.dumps(stats),flush=True)
    return report

if __name__=='__main__':
    freeze(O/'reviews/protocol_lock.json',[O/'protocol.md'])
    assert shutil.disk_usage(O).free>10*(1<<30)
    started=time.time();protect();rows=[teachers(ds) for ds in DS]
    dump(O/'reviews/teacher_verification.json',dict(status='PASS',datasets=rows,seconds=time.time()-started))
    dump(O/'state.json',dict(status='PREPARED_OBJECTIVE_TESTS_PENDING',training_runs=0,real_search_calls=0,heldout_access=False))
