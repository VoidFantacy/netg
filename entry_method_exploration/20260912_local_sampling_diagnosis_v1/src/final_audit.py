from shared import *
import re,ast
threads(8);resources();started=time.monotonic()
check(O/'reviews/prequery_freeze.json');check(O/'reviews/protected.json');check(O/'reviews/native_dependencies.json')
assert read(O/'reviews/verification.json')['status']=='PASS';assert read(O/'reviews/visual_review.json')['status']=='PASS'
jobs=read(O/'logs/jobs.json');assert len(jobs)==2 and all(x['status']=='COMPLETE' for x in jobs)
assert sum(x['actual'] for x in jobs)==739008 and sum(x['reserved'] for x in jobs)==739008
for x in jobs:assert x['native']['actual_threads']==1
for p in files(O/'src'):
 if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
roots=[R/x for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/33_local_sampling_diagnosis.md']]
links=0
for p in [O/'report.md',O/'protocol.md']+roots:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in link or link.startswith('#'):continue
  path=link.split('#')[0];assert (p.parent/path).exists(),(p,path);links+=1
rs=read(O/'results/analysis.json')
for ds,total,best,cov,damage in [(DS[0],63,35,24,4),(DS[1],26,26,0,0)]:
 rows=[x for x in rs['contexts'] if x['dataset']==ds]
 assert sum(x['oracle_hit_gain'] for x in rows)==total and sum(x['best_net_hits'] for x in rows)==best
 assert sum(x['oracle_coverage_gap'] for x in rows)==cov and sum(x['oracle_cancellation_gap'] for x in rows)==damage
rec=dict(status='PASS',NSG_calls=739008,HNSW_calls=738432,builds=180,optimizer_updates=0,
 protected_files=len(read(O/'reviews/protected.json')['files']),local_links=links,artifact_bytes=sum(x.stat().st_size for x in files(O)),
 independent_verification=read(O/'reviews/verification.json'),campaign_complete=False,seconds=time.monotonic()-started)
dump(O/'reviews/final_audit.json',rec);freeze(O/'reviews/final_artifact_freeze.json',files(O)+roots)
dump(O/'reviews/completion_audit.json',dict(status='PASS',stage_complete=True,campaign_complete=False,next='Fixed same-state batch/full-gradient one-step control, planned unrun'))
print(json.dumps(rec,indent=2),flush=True)
