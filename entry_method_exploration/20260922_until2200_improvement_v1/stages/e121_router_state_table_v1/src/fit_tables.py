"""Frozen four-fold state-conditional means and controls; no search calls."""
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
import datetime,hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
def dump(p,v):
 assert not p.exists(),p
 p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def ident(p):return {'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
C=read(R/'config.locked.json');OLD=Path(C['historical_label_root']);N=C['n'];names=C['arms'];inputs={}
def raw(p,dtype):
 p=Path(p);inputs[str(p)]=ident(p);return np.fromfile(p,dtype)
def act(mean,hubs):
 order=np.r_[0,1+np.argsort(hubs,kind='stable')]
 return int(order[np.argmax(mean[order])])
def stats(x):return {'mean':float(x.mean()),'min':float(x.min()),'max':float(x.max())}
def bootstrap(x,seed):
 rng=np.random.default_rng(seed);out=[]
 for start in range(0,C['bootstrap_reps'],128):
  size=min(128,C['bootstrap_reps']-start);idx=rng.integers(0,len(x),size=(size,len(x)))
  out.append(x[idx].mean(1))
 return np.concatenate(out)
alpha=(1-C['interval_coverage'])/2
def interval(x):return list(map(float,np.quantile(x,[alpha,1-alpha])))
assert read(R/'reviews/observer_complete.json')['status']=='PASS'
frozen={str(p.relative_to(R)):ident(p) for p in [R/'src/fit_tables.py',R/'config.locked.json',R/'protocol.md']+list((R/'models').rglob('roles.npz'))+list((R/'results').glob('*/upper_states.i32'))}
dump(R/'reviews/fit_frozen.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':frozen})
start=time.perf_counter();all_summary={};all_boot={};all_selected={};fold_records={}
for ds,dc in C['datasets'].items():
 d=dc['dimension'];p=OLD/'inputs'/ds/'fit';lab=OLD/'results'/ds/'labels';done=read(lab/'complete.json')
 gt=raw(p/'gt.i64','<i8').reshape(N,100);hubs=raw(dc['anchor']['ids'],'<i4');A=len(hubs)+1
 states=raw(R/'results'/ds/'upper_states.i32','<i4');entries=raw(R/'results'/ds/'entries.i32','<i4').reshape(N,3)
 roles=np.load(R/'models'/ds/'roles.npz');folds=roles['folds'];assert len(states)==N and np.bincount(folds).tolist()==[1024]*4
 rec=[];tim=[];checks=0
 for block in sorted(done['blocks'],key=lambda b:b['start']):
  b=lab/f"block_{block['start']}";n=block['n'];lo=block['start'];assert block['A']==A
  h1=raw(b/'hits1.u8','u1').reshape(n,A);h100=raw(b/'hits100.u8','u1').reshape(n,A)
  top=raw(b/'top1_ids.i32','<i4').reshape(n,A);masks=raw(b/'masks.u64','<u8').reshape(n,A,2)
  assert np.array_equal(h1,top==gt[lo:lo+n,:1])
  pop=np.array([x.bit_count() for x in range(256)],dtype='u1');assert np.array_equal(pop[masks.view('u1')].sum(2),h100)
  tt=raw(b/'seconds.f64','<f8').reshape(n,A,2,3);assert np.isfinite(tt).all() and (tt>0).all()
  rec.append(np.stack([h1,h100/100.],-1));tim.append(tt.mean(-1));checks+=n*A
 recall=np.concatenate(rec);seconds=np.concatenate(tim);dr=recall-recall[:,:1,:]
 actions=np.zeros((N,len(names),2),dtype='<i4');values=np.zeros((N,len(names),2,3));train_records=[];table_records=[]
 for f in range(4):
  fit=np.where(folds!=f)[0];out=np.where(folds==f)[0];assert not set(fit)&set(out)
  trperm=roles['train_shuffle'][f];teperm=roles['outer_shuffle'][f]
  assert set(trperm)==set(fit) and set(teperm)==set(out)
  zfit=states[fit];zout=states[out];shuffle_fit=states[trperm];shuffle_out=states[teperm]
  assert np.array_equal(np.sort(zfit),np.sort(shuffle_fit)) and np.array_equal(np.sort(zout),np.sort(shuffle_out))
  tref=seconds[fit,0].mean(0);dt=(seconds-seconds[:,:1,:])/tref;utility=dr-C['cost_weight']*dt
  for m,name in enumerate(names):
   for k,K in enumerate(C['K']):
    objective=utility[:,:,k] if name.endswith('Cost') else dr[:,:,k]
    fit_actions=np.zeros(len(fit),dtype='i4');out_actions=np.zeros(len(out),dtype='i4');table={}
    if name.startswith('Global'):
     a=act(objective[fit].mean(0),hubs);fit_actions[:]=a;out_actions[:]=a;table={'global':a}
    elif name.startswith(('State','Shuffle')):
     ztr,zte=(shuffle_fit,shuffle_out) if name.startswith('Shuffle') else (zfit,zout)
     for z in np.unique(ztr):
      local=np.where(ztr==z)[0];a=act(objective[fit[local]].mean(0),hubs);table[str(int(z))]=a;fit_actions[local]=a;out_actions[zte==z]=a
    actions[out,m,k]=out_actions
    for j,quantity in enumerate([dr,dt,utility]):values[out,m,k,j]=quantity[out,out_actions,k]
    train_records.append({'fold':f,'method':name,'K':K,'training_u_mean':float(utility[fit,fit_actions,k].mean()),'outer_u_mean':float(utility[out,out_actions,k].mean()),'training_recall_gain_pp':float(dr[fit,fit_actions,k].mean()*100),'outer_recall_gain_pp':float(dr[out,out_actions,k].mean()*100),'switched_fraction':float((out_actions!=0).mean()),'time_reference_seconds':float(tref[k])})
    table_records.append({'fold':f,'method':name,'K':K,'table':table})
 summary={};u=values[:,:,:,2].mean(2);boot=bootstrap(u,C['seed']+(0 if ds.startswith('web') else 10000));all_boot[ds]=boot;all_selected[ds]=u
 for m,name in enumerate(names):
  summary[name]={'equal_K_u_mean':float(u[:,m].mean()),'equal_K_u_interval':interval(boot[:,m]),'K':{}}
  for k,K in enumerate(C['K']):
   g=values[:,m,k,0];t=values[:,m,k,1];a=actions[:,m,k];outside=np.zeros(N,dtype=bool);sw=a>0;outside[sw]=~(entries[sw]==hubs[a[sw]-1,None]).any(1)
   summary[name]['K'][str(K)]={'recall_gain_pp':float(g.mean()*100),'positive_queries':int((g>0).sum()),'negative_queries':int((g<0).sum()),'positive_mass':float(g[g>0].sum()),'negative_mass':float(-g[g<0].sum()),'graph_time_change_pct':float(t.mean()*100),'switched_queries':int(sw.sum()),'chosen_single_outside_actual_top3':int(outside.sum()),'u_mean':float(values[:,m,k,2].mean())}
 np.savez(R/'models'/ds/'oof.npz',actions=actions,values=values,states=states,folds=folds)
 dump(R/'models'/ds/'tables.json',table_records);dump(R/'results'/ds/'fold_metrics.json',train_records)
 all_summary[ds]={'label_checks':checks,'methods':summary,'state_count':int(len(np.unique(states))),'state_occupancy':np.bincount(states,minlength=len(hubs)).tolist()}
 print(ds,{name:round(v['equal_K_u_mean']*100,5) for name,v in summary.items()},flush=True)

