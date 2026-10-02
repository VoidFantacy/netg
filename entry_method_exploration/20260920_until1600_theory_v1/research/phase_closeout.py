import json,time,hashlib,shutil,re,urllib.parse,ast,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];NEW=ROOT/'entry_method_exploration/20260920_until1900_theory_v1'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''):h.update(b)
 return h.hexdigest()
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
assert not (R/'complete.json').exists();assert read(NEW/'config.locked.json')['deadline_unix']==1789902000
refs={};origins={}
def add(x,origin):
 if not isinstance(x,dict):return
 if 'path' in x and 'sha256' in x:
  path=x['path'];assert path not in refs or refs[path]['sha256']==x['sha256'],(path,origin)
  refs[path]=x;origins.setdefault(path,[]).append(str(origin))
 for v in x.values():
  if isinstance(v,dict):add(v,origin)
  elif isinstance(v,list):
   for item in v:add(item,origin)
stages=[];jobs=[];stats={}
for st in sorted((R/'stages').iterdir()):
 complete=read(st/'complete.json');assert complete['status']=='COMPLETE';add(complete,st/'complete.json')
 audit=read(st/'reviews/completion_audit.json');assert audit['NSG_calls']>=0;stages.append(dict(stage=st.name,complete=ident(st/'complete.json'),audit=audit))
 for name in ['protected_before.json','search_source_freeze.json','source_freeze.json','binary_freeze.json','numeric_verification.json']:
  p=st/'reviews'/name
  if p.exists():
   obj=read(p)
   if isinstance(obj,list):
    for x in obj:add(x,p)
   else:add(obj,p)
 js=read(st/'reviews/jobs.json')
 for j in js:assert j['exit_code']==0;assert j['finished_unix']>=j['started_unix'];jobs.append(dict(stage=st.name,**j))
 cfg=read(st/'config.locked.json')
 for ds,c in cfg.get('datasets',{}).items():
  p=c['index'];v=c['index_stat'];assert p not in stats or stats[p]==v;stats[p]=v
assert sum(s['audit']['NSG_calls'] for s in stages)==2797056
for p in [R/'research/graph_dependence_v1/complete.json',R/'research/initial_seed_order_v1/complete.json']:add(read(p),p)
for j in read(R/'research/graph_dependence_v1/jobs.json'):jobs.append(dict(stage='graph_dependence',**j));assert j['exit_code']==0
for i,j in enumerate(read(R/'research/initial_seed_order_v1/jobs.json')):
 jobs.append(dict(stage='initial_order',kind='compile' if i==0 else 'initial_order',finished_unix=j['started_unix']+j['seconds'],finish_derived_from_recorded_elapsed=True,**j));assert j['exit_code']==0
e99=ROOT/'entry_method_exploration/20260916_nsg_search_optimization_v1/reviews'
for p in [e99/'protected.json',e99/'frozen_code.json']:
 for name,value in read(p).items():
  if '/ACSG/ACSG/' in name or '/build/' in name or 'libACSG.optimized.a' in name:
   add(dict(path=name,sha256=value if isinstance(value,str) else value['sha256']),p)
for p,x in refs.items():assert sha(p)==x['sha256'],p
for p,v in stats.items():s=Path(p).stat();assert s.st_size==v['bytes'] and s.st_mtime_ns==v['mtime_ns'],p
for x in read(R/'config.locked.json')['source_before']:assert sha(x['snapshot'])==x['sha256']
assert sha(ROOT/'AGENTS.md')==read(R/'config.locked.json')['source_before'][0]['sha256']
query_jobs=sorted([j for j in jobs if j['kind'] in ['smoke','main','formal']],key=lambda x:x['started_unix'])
assert all(a['finished_unix']<=b['started_unix'] for a,b in zip(query_jobs,query_jobs[1:]))
for q in query_jobs:
 if q['kind']=='formal':
  assert not any(j is not q and j['kind'] in ['build','compile','prepare','graphs','topology'] and max(q['started_unix'],j['started_unix'])<min(q['finished_unix'],j['finished_unix']) for j in jobs)
for j in jobs:
 if 'pid' not in j:continue
 p=Path('/proc')/str(j['pid'])/'cmdline'
 assert not p.exists() or str(R).encode() not in p.read_bytes(),('owned job still live',j['pid'])
v=read(R/'stages/e111_rank_core_certificate/results/identity_violation_records.json');assert len(v)==15 and len({(x['dataset'],x['query_index']) for x in v})==1
assert read(R/'state.json')['synthetic_calls']==6
draft=R/'reviews/synthesis_before_extension';draft.mkdir()
for name in ['report.md','state.json','research/working_notes.md']:
 p=draft/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/name,p)
for name in ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/107_timebox_theory_synthesis.md']:
 p=draft/'root'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,p)
