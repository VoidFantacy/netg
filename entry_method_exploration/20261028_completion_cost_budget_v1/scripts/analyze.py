#!/usr/bin/env python3
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
import csv,gzip,json,sys,time,hashlib,datetime
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];OLD=R.parent/'20261017_gt10_residual_comprehensive_v1'
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def table(p,rows):
 with p.open('w') as f:
  w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
def gt(d):
 n=d['n'];start=d.get('row_start',0);a=np.memmap(d['path'],dtype='<i8' if d['format']=='raw_i64' else '<i4',mode='r').reshape(-1,100);assert len(a)>=start+n;return a[start:start+n]
def hitmask(ids,g):
 out=np.empty(g.shape,bool)
 for lo in range(0,len(g),128):out[lo:lo+128]=(ids[lo:lo+128,:,None]==g[lo:lo+128,None,:]).any(1)
 return out
def ci(delta):
 v,n=np.unique(delta,return_counts=True);s=np.random.default_rng(20261028).multinomial(len(delta),n/len(delta),size=5000)@v/len(delta);return np.quantile(s,[.025,.975]).tolist()
def main():
 mode=sys.argv[1];formal=mode=='formal';root=R/('results' if formal else 'calibration');out=R/('analysis' if formal else 'calibration_analysis');out.mkdir(exist_ok=True);assert not (out/'points.csv').exists();t=time.perf_counter();points=[];pairs=[];comp=[];cost=[];choices=[]
 fields=['dataset','method','L','query','main_hits','hits','rescued','damaged','rescued_source_out']
 with gzip.open(out/'query_metrics.csv.gz','wt') as f:
  writer=csv.DictWriter(f,fields);writer.writeheader()
  for ds in ['coco','deep10m_l2_v1']:
   cfg=json.loads((root/ds/'config.json').read_text());done=json.loads((root/ds/'complete.json').read_text());assert done['points']==50 and done['batches']==150;g=gt(cfg['test_gt']);n=len(g);N=cfg['base']['n'];src=np.zeros(N,bool);src[np.fromfile(OLD/f"models/{ds}/compiled/{cfg['router']['name']}/source/global_ids.i32",'<i4')]=1;source=src[g];masks={};dp=[]
   for rr in done['results']:
    p=Path(rr['result_dir']);ids=np.fromfile(p/'raw/ids.i32','<i4').reshape(n,100);assert np.all((ids>=0)&(ids<N)) and np.all(np.diff(np.sort(ids,axis=1),axis=1)>0);mask=hitmask(ids,g);h=mask.sum(1);masks[rr['method'],rr['L']]=mask;qp=[x['qps'] for x in rr['rounds']];assert len(qp)==3 and all(x['threads']==1 for x in rr['rounds']);assert abs(np.median(qp)-rr['qps'])<1e-8
    x=dict(dataset=ds,method=rr['method'],L=rr['L'],n=n,recall_pct=float(h.mean()),hits=int(h.sum()),failed_lt10=int((h<10).sum()),failure_pct=float(100*(h<10).mean()),qps=rr['qps'],mean_us=1e6/rr['qps'],qps_min=min(qp),qps_max=max(qp),qps_round0=qp[0],qps_round1=qp[1],qps_round2=qp[2],scanned_codes_per_query=rr['scanned_codes_per_query'] if rr['method'] not in ['GT10','B32'] else None,extra_exact_scores_per_query=rr['extra_exact_scores_per_query'] if rr['method'] not in ['GT10','B32'] else None,block_centres_per_query=rr['block_centres_per_query'],scan_p95=None,scan_max=None,exact_max=None)
    if (p/'access.u64').exists():
     access=np.fromfile(p/'access.u64','<u8').reshape(n,3);x.update(scan_p95=float(np.percentile(access[:,0],95)),scan_max=int(access[:,0].max()),exact_max=int(access[:,2].max()));assert abs(access[:,0].mean()-rr['scanned_codes_per_query'])<1e-8
     if x['method'].startswith('BLOCK-'):assert x['scan_max']<=int(x['method'].split('R')[-1] if x['method'].startswith('BLOCK-R') else 2048) and x['exact_max']<=96
    points.append(x);dp.append(x)
   controls=[x for x in dp if x['method']=='GT10']
   for x in dp:
    m,L=x['method'],x['L'];mask=masks[m,L];base=masks['GT10',L];bh=base.sum(1);h=mask.sum(1);rescued=(mask&~base).sum(1);damaged=(base&~mask).sum(1);outside=(mask&~base&~source).sum(1)
    if m!='GT10':
     b=next(v for v in controls if v['L']==L);lo,hi=ci(h.astype(int)-bh.astype(int));pairs.append(dict(dataset=ds,method=m,L=L,recall_delta_pp=x['recall_pct']-b['recall_pct'],recall_delta_ci_lo_pp=lo,recall_delta_ci_hi_pp=hi,qps_delta_pct=100*(x['qps']/b['qps']-1),extra_mean_us=x['mean_us']-b['mean_us'],extra_time_pct=100*(x['mean_us']/b['mean_us']-1),members_missing=int((~base).sum()),members_rescued=int(rescued.sum()),members_damaged=int(damaged.sum()),rescued_source_out=int(outside.sum()),rescued_source_in=int(rescued.sum()-outside.sum()),improved_queries=int((h>bh).sum()),worsened_queries=int((h<bh).sum()),full_recovered_queries=int(((h==100)&(bh<100)).sum()),original_lt10=int((bh<10).sum()),final_lt10=int((h<10).sum()),lt10_improved=int(((bh<10)&(h>bh)).sum()),lt10_escaped=int(((bh<10)&(h>=10)).sum()),new_lt10=int(((bh>=10)&(h<10)).sum()),rescued_from_original_lt10=int(rescued[bh<10].sum())))
     target=[v for v in controls if v['recall_pct']>=x['recall_pct']];target=max(target,key=lambda v:v['qps']) if target else None;budget=[v for v in controls if v['qps']>=x['qps']];budget=max(budget,key=lambda v:v['recall_pct']) if budget else None;dom=[v for v in controls if v['recall_pct']>=x['recall_pct'] and v['qps']>=x['qps']]
     comp.append(dict(dataset=ds,method=m,L=L,recall_pct=x['recall_pct'],qps=x['qps'],target_GT_L=target['L'] if target else None,target_GT_recall_pct=target['recall_pct'] if target else None,target_GT_qps=target['qps'] if target else None,target_speed_delta_pct=100*(x['qps']/target['qps']-1) if target else None,target_speed_three_rounds_positive=all(x[f'qps_round{i}']>target[f'qps_round{i}'] for i in range(3)) if target else None,budget_GT_L=budget['L'] if budget else None,budget_GT_recall_pct=budget['recall_pct'] if budget else None,budget_GT_qps=budget['qps'] if budget else None,budget_recall_delta_pp=x['recall_pct']-budget['recall_pct'] if budget else None,dominated_by_GT_L=','.join(str(v['L']) for v in dom),dominated_by_GT_nonoverlapping_QPS_ranges=','.join(str(v['L']) for v in dom if v['qps_min']>x['qps_max'])))
    for i in range(n):writer.writerow(dict(dataset=ds,method=m,L=L,query=i,main_hits=int(bh[i]),hits=int(h[i]),rescued=int(rescued[i]),damaged=int(damaged[i]),rescued_source_out=int(outside[i])))
   if not formal:
    for L in [100,200,400]:
     base=next(x for x in controls if x['L']==L);limit=base['mean_us']*1.10;eligible=[x for x in dp if (x['method']=='GT10' or x['L']==L) and x['mean_us']<=limit and x['recall_pct']>=base['recall_pct']+.05];chosen=max(eligible,key=lambda x:(x['recall_pct'],x['qps'])) if eligible else base
     choices.append(dict(dataset=ds,main_L=L,budget_us=limit,chosen_method=chosen['method'],chosen_L=chosen['L'],calibration_recall_pct=chosen['recall_pct'],calibration_qps=chosen['qps'],reason='highest recall within 1.10x main cost and +0.05pp, otherwise GT10'))
   cost.append(dict(dataset=ds,internal_wall_seconds=sum(v['wall_seconds'] for x in done['results'] for v in x['rounds']),suite_wall_seconds=done['outer_seconds'],environment=json.loads((root/ds/'environment.json').read_text())))
 table(out/'points.csv',points);table(out/'paired.csv',pairs);table(out/'discrete_comparisons.csv',comp)
 if not formal:
  table(out/'selected_configurations.csv',choices);dump(R/'selection_freeze.json',dict(status='CALIBRATION_CHOICES_FROZEN_BEFORE_FORMAL',timestamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),choices=choices,points_sha256=hashlib.sha256((out/'points.csv').read_bytes()).hexdigest(),formal_results_read=False,models_changed=False))
 else:
  selected=json.loads((R/'corrected_selection_freeze.json').read_text())['choices'];validation=[]
  for s in selected:
   chosen=next(x for x in points if x['dataset']==s['dataset'] and x['method']==s['chosen_method'] and x['L']==s['chosen_L']);base=next(x for x in points if x['dataset']==s['dataset'] and x['method']=='GT10' and x['L']==s['main_L']);validation.append(dict(**s,test_recall_pct=chosen['recall_pct'],test_qps=chosen['qps'],test_recall_delta_pp=chosen['recall_pct']-base['recall_pct'],test_time_ratio=chosen['mean_us']/base['mean_us'],test_within_budget=chosen['mean_us']<=1.10*base['mean_us']))
  table(out/'selected_validation.csv',validation)
 dump(out/'summary.json',dict(status='PASS_E188_ANALYSIS',role=mode,points=len(points),paired_points=len(pairs),batches=300,costs=cost,seconds=time.perf_counter()-t,quality_scope='historically exposed queries; not blind',bootstrap='5000 paired draws, descriptive percentile95, no multiplicity adjustment',B32_counts='unmeasured in native stats; reconstructed separately'))
 print(json.dumps(dict(role=mode,points=len(points),pairs=len(pairs),seconds=time.perf_counter()-t,choices=choices)),flush=True)
if __name__=='__main__':main()
