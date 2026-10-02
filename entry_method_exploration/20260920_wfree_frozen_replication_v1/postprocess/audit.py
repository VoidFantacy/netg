from pathlib import Path
import json,csv,hashlib,time,os,re
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''):h.update(b)
 return h.hexdigest()
lock=read(R/'config.locked.json');decision=read(R/'reviews/decision.json');assert read(R/'reviews/analysis_complete.json')['status']=='PASS'
assert read(R/'reviews/figures_visual_check.json')['status']=='PASS'
pre=read(R/'reviews/pre_query_lock.json')
for p,s in pre['files'].items():assert sha(R/p)==s,p
protected=read(R/'reviews/protected_before.json')
for p in protected:assert sha(p['path'])==p['sha256'],p['path']
for p,s in read(R/'reviews/source_freeze.json')['files'].items():assert sha(p)==s,p
inputs=[]
for ds,c in lock['datasets'].items():
 s=Path(c['index']).stat();assert s.st_size==c['index_stat']['bytes'] and s.st_mtime_ns==c['index_stat']['mtime_ns']
 m=read(R/'inputs'/ds/'manifest.json');assert m['created_unix']>pre['created_unix']
 for name,v in m['files'].items():assert sha(R/'inputs'/ds/name)==v;inputs.append(str(R/'inputs'/ds/name))
 g=read(R/'inputs'/ds/'gt_manifest.json');assert sha(R/'inputs'/ds/'gt.i32')==g['GT_sha256'];assert sha(R/'inputs'/ds/'queries.f32')==g['query_sha256']
 assert all(x['set_overlap']==100 and x['top1_float64_ok'] for x in g['independent_float64'])
times=list(csv.DictReader((R/'results/wall_rounds.csv').open()));assert len(times)==384
metrics=list(csv.DictReader((R/'results/metrics.csv').open()));assert len(metrics)==128
boots=set()
for m in metrics:
 group=[x for x in times if all(x[k]==m[k] for k in ['dataset','method','K','L'])];assert len(group)==3 and sorted(int(x['repeat']) for x in group)==[0,1,2]
 secs=[]
 for w in group:
  assert int(w['n'])==4096 and int(w['threads'])==1 and int(w['cpu'])==15 and w['formal']=='True'
  sec=float(w['seconds']);assert abs(float(w['qps'])-4096/sec)<1e-8;secs.append(sec);boots.add(w['boot_id'])
 done=read(R/'results'/m['dataset']/('k'+m['K'])/(m['method']+'_L'+m['L'])/'complete.json')
 assert secs==done['seconds'];mean=sum(4096/x for x in secs)/3;assert abs(float(m['qps'])-mean)<1e-8
assert len(boots)==1
jobs=read(R/'reviews/jobs.json');assert len(jobs)==4 and all(j['exit_code']==0 for j in jobs)
assert sum(j['reserved_calls'] for j in jobs)==2621824
assert sum(j['complete']['search_calls'] for j in jobs)==2621824
for a,b in zip(jobs,jobs[1:]):assert a['finished_unix']<=b['started_unix']
for j in jobs:
 p=Path('/proc')/str(j['pid'])/'cmdline'
 assert not p.exists() or str(R/'bin/evaluate').encode() not in p.read_bytes(),'search still active'
checks=[];docs=[ROOT/p for p in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/99_wfree_frozen_replication.md']]+list(R.glob('*.md'))
for p in docs:
 for link in re.findall(r'\]\(([^\n]+?)\)',p.read_text()):
  if link.startswith(('http:','https:','mailto:','#')):continue
  link=link.split('#',1)[0].strip('<>');target=(p.parent/link).resolve()
  # Only plain Markdown destinations are used by these project documents.
  checks.append(dict(source=str(p),target=str(target),exists=target.exists()))
missing=[x for x in checks if not x['exists']];assert not missing,missing
audit=dict(status='PASS_TASK_COMPLETE',method_decision=decision['status'],created_unix=time.time(),protected_SHA_assets=len(protected),large_NSG_stat_checks=2,input_file_hash_checks=len(inputs)+4,frozen_source_hash_checks=len(read(R/'reviews/source_freeze.json')['files']),single_boot_id=list(boots)[0],serial_jobs=4,formal_points=128,wall_rounds=384,total_search_calls=2621824,new_training=0,new_graph_builds=0,new_K10=0,default_changed=False,checked_local_links=len(checks),all_local_links_exist=True,pending_actions=[])
(R/'reviews/completion_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
files=['report.md','protocol.md','config.locked.json','reviews/decision.json','reviews/completion_audit.json','reviews/cost.json','results/metrics.csv','results/paired.csv','results/thresholds.csv','results/primary_L128.json','figures/recall_qps.png','figures/recall_qps.pdf','figures/primary_intervals.png','figures/primary_intervals.pdf']
(R/'complete.json').write_text(json.dumps(dict(status=decision['status'],task_complete=True,created_unix=time.time(),pending_actions=[],default_changed=False,files={f:sha(R/f) for f in files}),indent=2)+'\n')
(R/'state.json').write_text(json.dumps(dict(status=decision['status'],task_complete=True,pending_actions=[]),indent=2)+'\n')
print(json.dumps(audit,indent=2))
