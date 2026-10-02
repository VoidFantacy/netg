import datetime,hashlib,json,pathlib,re,subprocess
D=pathlib.Path(__file__).resolve().parent.parent;R=D.parent.parent
read=lambda p:json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
 return h.hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
a=read(D/'reviews/results_audit.json');assert a['status']=='PASS' and a['main_configurations']==36 and a['plain_rounds']==108 and a['real_search_calls']==2296000 and a['actual_batch4_count']
assert read(D/'state.json')['status']=='MEASUREMENTS_COMPLETE'
post=read(D/'postprocess_state.json');assert post['status']=='REPORTS_READY_FOR_MANUAL_REVIEW'
rows=read(D/'results/summary.json')['metrics'];assert len(rows)==36 and {x['K'] for x in rows}=={1,100}
assert {x['method'] for x in rows}=={'NSG','GT10-hard','GT10-soft-t1','GATE','HNSW'}
assert all(x['kernel']=='reference' if x['method']=='HNSW' else x['kernel'] in ['current','span-batch4'] for x in rows)
checked={}
for name in ['frozen.json','protected.json']:
 x=read(D/'reviews'/name)
 for p,h in x.items():assert sha(pathlib.Path(p))==h,p
 checked[name]=len(x)
# The runner rehashed all large inputs after all query work; only lightweight
# report/plot/doc work happened since. Verify that completed audit, not a new query.
identity=read(D/'reviews/post_run_identity.json');assert identity['status']=='PASS'
assets=read(D/'reviews/assets.json')
for name,x in assets.items():assert pathlib.Path(name).stat().st_size==x['bytes'],name
backup=read(D/'reviews/git_backup.json')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==backup['main_head_unchanged']
assert sha(R/'.git/index')==backup['index_unchanged_sha256']
assert subprocess.check_output(['git','rev-parse',backup['branch']],cwd=R,text=True).strip()==backup['commit']
visual=read(D/'reviews/figures_visual_check.json');assert visual['status']=='PASS'
for name,h in visual['png_sha256'].items():assert sha(D/name)==h,name
running=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:args=(p/'cmdline').read_bytes().split(b'\0')
 except OSError:continue
 if any(str(D/'bin'/n).encode() in args for n in ['compare','compatibility']):running.append(p.name)
assert not running,running
docs=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/95_shared_span_batch4_comparison.md']
for name in docs:
 t=(R/name).read_text();assert 'E102' in t,name
 if not name.endswith('95_shared_span_batch4_comparison.md'):assert '95_shared_span_batch4' in t,name
for p in [D/'report.md',R/'experiment_history/95_shared_span_batch4_comparison.md']:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in link:continue
  target=p.parent/link.split('#')[0]
  if target==D/'reviews/final_review.json':continue
  assert target.exists(),(str(p),link)
size=sum(p.stat().st_size for p in D.rglob('*') if p.is_file());assert size<512*1024**2,size
now=datetime.datetime.now().astimezone().isoformat()
complete=dict(status='COMPLETE_SHARED_KERNEL_COMPARISON',completed_at=now,real_search_calls=2296000,main_search_calls=1800000,compatibility_search_calls=496000,new_synthetic_searches=0,main_configurations=36,main_plain_rounds=108,compatibility_configurations=64,compatibility_status=a['compatibility_status'],production_changed=False,default_changed=False,git_backup=backup['commit'],report_sha256=sha(D/'report.md'))
save(D/'complete.json',complete)
final=dict(status='PASS',reviewed_at=now,shared_kernel_for_all_four_methods=True,paired_current_controls=True,same_run_full_hnsw=True,actual_batch4_count=True,independent_gt_scoring=True,all_return_and_ndc_checks=True,compatibility_status=a['compatibility_status'],manual_figures_review=True,frozen_hash_checks=checked,all_assets_rehashed_by_completed_runner=identity['assets'],git_backup_main_index_verified=True,running_query_processes=running,directory_bytes=size,artifact_sha256={str(p.relative_to(R)):sha(p) for p in [D/'report.md',D/'complete.json',D/'results/metrics.csv',D/'results/shared_kernel_comparison.csv',*(R/n for n in docs)]})
save(D/'reviews/final_review.json',final);post.update(status='COMPLETE',manual_review=True,completed_at=now);save(D/'postprocess_state.json',post)
print(json.dumps({k:v for k,v in final.items() if k!='artifact_sha256'},ensure_ascii=False,indent=2))
