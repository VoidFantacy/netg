import csv,json,hashlib,datetime,math
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def main():
 assert (R/'primary_complete.json').exists() and not (R/'dense_freeze.json').exists();decisions=[];cfgs=[]
 for cp in sorted((R/'configs').glob('*.json')):
  if cp.name.count('.')!=1:continue
  c=json.loads(cp.read_text());ds=c['dataset'];points=list(csv.DictReader((R/f'analysis/{ds}/points.csv').open()));comp=list(csv.DictReader((R/f'analysis/{ds}/discrete_comparisons.csv').open()));grids={};cl={};positive=[]
  for x in comp:
   if x['method'] not in ['REUSE-SQ','MAIN-SQ']:continue
   speed=bool(x['target_speed_delta_pct']) and float(x['target_speed_delta_pct'])>=2 and x['target_speed_three_rounds_positive']=='True';budget=bool(x['budget_recall_delta_pp']) and float(x['budget_recall_delta_pp'])>=.05
   if not (speed or budget):continue
   K,L=int(x['K']),int(x['L']);controls=sorted([z for z in points if int(z['K'])==K and z['method']=='GT10'],key=lambda z:int(z['L']));target=next((z for z in controls if z['L']==x['target_GT_L']),None);quality=float(x['recall_pct']);nums={L}
   if target:
    hi=int(target['L']);lower=[z for z in controls if int(z['L'])<hi and float(z['recall_pct'])<quality];lo=max([int(z['L']) for z in lower],default=min(int(z['L']) for z in controls));nums.update([lo,hi]);nums.update(int(round(lo+(hi-lo)*j/6)) for j in range(1,6));bracket=[lo,hi]
   else:
    top=max(int(z['L']) for z in controls);nums.add(top);nums.update(min(2048,int(round(top*f))) for f in [1.125,1.25,1.5]);bracket=[top,None]
   nums={max(K,z) for z in nums};grids.setdefault(str(K),set()).update(nums);cl.setdefault(str(K),set()).add(L);positive.append(dict(K=K,L=L,method=x['method'],primary_speed_pass=bool(speed),primary_budget_pass=bool(budget),original_bracket=bracket,dense_control_L=sorted(nums),original_candidate_recall=quality,primary_target_speed_delta_pct=x['target_speed_delta_pct']))
  decisions.append(dict(dataset=ds,positive_points=positive,reason='one frozen quality-bracket check; no candidate/model/budget changes' if positive else 'no apparent SQ positive; no additional matrix'))
  if positive:
   d=json.loads(json.dumps(c));d['K_L']={k:sorted(v) for k,v in grids.items()};d['completion_L']={k:sorted(v) for k,v in cl.items()};d['output_dir']=str((R/'storage/dense_controls'/ds).resolve());p=R/f'configs/{ds}.dense.json';p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n');cfgs.append(p)
 files=cfgs+[R/'storage/benchmark',R/'src/benchmark.cpp',R/'protocol.md']+[R/'scripts'/x for x in ['analyze_dense.py','audit_dense_results.py','compress_dense_traces.py','select_dense_controls.py','run_dense_all.py']]
 files +=[p for p in (R/'analysis').rglob('*.csv')];rec=dict(status='FROZEN_SINGLE_DENSE_STAGE_BEFORE_NEW_POINTS',timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),decisions=decisions,files=[dict(path=str(p.resolve()),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files],candidate_parameters_changed=False,blind_confirmation=False,no_PDF=True)
 (R/'dense_freeze.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n');print(json.dumps(dict(datasets=len(cfgs),apparent_positive_points=sum(len(x['positive_points']) for x in decisions))),flush=True)
if __name__=='__main__':main()
