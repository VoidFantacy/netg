import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='8'
os.sched_setaffinity(0,range(8))
import hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;P=R.parent/'hybrid_full_build_cost_v1'
def main():
    start=time.perf_counter();C=json.loads((P/'config.locked.json').read_text());S=json.loads((R/'results/summary.json').read_text());checks=0
    for ds,c in C['datasets'].items():
        a=np.load(R/'results'/f'{ds}.npz');trace=json.loads((R/'results'/f'{ds}.trace.json').read_text());d=c['dimension']
        q=np.fromfile(c['qgt_queries'],'<f4').reshape(5000,d+1)[:,1:].copy();q/=np.maximum(np.linalg.norm(q,axis=1,keepdims=True),1e-12)
        centroid=a['centroids'].copy();centroid/=np.maximum(np.linalg.norm(centroid,axis=1,keepdims=True),1e-12)
        # New generated GT from the preceding full build, not the proxy's source array.
        gt=np.fromfile(Path(c['output'])/'qgt5000.ids.i64','<i8').reshape(5000,100)
        selected=[];seen=set();rows=[];ranks=[]
        for cluster in range(c['H']):
            members=np.where(a['assignment']==cluster)[0];assert len(members)>0
            s=q[members]@centroid[cluster];row=int(members[np.argsort(-s)[0]]);rows.append(row)
            rank=next(i for i,v in enumerate(gt[row]) if int(v) not in seen);candidate=int(gt[row,rank]);seen.add(candidate);selected.append(candidate);ranks.append(rank+1)
        assert rows==[x['row'] for x in trace] and ranks==[x['ranks_read'] for x in trace]
        assert all(x['source']=='cluster' and x['new_row'] for x in trace)
        assert np.array_equal(np.sort(rows),a['unique_rows']) and np.array_equal(rows,a['first_representatives'])
        assert np.array_equal(sorted(selected),a['selected_hubs'])
        rec=S['datasets'][ds];assert rec['unique_GT_rows_read']==len(rows)==c['H'] and rec['ranks_read_sum']==sum(ranks) and rec['ranks_read_max']==max(ranks)
        checks+=len(rows)
    for path,value in json.loads((R/'reviews/frozen.json').read_text())['inputs'].items():
        p=Path(path);assert {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}==value
    report={'status':'PASS','representative_rows_and_first_unused_ranks':checks,'independent_GT_source':'preceding newly generated exact QGT labels',
        'new_fits_or_GT_or_searches':0,'seconds':time.perf_counter()-start,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    with (R/'reviews/independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(report,flush=True)
if __name__=='__main__':main()
