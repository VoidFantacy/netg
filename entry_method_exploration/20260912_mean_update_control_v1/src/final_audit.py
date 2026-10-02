from shared import *
import re,ast
threads(8);resources();started=time.monotonic()
check(O/'reviews/prequery_freeze.json');check(O/'reviews/protected.json');check(O/'reviews/native_dependencies.json')
assert read(O/'reviews/verification.json')['status']=='PASS' and read(O/'reviews/visual_review.json')['status']=='PASS'
jobs=read(O/'logs/jobs.json');assert len(jobs)==2 and all(x['status']=='COMPLETE' and x['native']['actual_threads']==1 for x in jobs)
assert sum(x['actual'] for x in jobs)==167040 and sum(x['reserved'] for x in jobs)==167040
for p in files(O/'src'):
 if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
roots=[R/x for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/34_mean_update_control.md']]
links=0
for p in roots+[O/'report.md',O/'protocol.md']:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in link or link.startswith('#'):continue
  assert (p.parent/link.split('#')[0]).exists(),(p,link);links+=1
rs=read(O/'results/analysis.json')
for ds,batch,full,extra in [(DS[0],0,1,1),(DS[1],-2,3,5)]:
 d=next(x for x in rs['datasets'] if x['dataset']==ds);assert d['batch_net_hits']==batch and d['full_net_hits']==full and d['full_vs_batch_net_hits']==extra and d['passed']
rec=dict(status='PASS',NSG_calls=167040,HNSW_calls=166080,builds=60,counterfactual_single_steps=20,continuous_training_updates=0,
 protected_files=len(read(O/'reviews/protected.json')['files']),local_links=links,artifact_bytes=sum(x.stat().st_size for x in files(O)),
 independent_verification=read(O/'reviews/verification.json'),campaign_complete=False,seconds=time.monotonic()-started)
dump(O/'reviews/final_audit.json',rec);dump(O/'reviews/completion_audit.json',dict(status='PASS',stage_complete=True,campaign_complete=False,next='Exact NSG feedback reuse by complete entry identity, planned unrun'))
freeze(O/'reviews/final_artifact_freeze.json',files(O)+roots)
print(json.dumps(rec,indent=2),flush=True)
