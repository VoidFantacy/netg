import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
os.sched_setaffinity(0,{15})
from pathlib import Path
import json,time,hashlib,csv
import numpy as np
R=Path(__file__).resolve().parent;cfg=json.loads((R/'config.locked.json').read_text());started=time.time()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def write(name,rows):
 with (R/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
assert not (R/'complete.json').exists();assert sha(__file__)==cfg['source_sha256']
for x in cfg['inputs']:assert sha(x['path'])==x['sha256'],x['path']
stats=[];overlap=[];moments=[];unionstats=[];parts=[];supports=[];scope=[];moment={};gts={};qhash={};membership_checks=0
for ds,c in cfg['datasets'].items():
 for role,item in c['roles'].items():
  n=item['n'];gt=np.fromfile(item['GT'],item['GT_dtype']).reshape(n,100);q=np.fromfile(item['query'],'<f4').reshape(n,c['dimension']);assert np.all((gt>=0)&(gt<c['base_n'])) and np.isfinite(q).all();assert np.all(np.diff(np.sort(gt,axis=1),axis=1)>0)
  ids,counts=np.unique(gt[:,0],return_counts=True);norm=np.linalg.norm(q.astype('f8'),axis=1);assert np.all(norm>0);z=q.astype('f8')/norm[:,None];mu=z.mean(axis=0);cov=(z.T@z)/n-np.outer(mu,mu);assert np.trace(cov)>=0
  moment[ds,role]=(mu,cov);gts[ds,role]=gt;qhash[ds,role]={hashlib.sha256(row.tobytes()).digest() for row in q}
  stats.append(dict(dataset=ds,role=role,n=n,unique_GT1=len(ids),GT1_singleton_IDs=int((counts==1).sum()),GT1_repeat_query_mass_pct=100*float(counts[counts>1].sum())/n,GT1_pair_collision_pct=100*float((counts*(counts-1)).sum())/(n*(n-1)),unique_GT100=len(np.unique(gt)),query_byte_unique=len(qhash[ds,role]),query_norm_min=float(norm.min()),query_norm_median=float(np.median(norm)),query_norm_max=float(norm.max()),unit_query_mean_norm=float(np.linalg.norm(mu))))
  del z,q
 for a,b in [('QGT','fit'),('QGT','development'),('fit','development')]:
  x=gts[ds,a];y=gts[ds,b];overlap.append(dict(dataset=ds,source=a,target=b,source_n=len(x),target_n=len(y),target_GT1_in_source_GT1_pct=100*float(np.isin(y[:,0],x[:,0]).mean()),target_GT1_in_source_GT100_pct=100*float(np.isin(y[:,0],x).mean()),target_GT100_members_in_source_GT100_pct=100*float(np.isin(y,x).mean()),query_byte_intersection=len(qhash[ds,a]&qhash[ds,b])))
  ma,ca=moment[ds,a];mb,cb=moment[ds,b];d=float(np.linalg.norm(ma-mb));noise=float(np.trace(ca)/(len(x)-1)+np.trace(cb)/(len(y)-1));moments.append(dict(dataset=ds,source=a,target=b,unit_mean_distance=d,estimated_squared_mean_noise=noise,unbiased_squared_mean_difference=d*d-noise,centered_covariance_Frobenius=float(np.linalg.norm(ca-cb))))
 dev=gts[ds,'development'];train=gts[ds,'QGT'];seen1=np.isin(dev[:,0],train[:,0]);seen100=np.isin(dev[:,0],train);category=np.where(seen1,0,np.where(seen100,1,2));strict=np.fromfile(c['strict'],'u1').astype(bool)
 for method,item in c['methods'].items():
  rows=np.fromfile(item['rows'],'<i4').reshape(c['H'],65);un=np.unique(rows[rows>=0]);one=np.fromfile(item['GT1'],'u1').reshape(4096,c['H']);hit=np.isin(dev[:,0],un)&strict;assert np.array_equal(hit,one.any(axis=1));membership_checks+=len(dev)
  unionstats.append(dict(dataset=ds,method=method,H=c['H'],max_union_nodes=65*c['H'],actual_union_nodes=len(un),base_fraction_pct=100*len(un)/c['base_n'],development_GT1_certificate_pct=100*float(hit.mean()),target_mass_to_uniform_node_fraction_ratio=float(hit.mean())/(len(un)/c['base_n'])))
  recovered=0
  for i,label in enumerate(['seen_QGT_GT1','seen_QGT_GT2_to_100_only','unseen_QGT_GT100']):
   mask=category==i;count=int((hit&mask).sum());recovered+=count;parts.append(dict(dataset=ds,method=method,target_support=label,all_development_queries=4096,category_queries=int(mask.sum()),certified_queries=count,contribution_of_all_queries_pp=100*count/4096))
  assert recovered==int(hit.sum())
 manifest=json.loads(Path(c['profile_manifest']).read_text());supports.append(dict(dataset=ds,profile=manifest['name'],fit_n=manifest['assignments_shape'][0],H=manifest['assignments_shape'][1],mass_median=manifest['support']['mass']['median'],ESS_median=manifest['support']['ess']['median'],query_max_weight_median=manifest['support']['query_max_weight']['median'],prior_fraction_median=manifest['prior_fraction']['median'],actual_profile_SHA=sha(manifest['W'])))
 scope.append(dict(dataset=ds,QGT_source=c['QGT_source'],fit_source=c['fit_source'],development_source=c['development_source']))
 assert time.time()-started<180
for name,rows in [('target_support.csv',stats),('source_target_overlap.csv',overlap),('query_moments.csv',moments),('closed_neighborhood_union.csv',unionstats),('certificate_source_decomposition.csv',parts),('current_profile_support.csv',supports)]:write(name,rows)
dump(R/'source_scope.json',scope)
for x in cfg['inputs']:assert sha(x['path'])==x['sha256']
dump(R/'complete.json',dict(status='PASS_DESCRIPTIVE_SOURCE_AUDIT',seconds=time.time()-started,NSG_calls=0,ANN_calls=0,new_GT=0,new_training=0,new_graphs=0,E112_stop_unchanged=True,held_out_payload_access=False,posthoc_diagnostic=True,all_inputs_reverified=True,independent_union_membership_checks=membership_checks,outputs=[ident(p) for p in R.glob('*.csv')]+[ident(R/'source_scope.json')]))
print(json.dumps(dict(status='PASS_DESCRIPTIVE_SOURCE_AUDIT',seconds=time.time()-started,stats=stats,overlap=overlap,moments=moments,unions=unionstats,parts=parts,supports=supports),ensure_ascii=False,indent=2))
