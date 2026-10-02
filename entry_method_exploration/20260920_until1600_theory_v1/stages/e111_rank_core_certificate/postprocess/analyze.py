import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
import sys,json,time,csv,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];TB=R.parents[1];E=R.parent/'e107_initialization_factorial'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''):h.update(b)
 return h.hexdigest()
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
assert read(R/'reviews/topology_complete.json')['status']=='PASS' and not (R/'reviews/analysis_complete.json').exists();started=time.time();lock=read(R/'config.locked.json')
dump(R/'reviews/analysis_lock.json',dict(created_unix=started,source=ident(Path(__file__)),gate_coverage_definition='Current GT10Exact3 certificate hits divided by its actual GT1 hits at L128; all-H coverage also reported but not substituted.',no_numeric_certificate_outputs_read_before_this_lock=True))
datasets=read(E/'config.locked.json')['datasets'];rows=[];availability=[];rescue=[];raw=[];gates=[];boundary=[];violation_records=[]
for ds,original in datasets.items():
 c=read(R/'reviews'/(ds+'.json'));n=c['n'];h=c['H'];gt=np.fromfile(c['GT'],'<i4').reshape(n,100);ip=np.fromfile(c['GT_IP'],'<f4').reshape(n,100);assert np.isfinite(ip).all() and np.all(np.diff(ip,axis=1)<=0)
 gap=ip[:,63]-ip[:,64];boundary.append(dict(dataset=ds,m64_boundary_equal_count=int((gap==0).sum()),m64_min_stored_score_gap=float(gap.min()),GT1_GT2_stored_score_ties=int((ip[:,0]==ip[:,1]).sum()),m100_external_boundary_unobserved=True,GT_source_inherited_no_full_base_rescore=True));base=np.memmap(c['base'],dtype='<f4',mode='r').reshape(c['base_n'],c['dimension']+1)[:,1:];queries=np.fromfile(c['queries'],'<f4').reshape(n,c['dimension'])
 top=R/'results'/ds;complete=read(top/'complete.json');assert complete['status']=='PASS' and complete['NSG_calls']==0 and complete['ANN_calls']==0
 allh={}
 for m in [64,100]:
  cnt=np.fromfile(top/f'all_H_m{m}_count.u8','u1').reshape(n,h);one=np.fromfile(top/f'all_H_m{m}_GT1.u8','u1').reshape(n,h);assert cnt.max()<=m and one.max()<=1 and np.all(cnt>=one);allh[m]=(cnt,one)
  availability.append(dict(dataset=ds,m=m,any_H_GT1_certificate_queries=int(one.any(1).sum()),any_H_GT1_certificate_pct=float(one.any(1).mean()*100),mean_H_GT1_certificates=float(one.sum(1).mean()),median_H_GT1_certificates=float(np.median(one.sum(1))),any_H_positive_core_queries=int(cnt.any(1).sum()),mean_max_H_certified_count=float(cnt.max(1).mean()),max_H_complete_core_queries=int((cnt.max(1)==m).sum())))
 hits={};certificate={}
 for method in c['methods']:
  name=method['name'];certs={}
  for m in [64,100]:
   words=np.fromfile(top/name/f'm{m}.mask.u64','<u8').reshape(n,2);full=np.unpackbits(words.view('u1'),axis=1,bitorder='little').astype(bool);assert not full[:,m:].any();certs[m]=full[:,:100]
  for K,Ls in c['K_L'].items():
   K=int(K)
   for L in Ls:
    m=64 if K==1 and L==64 else 100;cert=certs[m];p=Path(method['reference_results'])/f'k{K}_L{L}';ids=np.fromfile(p/'ids.i32','<i4').reshape(n,K);mask=(ids[:,:,None]==gt[:,None,:K]).any(1);hit=mask.sum(1);cc=cert[:,:K]
    violations=cc&~mask
    for qi,rank in np.argwhere(violations):
     target=int(gt[qi,rank]);vec=np.asarray(base[target]);output=np.asarray(base[ids[qi]]);equiv=ids[qi][np.all(output.view('<u4')==vec.view('<u4'),axis=1)];target_ip=float(queries[qi].astype('float64')@vec.astype('float64'));returned_ip=output.astype('float64')@queries[qi].astype('float64')
     violation_records.append(dict(dataset=ds,method=name,K=K,L=L,m=m,query_index=int(qi),GT_rank=int(rank+1),target_id=target,byte_identical_returned_ids=equiv.tolist(),byte_duplicate_explanation=bool(len(equiv)),target_IP_float64=target_ip,returned_best_IP_float64=float(returned_ip.max()),returned_last_IP_float64=float(returned_ip[-1]),stored_GT_IP=float(ip[qi,rank]),GT_row_has_K_boundary_tie=bool(ip[qi,0]==ip[qi,1]) if K==1 else None))
    cv=cc.sum(1);hits[name,K,L]=hit;certificate[name,K,L]=cv
    rows.append(dict(dataset=ds,method=name,K=K,L=L,m=m,n=n,certified_recall=float(cv.mean()/K),actual_recall=float(hit.mean()/K),certified_fraction_of_actual_hits=float(cv.sum()/hit.sum()),queries_with_certificate=int((cv>0).sum()),actual_zero_queries=int((hit==0).sum()),certificate_violations=int(violations.sum()),conditional_on_GT_rank_and_tie_semantics=True,new_performance_measurement=False))
    raw.append(ident(p/'ids.i32'))
 for name in ['GT103','GT101','UnitHub3','DefaultANN']:
  for K in [1,100]:
   hit=hits[name,K,128];cnt,one=allh[100];best=one.max(1) if K==1 else cnt.max(1);delta=np.maximum(best.astype('int64')-hit,0)
   rescue.append(dict(dataset=ds,baseline=name,K=K,L=128,guaranteed_extra_GT_members=int(delta.sum()),guaranteed_rescue_queries=int((delta>0).sum()),guaranteed_recall_improvement_lower_bound_pp=float(delta.mean()/K*100),current_certificate_fraction_of_actual_hits=float(certificate[name,K,128].sum()/hit.sum()),any_H_certified_fraction_among_current_hit_queries=float(one.any(1)[hit>0].mean()),privileged_choose_baseline_or_single_H=True,not_actual_search_oracle_upper_bound=True,online_cost_unmeasured=True))
 main=next(x for x in rescue if x['dataset']==ds and x['baseline']=='GT103' and x['K']==1);passed=main['guaranteed_recall_improvement_lower_bound_pp']>=1 and main['current_certificate_fraction_of_actual_hits']>=.25;gates.append(dict(dataset=ds,guaranteed_GT1_rescue_pp=main['guaranteed_recall_improvement_lower_bound_pp'],current_success_certificate_fraction=main['current_certificate_fraction_of_actual_hits'],passed=passed))
 for p in top.rglob('*'):
  if p.is_file():raw.append(ident(p))
 s=Path(original['index']).stat();assert s.st_size==original['index_stat']['bytes'] and s.st_mtime_ns==original['index_stat']['mtime_ns']
 print(ds,'certificate inclusion and coverage complete',flush=True)
