import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='8'
os.sched_setaffinity(0,range(8))
import hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;C=json.loads((R/'config.locked.json').read_text());REF=json.loads((R/'reviews/validation_references.json').read_text())
def ident(p):
 p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
 start=time.perf_counter();diag=json.loads((R/'reviews/GT_distance_shape_diagnostic_v1.json').read_text());allresults={};checks=0
 for ds,c in C['datasets'].items():
  p=Path(c['output']);r=REF[ds];d=c['dimension'];full=Path(r['full_default']);fi=np.fromfile(full/'fit20000.ids.i64','<i8').reshape(20000,100);fd=np.fromfile(full/'fit20000.dist.f32','<f4').reshape(20000,100)
  affected=sorted(set(row for rec in diag['datasets'][ds].values() for row in rec['rows_differing']));assert all(row>=19968 for row in affected)
  if not affected:allresults[ds]={'affected_rows':[],'all_distance_bits_match':True};continue
  q=np.fromfile(c['fit_queries'],'<f4').reshape(20000,d)[affected].astype('f8');base=np.memmap(c['base'],'<f4',mode='r').reshape(c['base_n'],d+1)[:,1:]
  bestids=np.empty((len(q),0),dtype='i8');bestscore=np.empty((len(q),0),dtype='f8')
  for lo in range(0,c['base_n'],100000):
   assert time.perf_counter()-start<120
   hi=min(lo+100000,c['base_n']);block=np.array(base[lo:hi],dtype='f8');score=q@block.T
   local=np.argpartition(score,-101,axis=1)[:,-101:];ss=np.take_along_axis(score,local,axis=1);ii=local+lo
   ii=np.concatenate([bestids,ii],axis=1);ss=np.concatenate([bestscore,ss],axis=1)
   keep=np.argpartition(ss,-101,axis=1)[:,-101:];bestscore=np.take_along_axis(ss,keep,axis=1);bestids=np.take_along_axis(ii,keep,axis=1)
  result=[]
  for j,row in enumerate(affected):
   order=np.lexsort((bestids[j],-bestscore[j]));ids=bestids[j,order];scores=bestscore[j,order];truth=fi[row];check={}
   # No tolerance is used to assert ID sets. Report ties explicitly if this exact test fails.
   assert np.array_equal(truth,ids[:100]),('float64 full top100 order mismatch',row)
   calc=np.array(base[truth],dtype='f8')@q[j];np.testing.assert_allclose(calc,scores[:100],rtol=1e-13,atol=1e-13)
   assert float(np.max(np.abs(calc-fd[row])))<=3e-5
   for method,rowsfile,distfile in [('pilot',p/'pilot_rows.i32',p/'pilot1024.dist.f32')]+[(m,p/m/'added_rows.i32',p/m/'additional1024.dist.f32') for m in ['EnergyTree','ShuffledEnergyTree']]:
    rows=np.fromfile(rowsfile,'<i4');found=np.flatnonzero(rows==row)
    if len(found):
     new=np.fromfile(distfile,'<f4').reshape(1024,100)[found[0]];err=float(np.max(np.abs(calc-new)));assert err<=3e-5
     check[method]={'distance_score_max_error':err,'new_distance_bits_vs_old_positions':int(np.sum(new.view('u4')!=fd[row].view('u4')))}
   result.append({'row':row,'full_float64_top100_order_ID_match':True,'full_float64_GT1_2_gap':float(scores[0]-scores[1]),'GT100_101_gap':float(scores[99]-scores[100]),'old_distance_score_max_error':float(np.max(np.abs(calc-fd[row]))),'new':check,'float64_ids':ids[:100].tolist(),'float64_scores':scores[:100].tolist()});checks+=1
  allresults[ds]={'affected_rows':affected,'old_GT_batch_shape':32,'new_GT_batch_shape':256,'all_affected_full_float64_GT_order_checked':True,'records':result}
 out={'status':'PASS_REPORTED_SHORT_TAIL_SCORE_ROUNDING_ONLY','seconds':time.perf_counter()-start,'source':ident(__file__),'datasets':allresults,
  'independent_fullbase_float64_GT_checks':checks,'new_FAISS_GT':0,'new_NSG':0,'new_ANN':0,'selection_and_model_changed':False,
  'attribution':'all bit differences restricted to old final32 rows; all GT IDs and same-shape pilot bytes restored; old/new returned scores independently validated; no rerun to force bits'}
 assert checks==4
 with (R/'reviews/GT_tail_float64_audit.json').open('x') as f:json.dump(out,f,indent=2,allow_nan=False);f.write('\n')
 print('TAIL FLOAT64 PASS',checks,out['seconds'],flush=True)
if __name__=='__main__':main()
