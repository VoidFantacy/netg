from common import *
threads();resources();check(O/'reviews/prequery_freeze.json');check(O/'reviews/shared_bank_freeze.json');jobs=read(O/'logs/jobs.json');assert len(jobs)==2 and all(j['status']=='COMPLETE' for j in jobs)
start=time.monotonic();points=[];pairs=[];retention=[];failed=[];gates={};verified=0;pop=np.array([i.bit_count() for i in range(1024)],np.int16)
for ds in DS:
 pro=read(O/'inputs'/ds/'provenance.json');gt=np.fromfile(pro['gt_file'],np.int64).reshape(7952,100);rt=dict(np.load(O/'inputs'/ds/'routes.npz'));raw={m:old_raw(ds,m) for m in MODELS};patch=dict(np.load(O/'results'/ds/'missing.npz'));replay=dict(np.load(O/'results'/ds/'baseline_replay.npz'));same({k:v[:128] for k,v in raw['baseline10'].items()},replay)
 for bi,b in enumerate(BANKS):
  a={k:np.empty_like(raw['baseline10'][k]) for k in ['ids','distances','graph_ndc']};a['entries']=rt['exact_entries'][bi]
  for i in range(7952):
   mi=int(rt['source_method'][bi,i]);ix=int(rt['source_index'][bi,i]);s=patch if mi==len(MODELS) else raw[MODELS[mi]]
   if mi==len(MODELS):assert int(patch['rows'][ix])==i
   else:assert ix==i
   assert np.array_equal(a['entries'][i],s['entries'][ix])
   for k in ['ids','distances','graph_ndc']:a[k][i]=s[k][ix]
  a['hits'],a['mask']=score(a['ids'],gt);save(O/'results'/ds/('exact_'+b+'.npz'),source_rows=rt['source_rows'],source_method=rt['source_method'][bi],source_index=rt['source_index'][bi],**a);raw['exact_'+b]=a
 for m,a in raw.items():
  hits,mask=score(a['ids'],gt);assert np.array_equal(hits,a['hits']) and np.array_equal(mask,a['mask']);verified+=7952
 for name in ['baseline_replay','missing']:
  a=dict(np.load(O/'results'/ds/(name+'.npz')));b=dict(np.load(O/'results'/ds/(name+'_reference.npz')));same(b,{k:a[k][:len(b['ids'])] for k in ['ids','distances','graph_ndc']})
 comparisons=[('exact_'+b,ref) for b in BANKS for ref in ['exact_P','exact_mode','baseline10','compact10',b]];local={}
 for split,sl in [('all',slice(0,7952)),('first_half',slice(0,3976)),('second_half',slice(3976,7952))]:
  n=sl.stop-sl.start
  for m,a in raw.items():points.append(dict(dataset=ds,model=m,split=split,n=n,total_hits=int(a['hits'][sl].sum()),recall=float(a['hits'][sl].mean()/10),failures=int((a['hits'][sl]==0).sum()),failure_rate=float((a['hits'][sl]==0).mean()),mean_graph_NDC=float(a['graph_ndc'][sl].mean()),QPS=None))
  for cand,ref in comparisons:
   a=raw[cand];b=raw[ref];ah=a['hits'][sl].astype(int);bh=b['hits'][sl].astype(int);de=ah-bh;mg=pop[(a['mask'][sl]&~b['mask'][sl])&1023];ml=pop[(b['mask'][sl]&~a['mask'][sl])&1023];resc=(bh==0)&(ah>0);new=(bh>0)&(ah==0)
   rec=dict(dataset=ds,candidate=cand,reference=ref,split=split,n=n,net_hits=int(de.sum()),recall_delta_pp=float(de.mean()*10),positive_query_hits=int(np.maximum(de,0).sum()),negative_query_hits=int(np.maximum(-de,0).sum()),member_gained=int(mg.sum()),member_lost=int(ml.sum()),rescued=int(resc.sum()),new_failures=int(new.sum()),failure_change=int(new.sum()-resc.sum()),graph_NDC_change_pct=float((a['graph_ndc'][sl].mean()/b['graph_ndc'][sl].mean()-1)*100));assert rec['net_hits']==rec['member_gained']-rec['member_lost']==rec['positive_query_hits']-rec['negative_query_hits'];pairs.append(rec);local[(cand,ref,split)]=rec
 for bank in BANKS:
  cand='exact_'+bank;rules={}
  for ref in ['exact_P','compact10']:
   x=local[(cand,ref,'all')];rules.update({ref+'_positive':x['net_hits']>0,ref+'_halves':all(local[(cand,ref,s)]['net_hits']>=0 for s in ['first_half','second_half']),ref+'_failure':x['failure_change']<=0,ref+'_graph_cost':x['graph_NDC_change_pct']<=1})
  rules['own_approx_nonnegative']=local[(cand,bank,'all')]['net_hits']>=0;gates[ds+'/'+bank]=dict(passed=all(rules.values()),rules=rules)
  p=raw['baseline10']['hits'].astype(int);old=raw['compact10']['hits'].astype(int)-p;new=raw[cand]['hits'].astype(int)-p;op=np.maximum(old,0);np_=np.maximum(new,0);on=np.maximum(-old,0);nn=np.maximum(-new,0)
  v=dict(dataset=ds,model=cand,old_gain=int(op.sum()),retained_gain=int(np.minimum(op,np_).sum()),forgone_gain=int(np.maximum(op-np_,0).sum()),new_or_amplified_gain=int(np.maximum(np_-op,0).sum()),old_loss=int(on.sum()),avoided_loss=int(np.maximum(on-nn,0).sum()),new_or_amplified_loss=int(np.maximum(nn-on,0).sum()));assert -v['forgone_gain']+v['new_or_amplified_gain']+v['avoided_loss']-v['new_or_amplified_loss']==int(new.sum()-old.sum());retention.append(v)
  print(ds,bank,[(ref,local[(cand,ref,'all')]['net_hits'],local[(cand,ref,'all')]['failure_change']) for ref in ['exact_P','exact_mode','compact10',bank]],'gate',gates[ds+'/'+bank]['passed'],flush=True)
 # Complete union; include all-zero across all ten methods, not only transitions.
 hs=np.stack([raw[m]['hits'] for m in raw]);zero=hs==0;union=np.any(zero,axis=0);changed=np.any(zero!=zero[0],axis=0)
 for i in np.flatnonzero(union):
  rec=dict(dataset=ds,namespace=pro['namespace'],source_row=int(rt['source_rows'][i]),changed_zero_status=bool(changed[i]),gt10=' '.join(map(str,gt[i,:10])))
  for m,a in raw.items():rec[m+'_hits']=int(a['hits'][i]);rec[m+'_entries']=' '.join(map(str,a['entries'][i]));rec[m+'_ids']=' '.join(map(str,a['ids'][i]))
  failed.append(rec)
