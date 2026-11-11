"""Audit all COCO K100/L packets using original GT and stdlib set intersections."""
from pathlib import Path
import array,csv,hashlib,json,sys,time

W=Path(__file__).resolve().parents[3];R=Path(__file__).resolve().parents[1]
E=W/'entry_method_exploration/20261017_gt10_residual_comprehensive_v1'
T=W/'reports/20261105_low_recall_stage_attribution_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):return list(csv.DictReader(p.open()))
def ints(p,code):
    a=array.array(code)
    with p.open('rb') as f:a.fromfile(f,p.stat().st_size//a.itemsize)
    if sys.byteorder!='little':a.byteswap()
    return a
def write(name,records):
    with (R/'analysis'/name).open('w',newline='') as f:
        w=csv.DictWriter(f,list(records[0]));w.writeheader();w.writerows(records)

started=time.perf_counter()
identity=json.loads((R/'source_before/identity.json').read_text())
cfg=json.loads((E/'configs/coco.analysis.json').read_text());d=cfg['eval_gt']
assert d['format']=='raw_i64' and d['n']==10000 and d['width']==100
g=ints(Path(d['path']),'q');GT=[set(g[i*100:(i+1)*100]) for i in range(d['n'])]
assert all(len(s)==100 for s in GT)
reference={int(x['L']):x for x in rows(T/'analysis/stage_attribution_four_multimodal.csv') if x['dataset']=='coco'}
reference_queries={(int(x['L']),int(x['query_row'])):x for x in rows(T/'analysis/low_query_transitions.csv') if x['dataset']=='coco'}
metrics=[];queries=[];all_hits={}
for L in [100,128,200,400,800,1000,1200]:
    hits={}
    for method,source in [('NSG','NSG'),('GT10','GT10-hard'),('B32','hard-JOINT32')]:
        p=E/f'results/coco/k100/{source}_L{L}/raw/ids.i32'
        a=ints(p,'i');assert len(a)==d['n']*100
        hh=[]
        for i,gt in enumerate(GT):
            ids=set(a[i*100:(i+1)*100]);assert len(ids)==100
            hh.append(len(ids & gt))
        hits[method]=hh;all_hits[method,L]=hh
    counts={m:sum(h<10 for h in hh) for m,hh in hits.items()}
    gt_new=sum(a>=10 and b<10 for a,b in zip(hits['NSG'],hits['GT10']))
    b_new=sum(a>=10 and b<10 for a,b in zip(hits['GT10'],hits['B32']))
    b_rescued=sum(a<10 and b>=10 for a,b in zip(hits['GT10'],hits['B32']))
    record=dict(L=L,n=10000,NSG_low=counts['NSG'],GT10_low=counts['GT10'],B32_low=counts['B32'],GT10_new_low=gt_new,B32_new_low=b_new,B32_rescued=b_rescued)
    for k,v in record.items():
        if k in reference[L]:assert int(reference[L][k])==v,(L,k)
    metrics.append(record)
    for i,hh in enumerate(zip(hits['NSG'],hits['GT10'],hits['B32'])):
        if min(hh)<10:
            r=dict(L=L,query_row_zero_based=i,NSG_hits=hh[0],GT10_hits=hh[1],B32_hits=hh[2])
            old=reference_queries[L,i]
            for k in ['NSG_hits','GT10_hits','B32_hits']:assert int(old[k])==r[k],(L,i,k)
            queries.append(r)

# This second input route compares every recomputed hit count to the earlier aligned arrays.
# NumPy is used only to read that archive, not to recompute the set intersections above.
import numpy as np
z=np.load(W/'reports/20261024_failure_rescue_residual_lt10_v2/per_query_hits.npz')
for (m,L),hh in all_hits.items():assert hh==z[f'coco__{m}__L{L}'].tolist(),(m,L)
assert len(queries)==len(reference_queries)==6
assert all(r['B32_new_low']==0 and r['B32_rescued']==0 for r in metrics)
assert all_hits['NSG',200][4815]==97 and all_hits['GT10',200][4815]==all_hits['B32',200][4815]==3
write('COCO_low_counts_all_L.csv',metrics);write('COCO_low_query_hits.csv',queries)
for name,h in identity['sources'].items():assert sha(W/name)==h,name
receipt=dict(status='PASS_COCO_RAW_GT_AND_21_TIMED_PACKETS',points=21,query_point_evaluations=210000,all_L=7,strict_low_definition='Recall@100 < 10%, hits 0-9',counts=metrics,
             affected_query_rows_zero_based=sorted({x['query_row_zero_based'] for x in queries}),L200_query_4815_hits=[97,3,3],
             GT10_new_low_is_same_query_across_L100_to_400=True,B32_new_low_all_L=0,B32_low_rescues_all_L=0,
             old_aligned_array_equality_all_queries=True,reference_tables_match=True,source_hashes_unchanged=len(identity['sources']),
             new_ANN=0,new_GT=0,new_timing=0,independence='same operator; raw set-intersection implementation',seconds=time.perf_counter()-started)
(R/'reviews/coco_raw_audit.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print('COCO raw audit passed: 21 packets / 210,000 query-point checks; L200 0 -> 1 -> 1; query 4815: 97 -> 3 -> 3.')