p=R/'report.md';t=p.read_text();t=t.replace('2026-09-20，北京时间13:05:42–16:00的限时理论研究。阶段检验均已完成，截止验收由[状态](state.json)单独记录。','2026-09-20首阶段理论研究综合。原13:05:42–16:00目标已由用户于15:34延长到19:00；本报告封存已完成的E107–E111与理论核验，整体目标仍在[19:00接续版本](../20260920_until1900_theory_v1/state.json)推进。');t=t.replace('截止后没有预排训练、扩大m/路径或追加seed/ef的任务。','原停止版本没有预排训练、扩大m/路径或追加seed/ef的任务。用户延长后的新研究由独立版本记录，不能把延长时间当作重启旧网格的理由。');p.write_text(t)
p=ROOT/'summary.md';t=p.read_text().replace('限时理论综合：阶段完成，待16:00截止验收','首阶段理论综合完成；用户目标延长至19:00',1);p.write_text(t)
p=ROOT/'s-experiment.md';t=p.read_text().replace('截止验收待16:00','用户已延长至19:00，本阶段先封存',1);p.write_text(t)
p=ROOT/'s-target.md';parts=p.read_text().split('\n\n');assert parts[1].startswith('2026-09-20当前用户目标持续到北京时间16:00。');parts[1]='2026-09-20用户已将活动目标改为持续推进到北京时间19:00。E107–E111及首阶段理论综合完成并封存，后继见[19:00版本](entry_method_exploration/20260920_until1900_theory_v1/state.json)与[资源/截止合同](entry_method_exploration/20260920_until1900_theory_v1/config.locked.json)。当前先审查更充分的图条件及其与既有BTG/Atlas/效用画像的区别，未启动新模型或搜索。新增真实NSG上限1,200,000，两阶段合计不超过原4M；18:50禁止新搜索，19:00交付。原停止候选与默认保持。';p.write_text('\n\n'.join(parts))
p=ROOT/'experiment_history/107_timebox_theory_synthesis.md';t=p.read_text().replace('最终截止状态以[父状态]','用户于15:34把整体目标延长到19:00，本条首阶段完成状态以[父状态]',1).replace('截止后无自动训练、补网格或部署队列。','本条没有自动训练、补网格或部署队列；19:00新接续独立建协议。');p.write_text(t)
p=R/'research/working_notes.md';t=p.read_text().replace('当前仅证据审查与截止验收，没有在运行的搜索或训练。最终时间边界以[父状态](../state.json)为准。','用户15:34已把目标延长到19:00，本阶段封存，整体工作接续到[新版本](../../20260920_until1900_theory_v1/state.json)。本阶段没有待恢复的搜索或训练。');p.write_text(t)
docs=[ROOT/n for n in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/107_timebox_theory_synthesis.md']]+[R/'report.md']+list((R/'research').glob('*.md'))+[R/'research/graph_dependence_v1/report.md']
links=[];future={R/'reviews/completion_audit.json'}
for p in docs:
 for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',p.read_text()):
  target=target.strip('<> ')
  if urllib.parse.urlsplit(target).scheme or target.startswith('#'):continue
  q=(p.parent/urllib.parse.unquote(target.split('#')[0])).resolve();assert q.exists() or q in future,(p,target);links.append(dict(source=str(p),target=str(q)))
for p in (R/'research').glob('*.py'):ast.parse(p.read_text())
bytes_used=sum(p.stat().st_size for p in R.rglob('*') if p.is_file());free=shutil.disk_usage(R).free
assert bytes_used<2**31 and free>=4*2**30
peak=max(s['audit']['max_rss_gib'] for s in stages);assert peak<40
state=dict(status='PHASE_COMPLETE_GOAL_EXTENDED_TO_1900',completed_unix=time.time(),completed_NSG_calls=2797056,synthetic_calls=6,completed_stages=['E107','E108','E109','E110','E111'],active_stage_reserved_NSG_calls=0,pending=[],default_changed=False,production_changed=False,overall_goal_complete=False,next_timebox=str(NEW),goal_extension=ident(R/'reviews/goal_extension.json'))
dump(R/'state.json',state)
after=R/'source_after';after.mkdir()
for p in docs[:7]:dest=after/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
dump(R/'reviews/identity_verification.json',dict(status='PASS',unique_SHA_files=len(refs),files=[dict(**x,origins=origins[p]) for p,x in sorted(refs.items())],NSG_stat_checks=stats,source_before_snapshots_verified=True,production_E99_archive_verified=True))
dump(R/'reviews/document_checks.json',dict(status='PASS',documents=[ident(p) for p in docs],links=links))
audit=dict(status='PASS_PHASE_COMPLETE_GOAL_EXTENDED',state=state,stage_reports=[dict(stage=s['stage'],complete=s['complete'],report=s['audit']['report']) for s in stages],NSG_calls=2797056,synthetic_calls=6,new_dataset_router_graphs=4,new_synthetic_graphs=2,new_bottom_graphs=0,new_GT=0,new_training=0,new_graph_derived_diagnostic_labels=True,heldout_access=False,formal_points=54,formal_wall_rounds=162,serial_query_jobs=len(query_jobs),owned_jobs_closed=sum('pid' in j for j in jobs),recorded_jobs_completed=len(jobs),initial_order_jobs_have_no_PID_records=3,max_rss_gib=peak,logical_new_bytes=bytes_used,free_gib=free/2**30,unique_verified_SHA_files=len(refs),verified_NSG_stats=len(stats),local_links=len(links),E111_recorded_ID_violations=15,E111_distinct_violation_queries=1,report=ident(R/'report.md'),identity=ident(R/'reviews/identity_verification.json'),documents=ident(R/'reviews/document_checks.json'),source=ident(Path(__file__)),overall_goal_complete=False,next_deadline_local='2026-09-20 19:00:00 +08:00')
dump(R/'reviews/completion_audit.json',audit);dump(R/'complete.json',dict(status='COMPLETE_PHASE',report=ident(R/'report.md'),audit=ident(R/'reviews/completion_audit.json'),overall_goal_complete=False,next_timebox=str(NEW)))
dump(NEW/'reviews/previous_phase_complete.json',dict(created_unix=time.time(),previous_complete=ident(R/'complete.json'),previous_report=ident(R/'report.md'),previous_audit=ident(R/'reviews/completion_audit.json')))
print(json.dumps({k:audit[k] for k in ['status','NSG_calls','synthetic_calls','unique_verified_SHA_files','owned_jobs_closed','local_links','logical_new_bytes','overall_goal_complete']},indent=2))
