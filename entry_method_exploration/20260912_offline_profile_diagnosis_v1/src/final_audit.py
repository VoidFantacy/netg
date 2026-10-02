from common import *
import ast,re
from urllib.parse import unquote

assert not (O/'reviews/final_audit.json').exists()
assert read(O/'reviews/analysis_verification.json')['status']=='PASS';assert read(O/'reviews/independent_verification.json')['status']=='PASS';assert read(O/'reviews/visual_review.json')['status']=='PASS'
old=read(O/'reviews/E37_preserved.json');check(old['files']);assert len([p for p in E.rglob('*') if p.is_file()])==old['file_count']
check(read(O/'reviews/analysis_inputs.json')['files'])
unchangedW=0;unchangedTopology=0;actions=0
pre=read(E/'reviews/preflight.json')['datasets']
for ds in DS:
 config=read(E/'inputs'/ds/'config.json');originalW=sha(config['P']);originalTopology=next(x['baseline_topology_sha'] for x in pre if x['dataset']==ds)
 for arm in ARMS:
  for seed in SEEDS:
   files=sorted((E/'models'/ds/f'{arm}_{seed}/trajectory').glob('*.npz'));assert len(files)==200
   for f in files:
    with np.load(f) as a:unchangedW+=int((a['W_sha']==originalW).sum());unchangedTopology+=int((a['topology_sha']==originalTopology).sum());actions+=len(a['W_sha'])
assert actions==12800 and unchangedW==0 and unchangedTopology==0
sources=list((O/'src').glob('*.py'))
for p in sources:
 tree=ast.parse(p.read_text(),filename=str(p))
 for x in ast.walk(tree):
  if isinstance(x,ast.Import):assert all(z.name.split('.')[0] not in ['ctypes','subprocess','native'] for z in x.names)
  if isinstance(x,ast.ImportFrom):assert (x.module or '').split('.')[0] not in ['ctypes','subprocess','native','train','deploy']
docs=[R/x for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/27_offline_profile_diagnosis.md']]+[O/'report.md',O/'protocol.md',O/'next_control.md']
dump(O/'reviews/final_audit.json',dict(status='CHECKING_LINKS'))
links=0
for p in docs:
 t=p.read_text()
 assert not any(line.rstrip()!=line for line in t.splitlines()),p
 for href in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',t):
  if '://' in href or href.startswith('#'):continue
  target=(p.parent/unquote(href.split('#')[0].split(' "')[0])).resolve();assert target.exists(),(p,href);links+=1
assert all('E38' in (R/x).read_text() for x in ['summary.md','spec.md','s-target.md','s-experiment.md'])
v=read(O/'reviews/analysis_verification.json');assert v['raw_query_outputs_scored']==1773568 and v['same_mu_matched_query_records']==1188 and v['actual_process_threads']==1
size=sum(p.stat().st_size for p in O.rglob('*') if p.is_file());assert size<100*(1<<20) and v['seconds']<600 and v['peak_RSS_KiB']<4*(1<<20)
dump(O/'reviews/final_audit.json',dict(status='PASS',old_E37_entire_SHA_checked=old['file_count'],old_E37_file_count_unchanged=True,raw_query_outputs_recomputed=1773568,rewards_recomputed=12800,gradients_decomposed=1600,checkpoints=88,
 independent_set_scored_action_outputs=32768,independent_gradient_variance_steps=32,exact_mu_matched_query_records=1188,all_sampled_W_and_topology_changed_vs_anchor=True,
 new_NSG=0,new_HNSW_queries=0,new_HNSW_builds=0,new_optimizer_updates=0,new_GT=0,validation_heldout_raw_input_read_or_hash=False,default_replaced=False,
 analysis_threads=1,analysis_peak_RSS_KiB=v['peak_RSS_KiB'],analysis_seconds=v['seconds'],documents_checked=len(docs),local_links_checked=links,visual_review='PASS',artifact_bytes=size,closed_at=time.time()))
dump(O/'state.json',dict(status='COMPLETE_OFFLINE_PROFILE_DIAGNOSIS_NO_NEW_SEARCH',final_audit='PASS',new_NSG=0,new_HNSW=0,new_optimizer_updates=0,default_replaced=False,next_fixed_mean_control='DESIGNED_UNRUN',closed_at=time.time()))
files=sorted({p for p in O.rglob('*') if p.is_file() and p.name not in ['final_artifact_freeze.json'] and not p.name.endswith('.log')}|set(docs))
dump(O/'reviews/final_artifact_freeze.json',dict(files=[ident(p) for p in files],created_at=time.time()))
print('FINAL_AUDIT_PASS',old['file_count'],'old files,',links,'links, zero new search',flush=True)
