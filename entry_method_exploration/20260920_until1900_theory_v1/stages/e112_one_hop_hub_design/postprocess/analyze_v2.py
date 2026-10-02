import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
os.sched_setaffinity(0,{15})
import json,time,hashlib,csv
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''):h.update(b)
 return h.hexdigest()
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def csvwrite(p,rows):
 with Path(p).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
cfg=read(R/'config.locked.json');assert read(R/'reviews/label_complete.json')['status']=='PASS';assert not (R/'reviews/numeric_verification.json').exists();started=time.time()
assert sha(Path(__file__))==read(R/'reviews/analysis_v2_lock.json')['source']['sha256']
coverage=[];support=[];paired=[];rescue=[];raw=[];stored={};membership_checks=0;greedy_checks=0
for ds,c in cfg['datasets'].items():
 for role,n,qpath,gpath in [('QGT',5000,c['QGT_queries'],c['QGT_GT']),('development',4096,c['development_queries'],c['development_GT'])]:
  directory=R/'results'/(role+'_'+ds);gt=np.fromfile(gpath,'<i4').reshape(n,100);strict=np.fromfile(directory/'strict_GT1.u8','u1');assert strict.shape==(n,) and np.isin(strict,[0,1]).all()
  checked=np.floor(np.arange(64)*n/64).astype(int);stored[(ds,role)]={}
  for method in cfg['methods']:
   p=directory/method;h=c['H'];ids=np.fromfile(p/'hub_ids.i32','<i4');rows=np.fromfile(p/'closed_rows.i32','<i4').reshape(h,65)
   a=np.fromfile(p/'score.u8','u1').reshape(n,h);one=np.fromfile(p/'GT1.u8','u1').reshape(n,h);count=np.fromfile(p/'GT100_count.u8','u1').reshape(n,h)
   assert len(ids)==h and len(np.unique(ids))==h and np.isin(one,[0,1]).all() and np.all(count<=65)
   assert np.array_equal(a.astype('u2'),100*one.astype('u2')+count) and np.all(one<=strict[:,None]) and np.all(count>=one)
   assert np.all((rows==-1)|((rows>=0)&(rows<c['base_n'])))
   for i in range(h):valid=rows[i][rows[i]>=0];assert ids[i] in valid and len(np.unique(valid))==len(valid) and np.all(np.diff(valid)>0)
   for i in checked:
    expected=np.isin(rows,gt[i]).sum(axis=1);expected_one=np.any(rows==gt[i,0],axis=1)&bool(strict[i])
    assert np.array_equal(expected,count[i]) and np.array_equal(expected_one,one[i]);membership_checks+=h
   f=a.max(axis=1).astype(float)/200;anyone=one.any(axis=1);best100=count.max(axis=1).astype(float)/100
   self_hit=np.isin(gt[:,0],ids)&strict.astype(bool);edge_hit=np.any(one.astype(bool)&(ids[None,:]!=gt[:,0,None]),axis=1)
   record=dict(dataset=ds,role=role,method=method,n=n,H=h,F_mean_pct=100*f.mean(),GT1_any_pct=100*anyone.mean(),GT100_max_pct=100*best100.mean(),strict_GT1_queries=int(strict.sum()),GT1_self_pct=100*self_hit.mean(),GT1_nonself_edge_pct=100*edge_hit.mean())
   coverage.append(record);stored[(ds,role)][method]=dict(F=f,GT1=anyone,GT100=best100,ids=ids)
   complete=read(p/'complete.json');assert complete['objective_integer']==int(a.max(axis=1).astype('u8').sum())
   for file in p.iterdir():
    if file.is_file():raw.append(ident(file))
   if role=='QGT':
    positives=np.count_nonzero(a,axis=0);firsts=np.count_nonzero(one,axis=0)
    support.append(dict(dataset=ds,method=method,H=h,positive_QGT_min=int(positives.min()),positive_QGT_median=float(np.median(positives)),positive_QGT_max=int(positives.max()),GT1_QGT_min=int(firsts.min()),GT1_QGT_median=float(np.median(firsts)),GT1_QGT_max=int(firsts.max()),old_H_overlap=int(np.isin(ids,np.fromfile(c['old_hub_ids'],'<i4')).sum()),H_equal_QGT_GT1=int(np.isin(ids,gt[:,0]).sum())))
  raw.extend(ident(directory/f) for f in ['strict_GT1.u8','GT1_GT2.distances.f32','complete.json'])
  if role=='QGT':
   offset=np.memmap(directory/'all_base.offset.u64',dtype='<u8',mode='r');qi=np.memmap(directory/'all_base.query.u16',dtype='<u2',mode='r');value=np.memmap(directory/'all_base.score.u8',dtype='u1',mode='r')
   assert offset.shape==(c['base_n']+1,) and offset[0]==0 and offset[-1]==len(qi)==len(value) and np.all(offset[1:]>=offset[:-1])
   assert np.all(qi<n) and np.all((value>0)&(value<=165))
   boundary=np.zeros(len(qi),dtype=bool);starts=np.asarray(offset[:-1]);boundary[starts[starts<len(qi)]]=True;assert np.all((qi[1:]>qi[:-1])|boundary[1:]);del boundary,starts
   best=np.zeros(n,dtype='u1');objective=0;seen=set();trace=read(directory/'greedy_selection.json')
   for step in trace:
    h=step['id'];assert h not in seen;seen.add(h);sl=slice(int(offset[h]),int(offset[h+1]));qq=np.asarray(qi[sl]);vv=np.asarray(value[sl]);gain=int(np.maximum(vv.astype('i2')-best[qq].astype('i2'),0).sum())
    assert gain==step['gain_integer'] and gain>=step['remaining_heap_gain_upper'];best[qq]=np.maximum(best[qq],vv);objective+=gain;assert objective==step['objective_integer'];greedy_checks+=1
   assert np.array_equal(best,np.fromfile(directory/'greedy_best_score.u8','u1'))
   assert objective==read(directory/'GraphH/complete.json')['objective_integer'];assert seen.issubset(set(stored[(ds,role)]['GraphH']['ids']))
   raw.extend(ident(directory/f) for f in ['all_base.offset.u64','all_base.query.u16','all_base.score.u8','greedy_selection.json','greedy_best_score.u8'])
  else:
   predicted=np.fromfile(c['default_K1'],'<i4');assert predicted.shape==(n,);failed=predicted!=gt[:,0]
   for method in cfg['methods']:
    r=stored[(ds,role)][method]['GT1']&failed
    rescue.append(dict(dataset=ds,method=method,n=n,baseline='GT10Default_K1_L128',baseline_GT1_failures=int(failed.sum()),conditionally_rescuable_failures=int(r.sum()),conditional_rescue_pp=100*r.mean(),new_search_executed=False,privileged_baseline_or_single_choice=True))
  del a,one,count
 rng=np.random.default_rng(cfg['bootstrap_seed']);base=stored[(ds,'development')]['GraphH']['F'];diff=np.stack([base-stored[(ds,'development')][m]['F'] for m in ['OriginalH','FrequencyH']]);boot=np.empty((2,cfg['bootstrap_replicates']))
 for begin in range(0,cfg['bootstrap_replicates'],128):
  end=min(begin+128,cfg['bootstrap_replicates']);indices=rng.integers(0,4096,size=(end-begin,4096));boot[:,begin:end]=diff[:,indices].mean(axis=2)
 tail=(1-cfg['CI_level'])/2
 for i,control in enumerate(['OriginalH','FrequencyH']):
  lo,hi=np.quantile(boot[i],[tail,1-tail]);paired.append(dict(dataset=ds,candidate='GraphH',control=control,n=4096,mean_F_delta_pp=100*diff[i].mean(),CI_level=cfg['CI_level'],CI_lower_pp=100*lo,CI_upper_pp=100*hi))
