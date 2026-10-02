import sys,csv
from pathlib import Path
RUN=Path(__file__).resolve().parents[1];sys.path.insert(0,str(RUN/'src'))
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
assert read(RUN/'reviews/search_complete.json')['status']=='PASS'
assert not (RUN/'reviews/analysis_complete.json').exists()
protected_check();started=time.time();tail=(1-LOCK['CI_level'])/2
dump(RUN/'reviews/analysis_lock.json',dict(created_unix=started,source=identity(Path(__file__)),replicates=LOCK['bootstrap_replicates'],seed=LOCK['bootstrap_seed'],CI_level=LOCK['CI_level'],primary_contrasts=16,descriptive_fit_gate_only=True))
def boot(x):
 rng=np.random.default_rng(LOCK['bootstrap_seed']);v=[]
 for j in range(0,LOCK['bootstrap_replicates'],100):v.extend(x[rng.integers(len(x),size=(100,len(x)))].mean(1))
 return np.quantile(v,[tail,1-tail]).tolist()
def table(name,rows):
 with (RUN/'results'/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
metrics=[];pairs=[];raw=[];all_hits={};proxy_checks=[]
for ds,c in LOCK['datasets'].items():
 n=LOCK['n'];d=c['dimension'];h=c['H'];inp=RUN/'inputs'/ds;cfg=read(inp/'config.json');gt=np.fromfile(cfg['GT'],'<i4').reshape(n,100);q=np.fromfile(cfg['queries'],'<f4').reshape(n,d);mean=np.fromfile(cfg['target_mean'],'<f4').reshape(n,d);counts=np.fromfile(cfg['coverage_counts'],'<i4').reshape(n,h);hids=np.fromfile(cfg['hub_ids'],'<i4')
 unit=np.fromfile(cfg['unit_W'],'<f4').reshape(h,d).astype('float64');P=np.fromfile(cfg['GT10_W'],'<f4').reshape(h,d).astype('float64');scores={'GT10Exact':q.astype('float64')@P.T,'UnitHubExact':q.astype('float64')@unit.T,'TargetMean':mean.astype('float64')@unit.T}
 base=np.memmap(cfg['base'],dtype='<f4',mode='r').reshape(c['base_n'],d+1)[:,1:];folder=RUN/'results'/('main_'+ds);cache={};es={}
 for name in LOCK['methods']:
  p=folder/name;rec=read(p/'complete.json');assert rec['n']==n and rec['count_plain_bit_parity'] and not rec['formal_QPS'] and rec['K']==[1,100]
  entries=np.fromfile(p/'entries.i32','<i4').reshape(n,3);es[name]=entries;assert np.all(np.diff(entries,axis=1)>0);cols=np.searchsorted(hids,entries);assert np.array_equal(hids[cols],entries)
  cover=counts[np.arange(n)[:,None],cols].sum(1)/10;aff=scores['TargetMean'][np.arange(n)[:,None],cols].mean(1)
  assert np.allclose(cover,np.fromfile(p/'proxy_GT10_coverage.f32','<f4'),atol=1e-7,rtol=0)
  assert np.allclose(aff,np.fromfile(p/'proxy_mean_affinity.f32','<f4'),atol=2e-6,rtol=0)
  if name=='Coverage':
   best=np.partition(counts,-3,axis=1)[:,-3:];assert np.array_equal(cover*10,best.sum(1))
   for i in range(n):
    boundary=best[i].min();high=np.flatnonzero(counts[i]>boundary);assert np.isin(high,cols[i]).all();remaining=3-len(high);cand=np.flatnonzero(counts[i]==boundary);sel=cols[i][counts[i,cols[i]]==boundary];bound=np.partition(scores['GT10Exact'][i,cand],-remaining)[-remaining];assert scores['GT10Exact'][i,sel].min()>=bound-2e-6
  else:
   chosen=scores[name][np.arange(n)[:,None],cols];boundary=np.partition(scores[name],-3,axis=1)[:,-3];assert np.all(chosen.min(1)>=boundary-2e-6)
  proxy_checks.append(dict(dataset=ds,method=name,mean_GT10_input_coverage=float(cover.mean()),mean_target_affinity=float(aff.mean()),full_H_proxy_rank_verified=True))
  for K in [1,100]:
   ids=np.fromfile(p/f'k{K}.ids.i32','<i4').reshape(n,K);dist=np.fromfile(p/f'k{K}.distances.f32','<f4').reshape(n,K);ndc=np.fromfile(p/f'k{K}.ndc.u64','<u8');assert np.isfinite(dist).all() and np.all(np.diff(dist,axis=1)>=0) and np.all((ids>=0)&(ids<c['base_n']))
   assert K==1 or np.all(np.diff(np.sort(ids,axis=1),axis=1)>0)
   mask=(ids[:,:,None]==gt[:,None,:K]).any(1);hit=mask.sum(1).astype('int16');assert np.array_equal(hit,np.array([len(set(ids[i])&set(gt[i,:K])) for i in range(n)]))
   for i in range(0,n,512):assert np.allclose(-base[ids[i]].astype('float64')@q[i].astype('float64'),dist[i],atol=2e-5,rtol=2e-5)
   cache[name,K]=dict(hit=hit,mask=mask,ids=ids,bits=dist.view('<u4'),ndc=ndc);all_hits[ds+'__'+name+f'__K{K}']=hit
   metrics.append(dict(dataset=ds,method=name,K=K,L=128,n=n,recall=float(hit.mean()/K),failed=int((hit==0).sum()),graph_ndc=float(ndc.mean()),mean_input_coverage=float(cover.mean()),mean_target_affinity=float(aff.mean()),privileged_fit_proxy=name in ['TargetMean','Coverage'],formal_QPS=False))
  a=cache[name,1];b=cache[name,100];assert np.array_equal(a['ids'],b['ids'][:,:1]) and np.array_equal(a['bits'],b['bits'][:,:1]) and np.array_equal(a['ndc'],b['ndc'])
  raw.extend(identity(f) for f in p.iterdir() if f.is_file())
 for K in [1,100]:
  for an in ['GT10Exact','UnitHubExact']:
   for bn in ['TargetMean','Coverage']:
    a=cache[an,K];b=cache[bn,K];delta=(b['hit'].astype('int64')-a['hit'])/K*100;ci=boot(delta);same=np.all(es[an]==es[bn],axis=1)
    assert np.array_equal(a['ids'][same],b['ids'][same]) and np.array_equal(a['bits'][same],b['bits'][same]) and np.array_equal(a['ndc'][same],b['ndc'][same])
    pairs.append(dict(dataset=ds,baseline=an,method=bn,K=K,L=128,n=n,baseline_recall=float(a['hit'].mean()/K),method_recall=float(b['hit'].mean()/K),delta_recall_pp=float(delta.mean()),CI_adjusted_low=ci[0],CI_adjusted_high=ci[1],baseline_failed=int((a['hit']==0).sum()),method_failed=int((b['hit']==0).sum()),gained_queries=int((delta>0).sum()),harmed_queries=int((delta<0).sum()),new_GT_members=int((b['mask']&~a['mask']).sum()),lost_GT_members=int((a['mask']&~b['mask']).sum()),same_entries=int(same.sum()),delta_graph_ndc_pct=float((b['ndc'].mean()/a['ndc'].mean()-1)*100),privileged_fit_only=True))
 print(ds,'perfect proxy analysis complete',flush=True)
decisions=[]
for family in LOCK['priority']:
 datasets=[]
 for ds in LOCK['datasets']:
  r=[x for x in pairs if x['dataset']==ds and x['method']==family];nonnegative=all(x['delta_recall_pp']>=0 for x in r);qualifying=[]
  for K in [1,100]:
   rows=[x for x in r if x['K']==K];assert len(rows)==2
   if all(x['delta_recall_pp']>=LOCK['minimum_promise_pp'] and x['CI_adjusted_low']>0 for x in rows):qualifying.append(K)
  datasets.append(dict(dataset=ds,both_K_both_controls_mean_nonnegative=nonnegative,qualifying_K=qualifying,passed=nonnegative and bool(qualifying)))
 decisions.append(dict(family=family,datasets=datasets,passed=all(x['passed'] for x in datasets)))
passed=[x['family'] for x in decisions if x['passed']];selected=passed[0] if passed else None
gate=dict(status='PROMISING_PROXY_INFORMATION' if selected else 'STOP_PROXY_OBJECTIVES_BEFORE_TRAINING',selected_object=selected,decisions=decisions,CI_level=LOCK['CI_level'],primary_contrasts=len(pairs),fit_only=True,search_utility_upper_bound=False,deployable_method=False,new_training=0,new_formal_QPS=False,default_changed=False)
table('metrics.csv',metrics);table('paired.csv',pairs);table('proxy_values.csv',proxy_checks);np.savez_compressed(RUN/'results/aligned_hits.npz',**all_hits)
dump(RUN/'results/gate.json',gate);dump(RUN/'reviews/numeric_verification.json',dict(status='PASS',raw_files=raw,all_query_independent_scoring=True,all_H_proxy_rank_checks=True,source_GT10_labels_are_real_ID=True,same_L_K1_prefix=True,points=len(metrics)))
fig,axes=plt.subplots(2,2,figsize=(13,8),constrained_layout=True)
for i,ds in enumerate(LOCK['datasets']):
 for j,K in enumerate([1,100]):
  ax=axes[i,j];rows=[x for x in pairs if x['dataset']==ds and x['K']==K]
  for z,r in enumerate(rows):
   value=r['delta_recall_pp'];ax.errorbar(z,value,yerr=[[value-r['CI_adjusted_low']],[r['CI_adjusted_high']-value]],fmt='o',capsize=4,color='tab:blue' if r['method']=='Coverage' else 'tab:orange')
  ax.set_xticks(range(4),[(('Cov' if r['method']=='Coverage' else 'Mean')+' vs '+('GT10' if r['baseline']=='GT10Exact' else 'Unit')) for r in rows],rotation=20);ax.axhline(0,color='gray',ls='--');ax.set_ylabel('Recall change (pp)');ax.set_title(('WebVid' if i==0 else 'Yandex')+f' | K={K}');ax.grid(axis='y',alpha=.2)
fig.suptitle('Perfect target information: privileged fit diagnostic, not deployable Recall bound\n99.6875% paired bootstrap intervals; fixed L=128')
for ext in ['png','pdf']:fig.savefig(RUN/'figures'/('proxy_information_gate.'+ext),dpi=160)
plt.close(fig)
protected_check();dump(RUN/'reviews/analysis_complete.json',dict(status='PASS',seconds=time.time()-started,gate=gate,new_search=0));dump(RUN/'state.json',dict(status='PROXY_INFORMATION_ANALYZED',decision=gate['status'],selected_object=selected,pending=['report','closeout','new predictor protocol only if gate passed']))
print(json.dumps(gate,ensure_ascii=False,indent=2))
