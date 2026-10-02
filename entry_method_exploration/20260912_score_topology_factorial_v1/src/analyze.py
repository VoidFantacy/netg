from shared import *
from collections import Counter
threads(8);resources();started=time.monotonic()
assert all(read(O/'results'/ds/'query_complete.json')['status']=='PASS' for ds in DS)
actions=[];contexts=[];summaries=[]
def table(p,rows):
 with p.open('w',newline='') as f:
  z=csv.DictWriter(f,fieldnames=list(rows[0]));z.writeheader();z.writerows(rows)
def paired(d):
 return dict(gain_hits=int(np.maximum(d,0).sum()),loss_hits=int(np.maximum(-d,0).sum()),net_hits=int(d.sum()),gain_queries=int((d>0).sum()),loss_queries=int((d<0).sum()))
for ds in DS:
 c=read(O/'inputs'/ds/'config.json');gt=np.fromfile(c['gt_file'],np.int64).reshape(5120,100)[:4096]
 base={k:v[:4096] for k,v in dict(np.load(E37/'results'/ds/'baseline.npz')).items()}
 for rec in [x for x in read(O/'inputs/contexts.json') if x['dataset']==ds]:
  step=rec['step'];dest=O/'results'/ds/f'{step:04}';t=dict(np.load(rec['trajectory']));near=np.load(E44/'inputs'/ds/f'{step:04}_context.npz')['near']
  tags=['C']+[f'{family}{a}' for family in ['A','S','T'] for a in range(8)]
  raw=[dict(np.load(dest/tag/'raw.npz')) for tag in tags]
  h=np.stack([score(x['ids'],gt) for x in raw]).astype(np.int16);u=np.stack([utility(x,base,gt) for x in raw])
  dh=(h[1:]-h[0]).reshape(3,8,4096);du=(u[1:]-u[0]).reshape(3,8,4096)
  drift=np.stack([t['drift']-t['current_drift'],t['drift']-t['current_drift'],np.zeros(8)])
  interaction=dh[0]-dh[1]-dh[2];ui=du[0]-du[1]-du[2]
  save(dest/'derived.npz',hits=h,U=u,delta_hits=dh,delta_U=du,delta_drift=drift,interaction_hits=interaction,interaction_U=ui,
   score_alone=dh[1],score_with_new_topology=dh[0]-dh[2],topology_alone=dh[2],topology_with_new_score=dh[0]-dh[1],near=near)
  for f,family in enumerate(['A','S','T']):
   dd=dh[f];net=dd.sum(1);gain=np.maximum(dd,0).sum(1);loss=np.maximum(-dd,0).sum(1)
   best=int(np.argmax(np.r_[0,net]))-1;bg=int(gain[best]) if best>=0 else 0;bl=int(loss[best]) if best>=0 else 0;oracle=int(np.maximum(0,dd.max(0)).sum())
   cr=dict(dataset=ds,step=step,family=family,hub=rec['hub'],**paired(dd),positive_actions=int((net>0).sum()),mixed_actions=int(((gain>0)&(loss>0)).sum()),
    oracle_hits=oracle,best_action=best,best_net_hits=max(0,int(net.max())),best_gain_hits=bg,best_loss_hits=bl,uncovered_oracle_hits=oracle-bg,own_loss_gap=bl)
   assert oracle-cr['best_net_hits']==cr['uncovered_oracle_hits']+bl;contexts.append(cr)
  for a in range(8):
   A,S,T=dh[:,a];nonzero=bool(np.any(A));zeroS=not np.any(S);zeroT=not np.any(T)
   if not nonzero and zeroS and zeroT:kind='all_quality_null'
   elif nonzero and np.array_equal(S,A) and zeroT:kind='score_alone_recovers_A_topology_null'
   elif nonzero and np.array_equal(T,A) and zeroS:kind='topology_alone_recovers_A_score_null'
   elif nonzero and np.array_equal(S,A) and np.array_equal(T,A):kind='both_alone_recovers_A'
   elif nonzero and zeroS and zeroT:kind='joint_only'
   else:kind='mixed_or_interacting'
   ar=dict(dataset=ds,step=step,action=a,hub=rec['hub'],classification=kind,interaction_nonzero_queries=int(np.count_nonzero(interaction[a])),interaction_L1_hits=int(np.abs(interaction[a]).sum()),interaction_net_hits=int(interaction[a].sum()))
   for f,family in enumerate(['A','S','T']):
    x=raw[1+f*8+a];d=dh[f,a];metrics=paired(d)
    metrics.update(new_zero_queries=int(((h[1+f*8+a]==0)&(h[0]>0)).sum()),rescued_zero_queries=int(((h[1+f*8+a]>0)&(h[0]==0)).sum()),
     mean_delta_U=float(du[f,a].mean()),mean_delta_J=float(du[f,a].mean()-drift[f,a]),delta_graph_NDC=int((x['graph_ndc'].astype(np.int64)-raw[0]['graph_ndc']).sum()),
     delta_route_NDC=int((x['route_ndc'].astype(np.int64)-raw[0]['route_ndc']).sum()),entry_changes=int((x['entries']!=raw[0]['entries']).any(1).sum()))
    for maskname,mask in [('near',near),('far',~near),('A_gain',A>0),('A_loss',A<0)]:
     metrics.update({maskname+'_'+k:v for k,v in paired(d[mask]).items()})
    ar.update({family+'_'+k:v for k,v in metrics.items()})
   actions.append(ar)
 aa=[x for x in actions if x['dataset']==ds];cc=[x for x in contexts if x['dataset']==ds];dsr=dict(dataset=ds,classifications=dict(Counter(x['classification'] for x in aa)),interaction_actions=sum(x['interaction_nonzero_queries']>0 for x in aa),interaction_L1_hits=sum(x['interaction_L1_hits'] for x in aa))
 for family in ['A','S','T']:
  rr=[x for x in cc if x['family']==family]
  m={key:sum(x[key] for x in rr) for key in ['gain_hits','loss_hits','net_hits','positive_actions','mixed_actions','oracle_hits','best_net_hits','uncovered_oracle_hits','own_loss_gap']}
  m['hit_contexts']=sum(x['gain_hits']+x['loss_hits']>0 for x in rr);m['hit_actions']=sum(x[family+'_gain_hits']+x[family+'_loss_hits']>0 for x in aa)
  m['mean_delta_U']=float(np.mean([x[family+'_mean_delta_U'] for x in aa]));m['mean_delta_J']=float(np.mean([x[family+'_mean_delta_J'] for x in aa]))
  for key in ['near_gain_hits','near_loss_hits','far_gain_hits','far_loss_hits','delta_graph_NDC','delta_route_NDC']:
   m[key]=sum(x[family+'_'+key] for x in aa)
  dsr[family]=m
 for family in ['S','T']:
  m=dsr[family];ref=dsr['A'];m['followup_pass']=bool(m['gain_hits']>0 and ref['gain_hits']>0 and m['gain_hits']>=.75*ref['gain_hits'] and m['loss_hits']<=.5*ref['loss_hits'] and m['best_net_hits']>=ref['best_net_hits'])
 summaries.append(dsr)
