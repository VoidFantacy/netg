from common import *
from teacher_core import Transform,set_loss,triple_scores
import numpy as np
import torch

def learning_rate(step):
    assert 1<=step<=1200
    if step<=20:return 3e-5+(3e-4-3e-5)*(step-1)/19
    if step<=200:return 3e-4
    return 3e-6+.5*(3e-4-3e-6)*(1+np.cos(np.pi*(step-200)/1000))

def load_fit(ds):
    c=read(O/'inputs'/ds/'fit/config.json');n,d,h=c['num_queries'],c['dim'],c['hub_count']
    p=np.fromfile(E24/'models'/ds/'gt10_hard/W.f32',np.float32).reshape(h,d).astype(float)
    q=np.fromfile(c['queries_file'],np.float32).reshape(n,d).astype(float);q/=np.linalg.norm(q,axis=1,keepdims=True)
    ts=np.fromfile(E28/'inputs'/ds/'proposals/triples.i32',np.int32).reshape(n,56,3).astype(np.int64)
    g=np.fromfile(O/'inputs'/ds/'teachers/multi.u8',np.uint8).reshape(n,56).astype(bool)
    hits=np.fromfile(E28/'labels'/ds/'hits.u8',np.uint8).reshape(n,56).astype(float)
    ndc=np.fromfile(E28/'labels'/ds/'graph_ndc.u32',np.uint32).reshape(n,56).astype(float)
    return tuple(torch.from_numpy(x) for x in (q,p,ts,g,hits,ndc))

def compute(model,data,cell,beta=1.,with_anchor=True):
    q,p,ts,g,hits,ndc=data;n=len(q)
    model.zero_grad();exported=model();w=exported.detach().requires_grad_(True)
    total=0.;exp_r=0.;greedy_r=0.;exp_c=0.;greedy_c=0.;entropy=0.
    for b in range(0,n,1024):
        sl=slice(b,b+1024);s=triple_scores(q[sl]@w.T/.05,ts[sl]);pi=s.softmax(1)
        if cell=='teacher':loss=set_loss(s,g[sl]).sum()/n
        else:loss=beta*(pi*(hits[sl].max(1).values[:,None]-hits[sl])/10).sum()/n
        loss.backward();total+=loss.item()
        with torch.no_grad():
            slot=s.argmax(1);rows=torch.arange(len(s));prob=pi.detach()
            exp_r+=(prob*hits[sl]).sum().item()/n*10
            greedy_r+=hits[sl][rows,slot].sum().item()/n*10
            exp_c+=(prob*ndc[sl]).sum().item()/n
            greedy_c+=ndc[sl][rows,slot].sum().item()/n
            entropy+=(-(prob*prob.clamp_min(1e-300).log()).sum()).item()/n
    drift=(w-p).square().sum(1).mean()
    if with_anchor:(100*drift).backward()
    exported.backward(w.grad)
    norm=sum(v.grad.square().sum().item() for v in model.parameters())**.5
    result=dict(data_loss=total,drift=drift.item(),objective=total+(100*drift.item() if with_anchor else 0),
        gradient_norm=norm,expected_recall_pct=exp_r,greedy_recall_pct=greedy_r,
        expected_graph_ndc=exp_c,greedy_graph_ndc=greedy_c,entropy=entropy)
    assert all(np.isfinite(v) for v in result.values())
    return result

def fit(ds,cell,data,deadline):
    dest=O/'models'/ds/cell;assert not dest.exists();dest.mkdir(parents=True)
    beta=read(O/'reviews/reward_scales.json')[ds]['beta']
    torch.manual_seed(SEED);model=Transform(data[1]);opt=torch.optim.Adam(model.parameters(),lr=learning_rate(1))
    start=time.monotonic();curve=[];best_value=float('inf');best_epoch=None;best_a=None
    for epoch in range(1201):
        rec=compute(model,data,cell,beta)
        if epoch==0:base=rec.copy()
        feasible=rec['expected_graph_ndc']<=base['expected_graph_ndc']*1.01 and rec['greedy_graph_ndc']<=base['greedy_graph_ndc']*1.01
        if feasible and rec['objective']<best_value:
            best_value=rec['objective'];best_epoch=epoch;best_a=model.fn.weight.detach().clone()
        rec.update(epoch=epoch,seconds=time.monotonic()-start,feasible=feasible,best_epoch=best_epoch,best_objective=best_value,
            next_lr=learning_rate(epoch+1) if epoch<1200 else 0.)
        curve.append(rec);timeout=time.monotonic()>=deadline-3
        if epoch%100==0 or timeout:
            dump(dest/'training_curve.json',curve);print(ds,cell,rec,flush=True)
        if epoch==1200 or timeout:break
        opt.param_groups[0]['lr']=learning_rate(epoch+1);opt.step()
    model.fn.weight.detach().numpy().tofile(dest/'last_A.f64');model().detach().numpy().astype(np.float32).tofile(dest/'last_W.f32')
    model.fn.weight.data.copy_(best_a)
    model.fn.weight.detach().numpy().tofile(dest/'A.f64');model().detach().numpy().astype(np.float32).tofile(dest/'W.f32')
    report=dict(status='TRAINED_FIT_ONLY' if epoch==1200 else 'TIME_BUDGET_STOP',dataset=ds,cell=cell,updates=epoch,
        selected_epoch=best_epoch,selection='minimum own fit objective among expected and greedy graph NDC feasible checkpoints; earliest tie',
        beta=beta,lambda_anchor=100,temperature=.05,margin=.1,seed=SEED,training_seconds=time.monotonic()-start,
        first=curve[0],selected=curve[best_epoch],last=curve[-1],W=identity(dest/'W.f32'),A=identity(dest/'A.f64'),
        cal_used=False,audit_used=False,validation_used=False)
    dump(dest/'model.json',report);return report

if __name__=='__main__':
    assert read(O/'reviews/preflight.json')['status']=='PASS'
    assert read(O/'reviews/objective_tests.json')['status']=='PASS'
    check_freeze(O/'reviews/frozen_before_training.json')
    start=time.monotonic();deadline=start+600;runs=[]
    for ds in DS:
        data=load_fit(ds)
        for cell in CELLS:
            if time.monotonic()>=deadline-3:break
            dump(O/'state.json',dict(status='TRAINING_RUNNING',pid=os.getpid(),dataset=ds,cell=cell,training_runs=len(runs),real_search_calls=0,heldout_access=False))
            runs.append(fit(ds,cell,data,deadline));dump(O/'models/training_runs.json',runs)
    elapsed=time.monotonic()-start;full=len(runs)==4 and all(x['updates']==1200 for x in runs)
    dump(O/'models/training_budget.json',dict(status='PASS' if elapsed<=600 else 'FAIL',elapsed_seconds=elapsed,hard_seconds=600,all_runs_complete=full,runs=len(runs),updates=sum(x['updates'] for x in runs)))
    freeze(O/'models/frozen_after_training.json',[p for p in (O/'models').rglob('*') if p.is_file()])
    dump(O/'state.json',dict(status='TRAINING_COMPLETE_VERIFICATION_PENDING' if full else 'TRAINING_BUDGET_STOP_VERIFICATION_PENDING',training_runs=len(runs),real_search_calls=0,heldout_access=False))
    print('TRAINING_FINISHED',elapsed,full,flush=True)
