from common import *
import csv
import sys
sys.path.insert(0,str(R/'entry_method_exploration/20260911_gt10_shared_transform_v1/src/vendor'))
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

assert read(O/'results/deployment_complete.json')['status']=='PASS'
selection=read(O/'results/cal_selection.json')['selection'];points=[];paired=[];timings=[];query_rows=[];frontiers=[];raw={};verification=[]
def bootstrap(delta):
 rng=np.random.default_rng(20260912);values=[]
 for _ in range(50):values.extend(delta[rng.integers(0,len(delta),size=(100,len(delta)))].mean(1))
 return np.percentile(values,[2.5,97.5]).tolist()
def load_point(folder,m,n):
 p=folder/m['name'];return dict(ids=np.fromfile(p/'ids.i32',np.int32).reshape(n,10),distances=np.fromfile(p/'distances.f32',np.float32).reshape(n,10),entries=np.fromfile(p/'entry_ids.i32',np.int32).reshape(n,3),route_ndc=np.fromfile(p/'route_ndc.u32',np.uint32),graph_ndc=np.fromfile(p/'graph_ndc.u32',np.uint32))
for ds in DS:
 for phase in ['fit_parity','cal','audit','frontier']:
  folder=O/'results'/f'{phase}_{ds}';c=read(folder/'config.json');result=read(folder/'results.json');n=c['num_queries'];gt=np.fromfile(c['gt_file'],np.int64).reshape(n,100);rows=np.fromfile(c['row_ids'],np.int64)
  assert np.array_equal(rows,np.fromfile(folder/'row_ids.i64',np.int64));assert result['threads']==1 and result['GT_opened_after_all_raw_search']
  for m in result['methods']:
   a=load_point(folder,m,n);hits=np.fromiter((len(set(map(int,x))&set(map(int,g[:10]))) for x,g in zip(a['ids'],gt)),dtype=np.uint8,count=n)
   mask=np.array([sum((1<<j) for j in range(10) if int(g[j]) in set(map(int,x))) for x,g in zip(a['ids'],gt)],np.uint16)
   assert np.array_equal(hits,np.fromfile(folder/m['name']/'hits.u8',np.uint8));assert np.array_equal(mask,np.fromfile(folder/m['name']/'hitmask.u16',np.uint16))
   assert abs(hits.mean()/10-m['recall_at_10'])<1e-12 and int((hits==0).sum())==m['failed_queries']
   assert np.isfinite(a['distances']).all() and ((a['ids']>=0)&(a['ids']<c['base_count'])).all()
   if m['family']!='nsg':assert all(len(set(map(int,x)))==3 for x in a['entries'])
   a['hits']=hits;a['mask']=mask;raw[(ds,phase,m['model_name'],m['L'])]=a
   for key,array in [('mean_route_ndc',a['route_ndc']),('mean_graph_ndc',a['graph_ndc'])]:assert abs(m[key]-array.mean())<1e-10
   qps=None
   if phase=='frontier':
    qq=np.array([n/t for t in m['end_to_end_seconds']]);assert len(qq)==5 and np.max(np.abs(qq-m['qps_runs']))<1e-10;qps=float(np.median(qq));assert abs(qps-m['qps'])<1e-10
    for k,(sec,v) in enumerate(zip(m['end_to_end_seconds'],qq)):timings.append(dict(dataset=ds,model=m['model_name'],L=m['L'],repeat=k,seconds=sec,QPS=float(v)))
   rec=dict(dataset=ds,phase=phase,model=m['model_name'],L=m['L'],queries=n,recall_pct=float(hits.mean()*10),failure_pct=float((hits==0).mean()*100),failed_queries=int((hits==0).sum()),route_NDC=float(a['route_ndc'].mean()),graph_NDC=float(a['graph_ndc'].mean()),total_NDC=float(a['route_ndc'].mean()+a['graph_ndc'].mean()),QPS=qps,QPS_min=m['qps_min'],QPS_max=m['qps_max'],route_only_us=None if m['route_only_seconds'] is None else m['route_only_seconds']/n*1e6,graph_only_us=None if m['graph_only_seconds'] is None else m['graph_only_seconds']/n*1e6)
   points.append(rec)
  verification.append(dict(dataset=ds,phase=phase,points=len(result['methods']),outputs=n*len(result['methods']),native_original_queries=16*len(result['methods']),plain_count_repeated_parity=True))
 for phase in ['cal','audit','frontier']:
  ls=LS if phase=='frontier' else [128]
  for L in ls:
   base=raw[(ds,phase,'baseline',L)]
   current=[p for p in points if p['dataset']==ds and p['phase']==phase and p['L']==L]
   basep=next(p for p in current if p['model']=='baseline')
   for p in current:
    a=raw[(ds,phase,p['model'],L)];delta=a['hits'].astype(float)-base['hits'];u=utility(a,base,np.fromfile(O/'inputs'/ds/('audit' if phase=='frontier' else phase)/'gt.i64',np.int64).reshape(1024,100))
    p.update(delta_recall_pp=float(delta.mean()*10),delta_QPS_pct=None if phase!='frontier' else (p['QPS']/basep['QPS']-1)*100,total_NDC_delta_pct=(p['total_NDC']/basep['total_NDC']-1)*100,mean_U=float(u.mean()),helped=int((delta>0).sum()),harmed=int((delta<0).sum()),rescued=int(((base['hits']==0)&(a['hits']>0)).sum()),new_failures=int(((base['hits']>0)&(a['hits']==0)).sum()))
    p.update(entry_changed_queries=int(np.any(a['entries']!=base['entries'],axis=1).sum()),hits_gained=int(delta[delta>0].sum()),hits_lost=int(-delta[delta<0].sum()))
    assert p['rescued']-p['new_failures']==int((base['hits']==0).sum())-p['failed_queries']
    if p['model']!='baseline':
     ci=bootstrap(delta*10);paired.append(dict(dataset=ds,phase=phase,L=L,model=p['model'],reference='baseline',delta_recall_pp=p['delta_recall_pp'],CI_low_pp=ci[0],CI_high_pp=ci[1],rescued=p['rescued'],new_failures=p['new_failures'],helped=p['helped'],harmed=p['harmed']))
    if phase in ['audit','frontier']:
     source_rows=np.fromfile(O/'inputs'/ds/'audit/row_ids.i64',np.int64)
     for i in range(1024):query_rows.append(dict(dataset=ds,phase=phase,L=L,model=p['model'],query_row=int(source_rows[i]),hits=int(a['hits'][i]),baseline_hits=int(base['hits'][i]),delta_hits=int(delta[i]),route_NDC=int(a['route_ndc'][i]),graph_NDC=int(a['graph_ndc'][i])))
   rm=selection[ds]['rl']['model'];em=selection[ds]['es']['model'];rl=raw[(ds,phase,rm,L)];es=raw[(ds,phase,em,L)];delta=(rl['hits'].astype(float)-es['hits'])*10;ci=bootstrap(delta)
   paired.append(dict(dataset=ds,phase=phase,L=L,model=rm,reference=em,delta_recall_pp=float(delta.mean()),CI_low_pp=ci[0],CI_high_pp=ci[1]))
 # Same frozen profile/graph/entries across all L; audit128 and curve128 repeat exact outcomes.
 for model in ['baseline',selection[ds]['rl']['model'],selection[ds]['es']['model']]:
  for key in ['ids','distances','entries','route_ndc','graph_ndc','hits','mask']:
   assert np.array_equal(raw[(ds,'audit',model,128)][key].view(np.uint8),raw[(ds,'frontier',model,128)][key].view(np.uint8)),(ds,model,key)
  hashes=[]
  for L in LS:
   assert np.array_equal(raw[(ds,'frontier',model,L)]['entries'],raw[(ds,'frontier',model,128)]['entries'])
   hashes.append(sha(O/'results'/f'frontier_{ds}'/(model+f'_L{L}.hnsw')))
  assert len(set(hashes))==1
 # Current baseline independently regresses E33 cal/audit (no new old query/GT access).
 for phase in ['cal','audit']:
  p=E37/'results'/f'{phase}_{ds}'/'baseline_L128';old=np.fromfile(p/'ids.i32',np.int32).reshape(1024,10)
  assert np.array_equal(old,raw[(ds,phase,'baseline',128)]['ids'])
 for model in ['nsg','fast30k']:
  hashes=[]
  for L in LS:
   assert np.array_equal(raw[(ds,'frontier',model,L)]['entries'],raw[(ds,'frontier',model,128)]['entries'])
   if model!='nsg':hashes.append(sha(O/'results'/f'frontier_{ds}'/(model+f'_L{L}.hnsw')))
  if hashes:assert len(set(hashes))==1