gate=dict(status='PASS_SINGLE_FACTOR_RESEARCH_GATE' if any(all(x[f]['followup_pass'] for x in summaries) for f in ['S','T']) else 'KEEP_MIXED_MECHANISM_NO_SINGLE_FACTOR_TRAINING',
 qualifying_factors=[f for f in ['S','T'] if all(x[f]['followup_pass'] for x in summaries)],datasets=summaries,scope='Fixed original actions and contexts; no deployable aggregate or generalization claim')
table(O/'results/actions.csv',actions);table(O/'results/contexts.csv',contexts)
dump(O/'results/analysis.json',dict(actions=actions,contexts=contexts,datasets=summaries,seconds=time.monotonic()-started));dump(O/'results/gate.json',gate)
costs=[read(O/'results'/ds/'query_complete.json') for ds in DS]
dump(O/'results/cost.json',dict(NSG_calls=sum(x['NSG_calls'] for x in costs),HNSW_calls=sum(x['HNSW_calls'] for x in costs),builds=340,topology_installations=340,causal_installations=320,no_op_installations=20,states=500,
 historical_C_seed_NSG=81920,endpoint_new_NSG=1333,parity_NSG=4800,optimizer_updates=0,new_GT=0,new_development_queries=0,QPS_points=0,datasets=costs))
print(json.dumps(gate,ensure_ascii=False,indent=2),flush=True)
