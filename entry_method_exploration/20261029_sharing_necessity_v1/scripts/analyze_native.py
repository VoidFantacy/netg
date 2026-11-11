"""Quality, coverage and same-window complete-cost controls from actual timed packets."""
import collections,gzip,statistics,time
from common import *
def main():
 ds=sys.argv[1];root=R/'storage/results'/ds;out=R/'analysis'/ds;out.mkdir();t=time.perf_counter();c=read(root/'config.json');done=read(root/'complete.json');g=gt(c['test_gt']);n=len(g);K=100;model=read(Path(c['models'])/'model.json');ib=arr(model['files']['id_block'],'<i4');source=np.zeros(c['base']['n'],bool);source[arr(Path(c['source_dir'])/'global_ids.i32','<i4')]=True
 masks={};points=[];pairs=[];covers=[];queries=[]
 for rr in done['results']:
  p=Path(rr['result_dir']);ids=arr(p/'raw/ids.i32','<i4').reshape(n,K);z=mask(ids,g,K);masks[rr['method'],rr['L']]=z;qs=[x['qps'] for x in rr['rounds']];assert len(qs)==3
  points.append(dict(dataset=ds,K=K,method=rr['method'],L=rr['L'],n=n,hits=int(z.sum()),recall_pct=100*int(z.sum())/(n*K),qps=rr['qps'],qps_min=min(qs),qps_max=max(qs),qps_round0=qs[0],qps_round1=qs[1],qps_round2=qs[2],scanned_codes_per_query=rr['scanned_codes_per_query'],exact_scores_per_query=rr['extra_exact_scores_per_query'],block_centres_per_query=rr['block_centres_per_query'],failed_lt10=int((z.sum(1)<10).sum()),complete_queries=int((z.sum(1)==K).sum())))
 base=masks['GT10',200];b=next(x for x in points if x['method']=='GT10' and x['L']==200);controls=[x for x in points if x['method']=='GT10'];mainids=arr(root/'k100/GT10_L200/raw/ids.i32','<i4').reshape(n,K)
 for x in points:
  m=x['method'];L=x['L']
  if m=='GT10':continue
  z=masks[m,L];new=z&~base;lost=base&~z;bh=base.sum(1);h=z.sum(1);outside=new&~source[g[:,:K]]
  target=[v for v in controls if v['hits']>=x['hits']];target=max(target,key=lambda v:v['qps']) if target else None;budget=[v for v in controls if v['qps']>=x['qps']];budget=max(budget,key=lambda v:v['hits']) if budget else None;dom=[v for v in controls if v['hits']>=x['hits'] and v['qps']>=x['qps']]
  p=dict(dataset=ds,K=K,method=m,L=L,recall_delta_pp=x['recall_pct']-b['recall_pct'],qps=x['qps'],extra_time_pct=100*(b['qps']/x['qps']-1),members_missing=int((~base).sum()),members_rescued=int(new.sum()),members_damaged=int(lost.sum()),rescued_source_out=int(outside.sum()),improved_queries=int((h>bh).sum()),worsened_queries=int((h<bh).sum()),original_lt10=int((bh<10).sum()),final_lt10=int((h<10).sum()),lt10_escaped=int(((bh<10)&(h>=10)).sum()),target_GT_L=target['L'] if target else '',target_GT_recall_pct=target['recall_pct'] if target else '',target_GT_qps=target['qps'] if target else '',target_speed_delta_pct=100*(x['qps']/target['qps']-1) if target else '',budget_GT_L=budget['L'] if budget else '',budget_recall_delta_pp=x['recall_pct']-budget['recall_pct'] if budget else '',dominated_by_GT_L=','.join(str(v['L']) for v in dom));pairs.append(p)
  for i in range(n):queries.append(dict(dataset=ds,method=m,query=i,main_hits=int(bh[i]),hits=int(h[i]),rescued=int(new[i].sum()),damaged=int(lost[i].sum()),source_out_rescued=int(outside[i].sum())))
  if m=='B32':assert not outside.any();continue
  trace=arr(root/f'k100/{m}_L200/trace.i32','<i4').reshape(n,160);cnt=collections.Counter()
  for i in range(n):
   missing=set(map(int,g[i,:K][~base[i]]));pool=set(map(int,trace[i,:32]));scan=set(map(int,trace[i,32:64]));short=set(map(int,trace[i,64:]));cnt['missing_members']+=len(missing);cnt['pool_covered']+=sum(int(ib[v]) in pool for v in missing);cnt['scan_covered']+=sum(int(ib[v]) in scan for v in missing);cnt['shortlist_covered']+=len(missing&short)
  covers.append(dict(dataset=ds,K=100,method=m,L=200,**dict(cnt),rescued_members=int(new.sum()),damaged_members=int(lost.sum())))
 norm=masks['REUSE-SQ',200];shuffle=masks['SHUFFLE-SQ',200];diff=norm.sum(1).astype(int)-shuffle.sum(1).astype(int)
 impact=dict(dataset=ds,K=100,L=200,normal_minus_shuffled_hits=int(diff.sum()),normal_minus_shuffled_recall_pp=100*int(diff.sum())/(n*K),normal_better_queries=int((diff>0).sum()),shuffle_better_queries=int((diff<0).sum()),equal_queries=int((diff==0).sum()),scope='fixed workload/software intervention on hub-table assignment; not changing dataset geometry or training/test GT overlap')
 csvwrite(out/'points.csv',points);csvwrite(out/'paired.csv',pairs);csvwrite(out/'coverage.csv',covers)
 with gzip.open(out/'query_metrics.csv.gz','wt') as f:w=csv.DictWriter(f,list(queries[0]));w.writeheader();w.writerows(queries)
 dump(out/'intervention.json',impact);dump(out/'summary.json',dict(status='PASS_E192_NATIVE_ANALYSIS',dataset=ds,points=len(points),batches=3*len(points),seconds=time.perf_counter()-t));print(json.dumps(impact),flush=True)
if __name__=='__main__':main()
