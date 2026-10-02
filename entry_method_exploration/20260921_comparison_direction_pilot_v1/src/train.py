"""Multi-output ridge; per-query CV; no acceptance-dependent choices."""
from common import *
from cluster import feature_specs

METHODS={'GraphCost':('graph',.1,False),'GraphRecall':('graph',0.,False),
         'RandomCost':('random',.1,False),'GraphLinearCost':('linear',.1,False),
         'RawLinearCost':('raw',.1,False),'ShuffledCost':('graph',.1,True)}

def standardize(x):
    mean=x.mean(axis=0);scale=x.std(axis=0);scale=np.where(scale>1e-12,scale,1.)
    return (x-mean)/scale,mean,scale

class Ridge:
    def __init__(self,x,y):
        self.z,self.mean,self.scale=standardize(x);self.intercept=y.mean(axis=0);self.n=len(x)
        self.gram=self.z.T@self.z/self.n;self.rhs=self.z.T@(y-self.intercept)/self.n
        self.eig,self.V=np.linalg.eigh(self.gram)
    def solve(self,alpha):
        coef=self.V@((self.V.T@self.rhs)/(np.maximum(self.eig,0)+alpha)[:,None])
        residual=np.linalg.norm((self.gram+alpha*np.eye(len(self.gram)))@coef-self.rhs)/max(np.linalg.norm(self.rhs),1e-30)
        assert residual<2e-9,(alpha,residual)
        w=coef/self.scale[:,None];bias=self.intercept-self.mean@w
        return w,bias,float(residual)

def actions(scores,hubids):
    # Default wins exact zero; equal positive scores use the lower real base ID.
    order=np.argsort(hubids,kind='stable');local=scores[:,order].argmax(axis=1);h=order[local]
    return np.where(scores[np.arange(len(scores)),h]>0,h+1,0)

def targets(labels,train):
    times=labels['time'].mean(axis=3);tref=times[train,0,:].mean(axis=0)
    r=np.stack([labels['r1'],labels['r100']],axis=2)
    dr=r[:,1:]-r[:,:1];dt=(times[:,1:]-times[:,:1])/tref
    assert np.isfinite(dr).all() and np.isfinite(dt).all() and (tref>0).all()
    # Column layout is [R1,R100,T1,T100], each block has H columns.
    y=np.concatenate([dr[:,:,0],dr[:,:,1],dt[:,:,0],dt[:,:,1]],axis=1)
    return y,dr,dt,tref

def utility(dr,dt,cost):return dr-cost*dt

def selected_value(u,a):
    result=np.zeros(len(a));take=a>0;result[take]=u[np.flatnonzero(take),a[take]-1];return result

