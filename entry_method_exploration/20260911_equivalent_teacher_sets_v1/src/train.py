from common import *
import numpy as np
import torch
from torch import nn

torch.set_num_threads(8)
torch.set_num_interop_threads(1)
torch.set_default_dtype(torch.float64)

def set_loss(scores,accepted,margin=.1):
    positive=scores.masked_fill(~accepted,-torch.inf).max(1).values
    augmented=(scores+margin*(~accepted)).max(1).values
    return augmented-positive

def triple_scores(z,triples):
    return z.gather(1,triples.reshape(len(z),-1)).reshape(len(z),-1,3).sum(2)

class Transform(nn.Module):
    def __init__(self,p):
        super().__init__();self.register_buffer('p',p.clone())
        self.fn=nn.Linear(p.shape[1],p.shape[1],bias=False)
        nn.init.zeros_(self.fn.weight)
    def forward(self):return nn.functional.normalize(self.p+self.fn(self.p),dim=1)

def load_fit(ds):
    c=read(O/'inputs'/ds/'fit/config.json');n,d,h=c['num_queries'],c['dim'],c['hub_count']
    p=np.fromfile(E24/'models'/ds/'gt10_hard/W.f32',np.float32).reshape(h,d).astype(np.float64)
    q=np.fromfile(c['queries_file'],np.float32).reshape(n,d).astype(np.float64)
    q/=np.linalg.norm(q,axis=1,keepdims=True)
    triples=np.fromfile(E28/'inputs'/ds/'proposals/triples.i32',np.int32).reshape(n,56,3)
    td=O/'inputs'/ds/'teachers'
    accepts={x:np.fromfile(td/(x+'.u8'),np.uint8).reshape(n,56).astype(bool) for x in CELLS}
    headroom=np.fromfile(td/'headroom.u8',np.uint8).astype(bool)
    hits=np.fromfile(E28/'labels'/ds/'hits.u8',np.uint8).reshape(n,56)
    ndc=np.fromfile(E28/'labels'/ds/'graph_ndc.u32',np.uint32).reshape(n,56)
    return q,p,triples,accepts,headroom,hits,ndc

@torch.no_grad()
def diagnose(q,w,triples,accepted,gain,hits,ndc):
    records={k:[] for k in ['slot','full_slot','known','single_loss','multi_loss']}
    for b in range(0,len(q),1024):
        z=q[b:b+1024]@w.T/.05;ts=triples[b:b+1024]
        scores=triple_scores(z,ts)
        records['slot'].append(scores.argmax(1).numpy())
        # Stable tie rule is ascending local index, equivalent to ascending real IDs.
        pred=torch.argsort(z,dim=1,descending=True,stable=True)[:,:3].sort(1).values
        match=(ts==pred[:,None,:]).all(2)
        records['known'].append(match.any(1).numpy())
        records['full_slot'].append(match.to(torch.int64).argmax(1).numpy())
        for cell in CELLS:records[cell+'_loss'].append(set_loss(scores,accepted[cell][b:b+1024]).numpy())
    arrays={k:np.concatenate(v) for k,v in records.items()};rr=np.arange(len(q));result=[]
    for group,mask in [('all',np.ones(len(q),bool)),('headroom',gain),('no_headroom',~gain)]:
        known=mask&arrays['known'];slot=arrays['slot'];full=arrays['full_slot']
        for teacher,a in accepted.items():
            good=a.numpy();correct=good[rr,slot]
            loss=arrays[teacher+'_loss']
            result.append(dict(group=group,teacher=teacher,queries=int(mask.sum()),
                candidate_acceptance=float(correct[mask].mean()),candidate_recall_pct=float(hits[rr,slot][mask].mean()*10),
                candidate_graph_ndc=float(ndc[rr,slot][mask].mean()),loss=float(loss[mask].mean()),
                zero_loss_fraction=float((loss[mask]<1e-10).mean()),full_exact_known_fraction=float(known.sum()/mask.sum()),
                full_exact_accepted_fraction=float((good[rr,full]&arrays['known'])[mask].mean()),
                full_exact_known_recall_pct=float(hits[rr[known],full[known]].mean()*10) if known.any() else None,
                full_exact_known_graph_ndc=float(ndc[rr[known],full[known]].mean()) if known.any() else None,
                scope='candidate C8 scores and selection-conditioned exact subset; not actual HNSW/QPS'))
    return result

