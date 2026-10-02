"""Read-only decomposition: which fit queries had direct assignment changes?"""
from shared import *
import csv
threads();assert read(O/'reviews/verification.json')['status']=='PASS';rows=[]
for ds in DS:
    baseline=dict(np.load(O/'results'/ds/'baseline/raw.npz'));m=np.load(O/'inputs'/ds/'missing_supervision.npz')['counts']
    oldmask=baseline['hitmask'][:20000]
    for name in LABELS[1:]:
        out=dict(np.load(O/'results'/ds/name/'raw.npz'));newmask=out['hitmask'][:20000]
        dh=out['hits'][:20000].astype(int)-baseline['hits'][:20000].astype(int)
        recovered=np.array([int(x&(~y&1023)).bit_count() for x,y in zip(newmask,oldmask)])
        lost=np.array([int(y&(~x&1023)).bit_count() for x,y in zip(newmask,oldmask)])
        assert np.array_equal(recovered-lost,dh)
        for cohort,group in [('full_hit_m0',m==0),('partly_missing_m1to9',(m>0)&(m<10)),('zero_hit_m10',m==10)]:
            a=out['hits'][:20000][group];b=baseline['hits'][:20000][group];d=dh[group]
            rows.append(dict(dataset=ds,model=name,cohort=cohort,queries=int(group.sum()),own_assignment_changed_by_formula=cohort=='partly_missing_m1to9',
                gain_hits=int(np.maximum(d,0).sum()),loss_hits=int(np.maximum(-d,0).sum()),net_hits=int(d.sum()),
                recovered_previously_missing_members=int(recovered[group].sum()),lost_previously_found_members=int(lost[group].sum()),
                changed_entries=int((out['entries'][:20000][group]!=baseline['entries'][:20000][group]).any(1).sum()),
                newly_failed=int(((b>0)&(a==0)).sum()),rescued=int(((b==0)&(a>0)).sum())))
with (O/'results/fit_cohorts.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
dump(O/'reviews/cohort_verification.json',dict(status='PASS',rows=12,query_member_balance_rows=80000,new_queries=0,new_training=0,
     interpretation='m=0 and m=10 preserve that query own assignment mathematically; shared profiles and HNSW may still change their routes. This grouping is descriptive, not isolated causal intervention.'))
print(json.dumps(rows,indent=2),flush=True)
