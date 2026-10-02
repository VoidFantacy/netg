from common import *
import pandas as pd,resource

assert not (O/'results/diagnosis.json').exists();start=time.time()
dump(O/'reviews/analysis_inputs.json',dict(files=[ident(p) for p in sorted((O/'src').glob('*.py'))]+[ident(O/'protocol.md')],created_at=time.time()))
steps=[];actions=[];queries=[];centers=[];endpoints=[];matched=[];matching_groups=[];runs=[];geometry=[];verified_outputs=0
for ds in DS:
 c=read(E/'inputs'/ds/'config.json')
 for key in ['P','basis','queries_file','gt_file','row_ids']:assert Path(c[key]).is_relative_to(E),c[key]
 gt=np.fromfile(c['gt_file'],np.int64).reshape(5120,100);source_rows=np.fromfile(c['row_ids'],np.int64);base=dict(np.load(E/'results'/ds/'baseline.npz'));bh=hit(base['ids'],gt);assert np.array_equal(bh,base['hits'])
 bc=base['route_ndc'].astype(float)+base['graph_ndc'];p=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim']);b=np.fromfile(c['basis'],np.float64).reshape(c['dim'],16)
 q=np.fromfile(c['queries_file'],np.float32).reshape(5120,c['dim'])[:4096].astype(float);q/=np.linalg.norm(q,axis=1)[:,None]
 geometry.append(dict(dataset=ds,query_energy_in_B=float(np.square(q@b).sum(1).mean()),profile_energy_in_B=float((np.square(p.astype(float)@b).sum(1)/np.square(p.astype(float)).sum(1)).mean()),B_rank=int(np.linalg.matrix_rank(b)),PB_rank=int(np.linalg.matrix_rank(p.astype(float)@b))))
 for arm in ARMS:
  for seed in SEEDS:
   folder=E/'models'/ds/f'{arm}_{seed}';model=read(folder/'model.json');ckmeta={x['step']:x for x in read(folder/'checkpoints.json')};cps={s:dict(np.load(folder/'checkpoints'/f'{s:04}.npz')) for s in ckmeta}
   key=dict(dataset=ds,arm=arm,seed=seed);runsteps=[];prevg=None;prevupdate=None
   acc={k:np.zeros(4096,dtype=float) for k in ['batches','observations','entry_changes','hit_changes','discriminating_batches','hits_gained','hits_lost','gradient_norm_sum']}
   for step in range(1,201):
    assert time.time()-start<600 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<4*(1<<20)
    a=dict(np.load(folder/'trajectory'/f'{step:04}.npz'));rows=a['rows'];h=hit(a['ids'],gt[rows]);verified_outputs+=h.size;dh=h-bh[rows]
    cost=-.1*((a['route_ndc'].astype(float)+a['graph_ndc'])/bc[rows]-1);failure=-.1*((h==0).astype(float)-(bh[rows]==0).astype(float));u=dh+cost+failure
    reward=u.mean(1)-a['drift'];assert np.max(np.abs(reward-a['rewards']))<1e-13
    M=mat(arm,a['eps']);ghq=M@dh;guq=M@u;gh=ghq.mean(1);gc=M@cost.mean(1);gf=M@failure.mean(1);gr=M@(-a['drift']);gu=guq.mean(1);g=gu+gr
    assert np.max(np.abs(g-a['gradient']))<1e-12
    changed=np.any(a['entries']!=base['entries'][rows],axis=2);discriminates=np.ptp(h,axis=0)>0
    same=~changed
    assert np.array_equal(a['ids'][same],np.broadcast_to(base['ids'][rows],a['ids'].shape)[same]);assert np.array_equal(a['graph_ndc'][same],np.broadcast_to(base['graph_ndc'][rows],a['graph_ndc'].shape)[same])
    rng=np.random.default_rng(seed+step*10000);half=[];half_hits=[]
    for _ in range(16):
     ii=rng.permutation(128);half.append(cosine(guq[:,ii[:64]].mean(1),guq[:,ii[64:]].mean(1)));half_hits.append(cosine(ghq[:,ii[:64]].mean(1),ghq[:,ii[64:]].mean(1)))
    vmean=float(np.square(guq-gu[:,None]).sum()/127/128*(1-128/4096));snr=float(np.dot(gu,gu)/vmean-1) if vmean>1e-24 else None
    qnorm=np.linalg.norm(ghq,axis=0);big=int(np.argmax(qnorm));drop=cosine(gu,gu-guq[:,big]/128);up=a['mu_after']-a['mu_before']
    rec=dict(**key,step=step,block=(step-1)//20,mean_reward=float(reward.mean()),mean_hit_delta=float(dh.mean()),mean_cost_term=float(cost.mean()),mean_failure_term=float(failure.mean()),mean_drift_penalty=float(-a['drift'].mean()),
     reward_sd=float(reward.std(ddof=1)),hit_action_sd=float(dh.mean(1).std(ddof=1)),cost_action_sd=float(cost.mean(1).std(ddof=1)),failure_action_sd=float(failure.mean(1).std(ddof=1)),drift_action_sd=float(a['drift'].std(ddof=1)),
     entry_changed_observations=int(changed.sum()),hit_changed_observations=int((dh!=0).sum()),discriminating_queries=int(discriminates.sum()),equal_action_mean_hits=bool(np.ptp(dh.mean(1))==0),
     hit_gradient_norm=float(np.linalg.norm(gh)),cost_gradient_norm=float(np.linalg.norm(gc)),failure_gradient_norm=float(np.linalg.norm(gf)),drift_gradient_norm=float(np.linalg.norm(gr)),data_gradient_norm=float(np.linalg.norm(gu)),total_gradient_norm=float(np.linalg.norm(g)),
     auxiliary_dominates_hits=bool(np.linalg.norm(gc+gf+gr)>np.linalg.norm(gh)),cos_total_hits=cosine(g,gh),cos_adjacent_gradients=None if prevg is None else cosine(g,prevg),
     split_query_cosine=median(half),split_query_hit_cosine=median(half_hits),valid_hit_halves=sum(x is not None for x in half_hits),query_gradient_variance=vmean,conditional_query_snr_estimate=snr,
     largest_query_hit_gradient_share=None if qnorm.sum()==0 else float(qnorm.max()/qnorm.sum()),cos_after_drop_largest_query=drop,
     optimizer_update_norm=float(np.linalg.norm(up)),cos_update_current_hits=cosine(up,gh),cos_adjacent_updates=None if prevupdate is None else cosine(up,prevupdate),
     gradient_clipped=bool(np.linalg.norm(g)>1),mu_max_abs=float(np.abs(a['mu_after']).max()),mu_at_bound_count=int((np.abs(a['mu_after'])>=2-1e-12).sum()),action_tanh_saturated_pct=float((np.abs(np.tanh(a['actions']))>.95).mean()*100))
    steps.append(rec);runsteps.append(rec);prevg=g;prevupdate=up
    for j in range(8):actions.append(dict(**key,step=step,action=j,hits_delta_mean=float(dh[j].mean()),cost_term=float(cost[j].mean()),failure_term=float(failure[j].mean()),drift_penalty=float(-a['drift'][j]),reward=float(reward[j]),entry_changed_queries=int(changed[j].sum()),hit_changed_queries=int((dh[j]!=0).sum())))
    for name,values in [('batches',np.ones(128)),('observations',np.full(128,8)),('entry_changes',changed.sum(0)),('hit_changes',(dh!=0).sum(0)),('discriminating_batches',discriminates),('hits_gained',np.maximum(dh,0).sum(0)),('hits_lost',np.maximum(-dh,0).sum(0)),('gradient_norm_sum',qnorm)]:acc[name][rows]+=values
    s=step-1
    if s in cps:
     center=cps[s];assert np.array_equal(center['mu'],a['mu_before']);ii=np.flatnonzero(rows<512);rr=rows[ii];ch=hit(center['ids'][rr],gt[rr]);cu=ch-bh[rr]-.1*((center['route_ndc'][rr].astype(float)+center['graph_ndc'][rr])/bc[rr]-1)-.1*((ch==0).astype(float)-(bh[rr]==0).astype(float))
     gap=(h[:,ii].mean(0)-ch)*10;rewardgap=u[:,ii].mean(0)-a['drift'].mean()-(cu-ckmeta[s]['drift'])
     matching_groups.append(dict(**key,center_step=s,action_step=step,queries=len(rr),gap_sum_pp=float(gap.sum()),mean_recall_gap_pp=float(gap.mean()),mean_reward_gap=float(rewardgap.mean()),same_mu=True))
     for j,row in enumerate(rr):matched.append(dict(**key,center_step=s,query_row=int(source_rows[row]),query_index=int(row),deterministic_hits=int(ch[j]),sample_mean_hits=float(h[:,ii[j]].mean()),sample_min_hits=int(h[:,ii[j]].min()),sample_max_hits=int(h[:,ii[j]].max()),delta_recall_pp=float(gap[j]),reward_gap=float(rewardgap[j])))
   totalqgrad=acc['gradient_norm_sum'].sum();top=np.sort(acc['gradient_norm_sum'])[::-1]
   rr=dict(**key,updates=200,action_query_observations=int(acc['observations'].sum()),query_batch_observations=int(acc['batches'].sum()),unique_train_rows_seen=int((acc['batches']>0).sum()),min_query_batches=int(acc['batches'].min()),median_query_batches=float(np.median(acc['batches'])),max_query_batches=int(acc['batches'].max()),
    entry_change_pct=float(acc['entry_changes'].sum()/acc['observations'].sum()*100),hit_change_pct=float(acc['hit_changes'].sum()/acc['observations'].sum()*100),discriminating_query_pct=float(acc['discriminating_batches'].sum()/acc['batches'].sum()*100),
    median_discriminating_queries=median([x['discriminating_queries'] for x in runsteps]),zero_discrimination_step_pct=float(np.mean([x['discriminating_queries']==0 for x in runsteps])*100),at_most_one_discriminating_step_pct=float(np.mean([x['discriminating_queries']<=1 for x in runsteps])*100),
    equal_mean_hits_step_pct=float(np.mean([x['equal_action_mean_hits'] for x in runsteps])*100),auxiliary_dominates_hits_pct=float(np.mean([x['auxiliary_dominates_hits'] for x in runsteps])*100),
    split_query_cosine_median=median([x['split_query_cosine'] for x in runsteps]),split_query_hit_cosine_median=median([x['split_query_hit_cosine'] for x in runsteps]),conditional_query_snr_median=median([x['conditional_query_snr_estimate'] for x in runsteps]),
    largest_query_gradient_share_median=median([x['largest_query_hit_gradient_share'] for x in runsteps]),top10_query_gradient_share=float(top[:10].sum()/totalqgrad),top1pct_query_gradient_share=float(top[:41].sum()/totalqgrad),
    selected_step=model['selected_step'],clipped_steps=sum(x['gradient_clipped'] for x in runsteps),max_mu_abs=max(x['mu_max_abs'] for x in runsteps))
   for name in ['hit','cost','failure','drift','data','total']:rr[name+'_gradient_norm_median']=median([x[name+'_gradient_norm'] for x in runsteps])
   for name in ['hit_action_sd','cost_action_sd','failure_action_sd','drift_action_sd','cos_adjacent_gradients','cos_after_drop_largest_query','cos_update_current_hits']:rr[name+'_median']=median([x[name] for x in runsteps])
   runs.append(rr)
   for i in range(4096):queries.append(dict(**key,query_row=int(source_rows[i]),query_index=i,baseline_hits=int(bh[i]),**{k:float(v[i]) for k,v in acc.items()}))
   for s,center in cps.items():
    for tag,sl,rows in [('train',slice(0,512),np.arange(512)),('monitor',slice(512,None),np.arange(4096,5120))]:
     ids=center['ids'][sl];h=hit(ids,gt[rows]);verified_outputs+=len(h);delta=h-bh[rows];change=np.any(center['entries'][sl]!=base['entries'][rows],axis=1);absd=np.sort(np.abs(delta))[::-1];totalabs=int(absd.sum())
     u=delta-.1*((center['route_ndc'][sl].astype(float)+center['graph_ndc'][sl])/bc[rows]-1)-.1*((h==0).astype(float)-(bh[rows]==0).astype(float))
     assert abs(delta.mean()*10-ckmeta[s][tag]['delta_recall_pp'])<1e-12 and abs(u.mean()-ckmeta[s][tag]['mean_U'])<1e-13
     centers.append(dict(**key,step=s,split=tag,queries=len(rows),delta_recall_pp=float(delta.mean()*10),mean_U=float(u.mean()),reward=float(u.mean()-ckmeta[s]['drift']),entry_changed=int(change.sum()),hit_changed=int((delta!=0).sum()),helped=int((delta>0).sum()),harmed=int((delta<0).sum()),hits_gained=int(delta[delta>0].sum()),hits_lost=int(-delta[delta<0].sum()),largest_query_abs_hit_share=None if totalabs==0 else float(absd[0]/totalabs),top5_queries_abs_hit_share=None if totalabs==0 else float(absd[:5].sum()/totalabs),selected=s==model['selected_step'],last=s==200))
     if s in [model['selected_step'],200]:
      for i,row in enumerate(rows):endpoints.append(dict(**key,step=s,endpoint='selected' if s==model['selected_step'] else 'last',split=tag,query_row=int(source_rows[row]),baseline_hits=int(bh[row]),hits=int(h[i]),delta_hits=int(delta[i]),entry_changed=bool(change[i]),U=float(u[i])))
   print('DIAGNOSED',ds,arm,seed,'median discriminating queries',rr['median_discriminating_queries'],'split cosine',rr['split_query_cosine_median'],flush=True)

tables=dict(steps=steps,actions=actions,query_exposure=queries,centers=centers,endpoint_queries=endpoints,matched_queries=matched,matched_groups=matching_groups,runs=runs,geometry=geometry)
for name,rows in tables.items():pd.DataFrame(rows).to_csv(O/'results'/f'{name}.csv',index=False)
dump(O/'results/diagnosis.json',dict(status='ANALYSIS_COMPLETE',runs=runs,geometry=geometry,matched_groups=matching_groups,verified_raw_outputs=verified_outputs,zero_new_search=True,analysis_seconds=time.time()-start))
dump(O/'reviews/analysis_verification.json',dict(status='PASS',rewards_recomputed=12800,gradients_decomposed=1600,raw_query_outputs_scored=verified_outputs,centers_scored=len(centers),same_entries_identical_NSG=True,same_mu_matched_groups=len(matching_groups),same_mu_matched_query_records=len(matched),actual_process_threads=int(next(x.split(':')[1] for x in Path('/proc/self/status').read_text().splitlines() if x.startswith('Threads:'))),peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,seconds=time.time()-start))
print('ANALYSIS_COMPLETE',len(steps),'steps',len(matched),'matched query records',flush=True)
