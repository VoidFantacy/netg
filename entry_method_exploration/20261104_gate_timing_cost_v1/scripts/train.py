from model_io import *
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.tree import DecisionTreeRegressor
import torch
from torch import nn
torch.set_num_threads(1)
ds,K,L=sys.argv[1],int(sys.argv[2]),int(sys.argv[3])
start=time.perf_counter();p,m,f,actime,groups,y,gateX=load_labels(ds,K,L)
out=R/'storage/models'/ds/f'k{K}_L{L}';out.mkdir(parents=True,exist_ok=False)
fit=m[:,0]<2048;dev=(m[:,0]>=2048)&(m[:,0]<2560);cal=m[:,0]>=2560
teachers=[];tp=[];cost=[]
for b in range(2):
    t=time.perf_counter()
    tmodel=HistGradientBoostingRegressor(max_iter=128,max_leaf_nodes=15,l2_regularization=10,learning_rate=.08,random_state=198,early_stopping=False)
    tmodel.fit(f[fit],y[fit,b]);exp=tree_export(tmodel);teachers.append(exp)
    pred=tmodel.predict(f);tp.append(pred);cost.append(time.perf_counter()-t)
    dump(out/f'teacher{b}.json',exp)
tp=np.column_stack(tp)
qfeat=np.column_stack([f[:,24:40],f[:,STATE]])
nodefeat=np.column_stack([f[:,40:56],f[:,72:88],f[:,21:23]])
cfeat=f[:,CHEAP]
def standard(x,mask):
    mean=x[mask].astype('float64').mean(0);scale=x[mask].astype('float64').std(0);scale[scale<1e-8]=1
    return ((x-mean)/scale).astype('float32'),mean,scale
qx,qmean,qscale=standard(qfeat,fit);nx,nmean,nscale=standard(nodefeat,fit);cx,cmean,cscale=standard(cfeat,fit)
N=3072;M=max(len(v) for v in groups.values());assert M<=96
query=np.zeros((N,25),'float32');nodes=np.zeros((N,M,34),'float32');cheap=np.zeros((N,M,23),'float32')
target=np.zeros((N,M,2),'float32');truth=target.copy();mask=np.zeros((N,M),bool)
for qi,ix in groups.items():
    n=len(ix);query[qi]=qx[ix[0]];nodes[qi,:n]=nx[ix];cheap[qi,:n]=cx[ix];target[qi,:n]=tp[ix];truth[qi,:n]=y[ix];mask[qi,:n]=True
query,nodes,cheap,target,truth,mask=[torch.from_numpy(v) for v in (query,nodes,cheap,target,truth,mask)]
class Student(nn.Module):
    def __init__(self):
        super().__init__();self.q=nn.Sequential(nn.Linear(25,64),nn.ReLU(),nn.Linear(64,64));self.n=nn.Sequential(nn.Linear(34,64),nn.ReLU(),nn.Linear(64,32));self.c=nn.Linear(23,2)
    def forward(self,q,n,c):
        qe=self.q(q).reshape(-1,2,32);ne=self.n(n)
        return torch.einsum('bhr,bnr->bnh',qe,ne)/(32**.5)+self.c(c)
torch.manual_seed(198);np.random.seed(198);s=Student();optim=torch.optim.Adam(s.parameters(),lr=.002)
best=None;bestkey=None;epochs=[];gen=np.random.Generator(np.random.PCG64(198))
for epoch in range(24):
    s.train();loss_total=0.
    for batch in np.array_split(gen.permutation(2048),64):
        v=s(query[batch],nodes[batch],cheap[batch]);valid=mask[batch].unsqueeze(-1).expand_as(v)
        mse=((v-target[batch])**2)[valid].mean();actual=((v-truth[batch])**2)[valid].mean()
        logits=v.masked_fill(~valid,-1e9);positive=truth[batch].clamp_min(0)*valid
        sums=positive.sum(1,keepdim=True);weights=positive/sums.clamp_min(1e-8)
        ce=-(weights*torch.log_softmax(logits,dim=1)).sum(1);has=sums.squeeze(1)>0
        rank=ce[has].mean() if has.any() else ce.sum()*0
        loss=.5*mse+.5*actual+.25*rank
        optim.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(s.parameters(),5);optim.step();loss_total+=float(loss)
    s.eval();net=0;selected=[]
    with torch.no_grad():
        for batch in np.array_split(np.arange(2048,2560),16):
            v=s(query[batch],nodes[batch],cheap[batch]);v=v.masked_fill(~mask[batch].unsqueeze(-1),-1e9)
            choice=v.argmax(1)
            for j,q in enumerate(batch):
                if int(q) in groups:
                    for b in range(2):net+=float(truth[q,choice[j,b],b])
    key=(net,-epoch)
    if bestkey is None or key>bestkey:
        bestkey=key;best={k:v.detach().clone() for k,v in s.state_dict().items()}
    epochs.append(dict(epoch=epoch+1,loss=loss_total/64,dev_two_budget_gain=net))
    if epoch%6==5:print('EPOCH',ds,K,L,epoch+1,net,flush=True)
