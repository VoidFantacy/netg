import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import json,csv
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]
def main():
 assert not (R/'selection.json').exists();rows=list(csv.DictReader((R/'calibration_analysis/points.csv').open()));comp=list(csv.DictReader((R/'calibration_analysis/discrete_comparisons.csv').open()));sq=next(x for x in rows if x['method']=='SQ8-96' and x['L']=='200');pq=next(x for x in rows if x['method']=='REUSE-BLOCK' and x['L']=='200');s=next(x for x in comp if x['method']=='SQ8-96' and x['L']=='200')
 gain=float(sq['recall_pct'])-float(pq['recall_pct']);screen=(bool(s['target_speed_delta_pct']) and float(s['target_speed_delta_pct'])>=2 and s['target_speed_three_rounds_positive']=='True') or (bool(s['budget_recall_delta_pp']) and float(s['budget_recall_delta_pp'])>=.05)
 c=json.loads((R/'calibration/coco/config.json').read_text());n=c['queries']['n'];g=c['test_gt'];truth=np.memmap(g['path'],'<i8','r').reshape(-1,100)[g.get('row_start',0):][:n];main=np.fromfile(R/'calibration/coco/GT10_L200/raw/ids.i32','<i4').reshape(n,100);wide=np.fromfile(R/'calibration/coco/PQ384_diagnostic_L200.i32','<i4').reshape(n,384);short=np.fromfile(R/'calibration/coco/SQ8-96_L200/trace.i32','<i4').reshape(n,160)[:,64:];wc=sc=0
 for i in range(n):
  missing=set(map(int,truth[i]))-set(map(int,main[i]));wc+=len(missing&set(map(int,wide[i])));sc+=len(missing&set(map(int,short[i])))
 ratio=wc/sc if sc else 0;trigger=gain>=.1 and not screen and ratio>=.75
 rec=dict(status='FROZEN_CONDITIONAL_DECISION_BEFORE_FORMAL',cascade_triggered=trigger,L200_SQ8_minus_PQ_recall_pp=gain,SQ8_passes_GT10_exploration_screen=bool(screen),PQ384_missing_coverage=wc,SQ8_96_missing_coverage=sc,coverage_ratio=ratio,conditions=dict(recall_gain_ge_point10=gain>=.1,SQ8_fails_exploration_screen=not screen,PQ384_coverage_ge_75pct=ratio>=.75),formal_config='coco.formal_selected.json' if trigger else 'coco.json',configuration_tuned=False,old_B32_used_for_selection=False)
 (R/'selection.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps(rec),flush=True)
if __name__=='__main__':main()
