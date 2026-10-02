from pathlib import Path
import json,csv,time,hashlib,shutil,resource
import numpy as np
ROOT=Path('/data/netg/ACSG');TB=Path(__file__).resolve().parents[1];R=TB/'stages/e115_score_topology_factorial'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ident(p):
 p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def write_csv(p,rows):
 with Path(p).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
C=read(R/'config.locked.json');assert read(R/'reviews/diagnostic_complete.json')['status']=='PASS';assert not (R/'reviews/analysis_complete.json').exists()
start=time.time();shutil.copy2(__file__,R/'src/analyze.py');dump(R/'reviews/analysis_started.json',dict(started_unix=start,source=ident(__file__),copied_source=ident(R/'src/analyze.py'),config=ident(R/'config.locked.json'),selection_rule_unchanged=True))
metrics=[];factors=[];pairs=[];routes=[];gate=[];inputs=[];checks=dict(unique_output_rows=0,primary_prefix_rows=0,same_entry_pair_rows=0,integer_decomposition_rows=0)
names=['A_P_GP','B_U_GP','C_P_GU','D_U_GU'];contrast=np.array([[-1,1,0,0],[-1,0,1,0],[1,-1,-1,1],[0,0,-1,1],[0,-1,0,1],[-1,0,0,1]],np.int64)
cnames=['score_at_GP','graph_at_P','interaction','score_at_GU','graph_at_U','total_D_minus_A']
for ds in C['datasets']:
 n=4096;source=R/'results'/('main_'+ds['dataset']);assert read(source/'complete.json')['status']=='PASS';gt=np.fromfile(ds['GT'],np.int32).reshape(n,100);inputs.append(ident(ds['GT']))
 qoffset=np.arange(n,dtype=np.int64)[:,None]*ds['base_n'];packed_gt=(gt.astype(np.int64)+qoffset).ravel();batches={};point_values={};local_metrics=[];local_factors=[];local_pairs=[]
 for p in ds['points']:
  K,L=p['K'],p['L'];hits=[];gn=[];rn=[]
  for name in names:
   base=source/('k'+str(K))/(name+'_L'+str(L));batch={}
   for key,file,dtype,shape in [('ids','ids.i32',np.int32,(n,K)),('dist','distances.f32',np.float32,(n,K)),('entries','entry_ids.i32',np.int32,(n,3)),('graph','graph_ndc.u64',np.uint64,(n,)),('route','route_ndc.u64',np.uint64,(n,))]:
    batch[key]=np.fromfile(base/file,dtype).reshape(shape);inputs.append(ident(base/file))
   assert np.all(np.diff(np.sort(batch['ids'],axis=1),axis=1)>0) and np.all((batch['ids']>=0)&(batch['ids']<ds['base_n'])) and np.all(np.isfinite(batch['dist']));checks['unique_output_rows']+=n
   hit=(batch['ids'][:,0]==gt[:,0]).astype(np.int64) if K==1 else np.isin((batch['ids'].astype(np.int64)+qoffset).ravel(),packed_gt,assume_unique=True,kind='sort').reshape(n,K).sum(axis=1,dtype=np.int64)
   # Independent Python set scoring of the complete deterministic every-256th sample.
   for i in range(0,n,256):assert int(hit[i])==len(set(map(int,batch['ids'][i]))&set(map(int,gt[i,:K])))
   batch['hit']=hit;batches[K,L,name]=batch;hits.append(hit);gn.append(batch['graph'].astype(np.int64));rn.append(batch['route'].astype(np.int64))
   row=dict(dataset=ds['dataset'],K=K,L=L,method=name,n=n,recall=float(hit.mean()/K),failed=int((hit==0).sum()),mean_graph_ndc=float(batch['graph'].mean()),mean_route_ndc=float(batch['route'].mean()),formal_QPS=False);metrics.append(row);local_metrics.append(row)
  H=np.column_stack(hits);G=np.column_stack(gn);N=np.column_stack(rn);F=H@contrast.T;FG=G@contrast.T;FN=N@contrast.T
  assert np.array_equal(F[:,0]+F[:,1]+F[:,2],F[:,5]);assert np.array_equal(FG[:,0]+FG[:,1]+FG[:,2],FG[:,5]);assert np.array_equal(FN[:,0]+FN[:,1]+FN[:,2],FN[:,5]);checks['integer_decomposition_rows']+=n
  point_values[K,L]=F.astype(np.float64)/K
  for j,name in enumerate(cnames):
   row=dict(dataset=ds['dataset'],K=K,L=L,contrast=name,delta_recall_pp=float(F[:,j].mean()/K*100),gain_queries=int((F[:,j]>0).sum()),harm_queries=int((F[:,j]<0).sum()),zero_queries=int((F[:,j]==0).sum()),delta_graph_ndc=float(FG[:,j].mean()),delta_route_ndc=float(FN[:,j].mean()),CI98_75_low_pp=None,CI98_75_high_pp=None);factors.append(row);local_factors.append(row)
  a,b=batches[K,L,names[0]],batches[K,L,names[1]]
  row=dict(dataset=ds['dataset'],K=K,L=L,baseline_recall=float(a['hit'].mean()/K),candidate_recall=float(b['hit'].mean()/K),delta_recall_pp=float((b['hit']-a['hit']).mean()/K*100),baseline_failed=int((a['hit']==0).sum()),candidate_failed=int((b['hit']==0).sum()),rescued_zero=int(((a['hit']==0)&(b['hit']>0)).sum()),newly_zero=int(((a['hit']>0)&(b['hit']==0)).sum()),same_entries=int(np.all(a['entries']==b['entries'],axis=1).sum()),CI98_75_low_pp=None,CI98_75_high_pp=None);pairs.append(row);local_pairs.append(row)
  for i in range(4):
   for j in range(i+1,4):
    a,b=batches[K,L,names[i]],batches[K,L,names[j]];mask=np.all(a['entries']==b['entries'],axis=1);assert np.array_equal(a['ids'][mask],b['ids'][mask]) and np.array_equal(a['dist'][mask].view(np.uint32),b['dist'][mask].view(np.uint32)) and np.array_equal(a['graph'][mask],b['graph'][mask]);checks['same_entry_pair_rows']+=int(mask.sum())
 for L in [128,256,400,800]:
  for name in names:
   a,b=batches[1,L,name],batches[100,L,name];assert np.array_equal(a['ids'][:,0],b['ids'][:,0]) and np.array_equal(a['dist'][:,0].view(np.uint32),b['dist'][:,0].view(np.uint32)) and np.array_equal(a['graph'],b['graph']);checks['primary_prefix_rows']+=n
 for name in names:
  b=batches[1,128,name];ref=batches[1,128,names[0]]
  for p in ds['points']:assert np.array_equal(b['entries'],batches[p['K'],p['L'],name]['entries']) and np.array_equal(b['route'],batches[p['K'],p['L'],name]['route'])
  routes.append(dict(dataset=ds['dataset'],method=name,mean_route_ndc=float(b['route'].mean()),same_entries_as_A=int(np.all(b['entries']==ref['entries'],axis=1).sum()),same_first_result_as_A=int((b['ids'][:,0]==ref['ids'][:,0]).sum())))
 # Same paired query resamples for both K, with all six frozen factorial contrasts.
 values=np.concatenate([point_values[K,128] for K in [1,100]],axis=1);rng=np.random.default_rng(C['bootstrap_seed']);B=C['bootstrap_replicates'];boot=np.empty((B,12),np.float64)
 for first in range(0,B,64):
  z=min(64,B-first);idx=rng.integers(0,n,size=(z,n));boot[first:first+z]=values[idx].mean(axis=1)
 lower,upper=np.quantile(boot,[(1-C['individual_CI'])/2,1-(1-C['individual_CI'])/2],axis=0)
 for K in [1,100]:
  offset=0 if K==1 else 6
  for j,name in enumerate(cnames):
   row=next(x for x in local_factors if x['K']==K and x['L']==128 and x['contrast']==name);row['CI98_75_low_pp']=float(lower[offset+j]*100);row['CI98_75_high_pp']=float(upper[offset+j]*100)
  row=next(x for x in local_pairs if x['K']==K and x['L']==128);row['CI98_75_low_pp']=float(lower[offset]*100);row['CI98_75_high_pp']=float(upper[offset]*100)
 primary=[x for x in local_pairs if x['L']==128];mean_by_K={str(K):float(np.mean([x['delta_recall_pp'] for x in local_pairs if x['K']==K])) for K in [1,100]}
 tests=dict(primary_both_nonnegative=all(x['delta_recall_pp']>=0 for x in primary),some_gain_at_least_point5pp=any(x['delta_recall_pp']>=C['minimum_gain_pp'] for x in primary),some_corrected_lower_positive=any(x['CI98_75_low_pp']>0 for x in primary),both_K_mean_across_L_nonnegative=all(v>=0 for v in mean_by_K.values()))
 gate.append(dict(dataset=ds['dataset'],primary=primary,mean_by_K_delta_pp=mean_by_K,tests=tests,pass_quality_gate=all(tests.values())))
