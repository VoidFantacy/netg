from common import *
from collections import defaultdict

contract();check(O/'reviews/preanalysis_freeze.json');start=time.monotonic()
summaries=[];action_rows=[];query_rows=[];events=[];pair_rows=[];group_rows=[];neighbor_rows=[]
same_entry_checked=0
for ds in DS:
 c,rows,q,gt,source,hubs=inputs(ds);q=q/np.linalg.norm(q,axis=1,keepdims=True)
 similarities=q@q.T
 np.fill_diagonal(similarities,-2.)
 neighbors=np.stack([np.lexsort((rows,-similarities[i]))[:5] for i in range(1024)])
 for i in range(1024):
  for rank,j in enumerate(neighbors[i]):
   neighbor_rows.append(dict(dataset=ds,row=int(rows[i]),neighbor_row=int(rows[j]),rank=rank+1,cosine=float(similarities[i,j])))
 lookup={int(h):i for i,h in enumerate(hubs)}
 base=dict(np.load(E37/'results'/ds/'baseline.npz'));base_total=base['route_ndc'][rows].astype(float)+base['graph_ndc'][rows]
 for name in ['zero','selected']:
  _,_,_,_,_,_,raw,h,w=load_context(ds,name)
  delta=h-h[8];gain=np.maximum(delta,0).sum(1);loss=np.maximum(-delta,0).sum(1);net=delta.sum(1)
  ceiling=delta.max(0);floor=delta.min(0);b=best(net);nb=int(np.argmax(net[:8]))
  masks=np.sum((delta==ceiling)* (1<<np.arange(9))[:,None],axis=0).astype(np.int32)
  improving=np.sum((delta>0)*(1<<np.arange(9))[:,None],axis=0).astype(np.int32)
  all_total=np.stack([x['route_ndc'].astype(float)+x['graph_ndc'] for x in raw])
  u=(h-base['hits'][rows]-.1*(all_total/base_total-1)
       -.1*((h==0).astype(float)-(base['hits'][rows]==0).astype(float)))
  drift=np.array([read(E39/'models'/ds/name/label/'identity.json')['drift'] for label in LABELS])
  du=u-u[8];reward_delta=du.mean(1)-(drift-drift[8])
  saved=dict(np.load(E39/'results'/ds/(name+'_derived.npz')))
  assert np.array_equal(h[:8],saved['hits']) and np.array_equal(h[8],saved['center_hits'])
  assert np.allclose(u[:8],saved['U'],rtol=1e-13,atol=1e-13)
  for a in range(9):
   action_rows.append(dict(dataset=ds,context=name,action=LABELS[a],gross_gain_hits=int(gain[a]),
        loss_hits=int(loss[a]),net_hits=int(net[a]),recall_delta_pp=float(net[a]*10/1024),
        helped_queries=int((delta[a]>0).sum()),harmed_queries=int((delta[a]<0).sum()),
        rescued_zero=int(((h[8]==0)&(h[a]>0)).sum()),new_zero=int(((h[8]>0)&(h[a]==0)).sum()),
        route_NDC_delta_mean=float((raw[a]['route_ndc'].astype(float)-raw[8]['route_ndc']).mean()),
        graph_NDC_delta_mean=float((raw[a]['graph_ndc'].astype(float)-raw[8]['graph_ndc']).mean()),
        mean_U_delta=float(du[a].mean()),drift_delta=float(drift[a]-drift[8]),reward_delta=float(reward_delta[a]),
        first512_net=int(delta[a,:512].sum()),second512_net=int(delta[a,512:].sum())))
  transfers=[]
  for half in [0,1]:
   train=np.arange(half*512,(half+1)*512);other=np.arange((1-half)*512,(2-half)*512)
   winner=best(delta[:,train].sum(1))
   transfers.append(dict(selection_half=half,action=LABELS[winner],selection_net=int(delta[winner,train].sum()),other_net=int(delta[winner,other].sum())))
  ce=raw[8]['entries'];local_events=[]
  for a in range(8):
   ae=raw[a]['entries'];same=np.all(ae==ce,axis=1)
   for k in ['ids','distances','graph_ndc']:
    assert raw[a][k][same].tobytes()==raw[8][k][same].tobytes(),(ds,name,a,k)
   same_entry_checked+=int(same.sum())
   for qi in np.flatnonzero(~same):
    old=sorted(set(map(int,ce[qi]))-set(map(int,ae[qi])));new=sorted(set(map(int,ae[qi]))-set(map(int,ce[qi])))
    keep=sorted(set(map(int,ce[qi]))&set(map(int,ae[qi])))
    old_slots=[lookup[e] for e in old];new_slots=[lookup[e] for e in new]
    old0=w[8][old_slots]@q[qi];new0=w[8][new_slots]@q[qi]
    old1=w[a][old_slots]@q[qi];new1=w[a][new_slots]@q[qi]
    m0=float(new0.min()-old0.max());m1=float(new1.min()-old1.max())
    er=dict(dataset=ds,context=name,action=LABELS[a],qi=int(qi),row=int(rows[qi]),source_row_id=int(source[qi]),
       center_entries=';'.join(map(str,ce[qi])),action_entries=';'.join(map(str,ae[qi])),
       removed=';'.join(map(str,old)),added=';'.join(map(str,new)),kept=';'.join(map(str,keep)),swaps=len(old),
       center_hits=int(h[8,qi]),action_hits=int(h[a,qi]),delta_hits=int(delta[a,qi]),
       route_NDC_delta=int(raw[a]['route_ndc'][qi])-int(raw[8]['route_ndc'][qi]),
       graph_NDC_delta=int(raw[a]['graph_ndc'][qi])-int(raw[8]['graph_ndc'][qi]),
       center_margin=m0,action_margin=m1,margin_delta=m1-m0,margin_crossed=int(m0<=0<m1),
       removed_center_scores=';'.join(map(str,old0)),added_center_scores=';'.join(map(str,new0)),
       removed_action_scores=';'.join(map(str,old1)),added_action_scores=';'.join(map(str,new1)))
    events.append(er);local_events.append(er)
  grouped={}
  for kind in ['single_swap','full_transition','added_hub','removed_hub']:
   groups=defaultdict(list)
   for er in local_events:
    if kind=='single_swap':
     if er['swaps']!=1:continue
     keys=[er['removed']+'>'+er['added']]
    elif kind=='full_transition':keys=[er['center_entries']+'>'+er['action_entries']]
    else:keys=er['added' if kind=='added_hub' else 'removed'].split(';')
    for key in keys:groups[(er['action'],key)].append(er)
   mixed=[]
   for (action,key),ers in groups.items():
    positive=[e for e in ers if e['delta_hits']>0];negative=[e for e in ers if e['delta_hits']<0]
    gr=dict(dataset=ds,context=name,kind=kind,action=action,key=key,events=len(ers),
       unique_queries=len(set(e['row'] for e in ers)),helped=len(positive),harmed=len(negative),
       gross_gain=sum(e['delta_hits'] for e in positive),loss=-sum(e['delta_hits'] for e in negative),
       positive_rows=';'.join(str(e['row']) for e in positive),negative_rows=';'.join(str(e['row']) for e in negative),
       closest_conflict_cosine=None,closest_positive_row=None,closest_negative_row=None)
    if positive and negative:
     candidates=[(float(similarities[x['qi'],y['qi']]),x['row'],y['row']) for x in positive for y in negative]
     # Same action has only one event/query within these groups: no self-pair.
     value,pr,nr=max(candidates)
     gr.update(closest_conflict_cosine=value,closest_positive_row=pr,closest_negative_row=nr);mixed.append(gr)
    group_rows.append(gr)
   grouped[kind]=dict(groups=len(groups),mixed_groups=len(mixed),
       mixed_events=sum(x['events'] for x in mixed),
       most_balanced_examples=sorted(mixed,key=lambda x:(min(x['gross_gain'],x['loss']),x['closest_conflict_cosine']),reverse=True)[:3])
  positive_ids=np.flatnonzero(ceiling>0);near_positive={}
  for qi in positive_ids:
   candidates=positive_ids[positive_ids!=qi]
   near_positive[int(qi)]=set(candidates[np.lexsort((rows[candidates],-similarities[qi,candidates]))[:5]].tolist())
  local_pairs=[]
  for ai,qi in enumerate(positive_ids):
   for qj in positive_ids[ai+1:]:
    pr=dict(dataset=ds,context=name,row_a=int(rows[qi]),row_b=int(rows[qj]),
       query_cosine=float(similarities[qi,qj]),preference_cosine=cos(delta[:8,qi].astype(float),delta[:8,qj].astype(float)),
       max_actions_a=int(masks[qi]),max_actions_b=int(masks[qj]),improving_a=int(improving[qi]),improving_b=int(improving[qj]),
       best_compatible=bool(masks[qi]&masks[qj]),joint_improvement_possible=bool(improving[qi]&improving[qj]),
       nearest5_all=bool(qj in neighbors[qi] or qi in neighbors[qj]),
       nearest5_positive=bool(qj in near_positive[int(qi)] or qi in near_positive[int(qj)]))
    pair_rows.append(pr);local_pairs.append(pr)
  pair_stats={}
  for group,pairs in [('all_positive_pairs',local_pairs),('nearest5_all',[p for p in local_pairs if p['nearest5_all']]),
                      ('nearest5_positive',[p for p in local_pairs if p['nearest5_positive']])]:
   pair_stats[group]=dict(pairs=len(pairs),best_incompatible=sum(not p['best_compatible'] for p in pairs),
      improvement_incompatible=sum(not p['joint_improvement_possible'] for p in pairs),
      median_query_cosine=float(np.median([p['query_cosine'] for p in pairs])) if pairs else None)
  for qi in range(1024):
   query_rows.append(dict(dataset=ds,context=name,row=int(rows[qi]),source_row_id=int(source[qi]),center_hits=int(h[8,qi]),
       best_delta=int(ceiling[qi]),worst_delta=int(floor[qi]),best_action_mask=int(masks[qi]),improving_action_mask=int(improving[qi]),
       bidirectional=bool(ceiling[qi]>0 and floor[qi]<0),actions_help=int((delta[:8,qi]>0).sum()),
       actions_harm=int((delta[:8,qi]<0).sum()),best_static_delta=int(delta[b,qi])))
  event_hit=np.array([er['delta_hits'] for er in local_events]);one=[er for er in local_events if er['swaps']==1]
  s=dict(dataset=ds,context=name,center_recall_pct=float(h[8].mean()*10),
    ceiling_hits=int(ceiling.sum()),ceiling_pp=float(ceiling.sum()*10/1024),positive_queries=len(positive_ids),
    recoverable_residual_fraction=float(ceiling.sum()/(10240-h[8].sum())),
    vulnerable_queries=int((floor<0).sum()),bidirectional_queries=int(((ceiling>0)&(floor<0)).sum()),
    best_static_action=LABELS[b],best_static_net_hits=int(net[b]),best_static_pp=float(net[b]*10/1024),
    best_static_gain=int(gain[b]),best_static_loss=int(loss[b]),
    best_static_capture=float(net[b]/ceiling.sum()) if ceiling.sum() else None,
    ceiling_static_gap=int(ceiling.sum()-net[b]),uncovered_gain=int(ceiling.sum()-gain[b]),
    collateral_loss=int(loss[b]),best_noncenter_action=LABELS[nb],best_noncenter_net=int(net[nb]),
    average_action_gain=float(gain[:8].mean()),average_action_loss=float(loss[:8].mean()),
    average_action_net=float(net[:8].mean()),mixed_actions=int(((gain[:8]>0)&(loss[:8]>0)).sum()),
    best_reward_action=LABELS[best(reward_delta)],cross_half=transfers,
    entry_change_events=len(local_events),entry_change_hit_gain=int((event_hit>0).sum()),entry_change_hit_loss=int((event_hit<0).sum()),
    entry_change_no_hit=int((event_hit==0).sum()),single_swap_events=len(one),
    single_swap_margin_crossed=sum(e['margin_crossed'] for e in one),
    single_swap_positive_action_margin=sum(e['action_margin']>0 for e in one),
    grouped_conflicts=grouped,pair_preferences=pair_stats)
  assert s['ceiling_static_gap']==s['uncovered_gain']+s['collateral_loss']
  summaries.append(s)
  save_np(O/'results'/ds/(name+'.npz'),rows=rows,source_rows=source,hits=h,delta=delta,U=u,delta_U=du,
    gain=gain,loss=loss,net=net,ceiling=ceiling,floor=floor,best_masks=masks,improving_masks=improving,drift=drift)
  print(json.dumps({k:s[k] for k in ['dataset','context','ceiling_pp','best_static_pp','best_static_gain','best_static_loss','uncovered_gain','positive_queries','mixed_actions']}),flush=True)
for name,data in [('actions.csv',action_rows),('queries.csv',query_rows),('entry_events.csv',events),
                  ('transition_groups.csv',group_rows),('query_pairs.csv',pair_rows),('query_neighbors.csv',neighbor_rows)]:writecsv(name,data)
summary=dict(status='PAYOFF_ATTRIBUTION_ANALYZED',contexts=summaries,existing_outputs_scored=36864,
    same_entry_outputs_checked=same_entry_checked,new_NSG=0,new_HNSW=0,new_builds=0,optimizer_updates=0,new_GT=0,
    query_similarity_pairs_evaluated=2*1024*1024,actual_threads=1,seconds=time.monotonic()-start,
    peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
dump(O/'results/diagnosis.json',summary);contract()
print('Analysis complete: no native search or optimizer imports.')
