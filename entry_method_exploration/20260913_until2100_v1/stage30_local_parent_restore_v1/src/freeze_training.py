from common import *
import csv
threads();resources();check(O/'reviews/precompile_freeze.json');checks=[]
for ds in DS:
 cfg=read(O/'inputs'/ds/'routes.json');nc=read(O/'inputs'/ds/'native_training.json');m=cfg['method'];mapping=np.fromfile(m['mapping'],np.int32);W=np.fromfile(m['W'],np.float32).reshape(-1,cfg['dim']);Q=np.memmap(nc['queries_file'],np.float32,mode='r').reshape(20000,-1)
 p=raw(E66/'results'/ds/'fit/baseline_L128');c=dict(np.load(E86/'results'/ds/'fit/compact_baseline.npz'));actual=list(csv.DictReader((O/'inputs'/ds/'proposal_events.csv').open()));expected=[];weight={};support={}
 groups={h:np.flatnonzero(mapping==h) for h in np.unique(mapping)}
 for i in range(20000):
  diff=int(p['hits'][i])-int(c['hits'][i])
  if diff<=0:continue
  for h in c['entries'][i]:
   slots=groups[h]
   if h in p['entries'][i] or len(slots)!=3:continue
   first=next(int(s) for s in c['slots'][i] if mapping[s]==h)
   if first==slots[0]:continue
   expected.append((i,int(h),first,int(slots[0]),diff));weight[int(h)]=weight.get(int(h),0)+diff;support.setdefault(int(h),set()).add(i)
 actual_key=[(int(r['fit_index']),int(r['hub']),int(r['winner_slot']),int(r['parent_slot']),int(r['weight'])) for r in actual]
 assert sorted(expected)==sorted(actual_key)
 for r in actual:
  i,s,t=int(r['fit_index']),int(r['winner_slot']),int(r['parent_slot']);v=sum(float(q)*(float(a)-float(b)) for q,a,b in zip(Q[i],W[s],W[t]));assert abs(v-float(r['score_lift']))<1e-11
 selected=sorted([h for h in weight if len(support[h])>=2],key=lambda h:(-weight[h],h))[:32]
 candidates=read(O/'inputs'/ds/'candidates.json');assert selected==[r['hub'] for r in candidates]
 for r in candidates:assert r['votes']==weight[r['hub']] and r['support']==len(support[r['hub']])
 checks.append(dict(dataset=ds,verified_events=len(expected),candidate_hubs=len(selected)))
dump(O/'reviews/proposals_independent.json',dict(status='PASS',records=checks,new_ANN=0))
paths=[Path(x['path']) for x in read(O/'reviews/precompile_freeze.json')['files']]+[p for p in (O/'src').glob('*') if p.is_file()]+list((O/'bin').glob('*'))+[O/'reviews/proposals_independent.json']
for ds in DS:paths += list((E84/'results'/ds/'routes_fit').glob('*'))
freeze(O/'reviews/pretraining_freeze.json',paths);print('E89_FROZEN_TRAINING',checks)
