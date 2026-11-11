from common import *
rows=[]
for ds in DS:
 c=read(OLD/f'configs/{ds}.json');g=np.asarray(gt(c['test_gt']));n=len(g)
 for K in [1,100]:
  b=Path(c['output_dir'])/f'k{K}';a=arr(b/'GT10_L200/raw/ids.i32','<i4').reshape(n,K);z=arr(b/'REUSE-SQ_L200/raw/ids.i32','<i4').reshape(n,K);ha=mask(a,g,K);hz=mask(z,g,K);y=hz.sum(1).astype(int)-ha.sum(1);res=(hz&~ha).sum(1);loss=(ha&~hz).sum(1)
  pos=y[y>0];rows.append(dict(dataset=ds,K=K,n=n,main_recall=ha.mean(),sq_recall=hz.mean(),net_members=int(y.sum()),rescued=int(res.sum()),lost=int(loss.sum()),improved_queries=int((y>0).sum()),harmed_queries=int((y<0).sum()),oracle_on_rate=float((y>0).mean()),gain_top_1pct=int(np.sort(y)[::-1][:max(1,n//100)].sum()),gain_top_10pct=int(np.sort(y)[::-1][:max(1,n//10)].sum())))
  if ds in ANCHORS:
   ind=np.fromfile(R/f'storage/inputs/{ds}/test_indices.i32','<i4');out=R/f'storage/oracle/{ds}';out.mkdir(parents=True,exist_ok=True);np.asarray(y[ind]>0,np.uint8).tofile(out/f'k{K}.u8')
 print('diagnosed',ds,flush=True)
csvwrite(R/'analysis/seven_dataset_heterogeneity.csv',rows);dump(R/'reviews/diagnostics.json',dict(status='PASS_OLD_ACTUAL_RETURNS_REANALYSIS',cases=14,GT_used='diagnostic oracle only'))
