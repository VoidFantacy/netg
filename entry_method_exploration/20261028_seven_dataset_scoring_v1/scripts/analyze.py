import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
import csv,gzip,json,sys,time,collections,struct
from pathlib import Path
import numpy as np
from io_data import gt,read_array
R=Path(__file__).resolve().parents[1]
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def table(p,rows):
 if not rows:return
 with p.open('w') as f:w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
def hitmask(ids,g,K):
 z=np.empty((len(g),K),bool)
 for lo in range(0,len(g),128):z[lo:lo+128]=(ids[lo:lo+128,:,None]==g[lo:lo+128,None,:K]).any(1)
 return z
def ci(delta,K):
 vals,cnt=np.unique(delta,return_counts=True);draw=np.random.default_rng(20261028).multinomial(len(delta),cnt/len(delta),size=5000)@vals/len(delta)*100/K;return np.quantile(draw,[.025,.975]).tolist()
def postings(path):
 b=Path(path).read_bytes();head=struct.unpack_from('<8I',b,8);H,cap=head[1:3];labs=struct.unpack_from('<'+str(H)+'i',b,40);off=40+4*H;counts=b[off:off+H];off+=H;ids=struct.unpack_from('<'+str(H*cap)+'i',b,off);return {h:set(ids[j*cap:j*cap+counts[j]]) for j,h in enumerate(labs)}
