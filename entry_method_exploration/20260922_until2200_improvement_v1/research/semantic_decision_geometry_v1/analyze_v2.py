import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='8'
import hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;P=R.parent.parent;E=P/'stages/e124_semantic_service_ridge_v1';T=P/'stages/e123_target_service_gate_v1'
C=json.loads((E/'config.locked.json').read_text());I={}
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,v):assert not p.exists(),p;p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def load(p):I[str(p)]=ident(p);return np.load(p)
def read(p):I[str(p)]=ident(p);return json.loads(p.read_text())
def raw(p,t):I[str(p)]=ident(p);return np.fromfile(p,t)
def desc(v):return {'mean':float(v.mean()),'median':float(np.median(v)),'q10':float(np.quantile(v,.1)),'q90':float(np.quantile(v,.9))}
dump(R/'reviews/frozen_v2.json',{'files':{str(p):ident(p) for p in [R/'protocol.md',Path(__file__),E/'reviews/seal.json',T/'reviews/seal.json']}})
# Both predictions are valid simplex points; smaller MSE can still lose the decision.
a=np.array([.40,.35,.25]);b=np.array([.37,.38,.25]);c=np.array([.48,.43,.09]);s=np.array([[0,.05],[0,-.05],[0,0.]])
assert np.allclose([a.sum(),b.sum(),c.sum()],1) and min(a.min(),b.min(),c.min())>=0
assert np.mean((b-a)**2)<np.mean((c-a)**2) and (b@s).argmax()==0 and (a@s).argmax()==(c@s).argmax()==1
example={'truth':a.tolist(),'lower_MSE_prediction':b.tolist(),'higher_MSE_prediction':c.tolist(),'lower_MSE':float(np.mean((b-a)**2)),'higher_MSE':float(np.mean((c-a)**2)),'lower_MSE_decision_regret':float((a@s).max()-(a@s)[(b@s).argmax()])}
g=np.array([0.,.1,-.3]);ghat=g+17;assert g.argmax()==ghat.argmax() and np.ptp(ghat-g)<1e-12
dump(R/'reviews/synthetic_v2.json',{'status':'PASS','simplex_counterexample':example,'common_shift':17})
start=time.perf_counter();summaries={};max_identity=0.;max_bound=0.;scalar_checks=0
for ds,dc in C['datasets'].items():
    sem=load(E/'inputs'/ds/'semantic.npz');role=load(E/'inputs'/ds/'roles.npz');eo=load(E/'models'/ds/'oof.npz');to=load(T/'models_v2'/ds/'oof.npz')
    ids=sem['ids'];H=len(ids);n=C['n'];ri=role['response_indices'];q=sem['q_unit'][ri];owners=sem['owners'][ri];folds=role['response_folds'];actual=[];times=[];old=Path(C['historical_root'])/'results'/ds/'labels'
    for block in sorted(read(old/'complete.json')['blocks'],key=lambda x:x['start']):
        bp=old/f"block_{block['start']}";nn=block['n'];a=H+1
        h1=raw(bp/'hits1.u8','u1').reshape(nn,a);h100=raw(bp/'hits100.u8','u1').reshape(nn,a);secs=raw(bp/'seconds.f64','<f8').reshape(nn,a,2,3)
        actual.append(np.stack([h1,h100/100.],-1));times.append(secs.mean(-1))
    recall=np.concatenate(actual);seconds=np.concatenate(times)
    names=['semantic_MSE','semantic_L1','negative_mass','service_centered_MSE','service_error_range','privileged_score_regret','actual_u_gap','service_residual_contrast','action_agreement','privileged_selected_residual','predicted_selected_residual','action_centered_residual_MSE','true_u_privileged','true_u_predicted']
    data={key:np.zeros((n,2,2)) for key in names}
    for f in range(4):
        out=np.flatnonzero(folds==f);tr=np.flatnonzero(folds!=f);m=load(E/'models'/ds/f'fold_{f}.npz');service=load(T/'models_v2'/ds/f'fold_{f}.npz')
        yy=[np.eye(H)[owners[out,0]],np.stack([np.bincount(z,minlength=H)/100 for z in owners[out]])]
        for k in range(2):
            table=service['tables'][1,k];assert np.max(np.abs(table[:,0]))==0
            g=yy[k]@table;tref=seconds[tr,0,k].mean();u=(recall[out,:,k]-recall[out,:1,k])-.1*(seconds[out,:,k]-seconds[out,:1,k])/tref
            order=np.r_[0,np.argsort(ids,kind='stable')+1];ap=order[g[:,order].argmax(1)];assert np.array_equal(ap,to['actions'][out,read(T/'config.locked.json')['arms'].index('TargetService'),k]);ix=np.arange(len(out));res=u-g
            for size in range(2):
                ah=q[out]@m['semantic_maps'][size,k]+m['semantic_biases'][size,k];gh=ah@table
                chosen=order[gh[:,order].argmax(1)];assert np.array_equal(chosen,eo['actions'][out,size+2,k]);e=gh-g
                gap=g[ix,ap]-g[ix,chosen];ugap=u[ix,ap]-u[ix,chosen];rcontrast=res[ix,ap]-res[ix,chosen]
                err=float(np.max(np.abs(ugap-gap-rcontrast)));max_identity=max(max_identity,err);assert err<1e-12
                viol=float(np.max(gap-np.ptp(e,axis=1)));max_bound=max(max_bound,viol);assert viol<1e-12 and gap.min()>-1e-12
                vals=[((ah-yy[k])**2).mean(1),np.abs(ah-yy[k]).sum(1),-np.minimum(ah,0).sum(1),((e-e.mean(1,keepdims=True))**2).mean(1),np.ptp(e,axis=1),gap,ugap,rcontrast,ap==chosen,res[ix,ap],res[ix,chosen],((res-res.mean(1,keepdims=True))**2).mean(1),u[ix,ap],u[ix,chosen]]
                for key,v in zip(names,vals):data[key][out,size,k]=v
                # Deterministic scalar summation at evenly spaced rows/actions.
                for j in np.linspace(0,len(out)-1,8,dtype=int):
                    for action in [0,int(ap[j]),int(chosen[j]),H]:
                        sg=sum(float(yy[k][j,z])*float(table[z,action]) for z in range(H))
                        sh=sum(float(ah[j,z])*float(table[z,action]) for z in range(H))
                        assert abs(sg-g[j,action])<1e-12 and abs(sh-gh[j,action])<1e-12;scalar_checks+=2
    detail={}
    for k,K in enumerate(C['K']):
        detail[str(K)]={str(size):{key:desc(v[:,si,k]) for key,v in data.items()} for si,size in enumerate([3072,18976])}
        detail[str(K)]['19k_minus_3k']={key:desc(v[:,1,k]-v[:,0,k]) for key,v in data.items()}
    np.savez(R/'results'/f'{ds}.npz',**data,folds=folds,rows=sem['rows'][ri]);summaries[ds]=detail
    print(ds,{K:{size:{name:round(stats[name]['mean'],7) for name in ['service_centered_MSE','privileged_score_regret','actual_u_gap','service_residual_contrast']} for size,stats in detail[K].items()} for K in detail},flush=True)
for p,v in I.items():assert ident(Path(p))==v
dump(R/'results/summary.json',summaries);dump(R/'reviews/inputs.json',I)
dump(R/'reviews/complete.json',{'status':'PASS','seconds':time.perf_counter()-start,'input_files':len(I),'scalar_checks':scalar_checks,'all_query_identity_error':max_identity,'maximum_bound_violation':max_bound,'fits_ann_nsg_gt_graph_qps':0,'posthoc_diagnostic':True})
