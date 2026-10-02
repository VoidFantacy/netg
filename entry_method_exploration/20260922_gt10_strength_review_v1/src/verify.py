"""Separate arithmetic implementation; historical files are read only."""
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
import csv, hashlib, json, time
from pathlib import Path
import numpy as np

R=Path(__file__).resolve().parents[1]; E=R.parent
start=time.perf_counter();os.sched_setaffinity(0,{15})
def rd(p):return json.loads(p.read_text())
def assertclose(a,b):assert abs(a-b)<1e-10,(a,b)
hashes={}
def ary(p,t):
    hashes[str(p)]={'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    return np.fromfile(p,t)

full={(r['dataset'],r['K']):r for r in rd(R/'results/full_h_opportunity.json')}
coverage={(r['dataset'],r['K']):r for r in rd(R/'results/same_cohort_candidate_coverage.json')}
src=E/'20260921_comparison_direction_pilot_v1';cfg=rd(src/'config.locked.json')
pop=np.array([i.bit_count() for i in range(256)],dtype=np.uint8)
checked_masks=0
for ds,conf in cfg['datasets'].items():
    gt=ary(src/'inputs'/ds/'fit/gt.i64','<i8').reshape(-1,100)
    hubs=list(map(int,ary(Path(conf['anchor']['ids']),'<i4')))
    totals={k:dict(default=0,oracle=0,small=0,positive=0,negative=0,n=0) for k in (1,100)}
    d=src/'results'/ds/'labels'; blocks=rd(d/'complete.json')['blocks']
    for b in sorted(blocks,key=lambda x:x['start']):
        p=d/f"block_{b['start']}";n=b['n'];A=b['A']
        h1=ary(p/'hits1.u8','u1').reshape(n,A)
        h100=ary(p/'hits100.u8','u1').reshape(n,A)
        top=ary(p/'top1_ids.i32','<i4').reshape(n,A)
        mask=ary(p/'masks.u64','<u8').reshape(n,A,2)
        assert np.array_equal(pop[mask.view('u1')].sum(2),h100)
        assert np.array_equal(top==gt[b['start']:b['start']+n,:1],h1)
        checked_masks+=n*A
        entries=ary(p/'baseline_entries.i32','<i4').reshape(n,3)
        for k,hs in [(1,h1),(100,h100)]:
            t=totals[k]
            for row,es in zip(hs,entries):
                v=list(map(int,row));base=v[0]
                local=[base]+[v[1+hubs.index(int(h))] for h in es]
                t['default']+=base;t['oracle']+=max(v)-base;t['small']+=max(local)-base
                t['positive']+=sum(x>base for x in v[1:])
                t['negative']+=sum(x<base for x in v[1:]);t['n']+=1
    for k,t in totals.items():
        f=full[ds,k];c=coverage[ds,k];n=t['n'];assert n==4096
        assertclose(t['default']/(n*k)*100,f['default_recall_pct'])
        assertclose(t['oracle']/(n*k)*100,f['oracle_gain_pp'])
        assertclose(t['small']/(n*k)*100,c['default_plus_actual_three_singles_oracle_gain_pp'])
        assertclose(t['small']/t['oracle'],c['actual_three_captured_oracle_gain_fraction'])
        assert t['positive']==f['positive_query_action_pairs'] and t['negative']==f['negative_query_action_pairs']

finite=rd(R/'results/finite_responses.json')
for ds in cfg['datasets']:
    original=np.load(E/'20260922_target_budget_response_v1/analysis'/f'{ds}.npz')
    for r in [x for x in finite if x['dataset']==ds]:
        h=original[f"K{r['K']}_L{r['L']}"];rows=h[:,1:].tolist();n=len(rows);k=r['K']
        # Original order is UnitHub1, UnitHub3, GT11, GT13, GT101, GT103, DefaultANN.
        same=sum(len(set(v))==1 for v in rows)
        gain=sum(max(v)-v[-1] for v in rows)
        missing=sum(k-v[-1] for v in rows)
        assertclose(same/n*100,r['all_seven_equal_hitcount_pct'])
        assertclose(gain/(n*k)*100,r['oracle_gain_pp'])
        assertclose(gain/missing,r['missing_mass_recoverable_fraction'])

all_inputs={}
for fname in ('consumed_inputs.json','opportunity_inputs.json'):
    for p,ident in rd(R/'reviews'/fname).items():
        now=Path(p);assert now.stat().st_size==ident['size']
        assert hashlib.sha256(now.read_bytes()).hexdigest()==ident['sha256'],p
        all_inputs[p]=ident
out={'status':'PASS','same_cohort_heads':len(full),'all_action_masks_and_K1_labels_verified':checked_masks,
     'finite_points_verified':len(finite),'prior_consumed_files_unchanged':len(all_inputs),
     'new_inputs_for_independent_checks':len(hashes),'seconds':time.perf_counter()-start,
     'independent_implementation':True,'independent_person_or_agent':False,'new_searches':0,'new_training':0}
for name,obj in [('numeric_audit.json',out),('verification_inputs.json',hashes)]:
    path=R/'reviews'/name;assert not path.exists();path.write_text(json.dumps(obj,indent=2)+'\n')
print(json.dumps(out,indent=2))