def train_dataset(ds):
    start=time.time();labels=load_labels(ds);n,A=labels['r1'].shape;H=A-1;c=LOCK['datasets'][ds]
    hubs=np.fromfile(c['anchor']['ids'],np.int32);assert len(hubs)==H
    p=RUN/'models'/ds;features={s['name']:s for s in feature_specs(ds)}
    X={name:np.fromfile(RUN/'results'/ds/'fit_features'/f'{name}.features.f32',np.float32).reshape(n,-1).astype(np.float64) for name in features}
    rng=np.random.default_rng(LOCK['seed']);folds=np.empty(n,np.int32);folds[rng.permutation(n)]=np.arange(n)%LOCK['cv_folds']
    folds.tofile(p/'cv_folds.i32');allidx=np.arange(n);cv={};exports=[];report={}
    for name,(rep,cost,shuffle) in METHODS.items():
        trials={str(a):dict(gains=[],r_gains=[],time_gains=[],response_mse=[],response_mse_by_head=[],intercept_mse_by_head=[],switches=0) for a in LOCK['ridge_alphas']}
        for fold in range(LOCK['cv_folds']):
            tr=allidx[folds!=fold];va=allidx[folds==fold];y,dr,dt,tref=targets(labels,tr)
            # Permute only fold-training rows: a held-out response never becomes a training target.
            ytrain=y[tr]
            if shuffle:ytrain=ytrain[np.random.default_rng(LOCK['seed']+fold+901).permutation(len(tr))]
            fit=Ridge(X[rep][tr],ytrain)
            for alpha in LOCK['ridge_alphas']:
                w,b,resid=fit.solve(alpha);pred=X[rep][va]@w+b;t=trials[str(alpha)]
                t['response_mse'].append(float(np.mean((pred-y[va])**2)))
                t['response_mse_by_head'].append([float(np.mean((pred[:,j*H:(j+1)*H]-y[va,j*H:(j+1)*H])**2)) for j in range(4)])
                t['intercept_mse_by_head'].append([float(np.mean((fit.intercept[j*H:(j+1)*H]-y[va,j*H:(j+1)*H])**2)) for j in range(4)])
                for ki in range(2):
                    scores=pred[:,ki*H:(ki+1)*H]-cost*pred[:,(2+ki)*H:(3+ki)*H]
                    act=actions(scores,hubs);actual=selected_value(utility(dr[va,:,ki],dt[va,:,ki],cost),act)
                    t['gains'].append(float(actual.mean()));t['r_gains'].append(float(selected_value(dr[va,:,ki],act).mean()))
                    t['time_gains'].append(float(selected_value(dt[va,:,ki],act).mean()));t['switches']+=int((act>0).sum())
        for t in trials.values():t['mean_utility']=float(np.mean(t['gains']))
        chosen=max(LOCK['ridge_alphas'],key=lambda a:(trials[str(a)]['mean_utility'],a))
        y,dr,dt,tref=targets(labels,allidx);ytrain=y
        if shuffle:ytrain=y[np.random.default_rng(LOCK['seed']+901).permutation(n)]
        fit=Ridge(X[rep],ytrain);w,b,resid=fit.solve(chosen);pred=X[rep]@w+b
        mp=p/name;mp.mkdir();heads={};train_stats={}
        for ki,K in enumerate((1,100)):
            wr=w[:,ki*H:(ki+1)*H];br=b[ki*H:(ki+1)*H]
            wt=w[:,(2+ki)*H:(3+ki)*H];bt=b[(2+ki)*H:(3+ki)*H]
            wc=(wr-cost*wt).T.astype(np.float32);bc=(br-cost*bt).astype(np.float32)
            wc.tofile(mp/f'K{K}.weights.f32');bc.tofile(mp/f'K{K}.bias.f32')
            wr.T.astype(np.float32).tofile(mp/f'K{K}.recall_weights.f32');br.astype(np.float32).tofile(mp/f'K{K}.recall_bias.f32')
            wt.T.astype(np.float32).tofile(mp/f'K{K}.time_weights.f32');bt.astype(np.float32).tofile(mp/f'K{K}.time_bias.f32')
            scores=X[rep]@wc.astype(np.float64).T+bc.astype(np.float64);act=actions(scores,hubs);act.astype(np.int32).tofile(mp/f'K{K}.python_actions.i32')
            actual=utility(dr[:,:,ki],dt[:,:,ki],cost)
            train_stats[str(K)]=dict(fallback_fraction=float(np.mean(act==0)),utility=float(selected_value(actual,act).mean()),
                                    oracle_utility=float(np.maximum(actual.max(axis=1),0).mean()),
                                    recall_gain=float(selected_value(dr[:,:,ki],act).mean()),normalized_time_gain=float(selected_value(dt[:,:,ki],act).mean()),
                                    utility_mse=float(np.mean((scores-actual)**2)))
            heads[str(K)]=dict(weights=str(mp/f'K{K}.weights.f32'),bias=str(mp/f'K{K}.bias.f32'))
        model=dict(name=name,features=features[rep],heads=heads,H=H,dimension=c['dimension'],cost_weight=cost,
                   alpha=chosen,tref_seconds=tref.tolist(),feature_standardization=dict(mean=fit.mean.tolist(),scale=fit.scale.tolist()),
                   fallback='max predicted gain <= 0',tie='default at zero; lower real ID for equal positive gain')
        dump(mp/'model.json',model);exports.append(dict(name=name,type='learned',model=str(mp/'model.json')))
        report[name]=dict(alpha=chosen,cv=trials,normal_equation_relative_residual=resid,training=train_stats,
                          shuffled=shuffle,training_response_mse=float(np.mean((pred-y)**2)),
                          training_mse_by_head=[float(np.mean((pred[:,j*H:(j+1)*H]-y[:,j*H:(j+1)*H])**2)) for j in range(4)],
                          training_intercept_mse_by_head=[float(np.mean((fit.intercept[j*H:(j+1)*H]-y[:,j*H:(j+1)*H])**2)) for j in range(4)])
        print('TRAINED',ds,name,'alpha',chosen,'CV',trials[str(chosen)]['mean_utility'],flush=True)
    _,dr,dt,tref=targets(labels,allidx);fixed={}
    for ki,K in enumerate((1,100)):
        gain=utility(dr[:,:,ki],dt[:,:,ki],LOCK['cost_weight']).mean(axis=0)
        fixed[str(K)]=int(actions(gain[None,:],hubs)[0])-1
    methods=[dict(name='GT10',type='gt10'),dict(name='Single1',type='single1'),dict(name='BestFixed',type='fixed',fixed=fixed),dict(name='NSG',type='nsg')]
    methods+=exports+[dict(name='FeatureDefault',type='feature_default',model=str(p/'GraphCost/model.json'))]
    dump(p/'methods.json',methods)
    dump(p/'training_report.json',dict(status='PASS',dataset=ds,n=n,H=H,methods=report,best_fixed=fixed,tref=tref.tolist(),seconds=time.time()-start,
                                     cv_target_permutation='within each training fold; final permutation within full fit',acceptance_access=False))
    return methods

if __name__=='__main__':
    os.sched_setaffinity(0,{15})
    for ds in LOCK['datasets']:train_dataset(ds)
