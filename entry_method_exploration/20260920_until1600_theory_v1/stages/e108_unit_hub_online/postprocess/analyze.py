import sys,csv
from pathlib import Path
RUN=Path(__file__).resolve().parents[1];sys.path.insert(0,str(RUN/'src'))
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
assert read(RUN/'reviews/search_complete.json')['status']=='PASS'
assert not (RUN/'reviews/analysis_complete.json').exists()
protected_check();started=time.time()
dump(RUN/'reviews/analysis_lock.json',dict(created_unix=started,source=identity(Path(__file__)),bootstrap_replicates=LOCK['bootstrap_replicates'],seed=LOCK['bootstrap_seed'],descriptive=True))
def boot(x):
 rng=np.random.default_rng(LOCK['bootstrap_seed']);v=[]
 for j in range(0,LOCK['bootstrap_replicates'],100):v.extend(x[rng.integers(len(x),size=(100,len(x)))].mean(1))
 return np.quantile(v,[.025,.975]).tolist()
def table(name,rows):
 with (RUN/'results'/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
metrics=[];pairs=[];exact_pairs=[];routes=[];summaries=[];raw=[];aligned={};times=[]
for ds,c in LOCK['datasets'].items():
 n=LOCK['n'];d=c['dimension'];h=c['H'];gt=np.fromfile(c['evaluation_GT'],'<i4').reshape(n,100);q=np.fromfile(c['evaluation_queries'],'<f4').reshape(n,d)
 assert np.all(np.diff(np.sort(gt,axis=1),axis=1)>0)
 folder=RUN/'results'/('formal_'+ds);old=Path(LOCK['reference_E107'])/'results'/('main_'+ds);done=read(folder/'complete.json');assert done['formal'] and done['NSG_calls']==552960 and done['wall_rounds']==81
 timing=read(folder/'timing_progress.json');assert len(timing)==81 and all(x['threads']==1 and x['cpu']==15 and x['formal'] for x in timing)
 times.extend(dict(dataset=ds,**x) for x in timing)
 base=np.memmap(read(c['evaluation_manifest'])['base'],dtype='<f4',mode='r').reshape(c['base_n'],d+1)[:,1:]
 cache={};point_metrics={};delta_by_pair={};entries_by_method={}
 for name in LOCK['methods']:
  exact_name='UnitHub3' if name=='UnitHub' else 'GT103';exact_entry=np.fromfile(old/exact_name/'entries.i32','<i4').reshape(n,3)
  for ks,ls in LOCK['K_L'].items():
   K=int(ks)
   for L in ls:
    p=folder/('k'+ks)/(name+'_L'+str(L));rec=read(p/'complete.json');assert rec['n']==n and rec['K']==K and rec['L']==L and rec['warm_plain_count_bit_parity'] and rec['formal']
    ids=np.fromfile(p/'ids.i32','<i4').reshape(n,K);dist=np.fromfile(p/'distances.f32','<f4').reshape(n,K);e=np.fromfile(p/'entry_ids.i32','<i4').reshape(n,3);ndc=np.fromfile(p/'graph_ndc.u64','<u8');rn=np.fromfile(p/'route_ndc.u64','<u8')
    assert np.isfinite(dist).all() and np.all(np.diff(dist,axis=1)>=0) and np.all((ids>=0)&(ids<c['base_n'])) and np.all(np.diff(e,axis=1)>0)
    assert K==1 or np.all(np.diff(np.sort(ids,axis=1),axis=1)>0)
    if name in entries_by_method:assert np.array_equal(e,entries_by_method[name])
    else:entries_by_method[name]=e
    mask=(ids[:,:,None]==gt[:,None,:K]).any(1);hit=mask.sum(1).astype('int16');assert np.array_equal(hit,np.array([len(set(ids[i])&set(gt[i,:K])) for i in range(n)]))
    for i in range(0,n,1024):assert np.allclose(-base[ids[i]].astype('float64')@q[i].astype('float64'),dist[i],atol=2e-5,rtol=2e-5)
    wall=rec['seconds'];assert len(wall)==3 and all(x>0 for x in wall)
    tr=[x for x in timing if x['method']==name and x['K']==K and x['L']==L];assert [x['repeat'] for x in tr]==[0,1,2] and [x['seconds'] for x in tr]==wall
    assert all(abs(x['qps']-n/x['seconds'])<1e-8 for x in tr)
    qps=np.array([x['qps'] for x in tr]);metric=dict(dataset=ds,method=name,K=K,L=L,n=n,recall=float(hit.mean()/K),failed=int((hit==0).sum()),mean_qps=float(qps.mean()),min_qps=float(qps.min()),max_qps=float(qps.max()),qps_relative_range_pct=float((qps.max()/qps.min()-1)*100),graph_ndc=float(ndc.mean()),route_ndc=float(rn.mean()),formal_QPS=True)
    metrics.append(metric);point_metrics[name,K,L]=metric;cache[name,K,L]=dict(hit=hit,mask=mask,ids=ids,bits=dist.view('<u4'),ndc=ndc,entries=e,qps=qps)
    aligned[ds+'__'+name+f'__K{K}__L{L}']=hit
    op=old/exact_name/f'k{K}_L{L}';oi=np.fromfile(op/'ids.i32','<i4').reshape(n,K);ob=np.fromfile(op/'distances.f32','<u4').reshape(n,K);on=np.fromfile(op/'ndc.u64','<u8');om=(oi[:,:,None]==gt[:,None,:K]).any(1);oh=om.sum(1)
    same_entry=np.all(e==exact_entry,axis=1);assert np.array_equal(ids[same_entry],oi[same_entry]) and np.array_equal(dist.view('<u4')[same_entry],ob[same_entry]) and np.array_equal(ndc[same_entry],on[same_entry])
    delta=(hit-oh)/K*100;ci=boot(delta)
    exact_pairs.append(dict(dataset=ds,method=name,exact_reference=exact_name,K=K,L=L,delta_recall_pp=float(delta.mean()),CI95_low=ci[0],CI95_high=ci[1],gained_queries=int((delta>0).sum()),harmed_queries=int((delta<0).sum()),exact_failed=int((oh==0).sum()),ANN_failed=int((hit==0).sum()),same_entries=int(same_entry.sum()),new_GT_members=int((mask&~om).sum()),lost_GT_members=int((om&~mask).sum())))
    raw.extend(identity(f) for f in p.iterdir() if f.is_file())
  overlap=(e[:,:,None]==exact_entry[:,None,:]).any(2).sum(1)
  routes.append(dict(dataset=ds,method=name,n=n,exact_reference=exact_name,exact_top3_entry_recall=float(overlap.mean()/3),same_exact_entry_sets=int((overlap==3).sum()),route_ndc=float(rn.mean())))
 for name in LOCK['methods']:
  for L in LOCK['K_L']['100']:
   a=cache[name,1,L];b=cache[name,100,L];assert np.array_equal(a['ids'],b['ids'][:,:1]) and np.array_equal(a['bits'],b['bits'][:,:1]) and np.array_equal(a['ndc'],b['ndc'])
 for ks,ls in LOCK['K_L'].items():
  K=int(ks)
  for an,bn in [('GT10Default','UnitHub'),('GT10Rebuilt','UnitHub'),('GT10Default','GT10Rebuilt')]:
   aggregate=[];qp=[]
   for L in ls:
    a=cache[an,K,L];b=cache[bn,K,L];am=point_metrics[an,K,L];bm=point_metrics[bn,K,L];delta=(b['hit'].astype('int64')-a['hit'])/K*100;ci=boot(delta);same=np.all(a['entries']==b['entries'],axis=1)
    assert np.array_equal(a['ids'][same],b['ids'][same]) and np.array_equal(a['bits'][same],b['bits'][same]) and np.array_equal(a['ndc'][same],b['ndc'][same])
    ratio=bm['mean_qps']/am['mean_qps'];aggregate.append(delta);qp.append(ratio)
    pairs.append(dict(dataset=ds,baseline=an,method=bn,K=K,L=L,baseline_recall=am['recall'],method_recall=bm['recall'],delta_recall_pp=float(delta.mean()),CI95_low=ci[0],CI95_high=ci[1],baseline_failed=am['failed'],method_failed=bm['failed'],gained_queries=int((delta>0).sum()),harmed_queries=int((delta<0).sum()),new_GT_members=int((b['mask']&~a['mask']).sum()),lost_GT_members=int((a['mask']&~b['mask']).sum()),same_entries=int(same.sum()),baseline_qps=am['mean_qps'],method_qps=bm['mean_qps'],delta_mean_qps_pct=float((ratio-1)*100),min_same_repeat_qps_ratio=float((b['qps']/a['qps']).min()),max_same_repeat_qps_ratio=float((b['qps']/a['qps']).max()),nonoverlap_faster=bool(bm['min_qps']>am['max_qps']),mean_pareto_dominates=bool(delta.mean()>=0 and ratio>=1 and (delta.mean()>0 or ratio>1)),delta_graph_ndc_pct=float((bm['graph_ndc']/am['graph_ndc']-1)*100),delta_route_ndc_pct=float((bm['route_ndc']/am['route_ndc']-1)*100)))
   agg=np.array(aggregate).mean(0);ci=boot(agg);summaries.append(dict(dataset=ds,baseline=an,method=bn,K=K,points=len(ls),mean_L_delta_recall_pp=float(agg.mean()),CI95_low=ci[0],CI95_high=ci[1],geomean_L_qps_change_pct=float((np.exp(np.log(qp).mean())-1)*100),descriptive=True))
 print(ds,'analysis complete',flush=True)
for name,rows in [('metrics.csv',metrics),('paired.csv',pairs),('ANN_vs_exact.csv',exact_pairs),('routing.csv',routes),('summary_by_K.csv',summaries),('timing.csv',times)]:table(name,rows)
np.savez_compressed(RUN/'results/aligned_hits.npz',**aligned)
dump(RUN/'reviews/numeric_verification.json',dict(status='PASS',points=len(metrics),paired=len(pairs),ANN_exact=len(exact_pairs),raw_files=raw,independent_all_query_scoring=True,same_entry_output_bits_and_NDC=True,same_L_K1_prefix=True,all_three_plain_walls=True))
fig,axes=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
for i,ds in enumerate(LOCK['datasets']):
 for j,K in enumerate([1,100]):
  ax=axes[i,j]
  for name in LOCK['methods']:
   v=[x for x in metrics if x['dataset']==ds and x['method']==name and x['K']==K];ax.plot([x['recall']*100 for x in v],[x['mean_qps'] for x in v],marker='o',ms=4,label=name)
  ax.set_xlabel(f'Recall@{K} (%)');ax.set_ylabel('Mean QPS (3 plain repeats)');ax.set_title(('WebVid' if i==0 else 'Yandex')+f' | K={K}');ax.grid(alpha=.2);ax.legend()
fig.suptitle('Ordinary micro-HNSW routing + fixed NSG | CPU 15, one thread')
for ext in ['png','pdf']:fig.savefig(RUN/'figures'/('recall_qps.'+ext),dpi=160)
plt.close(fig)
fig,axes=plt.subplots(2,2,figsize=(12,7),constrained_layout=True)
for i,ds in enumerate(LOCK['datasets']):
 for j,K in enumerate([1,100]):
  ax=axes[i,j];v=[x for x in pairs if x['dataset']==ds and x['K']==K and x['baseline']=='GT10Default' and x['method']=='UnitHub'];ax.plot([x['L'] for x in v],[x['delta_mean_qps_pct'] for x in v],marker='o',label='Mean QPS change (%)');ax.axhline(0,color='gray',ls='--');ax.set_xlabel('L');ax.set_ylabel('UnitHub QPS versus current GT10 (%)');ax.set_title(('WebVid' if i==0 else 'Yandex')+f' | K={K}');ax.grid(alpha=.2)
fig.suptitle('Same-budget online speed differences | quality changes reported separately')
for ext in ['png','pdf']:fig.savefig(RUN/'figures'/('same_L_qps.'+ext),dpi=160)
plt.close(fig)
protected_check();dump(RUN/'reviews/analysis_complete.json',dict(status='PASS',seconds=time.time()-started,points=54,formal_wall_rounds=162,new_search=0,summary=summaries))
dump(RUN/'state.json',dict(status='ONLINE_MATRIX_ANALYZED',pending=['interpretation','report','closeout'],default_changed=False))
print('ONLINE_MATRIX_ANALYZED',flush=True)
