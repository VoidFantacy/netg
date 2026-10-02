import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
import hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;P=R.parents[1];MODEL=P/'stages/e122_action_coupled_ridge_v1'
C=json.loads((MODEL/'config.locked.json').read_text());OLD=Path(C['historical_root'])
inputs={}
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def load(p):inputs[str(p)]=ident(p);return dict(np.load(p))
def raw(p,t):inputs[str(p)]=ident(p);return np.fromfile(p,t)
def dump(p,v):assert not p.exists(),p;p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
dump(R/'frozen.json',{'files':{str(p):ident(p) for p in [Path(__file__),R/'protocol.md',MODEL/'reviews/seal.json']}})
started=time.perf_counter();summary={}
for ds,dc in C['datasets'].items():
    mp=MODEL/'models'/ds;d=dc['dimension'];n=C['n'];ids=raw(Path(dc['anchor']['ids']),'<i4');H=len(ids);A=H+1
    q=raw(OLD/'inputs'/ds/'fit/queries.f32','<f4').reshape(n,d).astype('f8');q/=np.linalg.norm(q,axis=1)[:,None]
    oof=load(mp/'oof.npz');folds=oof['folds'];lab=OLD/'results'/ds/'labels';done=json.loads((lab/'complete.json').read_text());rec=[];tim=[]
    for block in sorted(done['blocks'],key=lambda b:b['start']):
        b=lab/f"block_{block['start']}";nn=block['n']
        rec.append(np.stack([raw(b/'hits1.u8','u1').reshape(nn,A),raw(b/'hits100.u8','u1').reshape(nn,A)/100],axis=2))
        tim.append(raw(b/'seconds.f64','<f8').reshape(nn,A,2,3).mean(3))
    recall=np.concatenate(rec);seconds=np.concatenate(tim);dr=recall-recall[:,:1,:]
    # n, methods, K, target(u/recall), values(oracle/gated/factual/ranking/gating)
    decomp=np.zeros((n,4,2,2,5));mse=np.zeros((n,4,2,3));means=np.zeros((n,4,2));order=np.argsort(ids)
    checks=0
    for f in range(4):
        fit=np.flatnonzero(folds!=f);out=np.flatnonzero(folds==f);model=load(mp/f'fold_{f}.npz')
        tref=seconds[fit,0].mean(0);u=dr-.1*(seconds-seconds[:,:1,:])/tref
        for j,name in enumerate(C['arms'][2:]):
            for k in range(2):
                pred=q[out]@model['weights'][j,k]+model['biases'][j,k];a=1+order[pred[:,order].argmax(1)];s=pred[np.arange(len(out)),a-1]>0
                assert np.array_equal(np.where(s,a,0),oof['actions'][out,j+2,k])
                e=pred-u[out,1:,k];common=e.mean(1);centered=e-common[:,None]
                mse[out,j,k]=np.c_[(e*e).mean(1),common*common,(centered*centered).mean(1)];means[out,j,k]=pred.mean(1)
                for target,v in enumerate([u,dr]):
                    gain=v[out,a,k];oracle=np.maximum(0,v[out,1:,k].max(1));gated=np.maximum(0,gain);factual=s*gain
                    ranking=oracle-gated;gating=gated-factual
                    assert ranking.min()>-1e-12 and gating.min()>-1e-12
                    decomp[out,j,k,target]=np.c_[oracle,gated,factual,ranking,gating]
                    for t in np.linspace(0,len(out)-1,8,dtype=int):
                        i=out[t];o=max(0,max(float(z) for z in v[i,1:,k]));g=max(0,float(v[i,a[t],k]));p=float(v[i,a[t],k]) if s[t] else 0
                        assert max(abs(o-oracle[t]),abs(g-gated[t]),abs(p-factual[t]))<1e-12;checks+=1
    assert np.max(np.abs(mse[:,:,:,0]-mse[:,:,:,1]-mse[:,:,:,2]))<1e-12
    meanerr=float(np.max(np.abs(means-means[:,:1,:])));assert meanerr<1e-12
    np.savez(R/f'{ds}.query_values.npz',decomposition=decomp,mse=mse,mean_predictions=means,folds=folds)
    result={}
    for j,name in enumerate(C['arms'][2:]):
        result[name]={}
        for k,K in enumerate(C['K']):
            error=mse[:,j,k].mean(0);entry={'MSE':float(error[0]),'common_error_MSE':float(error[1]),'action_contrast_error_MSE':float(error[2]),'common_fraction':float(error[1]/error[0])}
            for target,tn in enumerate(['utility','recall']):
                val=decomp[:,j,k,target].mean(0);o,g,p,r,s=val
                entry[tn]={'oracle_gain':float(o),'oracle_switch_gain_current_ranking':float(g),'factual_gain':float(p),'ranking_regret':float(r),'switch_regret':float(s),'ranking_fraction_of_regret':float(r/(o-p)),'switch_fraction_of_regret':float(s/(o-p)),'oracle_switch_captures_oracle_fraction':float(g/o)}
            result[name][str(K)]=entry
    summary[ds]={'methods':result,'mean_prediction_max_control_difference':meanerr,'scalar_checks':checks}
    print(ds,{k:result['FunctionSmooth'][k] for k in ['1','100']},flush=True)
for path,v in inputs.items():assert ident(Path(path))==v,path
dump(R/'inputs.json',inputs)
dump(R/'summary.json',{'status':'DESCRIPTIVE_ONLY','datasets':summary,'seconds':time.perf_counter()-started,'new_training':0,'new_searches':0,'input_files':len(inputs)})
