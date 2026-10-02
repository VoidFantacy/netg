import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='8'
os.sched_setaffinity(0,set(range(8)))
import json,hashlib,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];ROOT=R.parents[3];C=json.loads((R/'config.locked.json').read_text());start=time.perf_counter();records={}
def dump(p,x):assert not p.exists(),p;p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def unit(x):return x/np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)
for ds,dc in C['datasets'].items():
    c=dc['original'];d=c['dimension'];mp=R/'models'/ds;base=np.memmap(c['base'],'<f4',mode='r').reshape(c['base_n'],d+1);ids=np.fromfile(c['anchor']['ids'],'<i4');h=unit(np.array(base[ids,1:],'f4'));q=unit(np.fromfile(c['fit_source']['queries_file'],'<f4').reshape(20000,d));H=len(ids)
    ex=np.fromfile(c['fit_source']['gt_file'],'<i8').reshape(20000,100);ap=np.fromfile(R/'results'/ds/'labels/ids.i32','<i4').reshape(20000,100);dd=np.fromfile(R/'results'/ds/'labels/distances.f32','<f4').reshape(20000,100)
    assert (ap>=0).all() and (ap<c['base_n']).all() and (np.diff(np.sort(ap,axis=1),axis=1)>0).all() and np.isfinite(dd).all() and (np.diff(dd,axis=1)>=0).all()
    family='gt10_soft_t1' if ds.startswith('web') else 'gt10_hard';mf=json.loads((ROOT/'entry_method_exploration/20260910_gt_topk_profiles_v1/models'/ds/family/'manifest.json').read_text());temp=mf['temperature'];values={};out={}
    for name,targets in [('ExactAudit',ex),('ApproxTarget10',ap)]:
        t=time.perf_counter();a=np.zeros((20000,H))
        for rank in range(10):
            z=unit(np.array(base[targets[:,rank],1:],'f4'))
            for lo in range(0,20000,4096):
                hi=min(lo+4096,20000);scores=z[lo:hi]@h.T
                if temp is None:a[np.arange(lo,hi),scores.argmax(1)]+=.1
                else:
                    s=scores.astype('f8');s-=s.max(1,keepdims=True);s/=temp;np.exp(s,out=s);s/=s.sum(1,keepdims=True);a[lo:hi]+=s/10
        v=h.astype('f8')+a.T@q.astype('f8');w=unit(v).astype('f4');assert np.isfinite(w).all();values[name]=(v,w)
        out[name]={'seconds':time.perf_counter()-t,'assignment_sha256':hashlib.sha256(a.tobytes()).hexdigest(),'profile_sha256':hashlib.sha256(w.tobytes()).hexdigest()}
        if name=='ExactAudit':assert w.tobytes()==Path(c['anchor']['W']).read_bytes(),'full original exact profile recovery'
        else:w.tofile(mp/'W.f32')
        del a
    v,w=values['ExactAudit'];vp,wp=values['ApproxTarget10'];bound=2*np.linalg.norm(vp-v,axis=1)/np.linalg.norm(v,axis=1);error=np.linalg.norm(unit(vp)-unit(v),axis=1);assert (error<=bound+1e-12).all();ang=np.degrees(np.arccos(np.clip((unit(vp)*unit(v)).sum(1),-1,1)))
    np.savez(mp/'direction_diagnostic.npz',exact_v=v,approx_v=vp,bound=bound,error=error,angle_degrees=ang)
    out['direction']={'median_angle_degrees':float(np.median(ang)),'q90_angle_degrees':float(np.quantile(ang,.9)),'max_angle_degrees':float(ang.max()),'mean_chord_error':float(error.mean()),'all_normalization_bounds_pass':True};out['temperature']=temp;out['exact_W_bit_recovery']=True;records[ds]=out;dump(mp/'profiles.json',out);print(ds,out['direction'],flush=True)
dump(R/'reviews/profiles_complete.json',{'status':'PASS','seconds':time.perf_counter()-start,'datasets':records,'candidate_profile_fits':2,'exact_control_profile_reconstructions':2,'new_GT':0})