for ref in [E,R.parent/'e110_first_expansion_intervention']:
 for x in read(ref/'reviews/numeric_verification.json')['raw_files']:assert sha(x['path'])==x['sha256'],x['path']
for x in read(R/'reviews/protected_before.json')+read(R/'reviews/source_freeze.json')['files']:assert sha(x['path'])==x['sha256'],x['path']
def table(name,data):
 with (R/'results'/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
table('certificate_coverage.csv',rows);table('all_H_availability.csv',availability);table('guaranteed_rescue_lower_bound.csv',rescue);dump(R/'results/GT_boundary.json',boundary)
no_violations=not violation_records;gate=dict(status='STOP_CERTIFICATE_ID_GUARANTEE_TIE_MISMATCH' if not no_violations else 'PROMISING_CERTIFICATE_SUPERVISION_INFORMATION' if all(x['passed'] for x in gates) else 'STOP_CERTIFICATE_SUPERVISION_INFORMATION',datasets=gates,zero_member_violations=no_violations,identity_member_violations=len(violation_records),byte_duplicate_explained_violations=sum(x['byte_duplicate_explanation'] for x in violation_records),points_checked=len(rows),conditional_on_GT_rank_and_tie_semantics=True,no_training=True,default_changed=False,new_NSG_calls=0,new_ANN_calls=0,new_GT=0,new_graphs=0,graph_derived_labels=True);dump(R/'results/gate.json',gate);dump(R/'results/identity_violation_records.json',violation_records)
fig,axes=plt.subplots(1,2,figsize=(12,4.6),constrained_layout=True)
for i,ds in enumerate(datasets):
 ax=axes[i];sel=[x for x in rows if x['dataset']==ds and x['L']==128 and x['method'] in ['NSGFixed1','UnitHub1','UnitHub3','GT101','GT103','DefaultANN','PrimaryFirst3']]
 names=['NSGFixed1','UnitHub1','UnitHub3','GT101','GT103','DefaultANN','PrimaryFirst3'];x=np.arange(len(names))
 for K,off,color in [(1,-.18,'tab:blue'),(100,.18,'tab:orange')]:ax.bar(x+off,[100*next(z['certified_fraction_of_actual_hits'] for z in sel if z['method']==name and z['K']==K) for name in names],.36,label=f'K={K}',color=color)
 ax.set_xticks(x,names,rotation=35,ha='right');ax.set_ylabel('Certified share of actual GT hits (%)');ax.set_title('WebVid' if i==0 else 'Yandex');ax.legend();ax.grid(axis='y',alpha=.2)
fig.suptitle('Retained-core conditional reachability | L=128, m=100\nIdentity tie mismatches are retained; no new NSG searches')
for ext in ['png','pdf']:fig.savefig(R/'figures'/('certificate_coverage.'+ext),dpi=160)
plt.close(fig);dump(R/'reviews/numeric_verification.json',dict(status='PASS_FULL_VIOLATION_AUDIT',raw_files=raw,points=len(rows),member_violations=len(violation_records),full_query_coverage=True,existing_E107_E110_outputs_hash_verified=True,zero_violation_gate_failed=not no_violations));dump(R/'reviews/analysis_complete.json',dict(status='PASS',seconds=time.time()-started,gate=gate));dump(R/'state.json',dict(status='CERTIFICATE_ANALYZED',decision=gate['status'],pending=['report','closeout']));print(json.dumps(gate,indent=2))