candidate_gates={};datasets=list(C['datasets'])
for name in C['eligible']:
 m=names.index(name);kind='Cost' if name.endswith('Cost') else 'Recall';checks={};contrasts={}
 for ds in datasets:
  s=all_summary[ds]['methods'][name]
  checks[ds+'.positive_u']=s['equal_K_u_mean']>0 and s['equal_K_u_interval'][0]>0
  checks[ds+'.recall_floor']=all(v['recall_gain_pp']>=-C['max_k_recall_loss_pp'] for v in s['K'].values())
 for control in ['Global'+kind,'Shuffle'+kind]:
  j=names.index(control);bs=sum((all_boot[ds][:,m]-all_boot[ds][:,j])/len(datasets) for ds in datasets)
  means={ds:float((all_selected[ds][:,m]-all_selected[ds][:,j]).mean()) for ds in datasets};ci=interval(bs)
  checks['beats_'+control]=all(v>0 for v in means.values()) and ci[0]>0
  contrasts[control]={'dataset_mean_differences':means,'equal_dataset_interval':ci}
 candidate_gates[name]={'pass':all(checks.values()),'checks':checks,'contrasts':contrasts}
chosen=next((n for n in C['eligible'] if candidate_gates[n]['pass']),None)
dump(R/'results/information.json',{'datasets':all_summary,'candidates':candidate_gates,'selected':chosen,'interval_coverage':C['interval_coverage'],'scope':'Historical four-fold development only; graph-time utility is not full QPS.'})
dump(R/'results/gate.json',{'status':'PASS_INFORMATION_ONLY' if chosen else 'STOP_ROUTER_STATE_TABLE_V1','selected':chosen,'candidate_gates':candidate_gates,'default_changed':False,'new_searches':0})
dump(R/'reviews/response_inputs.json',inputs)
for name,v in inputs.items():assert ident(Path(name))==v,name
dump(R/'reviews/fit_complete.json',{'status':'PASS','seconds':time.perf_counter()-start,'table_fits':len(names)*4*2*len(datasets),'new_gradient_training':0,'new_nsg':0,'new_router_calls':0,'source_identities_pass':True,'independent_implementation_review_pending':True})
print('GATE',chosen or 'STOP_ROUTER_STATE_TABLE_V1',flush=True)
