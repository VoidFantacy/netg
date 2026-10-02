from common import *
import argparse, random, sys
import torch
from torch import nn
from torch.nn import functional as F

class Tower(nn.Module):
    def __init__(self,d):
        super().__init__();h=2024
        self.fusion_fc1=nn.Linear(d,d)
        self.fusion_transformer=nn.TransformerEncoder(nn.TransformerEncoderLayer(d,8,2048,dropout=0.0,batch_first=True),2,enable_nested_tensor=False)
        self.fusion_fc=nn.Linear(d,h)
        self.pre=nn.Sequential(nn.Linear(h,h),nn.ReLU(),nn.Dropout(.05))
        self.transformer=nn.TransformerEncoder(nn.TransformerEncoderLayer(h,4,2048,dropout=.1,batch_first=True),2,enable_nested_tensor=False)
        self.post=nn.Sequential(nn.ReLU(),nn.Dropout(.05),nn.Linear(h,h),nn.ReLU(),nn.Dropout(.05),nn.Linear(h,d))
    def forward(self,node,graph):
        x=torch.stack([self.fusion_fc1(node),graph],dim=1)
        x=self.fusion_fc(self.fusion_transformer(x)[:,-1,:])
        x=self.transformer(self.pre(x).unsqueeze(1)).squeeze(1)
        return self.post(x)

def release_samples(hops):
    positives=[];negatives=[]
    for row in hops:
        positives.append(np.flatnonzero(row<=row.min()).tolist())
        a=row.copy();a[a==999]=-1;bar=int(a.max());floor=int(a.min())+1
        while True:
            neg=np.flatnonzero(a>=bar).tolist()
            if len(neg)>64 or bar==floor:break
            bar-=1
            assert bar>=-1,'release negative loop did not terminate'
        negatives.append(neg)
    return positives,negatives

def make_labels(inp):
    folder=inp/'labels';assert (folder/'complete.json').exists()
    hops=[];returned=[]
    for start in range(0,11024,128):
        p=folder/f'rows_{start}';meta=json.loads(p.with_suffix('.json').read_text());assert meta['start']==start
        hops.append(np.fromfile(str(p)+'.hop.i32','i4').reshape(-1,512));returned.append(np.fromfile(str(p)+'.ids.i32','i4').reshape(-1,512))
    hops=np.concatenate(hops);returned=np.concatenate(returned);assert hops.shape==(11024,512)
    gt=np.concatenate([np.fromfile(inp/'gate_train.gt.i32','i4').reshape(-1,100),np.fromfile(inp/'gate_monitor.gt.i32','i4').reshape(-1,100)])
    assert np.array_equal(hops!=999,returned==gt[:,:1]) and (hops>=0).all()
    pos,neg=release_samples(hops);good=np.array([10<=len(n)<=500 for n in neg]);ep_pos=[[] for _ in range(512)];ep_neg=[[] for _ in range(512)]
    for qi in range(10000):
        if good[qi]:
            for h in pos[qi]:ep_pos[h].append(qi)
            for h in neg[qi]:ep_neg[h].append(qi)
    rng=random.Random(42);pairs=[]
    for h in range(512):
        rng.shuffle(ep_neg[h]);rng.shuffle(ep_pos[h])
        pairs.extend((h,p,n) for n in ep_neg[h][:50] for p in ep_pos[h][:50])
    pairs=np.asarray(pairs,dtype='i4');assert pairs.ndim==2 and pairs.shape[1]==3 and len(pairs)>0
    target=np.zeros((1024,512),dtype=bool)
    for qi,pp in enumerate(pos[10000:]):target[qi,pp]=True
    assert good[10000:].sum()>0
    meta=dict(rows=11024,train_rows=10000,monitor_rows=1024,train_usable=int(good[:10000].sum()),monitor_usable=int(good[10000:].sum()),no_hit_rows=int((hops.min(axis=1)==999).sum()),triplets=len(pairs),represented_hubs=int(len(np.unique(pairs[:,0]))),negative_rule='literal release sample_neg: 999 becomes -1, descending max threshold until >64 negatives or threshold=min+1',positive_rule='all minimum-hop hubs; no-hit queries later filtered')
    dump(inp/'label_summary.json',meta);pairs.tofile(inp/'gate.triplets.i32')
    return pairs,torch.from_numpy(target),torch.from_numpy(good[10000:])

