from model_io import *
from sklearn.tree import DecisionTreeRegressor
ds=sys.argv[1];begin=time.perf_counter();allrows=[]
for K,L in STATES:
    root=R/'storage/gate_labels'/ds/f'k{K}';f=np.fromfile(root/'features.f32','<f4').reshape(3072,62);t=np.fromfile(root/'targets.i32','<i4').reshape(3072,4)
    # Labels are separately checked from the actual saved returned IDs and original GT.
    cfg=read(R/'configs'/f'{ds}.k1.labels.json');G=np.fromfile(cfg['test_gt']['path'],'<i4').reshape(3072,100)[:,:K]
    for col,name in [(0,'main'),(1,'direct'),(2,'final')]:
        ids=np.fromfile(root/f'{name}.i32','<i4').reshape(3072,K);h=np.array([len(set(a)&set(g)) for a,g in zip(ids,G)])
        assert np.array_equal(h,t[:,col])
    targets={'F':t[:,2]-t[:,0],'N':t[:,2]-t[:,1]};out=dict(K=K,L=L,static_full=bool(np.maximum(targets['F'][2560:],0).sum()),static_nav=bool(np.maximum(targets['N'][2560:],0).sum()),gates={})
    for family,variants in [('F',['PRE','POST']),('N',['PRE','POST','CPOST'])]:
      for variant in variants:
        X=f[:,slice(0,22) if variant=='PRE' else slice(22,50) if variant=='POST' else slice(50,62)];y=np.maximum(targets[family],0)
        dt=DecisionTreeRegressor(max_depth=3,min_samples_leaf=32,random_state=199).fit(X[2048:2560],y[2048:2560]);exp=single_tree_export(dt);exp['feature_count']=X.shape[1];pred=dt.predict(X)
        got=predict_tree(exp,X);assert np.max(np.abs(pred-got))<1e-12
        thresholds=sorted(set([0.]+[float(np.quantile(pred[2048:2560],q)) for q in [0,.25,.5,.75,.9,1]]));total=int(y[2560:].sum());off=total==0;screen=[];chosen={}
        for threshold in thresholds:
            use=pred[2560:]>=threshold;screen.append(dict(threshold=threshold,enabled=int(use.sum()),positive_kept=int(y[2560:][use].sum()),positive_reference=total))
        for target in [75,90]:
            feasible=[a for a in screen if a['positive_kept']>=total*target/100];pick=min(feasible,key=lambda a:(a['enabled'],-a['positive_kept'],a['threshold']));chosen[target]=pick['threshold']
            allrows.append(dict(dataset=ds,K=K,family=family,gate=variant,target=target,gate_all_off=off,threshold=chosen[target],cal_enabled=0 if off else pick['enabled'],cal_positive_kept=0 if off else pick['positive_kept'],cal_positive_reference=total))
        exp['gate_all_off']=off;out['gates'][family+'_'+variant]=dict(model=exp,threshold75=chosen[75],threshold90=chosen[90],calibration=screen,features=X.shape[1])
    dest=R/'storage/gates'/ds/f'k{K}.json';dump(dest,out)
csvwrite(R/'analysis'/f'{ds}.gate_calibration.csv',allrows)
dump(R/'reviews'/f'{ds}.gate_training.json',dict(status='PASS_FIT512_CAL512_FIXED_GATES',seconds=time.perf_counter()-begin,source='actual native matched CASCADE384 vs main/direct',states=[1,100]))
print('GATES_TRAINED',ds,time.perf_counter()-begin,flush=True)