s.load_state_dict(best)
def v(x):return x.detach().numpy().astype('float64').tolist()
export=dict(q_mean=qmean.tolist(),q_scale=qscale.tolist(),n_mean=nmean.tolist(),n_scale=nscale.tolist(),c_mean=cmean.tolist(),c_scale=cscale.tolist(),
            qw1=v(s.q[0].weight),qb1=v(s.q[0].bias),qw2=v(s.q[2].weight),qb2=v(s.q[2].bias),nw1=v(s.n[0].weight),nb1=v(s.n[0].bias),nw2=v(s.n[2].weight),nb2=v(s.n[2].bias),cw=v(s.c.weight),cb=v(s.c.bias),selected_epoch=-bestkey[1]+1)
node_ids=np.fromfile(p/'nodes.i32','<i4');node_raw=np.fromfile(p/'nodes.f32','<f4').reshape(-1,34).astype('float64')
hidden=np.maximum(((node_raw-nmean)/nscale)@np.asarray(export['nw1']).T+np.asarray(export['nb1']),0)
node_emb=hidden@np.asarray(export['nw2']).T+np.asarray(export['nb2'])
node_ids.tofile(out/'node_ids.i32');node_emb.astype('<f8').tofile(out/'node_embeddings.f64')
export['_ids']=m[:,1];sp=student_predict(export,f,node_emb,node_ids);del export['_ids']
# Evaluate the exported student in float64, exactly the precision of native deployment.
rows0=select(groups,sp,tp,y,0.);devrows=[x for x in rows0 if 2048<=x['q']<2560]
reference=sum(max(0,float(y[x['cascade'][1],1])) for x in devrows)
choices=[]
for lam in [0,.25,.5,1,2]:
    selected=select(groups,sp,tp,y,lam);d=[x for x in selected if 2048<=x['q']<2560]
    gain=sum(max(0,x['action_gain']) for x in d)
    cost_units=sum((.25,1)[x['action_budget']] for x in d if x['action_budget']>=0)
    choices.append(dict(lam=lam,retained_positive=gain,reference_positive=reference,cost_units=cost_units))
feasible=[x for x in choices if x['retained_positive']>=.9*reference]
chosen=min(feasible,key=lambda x:(x['cost_units'],-x['retained_positive'],x['lam'])) if feasible else choices[0]
lam=chosen['lam'];selected=select(groups,sp,tp,y,lam)
action_gain=np.zeros(N);action_index=np.full(N,-1);action_budget=np.full(N,-1)
for x in selected:action_gain[x['q']]=x['action_gain'];action_index[x['q']]=x['action_index'];action_budget[x['q']]=x['action_budget']
gate=DecisionTreeRegressor(max_depth=3,min_samples_leaf=32,random_state=198).fit(gateX[2048:2560],np.maximum(action_gain[2048:2560],0))
gx=single_tree_export(gate);gp=gate.predict(gateX);reference=sum(np.maximum(action_gain[2560:],0));thresholds=sorted(set(float(np.quantile(gp[2048:2560],1-rate)) for rate in [1,.75,.5,.25]))
screen=[]
for t in thresholds:
    enabled=gp[2560:]>=t;kept=float(np.maximum(action_gain[2560:],0)[enabled].sum())
    screen.append(dict(threshold=t,enabled=int(enabled.sum()),positive_kept=kept,reference_positive=float(reference)))
if reference>0:
    feasible=[x for x in screen if x['positive_kept']>=.9*reference]
    threshold=min(feasible,key=lambda x:(x['enabled'],-x['positive_kept'],x['threshold']))['threshold'] if feasible else min(thresholds)
    off=False
else:threshold=0.;off=True
gx.update(threshold=threshold,gate_all_off=off)
export.update(teacher=teachers,gate=gx,lam=lam,node_ids=str(out/'node_ids.i32'),node_embeddings=str(out/'node_embeddings.f64'),state=dict(K=K,L=L),bank='Q8',feature_count=104)
dump(out/'model.json',export);csvwrite(out/'epochs.csv',epochs)
with gzip.open(out/'prediction_reference.f64.gz','wb',compresslevel=3) as z:z.write(np.column_stack([sp,tp]).astype('<f8').tobytes())
summary=dict(status='TRAINED_FROZEN_STATE_MODEL',dataset=ds,K=K,L=L,rows=len(m),fit_rows=int(fit.sum()),dev_rows=int(dev.sum()),cal_rows=int(cal.sum()),teacher_seconds=cost,
    student_best_dev_gain=bestkey[0],selected_epoch=export['selected_epoch'],lambda_development=choices,chosen_lambda=lam,gate_calibration=screen,gate_threshold=threshold,gate_off=off,
    fit_queries=2048,development_gate_fit_queries=512,independent_cal_queries=512,seconds=time.perf_counter()-start,
    labels_sha256=sha(p/'labels.bin.gz'),model_sha256=sha(out/'model.json'),online_GT=False)
dump(out/'training.json',summary);print('TRAINED',ds,K,L,summary['seconds'],flush=True)
