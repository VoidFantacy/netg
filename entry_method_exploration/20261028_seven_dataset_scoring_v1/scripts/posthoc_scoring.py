import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
import json,csv,time,collections
from pathlib import Path
import numpy as np
from io_data import view,gt,read_array
R=Path(__file__).resolve().parents[1]
def main():
 assert (R/'primary_complete.json').exists();t=time.perf_counter();summary=[];loss_summary=[];loss_rows=[]
 for cp in sorted((R/'configs').glob('*.json')):
  if cp.name.count('.')!=1:continue
  c=json.loads(cp.read_text());ds=c['dataset'];n=c['queries']['n'];base=view(c['base']);q=view(c['queries']);g=gt(c['test_gt']);model=json.loads((Path(c['models'])/'model.json').read_text());off=read_array(model['files']['offsets'],'<u8').astype(int);bid=read_array(model['files']['ids'],'<i4');sample=np.random.default_rng(20261028).choice(n,min(128,n),False);root=R/'storage/results'/ds
  def metric(qi,ids):
   v=base[ids].astype('float64');qi=qi.astype('float64');return ((v-qi)**2).sum(1) if c['metric_id']==1 else -(v*qi).sum(1)
  for K in [1,100]:
   main=read_array(root/f'k{K}/GT10_L200/raw/ids.i32','<i4').reshape(n,K)
   for m in ['REUSE-PQ','REUSE-SQ','MAIN-SQ']:
    trace=read_array(root/f'k{K}/{m}_L200/trace.i32','<i4').reshape(n,160);counts=collections.Counter()
    for i in sample:
     missing=set(map(int,g[i,:K]))-set(map(int,main[i]));blocks=trace[i,32:64];blocks=blocks[blocks>=0];ids=np.concatenate([bid[off[b]:off[b+1]] for b in blocks]);ids=ids[~np.isin(ids,main[i])];scores=metric(q[i],ids);short=ids[np.argsort(scores,kind='stable')[:96]];counts['original_missing']+=len(missing);counts['scanned_missing']+=len(missing&set(map(int,ids)));counts['actual_shortlist_missing']+=len(missing&set(map(int,trace[i,64:])));counts['float64_exact96_missing']+=len(missing&set(map(int,short)))
    summary.append(dict(dataset=ds,K=K,method=m,L=200,sample_queries=len(sample),seed=20261028,**dict(counts)))
  # Full-query final merge losses are classified without changing strict GT-ID/tie rules.
  complete=json.loads((root/'complete.json').read_text())['results']
  for rr in complete:
   m,K,L=rr['method'],rr['K'],rr['L']
   if m not in ['REUSE-PQ','REUSE-SQ','MAIN-SQ']:continue
   main=read_array(root/f'k{K}/GT10_L{L}/raw/ids.i32','<i4').reshape(n,K);p=Path(rr['result_dir']);trace=read_array(p/'trace.i32','<i4').reshape(n,160);final=read_array(p/'raw/ids.i32','<i4').reshape(n,K);lost=dups=near=0
   for i in range(n):
    candidates=(set(map(int,g[i,:K]))-set(map(int,main[i])))&set(map(int,trace[i,64:]))-set(map(int,final[i]))
    if not candidates:continue
    vectors=base[final[i]];last=float(metric(q[i],final[i,-1:])[0])
    for target in sorted(candidates):
     lost+=1;identical=np.flatnonzero((vectors.view('<u4')==base[target].view('<u4')).all(1));value=float(metric(q[i],[target])[0]);close=abs(value-last)<=5e-5+3e-6*abs(last);dups+=bool(len(identical));near+=close;loss_rows.append(dict(dataset=ds,K=K,method=m,L=L,query=i,target=target,score64=value,final_worst_score64=last,score_difference=value-last,identical_returned_IDs=','.join(str(int(final[i,j])) for j in identical),near_boundary=close))
   loss_summary.append(dict(dataset=ds,K=K,method=m,L=L,shortlist_to_final_lost=lost,lost_with_identical_vector=dups,lost_near_boundary=near))
 for name,rows in [('scoring_diagnostic',summary),('merge_loss_summary',loss_summary),('merge_loss_cases',loss_rows)]:
  if rows:
   with (R/f'analysis/{name}.csv').open('w') as f:w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
 out=dict(status='PASS_E191_POSTHOC_SCORING_DIAGNOSTIC',fixed_samples=summary,merge_losses=loss_summary,seconds=time.perf_counter()-t,scope='post-result fixed128 float64 diagnosis, not a measured online method or native counterfactual',GT_or_tie_changed=False)
 (R/'reviews/posthoc_scoring_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(status=out['status'],diagnostic_rows=len(summary),loss_events=len(loss_rows),seconds=out['seconds'])),flush=True)
if __name__=='__main__':main()
