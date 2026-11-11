from common import *
import array,statistics,struct,gzip,collections
t=time.perf_counter();P=[];cache={};old=list(csv.DictReader((OLD/'analysis/points.csv').open()));oldmap={(x['dataset'],x['window'],int(x['K']),int(x['L']),x['method']):x for x in old};work=0;wall=0;oldparity=0;mappedparity=0;candidate_event_queries=0
for ds in DS:
 for w in ['A','B']:
  c=read(R/'configs'/f'{ds}.{w}.json');root=Path(c['output_dir']);n=c['queries']['n'];g=np.fromfile(c['test_gt']['path'],'<i4').reshape(n,100);records=read(root/'complete.json')['results'];packets={}
  for rec in records:
   K,L,m=rec['K'],rec['L'],rec['method'];d=Path(rec['result_dir']);ids=np.fromfile(d/'raw/ids.i32','<i4').reshape(n,K);dist=np.fromfile(d/'raw/distances.f32','<f4').reshape(n,K);hit=np.array([len(set(map(int,a))&set(map(int,b)))for a,b in zip(ids,g[:,:K])],dtype=np.int16)
   # stdlib array/set independently repeats integer quality and byte packet checks.
   aa=array.array('i');aa.frombytes((d/'raw/ids.i32').read_bytes());gg=array.array('i');gg.frombytes(Path(c['test_gt']['path']).read_bytes());hh=[]
   for i in range(n):
    rr=set(aa[i*K:(i+1)*K]);assert len(rr)==K and all(0<=x<c['base']['n']for x in rr);hh.append(len(rr&set(gg[i*100:i*100+K])))
   assert np.array_equal(hit,hh)
   h=hashlib.sha256();h.update(struct.pack('<QQ',n,K))
   for filename in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:h.update((d/'raw'/filename).read_bytes())
   h.update(bytes(n*8));h.update(bytes(n*8));rounds=[read(d/f'round{i}.json')for i in range(3)];assert all(a['packet_sha256']==h.hexdigest()and a['threads']==1 for a in rounds)
   assert all(np.isclose(a['qps'],n/a['wall_seconds'],rtol=1e-13)for a in rounds);qps=n/statistics.median(a['wall_seconds']for a in rounds);assert np.isclose(qps,rec['qps'],rtol=1e-13)
   if rec['old_packet_parity']:assert h.hexdigest()==read(OLD/f'storage/results/{ds}/{w}/k{K}/{m}_L{L}/round0.json')['packet_sha256'];oldparity+=1
   if m=='OPT-B32' and not rec['old_packet_parity']:
    mapped=OLD/f'storage/results/{ds}/{w}/k{K}/B32_L{L}/round0.json'
    if mapped.exists():assert h.hexdigest()==read(mapped)['packet_sha256'];mappedparity+=1
   p=dict(dataset=ds,window=w,K=K,L=L,method=m,n=n,hits=int(hit.sum()),recall_pct=float(hit.mean()*100/K),failed_lt10=int((hit<10).sum())if K==100 else '',qps=qps,mean_us=1e6/qps,qps_min=min(a['qps']for a in rounds),qps_max=max(a['qps']for a in rounds),old_packet_parity=rec['old_packet_parity'],packet_sha=h.hexdigest(),result_dir=str(d))
   P.append(p);packets[K,L,m]=(ids,dist,hit);cache[ds,w,K,L,m]=(ids,dist,hit);wall+=sum(a['wall_seconds']for a in rounds);work+=1
  # Fresh candidate events get a second full-sort check; original main packets are sealed E195 bytes.
  for p in [x for x in P if x['dataset']==ds and x['window']==w and x['method']not in ['GT10','OPT-B32']]:
   K,L,m=p['K'],p['L'],p['method'];d=Path(p['result_dir']);orig=OLD/f'storage/results/{ds}/{w}/k{K}/GT10_L{L}/raw';main=np.fromfile(orig/'ids.i32','<i4').reshape(n,K);md=np.fromfile(orig/'distances.f32','<f4').reshape(n,K);ids,dist,_=packets[K,L,m];data=gzip.open(d/'events.bin.gz','rb').read();pos=0
   for i in range(n):
    qi,ne,ns=struct.unpack_from('<III',data,pos);pos+=12;assert qi==i and ne<=480 and ns<=3;e=np.frombuffer(data,dtype=np.dtype([('id','<i4'),('distance','<f4'),('stage','<u4')]),count=ne,offset=pos);pos+=ne*12+ns*4;assert len(set(map(int,e['id'])))==ne and not(set(map(int,e['id']))&set(map(int,main[i])))
    allids=np.concatenate((main[i],e['id']));values=np.concatenate((md[i],e['distance']));order=np.lexsort((np.arange(K+ne),values))[:K];assert np.array_equal(allids[order],ids[i])and np.array_equal(values[order].view('<u4'),dist[i].view('<u4'));candidate_event_queries+=1
   assert pos==len(data)
  print('AUDITED',ds,w,len(records),flush=True)
