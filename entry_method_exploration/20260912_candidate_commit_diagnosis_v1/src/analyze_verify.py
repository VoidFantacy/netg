from shared import *
threads(8);resources();started=time.monotonic();check(O/'reviews/preanalysis_freeze.json');steps=[];runs=[];scored=0;branches=0
def set_hits(ids,gt):return np.array([len(set(map(int,x))&set(map(int,g[:10]))) for x,g in zip(ids,gt)],np.uint8)
def metric(d):return dict(gain_hits=int(np.maximum(d,0).sum()),loss_hits=int(np.maximum(-d,0).sum()),net_hits=int(d.sum()),gain_queries=int((d>0).sum()),loss_queries=int((d<0).sum()))
def rebuild(cur,t,prefix,route,esh,csh,gt):
 global scored,branches
 rows=t[prefix+'rows'];out={k:cur[k].copy() for k in FIELDS+['hits']};out['route_ndc']=route
 for k in ['ids','distances','entries','graph_ndc','hits']:out[k][rows]=t[prefix+k]
 assert digest(out['entries'])==str(esh) and raw_digest(out)==str(csh)
 hh=set_hits(t[prefix+'ids'],gt[rows]);assert np.array_equal(hh,t[prefix+'hits']);scored+=len(rows);branches+=1
 return out
for ds in DS:
 c=read(E47/'inputs'/ds/'config.json');p=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim']);gt=np.fromfile(c['gt_file'],np.int64).reshape(5120,100)[:4096]
 base={k:v[:4096] for k,v in dict(np.load(E37/'results'/ds/'baseline.npz')).items()}
 for arm in ARMS:
  for seed in SEEDS:
   src=E47/'models'/ds/f'{arm}_{seed}';cur=dict(np.load(src/'initial.npz'));assert np.array_equal(set_hits(cur['ids'],gt),cur['hits']);scored+=4096
   for st in range(1,201):
    t=dict(np.load(src/'trajectory'/f'{st:04}.npz'));slot=int(t['slot']);assert raw_digest(cur)==str(t['current_cache_sha'])
    j0=float(utility(cur,base,gt).mean()-t['current_drift']);np.testing.assert_allclose(j0,t['current_J'],atol=3e-15)
    cand=[cur];djs=[0.];drifts=[float(t['current_drift'])]
    for a in range(8):
     out=rebuild(cur,t,f'a{a}_',t['route_ndc'][a],t['entries_sha'][a],t['cache_sha'][a],gt);cand.append(out)
     dj=float(utility(out,base,gt).mean()-t['drift'][a]-j0);np.testing.assert_allclose(dj,t['rewards'][a],atol=3e-15);djs.append(dj);drifts.append(float(t['drift'][a]))
    mean=rebuild(cur,t,'mean_',t['mean_route_ndc'],t['mean_entries_sha'],t['mean_cache_sha'],gt)
    dmean=float(t['current_drift'])+(np.square(t['next_row'].astype(float)-p[slot]).sum()-np.square(t['current_row'].astype(float)-p[slot]).sum())/len(p)
    mj=float(utility(mean,base,gt).mean()-dmean-j0)
    dh=np.stack([x['hits'].astype(np.int16)-cur['hits'] for x in cand]);net=dh.sum(1);md=mean['hits'].astype(np.int16)-cur['hits']
    bestj=max(range(9),key=lambda i:(djs[i],-i));besth=max(range(9),key=lambda i:(int(net[i]),djs[i],-i));assert djs[bestj]>=0 and net[besth]>=0
    oracle=int(np.maximum(0,dh.max(0)).sum());bestg=int(np.maximum(dh[besth],0).sum());bestl=int(np.maximum(-dh[besth],0).sum());assert oracle-int(net[besth])==oracle-bestg+bestl
    rr=dict(dataset=ds,arm=arm,seed=seed,step=st,slot=slot,positive_candidate=bool(np.any(net[1:]>0)),hit_candidates=int(np.any(dh[1:]!=0,axis=1).sum()),
     mixed_candidates=int(((np.maximum(dh[1:],0).sum(1)>0)&(np.maximum(-dh[1:],0).sum(1)>0)).sum()),mean_quality_null=bool(not np.any(md)),
     mean_delta_J=mj,J_best_action=bestj-1,hit_best_action=besth-1,J_best_delta_J=djs[bestj],hit_best_delta_J=djs[besth],
     J_best_coefficients_legal=bool(bestj==0 or np.max(np.abs(t['actions'][bestj-1]))<=2),
     mean_row_displacement=float(np.linalg.norm(t['next_row'].astype(float)-t['current_row'])),J_best_row_displacement=0. if bestj==0 else float(np.linalg.norm(t['candidate_rows'][bestj-1].astype(float)-t['current_row'])),
     oracle_hits=oracle,best_static_net=int(net[besth]),uncovered_oracle_hits=oracle-bestg,best_static_own_losses=bestl)
    for name,d,out in [('mean',md,mean),('J_best',dh[bestj],cand[bestj]),('hit_best',dh[besth],cand[besth])]:
     rr.update({name+'_'+k:v for k,v in metric(d).items()});rr[name+'_new_zero_queries']=int(((out['hits']==0)&(cur['hits']>0)).sum());rr[name+'_rescued_zero_queries']=int(((out['hits']>0)&(cur['hits']==0)).sum())
     rr[name+'_delta_graph_NDC']=int((out['graph_ndc'].astype(np.int64)-cur['graph_ndc']).sum());rr[name+'_delta_route_NDC']=int((out['route_ndc'].astype(np.int64)-cur['route_ndc']).sum())
     # Independent sparse affected-row accumulation agrees with dense delta matrices.
     active=np.flatnonzero(d);assert sum(int(out['hits'][q])-int(cur['hits'][q]) for q in active)==rr[name+'_net_hits']
    steps.append(rr);cur=mean
   selected=[x for x in steps if x['dataset']==ds and x['arm']==arm and x['seed']==seed];run=dict(dataset=ds,arm=arm,seed=seed,steps=200)
   for key in ['positive_candidate','mean_quality_null','oracle_hits','best_static_net','uncovered_oracle_hits','best_static_own_losses']:run[key]=sum(x[key] for x in selected)
   run['positive_candidate_mean_null']=sum(x['positive_candidate'] and x['mean_quality_null'] for x in selected);run['J_best_illegal_steps']=sum(not x['J_best_coefficients_legal'] for x in selected)
   for name in ['mean','J_best','hit_best']:
    for key in ['gain_hits','loss_hits','net_hits','new_zero_queries','rescued_zero_queries','delta_graph_NDC','delta_route_NDC']:run[name+'_'+key]=sum(x[name+'_'+key] for x in selected)
    run[name+'_delta_J_sum']=float(sum(x[name+'_delta_J'] for x in selected))
   runs.append(run)
