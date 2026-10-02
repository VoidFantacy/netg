from common import *
import numpy as np
import torch

torch.set_num_threads(1)

def reference_losses(z, target):
    shift=z.max(1,keepdims=True)
    a=np.exp(z-shift)
    e1=np.cumsum(a,axis=1)
    e2=np.cumsum(a[:,1:]*e1[:,:-1],axis=1)
    e3=(a[:,2:]*e2[:,:-1]).sum(1)
    ts=np.take_along_axis(z,target,1).sum(1)
    ce=np.log(e3)+3*shift[:,0]-ts
    adjusted=z+.1
    np.put_along_axis(adjusted,target,np.take_along_axis(z,target,1),1)
    margin=np.sort(adjusted,axis=1)[:,-3:].sum(1)-ts
    return ce,margin

records=[]
for ds in DS:
    c=read(O/'inputs'/ds/'fit/config.json')
    n,h,d=c['num_queries'],c['hub_count'],c['dim']
    p=np.fromfile(E24/'models'/ds/'gt10_hard/W.f32',np.float32).reshape(h,d).astype(np.float64)
    q=np.fromfile(c['queries_file'],np.float32).reshape(n,d).astype(np.float64)
    q/=np.linalg.norm(q,axis=1,keepdims=True)
    for cell in CELLS:
        dest=O/'models'/ds/cell
        report=read(dest/'model.json')
        state=torch.load(dest/'model.pt',map_location='cpu',weights_only=True)
        assert np.array_equal(state['p'].numpy(),p)
        w=p+p@state['fn.weight'].numpy().T
        w/=np.linalg.norm(w,axis=1,keepdims=True)
        stored=np.fromfile(dest/'W.f32',np.float32).reshape(h,d)
        err=float(np.max(np.abs(w-stored)))
        assert err<6e-8 and np.max(np.abs(np.linalg.norm(stored,axis=1)-1))<2e-7
        teacher,kind=cell.split('_')
        target=np.fromfile(O/'inputs'/ds/'teachers'/f'{teacher}.i32',np.int32).reshape(n,3)
        totals=np.zeros(2)
        overlap=matches=missing=0
        for b in range(0,n,512):
            z=q[b:b+512]@w.T/.05
            ce,margin=reference_losses(z,target[b:b+512])
            totals+=np.array([ce.sum(),margin.sum()])/n
            pred=np.argsort(-z,axis=1,kind='stable')[:,:3]
            ov=(pred[:,:,None]==target[b:b+512,None,:]).any(2).sum(1)
            assert (margin>=.1*(3-ov)-1e-10).all()
            overlap+=ov.sum();matches+=(ov==3).sum();missing+=(3-ov).sum()
        ref=totals[0 if kind=='ce' else 1]
        assert abs(ref-report['last']['data_loss'])<1e-9,(ds,cell,ref,report['last'])
        drift=float(np.square(w-p).sum(1).mean())
        assert abs(drift-report['last']['drift'])<1e-12
        diagnostic=read(dest/'alignment_curve.json')[-1]['metrics'][teacher]['all']
        assert abs(diagnostic['entry_overlap']-overlap/(3*n))<1e-12
        assert abs(diagnostic['set_match']-matches/n)<1e-12
        assert diagnostic['missing_entries']==missing
        if cell=='cost_ce':
            assert sha(dest/'W.f32')==sha(E28/'models'/ds/'linear_r100/W.f32')
        records.append(dict(status='PASS',dataset=ds,cell=cell,max_export_error=err,
            independent_ce=float(totals[0]),independent_margin=float(totals[1]),drift=drift,
            teacher_entry_overlap=float(overlap/(3*n)),teacher_set_match=float(matches/n),
            E28_recovery=cell=='cost_ce'))
dump(O/'reviews/model_verification.json',dict(status='PASS',models=records,verified_models=8))
print(json.dumps(records),flush=True)
