import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='8'
os.sched_setaffinity(0,set(range(8)))
import hashlib,json,resource,time
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
R=Path(__file__).resolve().parent;CAMP=R.parents[1]
def unit_f32(x):
    assert x.dtype==np.float32 and np.isfinite(x).all()
    norm=np.linalg.norm(x,axis=1,keepdims=True);assert np.all(norm>0)
    return x/np.maximum(norm,np.float32(1e-12))
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def sha(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def put(p,x):
    with Path(p).open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def guard(start,c):
    assert time.time()<c['deadline_unix'] and time.perf_counter()-start<c['seconds_cap']
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<8*1024**2
def check_inputs(c):
    for p,v in c['files'].items():assert ident(p)==v,p
    for p,v in c['base_stats'].items():
        s=Path(p).stat();assert (s.st_size,s.st_mtime_ns)==(v['bytes'],v['mtime_ns'])
def load(d):
    base=np.memmap(d['base'],'<f4',mode='r',shape=(d['base_n'],d['dimension']+1))
    hubs=np.fromfile(d['hub_ids'],'<i4');ii=np.fromfile(d['exact_ids'],'<i8').reshape(20000,100)[:,:10];jj=np.fromfile(d['approx_ids'],'<i4').reshape(20000,100)[:,:10]
    assert np.all((ii>=0)&(ii<d['base_n'])) and np.all((jj>=0)&(jj<d['base_n']))
    for a in (ii,jj):assert np.all(np.diff(np.sort(a,axis=1),axis=1)>0)
    ids,inverse=np.unique(np.concatenate([ii.ravel(),jj.ravel()]),return_inverse=True)
    assert np.all(base[ids,0].copy().view('<i4')==d['dimension']) and np.all(base[hubs,0].copy().view('<i4')==d['dimension'])
    h=unit_f32(np.array(base[hubs,1:],dtype='f4')).astype('f8')
    return base,h,ids,inverse.reshape(2,20000,10),ii,jj
def soft(z):
    e=np.exp(z-z.max(axis=1,keepdims=True));return e/e.sum(axis=1,keepdims=True)
def assignment(c):
    r,s=linear_sum_assignment(c);return float(c[r,s].sum())
def soft_row(logits,exact,approx):
    x=np.setdiff1d(exact,approx,assume_unique=True);y=np.setdiff1d(approx,exact,assume_unique=True);r=len(x);k=len(exact)
    assert r==len(y)
    if r==0:return r,np.zeros(4,dtype='f8')
    a=logits[x];b=logits[y];p=soft(a);q=soft(b);mass=float(abs(p.sum(0)-q.sum(0)).sum()/k)
    pc=abs(p[:,None,:]-q[None,:,:]).sum(2);diff=a[:,None,:]-b[None,:,:];dd=np.ptp(diff,axis=2);cc=2*np.tanh(dd/4)
    result=np.asarray([mass,assignment(pc)/k,assignment(cc)/k,assignment(dd)/k])
    assert result[0]<=result[1]+2e-11 and result[1]<=result[2]+2e-11 and result[2]<=2*np.tanh(result[3]/4)+2e-11
    assert result[2]<=2*r/k+2e-11
    return r,result
def hard_row(labels,exact,approx,H):
    cx=np.bincount(labels[exact],minlength=H);cy=np.bincount(labels[approx],minlength=H);l1=int(abs(cx-cy).sum())
    ex=int(cx.argmax());ey=int(cy.argmax());ux=int(np.sum(cx==cx.max())==1);uy=int(np.sum(cy==cy.max())==1)
    return np.asarray([l1,int(l1==0),int(ex==ey),ux,uy],dtype='u1')
def quant(x):
    return dict(zip(['min','q01','q25','median','q75','q99','max'],[float(v) for v in np.quantile(x,[0,.01,.25,.5,.75,.99,1])]))
def summary(missing,metrics,kind):
    out={'queries':len(missing),'id_set_changed':int(np.sum(missing>0)),'missing_histogram':np.bincount(missing,minlength=11).tolist(),'missing_mean':float(np.mean(missing)),'by_missing':{}}
    for n in range(11):
        ix=missing==n
        if not ix.any():continue
        out['by_missing'][str(n)]={'queries':int(ix.sum()),'mean_metrics':metrics[ix].mean(0).tolist()}
    if kind=='soft':
        out['columns']=['mean_assignment_l1','probability_l1_transport','tanh_transport','oscillation_transport']
        out['means']=metrics.mean(0).tolist();out['quantiles']={k:quant(metrics[:,i]) for i,k in enumerate(out['columns'])}
        nz=missing>0;den=2*missing[nz].astype('f8')/10
        out['mass_to_id_bound_on_changed']=quant(metrics[nz,0]/den)
        pp=metrics[:,1]>1e-12;out['nonzero_transport_rows']=int(pp.sum());out['mass_to_probability_transport']=quant(metrics[pp,0]/metrics[pp,1])
        out['actual_l1_le_1e_12_changed_ids']=int(np.sum(nz&(metrics[:,0]<=1e-12)))
    else:
        out['columns']=['histogram_l1_times10','same_histogram','same_argmax','reference_unique_winner','candidate_unique_winner']
        out['actual_l1_mean']=float(metrics[:,0].mean()/10);out['same_histogram']=int(metrics[:,1].sum());out['same_argmax']=int(metrics[:,2].sum())
        out['changed_ids_same_histogram']=int(np.sum((missing>0)&(metrics[:,1]==1)))
        out['unique_same_winner_but_different_histogram']=int(np.sum((metrics[:,1]==0)&(metrics[:,2]==1)&(metrics[:,3]==1)&(metrics[:,4]==1)))
    return out