for name,rows in [('metrics',metrics),('factors',factors),('paired',pairs),('routing',routes)]:write_csv(R/'results'/(name+'.csv'),rows)
decision='PASS_EXPOSED_DEVELOPMENT_QUALITY_GATE' if all(x['pass_quality_gate'] for x in gate) else 'STOP_CROSS_SCORE_TOPOLOGY_CANDIDATE'
dump(R/'results/gate.json',dict(decision=decision,candidate=C['candidate'],datasets=gate,formal_QPS=False,default_changed=False,multiple_interval_scope='Four B-versus-A primary intervals are the prelocked gate; other factorial CIs are descriptive, not a simultaneous global claim.'))
dump(R/'reviews/analysis_complete.json',dict(status='PASS',seconds=time.time()-start,source_files=list({x['path']:x for x in inputs}.values()),outputs=[ident(R/'results'/(name+'.csv')) for name in ['metrics','factors','paired','routing']]+[ident(R/'results/gate.json')],checks=checks,maxrss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,new_NSG=0,new_ANN=0,new_GT=0,new_training=0,decision=decision))
dump(R/'state.json',dict(status='ANALYSIS_COMPLETE',decision=decision,pending=['interpretation','figure','conditional wall only if gate passes','report and closeout']))
print(json.dumps(dict(decision=decision,gate=gate,routing=routes,checks=checks,seconds=time.time()-start),ensure_ascii=False,indent=2))
