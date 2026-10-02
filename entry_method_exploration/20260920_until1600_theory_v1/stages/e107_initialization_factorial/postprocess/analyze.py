import sys,csv
from pathlib import Path
RUN=Path(__file__).resolve().parents[1];sys.path.insert(0,str(RUN/'src'))
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
assert read(RUN/'reviews/search_complete.json')['status']=='PASS'
assert not (RUN/'reviews/analysis_complete.json').exists()
protected_check();start=time.time();seed=20260920;replicates=5000
dump(RUN/'reviews/analysis_lock.json',dict(created_unix=start,source=identity(Path(__file__)),bootstrap_replicates=replicates,seed=seed,descriptive=True,selection=False))
def boot(delta):
 rng=np.random.default_rng(seed);v=[]
 for i in range(0,replicates,100):v.extend(delta[rng.integers(len(delta),size=(min(100,replicates-i),len(delta)))].mean(1))
 return np.quantile(v,[.025,.975]).tolist()
def table(path,rows):
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
metrics=[];pairs=[];interactions=[];raw=[];aligned={};ns={}
for ds,c in LOCK['datasets'].items():
 n=LOCK['n'];d=c['dimension'];gt=np.fromfile(c['evaluation_GT'],'<i4').reshape(n,100);q=np.fromfile(c['evaluation_queries'],'<f4').reshape(n,d)
 assert np.all(np.diff(np.sort(gt,axis=1),axis=1)>0)
 hubids=np.fromfile(Path(c['fit_input'])/'hub_ids.i32','<i4');p=RUN/'results'/('main_'+ds);results={};entries={};returned={};ndcs={};target_masks={}
 base=np.memmap(read(c['evaluation_manifest'])['base'],dtype='<f4',mode='r').reshape(c['base_n'],d+1)[:,1:]
 current=read(p/'config.json')
 for m in current['methods']:
  name=m['name'];e=np.fromfile(p/name/'entries.i32','<i4').reshape(n,3);entries[name]=e;count=m['entry_count']
  assert (count==3 and np.all(np.diff(e,axis=1)>0)) or (count==1 and np.all(e[:,1:]==-1))
  if m['route']!='fixed':assert np.isin(e[:,:count],hubids).all()
  if m['route']=='exact':
   w=np.fromfile(m['W'],'<f4').reshape(c['H'],d).astype('float64')
   for i in range(0,n,256):
    scores=w@q[i].astype('float64');sel=np.searchsorted(hubids,e[i,:count]);bound=np.partition(scores,-count)[-count]
    assert scores[sel].min()>=bound-2e-6*max(1,np.linalg.norm(q[i]))
  route=np.fromfile(p/name/'route_ndc.u64','<u8');assert route.shape==(n,)
  for Kstr,Ls in LOCK['K_L'].items():
   K=int(Kstr)
   for L in Ls:
    point=p/name/f'k{K}_L{L}';done=read(point/'complete.json');assert done['plain_count_bit_parity'] and done['n']==n and done['K']==K and done['L']==L
    ids=np.fromfile(point/'ids.i32','<i4').reshape(n,K);dist=np.fromfile(point/'distances.f32','<f4').reshape(n,K);ndc=np.fromfile(point/'ndc.u64','<u8')
    assert np.isfinite(dist).all() and np.all(np.diff(dist,axis=1)>=0) and np.all((ids>=0)&(ids<c['base_n']))
    assert K==1 or np.all(np.diff(np.sort(ids,axis=1),axis=1)>0)
    mask=(ids[:,:,None]==gt[:,None,:K]).any(1);hit=mask.sum(1).astype('int16');target_masks[name,K,L]=mask
    assert np.array_equal(hit,np.array([len(set(ids[i])&set(gt[i,:K])) for i in range(n)]))
    for i in range(0,n,1024):assert np.allclose(-base[ids[i]].astype('float64')@q[i].astype('float64'),dist[i],atol=2e-5,rtol=2e-5)
    results[name,K,L]=hit;returned[name,K,L]=(ids,dist.view('<u4'));ndcs[name,K,L]=ndc
    metrics.append(dict(dataset=ds,method=name,representation=m['representation'],entry_count=count,route=m['route'],K=K,L=L,n=n,recall=float(hit.mean()/K),failed=int((hit==0).sum()),graph_ndc=float(ndc.mean()),route_ndc=float(route.mean()),formal_QPS=False))
    aligned[ds+'__'+name+f'__K{K}__L{L}']=hit
    raw.extend(identity(f) for f in point.iterdir() if f.is_file())
 for rep in ['UnitHub','GT1','GT10']:assert np.all(np.any(entries[rep+'1'][:,:1]==entries[rep+'3'],axis=1)),'top1 retained in top3'
 for m in current['methods']:
  name=m['name']
  for L in LOCK['K_L']['100']:
   assert np.array_equal(returned[name,1,L][0],returned[name,100,L][0][:,:1]),'same-L K1 output is K100 prefix'
   assert np.array_equal(returned[name,1,L][1],returned[name,100,L][1][:,:1]) and np.array_equal(ndcs[name,1,L],ndcs[name,100,L]),'same-L search work and prefix distance bits'
 for Kstr,Ls in LOCK['K_L'].items():
  K=int(Kstr)
  for L in Ls:
   seen={}
   for m in current['methods']:
    name=m['name'];ids,bits=returned[name,K,L]
    for i,e in enumerate(entries[name]):
     key=(i,*map(int,e));value=(ids[i].tobytes(),bits[i].tobytes(),int(ndcs[name,K,L][i]))
     if key in seen:assert value==seen[key],'identical inputs/entries must have same output and NDC'
     else:seen[key]=value
   contrasts=[(rep+'1',rep+'3','entry_count') for rep in ['UnitHub','GT1','GT10']]
   contrasts += [(a+str(m),b+str(m),'representation') for m in [1,3] for a,b in [('UnitHub','GT1'),('GT1','GT10')]]
   contrasts += [('NSGFixed1',rep,'versus_NSG') for rep in ['UnitHub1','UnitHub3','GT11','GT13','GT101','GT103','DefaultANN']]
   contrasts += [('GT103','DefaultANN','ANN_effect')]
   for a,b,kind in contrasts:
    ah=results[a,K,L].astype('int64');bh=results[b,K,L].astype('int64');delta=bh-ah;diff=delta/K*100
    gained=int(delta[delta>0].sum());lost=int(-delta[delta<0].sum());ci=boot(diff)
    am=target_masks[a,K,L];bm=target_masks[b,K,L];new_members=int((bm&~am).sum());lost_members=int((am&~bm).sum());assert new_members-lost_members==gained-lost
    pairs.append(dict(dataset=ds,comparison=kind,baseline=a,method=b,K=K,L=L,n=n,baseline_recall=float(ah.mean()/K),method_recall=float(bh.mean()/K),delta_recall_pp=float(diff.mean()),CI95_low=ci[0],CI95_high=ci[1],baseline_failed=int((ah==0).sum()),method_failed=int((bh==0).sum()),gained_queries=int((delta>0).sum()),harmed_queries=int((delta<0).sum()),equal_queries=int((delta==0).sum()),positive_query_hit_delta=gained,negative_query_hit_delta=lost,new_GT_members=new_members,lost_GT_members=lost_members,net_target_hits=gained-lost,rescued=int(((ah==0)&(bh>0)).sum()),new_failed=int(((ah>0)&(bh==0)).sum()),same_entries=int(np.all(entries[a]==entries[b],axis=1).sum()),delta_graph_ndc_pct=float((ndcs[b,K,L].mean()/ndcs[a,K,L].mean()-1)*100),formal_QPS=False))
   for a,b in [('UnitHub','GT1'),('GT1','GT10')]:
    delta=((results[b+'3',K,L].astype('int64')-results[b+'1',K,L])-(results[a+'3',K,L].astype('int64')-results[a+'1',K,L]))/K*100
    ci=boot(delta);interactions.append(dict(dataset=ds,contrast=f'({b}3-{b}1)-({a}3-{a}1)',K=K,L=L,delta_recall_pp=float(delta.mean()),CI95_low=ci[0],CI95_high=ci[1]))
 print(ds,'scoring and paired analysis complete',flush=True)
