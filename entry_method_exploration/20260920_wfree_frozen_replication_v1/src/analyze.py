from pathlib import Path
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import json,csv,hashlib,time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
RUN=Path(__file__).resolve().parents[1];LOCK=json.loads((RUN/'config.locked.json').read_text());N=LOCK['n']
assert json.loads((RUN/'reviews/search_complete.json').read_text())['status']=='PASS'
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def table(p,rows):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
metrics=[];paired=[];primary=[];thresholds=[];allwall=[];verified=[];aligned={};failure_rows=[];start=time.time()
rng=np.random.default_rng(LOCK['seed'])
for ds,c in LOCK['datasets'].items():
 inp=RUN/'inputs'/ds;gt=np.fromfile(inp/'gt.i32',dtype='<i4').reshape(N,100);q=np.fromfile(inp/'queries.f32',dtype='<f4').reshape(N,c['dimension']);source_rows=np.fromfile(inp/'source_rows.i64',dtype='<i8')
 basepath=Path(json.loads((inp/'gt_manifest.json').read_text())['base']);raw=np.memmap(basepath,dtype='<f4',mode='r').reshape(-1,c['dimension']+1);base=raw[:,1:]
 out=RUN/'results'/ds;wall=json.loads((out/'timing_progress.json').read_text());assert len(wall)==192;allwall.extend([dict(dataset=ds,**w) for w in wall]);names=[c['anchor']['name'],'WFree'];cached={};route_ref={}
 for k,ls in LOCK['L'].items():
  K=int(k)
  for L in ls:
   for name in names:
    p=out/f'k{K}'/f'{name}_L{L}';done=json.loads((p/'complete.json').read_text());assert done['status']=='PASS' and done['n']==N and done['threads']==1
    ids=np.fromfile(p/'ids.i32',dtype='<i4').reshape(N,K);dist=np.fromfile(p/'distances.f32',dtype='<f4').reshape(N,K);entries=np.fromfile(p/'entry_ids.i32',dtype='<i4').reshape(N,3);rn=np.fromfile(p/'route_ndc.u64',dtype='<u8');gn=np.fromfile(p/'graph_ndc.u64',dtype='<u8')
    assert np.all((ids>=0)&(ids<c['base_n'])) and np.all(np.isfinite(dist)) and np.all(np.diff(dist,axis=1)>=0)
    assert K==1 or np.all(np.diff(np.sort(ids,axis=1),axis=1)>0)
    assert np.all(np.diff(entries,axis=1)>0) and len(rn)==len(gn)==N
    hit=(ids[:,:,None]==gt[:,None,:K]).any(axis=2).sum(axis=1).astype(np.int16)
    for i in range(0,N,128):assert hit[i]==len(set(ids[i])&set(gt[i,:K]))
    for i in range(0,N,512):
     scores=-np.sum(base[ids[i]].astype(np.float64)*q[i].astype(np.float64),axis=1)
     assert np.allclose(scores,dist[i],rtol=2e-5,atol=2e-5),'raw IP output distance'
    if name in route_ref:assert np.array_equal(entries,route_ref[name])
    else:route_ref[name]=entries.copy()
    seconds=np.asarray(done['seconds']);assert len(seconds)==3 and np.all(seconds>0)
    row=dict(dataset=ds,method=name,K=K,L=L,n=N,recall=float(hit.mean()/K),failed_queries=int((hit==0).sum()),failure_rate=float((hit==0).mean()),qps=float(np.mean(N/seconds)),qps_min=float(np.min(N/seconds)),qps_max=float(np.max(N/seconds)),graph_ndc=float(gn.mean()),route_ndc=float(rn.mean()),total_ndc=float((gn+rn).mean()))
    metrics.append(row);cached[(name,K,L)]=(hit,row,seconds,entries)
    aligned[f'{ds}__{name}__K{K}_L{L}']=hit
    verified.extend([dict(path=str(f),sha256=sha(f)) for f in p.iterdir() if f.is_file()])
   ah,ar,at,ae=cached[(names[0],K,L)];wh,wr,wt,we=cached[('WFree',K,L)];delta=(wh.astype(float)-ah)/K*100
   rescue=(ah==0)&(wh>0);harm=(ah>0)&(wh==0);assert rescue.sum()-harm.sum()==ar['failed_queries']-wr['failed_queries']
   same_entries=(ae==we).all(axis=1)
   ap=out/f'k{K}'/f'{names[0]}_L{L}';wp=out/f'k{K}'/f'WFree_L{L}'
   for file,dtype,width in [('ids.i32','<i4',K),('distances.f32','<u4',K),('graph_ndc.u64','<u8',1)]:
    aa=np.fromfile(ap/file,dtype=dtype).reshape(N,width);ww=np.fromfile(wp/file,dtype=dtype).reshape(N,width);assert np.array_equal(aa[same_entries],ww[same_entries])
   row=dict(dataset=ds,K=K,L=L,delta_recall_pp=float(delta.mean()),delta_qps_pct=float((wr['qps']/ar['qps']-1)*100),baseline_failed=ar['failed_queries'],WFree_failed=wr['failed_queries'],rescued=int(rescue.sum()),newly_harmed=int(harm.sum()),same_entries=int(same_entries.sum()),first_half_delta_pp=float(delta[:N//2].mean()),second_half_delta_pp=float(delta[N//2:].mean()),delta_graph_ndc_pct=float((wr['graph_ndc']/ar['graph_ndc']-1)*100))
   paired.append(row)
   for i in np.flatnonzero((ah==0)|(wh==0)):
    failure_rows.append(dict(dataset=ds,K=K,L=L,position=int(i),source_row=int(source_rows[i]),baseline_hits=int(ah[i]),WFree_hits=int(wh[i]),rescued=bool(rescue[i]),newly_harmed=bool(harm[i])))
   if L==128:
    means=np.empty(20000)
    for j in range(0,len(means),128):
     ix=rng.integers(N,size=(min(128,len(means)-j),N));means[j:j+len(ix)]=delta[ix].mean(axis=1)
    p=dict(row,baseline_recall=ar['recall'],WFree_recall=wr['recall'],CI95=np.quantile(means,[.025,.975]).tolist(),CI98_75=np.quantile(means,[.00625,.99375]).tolist(),bootstrap_replicates=20000)
    primary.append(p)
  for target in LOCK['targets']:
   options={name:[cached[(name,K,L)] for L in ls if cached[(name,K,L)][1]['recall']>=target] for name in names}
   best={name:min(v,key=lambda x:(-x[1]['qps'],x[1]['L'])) if v else None for name,v in options.items()}
   a=best[names[0]];w=best['WFree'];r=dict(dataset=ds,K=K,target=target,baseline_reachable=a is not None,WFree_reachable=w is not None,baseline_L=a[1]['L'] if a else None,WFree_L=w[1]['L'] if w else None,baseline_recall=a[1]['recall'] if a else None,WFree_recall=w[1]['recall'] if w else None,baseline_qps=a[1]['qps'] if a else None,WFree_qps=w[1]['qps'] if w else None,delta_qps_pct=(w[1]['qps']/a[1]['qps']-1)*100 if a and w else None,all_three_rounds_gain=bool(np.all(N/w[2]>N/a[2])) if a and w else None)
   thresholds.append(r)
 aligned[ds+'__source_rows']=source_rows
gate=[]
for ds in LOCK['datasets']:
 p=[x for x in primary if x['dataset']==ds];ts=[x for x in thresholds if x['dataset']==ds and x['baseline_reachable'] and x['WFree_reachable']]
 quality=all(x['delta_recall_pp']>=0 for x in p) and any(x['delta_recall_pp']>=.5 for x in p) and any(x['CI98_75'][0]>0 for x in p)
 speed=bool(ts) and any(x['delta_qps_pct']>=3 and x['all_three_rounds_gain'] for x in ts) and all(x['delta_qps_pct']>=-3 for x in ts)
 gate.append(dict(dataset=ds,L128_quality_pass=quality,full_wall_pass=speed,pass_both=quality and speed))
status='PASS_FROZEN_REPLICATION_FOR_MECHANISM_RESEARCH' if all(x['pass_both'] for x in gate) else 'STOP_WFREE_REPLICATION'
table(RUN/'results/metrics.csv',metrics);table(RUN/'results/paired.csv',paired);table(RUN/'results/thresholds.csv',thresholds);table(RUN/'results/wall_rounds.csv',allwall);table(RUN/'results/failure_queries.csv',failure_rows)
np.savez_compressed(RUN/'results/aligned_hits.npz',**aligned);dump(RUN/'results/primary_L128.json',primary);dump(RUN/'reviews/decision.json',dict(status=status,datasets=gate,primary=primary,thresholds=thresholds,default_changed=False,training_runs=0,graph_builds=0))
dump(RUN/'reviews/numeric_verification.json',dict(status='PASS',method_points=len(metrics),paired_points=len(paired),wall_rounds=len(allwall),scored_returns=N*len(metrics),raw_files=verified,cross_L_K_entries_constant=True,same_entries_same_output_bits_and_graph_cost=True,independent_set_scoring_rows_per_point=32,float64_distance_queries_per_point=8,seconds=time.time()-start))
fig,axs=plt.subplots(2,2,figsize=(11,8),constrained_layout=True)
for j,(ds,c) in enumerate(LOCK['datasets'].items()):
 for i,K in enumerate([1,100]):
  ax=axs[i,j]
  for name,color in [(c['anchor']['name'],'#3568b0'),('WFree','#d85a32')]:
   rr=[r for r in metrics if r['dataset']==ds and r['K']==K and r['method']==name];x=np.array([r['recall']*100 for r in rr]);y=np.array([r['qps'] for r in rr]);ax.plot(x,y,'o-',ms=3,label=name,color=color);ax.fill_between(x,[r['qps_min'] for r in rr],[r['qps_max'] for r in rr],color=color,alpha=.15)
  ax.set_title(('WebVid' if ds.startswith('webvid') else 'Yandex')+f' | Recall@{K}');ax.set_xlabel('Recall (%)');ax.set_ylabel('QPS (single thread)');ax.grid(alpha=.2);ax.legend()
fig.suptitle('Frozen WFree replication | 4,096 new queries per dataset\nShared NSG kernel; complete online wall; bands: 3 timing rounds')
fig.savefig(RUN/'figures/recall_qps.png',dpi=180);fig.savefig(RUN/'figures/recall_qps.pdf');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(10,4),constrained_layout=True)
for j,ds in enumerate(LOCK['datasets']):
 rr=[p for p in primary if p['dataset']==ds];x=np.arange(2);y=np.array([p['delta_recall_pp'] for p in rr]);lo=np.array([p['CI98_75'][0] for p in rr]);hi=np.array([p['CI98_75'][1] for p in rr]);axs[j].errorbar(x,y,yerr=[y-lo,hi-y],fmt='o',capsize=5);axs[j].axhline(0,color='gray',ls='--');axs[j].set_xticks(x,['Recall@1','Recall@100']);axs[j].set_ylabel('Change vs GT10 (percentage points)');axs[j].set_title(('WebVid' if ds.startswith('webvid') else 'Yandex')+' | L=128');axs[j].grid(alpha=.2)
fig.suptitle('Paired query bootstrap | Bonferroni-adjusted 98.75% intervals');fig.savefig(RUN/'figures/primary_intervals.png',dpi=180);fig.savefig(RUN/'figures/primary_intervals.pdf');plt.close(fig)
dump(RUN/'reviews/analysis_complete.json',dict(status='PASS',decision=status,created_unix=time.time()))
print(json.dumps(dict(status=status,gates=gate,primary=primary),indent=2))
