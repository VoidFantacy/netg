"""Post-result diagnosis only: no model changes or additional performance points."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
import json,time,hashlib
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]
def main():
 t=time.perf_counter();checks=[]
 for ds in ['coco','deep10m_l2_v1']:
  c=json.loads((R/f'configs/{ds}.json').read_text());N=c['base']['n'];d=c['base']['d'];n=c['queries']['n'];base=np.memmap(c['base']['path'],'<f4','r').reshape(N,d+1)[:,1:] if c['base']['format']=='fvecs' else np.memmap(c['base']['path'],'<f4','r').reshape(N,d);q=np.memmap(c['queries']['path'],'<f4','r').reshape(n,d);g=c['test_gt'];gt=np.memmap(g['path'],'<i8' if g['format']=='raw_i64' else '<i4','r').reshape(-1,100)[:n];p=R/'results'/ds;main=np.fromfile(p/'GT10_L200/raw/ids.i32','<i4').reshape(n,100);bp=Path(c['blocks']);off=np.fromfile(bp/'block_offsets.u64','<u8').astype(int);bid=np.fromfile(bp/'block_ids.i32','<i4');sample=np.random.default_rng(20261028).choice(n,256,False)
  def metric(qi,ids):
   x=base[ids].astype('float64');qi=qi.astype('float64');return ((x-qi)**2).sum(1) if c['metric_id']==1 else -(x*qi).sum(1)
  for m in ['REUSE-BLOCK','MAIN-BLOCK']:
   trace=np.fromfile(p/f'{m}_L200/trace.i32','<i4').reshape(n,160);final=np.fromfile(p/f'{m}_L200/raw/ids.i32','<i4').reshape(n,100);dist=np.fromfile(p/f'{m}_L200/raw/distances.f32','<f4').reshape(n,100);missing=pool=actual=exact=0;loss=[]
   for i in sample:
    truth=set(map(int,gt[i]))-set(map(int,main[i]));missing+=len(truth);blocks=trace[i,32:64];blocks=blocks[blocks>=0];ids=np.concatenate([bid[off[b]:off[b+1]] for b in blocks]);ids=ids[~np.isin(ids,main[i])];pool+=len(truth&set(ids));scores=metric(q[i],ids);chosen=ids[np.argsort(scores,kind='stable')[:96]];exact+=len(truth&set(chosen));actual+=len(truth&set(trace[i,64:]))
   for i in range(n):
    dropped=(set(map(int,gt[i]))-set(map(int,main[i])))&set(map(int,trace[i,64:]))-set(map(int,final[i]))
    if not dropped:continue
    last64=float(metric(q[i],final[i,-1:])[0]);vectors=base[final[i]]
    for target in sorted(dropped):
     score64=float(metric(q[i],[target])[0]);dup=np.flatnonzero((vectors.view('<u4')==base[target].view('<u4')).all(1));loss.append(dict(query=i,target=target,target_score64=score64,final_worst_score64=last64,target_minus_worst64=score64-last64,native_final_worst=float(dist[i,-1]),identical_vector_returned_ids=[int(final[i,j]) for j in dup],within_score_tolerance=abs(score64-last64)<=5e-5+3e-6*abs(last64)))
   checks.append(dict(dataset=ds,method=m,sample_queries=256,sample_seed=20261028,sample_original_missing=missing,sample_scanned_GT_missing=pool,sample_actual_PQ96_GT_missing=actual,sample_float64_exact96_GT_missing=exact,all_query_shortlist_to_final_lost=len(loss),lost_with_returned_identical_vector=sum(bool(v['identical_vector_returned_ids']) for v in loss),lost_within_score_tolerance=sum(v['within_score_tolerance'] for v in loss),losses=loss))
 out=dict(status='PASS_E189_POSTHOC_SCORING_DIAGNOSIS',scope='post-result fixed256 sample float64 shortlist diagnostic; not measured online Recall/QPS or native counterfactual',model_or_parameters_changed=False,seconds=time.perf_counter()-t,checks=checks);(R/'reviews/posthoc_scoring_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps([{k:v for k,v in x.items() if k!='losses'} for x in checks]),flush=True)
if __name__=='__main__':main()
