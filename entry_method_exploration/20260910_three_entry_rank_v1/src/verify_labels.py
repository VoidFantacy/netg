#!/usr/bin/env python3
import numpy as np
from common import DATASETS, RUN, dump, identity, read

reports=[]
for dataset in DATASETS:
    inp=RUN/'inputs'/dataset/'fit';out=RUN/'labels'/dataset
    complete=read(out/'complete.json');assert complete['status']=='COMPLETE'
    n=read(inp/'config.json')['num_queries']
    ids=np.fromfile(out/'ids.i32',dtype='<i4').reshape(n,24,10)
    hits=np.fromfile(out/'hits.u8',dtype='u1').reshape(n,24)
    masks=np.fromfile(out/'masks.u16',dtype='<u2').reshape(n,24)
    ndc=np.fromfile(out/'graph_ndc.u32',dtype='<u4').reshape(n,24)
    gt=np.fromfile(inp/'gt.i64',dtype='<i8').reshape(n,100)[:,:10]
    triples=np.fromfile(inp/'triples.i32',dtype='<i4').reshape(n,24,3)
    assert (ndc>=3).all() and np.all(np.diff(np.sort(ids,axis=2),axis=2)!=0)
    assert np.all(np.diff(np.sort(gt,axis=1),axis=1)!=0)
    for begin in range(0,n,256):
        stop=min(begin+256,n)
        member=(ids[begin:stop,:,:,None]==gt[begin:stop,None,None,:]).any(axis=2)
        independent_hits=member.sum(axis=2).astype('u1')
        independent_masks=(member*(1<<np.arange(10,dtype='<u2'))).sum(axis=2).astype('<u2')
        assert np.array_equal(independent_hits,hits[begin:stop])
        assert np.array_equal(independent_masks,masks[begin:stop])
    # The Fast baseline appears as the first option in each of the first three contexts.
    assert np.array_equal(triples[:,0],triples[:,6]) and np.array_equal(triples[:,0],triples[:,12])
    assert np.array_equal(ids[:,0],ids[:,6]) and np.array_equal(ids[:,0],ids[:,12])
    assert np.array_equal(ndc[:,0],ndc[:,6]) and np.array_equal(ndc[:,0],ndc[:,12])
    records=[identity(out/name) for name in ['hits.u8','masks.u16','graph_ndc.u32','ids.i32']]
    reports.append({'dataset':dataset,'status':'PASS','logical_triples_verified':n*24,
       'physical_label_calls':complete['physical_calls'],'entry_count':3,
       'all_returned_ids_unique':True,'independent_gt10_hits_masks':True,'cached_baseline_identity':True,
       'files':records})
    print(dataset,'LABELS_VERIFIED',flush=True)
dump(RUN/'reviews/labels_verified.json',{'status':'PASS','datasets':reports})