csvwrite(R/'analysis/points.csv',P)
candidate=[]
for p in [x for x in P if x['method']not in ['GT10','OPT-B32']]:
 ds,w,K,L,m=p['dataset'],p['window'],p['K'],p['L'],p['method'];peers=[x for x in P if(x['dataset'],x['window'],x['K'])==(ds,w,K)];controls=[x for x in peers if x['method']in ['GT10','OPT-B32']];ids,dist,h=cache[ds,w,K,L,m];base=next(x for x in controls if x['method']=='OPT-B32'and x['L']==L);bids,_,bh=cache[ds,w,K,L,'OPT-B32'];gain=h-bh
 eligible=[x for x in controls if x['hits']>=p['hits']];cover=[x for x in eligible if x['qps']>=p['qps']and(x['hits']>p['hits']or x['qps']>p['qps'])];range_cover=[x for x in cover if x['qps_min']>=p['qps_max']];best=max(eligible,key=lambda x:x['qps'])if eligible else None
 within=[x for x in controls if x['qps']>=p['qps']];budget=max(within,key=lambda x:(x['hits'],x['qps']))if within else None;delta=h-cache[ds,w,K,budget['L'],budget['method']][2]if budget else None
 rng=np.random.default_rng(19620261101);boot=rng.integers(len(h),size=(1000,len(h)));ci=np.percentile(delta[boot].mean(1)*100/K,[2.5,97.5])if delta is not None else ['',''];gc=np.percentile(gain[boot].mean(1)*100/K,[2.5,97.5])
 g=np.fromfile(read(R/'configs'/f'{ds}.{w}.json')['test_gt']['path'],'<i4').reshape(len(h),100);rescue=loss=budget_rescue=budget_loss=0
 for i in range(len(h)):
  G=set(map(int,g[i,:K]));F=set(map(int,ids[i]))&G;B=set(map(int,bids[i]))&G;rescue+=len(F-B);loss+=len(B-F)
  if budget:
   Q=set(map(int,cache[ds,w,K,budget['L'],budget['method']][0][i]))&G;budget_rescue+=len(F-Q);budget_loss+=len(Q-F)
 others=[x for x in peers if x['hits']>=p['hits']and x['qps']>=p['qps']and(x['hits']>p['hits']or x['qps']>p['qps'])]
 dominates=[x for x in controls if p['hits']>=x['hits'] and p['qps']>=x['qps'] and (p['hits']>x['hits'] or p['qps']>x['qps'])]
 strict=[x for x in dominates if p['hits']>x['hits'] and p['qps']>x['qps']]
 proof=max(dominates,key=lambda x:(x['hits'],x['qps']))if dominates else None
 r=dict(dataset=ds,window=w,K=K,L=L,method=m,n=len(h),recall_pct=p['recall_pct'],qps=p['qps'],mean_us=p['mean_us'],gain_vs_same_L_OPT_B32_pp=float(gain.mean()*100/K),gain_ci_lo=float(gc[0]),gain_ci_hi=float(gc[1]),rescued=rescue,lost=loss,qps_change_vs_same_L_OPT_B32_pct=(p['qps']/base['qps']-1)*100,GT_or_OPT_covers=';'.join(f"{a['method']}@{a['L']}"for a in cover),range_cover=';'.join(f"{a['method']}@{a['L']}"for a in range_cover),new_global_covers=';'.join(f"{a['method']}@{a['L']}"for a in others),quality_threshold_method=best['method']if best else '',quality_threshold_L=best['L']if best else '',quality_threshold_recall_pct=best['recall_pct']if best else '',quality_threshold_qps=best['qps']if best else '',threshold_speed_pct=(p['qps']/best['qps']-1)*100 if best else '',same_cost_method=budget['method']if budget else '',same_cost_L=budget['L']if budget else '',same_cost_control_recall_pct=budget['recall_pct']if budget else '',same_cost_control_qps=budget['qps']if budget else '',same_cost_recall_delta_pp=float(delta.mean()*100/K)if budget else '',same_cost_ci_lo=float(ci[0])if budget else '',same_cost_ci_hi=float(ci[1])if budget else '')
 r.update(same_cost_rescued=budget_rescue if budget else '',same_cost_lost=budget_loss if budget else '',same_cost_improved_queries=int((delta>0).sum())if budget else '',same_cost_harmed_queries=int((delta<0).sum())if budget else '',same_cost_control_failed_lt10=int((cache[ds,w,K,budget['L'],budget['method']][2]<10).sum())if budget and K==100 else '',same_cost_failed_escaped=int(((cache[ds,w,K,budget['L'],budget['method']][2]<10)&(h>=10)).sum())if budget and K==100 else '',same_cost_new_failure=int(((cache[ds,w,K,budget['L'],budget['method']][2]>=10)&(h<10)).sum())if budget and K==100 else '')
 if budget:assert budget_rescue-budget_loss==int(delta.sum())
 r.update(candidate_dominates_controls=';'.join(f"{x['method']}@{x['L']}"for x in dominates),strict_double_controls=';'.join(f"{x['method']}@{x['L']}"for x in strict),proof_control_method=proof['method']if proof else '',proof_control_L=proof['L']if proof else '',proof_control_recall_pct=proof['recall_pct']if proof else '',proof_control_qps=proof['qps']if proof else '')
 candidate.append(r)