def frontier(pp):
 result=[]
 for p in pp:
  if not any((q['recall_pct']>=p['recall_pct'] and q['QPS']>=p['QPS'] and (q['recall_pct']>p['recall_pct'] or q['QPS']>p['QPS'])) for q in pp):result.append(p)
 return sorted(result,key=lambda x:x['recall_pct'])
for ds in DS:
 pp=[p for p in points if p['dataset']==ds and p['phase']=='frontier'];base=frontier([p for p in pp if p['model']=='baseline'])
 for model in sorted({p['model'] for p in pp}):
  f=frontier([p for p in pp if p['model']==model]);lo=max(f[0]['recall_pct'],base[0]['recall_pct']);hi=min(f[-1]['recall_pct'],base[-1]['recall_pct'])
  for p in base[1:-1]:
   x=p['recall_pct']
   if lo<=x<=hi:
    v=float(np.exp(np.interp(x,[p['recall_pct'] for p in f],np.log([p['QPS'] for p in f]))));frontiers.append(dict(dataset=ds,model=model,reference_recall_pct=x,baseline_QPS=p['QPS'],interpolated_QPS=v,speedup_pct=(v/p['QPS']-1)*100,kind='descriptive log-QPS interpolation within common nondominated domain'))
gate=[]
for ds in DS:
 model=selection[ds]['rl']['model'];cal=next(p for p in points if p['dataset']==ds and p['phase']=='cal' and p['model']==model);audit=next(p for p in points if p['dataset']==ds and p['phase']=='audit' and p['model']==model)
 passed=cal['delta_recall_pp']>=.1 and audit['delta_recall_pp']>0 and cal['total_NDC_delta_pct']<=1 and audit['total_NDC_delta_pct']<=1
 gate.append(dict(dataset=ds,model=model,cal_delta_recall_pp=cal['delta_recall_pp'],audit_delta_recall_pp=audit['delta_recall_pp'],cal_cost_delta_pct=cal['total_NDC_delta_pct'],audit_cost_delta_pct=audit['total_NDC_delta_pct'],passed=bool(passed)))
