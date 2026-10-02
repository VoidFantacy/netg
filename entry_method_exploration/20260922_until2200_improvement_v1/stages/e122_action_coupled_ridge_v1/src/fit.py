"""Frozen action-graph function regularization. Historical development only."""
import os
for key in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS']:
    os.environ[key] = '8'
import datetime, hashlib, json, time
from pathlib import Path
import numpy as np

R = Path(__file__).resolve().parents[1]
def read(p): return json.loads(Path(p).read_text())
def ident(p):
    p = Path(p)
    return {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p, value):
    assert not p.exists(), p
    p.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
C = read(R / 'config.locked.json')
OLD = Path(C['historical_root'])
inputs = {}
def raw(p, dtype):
    inputs[str(p)] = ident(p)
    return np.fromfile(p, dtype)
def choose(scores, ids):
    order = np.argsort(ids, kind='stable')
    a = order[np.argmax(scores[:, order], axis=1)]
    return np.where(scores[np.arange(len(scores)), a] > 0, a + 1, 0).astype('i4')
def laplacian(left, right, H):
    b = np.zeros((H, H))
    b[left, right] = 1
    assert np.all(b.sum(1) == C['neighbors'])
    a = (b + b.T) / 2
    return (np.diag(a.sum(1)) - a) / a.sum(1).mean()
def fit_spectral(x, y, lap, alpha, beta=1, coefficient=False):
    g = x.T @ x
    lam, p = np.linalg.eigh(g)
    gam, v = np.linalg.eigh(lap)
    c = x.T @ y
    den = (lam[:, None] + alpha + beta * gam[None, :]) if coefficient else (lam[:, None] * (1 + beta * gam[None, :]) + alpha)
    return p @ ((p.T @ c @ v) / den) @ v.T

def synthetic_checks():
    rng = np.random.default_rng(2026092220)
    x = rng.normal(size=(19, 5)); y = rng.normal(size=(19, 7))
    a = rng.uniform(size=(7, 7)); a = (a + a.T) / 2
    lap = np.diag(a.sum(1)) - a
    g = x.T @ x; c = x.T @ y
    w = fit_spectral(x, y, lap, 10)
    direct = np.linalg.solve(np.kron(np.eye(7) + lap, g) + 10*np.eye(35), c.ravel(order='F')).reshape(5, 7, order='F')
    zero = fit_spectral(x, y, lap, 10, beta=0)
    ridge = np.linalg.solve(g + 10*np.eye(5), c)
    wc = fit_spectral(x, y, lap, 10, beta=10, coefficient=True)
    directc = np.linalg.solve(np.kron(np.eye(7), g + 10*np.eye(5)) + 10*np.kron(lap, np.eye(5)), c.ravel(order='F')).reshape(5, 7, order='F')
    xm = rng.normal(size=5); ym = rng.normal(size=7); b = ym-xm@w
    query = rng.normal(size=(13, 5))
    checks = {
        'function_vs_kronecker_max_error': float(np.max(np.abs(w-direct))),
        'coefficient_vs_kronecker_max_error': float(np.max(np.abs(wc-directc))),
        'zero_beta_vs_ridge_max_error': float(np.max(np.abs(zero-ridge))),
        'normal_equation_max_residual': float(np.max(np.abs(g@w+g@w@lap+10*w-c))),
        'augmented_prediction_max_error': float(np.max(np.abs((query-xm)@w+ym - np.c_[query,np.ones(len(query))]@np.vstack([w,b])))),
    }
    assert max(checks.values()) < 1e-10, checks
    dump(R/'reviews/synthetic_checks.json', {'status':'PASS','checks':checks})

def bootstrap(x, seed):
    rng=np.random.default_rng(seed); out=[]
    for start in range(0,C['bootstrap_reps'],128):
        ix=rng.integers(0,len(x),size=(min(128,C['bootstrap_reps']-start),len(x)))
        out.append(x[ix].mean(1))
    return np.concatenate(out)
def ci(x):
    a=(1-C['interval_coverage'])/2
    return list(map(float,np.quantile(x,[a,1-a])))

frozen = [R/'protocol.md',R/'config.locked.json',Path(__file__)]
for ds in C['datasets']:
    frozen.extend([Path(C['roles_root'])/ds/'roles.npz',Path(C['relations_root'])/f'{ds}.relations.npz'])
