import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='8'
os.sched_setaffinity(0,set(range(8)))
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_info

R=Path(__file__).resolve().parent

def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def dump(p,x):
    with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')

def unit(x):return x/np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)

def assignment(base,targets,h,temp):
    a=np.zeros((len(targets),len(h)))
    for rank in range(10):
        z=unit(np.array(base[targets[:,rank]],dtype='f4'))
        for lo in range(0,len(targets),4096):
            hi=min(lo+4096,len(targets));scores=z[lo:hi]@h.T
            if temp is None:a[np.arange(lo,hi),scores.argmax(1)]+=.1
            else:
                scores=scores.astype('f8');scores-=scores.max(1,keepdims=True);scores/=temp
                np.exp(scores,out=scores);scores/=scores.sum(1,keepdims=True);a[lo:hi]+=scores/10
    assert a.min()>=0
    np.testing.assert_allclose(a.sum(1),1.,rtol=1e-13,atol=1e-13)
    return a

def main():
    started=time.perf_counter();records={}
    # These input manifests do not contain the full exact-training-target path.
    for path in sorted((R/'inputs').glob('*/profiles.json')):
        c=json.loads(path.read_text());ds=c['dataset'];d=c['dimension'];n=c['n']
        base=np.memmap(c['base'],'<f4',mode='r').reshape(c['base_n'],d+1)[:,1:]
        ids=np.fromfile(c['hub_ids'],'<i4');h=unit(np.array(base[ids],dtype='f4'))
        q=unit(np.fromfile(c['queries'],'<f4').reshape(n,d)).astype('f8')
        rows=np.fromfile(c['selected_rows'],'<i4');gt=np.fromfile(c['selected_gt'],'<i8').reshape(c['pilot_n'],100)
        assert len(rows)==2048 and len(set(rows))==2048
        ap=np.fromfile(c['approx_ids'],'<i4').reshape(n,100)
        original_T=c['old_temperature'];pilot_T=None
        if original_T is not None:
            target=unit(np.array(base[gt[:,0]],dtype='f4'))
            scores=target@h.T;top=np.partition(scores,-2,axis=1)[:,-2:]
            gaps=(top.max(1)-top.min(1)).astype('f8');pilot_T=max(float(np.median(gaps)),1e-4)
            np.save(R/'models'/ds/'pilot_temperature_gaps.npy',gaps)
        records[ds]={'old_temperature':original_T,'pilot_temperature':pilot_T,'methods':{},
                     'candidate_exact_labels_read':len(rows),'selected_gt_identity':ident(c['selected_gt'])}
        for temperature_name,temp in [('FixedTemperature',original_T)]+([('PilotTemperature',pilot_T)] if original_T is not None else []):
            approx=assignment(base,ap,h,temp)
            exact_pilot=assignment(base,gt,h,temp)
            for mode in ['Approx','Hybrid']:
                name=mode+temperature_name
                t0=time.perf_counter()
                if mode=='Approx':weights=approx
                else:
                    weights=approx.copy();weights[rows]=exact_pilot
                v=h.astype('f8')+weights.T@q;w=unit(v).astype('f4')
                assert np.isfinite(w).all() and np.linalg.norm(v,axis=1).min()>1e-12
                values={'temperature':temp,'assignment_sha256':hashlib.sha256(weights.tobytes()).hexdigest(),
                        'profile_sha256':hashlib.sha256(w.tobytes()).hexdigest(),'aggregation_seconds':time.perf_counter()-t0,
                        'minimum_resultant_norm':float(np.linalg.norm(v,axis=1).min())}
                if name=='ApproxFixedTemperature':
                    assert w.tobytes()==Path(c['methods'][1]['W']).read_bytes(),'old ApproxTarget10 bit recovery'
                    name='ApproxTarget10'
                else:
                    dest=R/'models'/ds/name
                    assert not (dest/'W.f32').exists()
                    w.tofile(dest/'W.f32');np.savez(dest/'construction.npz',v=v,pilot_assignment=exact_pilot)
                records[ds]['methods'][name]=values
                print(ds,name,values,flush=True)
        dump(R/'models'/ds/'profiles_complete.json',records[ds])
    dump(R/'reviews/profiles_complete.json',{'status':'PASS','datasets':records,'seconds':time.perf_counter()-started,
         'new_profiles':4,'approx_controls_bit_restored':2,'new_GT':0,'new_searches':0,
         'threadpools':threadpool_info(),'affinity':sorted(os.sched_getaffinity(0))})

if __name__=='__main__':main()
