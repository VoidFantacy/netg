from common import *
import math,resource,itertools
import torch
from torch import nn
torch.set_num_threads(1);torch.set_num_interop_threads(1)

class Model(nn.Module):
    def __init__(self,p,family,r=16):
        super().__init__();self.register_buffer('P',p.clone());self.family=family
        h,d=p.shape
        if family=='WFree':self.W=nn.Parameter(p.clone())
        else:
            self.U=nn.Parameter(torch.zeros(d,r))
            self.V=nn.Parameter(torch.empty(r,d));nn.init.uniform_(self.V,-1/math.sqrt(d),1/math.sqrt(d))
    def encode(self,q):
        if self.family=='WFree':return q
        h=q@self.V.T
        if self.family=='QMLP':h=h.relu()
        return q+h@self.U.T
    def forward(self,q):
        if self.family=='WFree':return q@self.W.T
        return self.encode(q)@self.P.T

def set_ce(scores,triples,teachers,tau):
    b,c,k=triples.shape;assert k==3 and teachers.any(1).all()
    logits=(scores/tau).gather(1,triples.reshape(b,c*3)).reshape(b,c,3).sum(2)
    return (torch.logsumexp(logits,1)-torch.logsumexp(logits.masked_fill(~teachers,-torch.inf),1)).mean()

def objective_checks():
    triples=torch.tensor(list(itertools.combinations(range(5),3)),dtype=torch.long)[None,:,:]
    mask=torch.zeros((1,10),dtype=torch.bool);mask[0,[1,7]]=True
    s=torch.tensor([[.1,-.2,.3,.2,-.1]],dtype=torch.float64,requires_grad=True)
    loss=set_ce(s,triples,mask,1.)
    incidence=torch.zeros((10,5),dtype=torch.float64)
    for i,t in enumerate(triples[0]):incidence[i,t]=1
    logits=incidence@s[0];prob=logits.softmax(0)
    target=torch.zeros_like(prob);target[mask[0]]=logits[mask[0]].softmax(0)
    direct=-torch.log(prob[mask[0]].sum());grad=(prob-target)@incidence
    loss.backward();assert torch.allclose(loss,direct,atol=1e-12)
    assert torch.allclose(s.grad[0],grad,atol=1e-12)
    assert torch.allclose(set_ce(s.detach()+100,triples,mask,1.),loss,atol=1e-12)
    assert set_ce(s.detach(),triples,torch.ones_like(mask),1.).item()==0
    assert abs(set_ce(torch.zeros_like(s),triples,mask,1.).item()-math.log(5))<1e-12
    dump(RUN/'reviews/objective_checks.json',dict(status='PASS',tests=['explicit_subset_probability','independent_incidence_gradient','constant_shift','all_teachers_zero','uniform_log_count_ratio']))

