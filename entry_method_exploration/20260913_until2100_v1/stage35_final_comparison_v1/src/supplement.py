from pathlib import Path
import sys,csv,itertools,time
import numpy as np
F=Path(__file__).resolve().parents[1];C=F.parent
sys.path.insert(0,str(C/'stage32_final_tooling_v1/src'))
from common import read,dump,sha,freeze,table,DS,LS,threads
from scoring_v3 import raw
threads();assert all(j['status']=='COMPLETE' for j in read(F/'logs/jobs.json')) and len(read(F/'logs/jobs.json'))==2
A=F/'analysis_v1';assert read(A/'verification.json')['status']=='PASS';O=F/'supplement_v1';assert not O.exists();O.mkdir()
points=list(csv.DictReader((A/'points.csv').open()));selected=read(F/'selection.json');E34=C.parent/'20260911_hnsw_rl_benchmark_v1'
sources=[Path(__file__),A/'verification.json',A/'points.csv',A/'paired.csv',F/'selection.json'];cache={};regression=0;regrecords=[];failurecells=[];intervals=[];frontierrows=[];interpolated=[];deltas=[];group_counts=[]
for ds in DS:
 c=read(F/'inputs'/ds/'config.json');oldc=read(E34/'inputs'/ds/'config.json');oldresult=read(E34/'results'/ds/'results.json');rows=np.fromfile(c['row_ids'],np.int64);gt=np.fromfile(c['gt_file'],np.int64).reshape(2000,100)
 for k in ['queries_file','gt_file','row_ids']:assert sha(c[k])==sha(oldc[k]);sources+=[Path(c[k]),Path(oldc[k])]
 names=[m['model_name'] for m in c['methods'] if m['L']==64];candidate=selected['datasets'][ds]['best_new'];reference='baseline_soft' if ds==DS[0] else 'gt10_hard'
 for m in c['methods']:
  name,L=m['model_name'],m['L'];p=F/'results'/ds/m['name'];a=raw(p);cache[ds,name,L]=a;sources+=list(p.glob('*'))
  if name in ['nsg','fast30k','gt10_hard','baseline_soft']:
   # E34 names the same matched Web endpoint gt10_soft.
   oldname='gt10_soft' if name=='baseline_soft' else name
   om=next(z for z in oldresult['methods'] if z['model_name']==oldname and z['L']==L);oldp=E34/'results'/ds/om['name']
   for fn in ['ids.i32','distances.f32','entry_ids.i32','hits.u8','hitmask.u16','route_ndc.u32','graph_ndc.u32']:assert sha(p/fn)==sha(oldp/fn),(ds,name,L,fn);sources.append(oldp/fn)
   regression+=2000;regrecords.append(dict(dataset=ds,model=name,L=L,rows=2000,status='ALL_SEVEN_FIELDS_BIT_EXACT_E34'))
 failed_union=np.flatnonzero(np.any(np.stack([cache[ds,name,L]['hits']==0 for L in LS for name in names]),axis=0));changed=0
 for i in failed_union:
  if any(len({bool(cache[ds,name,L]['hits'][i]==0) for name in names})>1 for L in LS):changed+=1
  for L in LS:
   statuses=[bool(cache[ds,name,L]['hits'][i]==0) for name in names]
   for name in names:
    a=cache[ds,name,L];failurecells.append(dict(dataset=ds,namespace='validation',source_row=int(rows[i]),L=L,model=name,hits=int(a['hits'][i]),failed=bool(a['hits'][i]==0),changed_zero_status_at_L=len(set(statuses))>1,GT10=' '.join(map(str,gt[i,:10])),entries=' '.join(map(str,a['entries'][i])),returned=' '.join(map(str,a['ids'][i]))))
 group_counts.append(dict(dataset=ds,all_L_failed_union_queries=len(failed_union),any_method_failure_status_change_queries=changed,all_L_method_cells=len(failed_union)*5*len(names)))
 rng=np.random.default_rng(20260913+DS.index(ds));bs=rng.integers(0,2000,(2000,2000),dtype=np.int32)
 for L in LS:
  a=cache[ds,candidate,L];b=cache[ds,reference,L];d=a['hits'].astype(np.int16)-b['hits'];df=(a['hits']==0).astype(np.int16)-(b['hits']==0);rc=np.quantile(d[bs].mean(1)*10,[.025,.975]);fc=np.quantile(df[bs].mean(1)*100,[.025,.975]);intervals.append(dict(dataset=ds,candidate=candidate,reference=reference,L=L,recall_delta_pp=float(d.mean()*10),recall_low_pp=float(rc[0]),recall_high_pp=float(rc[1]),failure_delta_pp=float(df.mean()*100),failure_low_pp=float(fc[0]),failure_high_pp=float(fc[1]),scope='descriptive paired query bootstrap; historically exposed validation; no multiplicity correction'))
 def fp(name):
  ps=[dict(L=int(p['L']),r=float(p['recall_pct']),q=float(p['QPS']),lo=float(p['QPS_min']),hi=float(p['QPS_max'])) for p in points if p['dataset']==ds and p['model']==name]
  return sorted([p for p in ps if not any(t['r']>=p['r'] and t['q']>=p['q'] and (t['r']>p['r'] or t['q']>p['q']) for t in ps)],key=lambda p:p['r'])
 for name in names:
  for p in fp(name):frontierrows.append(dict(dataset=ds,model=name,L=p['L'],recall_pct=p['r'],QPS=p['q']))
 fa=fp(candidate)
 for ref in names:
  if ref==candidate:continue
  fb=fp(ref);low=max(fa[0]['r'],fb[0]['r']);high=min(fa[-1]['r'],fb[-1]['r']);assert low<high
  def interp(ps,x,key):return float(np.exp(np.interp(x,[p['r'] for p in ps],np.log([p[key] for p in ps]))))
  for frac in [.25,.5,.75]:
   target=low+frac*(high-low);qa,qb=interp(fa,target,'q'),interp(fb,target,'q');rl=(interp(fa,target,'lo')/interp(fb,target,'hi')-1)*100;rh=(interp(fa,target,'hi')/interp(fb,target,'lo')-1)*100
   interpolated.append(dict(dataset=ds,candidate=candidate,reference=ref,overlap_fraction=frac,target_recall_pct=target,QPS_change_pct=(qa/qb-1)*100,range_low_pct=rl,range_high_pct=rh,kind='descriptive log-QPS interpolation within measured nondominated overlap, no new measurements'))
table(O/'baseline_regression.csv',regrecords);table(O/'failed_queries_all_L.csv',failurecells);table(O/'paired_query_intervals.csv',intervals);table(O/'frontier_points.csv',frontierrows);table(O/'same_recall_interpolation.csv',interpolated)
dump(O/'verification.json',dict(status='PASS',E34_baseline_bit_regression_rows=regression,failure_groups=group_counts,all_L_failure_cells=len(failurecells),bootstrap_samples=2000,bootstrap_seed_rule='20260913 + dataset index',new_ANN=0,final_feedback_returned_to_training=False))
freeze(O/'input_freeze.json',[p for p in sources if p.is_file()]);print('FINAL_SUPPLEMENT_PASS',regression,group_counts)
