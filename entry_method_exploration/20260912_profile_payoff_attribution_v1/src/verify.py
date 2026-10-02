from common import *
from collections import defaultdict
contract();start=time.monotonic();check(O/'reviews/preanalysis_freeze.json')
summary=read(O/'results/diagnosis.json');saved_context={};scored=0
for ds in DS:
 for name in ['zero','selected']:
  c,rows,q,gt,source,hubs,raw,_,w=load_context(ds,name)
  h=np.empty((9,1024),np.int16)
  for a in range(9):
   for qi in range(1024):
    result=set(map(int,raw[a]['ids'][qi]));truth=set(map(int,gt[qi,:10]))
    assert len(result)==len(truth)==10
    h[a,qi]=len(result.intersection(truth));scored+=1
  values=dict(np.load(O/'results'/ds/(name+'.npz')))
  assert np.array_equal(h,values['hits'])
  delta=h-h[8];assert np.array_equal(delta,values['delta'])
  gains=np.array([sum(max(int(x),0) for x in row) for row in delta]);losses=np.array([sum(max(-int(x),0) for x in row) for row in delta])
  ceiling=np.array([max(map(int,delta[:,qi])) for qi in range(1024)])
  net=gains-losses;chosen=8 if net[8]==max(net) else list(net).index(max(net))
  assert np.array_equal(gains,values['gain']) and np.array_equal(losses,values['loss'])
  s=next(x for x in summary['contexts'] if x['dataset']==ds and x['context']==name)
  assert s['ceiling_hits']==sum(ceiling) and s['best_static_action']==LABELS[chosen]
  assert s['best_static_net_hits']==int(net[chosen])
  assert s['uncovered_gain']==sum(ceiling)-gains[chosen] and s['collateral_loss']==losses[chosen]
  assert s['ceiling_static_gap']==sum(ceiling)-net[chosen]
  for qi in range(1024):
   bm=sum(1<<a for a in range(9) if delta[a,qi]==ceiling[qi]);im=sum(1<<a for a in range(9) if delta[a,qi]>0)
   assert bm==values['best_masks'][qi] and im==values['improving_masks'][qi]
  q=q/np.linalg.norm(q,axis=1,keepdims=True)
  saved_context[ds,name]=(rows,q,gt,hubs,raw,h,w,values)
actions=list(csv.DictReader((O/'results/actions.csv').open()))
for a in actions:
 ds,name=a['dataset'],a['context'];i=LABELS.index(a['action']);rows,q,gt,hubs,raw,h,w,v=saved_context[ds,name]
 assert int(a['gross_gain_hits'])==v['gain'][i] and int(a['loss_hits'])==v['loss'][i]
 assert int(a['net_hits'])==v['delta'][i].sum()
 assert int(a['rescued_zero'])==sum(h[8,qi]==0 and h[i,qi]>0 for qi in range(1024))
 assert int(a['new_zero'])==sum(h[8,qi]>0 and h[i,qi]==0 for qi in range(1024))
 np.testing.assert_allclose(float(a['mean_U_delta']),v['delta_U'][i].mean(),rtol=1e-12,atol=1e-12)
events=list(csv.DictReader((O/'results/entry_events.csv').open()));seen=set();regroups=defaultdict(list)
for e in events:
 ds,name=e['dataset'],e['context'];a=LABELS.index(e['action']);qi=int(e['qi'])
 rows,q,gt,hubs,raw,h,w,v=saved_context[ds,name];lookup={int(hub):j for j,hub in enumerate(hubs)}
 key=(ds,name,a,qi);assert key not in seen;seen.add(key)
 old=set(map(int,raw[8]['entries'][qi]));new=set(map(int,raw[a]['entries'][qi]))
 removed=sorted(old-new);added=sorted(new-old)
 assert removed==list(map(int,e['removed'].split(';'))) and added==list(map(int,e['added'].split(';')))
 assert int(e['row'])==rows[qi] and int(e['delta_hits'])==int(h[a,qi])-int(h[8,qi])
 assert e['center_entries']==';'.join(map(str,raw[8]['entries'][qi]))
 assert e['action_entries']==';'.join(map(str,raw[a]['entries'][qi]))
 def dot(which,hub):return sum(float(x)*float(y) for x,y in zip(q[qi],w[which][lookup[hub]]))
 m0=min(dot(8,hub) for hub in added)-max(dot(8,hub) for hub in removed)
 m1=min(dot(a,hub) for hub in added)-max(dot(a,hub) for hub in removed)
 np.testing.assert_allclose([float(e['center_margin']),float(e['action_margin'])],[m0,m1],atol=1e-12,rtol=1e-10)
 assert int(e['margin_crossed'])==int(m0<=0<m1)
 for kind,keys in [('full_transition',[e['center_entries']+'>'+e['action_entries']]),
       ('added_hub',e['added'].split(';')),('removed_hub',e['removed'].split(';')),
       ('single_swap',[e['removed']+'>'+e['added']] if len(removed)==1 else [])]:
  for value in keys:regroups[(ds,name,kind,e['action'],value)].append(e)
expected=0
for (ds,name),(rows,q,gt,hubs,raw,h,w,v) in saved_context.items():
 for a in range(8):
  changed=np.any(raw[a]['entries']!=raw[8]['entries'],axis=1)
  expected+=int(changed.sum())
  assert all((ds,name,a,int(qi)) in seen for qi in np.flatnonzero(changed))
assert expected==len(events)==6508
groups=list(csv.DictReader((O/'results/transition_groups.csv').open()))
assert len(groups)==len(regroups)
for g in groups:
 ers=regroups[(g['dataset'],g['context'],g['kind'],g['action'],g['key'])]
 dh=[int(e['delta_hits']) for e in ers]
 assert int(g['events'])==len(dh) and int(g['helped'])==sum(x>0 for x in dh) and int(g['harmed'])==sum(x<0 for x in dh)
 assert int(g['gross_gain'])==sum(max(x,0) for x in dh) and int(g['loss'])==sum(max(-x,0) for x in dh)
pairs=list(csv.DictReader((O/'results/query_pairs.csv').open()))
for p in pairs:
 rows,q,gt,hubs,raw,h,w,v=saved_context[p['dataset'],p['context']]
 i=int(np.flatnonzero(rows==int(p['row_a']))[0]);j=int(np.flatnonzero(rows==int(p['row_b']))[0])
 assert int(v['ceiling'][i])>0 and int(v['ceiling'][j])>0
 bothmax=set(np.flatnonzero(v['delta'][:,i]==v['ceiling'][i]))&set(np.flatnonzero(v['delta'][:,j]==v['ceiling'][j]))
 bothbetter=set(np.flatnonzero(v['delta'][:,i]>0))&set(np.flatnonzero(v['delta'][:,j]>0))
 assert (p['best_compatible']=='True')==bool(bothmax)
 assert (p['joint_improvement_possible']=='True')==bool(bothbetter)
 np.testing.assert_allclose(float(p['query_cosine']),q[i]@q[j],atol=1e-12,rtol=1e-12)
assert scored==36864
dump(O/'reviews/independent_verification.json',dict(status='PASS',set_scored=scored,
       payoff_decompositions=4,action_summaries=len(actions),entry_events=len(events),
       scalar_dot_margin_checks=2*len(events),transition_groups=len(groups),query_pairs=len(pairs),
       seconds=time.monotonic()-start,NSG_calls=0,HNSW_calls=0,optimizer_updates=0))
print(json.dumps(read(O/'reviews/independent_verification.json')))