table(RUN/'results/metrics.csv',metrics);table(RUN/'results/paired.csv',pairs);table(RUN/'results/interactions.csv',interactions)
np.savez_compressed(RUN/'results/aligned_hits.npz',**aligned)
dump(RUN/'reviews/numeric_verification.json',dict(status='PASS',points=len(metrics),paired=len(pairs),interactions=len(interactions),all_query_independent_scoring=True,same_entries_output_parity=True,raw_files=raw))
names={'NSGFixed1':'NSG fixed','UnitHub1':'Unit hub / 1','UnitHub3':'Unit hub / 3','GT11':'GT1 / 1','GT13':'GT1 / 3','GT101':'GT10 / 1','GT103':'GT10 / 3','DefaultANN':'Default ANN / 3'}
fig,axes=plt.subplots(2,2,figsize=(13,8),constrained_layout=True)
for i,ds in enumerate(LOCK['datasets']):
 for j,K in enumerate([1,100]):
  ax=axes[i,j]
  for name in names:
   rows=[r for r in metrics if r['dataset']==ds and r['K']==K and r['method']==name];ax.plot([r['graph_ndc'] for r in rows],[r['recall']*100 for r in rows],marker='o',ms=3,label=names[name])
  ax.set_xlabel('Graph distance computations / query');ax.set_ylabel(f'Recall@{K} (%)');ax.set_title(('WebVid' if i==0 else 'Yandex')+f' | K={K}');ax.grid(alpha=.2)
axes[0,0].legend(fontsize=8,ncol=2);fig.suptitle('Initialization factorial | measured search work, not online QPS')
for ext in ['png','pdf']:fig.savefig(RUN/'figures'/('factorial_quality_cost.'+ext),dpi=160)
plt.close(fig)
fig,axes=plt.subplots(2,2,figsize=(13,7),constrained_layout=True)
for i,ds in enumerate(LOCK['datasets']):
 for j,K in enumerate([1,100]):
  ax=axes[i,j]
  for rep in ['UnitHub','GT1','GT10']:
   rows=[r for r in pairs if r['dataset']==ds and r['K']==K and r['baseline']==rep+'1' and r['method']==rep+'3'];ax.plot([r['L'] for r in rows],[r['delta_recall_pp'] for r in rows],marker='o',label=rep)
  ax.axhline(0,color='gray',ls='--');ax.set_xlabel('L');ax.set_ylabel('Recall: 3 entries minus 1 (pp)');ax.set_title(('WebVid' if i==0 else 'Yandex')+f' | K={K}');ax.grid(alpha=.2);ax.legend()
fig.suptitle('Entry-count effects depend on representation and search budget')
for ext in ['png','pdf']:fig.savefig(RUN/'figures'/('entry_count_effect.'+ext),dpi=160)
plt.close(fig)
protected_check();dump(RUN/'reviews/analysis_complete.json',dict(status='PASS',seconds=time.time()-start,points=len(metrics),new_search=0,formal_QPS=False))
dump(RUN/'state.json',dict(status='FACTORIAL_ANALYZED',pending=['report','method derivation under active timebox']))
print('FACTORIAL_ANALYZED',flush=True)