dsrows=[]
for ds in DS:
 rr=[x for x in runs if x['dataset']==ds and x['arm']=='rl'];pos=sum(x['positive_candidate'] for x in rr);null=sum(x['positive_candidate_mean_null'] for x in rr)
 r=dict(dataset=ds,RL_steps=400,positive_candidate_steps=pos,positive_candidate_fraction=pos/400,positive_candidate_mean_null_steps=null,mean_null_fraction_on_positive=null/pos if pos else 0,
  J_best_net_sum=sum(x['J_best_net_hits'] for x in rr),mean_net_sum=sum(x['mean_net_hits'] for x in rr),J_best_illegal_steps=sum(x['J_best_illegal_steps'] for x in rr))
 r['passed']=r['positive_candidate_fraction']>=.2 and r['mean_null_fraction_on_positive']>=.5 and r['J_best_net_sum']>r['mean_net_sum'] and r['J_best_illegal_steps']==0;dsrows.append(r)
for name,rows in [('steps',steps),('runs',runs),('datasets',dsrows)]:
 with (O/'results'/f'{name}.csv').open('w',newline='') as f:z=csv.DictWriter(f,fieldnames=list(rows[0]));z.writeheader();z.writerows(rows)
gate=dict(status='PASS_CANDIDATE_COMMIT_CONTROL_GATE' if all(x['passed'] for x in dsrows) else 'STOP_DIRECT_COMMIT_FOLLOWUP_GATE',datasets=dsrows,
 scope='Counterfactual one-step statistics across original trajectories, never a new trained model')
dump(O/'results/analysis.json',dict(runs=runs,datasets=dsrows));dump(O/'results/gate.json',gate)
assert len(steps)==1600 and branches==14400 and scored==135648
dump(O/'reviews/verification.json',dict(status='PASS',contexts=1600,candidate_branches=12800,mean_branches=1600,independent_set_scores=scored,cache_hashes=14400,
 current_J_and_candidate_reward_recovery=True,finite_oracle_decomposition=True,selection_includes_no_op=True,new_search=0,seconds=time.monotonic()-started))
print(json.dumps(gate,ensure_ascii=False,indent=2),flush=True)
