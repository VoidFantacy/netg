from native import *
import test_reinforce
assert read(O/'reviews/reinforce_tests.json')['status']=='PASS'
resources()
freeze(O/'reviews/protocol_and_implementation_before_queries.json',[O/'protocol.md']+list((O/'src').rglob('*.py'))+list((O/'src').rglob('*.cpp'))+list((O/'src/hnswlib').glob('*.h'))+list((O/'bin').glob('*'))+list((O/'inputs').rglob('*.*')))
records=[]
for ds in DS:
 c=read(O/'inputs'/ds/'config.json')
 with Environment(c,O/'inputs'/ds,load_nsg=False) as env:
  t=env.topology;protected=np.array(t['protected'],np.uint8);rng=np.random.default_rng(92741)
  masks=[np.ones(env.edges,np.uint8),protected.copy(),np.maximum(protected,rng.integers(0,2,env.edges,dtype=np.uint8))]
  rows=np.arange(512,dtype=np.int32)
  for mask in masks:env.parity(rows,mask,native=False)
  # p=0/1 sampling and fixed masks must agree bitwise on the same topology.
  a=env.run(rows,p=masks[2].astype(float),seed=199,search=False,trace=True);b=env.run(rows,mask=masks[2],search=False,trace=True)
  for key in ['entries','route_ndc','actions','offsets']:assert np.array_equal(a[key],b[key]),key
  for i in range(len(rows)):
   edges=a['actions'][a['offsets'][i]:a['offsets'][i+1]]//2;assert len(np.unique(edges))==len(edges);assert not protected[edges].any()
  assert env.calls==0
  records.append(dict(dataset=ds,status='PASS',nodes=t['nodes'],edges=t['edges'],protected=t['protected_edges'],route_calls=env.route_calls,
   all_keep_parity=True,protected_only_parity=True,random_mask_parity=True,sampling_extremes_parity=True,actions_unique_per_episode=True))
dump(O/'reviews/router_preflight.json',dict(status='PASS',datasets=records,NSG_calls=0))
freeze(O/'reviews/initial_graphs.json',list((O/'inputs').rglob('*.*')))
dump(O/'state.json',dict(status='ROUTER_PREFLIGHT_PASS_TRAINING_READY',real_calls=0,optimizer_updates=0))
print('ROUTER_PREFLIGHT_PASS',records,flush=True)
