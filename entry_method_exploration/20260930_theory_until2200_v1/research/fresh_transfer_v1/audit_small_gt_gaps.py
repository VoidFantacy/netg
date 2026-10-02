"""Audit every changed K1 hit with the predeclared <=2e-5 GT1/GT2 gap flag.

This is a label-validity follow-up, not a rerun, method selection, or GT edit.
All such queries across every comparison are included; no sign filter is used.
"""
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='8'
os.sched_setaffinity(0,range(8))
import hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
    start=time.perf_counter();assert json.loads((R/'reviews/independent_audit.json').read_text())['status']=='PASS'
    config=json.loads((R/'config.locked.json').read_text());summary=json.loads((R/'results/summary.json').read_text());saved=np.load(R/'results/aligned_hits_and_bootstrap.npz')
    paths=[Path(__file__),R/'config.locked.json',R/'results/summary.json',R/'results/aligned_hits_and_bootstrap.npz'];freeze={str(p):ident(p) for p in paths}
    with (R/'reviews/small_gap_audit_frozen.json').open('x') as f:json.dump({'unix':time.time(),'files':freeze,'selection':'all changed K1 hits with stored GT1/GT2 gap <=2e-5; no method or sign selection'},f,indent=2)
    rows=[]
    for case,c in config['cases'].items():
        n,d=c['n'],c['dimension'];gt=np.fromfile(c['gt'],'<i4').reshape(n,100);ip=np.fromfile(R/'inputs'/case/'gt_ip.f32','<f4').reshape(n,100);changed=np.zeros(n,dtype=bool)
        for point in summary['cases'][case]['points']:
            if point['K']!=1:continue
            for item in point['comparisons']:
                a,b=item['method'],item['reference'];changed|=saved[f'{case}__K1__{a}__hits']!=saved[f'{case}__K1__{b}__hits']
        flagged=np.flatnonzero(changed & ((ip[:,0]-ip[:,1])<=2e-5))
        if not len(flagged):continue
        base=np.memmap(c['base'],'<f4',mode='r').reshape(c['base_n'],d+1)[:,1:];queries=np.fromfile(R/'inputs'/case/'queries.f32','<f4').reshape(n,d)
        for qid in flagged:
            t=time.perf_counter();query=queries[qid].astype('f8');ids=[];scores=[]
            for lo in range(0,c['base_n'],65536):
                block=np.array(base[lo:lo+65536],dtype='f8')@query;chosen=np.argpartition(block,-2)[-2:];ids.extend((chosen+lo).tolist());scores.extend(block[chosen].tolist())
            ids=np.asarray(ids);scores=np.asarray(scores);order=np.lexsort((ids,-scores));top=ids[order[:2]];values=scores[order[:2]]
            assert int(top[0])==int(gt[qid,0]) and values[0]>values[1]
            rows.append({'case':case,'query_row':int(qid),'original_GT1':int(gt[qid,0]),'float64_top2_ids':top.tolist(),'float64_top2_scores':values.tolist(),
                'float64_gap':float(values[0]-values[1]),'stored_float32_gap':float(ip[qid,0]-ip[qid,1]),'seconds':time.perf_counter()-t})
    for p,v in freeze.items():assert ident(p)==v
    result={'status':'PASS','seconds':time.perf_counter()-start,'checked_queries':rows,'new_GT_labels':0,'additional_full_base_float64_checks':len(rows),'GT_changed':False,'models_changed':False}
    with (R/'reviews/small_gap_float64_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
