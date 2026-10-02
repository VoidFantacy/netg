from common import *
import numpy as np

def unit(x):return x/np.linalg.norm(x,axis=1,keepdims=True)
def loss_numpy(scores,accepted):
    return np.max(scores+.1*(~accepted),axis=1)-np.max(np.where(accepted,scores,-np.inf),axis=1)
def drift(x,p):return float(np.square(x-p).sum(1).mean())

assert read(O/'state.json')['status']=='DRIFT_MATCH_COMPLETE_VERIFICATION_PENDING'
check_freeze(O/'models/frozen_before_development.json')
checks=[];matches=[]
for ds in DS:
    c=read(O/'inputs'/ds/'fit/config.json');n,d,h=c['num_queries'],c['dim'],c['hub_count']
    p=np.fromfile(E24/'models'/ds/'gt10_hard/W.f32',np.float32).reshape(h,d).astype(float)
    q=unit(np.fromfile(c['queries_file'],np.float32).reshape(n,d).astype(float))
    ts=np.fromfile(E28/'inputs'/ds/'proposals/triples.i32',np.int32).reshape(n,56,3)
    good={k:np.fromfile(O/'inputs'/ds/'teachers'/(k+'.u8'),np.uint8).reshape(n,56).astype(bool) for k in CELLS}
    hits=np.fromfile(E28/'labels'/ds/'hits.u8',np.uint8).reshape(n,56)
    ndc=np.fromfile(E28/'labels'/ds/'graph_ndc.u32',np.uint32).reshape(n,56)
    gain=np.fromfile(O/'inputs'/ds/'teachers/headroom.u8',np.uint8).astype(bool)
    rr=np.arange(n);raw={}
    for cell in CELLS:
        dest=O/'models'/ds/cell;a=np.fromfile(dest/'A.f64',np.float64).reshape(d,d)
        w=unit(p+p@a.T);exported=np.fromfile(dest/'W.f32',np.float32).reshape(h,d)
        assert np.allclose(w,exported,atol=2e-8,rtol=1e-7)
        assert np.max(np.abs(np.linalg.norm(exported.astype(float),axis=1)-1))<1e-7
        raw[cell]=exported.astype(float)
        losses={k:[] for k in CELLS};slots=[];fullslots=[];known=[]
        for b in range(0,n,512):
            z=q[b:b+512]@w.T/.05
            scores=np.take_along_axis(z[:,None,:],ts[b:b+512],axis=2).sum(2)
            slots.extend(np.argmax(scores,axis=1))
            pred=np.sort(np.argsort(-z,axis=1,kind='stable')[:,:3],axis=1)
            match=(ts[b:b+512]==pred[:,None,:]).all(2)
            known.extend(match.any(1));fullslots.extend(match.argmax(1))
            for k in CELLS:losses[k].extend(loss_numpy(scores,good[k][b:b+512]))
        curve=read(dest/'training_curve.json');last=curve[-1]
        assert len(curve)==81 and [x['epoch'] for x in curve]==list(range(81))
        own=float(np.mean(losses[cell]));dr=drift(w,p)
        assert abs(own-last['data_loss'])<1e-8 and abs(dr-last['drift'])<1e-10
        assert abs(own+100*dr-last['objective'])<1e-8
        slots=np.array(slots);fullslots=np.array(fullslots);known=np.array(known)
        alignment=read(dest/'alignment_curve.json');assert [x['epoch'] for x in alignment]==list(range(0,81,10))
        for m in alignment[-1]['metrics']:
            mask=np.ones(n,bool) if m['group']=='all' else gain if m['group']=='headroom' else ~gain
            target=good[m['teacher']]
            assert abs(target[rr,slots][mask].mean()-m['candidate_acceptance'])<1e-12
            assert abs(hits[rr,slots][mask].mean()*10-m['candidate_recall_pct'])<1e-12
            assert abs(ndc[rr,slots][mask].mean()-m['candidate_graph_ndc'])<1e-9
            assert abs(known[mask].mean()-m['full_exact_known_fraction'])<1e-12
            assert abs((target[rr,fullslots]&known)[mask].mean()-m['full_exact_accepted_fraction'])<1e-12
        checks.append(dict(dataset=ds,cell=cell,status='PASS',data_loss=own,drift=dr,numpy_forward=True,alignment_all_groups=True))
    match=read(O/'models'/ds/'drift_match.json');dd={k:drift(w,p) for k,w in raw.items()}
    assert dd==match['raw_drifts']
    assert abs(min(dd.values())-match['target_drift'])<1e-15
    canonical={x['name']:x for x in match['canonical_models']}
    assert len(canonical)==len(match['canonical_models'])
    for name,alias in match['aliases'].items():
        assert name==alias+'_matched' and alias in canonical
    large=match['matched_larger'];target=match['target_drift']
    if large+'_matched' in canonical:
        w=raw[large];alpha=match['alpha'];assert 0<alpha<1
        independent=unit(p+alpha*(w-p)).astype(np.float32)
        path=canonical[large+'_matched']['W']['path'];stored=np.fromfile(path,np.float32).reshape(h,d)
        assert np.array_equal(independent,stored)
        actual=drift(stored.astype(float),p)
        assert abs(actual-target)/target<1e-4
        mesh=[drift(unit(p+t*(w-p)),p) for t in np.linspace(0,1,101)]
        assert np.all(np.diff(mesh)>=-1e-15)
        lo,hi=0.,1.
        for _ in range(80):
            mid=(lo+hi)/2
            if drift(unit(p+mid*(w-p)),p)>target:hi=mid
            else:lo=mid
        assert abs((lo+hi)/2-alpha)<1e-14
    for item in canonical.values():assert identity(item['W']['path'])==item['W']
    matches.append(dict(dataset=ds,status='PASS',canonical_models=len(canonical),alpha=match['alpha'],target=target,relative_error=match['relative_error']))
dump(O/'reviews/model_verification.json',dict(status='PASS',models=checks,matching=matches,NSG_calls=0,optimizer_steps=0))
print('MODEL_VERIFICATION_PASS',json.dumps(matches),flush=True)
