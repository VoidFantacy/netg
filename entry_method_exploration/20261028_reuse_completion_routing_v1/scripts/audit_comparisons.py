import csv,json,statistics,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def rows(p):return list(csv.DictReader(p.open()))
def main():
 t=time.perf_counter();counts=[]
 for role,folder in [('formal','analysis'),('calibration','calibration_analysis')]:
  points=rows(R/f'{folder}/points.csv');comp=rows(R/f'{folder}/discrete_comparisons.csv')
  for x in comp:
   p=next(p for p in points if (p['dataset'],p['method'],p['L'])==(x['dataset'],x['method'],x['L']));controls=[p for p in points if p['dataset']==x['dataset'] and p['method']=='GT10'];ph=int(p['hits']);pq=float(p['qps']);reach=[g for g in controls if int(g['hits'])>=ph];fastest=max(reach,key=lambda g:float(g['qps'])) if reach else None;afford=[g for g in controls if float(g['qps'])>=pq];best=max(afford,key=lambda g:int(g['hits'])) if afford else None;dom=[g['L'] for g in controls if int(g['hits'])>=ph and float(g['qps'])>=pq]
   assert x['dominated_by_GT_L']==','.join(dom)
   if fastest:
    assert x['target_GT_L']==fastest['L'] and abs(float(x['target_speed_delta_pct'])-100*(pq/float(fastest['qps'])-1))<1e-8
    assert (x['target_speed_three_rounds_positive']=='True')==all(float(p[f'qps_round{i}'])>float(fastest[f'qps_round{i}']) for i in range(3))
   else:assert not x['target_GT_L']
   if best:assert x['budget_GT_L']==best['L'] and abs(float(x['budget_recall_delta_pp'])-(ph-int(best['hits']))/int(p['n']))<1e-8
   else:assert not x['budget_GT_L']
  counts.append(dict(role=role,comparisons=len(comp)))
 (R/'reviews/comparison_audit.json').write_text(json.dumps(dict(status='PASS_E189_DISCRETE_COMPARISONS',checks=counts,seconds=time.perf_counter()-t),indent=2)+'\n');print(json.dumps(counts))
if __name__=='__main__':main()
