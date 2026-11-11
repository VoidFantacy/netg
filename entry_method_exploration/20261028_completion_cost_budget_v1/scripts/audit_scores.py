#!/usr/bin/env python3
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]
def view(d):
    n=d['n'];dim=d['d'];total=d.get('total_n',n);start=d.get('row_start',0)
    if d['format']=='fvecs':return np.memmap(d['path'],'<f4','r',shape=(total,dim+1))[start:start+n,1:]
    return np.memmap(d['path'],'<f4','r',shape=(total,dim))[start:start+n]
def main():
    start=time.perf_counter();checks=[]
    for ds in ['coco','deep10m_l2_v1']:
        c=json.loads((R/f'configs/{ds}.json').read_text());base=view(c['base']);queries=view(c['queries']);n=c['queries']['n']
        sample=np.random.default_rng(20261028).choice(n,32,replace=False);mx=0.;count=0
        for method in ['GT10','B32','REG-R','OPT-R','BLOCK-R512','BLOCK-R2048','BLOCK-R8192','BLOCK-C2048']:
            p=R/f'results/{ds}/{method}_L200/raw';ids=np.memmap(p/'ids.i32','<i4','r',shape=(n,100));dist=np.memmap(p/'distances.f32','<f4','r',shape=(n,100))
            for i in sample:
                q=np.asarray(queries[i],dtype='float64');x=np.asarray(base[ids[i]],dtype='float64')
                expected=((x-q)**2).sum(axis=1) if c['metric_id']==1 else -(x*q).sum(axis=1)
                error=np.abs(expected-dist[i]);assert np.all(error<=5e-5+3e-6*np.abs(expected)),(ds,method,i,error.max())
                mx=max(mx,float(error.max()));count+=100
        checks.append(dict(dataset=ds,query_sample=32,methods=8,raw_base_metric_scores_checked=count,max_abs_float64_deviation=mx,tolerance='5e-5 + 3e-6*abs(float64 expected)',point='fixed L200'))
    (R/'reviews/score_binding_audit.json').write_text(json.dumps(dict(status='PASS_E188_INDEPENDENT_FLOAT64_SCORE_BINDING',checks=checks,seconds=time.perf_counter()-start),indent=2)+'\n')
    print('PASS independent raw vector score check')
if __name__=='__main__':main()