def main():
 ds=sys.argv[1];mode=sys.argv[2] if len(sys.argv)>2 else 'formal';root=R/'storage'/('results' if mode=='formal' else mode)/ds;c=json.loads((root/'config.json').read_text());done=json.loads((root/'complete.json').read_text());t=time.perf_counter();out=R/'analysis'/ds;out.mkdir();g=gt(c['test_gt']);n=len(g);N=c['base']['n'];source=np.zeros(N,bool);source[read_array(Path(c['source_dir'])/'global_ids.i32','<i4')]=True;model=json.loads((Path(c['models'])/'model.json').read_text());ib=read_array(model['files']['id_block'],'<i4');tab=postings(c['table']);masks={};points=[];pairs=[];coverage=[];strata=[];comparisons=[];freq=[]
 with gzip.open(out/'query_metrics.csv.gz','wt') as f:
  fields=['dataset','K','method','L','query','main_hits','hits','rescued','damaged','rescued_source_out','missing_source_fraction'];writer=csv.DictWriter(f,fields);writer.writeheader()
  for rr in done['results']:
   K,L,m=rr['K'],rr['L'],rr['method'];p=Path(rr['result_dir']);ids=read_array(p/'raw/ids.i32','<i4').reshape(n,K);dist=read_array(p/'raw/distances.f32','<f4').reshape(n,K);assert np.all((ids>=0)&(ids<N)) and np.all(np.diff(np.sort(ids,axis=1),axis=1)>0) and np.isfinite(dist).all();mask=hitmask(ids,g,K);masks[K,m,L]=mask;h=mask.sum(1);qs=[v['qps'] for v in rr['rounds']];assert len(qs)==3 and all(v['threads']==1 for v in rr['rounds']);assert abs(np.median(qs)-rr['qps'])<1e-8
   point=dict(dataset=ds,K=K,method=m,L=L,n=n,recall_pct=float(h.mean()*100/K),hits=int(h.sum()),qps=rr['qps'],mean_us=1e6/rr['qps'],qps_min=min(qs),qps_max=max(qs),qps_round0=qs[0],qps_round1=qs[1],qps_round2=qs[2],zero_hit_queries=int((h==0).sum()),failed_lt10=int((h<10).sum()) if K==100 else None,complete_queries=int((h==K).sum()),scanned_codes_per_query=rr['scanned_codes_per_query'] if m not in ['GT10','B32'] else None,exact_scores_per_query=rr['extra_exact_scores_per_query'] if m not in ['GT10','B32'] else None,PQ_scores_per_query=rr['PQ_scores_per_query'],SQ_scores_per_query=rr['SQ_scores_per_query'],block_centres_per_query=rr['block_centres_per_query'],scan_max=None,exact_max=None)
   if m not in ['GT10','B32']:
    access=read_array(p/'access.u64','<u8').reshape(n,5);assert access[:,0].max()<=2048 and access[:,2].max()<=96;point.update(scan_max=int(access[:,0].max()),exact_max=int(access[:,2].max()))
   points.append(point)
  for x in points:
   K,m,L=x['K'],x['method'],x['L'];mask=masks[K,m,L]
   if (K,'GT10',L) not in masks:continue
   base=masks[K,'GT10',L];bh=base.sum(1);h=mask.sum(1);rescued=(mask&~base).sum(1);damaged=(base&~mask).sum(1);source_mask=source[g[:,:K]];outside=(mask&~base&~source_mask).sum(1);missing=K-bh;available=(~base&source_mask).sum(1);fraction=np.divide(available,missing,out=np.zeros(n,float),where=missing>0)
   if m!='GT10':
    mainpoint=next(v for v in points if v['K']==K and v['method']=='GT10' and v['L']==L);lo,hi=ci(h.astype(int)-bh.astype(int),K);pair=dict(dataset=ds,K=K,method=m,L=L,recall_delta_pp=x['recall_pct']-mainpoint['recall_pct'],recall_delta_ci_lo_pp=lo,recall_delta_ci_hi_pp=hi,qps_delta_pct=100*(x['qps']/mainpoint['qps']-1),extra_mean_us=x['mean_us']-mainpoint['mean_us'],extra_time_pct=100*(x['mean_us']/mainpoint['mean_us']-1),members_missing=int(missing.sum()),missing_in_old_source=int(available.sum()),members_rescued=int(rescued.sum()),members_damaged=int(damaged.sum()),rescued_source_out=int(outside.sum()),rescued_source_in=int(rescued.sum()-outside.sum()),improved_queries=int((h>bh).sum()),worsened_queries=int((h<bh).sum()),complete_recovered_queries=int(((h==K)&(bh<K)).sum()),zero_hit_to_hit=int(((bh==0)&(h>0)).sum()),original_lt10=int((bh<10).sum()) if K==100 else None,final_lt10=int((h<10).sum()) if K==100 else None,lt10_improved=int(((bh<10)&(h>bh)).sum()) if K==100 else None,lt10_escaped=int(((bh<10)&(h>=10)).sum()) if K==100 else None,new_lt10=int(((bh>=10)&(h<10)).sum()) if K==100 else None)
    if m=='B32':
     mainids=read_array(root/f'k{K}/GT10_L{L}/raw/ids.i32','<i4').reshape(n,K);routes=read_array(root/f'k{K}/GT10_L{L}/raw/entry_ids.i32','<i4').reshape(n,3);x['exact_scores_per_query']=sum(len(set.union(*(tab[int(z)] for z in routes[i]))-set(map(int,mainids[i]))) for i in range(n))/n
    pairs.append(pair)
    controls=[v for v in points if v['K']==K and v['method']=='GT10'];target=[v for v in controls if v['recall_pct']>=x['recall_pct']];target=max(target,key=lambda v:v['qps']) if target else None;budget=[v for v in controls if v['qps']>=x['qps']];budget=max(budget,key=lambda v:v['recall_pct']) if budget else None;dom=[v for v in controls if v['recall_pct']>=x['recall_pct'] and v['qps']>=x['qps']]
    comparisons.append(dict(dataset=ds,K=K,method=m,L=L,recall_pct=x['recall_pct'],qps=x['qps'],target_GT_L=target['L'] if target else None,target_GT_recall_pct=target['recall_pct'] if target else None,target_GT_qps=target['qps'] if target else None,target_speed_delta_pct=100*(x['qps']/target['qps']-1) if target else None,target_speed_three_rounds_positive=all(x[f'qps_round{i}']>target[f'qps_round{i}'] for i in range(3)) if target else None,budget_GT_L=budget['L'] if budget else None,budget_recall_delta_pp=x['recall_pct']-budget['recall_pct'] if budget else None,dominated_by_GT_L=','.join(str(v['L']) for v in dom),dominated_by_GT_nonoverlap=','.join(str(v['L']) for v in dom if v['qps_min']>x['qps_max'])))
    for label,cond in [('no_missing',missing==0),('no_old_source',(missing>0)&(available==0)),('source_0_to_25pct',(missing>0)&(fraction>0)&(fraction<=.25)),('source_25_to_75pct',(fraction>.25)&(fraction<=.75)),('source_over_75pct',(missing>0)&(fraction>.75))]:
     count=int(cond.sum())
     if not count:continue
     strata.append(dict(dataset=ds,K=K,method=m,L=L,stratum=label,queries=count,main_recall_pct=float(bh[cond].mean()*100/K),recall_delta_pp=float((h[cond].astype(int)-bh[cond].astype(int)).mean()*100/K),members_missing=int(missing[cond].sum()),members_rescued=int(rescued[cond].sum()),members_damaged=int(damaged[cond].sum()),rescued_source_out=int(outside[cond].sum())))
    if m in ['REUSE-PQ','REUSE-SQ','MAIN-SQ']:
     trace=read_array(root/f'k{K}/{m}_L{L}/trace.i32','<i4').reshape(n,160);final_ids=read_array(root/f'k{K}/{m}_L{L}/raw/ids.i32','<i4').reshape(n,K);cnt=collections.Counter()
     if m=='REUSE-SQ':assert np.array_equal(trace[:,:64],read_array(root/f'k{K}/REUSE-PQ_L{L}/trace.i32','<i4').reshape(n,160)[:,:64])
     for i in range(n):
      absent=set(map(int,g[i,:K][~base[i]]));pool=set(map(int,trace[i,:32]));scans=set(map(int,trace[i,32:64]));short=set(map(int,trace[i,64:]));returned=set(map(int,final_ids[i]));cnt['members_missing']+=len(absent);cnt['pool_covered']+=sum(int(ib[z]) in pool for z in absent);cnt['scanned_covered']+=sum(int(ib[z]) in scans for z in absent);cnt['shortlist_covered']+=len(absent&short);cnt['rescued']+=len(absent&returned)
     coverage.append(dict(dataset=ds,K=K,method=m,L=L,**dict(cnt)))
   if m!='GT10' or L in c['completion_L'][str(K)]:
    for i in range(n):writer.writerow(dict(dataset=ds,K=K,method=m,L=L,query=i,main_hits=int(bh[i]),hits=int(h[i]),rescued=int(rescued[i]),damaged=int(damaged[i]),rescued_source_out=int(outside[i]),missing_source_fraction=float(fraction[i]) if missing[i] else ''))
 table(out/'points.csv',points);table(out/'paired.csv',pairs);table(out/'coverage.csv',coverage);table(out/'source_strata.csv',strata);table(out/'discrete_comparisons.csv',comparisons);dump(out/'summary.json',dict(status='PASS_E191_ANALYSIS',dataset=ds,points=len(points),batches=3*len(points),paired_points=len(pairs),coverage_points=len(coverage),internal_wall_seconds=sum(v['wall_seconds'] for x in done['results'] for v in x['rounds']),suite_seconds=done['outer_seconds'],seconds=time.perf_counter()-t,quality_scope='historically exposed test, no new blind confirmation',bootstrap='5000 paired descriptive percentile95, no multiplicity adjustment'))
 print(json.dumps(dict(dataset=ds,points=len(points),seconds=time.perf_counter()-t)),flush=True)
if __name__=='__main__':main()
