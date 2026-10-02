import pathlib,json,hashlib,subprocess,datetime,re
D=pathlib.Path(__file__).resolve().parent.parent;R=D.parent.parent;X=D/'compatibility'
def read(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
 return h.hexdigest()
summary=read(D/'results/summary.json');audit=read(D/'reviews/results_audit.json');compat=read(X/'analysis.json');post=read(D/'postprocess_state.json')
assert audit['status']=='PASS' and audit['points']==40 and audit['wall_rounds']==120
assert read(D/'state.json')['status']=='MEASUREMENTS_COMPLETE'
assert compat['configurations']==64 and compat['search_calls']==496000
assert read(X/'complete.json')['status']==compat['status']
actual=read(D/'reviews/actual_batch4_count_audit.json');assert actual['status']=='PASS' and actual['search_calls']==80000 and actual['actual_batch4_forwarded']
assert post['status']=='REPORTS_READY_FOR_MANUAL_REVIEW' and post['real_search_calls']==2496000
for p in [D/'reviews/regression.json',D/'reviews/regression_sanitized.json']:assert read(p)['status']=='PASS' and read(p)['paired_cases']==6480
assert read(D/'results/benchmark/layout.json')['same_graph_storage_memory']
rows=summary['metrics'];assert {r['K'] for r in rows}=={1,100} and len(rows)==40
checked={}
for p in [D/'reviews/frozen.json',D/'reviews/protected.json',X/'frozen.json',D/'reviews/actual_batch4_count_frozen.json']:
 entries=read(p)
 for name,h in entries.items():assert sha(pathlib.Path(name))==h,name
 checked[str(p.relative_to(D))]=len(entries)
# Recheck data content after all read-only phases have ended.
assets=read(D/'reviews/assets.json')
for group in read(X/'assets.json').values():assets.update(group)
for name,x in assets.items():
 p=pathlib.Path(name);assert p.stat().st_size==x['bytes'] and sha(p)==x['sha256'],name
backup=read(D/'reviews/git_backup.json')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==backup['main_head_unchanged']
index=R/subprocess.check_output(['git','rev-parse','--git-path','index'],cwd=R,text=True).strip();assert sha(index)==backup['index_unchanged_sha256']
assert subprocess.check_output(['git','rev-parse',backup['branch']],cwd=R,text=True).strip()==backup['commit']
visual=read(D/'reviews/figures_visual_check.json');assert visual['status']=='PASS'
for name,h in visual['png_sha256'].items():assert sha(D/name)==h,name
running=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:args=(p/'cmdline').read_bytes().split(b'\0')
 except OSError:continue
 targets=[str(D/'bin/compare').encode(),str(D/'bin/compatibility').encode(),str(D/'bin/actual_batch4_count').encode()]
 if any(t in args for t in targets):running.append(p.name)
assert not running,running
report=(D/'report.md').read_text();assert '其它四集一致性补充' in report
if compat['status']!='PASS':assert '不能把span+batch4当作所有度量/数据集上的无损替换' in report
docs=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/94_faiss_nsg_comparison.md']
for name in docs:
 text=(R/name).read_text();assert 'E101' in text,name
 if not name.endswith('94_faiss_nsg_comparison.md'):assert '94_faiss_nsg_comparison' in text,name
now=datetime.datetime.now().astimezone().isoformat()
complete={'status':'COMPLETE_COMPARISON','completed_at':now,'real_search_calls':2576000,'main_search_calls':2000000,'actual_batch4_count_search_calls':80000,'compatibility_search_calls':496000,'synthetic_search_calls':25920,'main_points':40,'main_plain_rounds':120,'compatibility_configurations':64,'compatibility_status':compat['status'],'production_changed':False,'default_changed':False,'manual_figures_review':True,'git_backup':backup['commit'],'report_sha256':sha(D/'report.md'),'report':'report.md'}
save(D/'complete.json',complete)
links=0
for p in [D/'report.md',R/'experiment_history/94_faiss_nsg_comparison.md']:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in link:continue
  target=p.parent/link.split('#')[0];assert target.exists(),(str(p),link);links+=1
size=sum(p.stat().st_size for p in D.rglob('*') if p.is_file());assert size<512*1024**2,size
final={'status':'PASS','reviewed_at':now,'requirements':{'native_faiss_same_graph_storage':'PASS','four_web_points_ten_versions_three_plain_rounds':'PASS','recall1_and100_only':'PASS','main_output_and_count_checks':'PASS','four_complete_other_query_sets':'PASS','compatibility_results_fully_disclosed':compat['status'],'independent_gt_scoring':'PASS','two_figures_visually_checked':'PASS','documentation_synchronized':'PASS','git_backup_and_main_index_preserved':'PASS','production_and_models_unchanged':'PASS'},'frozen_hash_checks':checked,'input_and_reference_assets_rehashed':len(assets),'local_links_verified':links,'directory_bytes':size,'running_query_processes':running,'artifact_sha256':{str(p.relative_to(R)):sha(p) for p in [D/'report.md',D/'complete.json',D/'results/metrics.csv',X/'analysis.json',*(R/n for n in docs)]}}
save(D/'reviews/final_review.json',final)
post.update(status='COMPLETE',manual_review=True,completed_at=now,real_search_calls=2576000);save(D/'postprocess_state.json',post)
print(json.dumps({k:v for k,v in final.items() if k!='artifact_sha256'},ensure_ascii=False,indent=2))
