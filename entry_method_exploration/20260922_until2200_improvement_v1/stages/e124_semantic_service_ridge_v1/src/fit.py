import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='8'
import hashlib,json,time,resource
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];C=json.loads((R/'config.locked.json').read_text());OLD=Path(C['historical_root']);SERVICE=Path(C['service_root']);DIRECT=Path(C['direct_reference']);inputs={}
def read(p):return json.loads(p.read_text())
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def raw(p,t):inputs[str(p)]=ident(p);return np.fromfile(p,t)
def loaded(p):inputs[str(p)]=ident(p);return dict(np.load(p))
def dump(p,v):assert not p.exists(),p;p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
assert read(R/'reviews/prepare_complete.json')['status']=='PASS'
fixed=[R/'protocol.md',R/'theory.md',R/'config.locked.json',Path(__file__),SERVICE/'reviews/seal.json']+list((R/'inputs').glob('*/*.npz'))
dump(R/'reviews/fit_frozen.json',{'files':{str(p):ident(p) for p in fixed}})
def choose(pred,ids):
    order=np.argsort(ids,kind='stable');a=order[pred[:,order].argmax(1)];return np.where(pred[np.arange(len(pred)),a]>0,a+1,0).astype('i4')
def ridge(x,y,alpha):
    xm=x.mean(0);ym=y.mean(0);xx=x-xm;yy=y-ym;g=xx.T@xx;c=xx.T@yy;lam,p=np.linalg.eigh(g);w=p@((p.T@c)/(lam[:,None]+alpha));b=ym-xm@w
    residual=float(np.linalg.norm(g@w+alpha*w-c)/max(np.linalg.norm(c),1e-30));assert residual<1e-10
    return w,b,residual
def bootstrap(x,seed):
    rng=np.random.default_rng(seed);pieces=[]
    for lo in range(0,C['bootstrap_reps'],128):
        ix=rng.integers(0,len(x),size=(min(128,C['bootstrap_reps']-lo),len(x)));pieces.append(x[ix].mean(1))
    return np.concatenate(pieces)
def ci(x):
    a=(1-C['interval_coverage'])/2;return list(map(float,np.quantile(x,[a,1-a])))
