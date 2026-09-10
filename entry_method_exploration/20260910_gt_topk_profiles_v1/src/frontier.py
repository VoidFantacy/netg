"""Descriptive frontier accounting from completed measured points; no new evaluation."""
import csv
import numpy as np
from common import DATASETS, RUN, dump, read


def dominates(a,b):
    return (a['recall_percent']>=b['recall_percent'] and a['qps']>=b['qps'] and
            (a['recall_percent']>b['recall_percent'] or a['qps']>b['qps']))


def frontier(rows):
    return sorted([x for x in rows if not any(dominates(y,x) for y in rows)],key=lambda x:x['recall_percent'])


summary=read(RUN/'results/summary.json')
assert summary['completed_validation']
rows=summary['metrics'];records=[];interpolations=[]
for ds in DATASETS:
    base=[x for x in rows if x['dataset']==ds and x['stage']=='validation' and x['family']=='gt1_hard']
    for family in ['gt10_hard','gt1_soft','gt10_soft']:
        candidates=[x for x in rows if x['dataset']==ds and x['stage']=='validation' and x['family']==family]
        for c in candidates:
            records.append({'dataset':ds,'family':family,'L':c['L'],'recall_percent':c['recall_percent'],'qps':c['qps'],
                'dominated_by_measured_Fast20K':any(dominates(b,c) for b in base),
                'Fast20K_L_points_strictly_dominated':','.join(str(b['L']) for b in base if dominates(c,b)),
                'on_union_observed_frontier':not any(dominates(x,c) for x in base+candidates),
                'boundary':'single wall; measured-point dominance, not statistical confirmation'})
        points=frontier(candidates)
        rr=np.array([p['recall_percent'] for p in points]);qq=np.array([p['qps'] for p in points])
        for b in base:
            if b['L'] not in [128,256,400]:continue
            target=b['recall_percent'];covered=rr.min()<=target<=rr.max()
            lin=float(np.interp(target,rr,qq)) if covered else None
            log=float(np.exp(np.interp(target,rr,np.log(qq)))) if covered else None
            interpolations.append({'dataset':ds,'family':family,'reference_Fast20K_L':b['L'],
                'matched_recall_percent':target,'Fast20K_measured_qps':b['qps'],
                'candidate_linear_interpolated_qps':lin,'candidate_log_interpolated_qps':log,
                'linear_qps_change_percent':100*(lin/b['qps']-1) if covered else None,
                'log_qps_change_percent':100*(log/b['qps']-1) if covered else None,
                'not_measured_at_equal_recall':True,'selection_use':False,
                'limitation':'post-run descriptive interpolation across sparse L points; neither estimate proves equal-recall speedup'})
for path,data in [('frontier_points.csv',records),('frontier_interpolation.csv',interpolations)]:
    with (RUN/'results'/path).open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
dump(RUN/'results/frontier.json',{'status':'DESCRIPTIVE_ONLY_NO_ADDITIONAL_SEARCHES','measured_points':records,
     'interpolation':interpolations,'primary_families':summary['primary_families'],
     'interpretation':'Observations from the same machine and complete routed plain wall; single timing and reused validation prevent formal performance GO.'})
for ds,family in summary['primary_families'].items():
    part=[r for r in records if r['dataset']==ds and r['family']==family]
    print(ds,family,'observed_union_frontier_points',sum(x['on_union_observed_frontier'] for x in part),
          'dominated_by_Fast20K',sum(x['dominated_by_measured_Fast20K'] for x in part),flush=True)
