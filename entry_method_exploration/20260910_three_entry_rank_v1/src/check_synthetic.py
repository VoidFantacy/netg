#!/usr/bin/env python3
import copy
import itertools
import os
import subprocess
import numpy as np
from common import OLD, RUN, dump, read

env={**os.environ, 'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
source=read(OLD/'exploration_5point_v1/reviews/synthetic_config.json')
dest=RUN/'reviews/synthetic_inputs';assert not dest.exists();dest.mkdir()
base=next(x for x in source['methods'] if x['family']=='fast30k_3').copy()
base.update({'legacy_heap_order':False,'canonical_entry_order':True,'hnsw_seed':20260828})
methods=[]
for L in [64,128,256,400,800]:
    for exact in [False,True]:
        x=base.copy();x.update({'family':'test_exact' if exact else 'test_hnsw','exact':exact,'L':L,
                              'name':('exact' if exact else 'hnsw')+f'_L{L}'})
        methods.append(x)
    methods.append({'family':'nsg_medoid','seed':20260828,'L':L,'name':f'nsg_L{L}','k':1})
config=source.copy();config.update({'methods':methods,'threads':1,'measure_wall':True,'split':'synthetic'})
dump(dest/'evaluate.json',config)
with (RUN/'logs/synthetic_evaluate.log').open('w') as log:
    subprocess.run([str(RUN/'bin/evaluate'),str(dest/'evaluate.json'),str(RUN/'reviews/synthetic_evaluate')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
hubs=np.fromfile(source['hub_ids'],dtype='<i4');h=len(hubs);n=source['num_queries'];d=source['dim']
q=np.fromfile(source['queries_file'],dtype='<f4').reshape(n,d)
p=np.fromfile(base['W'],dtype='<f4').reshape(h,d)
order=np.argsort(hubs,kind='stable');idx=order[np.argsort(-(q@p.T)[:,order],axis=1,kind='stable')[:,:3]]
expected=np.sort(hubs[idx],axis=1)
for L in [64,128,256,400,800]:
    actual=np.fromfile(RUN/f'reviews/synthetic_evaluate/exact_L{L}/entry_ids.i32',dtype='<i4').reshape(n,3)
    assert np.array_equal(actual,expected), 'exact top3 differs from independent NumPy sort'
# Twenty-four nonduplicate triples/query exercise cache, canonicalization, real entry injection, and independent scoring.
tuples=list(itertools.combinations(range(h),3))[:24]
triples=np.array([[sorted(t,key=lambda e:int(hubs[e])) for t in tuples] for _ in range(n)],dtype='<i4')
triples.tofile(dest/'triples.i32')
label={k:source[k] for k in ['dim','queries_file','gt_file','gt_k','hub_ids','index_path','num_queries']}
label.update({'hub_count':h,'contexts':4,'options':6,'triples_file':str(dest/'triples.i32'),
              'L':128,'threads':1,'logical_call_cap':n*24})
dump(dest/'labels.json',label)
with (RUN/'logs/synthetic_labels.log').open('w') as log:
    subprocess.run([str(RUN/'bin/label_triples'),str(dest/'labels.json'),str(RUN/'reviews/synthetic_labels')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
ids=np.fromfile(RUN/'reviews/synthetic_labels/ids.i32',dtype='<i4').reshape(n,24,10)
gt=np.fromfile(source['gt_file'],dtype='<i8').reshape(n,100)[:,:10]
expected_hits=np.array([[len(set(x)&set(gt[i])) for x in ids[i]] for i in range(n)],dtype='u1')
hits=np.fromfile(RUN/'reviews/synthetic_labels/hits.u8',dtype='u1').reshape(n,24)
assert np.array_equal(hits,expected_hits)
bad=copy.deepcopy(config);bad['threads']=2;dump(dest/'invalid_threads.json',bad)
denied=subprocess.run([str(RUN/'bin/evaluate'),str(dest/'invalid_threads.json'),str(RUN/'reviews/invalid_threads_must_not_exist')],env=env,capture_output=True,text=True)
assert denied.returncode!=0 and not (RUN/'reviews/invalid_threads_must_not_exist').exists()
dump(RUN/'reviews/synthetic_check.json',{'status':'PASS','five_L_three_entry_exact_and_hnsw':True,
     'independent_exact_top3_numpy':n*5,'label_hits_independently_checked':n*24,
     'reject_multithread_query_config':True,'fixture_identity':'reused historical synthetic fixture; no dataset evaluation'})
print('SYNTHETIC_CHECK_PASS',flush=True)
