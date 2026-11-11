from common import *
import collections,math
P=list(csv.DictReader((OLD/'analysis/points.csv').open()));G=collections.defaultdict(list)
for p in P:G[p['dataset'],p['window'],p['K']].append(p)
ret=collections.defaultdict(list)
for p in P:
 if p['method']in ['GT10','B32','OPT-B32','REUSE-SQ']or float(p['gain_vs_B32_pp'])<=0:continue
 if not any(int(q['hits'])>=int(p['hits'])and float(q['qps'])>=float(p['qps'])and(int(q['hits'])>int(p['hits'])or float(q['qps'])>float(p['qps']))for q in G[p['dataset'],p['window'],p['K']]):ret[p['dataset'],p['K'],p['L'],p['method']].append(p)
ret=[v for v in ret.values()if len(v)==2];assert len(ret)==51;plan=collections.defaultdict(set);proposals=[]
for vv in ret:
 for p in vv:
  ds,w,K,L=p['dataset'],p['window'],p['K'],int(p['L']);pp=G[ds,w,K];key=ds,w;plan[key].add((int(K),L,p['method']));plan[key].add((int(K),L,'OPT-B32'))
  for comp,orig in [('GT10','GT10'),('OPT-B32','B32')]:
   curve=sorted([(int(x['L']),float(x['mean_us']))for x in pp if x['method']==orig]);saving=0
   if comp=='OPT-B32':saving=next(float(x['mean_us'])for x in pp if x['method']=='B32'and x['L']=='100')-next(float(x['mean_us'])for x in pp if x['method']=='OPT-B32')
   target=float(p['mean_us'])+saving;estimate=curve[-1][0]
   for (lo,t0),(hi,t1)in zip(curve,curve[1:]):
    if t0<=target<=t1:estimate=round(lo+(target-t0)*(hi-lo)/(t1-t0));break
   for delta in [-2,0,2]:plan[key].add((int(K),max(int(K),estimate+delta),comp))
   plan[key].add((int(K),L+1,comp));proposals.append(dict(dataset=ds,window=w,K=int(K),candidate_L=L,candidate=p['method'],control=comp,estimated_L=estimate,old_time_us=float(p['mean_us']),old_absolute_optimization_saving_us=saving))
csvwrite(R/'analysis/selection.csv',[p for v in ret for p in v]);csvwrite(R/'analysis/control_proposals.csv',proposals)
points=[]
for ds in DS:
 for w in ['A','B']:
  c=read(OLD/'configs'/f'{ds}.{w}.json');c['output_dir']=str(R/'storage/results'/ds/w);c['old_output_dir']=str(OLD/'storage/results'/ds/w);c['points']=[dict(K=K,L=L,method=m)for K,L,m in sorted(plan[ds,w])];dump(R/'configs'/f'{ds}.{w}.json',c)
  points += [dict(dataset=ds,window=w,**p)for p in c['points']]
csvwrite(R/'analysis/frozen_point_list.csv',points);dump(R/'selection_freeze.json',dict(configurations=51,candidate_window_points=102,formal_points=len(points),formal_batches=len(points)*3,old_points_sha=sha(OLD/'analysis/points.csv'),protocol_sha=sha(R/'protocol.md'),time=time.time()))
print('PREPARED',len(points),len(points)*3,flush=True)
