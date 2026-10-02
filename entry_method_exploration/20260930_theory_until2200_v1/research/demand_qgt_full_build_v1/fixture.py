import json,time
from pathlib import Path
import numpy as np
from lazy_gt import Replay,LazyGT,selector_scope
R=Path(__file__).resolve().parent;ROOT=R.parents[3]
def main():
    start=time.perf_counter();source=ROOT/'benches/run/build_fast_entry_variants.py'
    q=np.eye(4,dtype='f4');centroids=np.eye(4,dtype='f4');assignment=np.array([0,1,1,2],dtype='i8')[:,None]
    search=(np.zeros((4,1),dtype='f4'),assignment);replay=Replay(q,centroids,search);scope=selector_scope(source,lambda *a,**kw:replay)
    # Cluster1's first row collides; its second row supplies a new node. Cluster3 is empty.
    # Ravel must subsequently fetch row0's second candidate to complete H=4.
    gt=np.array([[10,11],[10,11],[12,13],[10,11]],dtype='i8')
    # To exhaust the first row in cluster1, cluster0 must already consume both its candidates.
    # A repeated candidate within the synthetic row supplies that collision without changing the selector.
    gt[1]=[10,10];gt[3]=[10,10]
    def backend(rows,phase):return np.tile(np.array([2.,1.],dtype='f4'),(len(rows),1)),gt[rows].copy()
    oracle=LazyGT(4,2,backend,batch=2);oracle.prefetch([0,1,3]);actual,detail=scope['choose_unique_gt_hubs'](q,oracle,4,20260828,25)
    expected,full_detail=scope['choose_unique_gt_hubs'](q,gt,4,20260828,25)
    assert np.array_equal(actual,expected) and detail==full_detail and actual.tolist()==[10,11,12,13]
    assert oracle.overlap_checks>0 and any(x['source']=='fallback' for x in oracle.trace)
    assert any(x['row']==2 and x['source']=='cluster' for x in oracle.trace)
    assert detail['empty_clusters']==1
    impossible=np.full_like(gt,7);errors=[]
    for obj in [impossible,LazyGT(4,2,lambda rows,phase:(np.zeros((len(rows),2),dtype='f4'),impossible[rows]),batch=2)]:
        try:scope['choose_unique_gt_hubs'](q,obj,4,20260828,25)
        except RuntimeError as e:errors.append(str(e))
    assert len(errors)==2 and errors[0]==errors[1]
    result={'status':'PASS','seconds':time.perf_counter()-start,'success_H':actual.tolist(),'details':detail,'trace':oracle.trace,'generation':oracle.generated,
        'overlap_checks':oracle.overlap_checks,'insufficient_unique_errors':errors,'synthetic_only':True,'real_GT_queries':0}
    with (R/'reviews/fixture.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print('FIXTURE PASS',flush=True)
if __name__=='__main__':main()
