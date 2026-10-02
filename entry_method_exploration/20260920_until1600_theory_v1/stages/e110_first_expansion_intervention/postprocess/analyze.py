import sys,csv
from pathlib import Path
RUN=Path(__file__).resolve().parents[1];sys.path.insert(0,str(RUN/'src'))
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
assert read(RUN/'reviews/search_complete.json')['status']=='PASS' and not (RUN/'reviews/analysis_complete.json').exists()
protected_check();started=time.time();dump(RUN/'reviews/analysis_lock.json',dict(created_unix=started,source=identity(Path(__file__)),bootstrap_replicates=LOCK['bootstrap_replicates'],seed=LOCK['bootstrap_seed']))
def boot(x,level):
 rng=np.random.default_rng(LOCK['bootstrap_seed']);v=[]
 for i in range(0,LOCK['bootstrap_replicates'],100):v.extend(x[rng.integers(len(x),size=(100,len(x)))].mean(1))
 return np.quantile(v,[(1-level)/2,1-(1-level)/2]).tolist()
def table(name,rows):
 with (RUN/'results'/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
metrics=[];pairs=[];summary=[];groups=[];raw=[];gates=[];aligned={}
for ds,c in LOCK['datasets'].items():
 cfg=read(RUN/'reviews'/('main_'+ds+'.json'));n=4096;gt=np.fromfile(cfg['GT'],'<i4').reshape(n,100);q=np.fromfile(cfg['queries'],'<f4').reshape(n,c['dimension']);base=np.memmap(cfg['base'],dtype='<f4',mode='r').reshape(c['base_n'],c['dimension']+1)[:,1:];cache={};entries={}
 original_first=np.fromfile(Path(LOCK['reference_initial_order'])/ds/'GT103/first.i32','<i4')
 for name in LOCK['methods']:
  folder=RUN/'results'/('main_'+ds)/name;entries[name]=np.fromfile(folder/'entries.i32','<i4').reshape(n,3);primary=np.fromfile(folder/'primary.i32','<i4');changed=primary!=original_first
  for K,Ls in LOCK['K_L'].items():
   K=int(K)
   for L in Ls:
    p=folder/f'k{K}_L{L}';check=read(p/'complete.json');assert check['plain_count_bit_parity'] and check['K']==K and check['L']==L
    ids=np.fromfile(p/'ids.i32','<i4').reshape(n,K);dist=np.fromfile(p/'distances.f32','<f4').reshape(n,K);ndc=np.fromfile(p/'ndc.u64','<u8');first=np.fromfile(p/'first_expanded.i32','<i4');assert np.array_equal(first,original_first if name=='GT103' else primary)
    assert np.isfinite(dist).all() and np.all(np.diff(dist,axis=1)>=0) and np.all((ids>=0)&(ids<c['base_n']))
    assert K==1 or np.all(np.diff(np.sort(ids,axis=1),axis=1)>0)
    mask=(ids[:,:,None]==gt[:,None,:K]).any(1);hit=mask.sum(1).astype('int16');assert np.array_equal(hit,np.array([len(set(ids[i])&set(gt[i,:K])) for i in range(n)]))
    for i in range(0,n,1024):assert np.allclose(-base[ids[i]].astype('float64')@q[i].astype('float64'),dist[i],atol=2e-5,rtol=2e-5)
    cache[name,K,L]=dict(ids=ids,bits=dist.view('<u4'),ndc=ndc,hit=hit,mask=mask);aligned[ds+'__'+name+f'__K{K}_L{L}']=hit
    metrics.append(dict(dataset=ds,method=name,K=K,L=L,n=n,recall=float(hit.mean()/K),failed=int((hit==0).sum()),graph_ndc=float(ndc.mean()),first_changed_from_original=int(changed.sum()) if name=='PrimaryFirst3' else 0,formal_QPS=False))
    raw.extend(identity(f) for f in p.iterdir() if f.is_file())
  for L in LOCK['K_L']['100']:
   a=cache[name,1,L];b=cache[name,100,L];assert np.array_equal(a['ids'],b['ids'][:,:1]) and np.array_equal(a['bits'],b['bits'][:,:1]) and np.array_equal(a['ndc'],b['ndc'])
 assert np.array_equal(entries['GT103'],entries['PrimaryFirst3']) and np.all(np.any(entries['GT103']==entries['GT101'][:,:1],axis=1))
 for an in ['GT103','GT101']:
  deltas={};ndc_ratios=[]
  for K,Ls in LOCK['K_L'].items():
   K=int(K);deltas[K]=[]
   for L in Ls:
    a=cache[an,K,L];b=cache['PrimaryFirst3',K,L];delta=(b['hit'].astype('int64')-a['hit'])/K*100;deltas[K].append(delta);ci=boot(delta,.95);ndc_ratios.append(b['ndc'].mean()/a['ndc'].mean())
    if an=='GT103':assert np.array_equal(a['ids'][~changed],b['ids'][~changed]) and np.array_equal(a['bits'][~changed],b['bits'][~changed]) and np.array_equal(a['ndc'][~changed],b['ndc'][~changed])
    pairs.append(dict(dataset=ds,baseline=an,method='PrimaryFirst3',K=K,L=L,delta_recall_pp=float(delta.mean()),CI95_low=ci[0],CI95_high=ci[1],baseline_failed=int((a['hit']==0).sum()),method_failed=int((b['hit']==0).sum()),gained_queries=int((delta>0).sum()),harmed_queries=int((delta<0).sum()),new_GT_members=int((b['mask']&~a['mask']).sum()),lost_GT_members=int((a['mask']&~b['mask']).sum()),delta_graph_ndc_pct=float((ndc_ratios[-1]-1)*100)))
    if an=='GT103':
     for group,m in [('first_retained',~changed),('first_changed',changed)]:groups.append(dict(dataset=ds,K=K,L=L,group=group,n=int(m.sum()),delta_recall_pp=float(delta[m].mean()),gained=int((delta[m]>0).sum()),harmed=int((delta[m]<0).sum()),complete_predefined_group=True))
  km={K:np.stack(x).mean(0) for K,x in deltas.items()};equal=(km[1]+km[100])/2;ci=boot(equal,LOCK['primary_CI_level']);summary.append(dict(dataset=ds,baseline=an,K1_mean_delta_pp=float(km[1].mean()),K100_mean_delta_pp=float(km[100].mean()),equal_K_mean_delta_pp=float(equal.mean()),CI9875_low=ci[0],CI9875_high=ci[1],mean_graph_NDC_ratio=float(np.mean(ndc_ratios))))
 rows=[x for x in summary if x['dataset']==ds];quality=all(x['K1_mean_delta_pp']>=0 and x['K100_mean_delta_pp']>=0 and x['equal_K_mean_delta_pp']>=.10 and x['CI9875_low']>0 for x in rows);cost=next(x['mean_graph_NDC_ratio'] for x in rows if x['baseline']=='GT103')<=1.01;gates.append(dict(dataset=ds,quality_passed=quality,NDC_passed=cost,passed=quality and cost))
 print(ds,'analysis complete',flush=True)
table('metrics.csv',metrics);table('paired.csv',pairs);table('primary_summary.csv',summary);table('first_order_groups.csv',groups);np.savez_compressed(RUN/'results/aligned_hits.npz',**aligned)
gate=dict(status='PROMISING_FIRST_EXPANSION_CANDIDATE' if all(x['passed'] for x in gates) else 'STOP_FIRST_EXPANSION_CANDIDATE',datasets=gates,default_changed=False,exposed_development=True,new_QPS=False,method_is_exact_only=True);dump(RUN/'results/gate.json',gate)
fig,axes=plt.subplots(2,2,figsize=(12,7),constrained_layout=True)
for i,ds in enumerate(LOCK['datasets']):
 for j,K in enumerate([1,100]):
  ax=axes[i,j]
  for base_name,color in [('GT103','tab:blue'),('GT101','tab:orange')]:
   r=[x for x in pairs if x['dataset']==ds and x['K']==K and x['baseline']==base_name];y=np.array([x['delta_recall_pp'] for x in r]);ax.errorbar([x['L'] for x in r],y,yerr=[y-[x['CI95_low'] for x in r],[x['CI95_high'] for x in r]-y],label='vs '+base_name,color=color,fmt='o-',capsize=3)
  ax.axhline(0,color='gray',ls='--');ax.set_title(('WebVid' if i==0 else 'Yandex')+f' | K={K}');ax.set_xlabel('L');ax.set_ylabel('Recall change (pp)');ax.grid(alpha=.2);ax.legend()
fig.suptitle('Same three entries, force profile-top1 to expand first\nFull exposed development; pointwise 95% descriptive intervals')
for ext in ['png','pdf']:fig.savefig(RUN/'figures'/('first_expansion_effect.'+ext),dpi=160)
plt.close(fig);protected_check();dump(RUN/'reviews/numeric_verification.json',dict(status='PASS',raw_files=raw,points=54,pairs=36,primary_summaries=4,same_entries_and_same_first_noop=True,original_controls_full_restored=True,all_first_expansions_verified=True,K1_prefix_parity=True))
dump(RUN/'reviews/analysis_complete.json',dict(status='PASS',seconds=time.time()-started,gate=gate));dump(RUN/'state.json',dict(status='FIRST_EXPANSION_ANALYZED',decision=gate['status'],pending=['report','closeout']));print(json.dumps(gate,indent=2))
