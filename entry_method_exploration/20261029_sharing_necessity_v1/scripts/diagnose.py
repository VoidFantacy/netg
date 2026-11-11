"""Finite support bounds and prespecified reassignment diagnostics, no ANN timing."""
import collections,time
from common import *
def covered(missing,blocks,pool):
 return (missing & (blocks[:,:,None]==pool[:,None,:]).any(2)).sum(1).astype('<i2')
def main():
 t=time.perf_counter();summary=[];perms=[];strata=[];nearest=[];witnesses=[]
 for ds in DS:
  c=read(OLD/f'configs/{ds}.json');g=gt(c['test_gt']);n=len(g);model=read(Path(c['models'])/'model.json');ib=arr(model['files']['id_block'],'<i4');tab=arr(model['files']['hub_blocks'],'<i4').reshape(-1,8);hubs=arr(c['router']['ids'],'<i4');slot={int(z):j for j,z in enumerate(hubs)}
  source=np.zeros(c['base']['n'],bool);source[arr(Path(c['source_dir'])/'global_ids.i32','<i4')]=True
  nn=np.load(R.parent/f'20261024_manifold_residual_probe_v1/analysis/{ds}.npz')
  qrows=nn['query_rows'];saved={}
  for K in [1,100]:
   root=OLD/'storage/results'/ds/f'k{K}';mainids=arr(root/'GT10_L200/raw/ids.i32','<i4').reshape(n,K);base=mask(mainids,g,K);missing=~base;mb=ib[g[:,:K]];in_source=missing&source[g[:,:K]]
   routes=arr(root/'GT10_L200/raw/entry_ids.i32','<i4').reshape(n,3);slots=np.array([[slot[int(v)] for v in row] for row in routes],dtype=int)
   traces={m:arr(root/f'{m}_L200/trace.i32','<i4').reshape(n,160) for m in ['REUSE-SQ','MAIN-SQ']}
   mainpool=traces['MAIN-SQ'][:,:8];nativepool=traces['REUSE-SQ'][:,:32]
   # Validate main block proposals by a separate Counter implementation on all rows.
   for i,row in enumerate(mainids):
    freq=collections.Counter(map(int,ib[row]));expected=sorted([b for b,_ in sorted(freq.items(),key=lambda x:(-x[1],x[0]))[:8]])
    assert expected==sorted(map(int,mainpool[i][mainpool[i]>=0]))
   normalpool=np.concatenate([mainpool,tab[slots].reshape(n,24)],1)
   assert all(set(map(int,normalpool[i]))-{ -1 }==set(map(int,nativepool[i]))-{ -1 } for i in range(n))
   normalcov=covered(missing,mb,normalpool);maincov=covered(missing,mb,mainpool);scancov=covered(missing,mb,traces['REUSE-SQ'][:,32:64]);b32=mask(arr(root/'B32_L200/raw/ids.i32','<i4').reshape(n,K),g,K)
   assert np.all((b32&~base).sum(1)<=in_source.sum(1));b32out=int((b32&~base&~source[g[:,:K]]).sum());assert b32out==0
   values=[]
   for j in range(32):
    mapping=arr(R/f'storage/models/{ds}/permutation{j:02d}.i32','<i4');pool=np.concatenate([mainpool,tab[mapping[slots]].reshape(n,24)],1);cov=covered(missing,mb,pool);values.append(cov)
    perms.append(dict(dataset=ds,K=K,L=200,permutation=j,seed=20261029+j,pool_missing_covered=int(cov.sum()),normal_pool_missing_covered=int(normalcov.sum()),pool_oracle_delta_pp=100*int(cov.sum())/(n*K),normal_minus_permuted_members=int(normalcov.sum()-cov.sum())))
   vals=np.stack(values);saved[f'k{K}_normal_pool']=normalcov;saved[f'k{K}_permuted_pool']=vals;saved[f'k{K}_main_pool']=maincov;saved[f'k{K}_missing']=missing.sum(1).astype('<i2')
   normal_out=None
   for method in ['REUSE-SQ','MAIN-SQ']:
    final=arr(root/f'{method}_L200/raw/ids.i32','<i4').reshape(n,K);fm=mask(final,g,K);resc=fm&missing;dam=base&~fm;rescq=resc.sum(1);damq=dam.sum(1);outside=(resc&~source[g[:,:K]]).sum(1);oldavailable=in_source.sum(1);zero=(missing.sum(1)>0)&(oldavailable==0)
    if method=='REUSE-SQ':normal_out=int(outside.sum())
    strata.append(dict(dataset=ds,K=K,method=method,stratum='missing_outside_entire_old_source',queries=int(zero.sum()),missing_members=int(missing[zero].sum()),rescued_members=int(rescq[zero].sum()),damaged_members=int(damq[zero].sum()),improved_queries=int((rescq[zero]>damq[zero]).sum())))
    for label,cond in [('nearest_GT_zero',nn['nearest_GT_overlap']==0),('nearest_GT_positive',nn['nearest_GT_overlap']>0),('nearest_missing_zero',nn['nearest_missing_covered']==0),('nearest_missing_positive',nn['nearest_missing_covered']>0)]:
     ix=qrows[cond]
     nearest.append(dict(dataset=ds,K=K,method=method,stratum=label,queries=len(ix),missing_members=int(missing[ix].sum()),rescued_members=int(rescq[ix].sum()),damaged_members=int(damq[ix].sum()),improved_queries=int((rescq[ix]>damq[ix]).sum()),source_out_rescued=int(outside[ix].sum())))
    # Retain up to three deterministic actual-ID counterexamples per stratum.
    for i in np.flatnonzero(zero & (rescq>0))[:3]:
     witnesses.append(dict(dataset=ds,K=K,method=method,query=int(i),test_GT=list(map(int,g[i,:K])),main_return=list(map(int,mainids[i])),rescued_ids=list(map(int,g[i,:K][resc[i]])),old_source_covered_missing=0,scope='Actual E191 return; no shared missing ID with entire old source; not zero block sharing.'))
   total=int(missing.sum());avg=vals.sum(1)
   summary.append(dict(dataset=ds,K=K,L=200,n=n,missing_members=total,old_source_covered=int(in_source.sum()),fixed_ID_ceiling_pp=100*int(in_source.sum())/(n*K),B32_rescued=int((b32&~base).sum()),B32_source_out=b32out,normal_pool_covered=int(normalcov.sum()),main_pool_covered=int(maincov.sum()),normal_scanned_covered=int(scancov.sum()),block_pool_ceiling_pp=100*int(normalcov.sum())/(n*K),permuted_pool_mean=float(avg.mean()),permuted_pool_min=int(avg.min()),permuted_pool_max=int(avg.max()),normal_above_all_32=bool(normalcov.sum()>avg.max()),SQ_source_out_rescued=normal_out))
  np.savez_compressed(R/f'analysis/{ds}.npz',**saved)
  print(json.dumps(dict(dataset=ds,status='DIAGNOSTIC_COMPLETE')),flush=True)
 csvwrite(R/'analysis/support_bounds.csv',summary);csvwrite(R/'analysis/permutation_pool.csv',perms);csvwrite(R/'analysis/zero_source_strata.csv',strata);csvwrite(R/'analysis/nearest_query_strata.csv',nearest);dump(R/'analysis/actual_counterexamples.json',witnesses)
 # Analytic counterexample: arbitrarily close positive L2 queries, disjoint GT1,
 # a training-miss block contains an unseen missing ID and repairs the test.
 eps=.001;x=np.array([0.,2.]);qt=1-eps;q=1+eps;gttrain=int(np.argmin((x-qt)**2));gttest=int(np.argmin((x-q)**2));train_source={gttrain};main={gttrain};block={0,1};final=min(main|block,key=lambda i:(x[i]-q)**2)
 assert gttrain!=gttest and gttest not in train_source and final==gttest
 dump(R/'analysis/mathematical_counterexample.json',dict(status='PASS_EXECUTABLE_COUNTEREXAMPLE',base=x.tolist(),train_query=qt,test_query=q,query_distance=abs(qt-q),GT1_train=gttrain,GT1_test=gttest,training_missing_IDs=sorted(train_source),assumed_test_main_return=sorted(main),proposed_block=sorted(block),final_return=final,claim_refuted='No shared GT/missed ID implies every block completion has zero quality gain.',scope='Mathematical finite candidate model; not a measured ANN/QPS result.'))
 dump(R/'reviews/diagnostic_complete.json',dict(status='PASS_FROZEN_E192_DIAGNOSTICS',support_rows=len(summary),permutation_rows=len(perms),zero_source_rows=len(strata),nearest_strata_rows=len(nearest),actual_counterexamples=len(witnesses),seconds=time.perf_counter()-t))
if __name__=='__main__':main()
