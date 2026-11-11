import csv,json,time,hashlib,statistics,struct
from pathlib import Path
from audit_results import load,sha
R=Path(__file__).resolve().parents[1]
def table(p,rows):
 with p.open('w') as f:w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 t=time.perf_counter();root=R/'dense_control/coco';c=json.loads((root/'config.json').read_text());done=json.loads((root/'complete.json').read_text());assert done['points']==9 and done['batches']==27;n=c['queries']['n'];g=load(c['test_gt']['path'],'q');truth=[set(g[i*100:(i+1)*100]) for i in range(n)];points=[];old=0
 for x in done['results']:
  m,L=x['method'],x['L'];p=Path(x['result_dir']);ids=load(p/'raw/ids.i32');score=load(p/'raw/distances.f32','f');hits=[len(set(ids[i*100:(i+1)*100])&truth[i]) for i in range(n)];h=hashlib.sha256(struct.pack('<QQ',n,100))
  for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:h.update((p/'raw'/name).read_bytes())
  h.update(bytes(n*16));assert all(h.hexdigest()==z['packet_sha256'] and z['threads']==1 for z in x['rounds'])
  previous=R/f'results/coco/{m}_L{L}/raw'
  if previous.exists():
   for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:assert (p/'raw'/name).read_bytes()==(previous/name).read_bytes()
   old+=1
  if m in ['SQ8-96','REUSE-BLOCK']:
   a=load(p/'access.u64','Q');assert len(a)==n*3 and max(a[0::3])<=2048 and max(a[2::3])<=96
  points.append(dict(method=m,L=L,n=n,recall_pct=sum(hits)/n,hits=sum(hits),failed_lt10=sum(z<10 for z in hits),qps=statistics.median(z['qps'] for z in x['rounds']),qps_min=min(z['qps'] for z in x['rounds']),qps_max=max(z['qps'] for z in x['rounds']),**{f'qps_round{i}':x['rounds'][i]['qps'] for i in range(3)}))
 controls=[x for x in points if x['method']=='GT10'];comparisons=[]
 for x in points:
  if x['method']=='GT10':continue
  target=[z for z in controls if z['recall_pct']>=x['recall_pct']];target=max(target,key=lambda z:z['qps']) if target else None;budget=[z for z in controls if z['qps']>=x['qps']];budget=max(budget,key=lambda z:z['recall_pct']) if budget else None;dom=[z for z in controls if z['qps']>=x['qps'] and z['recall_pct']>=x['recall_pct']]
  comparisons.append(dict(method=x['method'],L=x['L'],target_GT_L=target['L'] if target else None,target_GT_recall_pct=target['recall_pct'] if target else None,target_GT_qps=target['qps'] if target else None,target_speed_delta_pct=100*(x['qps']/target['qps']-1) if target else None,three_rounds_positive=all(x[f'qps_round{i}']>target[f'qps_round{i}'] for i in range(3)) if target else None,budget_GT_L=budget['L'] if budget else None,budget_recall_delta_pp=x['recall_pct']-budget['recall_pct'] if budget else None,dominated_by_GT_L=','.join(str(z['L']) for z in dom),nonoverlapping_QPS_dominance=','.join(str(z['L']) for z in dom if z['qps_min']>x['qps_max'])))
 candidate=next(x for x in comparisons if x['method']=='SQ8-96');speed=candidate['target_speed_delta_pct'] is not None and candidate['target_speed_delta_pct']>=2 and candidate['three_rounds_positive'];budget=candidate['budget_recall_delta_pp'] is not None and candidate['budget_recall_delta_pp']>=.05
 for name in ['freeze.json','dense_control_freeze.json']:
  for x in json.loads((R/name).read_text())['files']:assert sha(x['path'])==x['sha256'],x['path']
 out=R/'dense_control_analysis';out.mkdir();table(out/'points.csv',points);table(out/'discrete_comparisons.csv',comparisons)
 rec=dict(status='PASS_E190_DENSE_CONTROL_SECOND_IMPLEMENTATION',points=9,batches=27,primary_packets_equal=old,candidate_unchanged=True,primary_positive_screen_preserved=True,candidate_comparison=candidate,speed_screen=bool(speed),budget_recall_screen=bool(budget),scope='post-primary frozen grid/timing control on exposed test; not blind',internal_wall_seconds=sum(z['wall_seconds'] for x in done['results'] for z in x['rounds']),suite_seconds=done['outer_seconds'],seconds=time.perf_counter()-t)
 (R/'reviews/dense_control_results_audit.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps(rec),flush=True)
if __name__=='__main__':main()