def train():
    finite_deadline();assert read(RUN/'reviews/headroom_gate.json')['status']=='PASS'
    objective_checks()
    # Freeze implementation before the first model update; cal remains unopened.
    dump(RUN/'reviews/training_lock.json',dict(status='FROZEN',source=identity(Path(__file__)),
         protocol=identity(RUN/'protocol.md'),headroom=identity(RUN/'reviews/headroom_gate.json'),
         config=identity(RUN/'config.locked.json'),cal_payload_access=False))
    started=time.time();records=[];frozen_files=[]
    for ds in DS:
        c=read(RUN/'inputs'/ds/'fit/config.json');n,d,h=c['n'],c['dimension'],c['hub_count']
        label=RUN/'labels'/ds/'fit_labels'
        q=np.fromfile(c['queries'],'float32').reshape(n,d).astype('float64')
        q=(q/np.linalg.norm(q,axis=1,keepdims=True)).astype('float32');q=torch.from_numpy(q)
        p=torch.from_numpy(np.fromfile(c['routers'][0]['W'],'float32').reshape(h,d).copy())
        triples=torch.from_numpy(np.fromfile(label/'triples.i32','int32').reshape(n,56,3).astype('int64'))
        teachers=torch.from_numpy(np.fromfile(label/'teacher_mask.u8','uint8').reshape(n,56).astype(bool))
        with torch.no_grad():anchor=q@p.T
        for family in ['QLinear','QMLP','WFree']:
            out=RUN/'models'/ds/family;assert not out.exists();out.mkdir(parents=True)
            torch.manual_seed(LOCK['train_seed']);model=Model(p,family,LOCK['hidden'])
            assert torch.equal(model.encode(q[:16]),q[:16])
            assert torch.equal(model(q[:16]),q[:16]@p.T)
            optimizer=torch.optim.Adam(model.parameters(),lr=LOCK['lr'])
            generator=torch.Generator().manual_seed(LOCK['train_seed'])
            run_start=time.time();log=[]
            def monitor():
                with torch.no_grad():
                    scores=model(q);ce=set_ce(scores,triples,teachers,LOCK['tau']);drift=(scores-anchor).square().mean()
                    logits=scores.gather(1,triples.reshape(n,-1)).reshape(n,56,3).sum(2)
                    teacher_accuracy=teachers[torch.arange(n),logits.argmax(1)].float().mean()
                    return dict(ce=float(ce),score_drift=float(drift),objective=float(ce+LOCK['lambda_score_anchor']*drift),
                                measured_candidate_teacher_accuracy=float(teacher_accuracy))
            log.append(dict(epoch=0,**monitor(),seconds=0.))
            for epoch in range(1,LOCK['epochs']+1):
                order=torch.randperm(n,generator=generator)
                for lo in range(0,n,LOCK['batch']):
                    finite_deadline();assert time.time()-started<LOCK['train_seconds'],'training wall cap'
                    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<8*1024*1024,'8GiB RSS cap'
                    rows=order[lo:lo+LOCK['batch']];optimizer.zero_grad(set_to_none=True)
                    scores=model(q[rows]);ce=set_ce(scores,triples[rows],teachers[rows],LOCK['tau'])
                    drift=(scores-anchor[rows]).square().mean();loss=ce+LOCK['lambda_score_anchor']*drift
                    assert torch.isfinite(loss);loss.backward()
                    assert all(x.grad is not None and torch.isfinite(x.grad).all() for x in model.parameters())
                    optimizer.step();assert all(torch.isfinite(x).all() for x in model.parameters())
                if epoch%10==0:
                    row=dict(epoch=epoch,**monitor(),seconds=time.time()-run_start);log.append(row)
                    dump(out/'training_curve.json',log);print(ds,family,json.dumps(row),flush=True)
            torch.save(model.state_dict(),out/'model.pt')
            if family=='WFree':model.W.detach().numpy().astype('float32').tofile(out/'W.f32')
            else:
                model.U.detach().numpy().astype('float32').tofile(out/'U.f32')
                model.V.detach().numpy().astype('float32').tofile(out/'V.f32')
            with torch.no_grad():encoded=model.encode(q).numpy();scores=model(q).numpy()
            encoded.astype('float32').tofile(out/'fit.encoded.f32')
            scores.astype('float32').tofile(out/'fit.scores.f32')
            cfg=dict(status='TRAINED_FIT_ONLY',family=family,dataset=ds,dim=d,h=h,rank=16,
                     parameter_count=sum(x.numel() for x in model.parameters()),seed=LOCK['train_seed'],epochs=40,
                     seconds=time.time()-run_start,initial=log[0],final=log[-1],cal_payload_access=False,
                     P=c['routers'][0]['W'],U=str(out/'U.f32') if family!='WFree' else None,
                     V=str(out/'V.f32') if family!='WFree' else None,W=str(out/'W.f32') if family=='WFree' else c['routers'][0]['W'])
            dump(out/'model.json',cfg);records.append(cfg)
            dump(RUN/'results/training_runs.json',records)
            frozen_files.extend(identity(path) for path in sorted(out.iterdir()) if path.is_file())
    model_files=[x for x in frozen_files if x['path'].endswith('/model.pt')]
    assert len(model_files)==6
    dump(RUN/'reviews/models_frozen.json',dict(status='FROZEN',models=model_files,all_files=frozen_files,
         source=identity(Path(__file__)),wall_seconds=time.time()-started,cal_payload_access=False,
         torch_version=torch.__version__,maxrss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    dump(RUN/'state.json',dict(status='SIX_MODELS_FROZEN',training_runs=6,cal_payload_access=False,heldout_access=False))
    print('SIX_MODELS_FROZEN',flush=True)

if __name__=='__main__':train()
