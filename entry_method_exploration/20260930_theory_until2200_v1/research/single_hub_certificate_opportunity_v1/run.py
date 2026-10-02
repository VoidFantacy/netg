import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key] = '8'
os.sched_setaffinity(0, range(8))
import hashlib
import json
import shutil
import time
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_info, threadpool_limits

R = Path(__file__).resolve().parent

def ident(path):
    p = Path(path)
    return {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}

def dump(path, x):
    with Path(path).open('x') as f:
        json.dump(x, f, indent=2, allow_nan=False); f.write('\n')

def arrsha(x):
    return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()

def check(c, start):
    assert time.time() < c['deadline_unix'] and time.perf_counter()-start < 300
    assert shutil.disk_usage(R).free >= 6*1024**3
    assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file()) < 2*1024**2
    assert sum(p.stat().st_size for p in R.parents[1].rglob('*') if p.is_file()) < 1024**3

def quantiles(x):
    return dict(zip(('min','q01','q25','median','q75','q99','max'), np.quantile(x,[0,.01,.25,.5,.75,.99,1]).tolist()))

def main():
    started = time.perf_counter(); c = json.loads((R/'config.locked.json').read_text())
    assert time.time() < c['latest_start_unix']; check(c, started)
    for p, v in c['small_identity'].items(): assert ident(p) == v, p
    for p, v in c['large_identity'].items():
        st = Path(p).stat(); assert (st.st_size, st.st_mtime_ns) == (v['bytes'], v['mtime_ns'])
    results = {}
    with threadpool_limits(8):
        for ds, d in c['datasets'].items():
            check(c, started); begin = time.perf_counter(); dim = d['dimension']; n = d['base_n']
            raw = np.memmap(d['base'], '<f4', mode='r', shape=(n,dim+1)); base = raw[:,1:]
            blocks = []; maxsq = -1.; maxrow = -1; t = time.perf_counter()
            for lo in range(0,n,65536):
                check(c, started); z = np.array(base[lo:lo+65536], dtype='f8')
                assert np.isfinite(z).all() and np.all(raw[lo:lo+len(z),0].view('<i4') == dim)
                normsq = np.sum(z*z,axis=1); slot = int(np.argmax(normsq)); val = float(normsq[slot])
                blocks.append({'lo':lo,'n':len(z),'max_squared_norm':val,'max_row':lo+slot})
                if val > maxsq: maxsq,maxrow = val,lo+slot
            norm_seconds = time.perf_counter()-t
            assert maxsq > 0 and sum(b['n'] for b in blocks) == n
            # Positive sums of exact f32->f64 products, with an outward rounding allowance.
            m = float(np.nextafter(np.sqrt(np.nextafter(maxsq*(1+(dim+2)*np.finfo('f8').eps),np.inf)),np.inf))
            ids = np.fromfile(d['hub_ids'],'<i4'); h0 = np.array(base[ids],dtype='f4')
            h = (h0/np.maximum(np.linalg.norm(h0,axis=1,keepdims=True),1e-12)).astype('f8')
            q = np.fromfile(d['fit_queries'],'<f4').reshape(20000,dim).astype('f8')
            qnorm = np.linalg.norm(q,axis=1); assert np.all(qnorm > 0) and np.isfinite(q).all()
            t = time.perf_counter(); scores = q@h.T; nearest = scores.argmax(1).astype('i4')
            hs = np.sum(h*h,axis=1)
            distances = np.sqrt(np.maximum(hs[:,None]+hs[None,:]-2*(h@h.T),0))
            # Same index is excluded; any duplicate different hub yields a zero margin and no certificate.
            diff = scores[np.arange(len(q)),nearest,None]-scores
            denom = qnorm[:,None]*distances[nearest]
            margins = np.divide(diff,denom,out=np.zeros_like(diff),where=denom>0)
            margins[np.arange(len(q)),nearest] = np.inf
            delta = np.maximum(0,np.minimum(1,margins.min(1)))
            u = np.sqrt(np.maximum(0,1-delta*delta)); geometry_seconds = time.perf_counter()-t
            t = time.perf_counter(); ts = {}
            for name,path,dtype in [('exact',d['exact_ids'],'<i8'),('approx',d['approx_ids'],'<i4')]:
                target = np.memmap(path,dtype,mode='r',shape=(20000,100))[:,:10]
                assert target.min() >= 0 and target.max() < n
                assert np.all(np.diff(np.sort(target,axis=1),axis=1)>0)
                tau = np.empty(20000,dtype='f8')
                for lo in range(0,20000,256):
                    check(c,started); rows = target[lo:lo+256]
                    values = np.einsum('nkd,nd->nk',np.array(base[rows],dtype='f8'),q[lo:lo+len(rows)])
                    tau[lo:lo+len(rows)] = values.min(1)
                ts[name] = tau/(m*qnorm)
            score_seconds = time.perf_counter()-t
            arrays = {'delta':delta,'u':u,'t_exact':ts['exact'],'t_approx':ts['approx'],'qnorm':qnorm,'nearest':nearest}
            np.savez_compressed(R/(ds+'.npz'),**arrays)
            comparisons = {}
            for name, tv in ts.items():
                slack = tv-u
                comparisons[name] = {'t':quantiles(tv),'slack':quantiles(slack),'strict_positive':int(np.sum(slack>0)),
                    'positive_outside_buffer':int(np.sum(slack>1e-10)),'negative_outside_buffer':int(np.sum(slack < -1e-10)),
                    'buffer_band':int(np.sum(np.abs(slack)<=1e-10))}
            # Fixed before audit: every positive/ambiguous row plus fixed/tightest witnesses.
            mandatory = np.flatnonzero((ts['exact']-u >= -1e-10)|(ts['approx']-u >= -1e-10))
            assert len(mandatory) <= 64, 'STOP: full positive/ambiguous audit exceeds fixed cap'
            selected = sorted(set(range(0,20000,625)) | set(np.argsort(-(ts['exact']-u),kind='stable')[:16].tolist()) | set(mandatory.tolist()))
            witnesses = [{'source_row':int(i),'nearest_hub_slot':int(nearest[i]),'delta':float(delta[i]),'u':float(u[i]),
                          't_exact':float(ts['exact'][i]),'t_approx':float(ts['approx'][i])} for i in selected]
            results[ds] = {'n':n,'dimension':dim,'H':len(h),'mathematical_hard_only':True,'actual_default_is_hard':d['actual_default_is_hard'],
                'full_base_norm_seconds':norm_seconds,'geometry_seconds':geometry_seconds,'candidate_rescore_seconds':score_seconds,
                'dataset_seconds':time.perf_counter()-begin,'max_squared_norm':maxsq,'max_norm_row':maxrow,'M_outward':m,
                'blocks':blocks,'H_f32_sha256':arrsha(h.astype('f4')),'delta':quantiles(delta),'u':quantiles(u),'comparisons':comparisons,'mandatory_rows':mandatory.tolist(),
                'audit_rows':selected,'witnesses':witnesses,'array_sha256':{k:arrsha(v) for k,v in arrays.items()}}
            print(ds, json.dumps({'norm_seconds':norm_seconds,'comparisons':comparisons}),flush=True)
            del raw,base,h0,h,q,scores,margins,diff,denom
    for p,v in c['small_identity'].items(): assert ident(p) == v, p
    for p,v in c['large_identity'].items():
        st=Path(p).stat();assert (st.st_size,st.st_mtime_ns)==(v['bytes'],v['mtime_ns'])
    check(c,started)
    dump(R/'results.json',{'status':'OPPORTUNITY_DIAGNOSTIC_PENDING_AUDIT','seconds':time.perf_counter()-started,
        'affinity':sorted(os.sched_getaffinity(0)),'threadpools':threadpool_info(),'datasets':results,
        'new_exact_GT':0,'NSG':0,'ANN':0,'new_profiles':0,'default_changed':False})

if __name__ == '__main__':main()
