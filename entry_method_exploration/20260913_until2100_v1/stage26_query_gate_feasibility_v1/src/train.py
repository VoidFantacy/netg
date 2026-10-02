from common import *
runtime();assert not (O/'reviews/pretraining_freeze.json').exists();paths=list((O/'src').glob('*.py'))+list((O/'source_before').glob('*'))+[O/'protocol.md'];configs={}
for ds in DS:
 cp=E73/'inputs'/ds/'aux.json';c=read(cp);configs[ds]=c;paths+=[cp]+[Path(c[k]) for k in ['queries_file','row_ids','gt_file']]
 for name in ['baseline10','compact10']:
  paths+=list((E73/'results'/ds/'aux'/(name+'_L128')).glob('*'))
freeze(O/'reviews/pretraining_freeze.json',[p for p in paths if p.is_file()]);t=time.monotonic();models=[]
for ds,c in configs.items():
 folder=O/'models'/ds;folder.mkdir();d=c['dim'];q=np.fromfile(c['queries_file'],np.float32,count=N*d).reshape(N,d);x=features(q);rows=np.fromfile(c['row_ids'],np.int64,count=N);assert np.array_equal(rows,np.arange(2048,6024));hp=np.fromfile(E73/'results'/ds/'aux/baseline10_L128/hits.u8',np.uint8,count=N);hc=np.fromfile(E73/'results'/ds/'aux/compact10_L128/hits.u8',np.uint8,count=N);y=hc.astype(float)-hp.astype(float);perm=np.random.default_rng(20260913).permutation(N);mu=x.mean(0);xc=x-mu;H=xc.T@xc+(N/d)*np.eye(d)
 for kind,target in [('query_gate',y),('shuffle_gate',y[perm])]:
  ts=time.monotonic();ym=float(target.mean());rhs=xc.T@(target-ym);beta=np.linalg.solve(H,rhs);bias=float(ym-mu@beta);res=float(np.max(np.abs(H@beta-rhs)));assert res<1e-9
  np.savez_compressed(folder/(kind+'.npz'),beta=beta,bias=bias,mean=mu,source_rows=rows,target=target,permutation=perm if kind=='shuffle_gate' else np.arange(N),training_labels=y)
  rec=dict(dataset=ds,kind=kind,n=N,d=d,penalty=1/d,normal_equation_residual=res,fit_seconds=time.monotonic()-ts,positive_queries=int((y>0).sum()),negative_queries=int((y<0).sum()),zero_queries=int((y==0).sum()),fit_positive_hits=int(np.maximum(y,0).sum()),fit_negative_hits=int(np.maximum(-y,0).sum()),model=identity(folder/(kind+'.npz')));models.append(rec)
dump(O/'results/training.json',dict(status='PASS',models=models,fits=4,seconds=time.monotonic()-t));freeze(O/'reviews/before_accept_freeze.json',[Path(x['model']['path']) for x in models]+[O/'results/training.json',O/'reviews/pretraining_freeze.json']);dump(O/'state.json',dict(status='MODELS_FROZEN_BEFORE_ACCEPT',NSG=0,HNSW=0,builds=0,fits=4,day_goal_complete=False));print('E85_TRAINED',models)