for name,data in [('points',points),('paired',pairs),('gain_retention',retention),('failure_queries',failed)]:table(O/'results'/(name+'.csv'),data)
candidates=[]
for bank in ['joint10','conditional10','target10']:
 if any(gates[ds+'/'+bank]['passed'] for ds in DS):
  x=[p for p in pairs if p['candidate']=='exact_'+bank and p['reference']=='compact10' and p['split']=='all'];candidates.append((sum(p['net_hits'] for p in x),-sum(p['failure_change'] for p in x),-['joint10','conditional10','target10'].index(bank),bank))
chosen=max(candidates)[3] if candidates else None
dump(O/'results/gate.json',dict(status='COMPLETE_TARGET_EXACT_DIAGNOSIS',datasets_banks=gates,bank_for_new_approximation=chosen,not_performance_GO=True))
cov=read(O/'reviews/cache_coverage.json')['datasets'];cost=dict(NSG=sum(j['native']['NSG'] for j in jobs),HNSW=0,builds=0,new_training=0,new_GT=0,compile_seconds=0,logical_exact_outputs=47712,old_reused=sum(x['old_reused'] for x in cov),missing_unique=sum(x['missing_unique'] for x in cov),new_aliases=sum(x['new_aliases'] for x in cov),baseline_replay_NSG=512,reference_NSG=64,native_elapsed_seconds=sum(j['elapsed_seconds'] for j in jobs),load_seconds=sum(j['load_seconds'] for j in jobs),rank_prepare_seconds=read(O/'reviews/ranking_verification.json')['seconds'],analysis_seconds=time.monotonic()-start,QPS=None,inherited_GT_and_profiles_cost=None)
assert cost['NSG']==read(O/'config.locked.json')['NSG_expected'];dump(O/'results/cost.json',cost);dump(O/'reviews/verification.json',dict(status='PASS',set_scored_outputs=verified,source_collision_checks=sum(x['old_collisions'] for x in cov),baseline_replay_rows=256,original_kernel_reference_rows=64,cache_key_reconstruction_rows=47712,paired_member_net_identities=len(pairs),failure_union_queries=len(failed),changed_failure_queries=sum(x['changed_zero_status'] for x in failed),actual_threads=[j['native']['actual_threads'] for j in jobs],all_sources_unchanged=True));dump(O/'state.json',dict(status='COMPLETE_TARGET_EXACT_DIAGNOSIS',NSG=cost['NSG'],HNSW=0,builds=0,bank_for_new_approximation=chosen,day_goal_complete=False));resources()