csvwrite(R/'analysis/candidate_comparisons.csv',candidate);stable=[]
for key in dict.fromkeys((x['dataset'],x['K'],x['L'],x['method'])for x in candidate):
 aa=sorted([x for x in candidate if(x['dataset'],x['K'],x['L'],x['method'])==key],key=lambda x:x['window']);assert len(aa)==2;a,b=aa
 stable.append(dict(dataset=key[0],K=key[1],L=key[2],method=key[3],A_covered=bool(a['GT_or_OPT_covers']),B_covered=bool(b['GT_or_OPT_covers']),both_not_covered=not a['GT_or_OPT_covers']and not b['GT_or_OPT_covers'],both_new_global_not_covered=not a['new_global_covers']and not b['new_global_covers'],A_same_cost_delta_pp=a['same_cost_recall_delta_pp'],B_same_cost_delta_pp=b['same_cost_recall_delta_pp'],A_threshold_speed_pct=a['threshold_speed_pct'],B_threshold_speed_pct=b['threshold_speed_pct'],both_joint_dominance=not a['GT_or_OPT_covers'] and not b['GT_or_OPT_covers'] and bool(a['candidate_dominates_controls']) and bool(b['candidate_dominates_controls']),both_strict_double=not a['GT_or_OPT_covers'] and not b['GT_or_OPT_covers'] and bool(a['strict_double_controls']) and bool(b['strict_double_controls']),A_range_covered=bool(a['range_cover']),B_range_covered=bool(b['range_cover'])))
csvwrite(R/'analysis/stability.csv',stable);summary=[]
for ds in DS:
 pp=[a for a in candidate if a['dataset']==ds];ss=[a for a in stable if a['dataset']==ds];summary.append(dict(dataset=ds,candidate_window_points=len(pp),covered_window_points=sum(bool(a['GT_or_OPT_covers'])for a in pp),range_covered_points=sum(bool(a['range_cover'])for a in pp),configurations=len(ss),both_not_covered=sum(a['both_not_covered']for a in ss),both_new_global_not_covered=sum(a['both_new_global_not_covered']for a in ss),both_joint_dominance=sum(a['both_joint_dominance']for a in ss),both_strict_double=sum(a['both_strict_double']for a in ss)))
csvwrite(R/'analysis/dataset_summary.csv',summary)
dump(R/'analysis/validation.json',dict(status='PASS_E196_INTEGER_HASH_WALL_AND_FULL_SORT_AUDIT',points=work,batches=work*3,original_E195_packet_parity_points=oldparity,equivalent_original_B32_packet_checks=mappedparity,original_candidate_window_points=len(candidate),candidate_event_queries=candidate_event_queries,formal_batch_wall_seconds=wall,seconds=time.perf_counter()-t,default_changed=False))
print('E196_ANALYSIS_COMPLETE',work,len(candidate),flush=True)