def train(ds):
    torch.set_num_threads(16);torch.set_num_interop_threads(1);torch.manual_seed(42);np.random.seed(42);random.seed(42)
    inp=RUN/'inputs'/ds;out=RUN/'models'/ds/'gate';out.mkdir(parents=True,exist_ok=True)
    if (out/'complete.json').exists():return
    assert not (out/'history.json').exists() or (out/'latest.resume.pt').exists(),'interrupted training lacks optimizer/RNG state; do not restart silently'
    cfg=dict(dim=json.loads((inp/'manifest.json').read_text())['shape'][1],hidden=2024,fusion_heads=8,hidden_heads=4,layers=2,feedforward=2048,fusion_dropout=0.,hidden_attention_dropout=.1,relu_dropout=.05,batch_size=16384,max_epochs=200,patience=20,learning_rate=1e-5,margin=1,seed=42,threads=16,batch_first=True,unique_hub_forward=True)
    dump(out/'config.json',cfg);pairs,target,usable=make_labels(inp);d=cfg['dim'];pairs=torch.from_numpy(pairs.astype('i8'));node=torch.from_numpy(np.fromfile(inp/'gate.hubs.f32','f4').reshape(512,d));graph=torch.from_numpy(np.fromfile(inp/'gate.graph2vec.f32','f4').reshape(512,d));q=torch.from_numpy(np.fromfile(inp/'gate_train.f32','f4').reshape(10000,d));qm=torch.from_numpy(np.fromfile(inp/'gate_monitor.f32','f4').reshape(1024,d));model=Tower(d)
    # No cross-example attention: batch versus singleton must agree at inference.
    model.eval()
    with torch.no_grad():
        a=model(node[:8],graph[:8]);b=torch.cat([model(node[i:i+1],graph[i:i+1]) for i in range(8)])
        torch.testing.assert_close(a,b,atol=3e-6,rtol=3e-5)
    dump(out/'independence.json',dict(status='PASS',max_abs=float((a-b).abs().max())))
    optimizer=torch.optim.Adam(model.parameters(),lr=1e-5);history=[];best=-1.;best_epoch=-1;stale=0;start_epoch=0;elapsed_before=0.;start=time.time()
    resume=out/'latest.resume.pt'
    if resume.exists():
        saved=torch.load(resume,map_location='cpu',weights_only=False);assert saved['config']==cfg
        model.load_state_dict(saved['model']);optimizer.load_state_dict(saved['optimizer']);torch.set_rng_state(saved['torch_rng']);history=saved['history'];best=saved['best'];best_epoch=saved['best_epoch'];stale=saved['stale'];start_epoch=saved['epoch']+1;elapsed_before=saved['elapsed_seconds'];start=time.time()
        # Latest checkpoint commits the epoch before updating the selected model.
        # Recover an interrupted improved-epoch export from that exact model state.
        if best_epoch==saved['epoch']:
            model.eval()
            with torch.no_grad():w=F.normalize(model(node,graph),dim=1)
            p=out/'best.pt.tmp';torch.save(model.state_dict(),p);p.replace(out/'best.pt');w.numpy().astype('f4').tofile(out/'W.f32');dump(out/'best.json',dict(epoch=best_epoch,monitor_route_accuracy=best,embedding_sha256=sha(out/'W.f32')))
        dump(out/f'resume_epoch{start_epoch}.json',dict(unix=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),epoch=start_epoch,optimizer_and_rng_restored=True));print('RESUME',ds,start_epoch,flush=True)
    criterion=nn.TripletMarginWithDistanceLoss(distance_function=lambda x,y:1-F.cosine_similarity(x,y),margin=1)
    for epoch in range(start_epoch,200):
        if stale>=20:break
        resource_check();t=time.time();model.train();order=torch.randperm(len(pairs));loss_sum=0.
        for lo in range(0,len(pairs),16384):
            batch=pairs[order[lo:lo+16384]];unique,inv=torch.unique(batch[:,0],sorted=True,return_inverse=True)
            optimizer.zero_grad(set_to_none=True);anchors=model(node[unique],graph[unique])[inv];loss=criterion(anchors,q[batch[:,1]],q[batch[:,2]]);assert torch.isfinite(loss);loss.backward();optimizer.step();loss_sum+=float(loss.detach())*len(batch)
        model.eval()
        with torch.no_grad():
            emb=model(node,graph);w=F.normalize(emb,dim=1);score=F.normalize(qm,dim=1)@w.T;pred=score.argmax(dim=1);acc=float(target[torch.arange(1024),pred][usable].float().mean());assert torch.isfinite(w).all()
        improved=acc>best
        if improved:best=acc;best_epoch=epoch;stale=0
        else:stale+=1
        row=dict(epoch=epoch,loss=loss_sum/len(pairs),monitor_route_accuracy=acc,best=improved,seconds=time.time()-t,total_seconds=elapsed_before+time.time()-start,stale=stale);history.append(row)
        # Rolling recovery state is temporary, not a second selected model.
        tmp=out/'latest.resume.pt.tmp';torch.save(dict(config=cfg,model=model.state_dict(),optimizer=optimizer.state_dict(),torch_rng=torch.get_rng_state(),history=history,best=best,best_epoch=best_epoch,stale=stale,epoch=epoch,elapsed_seconds=elapsed_before+time.time()-start),tmp);tmp.replace(resume)
        if improved:
            p=out/'best.pt.tmp';torch.save(model.state_dict(),p);p.replace(out/'best.pt');w.numpy().astype('f4').tofile(out/'W.f32');dump(out/'best.json',dict(epoch=epoch,monitor_route_accuracy=acc,embedding_sha256=sha(out/'W.f32')))
        dump(out/'history.json',history);print(ds,json.dumps(row),flush=True)
        if stale>=20:break
    dump(out/'complete.json',dict(status='COMPLETE',epochs=len(history),training_seconds=elapsed_before+time.time()-start,best=json.loads((out/'best.json').read_text()),stop='patience20' if stale>=20 else 'max200',model_parameters=sum(p.numel() for p in model.parameters()),threads=torch.get_num_threads(),checkpoint_sha256=sha(out/'best.pt')))
    if resume.exists():resume.unlink()

if __name__=='__main__':train(sys.argv[1])
