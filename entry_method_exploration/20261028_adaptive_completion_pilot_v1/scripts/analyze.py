#!/usr/bin/env python3
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
import csv,gzip,hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];A=R/'analysis';OLD=R.parent/'20261017_gt10_residual_comprehensive_v1'
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def table(path,rows):
    with path.open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def gt(d):
    n=d['n'];total=d.get('total_n',n);k=d.get('width',d.get('k',100));start=d.get('row_start',0)
    assert d['format'] in ['raw_i32','raw_i64']
    return np.memmap(d['path'],dtype='<i8' if d['format']=='raw_i64' else '<i4',mode='r',shape=(total,k))[start:start+n,:100]
def hits(ids,g):
    out=np.empty_like(g,dtype=bool)
    for lo in range(0,len(g),128):out[lo:lo+128]=(ids[lo:lo+128,:,None]==g[lo:lo+128,None,:]).any(axis=1)
    return out
def ci(delta):
    values,counts=np.unique(delta,return_counts=True);rng=np.random.default_rng(20261028)
    samples=rng.multinomial(len(delta),counts/len(delta),size=5000)@values/len(delta)
    return [float(v) for v in np.quantile(samples,[.025,.975])]
def main():
    t=time.perf_counter();A.mkdir(exist_ok=False);points=[];paired=[];comparisons=[];summaries=[]
    fields=['dataset','method','L','query','main_hits','hits','rescued','damaged','rescued_source_out','original_lt10','final_lt10']
    with gzip.open(A/'query_metrics.csv.gz','wt') as f:
        writer=csv.DictWriter(f,fields);writer.writeheader()
        for ds in ['coco','deep10m_l2_v1']:
            c=json.loads((R/f'configs/{ds}.json').read_text());completed=json.loads((R/f'results/{ds}/complete.json').read_text());assert completed['status']=='PASS_E187_FORMAL' and completed['points']==23 and completed['batches']==69
            control_receipt=json.loads((R/f'controls_v1/results/{ds}/complete.json').read_text());assert control_receipt['points']==3 and control_receipt['batches']==9
            original_outer=completed['outer_seconds'];completed['results']+=control_receipt['results']
            truth=gt(c['test_gt']);n=len(truth);N=c['base']['n'];source=np.zeros(N,bool)
            source[np.fromfile(OLD/f"models/{ds}/compiled/{c['router']['name']}/source/global_ids.i32",'<i4')]=True
            in_source=source[truth];masks={};datasetpoints=[]
            for r in completed['results']:
                p=Path(r['result_dir']);ids=np.fromfile(p/'raw/ids.i32','<i4').reshape(n,100)
                assert np.all((ids>=0)&(ids<N));s=np.sort(ids,axis=1);assert np.all(np.diff(s,axis=1)>0)
                mask=hits(ids,truth);counts=mask.sum(axis=1);masks[r['method'],r['L']]=mask
                qps=np.array([x['qps'] for x in r['rounds']]);assert len(qps)==3 and all(x['threads']==1 for x in r['rounds'])
                assert abs(np.median(qps)-r['qps'])<1e-8
                point=dict(dataset=ds,method=r['method'],L=r['L'],n=n,recall_pct=float(counts.mean()),hits=int(counts.sum()),failed_lt10=int((counts<10).sum()),failure_pct=float((counts<10).mean()*100),
                    qps=r['qps'],qps_min=float(qps.min()),qps_max=float(qps.max()),qps_round0=float(qps[0]),qps_round1=float(qps[1]),qps_round2=float(qps[2]),
                    scanned_codes_per_query=r['scanned_codes_per_query'] if r['method'].startswith('REG-') else None,
                    extra_exact_scores_per_query=r['extra_exact_scores_per_query'] if r['method'].startswith('REG-') else None)
                points.append(point);datasetpoints.append(point)
            for p in datasetpoints:
                method,L=p['method'],p['L'];mask=masks[method,L];base=masks['GT10',L];bh=base.sum(axis=1);h=mask.sum(axis=1)
                rescued=(mask&~base).sum(axis=1);damaged=(base&~mask).sum(axis=1);outside=(mask&~base&~in_source).sum(axis=1)
                if method!='GT10':
                    b=next(x for x in datasetpoints if x['method']=='GT10' and x['L']==L);interval=ci(h.astype(int)-bh.astype(int))
                    pair=dict(dataset=ds,method=method,L=L,recall_delta_pp=p['recall_pct']-b['recall_pct'],recall_delta_ci_lo_pp=interval[0],recall_delta_ci_hi_pp=interval[1],
                        qps_delta_pct=100*(p['qps']/b['qps']-1),members_missing=int((~base).sum()),members_rescued=int(rescued.sum()),members_damaged=int(damaged.sum()),
                        member_repair_pct=float(rescued.sum()/(~base).sum()*100),rescued_source_out=int(outside.sum()),rescued_source_in=int(rescued.sum()-outside.sum()),
                        improved_queries=int((h>bh).sum()),worsened_queries=int((h<bh).sum()),full_recovered_queries=int(((h==100)&(bh<100)).sum()),
                        original_lt10=int((bh<10).sum()),final_lt10=int((h<10).sum()),lt10_improved=int(((bh<10)&(h>bh)).sum()),
                        lt10_escaped=int(((bh<10)&(h>=10)).sum()),new_lt10=int(((bh>=10)&(h<10)).sum()),
                        rescued_from_original_lt10=int(rescued[bh<10].sum()),rescued_from_original_ge10=int(rescued[bh>=10].sum()))
                    paired.append(pair)
                    controls=[x for x in datasetpoints if x['method']=='GT10']
                    target=[x for x in controls if x['recall_pct']>=p['recall_pct']];target=min(target,key=lambda x:-x['qps']) if target else None
                    budget=[x for x in controls if x['qps']>=p['qps']];budget=max(budget,key=lambda x:x['recall_pct']) if budget else None
                    dominates=[x for x in controls if x['recall_pct']>=p['recall_pct'] and x['qps']>=p['qps']]
                    comp=dict(dataset=ds,method=method,L=L,recall_pct=p['recall_pct'],qps=p['qps'],
                        target_GT_L=target['L'] if target else None,target_GT_recall_pct=target['recall_pct'] if target else None,target_GT_qps=target['qps'] if target else None,
                        target_speed_delta_pct=100*(p['qps']/target['qps']-1) if target else None,
                        target_speed_three_rounds_positive=all(p[f'qps_round{i}']>target[f'qps_round{i}'] for i in range(3)) if target else None,
                        budget_GT_L=budget['L'] if budget else None,budget_GT_recall_pct=budget['recall_pct'] if budget else None,budget_GT_qps=budget['qps'] if budget else None,
                        budget_recall_delta_pp=p['recall_pct']-budget['recall_pct'] if budget else None,
                        budget_GT_three_rounds_within=all(budget[f'qps_round{i}']>=p[f'qps_round{i}'] for i in range(3)) if budget else None,
                        dominated_by_GT_L=','.join(str(x['L']) for x in dominates),
                        dominated_by_GT_nonoverlapping_QPS_ranges=','.join(str(x['L']) for x in dominates if x['qps_min']>p['qps_max']))
                    comparisons.append(comp)
                for i in range(n):writer.writerow(dict(dataset=ds,method=method,L=L,query=i,main_hits=int(bh[i]),hits=int(h[i]),rescued=int(rescued[i]),damaged=int(damaged[i]),rescued_source_out=int(outside[i]),original_lt10=int(bh[i]<10),final_lt10=int(h[i]<10)))
            summaries.append(dict(dataset=ds,formal_outer_seconds=original_outer+control_receipt['outer_seconds'],original_formal_outer_seconds=original_outer,controls_outer_seconds=control_receipt['outer_seconds'],formal_internal_seconds=sum(x['wall_seconds'] for p in completed['results'] for x in p['rounds']),
                backend=json.loads((Path(c['backend'])/'backend.json').read_text()),training=json.loads((Path(c['backend'])/'training.json').read_text()),
                environment=json.loads((R/f'results/{ds}/environment.json').read_text())))
    table(A/'points.csv',points);table(A/'paired.csv',paired);table(A/'discrete_comparisons.csv',comparisons)
    dump(A/'summary.json',dict(status='PASS_E187_ANALYSIS',point_count=len(points),original_matrix_points=46,supplemental_GT_points=6,formal_batches=156,summaries=summaries,seconds=time.perf_counter()-t,
        failure='per query Recall100<10%, hits 0..9',bootstrap='5000 paired query multinomial draws, percentile95%, descriptive unadjusted intervals',
        B32_counters='native stats not instrumented for B32; zeros in original result are placeholders; online cost is included in wall',
        quality_scope='historically exposed original10K test per dataset; no blind confirmation'))
    print('PASS analyze',time.perf_counter()-t)
if __name__=='__main__':main()
