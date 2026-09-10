#!/usr/bin/env python3
"""Locked CPU low-rank utility training. Audit/test never participate in fitting."""
import argparse,hashlib,json,math,time
from pathlib import Path
import numpy as np
import torch

OUT=Path(__file__).resolve().parents[1]

def dump(p,j):p.write_text(json.dumps(j,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def hard_slots(scores,tie_order):
    # The initial slot's real ID defines the stable slot order, independent of pi.
    return tie_order[scores[:,tie_order].argmax(1)]

def remap(slots,hits,pi,tie_order):
    h=len(pi);total=torch.zeros((h,h),dtype=hits.dtype)
    total.index_add_(0,slots,hits)
    best=total[:,tie_order].argmax(1);best=tie_order[best]
    maximum=total.max(1).values
    # This also retains every empty slot's previous action.
    keep=total[torch.arange(h),pi]==maximum
    return torch.where(keep,pi,best)

@torch.no_grad()
def project(v,z,radius):
    orth,tri=torch.linalg.qr(v,mode='reduced')
    newz=tri@z
    newz*=min(1.,radius/max(float(torch.linalg.vector_norm(newz)),1e-20))
    v.copy_(orth);z.copy_(newz)

def soft_loss(scores,rewards,tau):
    regrets=rewards.max(1).values[:,None]-rewards
    return (torch.softmax(scores/tau,dim=1)*regrets).sum(1).mean()

def fold(p,v,z):
    return p+(v@z).T

class Problem:
    def __init__(self,q,p,hits,hubs,nfit,rank,rho,seed):
        self.q=q;self.p=p;self.hits=hits;self.hubs=hubs;self.nfit=nfit
        self.h=len(hubs);self.rank=rank;self.radius=rho*math.sqrt(self.h)
        self.order=torch.argsort(hubs,stable=True)
        self.old=q@p.T;self.row=torch.arange(nfit)
        self.fitmax=hits[:nfit].max(1).values/10.
        gen=torch.Generator().manual_seed(seed)
        self.init_v=torch.linalg.qr(torch.randn(q.shape[1],rank,generator=gen),mode='reduced').Q
        self.init_z=torch.zeros(rank,self.h)
        top=torch.topk(self.old[:nfit],8,dim=1).values
        self.tau0=max(float(torch.median(top[:,0]-top[:,7])),1e-6)

    @torch.no_grad()
    def evaluate(self,v,z,pi,tau):
        # Hard acceptance uses the compiled W, not an unfused factor score.
        w=fold(self.p,v,z)
        scores=self.q@w.T
        slots=hard_slots(scores,self.order);actions=pi[slots]
        chosen=self.hits[torch.arange(len(self.q)),actions]
        fit=chosen[:self.nfit];cal=chosen[self.nfit:]
        mapped=self.hits[:self.nfit,pi]/10.
        regret=(torch.softmax(scores[:self.nfit]/tau,1)*(self.fitmax[:,None]-mapped)).sum(1).mean()
        return {'fit_hits':int(fit.sum()),'cal_hits':int(cal.sum()),'fit_recall':float(fit.mean()/10),
                'cal_recall':float(cal.mean()/10),'fit_failure':float((fit==0).float().mean()),
                'cal_failure':float((cal==0).float().mean()),'soft_regret':float(regret),
                'occupied_fit_slots':int(torch.unique(slots[:self.nfit]).numel()),
                'mapped_actions':int(torch.unique(pi).numel()),'pi_changed':int((pi!=torch.arange(self.h)).sum()),
                'residual_norm':float(torch.linalg.vector_norm(z))},slots

def run_family(problem,family,dest,cfg,seed):
    assert not dest.exists();dest.mkdir(parents=True)
    p=problem;v=p.init_v.clone();z=p.init_z.clone();pi=torch.arange(p.h)
    history=[];snapshots=[];started=time.monotonic();counter=0
    def checkpoint(temperature,round_no,change):
        nonlocal counter
        metrics,_=p.evaluate(v,z,pi,temperature)
        cp=dest/f'checkpoint_{counter:03d}.npz'
        np.savez(cp,V=v.numpy(),Z=z.numpy(),pi=pi.numpy().astype('int32'))
        record={'checkpoint':counter,'file':str(cp),'temperature':temperature,'round':round_no,'change':change,
                'elapsed_seconds':time.monotonic()-started,**metrics}
        history.append(record);snapshots.append((metrics['cal_hits'],counter))
        with (dest/'trace.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
        print(json.dumps({'family':family,'seed':seed,**record}),flush=True)
        counter+=1
    checkpoint(p.tau0,-1,'Fast identity initialization')
    if family=='mapping_only':
        _,slots=p.evaluate(v,z,pi,p.tau0);pi=remap(slots[:p.nfit],p.hits[:p.nfit],pi,p.order)
        checkpoint(p.tau0,0,'full-H mapping')
    else:
        for t_index,mult in enumerate(cfg['temperature_multipliers']):
            tau=p.tau0*mult;stalls=0
            for rnd in range(cfg['max_rounds_per_temperature']):
                before,slots=p.evaluate(v,z,pi,tau);mapping_changed=False
                if family=='joint':
                    newpi=remap(slots[:p.nfit],p.hits[:p.nfit],pi,p.order)
                    mapping_changed=not torch.equal(newpi,pi);pi=newpi
                current,_=p.evaluate(v,z,pi,tau)
                assert current['fit_hits']>=before['fit_hits'],'mapping decreased hard objective'
                accepted=False;accept_info=None
                # Each backtrack starts at the same incumbent and same batch order.
                for bt in range(cfg['max_backtracks']+1):
                    cv=v.clone().requires_grad_(True);cz=z.clone().requires_grad_(True)
                    optim=torch.optim.SGD([cv,cz],lr=cfg['lr']*(.5**bt))
                    gen=torch.Generator().manual_seed(seed+10000*t_index+100*rnd)
                    for epoch in range(cfg['max_epochs_per_proposal']):
                        perm=torch.randperm(p.nfit,generator=gen)
                        for b in perm.split(cfg['train_batch']):
                            optim.zero_grad(set_to_none=True)
                            scores=p.old[b]+(p.q[b]@cv)@cz
                            rewards=p.hits[b][:,pi]/10.
                            # Include the full-H oracle, even when pi omits actions.
                            regret=p.fitmax[b,None]-rewards
                            loss=(torch.softmax(scores/tau,1)*regret).sum(1).mean()
                            loss.backward();torch.nn.utils.clip_grad_norm_([cv,cz],1.0);optim.step()
                        project(cv,cz,p.radius)
                        proposal,_=p.evaluate(cv,cz,pi,tau)
                        higher=proposal['fit_hits']>current['fit_hits']
                        tie_better=proposal['fit_hits']==current['fit_hits'] and proposal['soft_regret']<current['soft_regret']-1e-10
                        if higher or tie_better:
                            v=cv.detach().clone();z=cz.detach().clone();accepted=True
                            accept_info={'backtrack':bt,'epoch':epoch+1,'fit_hit_gain':proposal['fit_hits']-current['fit_hits']}
                            break
                    if accepted:break
                if mapping_changed or accepted:
                    checkpoint(tau,t_index*cfg['max_rounds_per_temperature']+rnd,
                               {'mapping_changed':mapping_changed,'continuous_accepted':accepted,'continuous':accept_info})
                    stalls=0
                else:stalls+=1
                if stalls>=cfg['no_accept_round_stop']:break
    # Prefer earliest checkpoint on exact calibration total-hit ties (including Fast).
    best=max(snapshots,key=lambda x:(x[0],-x[1]))[1]
    learned=[x for x in snapshots if x[1]>0]
    best_new=max(learned,key=lambda x:(x[0],-x[1]))[1] if learned else 0
    selection={'family':family,'best_including_fast':best,'best_new_candidate':best_new,'checkpoints':history,
               'tau0':p.tau0,'rank':p.rank,'radius':p.radius,'elapsed_seconds':time.monotonic()-started,
               'selection':'cal exact total hits; earliest checkpoint on ties','audit_used':False}
    for label,idx in [('selected',best),('candidate',best_new)]:
        a=np.load(history[idx]['file']);w=fold(p.p,torch.from_numpy(a['V']),torch.from_numpy(a['Z'])).numpy()
        np.ascontiguousarray(w,dtype='float32').tofile(dest/f'{label}.W.f32')
        real=p.hubs.numpy()[a['pi']];real.astype('int32').tofile(dest/f'{label}.mapping.i32')
        selection[label]={'W':str(dest/f'{label}.W.f32'),'mapping':str(dest/f'{label}.mapping.i32'),
                          'W_sha256':sha(dest/f'{label}.W.f32'),'mapping_sha256':sha(dest/f'{label}.mapping.i32'),
                          'checkpoint':idx,'metrics':history[idx]}
    dump(dest/'selection.json',selection)
    return selection

def staged(problem,w_only,dest):
    """One mapping step after the calibration-selected W-only checkpoint, fit only."""
    p=problem;assert not dest.exists();dest.mkdir(parents=True)
    idx=w_only['best_including_fast'];cp=np.load(w_only['checkpoints'][idx]['file'])
    v=torch.from_numpy(cp['V']);z=torch.from_numpy(cp['Z']);pi=torch.arange(p.h)
    before,slots=p.evaluate(v,z,pi,p.tau0);pi=remap(slots[:p.nfit],p.hits[:p.nfit],pi,p.order)
    after,_=p.evaluate(v,z,pi,p.tau0)
    assert after['fit_hits']>=before['fit_hits']
    w=fold(p.p,v,z).numpy()
    np.ascontiguousarray(w,dtype='float32').tofile(dest/'candidate.W.f32')
    p.hubs.numpy()[pi.numpy()].astype('int32').tofile(dest/'candidate.mapping.i32')
    result={'family':'staged','source_w_checkpoint':idx,'before':before,'after':after,'audit_used':False,
            'candidate':{'W':str(dest/'candidate.W.f32'),'mapping':str(dest/'candidate.mapping.i32')}}
    dump(dest/'selection.json',result);return result

def self_test():
    torch.set_num_threads(1)
    hits=torch.tensor([[1.,5.,5.],[3.,3.,3.],[8.,1.,0.],[8.,1.,0.]])
    slots=torch.tensor([0,0,1,1]);pi=torch.tensor([2,1,2]);order=torch.tensor([1,2,0])
    mapped=remap(slots,hits,pi,order)
    assert mapped.tolist()==[2,0,2] # aggregate ties retain old; empty slot retained.
    h=torch.arange(3);assert hits[torch.arange(4),mapped[slots]].sum()>=hits[torch.arange(4),pi[slots]].sum()
    scores=torch.zeros(4,3,requires_grad=True)
    loss=soft_loss(scores,torch.ones(4,3),.3);loss.backward();assert torch.count_nonzero(scores.grad)==0
    v=torch.randn(9,3);z=torch.randn(3,7);product=v@z;project(v,z,1000)
    assert torch.allclose(v@z,product,atol=1e-5) and torch.allclose(v.T@v,torch.eye(3),atol=1e-6)
    project(v,z,.1);assert float(torch.linalg.vector_norm(z))<=.100001
    assert hard_slots(torch.tensor([[1.,1.,0.]]),torch.tensor([1,0,2])).item()==1
    assert np.array_equal(np.array([0,1,2,10])==0,np.array([True,False,False,False]))
    print(json.dumps({'status':'PASS','checks':['aggregate mapping ties','empty slot retention','monotone mapping',
          'all-tie zero gradient','QR product preservation','radius constraint','stable slot tie','strict failure hits0']}))

def main():
    a=argparse.ArgumentParser();a.add_argument('--dataset');a.add_argument('--seed',type=int);a.add_argument('--L',type=int)
    a.add_argument('--self-test',action='store_true');args=a.parse_args()
    if args.self_test:self_test();return
    assert args.L in [64,128] and args.seed in [20260828,20260829,20260830]
    cfg=json.loads((OUT/'config.locked.json').read_text());torch.set_num_threads(cfg['threads']);torch.set_num_interop_threads(1)
    assert not torch.cuda.is_available() and torch.version.cuda is None
    assert sha(OUT/'protocol.md')==cfg['protocol_sha256']
    inp=OUT/'inputs'/args.dataset;c=json.loads((inp/'runner_config.json').read_text())
    done=json.loads((OUT/'labels'/args.dataset/'complete.json').read_text());assert done['status']=='COMPLETE'
    seed=json.loads((inp/f'seed{args.seed}/config.json').read_text())
    nfit=c['fit_count'];ncal=c['cal_count'];n=nfit+ncal;d=c['dim'];h=seed['hub_count']
    qmap=np.memmap(inp/'queries.f32',dtype='float32',mode='r',shape=(c['num_queries'],d))
    hitmap=np.memmap(OUT/'labels'/args.dataset/f'L{args.L}/hitcount.u8',dtype='uint8',mode='r',shape=(c['num_queries'],c['hub_count']))
    cols=np.fromfile(seed['union_columns'],dtype='int32')
    q=torch.from_numpy(qmap[:n].copy());hits=torch.from_numpy(hitmap[:n,cols].copy().astype('float32'))
    assert hits.shape==(n,h) and hits.min()>=0 and hits.max()<=10
    proto=torch.from_numpy(np.fromfile(seed['prototypes'],dtype='float32').reshape(h,d))
    hubs=torch.from_numpy(np.fromfile(seed['hub_ids'],dtype='int32').astype('int64'))
    problem=Problem(q,proto,hits,hubs,nfit,cfg['rank'],cfg['rho'],args.seed+args.L)
    dest=OUT/'models'/args.dataset/f'seed{args.seed}'/f'L{args.L}';assert not dest.exists();dest.mkdir(parents=True)
    results={}
    for family in ['mapping_only','w_only','joint']:
        results[family]=run_family(problem,family,dest/family,cfg,args.seed+args.L)
    results['staged']=staged(problem,results['w_only'],dest/'staged')
    dump(dest/'complete.json',{'status':'TRAINING_COMPLETE_MODEL_FROZEN','dataset':args.dataset,'seed':args.seed,'L':args.L,
                             'families':list(results),'protocol_sha256':cfg['protocol_sha256'],'trainer_sha256':sha(Path(__file__)),
                             'audit_used':False,'validation_used':False,'heldout_used':False})

if __name__=='__main__':main()
