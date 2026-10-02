from common import *
seen={}
def verify_slots(folder,mapping,W,q,entries):
    n=len(q);slots=np.fromfile(folder/'candidate_slots.i32',np.int32).reshape(n,7);dist=np.fromfile(folder/'candidate_distances.f32',np.float32).reshape(n,7)
    labels=np.fromfile(folder/'router_labels.i32',np.int32).reshape(n,3);assert slots.min()>=0 and slots.max()<len(mapping)
    assert np.all(np.diff(np.sort(slots,axis=1),axis=1)>0) and np.all(np.diff(entries,axis=1)>0)
    key=(digest(W),digest(q));fingerprint=(digest(slots),digest(dist),digest(entries),digest(labels))
    if key in seen:assert seen[key]==fingerprint
    seen[key]=fingerprint
    for i in range(n):
        ordered=sorted(zip(dist[i],slots[i]));assert [int(s) for _,s in ordered]==list(slots[i]);selected={}
        for _,slot in ordered:
            if int(mapping[slot]) not in selected:selected[int(mapping[slot])]=int(slot)
            if len(selected)==3:break
        ordered=sorted(selected.items());assert np.array_equal(entries[i],[h for h,s in ordered]) and np.array_equal(labels[i],[s for h,s in ordered])
    for i in range(0,n,137):
        ref=1-W[slots[i]].astype(float)@q[i].astype(float);assert np.allclose(ref,dist[i],atol=2e-5,rtol=2e-5)