dump(R/'reviews/fit_frozen.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':{str(p):ident(p) for p in frozen}})
synthetic_checks()
started=time.perf_counter(); summaries={}; all_boot={}; all_u={}; records={}
for di,(ds,dc) in enumerate(C['datasets'].items()):
    dest=R/'models'/ds; dest.mkdir(parents=True)
    res=R/'results'/ds; res.mkdir(parents=True)
    ids=raw(dc['anchor']['ids'],'<i4'); H=len(ids); A=H+1; n=C['n']; d=dc['dimension']
    q=raw(OLD/'inputs'/ds/'fit/queries.f32','<f4').reshape(n,d).astype('f8')
    norms=np.linalg.norm(q,axis=1); assert np.all(norms>0) and np.isfinite(q).all()
    q/=norms[:,None]
    roles_path=Path(C['roles_root'])/ds/'roles.npz'; inputs[str(roles_path)]=ident(roles_path)
    roles=dict(np.load(roles_path)); folds=roles['folds']; assert np.bincount(folds).tolist()==[1024]*4
    rows=raw(OLD/'inputs'/ds/'fit/row_ids.i64','<i8'); assert np.array_equal(rows,roles['rows'])
    rp=Path(C['relations_root'])/f'{ds}.relations.npz'; inputs[str(rp)]=ident(rp); pairs=dict(np.load(rp))
    lap=laplacian(pairs['RawHub_left'],pairs['RawHub_right'],H)
    plap=laplacian(pairs['RawHub_shuffle_left'],pairs['RawHub_shuffle_right'],H)
    gam,v=np.linalg.eigh(lap); pgam,pv=np.linalg.eigh(plap)
    assert np.max(np.abs(gam-pgam))<1e-12 and gam.min()>-1e-12
    assert abs(np.trace(lap)/H-1)<1e-14 and np.max(np.abs(lap.sum(1)))<1e-14
    np.savez(dest/'geometry.npz',lap=lap,permuted_lap=plap,eigenvalues=gam,ids=ids,folds=folds,rows=rows)
    labels=OLD/'results'/ds/'labels'; done=read(labels/'complete.json'); rec=[]; tim=[]
    for block in sorted(done['blocks'],key=lambda b:b['start']):
        b=labels/f"block_{block['start']}"; count=block['n']; assert block['A']==A
        h1=raw(b/'hits1.u8','u1').reshape(count,A); h100=raw(b/'hits100.u8','u1').reshape(count,A)
        assert h1.max()<=1 and h100.max()<=100
        sec=raw(b/'seconds.f64','<f8').reshape(count,A,2,3); assert np.isfinite(sec).all() and (sec>0).all()
        rec.append(np.stack([h1,h100/100.],axis=2)); tim.append(sec.mean(3))
    recall=np.concatenate(rec); seconds=np.concatenate(tim); dr=recall-recall[:,:1,:]
    M=len(C['arms']); actions=np.zeros((n,M,2),dtype='i4'); values=np.zeros((n,M,2,3)); mse=np.zeros((n,M,2)); selected_prediction=np.zeros((n,M,2))
    fold_records=[]
    for f in range(4):
        fit=np.flatnonzero(folds!=f); out=np.flatnonzero(folds==f)
        assert len(np.intersect1d(fit,out))==0 and len(fit)==3072 and len(out)==1024
        xmean=q[fit].mean(0); x=q[fit]-xmean; g=x.T@x; lam,p=np.linalg.eigh(g)
        tref=seconds[fit,0].mean(0); dt=(seconds-seconds[:,:1,:])/tref; u=dr-C['cost_weight']*dt
        weights=np.empty((4,2,d,H)); biases=np.empty((4,2,H)); means=np.empty((2,H))
        for k,K in enumerate(C['K']):
            ymean=u[fit,1:,k].mean(0); y=u[fit,1:,k]-ymean; c=x.T@y; means[k]=ymean
            specs=[('Independent',None,None),('FunctionSmooth',gam,v),('PermutedFunction',pgam,pv),('CoefficientSmooth',gam,v)]
            for j,(name,eigs,vecs) in enumerate(specs):
                if name=='Independent':
                    w=p@((p.T@c)/(lam[:,None]+C['alpha']))
                    residual=g@w+C['alpha']*w-c
                else:
                    den=lam[:,None]+C['alpha']+C['coefficient_beta']*eigs[None,:] if name=='CoefficientSmooth' else lam[:,None]*(1+C['beta']*eigs[None,:])+C['alpha']
                    w=p@((p.T@c@vecs)/den)@vecs.T
                    glap=plap if name=='PermutedFunction' else lap
                    residual=g@w+C['alpha']*w+(C['coefficient_beta']*w@glap if name=='CoefficientSmooth' else C['beta']*g@w@glap)-c
                relative=float(np.linalg.norm(residual)/max(np.linalg.norm(c),1e-30)); assert relative<1e-10
                b=ymean-xmean@w; weights[j,k]=w; biases[j,k]=b
                m=C['arms'].index(name); pred=q[out]@w+b; chosen=choose(pred,ids); actions[out,m,k]=chosen
                selected_prediction[out,m,k]=np.where(chosen>0,pred[np.arange(len(out)),np.maximum(chosen-1,0)],0)
                mse[out,m,k]=((pred-u[out,1:,k])**2).mean(1)
                trpred=q[fit]@w+b; tra=choose(trpred,ids)
                energy=float(np.sum((x@w@lap)*(x@w))/len(fit)/H)
                fold_records.append({'fold':f,'K':K,'method':name,'normal_equation_relative_residual':relative,'train_selected_u':float(u[fit,tra,k].mean()),'outer_selected_u':float(u[out,chosen,k].mean()),'train_mse':float(((trpred-u[fit,1:,k])**2).mean()),'outer_mse':float(mse[out,m,k].mean()),'train_prediction_graph_energy':energy,'time_reference_seconds':float(tref[k])})
            globalm=C['arms'].index('GlobalCost'); ga=choose(ymean[None,:],ids)[0]
            actions[out,globalm,k]=ga
            mse[out,globalm,k]=((ymean-u[out,1:,k])**2).mean(1)
            selected_prediction[out,globalm,k]=0 if ga==0 else ymean[ga-1]
            mse[out,0,k]=(u[out,1:,k]**2).mean(1)
        for m in range(M):
            for k in range(2):
                a=actions[out,m,k]
                for col,quantity in enumerate([dr,dt,u]): values[out,m,k,col]=quantity[out,a,k]
        np.savez(dest/f'fold_{f}.npz',weights=weights,biases=biases,xmean=xmean,ymean=means,time_reference=tref,fit_rows=rows[fit],outer_rows=rows[out])
        print(ds,'fold',f,'complete',flush=True)
    np.savez(dest/'oof.npz',actions=actions,values=values,mse=mse,selected_prediction=selected_prediction,folds=folds,rows=rows)
    equal_u=values[:,:,:,2].mean(2); all_u[ds]=equal_u; boot=bootstrap(equal_u,C['seed']+di*10000); all_boot[ds]=boot
    methods={}
    for m,name in enumerate(C['arms']):
        details={}
        for k,K in enumerate(C['K']):
            gain=values[:,m,k,0]; sel=actions[:,m,k]
            details[str(K)]={'recall_gain_pp':float(gain.mean()*100),'graph_time_change_pct':float(values[:,m,k,1].mean()*100),'u_mean':float(values[:,m,k,2].mean()),'positive_queries':int((gain>0).sum()),'negative_queries':int((gain<0).sum()),'positive_mass':float(gain[gain>0].sum()),'negative_mass':float(-gain[gain<0].sum()),'switches':int((sel>0).sum()),'response_mse':float(mse[:,m,k].mean()),'selected_prediction_mean':float(selected_prediction[:,m,k].mean())}
        methods[name]={'equal_K_u_mean':float(equal_u[:,m].mean()),'equal_K_u_interval':ci(boot[:,m]),'K':details}
    summaries[ds]={'methods':methods,'graph_spectrum_minmax':[float(gam.min()),float(gam.max())],'permuted_spectrum_max_error':float(np.max(np.abs(gam-pgam)))}
    dump(res/'fold_metrics.json',fold_records)
    print(ds,{name:round(met['equal_K_u_mean']*100,5) for name,met in methods.items()},flush=True)