# Convex composition identity on an independent small fixture before actual labels.
rng=np.random.default_rng(2026092225);sx=rng.normal(size=(37,9));sy=rng.normal(size=(37,11));st=rng.normal(size=(11,7));sw,sb,_=ridge(sx,sy,10);dw,db,_=ridge(sx,sy@st,10)
error=max(float(np.max(np.abs(sw@st-dw))),float(np.max(np.abs(sb@st-db))));assert error<1e-12
dump(R/'reviews/synthetic_checks.json',{'status':'PASS','ridge_composition_max_error':error})
started=time.perf_counter();summaries={};all_u={};all_boot={};reference_errors=[]
for di,(ds,dc) in enumerate(C['datasets'].items()):
    mp=R/'models'/ds;mp.mkdir(parents=True);rp=R/'results'/ds;rp.mkdir(parents=True)
    semantic=loaded(R/'inputs'/ds/'semantic.npz');roles=loaded(R/'inputs'/ds/'roles.npz');q=semantic['q_unit'];owner=semantic['owners'];ids=semantic['ids'];H=len(ids);A=H+1;n=C['n'];d=dc['dimension'];ri=roles['response_indices'];qr=q[ri]
    a1=np.zeros((len(q),H));a1[np.arange(len(q)),owner[:,0]]=1
    a100=np.zeros((len(q),H));np.add.at(a100,(np.repeat(np.arange(len(q)),100),owner.ravel()),.01);assert np.max(np.abs(a100.sum(1)-1))<1e-12
    semantic_targets=[a1,a100];lab=OLD/'results'/ds/'labels';done=read(lab/'complete.json');rec=[];tim=[]
    for block in sorted(done['blocks'],key=lambda b:b['start']):
        p=lab/f"block_{block['start']}";nn=block['n'];h1=raw(p/'hits1.u8','u1').reshape(nn,A);h100=raw(p/'hits100.u8','u1').reshape(nn,A);secs=raw(p/'seconds.f64','<f8').reshape(nn,A,2,3)
        assert np.isfinite(secs).all() and secs.min()>0;rec.append(np.stack([h1,h100/100.],axis=2));tim.append(secs.mean(3))
    recall=np.concatenate(rec);seconds=np.concatenate(tim);dr=recall-recall[:,:1,:];folds=roles['response_folds'];M=len(C['arms'])
    actions=np.zeros((n,M,2),dtype='i4');values=np.zeros((n,M,2,3));selected_pred=np.zeros((n,M,2));records=[];semantic_records=[]
    for f in range(4):
        tr=np.flatnonzero(folds!=f);out=np.flatnonzero(folds==f);sem_small=roles[f'response_fit_{f}'];sem_large=roles[f'semantic_fit_{f}'];sem_out=roles[f'outer_{f}']
        assert np.array_equal(ri[tr],sem_small) and np.array_equal(ri[out],sem_out) and not set(sem_large)&set(sem_out)
        service=loaded(SERVICE/'models_v2'/ds/f'fold_{f}.npz');reference=loaded(DIRECT/'models'/ds/f'fold_{f}.npz');reference_oof=loaded(DIRECT/'models'/ds/'oof.npz')
        assert np.array_equal(service['fit_rows'],semantic['rows'][sem_small]) and np.array_equal(service['outer_rows'],semantic['rows'][sem_out])
        tref=seconds[tr,0].mean(0);assert np.max(np.abs(tref-service['time_reference']))<1e-16;dt=(seconds-seconds[:,:1,:])/tref;u=dr-C['cost_weight']*dt
        weights=np.empty((4,2,d,H));biases=np.empty((4,2,H));maps=np.empty((2,2,d,H));map_biases=np.empty((2,2,H));errors=[]
        for k,K in enumerate(C['K']):
            w,b,residual=ridge(qr[tr],u[tr,1:,k],C['alpha']);weights[0,k]=w;biases[0,k]=b
            referr=max(float(np.max(np.abs(w-reference['weights'][0,k]))),float(np.max(np.abs(b-reference['biases'][0,k]))));assert referr<1e-11;reference_errors.append(referr)
            direct_actions=choose(qr[out]@w+b,ids);assert np.array_equal(direct_actions,reference_oof['actions'][out,2,k])
            for size_index,fit_indices in enumerate([sem_small,sem_large]):
                wa,ba,res=ridge(q[fit_indices],semantic_targets[k][fit_indices],C['alpha']);maps[size_index,k]=wa;map_biases[size_index,k]=ba
                modes=[(1,'SemanticService3k',1)] if size_index==0 else [(2,'SemanticService19k',1),(3,'ShuffleService19k',2)]
                latent=qr[out]@wa+ba
                for model_index,name,table_index in modes:
                    table=service['tables'][table_index,k,:,1:];ww=wa@table;bb=ba@table;weights[model_index,k]=ww;biases[model_index,k]=bb
                    compiled=qr[out]@ww+bb;sequential=latent@table;err=float(np.max(np.abs(compiled-sequential)));assert err<1e-12;errors.append(err)
                semantic_records.append({'fold':f,'K':K,'semantic_fit_n':len(fit_indices),'response_fit_n':len(tr),'normal_equation_relative_residual':res,'outer_label_MSE':float(((latent-semantic_targets[k][sem_out])**2).mean()),'outer_label_mean_L1_error':float(np.abs(latent-semantic_targets[k][sem_out]).sum(1).mean()),'negative_component_fraction':float((latent<0).mean()),'row_mass_max_error':float(np.abs(latent.sum(1)-1).max()),'region_top1_accuracy':float((latent.argmax(1)==owner[sem_out,0]).mean())})
            for j,name in enumerate(C['arms'][1:]):
                m=j+1;pred=qr[out]@weights[j,k]+biases[j,k];a=choose(pred,ids);actions[out,m,k]=a;selected_pred[out,m,k]=np.where(a>0,pred[np.arange(len(out)),np.maximum(a-1,0)],0)
                tra=choose(qr[tr]@weights[j,k]+biases[j,k],ids)
                records.append({'fold':f,'K':K,'method':name,'train_u':float(u[tr,tra,k].mean()),'outer_u':float(u[out,a,k].mean()),'train_recall_gain_pp':float(dr[tr,tra,k].mean()*100),'outer_recall_gain_pp':float(dr[out,a,k].mean()*100),'predicted_selected_outer_u':float(selected_pred[out,m,k].mean()),'switches':int((a>0).sum()),'time_reference_seconds':float(tref[k])})
            for m in range(M):
                a=actions[out,m,k]
                for col,quantity in enumerate([dr,dt,u]):values[out,m,k,col]=quantity[out,a,k]
        np.savez(mp/f'fold_{f}.npz',weights=weights,biases=biases,semantic_maps=maps,semantic_biases=map_biases,time_reference=tref,response_fit_rows=semantic['rows'][sem_small],semantic_fit_rows=semantic['rows'][sem_large],outer_rows=semantic['rows'][sem_out],composition_errors=np.array(errors))
        print(ds,'fold',f,'complete',flush=True)
    np.savez(mp/'oof.npz',actions=actions,values=values,selected_prediction=selected_pred,folds=folds,rows=semantic['rows'][ri]);uu=values[:,:,:,2].mean(2);bb=bootstrap(uu,C['seed']+di*10000);all_u[ds]=uu;all_boot[ds]=bb;methods={}
    for m,name in enumerate(C['arms']):
        detail={}
        for k,K in enumerate(C['K']):
            g=values[:,m,k,0];detail[str(K)]={'recall_gain_pp':float(g.mean()*100),'graph_time_change_pct':float(values[:,m,k,1].mean()*100),'u_mean':float(values[:,m,k,2].mean()),'positive_queries':int((g>0).sum()),'negative_queries':int((g<0).sum()),'positive_mass':float(g[g>0].sum()),'negative_mass':float(-g[g<0].sum()),'switches':int((actions[:,m,k]>0).sum()),'predicted_selected_u_mean':float(selected_pred[:,m,k].mean())}
        methods[name]={'equal_K_u_mean':float(uu[:,m].mean()),'equal_K_u_interval':ci(bb[:,m]),'K':detail}
    summaries[ds]={'methods':methods};dump(rp/'fold_metrics.json',records);dump(rp/'semantic_diagnostics.json',semantic_records);print(ds,{n:round(v['equal_K_u_mean']*100,5) for n,v in methods.items()},flush=True)
