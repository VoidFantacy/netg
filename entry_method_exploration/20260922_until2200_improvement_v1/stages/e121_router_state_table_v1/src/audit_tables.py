"""Independent table reconstruction, OOF arithmetic and input protection."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
c=read(R/'config.locked.json');old=Path(c['historical_label_root']);report=read(R/'results/information.json');start=time.perf_counter()
def scalar_choice(means,hubs):
 best=0;value=0.
 for a in sorted(range(1,len(hubs)+1),key=lambda a:int(hubs[a-1])):
  if float(means[a])>value:best=a;value=float(means[a])
 return best
checked=0;table_count=0;method_evaluations=0;diagnostics={}
for ds,dc in c['datasets'].items():
 labs=old/'results'/ds/'labels';blocks=read(labs/'complete.json')['blocks'];hubs=np.fromfile(dc['anchor']['ids'],'<i4');A=len(hubs)+1
 hit=[];tt=[]
 for b in sorted(blocks,key=lambda x:x['start']):
  p=labs/f"block_{b['start']}";n=b['n']
  a=np.fromfile(p/'hits1.u8','u1').reshape(n,A).astype('f8');b100=np.fromfile(p/'hits100.u8','u1').reshape(n,A).astype('f8')/100
  hit.append(np.stack([a,b100],axis=2));t=np.fromfile(p/'seconds.f64','<f8').reshape(n,A,2,3);tt.append((t[:,:,:,0]+t[:,:,:,1]+t[:,:,:,2])/3)
 hits=np.concatenate(hit);times=np.concatenate(tt);roles=np.load(R/'models'/ds/'roles.npz');saved=np.load(R/'models'/ds/'oof.npz');z=saved['states'];folds=roles['folds'];tables=read(R/'models'/ds/'tables.json');lookup={(t['fold'],t['method'],t['K']):t['table'] for t in tables}
 fold_metrics=read(R/'results'/ds/'fold_metrics.json');diagnostics[ds]={'training_vs_outer':{},'state_occupancy_nonempty':list(map(int,np.bincount(z)[np.bincount(z)>0])),'chosen_action_agreement':{}}
 for f in range(4):
  train=np.flatnonzero(folds!=f);test=np.flatnonzero(folds==f);scale=times[train,0].sum(0)/len(train)
  for k,K in enumerate(c['K']):
   delta=hits[:,:,k]-hits[:,0,k,None];dt=(times[:,:,k]-times[:,0,k,None])/scale[k];u=delta-.1*dt
   for m,name in enumerate(c['arms']):
    method_evaluations+=1;tab=lookup[f,name,K];obj=u if name.endswith('Cost') else delta
    ztr=z[roles['train_shuffle'][f]] if name.startswith('Shuffle') else z[train]
    zte=z[roles['outer_shuffle'][f]] if name.startswith('Shuffle') else z[test]
    if name.startswith('Global'):
     a=scalar_choice(obj[train].sum(0)/len(train),hubs);assert tab=={'global':a};table_count+=1
    elif name.startswith(('State','Shuffle')):
     for key,expected in tab.items():
      support=[int(train[j]) for j,v in enumerate(ztr) if v==int(key)]
      candidate=scalar_choice(obj[support].sum(0)/len(support),hubs);assert candidate==expected,(ds,f,name,K,key,candidate,expected)
     table_count+=1
    for j,i in enumerate(test):
     a=0 if name=='Default' else int(tab['global'] if name.startswith('Global') else tab.get(str(int(zte[j])),0))
     assert saved['actions'][i,m,k]==a
     expected=np.array([delta[i,a],dt[i,a],u[i,a]])
     assert np.max(np.abs(saved['values'][i,m,k]-expected))<1e-10
     checked+=1
 for m in ['StateCost','StateRecall']:
  rows=[x for x in fold_metrics if x['method']==m]
  diagnostics[ds]['training_vs_outer'][m]={key:float(np.mean([x[key] for x in rows])) for key in ['training_u_mean','outer_u_mean','training_recall_gain_pp','outer_recall_gain_pp']}
  ag=[]
  for K in c['K']:
   stable=0;total=0
   for s in np.unique(z):
    acts=[lookup[f,m,K].get(str(int(s)),0) for f in range(4)]
    stable+=len(set(acts))==1;total+=1
   ag.append({'K':K,'states_with_identical_action_all_folds':stable,'observed_states':total})
  diagnostics[ds]['chosen_action_agreement'][m]=ag
 for m,name in enumerate(c['arms']):
  means=saved['values'][:,m,:,2].mean(1).mean();assert abs(means-report['datasets'][ds]['methods'][name]['equal_K_u_mean'])<1e-12
  for k,K in enumerate(c['K']):
   gain=saved['values'][:,m,k,0];s=report['datasets'][ds]['methods'][name]['K'][str(K)]
   assert abs(gain.mean()*100-s['recall_gain_pp'])<1e-12
   assert int((gain>0).sum())==s['positive_queries'] and int((gain<0).sum())==s['negative_queries']

preserved={}
for name in ['router_inputs_before.json','response_inputs.json']:
 for p,ident in read(R/'reviews'/name).items():
  assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==ident['sha256'],p
  preserved[p]=ident
for name,ident in read(R/'reviews/fit_frozen.json')['files'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==ident['sha256'],name
# The decisive main-gate failure is reproduced from actual selected responses,
# without relying on the saved gate booleans or on a particular bootstrap draw.
for candidate in c['eligible']:
 assert all(report['datasets'][ds]['methods'][candidate]['equal_K_u_mean']<0 for ds in c['datasets'])
assert read(R/'results/gate.json')['status']=='STOP_ROUTER_STATE_TABLE_V1'
out={'status':'PASS','actions_and_query_K_values_checked':checked,'nondefault_table_or_global_fits':table_count,'method_fold_K_evaluations':method_evaluations,'preserved_files':len(preserved),'seconds':time.perf_counter()-start,'scope':'Same-session independent implementation, not an independent person or agent','accounting_clarification':'fit_complete.table_fits includes 16 default no-fit evaluations; actual learned tables/global means=96, total method-fold-K evaluations=112','new_searches':0,'diagnostics':diagnostics}
assert not (R/'reviews/independent_numeric_audit.json').exists();(R/'reviews/independent_numeric_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='diagnostics'},indent=2))