candidate='FunctionSmooth'; m=C['arms'].index(candidate); checks={}; contrasts={}
for ds,s in summaries.items():
    met=s['methods'][candidate]
    checks[ds+'.positive_u']=met['equal_K_u_interval'][0]>0
    checks[ds+'.recall_floor']=all(v['recall_gain_pp']>=-C['max_k_recall_loss_pp'] for v in met['K'].values())
for control in ['Independent','PermutedFunction']:
    j=C['arms'].index(control); boot=sum((b[:,m]-b[:,j])/len(all_boot) for b in all_boot.values())
    means={ds:float((u[:,m]-u[:,j]).mean()) for ds,u in all_u.items()}; bounds=ci(boot)
    checks['beats_'+control]=all(v>0 for v in means.values()) and bounds[0]>0
    contrasts[control]={'dataset_mean_differences':means,'equal_dataset_interval':bounds}
passed=all(checks.values())
dump(R/'results/information.json',{'datasets':summaries,'contrasts':contrasts,'checks':checks,'interval_coverage':C['interval_coverage'],'scope':'Development only; not fresh holdout or full QPS.'})
dump(R/'results/gate.json',{'status':'PASS_INFORMATION_ONLY' if passed else 'STOP_ACTION_COUPLED_RIDGE_V1','checks':checks,'eligible':candidate,'default_changed':False})
dump(R/'reviews/response_inputs.json',inputs)
for path,identity in inputs.items(): assert ident(path)==identity,path
dump(R/'reviews/fit_complete.json',{'status':'PASS','wall_seconds':time.perf_counter()-started,'ridge_heads':64,'global_mean_heads':16,'new_ann':0,'new_nsg':0,'new_gt':0,'new_search_graphs':0,'protected_input_files':len(inputs),'protected_input_identity_pass':True,'independent_review_pending':True})
print('GATE',passed,flush=True)
