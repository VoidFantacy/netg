"""Check frozen selection consistency and exact-count threshold boundaries."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def rows(path):return list(csv.DictReader(path.open()))
def screen(row):
    return (bool(row['target_speed_delta_pct']) and float(row['target_speed_delta_pct'])>=2 and row['target_speed_three_rounds_positive']=='True') or (bool(row['budget_recall_delta_pp']) and float(row['budget_recall_delta_pp'])>=.05)
assert (R/'dense_complete.json').exists();notes=[];selected=set()
for window,pn,cn in [('primary','all_primary_points.csv','all_discrete_comparisons.csv'),('dense','all_dense_points.csv','all_dense_comparisons.csv')]:
    points={(x['dataset'],x['K'],x['method'],x['L']):x for x in rows(R/'analysis'/pn)}
    for row in rows(R/'analysis'/cn):
        if row['method'] not in ['REUSE-SQ','MAIN-SQ']:continue
        key=row['dataset'],row['K'],row['method'],row['L']
        if window=='primary' and screen(row):selected.add(key)
        if not row['budget_GT_L']:continue
        x=points[key];y=points[row['dataset'],row['K'],'GT10',row['budget_GT_L']]
        assert x['n']==y['n'];difference=int(x['hits'])-int(y['hits'])
        exact=2000*difference>=int(x['n'])*int(x['K']);floating=float(row['budget_recall_delta_pp'])>=.05
        if exact!=floating:notes.append(dict(window=window,key=key,budget_GT_L=row['budget_GT_L'],hit_difference=difference,n=int(x['n']),K=int(x['K']),float_delta_pp=row['budget_recall_delta_pp'],exact_budget_gate=exact,frozen_float_budget_gate=floating))
frozen={(d['dataset'],str(x['K']),x['method'],str(x['L'])) for d in json.loads((R/'dense_freeze.json').read_text())['decisions'] for x in d['positive_points']}
assert frozen==selected,(frozen-selected,selected-frozen)
v=dict(status='PASS_FROZEN_SCREEN_SELECTION_RECOMPUTED',primary_selected=len(selected),exact_threshold_boundary_notes=notes,scope='No new selection or experiment; exact-count boundaries reported separately from frozen float implementation.')
(R/'reviews/screen_numerics_audit.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v),flush=True)