decisions=[]
for ds in cfg['datasets']:
 pairs=[x for x in paired if x['dataset']==ds];original=next(x for x in pairs if x['control']=='OriginalH');r=next(x for x in rescue if x['dataset']==ds and x['method']=='GraphH')
 clauses=dict(F_gain_over_original_at_least_2pp=bool(original['mean_F_delta_pp']>=2),both_CI_lower_positive=all(x['CI_lower_pp']>0 for x in pairs),conditional_GT1_rescue_at_least_1pp=r['conditional_rescue_pp']>=1)
 decisions.append(dict(dataset=ds,clauses=clauses,pass_all=all(clauses.values())))
gate=dict(status='PASS_H_INFORMATION_GATE_NEEDS_REAL_SEARCH' if all(x['pass_all'] for x in decisions) else 'STOP_ONE_HOP_H_DESIGN_INFORMATION_GATE',datasets=decisions,new_NSGruns=0,actual_deployable_Recall_improvement_proven=False,coverage_score_is_conditional=True,baseline_oracle_choice_is_privileged=True)
for name,rows in [('certificate_coverage.csv',coverage),('selected_H_support.csv',support),('paired_information.csv',paired),('conditional_rescue.csv',rescue)]:csvwrite(R/'results'/name,rows)
dump(R/'results/gate.json',gate)
dump(R/'reviews/numeric_verification.json',dict(status='PASS',independent_membership_checks=membership_checks,greedy_prefix_checks=greedy_checks,all_sparse_row_order_checked=True,integer_score_arithmetic_checked=True,all_queries_retained=True,raw_files=raw,analysis_source=ident(Path(__file__)),seconds=time.time()-started))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
(R/'figures').mkdir(exist_ok=True);fig,axes=plt.subplots(1,2,figsize=(10,4),sharey=True);plot_upper=min(100,10*np.ceil((max(x['F_mean_pct'] for x in coverage)+5)/10))
for ax,ds in zip(axes,cfg['datasets']):
 for j,role in enumerate(['QGT','development']):
  values=[next(x['F_mean_pct'] for x in coverage if x['dataset']==ds and x['role']==role and x['method']==m) for m in cfg['methods']]
  bars=ax.bar(np.arange(3)+(j-.5)*.35,values,width=.35,label=role)
  ax.bar_label(bars,fmt='%.1f',fontsize=8)
 ax.set_xticks(np.arange(3),cfg['methods']);ax.set_title('WebVid' if ds.startswith('web') else 'Yandex');ax.set_ylabel('Conditional joint coverage F (%)');ax.set_ylim(0,plot_upper);ax.legend();ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
fig.suptitle('Same QGT source and hub count; not deployed Recall');fig.tight_layout();fig.savefig(R/'figures/conditional_coverage.png',dpi=170);fig.savefig(R/'figures/conditional_coverage.pdf');plt.close(fig)
dump(R/'reviews/analysis_complete.json',dict(status='PASS',seconds=time.time()-started,gate=gate,source=ident(Path(__file__))))
dump(R/'state.json',dict(status='INFORMATION_ANALYSIS_COMPLETE',decision=gate['status'],pending=['visual inspection','interpretation and stage closeout']))
print(json.dumps(dict(gate=gate,paired=paired,coverage=coverage,rescue=rescue,seconds=time.time()-started),ensure_ascii=False,indent=2))