def fit(ds,cell,data):
    q_np,p_np,ts_np,accept_np,gain,hits,ndc=data
    dest=O/'models'/ds/cell;assert not dest.exists();dest.mkdir(parents=True)
    torch.manual_seed(SEED)
    q=torch.from_numpy(q_np);p=torch.from_numpy(p_np);ts=torch.from_numpy(ts_np.astype(np.int64))
    accepted={k:torch.from_numpy(v) for k,v in accept_np.items()}
    model=Transform(p);optimizer=torch.optim.Adam(model.parameters(),lr=.003)
    n=len(q);curve=[];align=[];start=time.time()
    for epoch in range(81):
        optimizer.zero_grad();exported=model();w=exported.detach().requires_grad_(True);data_sum=0.
        for b in range(0,n,1024):
            z=q[b:b+1024]@w.T/.05
            loss=set_loss(triple_scores(z,ts[b:b+1024]),accepted[cell][b:b+1024]).sum()/n
            assert torch.isfinite(loss) and loss.item()>-1e-10
            loss.backward();data_sum+=loss.item()
        drift=(w-p).square().sum(1).mean();(100*drift).backward();exported.backward(w.grad)
        gn=sum(v.grad.square().sum().item() for v in model.parameters())**.5
        assert np.isfinite(gn)
        rec=dict(epoch=epoch,data_loss=data_sum,drift=drift.item(),objective=data_sum+100*drift.item(),gradient_norm=gn,seconds=time.time()-start)
        curve.append(rec)
        if epoch%10==0:
            align.append(dict(epoch=epoch,metrics=diagnose(q,exported,ts,accepted,gain,hits,ndc)))
            dump(dest/'training_curve.json',curve);dump(dest/'alignment_curve.json',align)
            print(ds,cell,rec,flush=True)
        if epoch<80:optimizer.step()
    w=model().detach().numpy();exported=w.astype(np.float32)
    assert np.isfinite(exported).all()
    exported.tofile(dest/'W.f32');model.fn.weight.detach().numpy().tofile(dest/'A.f64')
    report=dict(status='TRAINED_FIT_ONLY',dataset=ds,cell=cell,epochs=80,seed=SEED,lambda_anchor=100,temperature=.05,margin=.1,
        parameter_count=sum(v.numel() for v in model.parameters()),training_seconds=time.time()-start,first=curve[0],last=curve[-1],
        objective_decreased=curve[-1]['objective']<curve[0]['objective'],W=identity(dest/'W.f32'),A=identity(dest/'A.f64'),
        cal_used=False,audit_used=False,validation_used=False)
    dump(dest/'model.json',report);return report

if __name__=='__main__':
    assert read(O/'reviews/teacher_verification.json')['status']=='PASS'
    assert read(O/'reviews/objective_tests.json')['status']=='PASS'
    files=[O/'protocol.md']+[O/'src'/s for s in ['common.py','train.py','test_objective.py','prepare.py']]
    files += [p for p in (O/'inputs').glob('*/teachers/*') if p.is_file()]
    for ds in DS:
        c=read(O/'inputs'/ds/'fit/config.json')
        files += [Path(c[x]) for x in ['queries_file','gt_file','row_ids','hub_ids']]
        files += [E24/'models'/ds/'gt10_hard/W.f32',E28/'inputs'/ds/'proposals/triples.i32']
    freeze(O/'reviews/frozen_before_training.json',files)
    runs=[]
    for ds in DS:
        data=load_fit(ds)
        for cell in CELLS:
            check_freeze(O/'reviews/frozen_before_training.json')
            dump(O/'state.json',dict(status='TRAINING_RUNNING',pid=os.getpid(),dataset=ds,cell=cell,training_runs=len(runs),real_search_calls=0,heldout_access=False))
            runs.append(fit(ds,cell,data));dump(O/'models/training_runs.json',runs)
    freeze(O/'models/raw_frozen_before_matching.json',files+[p for p in (O/'models').glob('*/*/*') if p.is_file()])
    dump(O/'state.json',dict(status='TRAINING_COMPLETE_DRIFT_MATCH_PENDING',training_runs=4,real_search_calls=0,heldout_access=False))
