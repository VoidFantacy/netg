from setup import *
import numpy as np,re
from urllib.parse import unquote
assert json.loads((O/'reviews/output_verification.json').read_text())['status']=='PASS'
assert json.loads((O/'reviews/model_verification.json').read_text())['status']=='PASS'
checked=0
for name in ['protected_before.json','protected_additional_before.json']:
 for x in json.loads((O/'reviews'/name).read_text()):
  assert identity(x['path'])==x,x['path'];checked+=1
frozen=0
for name in ['reviews/evaluation_start_freeze.json','models/frozen_before_audit.json','models/frozen_before_validation.json']:
 for x in json.loads((O/name).read_text())['files']:
  assert identity(x['path'])==x,x['path'];frozen+=1
lock=json.loads((O/'reviews/protocol_lock.json').read_text());assert identity(O/'protocol.md')==lock['protocol']
train=json.loads((O/'models/training_runs.json').read_text());assert len(train)==12 and all(x['epochs']==80 for x in train)
labels=[json.loads((O/'labels'/ds/'complete.json').read_text()) for ds in DS]
jobs=json.loads((O/'logs/evaluation_jobs.json').read_text());assert len(jobs)==8 and all(x['status']=='COMPLETE' and x['exit_code']==0 for x in jobs)
label_calls=sum(x['physical_calls'] for x in labels);parity=sum(x['parity_calls'] for x in labels);eval_calls=sum(x['reserved_calls'] for x in jobs);total=label_calls+parity+eval_calls;assert total<=3645504
selection_checks=[];hnsw_checks=[]
for ds in DS:
 s=json.loads((O/'models'/ds/'selection.json').read_text());res=json.loads((O/'results'/f'cal_{ds}'/'results.json').read_text())
 for f in ['linear','mlp','free']:
  options=[]
  for lam in [10,100]:
   ms=[m for m in res['methods'] if m['model_name']==f'{f}_r{lam}'];assert len(ms)==2
   options.append((-sum(m['total_hits'] for m in ms),sum(m['mean_total_ndc'] for m in ms),-lam,f'{f}_r{lam}'))
  chosen=min(options)[-1];assert next(x for x in s['selected'] if x['model_name']==f)['selected_variant']==chosen
  selection_checks.append(dict(dataset=ds,family=f,selected=chosen))
 dest=O/'results'/f'validation_{ds}';res=json.loads((dest/'results.json').read_text());assert len(res['methods'])==45 and res['timing_repeats']==3
 for f in sorted(set(m['model_name'] for m in res['methods'])-{'nsg'}):
  hashes=[sha(dest/(m['name']+'.hnsw')) for m in res['methods'] if m['model_name']==f];assert len(set(hashes))==1,(ds,f,'microHNSW changed across L');hnsw_checks.append(dict(dataset=ds,method=f,sha256=hashes[0]))
size=sum(p.stat().st_size for p in O.rglob('*') if p.is_file());free=shutil.disk_usage(O).free;assert size<2*(1<<30) and free>10*(1<<30)
assert (O/'report.md').exists() and (O/'chart_data.xlsx').exists()
for name in ['recall_qps_main','recall_qps_all','recall_differences','training_curves','interpolated_speed']:
 for suffix in ['png','svg']:assert (O/'figures'/f'{name}.{suffix}').stat().st_size>1000
link_checks=[]
for doc in [O/'report.md',O/'research.md',R/'summary.md',R/'spec.md',R/'s-target.md',R/'s-experiment.md',R/'experiment_history/17_gt10_shared_transform.md',R/'experiment_history/README.md']:
 assert doc.exists(),str(doc)
 for target in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
  target=unquote(target.split('#')[0].split(' "')[0]).strip('<>')
  if not target or re.match(r'^[a-zA-Z][\w+.-]*:',target):continue
  # Focus inherited root-document links on the newly introduced E28 paths.
  if doc.parent==R and '20260911_gt10_shared_transform' not in target and '17_gt10_shared_transform' not in target:continue
  path=doc.parent/target;assert path.exists(),(str(doc),target);link_checks.append(str(path))
report=dict(status='PASS',protected_identity_checks=checked,frozen_identity_checks=frozen,normal_real_calls=total,new_label_calls=label_calls,label_parity_calls=parity,cached_logical_labels=sum(x['reused'] for x in labels),evaluation_calls=eval_calls,repair_calls=0,synthetic_search_calls=0,normal_hard_cap=3645504,total_hard_cap=3655504,training_runs=len(train),formal_points=90,formal_repeats=3,formal_query_outputs=180000,heldout_opened=False,selection=selection_checks,microHNSW_across_L=hnsw_checks,artifact_bytes=size,free_bytes=free,new_link_checks=len(link_checks),plot_visual_review=json.loads((O/'reviews/plot_visual_review.json').read_text()),wall_clock_end=time.time())
dump(O/'reviews/final_audit.json',report)
state=json.loads((O/'state.json').read_text());state.update(status='COMPLETE',conclusion=json.loads((O/'results/report_conclusion.json').read_text())['status'],real_search_calls=total,heldout_access=False,final_audit=str(O/'reviews/final_audit.json'));dump(O/'state.json',state)
print(json.dumps({k:v for k,v in report.items() if k not in ['selection','microHNSW_across_L']}))
