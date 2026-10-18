#!/usr/bin/env python3
"""Independent blocked float64 exhaustive audit on frozen train/test samples.

This is an offline sample audit, never an ANN timing or a replacement GT.
"""
import argparse
import json
import os
import time
from pathlib import Path

for _key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_key]='16'
import numpy as np


def matrix(spec, integer=False):
    p=Path(spec['path']);n=spec['n'];d=spec.get('d',spec.get('k',100));fmt=spec['format']
    if fmt in ('raw_f32','raw_i32','raw_i64'):
        dtype={'raw_f32':'<f4','raw_i32':'<i4','raw_i64':'<i8'}[fmt]
        total=spec.get('total_n',p.stat().st_size//(np.dtype(dtype).itemsize*d));start=spec.get('row_start',0)
        assert p.stat().st_size==total*d*np.dtype(dtype).itemsize and start+n<=total
        return np.memmap(p,mode='r',dtype=dtype,shape=(total,d))[start:start+n]
    if fmt in ('fvecs','ivecs'):
        a=np.memmap(p,mode='r',dtype='<i4').reshape(-1,d+1)
        start=spec.get('row_start',0);assert start+n<=len(a)
        if 'total_n' in spec:assert len(a)==spec['total_n']
        assert bool((a[start:start+n,0]==d).all()),(p,'header')
        return a[start:start+n,1:] if integer else a[start:start+n,1:].view('<f4')
    if fmt=='fbin':
        header=np.fromfile(p,dtype='<u4',count=2);total=int(header[0]);start=spec.get('row_start',0)
        assert int(header[1])==d and p.stat().st_size==8+total*d*4 and start+n<=total
        return np.memmap(p,mode='r',dtype='<f4',offset=8,shape=(total,d))[start:start+n]
    raise ValueError(fmt)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--catalogue',required=True,type=Path)
    ap.add_argument('--output',required=True,type=Path);ap.add_argument('--samples-per-role',type=int,default=16)
    args=ap.parse_args();assert not args.output.exists();started=time.monotonic()
    catalogue=json.loads(args.catalogue.read_text());rows=[]
    for name,c in catalogue['datasets'].items():
        x=matrix(c['base']);qs=[];gts=[];roles=[]
        for role in ('train','test'):
            q=matrix(c[role+'_queries']);g=matrix(c[role+'_gt'],True)
            idx=np.linspace(0,len(q)-1,min(args.samples_per_role,len(q)),dtype=np.int64)
            qs.extend(np.asarray(q[idx],dtype=np.float64));gts.extend(np.asarray(g[idx],dtype=np.int64))
            roles.extend((role,int(i)) for i in idx)
        Q=np.asarray(qs,dtype=np.float64);qnorm=np.einsum('ij,ij->i',Q,Q)
        best_d=np.full((len(Q),100),np.inf);best_i=np.full((len(Q),100),-1,dtype=np.int64)
        for start in range(0,len(x),65536):
            block=np.asarray(x[start:start+65536],dtype=np.float64)
            score=-(Q@block.T)
            if c['metric_id']==1:score=2*score+qnorm[:,None]+np.einsum('ij,ij->i',block,block)[None,:]
            loc=np.argpartition(score,99,axis=1)[:,:100]
            d=np.take_along_axis(score,loc,axis=1);ids=loc+start
            all_d=np.concatenate((best_d,d),axis=1);all_i=np.concatenate((best_i,ids),axis=1)
            for j in range(len(Q)):
                order=np.lexsort((all_i[j],all_d[j]))[:100]
                best_d[j]=all_d[j,order];best_i[j]=all_i[j,order]
        for j,(role,row) in enumerate(roles):
            gt=np.asarray(gts[j]);gb=np.asarray(x[gt],dtype=np.float64)
            gd=-(gb@Q[j])
            if c['metric_id']==1:gd=2*gd+qnorm[j]+np.einsum('ij,ij->i',gb,gb)
            scale=max(1.0,float(np.max(np.abs(best_d[j]))),float(np.max(np.abs(gd))))
            # Existing GT was produced in float32; compare quality within an
            # explicit conservative accumulation bound without rewriting IDs.
            tol=8*np.finfo(np.float32).eps*c['base']['d']*scale
            top1_gap=float(gd[0]-best_d[j,0]);boundary_gap=float(np.max(gd)-best_d[j,-1])
            record={'dataset':name,'role':role,'row':row,'exact_top1_id':int(best_i[j,0]),
                    'stored_top1_id':int(gt[0]),'top1_equal':bool(gt[0]==best_i[j,0]),
                    'top100_set_equal':bool(set(gt)==set(best_i[j])),
                    'top1_distance_gap':top1_gap,'top100_boundary_gap':boundary_gap,
                    'float32_tolerance':tol,'acceptable':bool(top1_gap<=tol and boundary_gap<=tol)}
            assert record['acceptable'],record
            rows.append(record)
        print(json.dumps({'dataset':name,'sample_count':len(Q),'acceptable':True}),flush=True)
    result={'status':'PASS_EXHAUSTIVE_FLOAT64_SAMPLE_GT_AUDIT','samples':len(rows),'rows':rows,
            'elapsed_seconds':time.monotonic()-started,'threads':16,
            'scope':'Fixed samples only; full base float64 scan per dataset; exact IDs and bounded float32 acceptance retained; original GT unchanged'}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
