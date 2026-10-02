from pathlib import Path
import json,csv,hashlib,os,time,ast,re,math
R=Path('/data/netg/ACSG');D=R/'entry_method_exploration';O=Path(__file__).resolve().parent
E55=D/'20260912_final_method_comparison_v1';E56=D/'20260912_construction_only_rl_v1';E57=D/'20260912_expanded_final_comparison_v1';E58=D/'20260912_accepted_action_conflicts_v1';E59=D/'20260912_frozen_pool_transfer_v1'
def read(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def dump(p,a):p.write_text(json.dumps(a,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
assert os.sched_getaffinity(0)=={8};assert all(os.environ[k]=='1' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'])
started=time.monotonic();allowed={str(R/x) for x in ['summary.md','spec.md','s-target.md','s-experiment.md']};transitions=[];unchanged=0
for x in read(E59/'reviews/final_artifact_freeze.json')['files']:
 p=Path(x['path']);now=sha(p)
 if now!=x['sha256']:
  assert str(p) in allowed,p;before=O/'source_before'/p.name;assert sha(before)==x['sha256'],before
  transitions.append(dict(path=str(p),before_sha=x['sha256'],after_sha=now,preserved_before=str(before)))
 else:unchanged+=1
assert {x['path'] for x in transitions}==allowed
for x in read(E59/'reviews/protected.json')['files']:assert sha(Path(x['path']))==x['sha256'],x['path']
old=read(E55/'results/analysis.json');new=read(E57/'results/analysis.json');old_points=[x for x in old['points'] if x['phase']=='validation'];new_points=[x for x in new['points'] if x['phase']=='validation'];assert len(old_points)==len(new_points)==45
for a,b in zip(old_points,new_points):
 for k in a:assert a[k]==b[k],(k,a,b)
 assert b['source_run']=='E55'
assert old['selection']==new['selection']
with (E57/'results/timings.csv').open() as f:times=list(csv.DictReader(f))
assert len(times)==225
for t in times:assert abs(float(t['QPS'])-2000/float(t['seconds']))<1e-8
for ds in [x for x in new['selection']]:
 ref='baseline_soft' if ds.startswith('webvid') else 'gt10_hard';rows=[x for x in new['paired'] if x['dataset']==ds and x['reference']==ref]
 assert len(rows)==5 and all(x['delta_recall_pp']<0 and x['QPS_envelope_low_pct']<=0<=x['QPS_envelope_high_pct'] for x in rows)
 small=next(x for x in rows if x['L']==128)
 assert (small['gain_hits'],small['loss_hits'],small['rescued_failures'],small['new_failures'])==((27,36,4,2) if ds.startswith('webvid') else (0,15,0,2))
r=read(E58/'results/summary.json');a=r['aggregates'];assert r['cost']['NSG_calls']==3146 and r['cost']['HNSW_calls']==943104 and r['cost']['builds']==1185
assert sum(x['accepted'] for x in a)==908 and sum(x['decision_steps'] for x in a)==2400
assert [(x['monitor_gain_hits'],x['monitor_loss_hits']) for x in a if x['stage']=='E53']==[(80,84),(8,8)]
assert all(x['monitor_conflict_steps']==0 for x in a if x['dataset'].startswith('yandex'))
assert [x['monitor_conflict_steps'] for x in a if x['dataset'].startswith('webvid')]==[7,9,0]
assert all(.7<=x['monitor_trajectory_loss_top5_share']<=.778 for x in r['runs'] if x['dataset'].startswith('webvid') and x['stage'] in ['E52','E53'])
tr=read(E59/'results/summary.json');cc=[x for x in tr['splits'] if x['phase']=='cal'];assert [(x['any_gain_queries'],x['oracle_hits'],x['best_hit_net'],x['best_hit_uncovered'],x['best_hit_own_loss']) for x in cc]==[(11,30,12,17,1),(7,12,9,2,1)]
assert all(x['train_positive'] for x in tr['transfers'])
assert all(sum(x['monitor_positive_cal_negative'] for x in tr['transfers'] if x['dataset']==ds)==7 for ds in new['selection'])
for x in tr['splits']:assert x['oracle_hits']-x['best_hit_net']==x['best_hit_uncovered']+x['best_hit_own_loss']
assert all(x['opposite_model_sign_queries']==0 for x in cc)
stages={'E52':'20260912_direct_candidate_commit_v1','E53':'20260912_feedback_step_rl_v1','E56':'20260912_construction_only_rl_v1'}
with (O/'training_costs.csv').open() as f:
 for row in csv.DictReader(f):
  cost=read(D/stages[row['stage']]/'results/cost.json')
  assert int(row['NSG_calls'])==cost['NSG_calls'] and int(row['HNSW_calls'])==cost['HNSW_calls'] and int(row['physical_builds'])==cost['builds'] and abs(float(row['process_seconds'])-cost['training_process_seconds'])<1e-10
bud=read(E56/'logs/jobs.json');assert len(bud)==4 and all(x['status']=='COMPLETE' and x['completed_at']<1789218900 for x in bud)
for stage in [E55,E57,E58]:
 jobs=read(stage/'logs/jobs.json');assert all(x['status']=='COMPLETE' for x in jobs)
 assert max(x.get('closed_at',x.get('completed_at')) for x in jobs)<1789220400
assert read(E56/'reviews/training_verification.json')['serialized_constant_profile_rows']==6544
assert read(E58/'reviews/verification.json')['checkpoint_train_rows']+read(E58/'reviews/verification.json')['checkpoint_monitor_rows']==675840
assert read(E59/'reviews/verification.json')['independent_set_scoring_rows']==233472
roles=read(O/'next_input_inventory.json');assert roles['new_vectors_read']==roles['new_GT_labels_read']==roles['new_ANN']==roles['new_training']==0
assert 4*40*1024+160*16*3+1024+16*3==172592<180000
text=(O/'final_report.md').read_text();labels={'nsg':'NSG','fast30k':'Fast（GT1、30K）','gt10_hard':'FastGT10-hard','baseline_soft':'GT10-soft匹配起点','best_new':'cal选中新候选'}
for p in [O/'final_report.md',R/'summary.md']:
 lines=[x.split('|')[1:-1] for x in p.read_text().splitlines() if x.startswith('| WebVid |') or x.startswith('| Yandex |')];assert len(lines)==9
 for line,x in zip(lines,[x for x in new_points if x['L']==128]):
  vals=[s.strip() for s in line];assert vals[0]==('WebVid' if x['dataset'].startswith('webvid') else 'Yandex') and vals[1]==labels[x['model']]
  assert vals[2]==f'{x["recall_pct"]:.3f}' and vals[3]==f'{x["QPS"]:.2f}' and vals[5]==f'{x["failure_pct"]:.2f}'
assert 'WebVid815、Yandex821' in text and '815/821' in (R/'summary.md').read_text()
links=0
for p in [R/x for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']]+[O/'final_report.md',O/'next_experiment_design.md']:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in link or link.startswith('#'):continue
  assert (p.parent/link.split('#')[0]).exists(),(p,link);links+=1
for p in O.glob('*.py'):ast.parse(p.read_text())
active=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:args=proc.joinpath('cmdline').read_bytes().decode(errors='replace').split('\0')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 for arg in args:
  if arg.startswith(str(D)) and Path(arg).name in ['train.py','train_v2.py','run.py','deploy.py','evaluate']:
   active.append(dict(pid=int(proc.name),entrypoint=arg));break
assert not active,active
dump(O/'handoff_transition.json',dict(status='PASS',unchanged_E59_sealed_files=unchanged,allowed_root_document_transitions=transitions,older_artifacts_unchanged=True))
dump(O/'final_review.json',dict(status='PASS',numerical_claims_recomputed=True,final45_points_identical_to_frozen_E55=True,wall_repeats=225,source_selection_unchanged=True,scope_inventory_pass=True,training_and_query_deadlines_pass=True,active_research_processes=active,local_links=links,old_artifacts_unchanged=True,default_replaced=False,seconds=time.monotonic()-started,reviewed_at=time.time()))
print('CLOSEOUT INDEPENDENT REVIEW PASS',flush=True)