dump(O/'results/development_gate.json',dict(status='PASS_LOCAL_DUAL_DEVELOPMENT' if all(x['passed'] for x in gate) else 'STOP_DUAL_DEVELOPMENT_GATE',datasets=gate,default_replaced=False,independent_formal_GO=False,historical_audit_frontier_measured=True))
tables=dict(points=points,paired=paired,timings=timings,query_results=query_rows,frontier_interpolation=frontiers)
for name,rows in tables.items():pd.DataFrame(rows).to_csv(O/'results'/f'{name}.csv',index=False)
dump(O/'results/analysis.json',dict(points=points,paired=paired,frontier=frontiers,development_gate=gate,verification=verification))
dump(O/'reviews/output_verification.json',dict(status='PASS',points=len(points),outputs=sum(x['outputs'] for x in verification),old_baseline_regression_queries=4096,audit_to_curve_parity_queries=6144,full_five_L_entry_graph_consistency=True,GT_independent_set_scoring=True,wall_repeats=250,records=verification))
plt.rcParams.update({'font.size':10,'figure.dpi':130,'savefig.dpi':180})
colors={'baseline':'#252525','rl':'#c84536','es':'#206e9e','fast30k':'#47945b','nsg':'#8c76a0'}
def label(model):return 'Original GT10' if model=='baseline' else ('Full-feedback RL' if model.startswith('rl_') else ('Paired ES' if model.startswith('es_') else ('Fast30K' if model=='fast30k' else 'NSG')))
def color(model):return colors['rl' if model.startswith('rl_') else 'es' if model.startswith('es_') else model]
def save(fig,name):
 fig.tight_layout()
 for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'{name}.{ext}',bbox_inches='tight')
 plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(12,4.7))
for ax,ds,title in zip(axes,DS,['WebVid-2.5M','Yandex-IP 10M']):
 pp=[p for p in points if p['dataset']==ds and p['phase']=='frontier']
 for model in ['nsg','fast30k','baseline',selection[ds]['rl']['model'],selection[ds]['es']['model']]:
  a=sorted([p for p in pp if p['model']==model],key=lambda p:p['L']);ax.plot([p['recall_pct'] for p in a],[p['QPS'] for p in a],'-o',label=label(model),color=color(model),markersize=4)
 ax.set(title=title,xlabel='Recall@10 (%)',ylabel='QPS (one thread; median of 5 runs)');ax.grid(alpha=.22);ax.legend(fontsize=8)
fig.suptitle('E47 frozen static profiles: one HNSW top3, then original NSG\nHistorical audit1024; all five measured L values',y=1.04);save(fig,'recall_qps')
fig,axes=plt.subplots(2,2,figsize=(12,7))
for col,ds in enumerate(DS):
 for arm in ARMS:
  model=selection[ds][arm]['model'];a=sorted([p for p in points if p['dataset']==ds and p['phase']=='frontier' and p['model']==model],key=lambda x:x['L'])
  axes[0,col].plot(LS,[p['delta_recall_pp'] for p in a],'-o',color=colors[arm],label=label(model));axes[1,col].plot(LS,[p['delta_QPS_pct'] for p in a],'-o',color=colors[arm],label=label(model))
 for row in range(2):axes[row,col].axhline(0,color='grey',linewidth=.8);axes[row,col].grid(alpha=.2);axes[row,col].set_xlabel('NSG L');axes[row,col].legend()
 axes[0,col].set_title('WebVid' if col==0 else 'Yandex-IP');axes[0,col].set_ylabel('Recall change vs GT10 (pp)');axes[1,col].set_ylabel('Median QPS change vs GT10 (%)')
save(fig,'quality_cost_changes')

print('E49 ANALYSIS COMPLETE',len(points),'points',flush=True)