m=C['arms'].index(C['eligible']);checks={};contrasts={}
for ds,s in summaries.items():
    v=s['methods'][C['eligible']];checks[ds+'.positive_u']=v['equal_K_u_interval'][0]>0;checks[ds+'.recall_floor']=all(x['recall_gain_pp']>=-C['max_k_recall_loss_pp'] for x in v['K'].values())
for control in ['DirectUtility3k','ShuffleService19k']:
    j=C['arms'].index(control);boot=sum((b[:,m]-b[:,j])/len(all_boot) for b in all_boot.values());means={ds:float((u[:,m]-u[:,j]).mean()) for ds,u in all_u.items()};bounds=ci(boot)
    checks['beats_'+control]=all(v>0 for v in means.values()) and bounds[0]>0;contrasts[control]={'dataset_mean_differences':means,'equal_dataset_interval':bounds}
passed=all(checks.values());status='PASS_DEVELOPMENT_ONLY' if passed else 'STOP_SEMANTIC_SERVICE_LINEAR_COMPILE'
dump(R/'results/information.json',{'status':status,'datasets':summaries,'checks':checks,'contrasts':contrasts,'interval_coverage':C['interval_coverage'],'online_GT_input':False})
dump(R/'results/gate.json',{'status':status,'eligible':C['eligible'],'default_changed':False,'full_QPS_measured':False})
dump(R/'reviews/response_inputs.json',inputs)
for path,x in inputs.items():assert ident(Path(path))==x,path
dump(R/'reviews/fit_complete.json',{'status':'PASS','seconds':time.perf_counter()-started,'ridge_heads':48,'compiled_service_heads':48,'direct_heads':16,'max_reference_parameter_error':max(reference_errors),'maxrss_GiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20,'input_files':len(inputs),'new_ann_nsg_gt':0,'new_search_graphs':0,'new_QPS':0,'independent_audit_pending':True})
print(status,flush=True)
