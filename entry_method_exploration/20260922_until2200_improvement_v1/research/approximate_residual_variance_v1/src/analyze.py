import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='8'
os.sched_setaffinity(0,set(range(8)))
from pathlib import Path
import json,hashlib,time
import numpy as np
R=Path(__file__).resolve().parents[1];P=R.parent.parent;E=P/'stages/e125_approximate_target_profiles_v1';C=json.loads((E/'config.locked.json').read_text());start=time.perf_counter();records={};identities={}
def ident(p):p=Path(p);v={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()};identities[str(p)]=v;return v
def dump(p,x):assert not p.exists();p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def unit(x):return x/np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)
for ds,dc in C['datasets'].items():
 c=dc['original']
 for p in [c['anchor']['ids'],c['fit_source']['queries_file'],c['fit_source']['gt_file'],E/'results'/ds/'labels/ids.i32',E/'models'/ds/'profiles.json',E/'models'/ds/'direction_diagnostic.npz']:ident(p)
ident(Path(__file__));ident(R/'protocol.md');ident(E/'config.locked.json');dump(R/'reviews/frozen.json',{'unix':time.time(),'files':identities})
for ds,dc in C['datasets'].items():
 t=time.perf_counter();c=dc['original'];d=c['dimension'];N=20000;raw=np.memmap(c['base'],'<f4',mode='r').reshape(-1,d+1);base=raw[:,1:];ids=np.fromfile(c['anchor']['ids'],'<i4');h=unit(np.array(base[ids],'f4'));q=unit(np.fromfile(c['fit_source']['queries_file'],'<f4').reshape(N,d));H=len(h);qn=(q.astype('f8')**2).sum(1)
 ex=np.fromfile(c['fit_source']['gt_file'],'<i8').reshape(N,100);ap=np.fromfile(E/'results'/ds/'labels/ids.i32','<i4').reshape(N,100);meta=json.loads((E/'models'/ds/'profiles.json').read_text());temp=meta['temperature'];aa=[];sums=[]
 for name,target in [('ExactAudit',ex),('ApproxTarget10',ap)]:
  a=np.zeros((N,H))
  for rank in range(10):
   z=unit(np.array(base[target[:,rank]],'f4'))
   for lo in range(0,N,4096):
    hi=min(lo+4096,N);sc=z[lo:hi]@h.T
    if temp is None:a[np.arange(lo,hi),sc.argmax(1)]+=.1
    else:
     sc=sc.astype('f8');sc-=sc.max(1,keepdims=True);sc/=temp;np.exp(sc,out=sc);sc/=sc.sum(1,keepdims=True);a[lo:hi]+=sc/10
  assert hashlib.sha256(a.tobytes()).hexdigest()==meta[name]['assignment_sha256'];aa.append(a);sums.append(a.T@q.astype('f8'))
 diag=np.load(E/'models'/ds/'direction_diagnostic.npz');v=diag['exact_v'];vp=diag['approx_v'];assert np.max(np.abs(sums[0]+h-v))<1e-9 and np.max(np.abs(sums[1]+h-vp))<1e-9
 a,apw=aa;delta=a-apw;sd=sums[0]-sums[1];var=((delta**2).T@qn-(sd**2).sum(1)/N)/(N-1);vary=((a**2).T@qn-(sums[0]**2).sum(1)/N)/(N-1);assert np.min(var)>-1e-12 and np.min(vary)>-1e-12;var=np.maximum(var,0);bias2=(sd**2).sum(1);norm2=(v**2).sum(1)
 audits=[]
 for j in np.linspace(0,H-1,16,dtype=int):
  dv=delta[:,j,None]*q.astype('f8');dv-=dv.mean(0);direct=float((dv**2).sum()/(N-1));assert abs(direct-var[j])<1e-10;audits.append({'hub':int(j),'trace_formula':float(var[j]),'trace_direct':direct})
 totals={}
 for name,w in [('raw_sum',np.ones(H)),('relative_to_exact_vector_norm',1/norm2)]:
  V=float(var@w);B=float(bias2@w);Y=float(vary@w);threshold=N*N*V/(B+N*V) if B+N*V>0 else None
  totals[name]={'sum_trace_residual_cov':V,'sum_trace_exact_contribution_cov':Y,'residual_to_exact_variance_ratio':V/Y,'direct_approx_squared_bias':B,'correction_MSE_formula':'(N*N/m-N)*sum_trace_residual_cov','critical_m_to_beat_direct_approx_vector_MSE':threshold,'critical_fraction':threshold/N if threshold is not None else None}
 overlap=float((ap[:,:10,None]==ex[:,None,:10]).any(axis=2).mean());record={'N':N,'H':H,'assignment_digest_restored':True,'exact_approx_vectors_restored':True,'teacher_top10_ID_recall_mean':overlap,'teacher_top1_ID_hit_rate':float((ap[:,0]==ex[:,0]).mean()),'mean_assignment_total_variation':float(np.abs(delta).sum(1).mean()/2),'maximum_assignment_total_variation':float(np.abs(delta).sum(1).max()/2),'totals':totals,'independent_trace_audits':audits,'seconds':time.perf_counter()-t};records[ds]=record;print(ds,json.dumps({k:v for k,v in record.items() if k!='independent_trace_audits'}),flush=True)
 np.savez_compressed(R/'results'/f'{ds}.npz',trace_residual_cov=var,trace_exact_cov=vary,approx_squared_bias=bias2,exact_vector_norm2=norm2)
 assert time.perf_counter()-start<120
 del aa,a,apw,delta,raw,base
for path,expected in identities.items():assert ident(path)==expected
dump(R/'results/summary.json',{'status':'PASS_TRAINING_DIAGNOSTIC','datasets':records,'seconds':time.perf_counter()-start,'new_GT':0,'new_searches':0,'new_candidate_profiles':0,'new_performance_points':0,'actual_arrays':'existing assignment and vector statistics reconstructed; no correction samples, W or router exported','source_queries':'original training only; no evaluation query access'});print('ALL PASS',round(time.perf_counter()-start,3),flush=True)
