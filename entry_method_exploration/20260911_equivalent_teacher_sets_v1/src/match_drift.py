from common import *
import numpy as np

def unit(x):return x/np.linalg.norm(x,axis=1,keepdims=True)
def drift(x,p):return float(np.square(x-p).sum(1).mean())

assert read(O/'state.json')['status']=='TRAINING_COMPLETE_DRIFT_MATCH_PENDING'
check_freeze(O/'models/raw_frozen_before_matching.json')
for ds in DS:
    c=read(O/'inputs'/ds/'fit/config.json');shape=(c['hub_count'],c['dim'])
    p=np.fromfile(E24/'models'/ds/'gt10_hard/W.f32',np.float32).reshape(shape).astype(float)
    ws={k:np.fromfile(O/'models'/ds/k/'W.f32',np.float32).reshape(shape).astype(float) for k in CELLS}
    dd={k:drift(w,p) for k,w in ws.items()};small=min(CELLS,key=lambda k:(dd[k],k));large=max(CELLS,key=lambda k:(dd[k],k))
    aliases={small+'_matched':small};target=dd[small]
    canonical=[dict(name=k,W=identity(O/'models'/ds/k/'W.f32')) for k in CELLS]
    rec=dict(status='PASS',dataset=ds,raw_drifts=dd,target_drift=target,matched_smaller=small,matched_larger=large,
             cal_used=False,audit_used=False,validation_used=False,optimizer_steps=0,NSG_calls=0)
    if abs(dd[large]-target)<=1e-15:
        aliases[large+'_matched']=large;rec.update(alpha=1.,actual_drift=dd[large],relative_error=0.)
    else:
        lo,hi=0.,1.;w=ws[large]
        assert drift(unit(p),p)<=target
        for _ in range(80):
            t=(lo+hi)/2
            if drift(unit(p+t*(w-p)),p)>target:hi=t
            else:lo=t
        alpha=(lo+hi)/2;exported=unit(p+alpha*(w-p)).astype(np.float32)
        actual=drift(exported.astype(float),p);error=abs(actual-target)/max(target,1e-30)
        assert error<1e-4,(ds,error)
        name=large+'_matched';dest=O/'models'/ds/name;assert not dest.exists();dest.mkdir()
        exported.tofile(dest/'W.f32');canonical.append(dict(name=name,W=identity(dest/'W.f32')))
        rec.update(alpha=alpha,actual_drift=actual,relative_error=error)
        dump(dest/'model.json',dict(status='FIT_ONLY_DRIFT_MATCHED',source=large,alpha=alpha,target_drift=target,actual_drift=actual,W=identity(dest/'W.f32')))
    rec.update(canonical_models=canonical,aliases=aliases)
    dump(O/'models'/ds/'drift_match.json',rec);print(json.dumps(rec),flush=True)
files=[O/'protocol.md',O/'src/match_drift.py']+[p for p in (O/'models').rglob('*') if p.is_file()]
freeze(O/'models/frozen_before_development.json',files)
dump(O/'state.json',dict(status='DRIFT_MATCH_COMPLETE_VERIFICATION_PENDING',training_runs=4,real_search_calls=0,heldout_access=False))
