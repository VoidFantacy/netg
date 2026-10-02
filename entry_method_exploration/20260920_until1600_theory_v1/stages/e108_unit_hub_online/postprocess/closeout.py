import sys,csv,re,shutil,urllib.parse,ast
from pathlib import Path
RUN=Path(__file__).resolve().parents[1];sys.path.insert(0,str(RUN/'src'))
from common import *
assert not (RUN/'reviews/completion_audit.json').exists()
assert read(RUN/'reviews/search_complete.json')['status']=='PASS' and read(RUN/'reviews/analysis_complete.json')['status']=='PASS'
protected_check();freeze=read(RUN/'reviews/search_source_freeze.json')['files'];models=read(RUN/'reviews/models_frozen.json')['files'];raw=read(RUN/'reviews/numeric_verification.json')['raw_files']
for r in freeze+models+raw+read(RUN/'reviews/closeout_before.json'):assert sha(r['path'])==r['sha256'],r['path']
for n in ['analysis_lock','report_source']:
 r=read(RUN/'reviews'/(n+'.json'))['source'];assert sha(r['path'])==r['sha256']
old=Path(LOCK['reference_E107'])
for p in (RUN/'source_before').rglob('*'):
 if p.is_file():assert sha(p)==sha(old/'source_after'/p.relative_to(RUN/'source_before'))
jobs=read(RUN/'reviews/jobs.json');assert len(jobs)==6 and all(j['exit_code']==0 for j in jobs) and all(a['finished_unix']<=b['started_unix'] for a,b in zip(jobs,jobs[1:]))
for j in jobs:
 proc=Path('/proc')/str(j['pid'])/'cmdline';assert not proc.exists() or str(RUN/'bin/evaluate').encode() not in proc.read_bytes()
search=[j for j in jobs if j['reserved_calls']];formal=[j for j in search if j['kind']=='formal'];assert sum(j['reserved_calls'] for j in search)==1106688
assert all(j['complete']['threads']==1 and j['complete']['cpu']==15 for j in search)
assert sum(j['complete']['wall_rounds'] for j in formal)==162 and len(models)==4
assert read(RUN/'reviews/models_frozen.json')['created_unix']<read(RUN/'reviews/inputs_validated.json')['created_unix']<search[0]['started_unix']
metrics=list(csv.DictReader((RUN/'results/metrics.csv').open()));pairs=list(csv.DictReader((RUN/'results/paired.csv').open()));assert len(metrics)==54 and len(pairs)==54
ranges=[]
for b in [x for x in metrics if x['method']=='UnitHub']:
 a=next(x for x in metrics if x['dataset']==b['dataset'] and x['method']=='GT10Default' and x['K']==b['K'] and x['L']==b['L'])
 outcome='faster_nonoverlap' if float(b['min_qps'])>float(a['max_qps']) else 'slower_nonoverlap' if float(b['max_qps'])<float(a['min_qps']) else 'overlap';ranges.append(dict(dataset=b['dataset'],K=b['K'],L=b['L'],outcome=outcome))
assert sum(r['outcome']=='faster_nonoverlap' for r in ranges)==0 and sum(r['outcome']=='slower_nonoverlap' for r in ranges)==4;dump(RUN/'results/timing_ranges.json',ranges)
figs=[identity(RUN/'figures'/(n+'.'+ext)) for n in ['recall_qps','same_L_qps'] for ext in ['png','pdf']];assert all(x['bytes']>1000 for x in figs)
dump(RUN/'reviews/visual_inspection.json',dict(status='PASS',figures=figs,method='Both PNG files viewed in tool output and compared to full metric tables; same figure objects exported to PDF.',notes=['Three real online methods shown.','Speed figure is same-L and quality differences kept separate.','Four panels use true K1/K100; no K100 below100.']))
docs=[ROOT/n for n in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/103_unit_hub_online.md']]+[RUN/n for n in ['report.md','protocol.md','reviews/interpretation_notes.md']]
links=[]
for p in docs:
 for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',p.read_text()):
  target=link.strip().strip('<>')
  if urllib.parse.urlsplit(target).scheme or target.startswith('#'):continue
  q=(p.parent/urllib.parse.unquote(target.split('#')[0])).resolve();assert q.exists() or q==RUN/'reviews/completion_audit.json',(str(p),link);links.append(dict(source=str(p),target=str(q)))
for p in list((RUN/'src').glob('*.py'))+list((RUN/'postprocess').glob('*.py')):ast.parse(p.read_text())
new_bytes=sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file());assert new_bytes<=LOCK['max_new_bytes'] and shutil.disk_usage(RUN).free>=4*1024**3
state=dict(status='COMPLETE_UNIT_HUB_ONLINE_NO_DEFAULT_CHANGE',completed_unix=time.time(),pending=[],default_changed=False,production_changed=False,stable_cross_dataset_replacement=False,timebox_research_continues=True)
dump(RUN/'state.json',state);dump(RUN/'reviews/document_checks.json',dict(status='PASS',documents=[identity(p) for p in docs],links=links))
after=RUN/'source_after';after.mkdir()
for n in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/103_unit_hub_online.md']:
 d=after/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,d)
audit=dict(status='PASS_STAGE_COMPLETE',state=state,protected_SHA_files=len(read(RUN/'reviews/protected_before.json')),NSG_stat_checks=2,frozen_source_files=len(freeze),frozen_graphs=len(models),raw_result_files=len(raw),NSG_calls=1106688,router_calls=sum(j['complete']['router_calls'] for j in search),formal_points=54,formal_wall_rounds=162,new_GT=0,new_training=0,new_graphs=4,threads=1,search_seconds=sum(j['seconds'] for j in search),max_rss_gib=max(j['complete']['maxrss_kib'] for j in search)/1024**2,new_bytes=new_bytes,local_links=len(links),visual_inspection='PASS',report=identity(RUN/'report.md'),source=identity(Path(__file__)),preserved_preexecution_arithmetic_and_draft_wording_corrections=True)
dump(RUN/'reviews/completion_audit.json',audit);assert all(Path(x['target']).exists() for x in links);dump(RUN/'complete.json',dict(status='COMPLETE',audit=identity(RUN/'reviews/completion_audit.json'),report=identity(RUN/'report.md')))
parent=read(TB/'state.json');assert parent['completed_NSG_calls']==1181184;parent.update(stage='E108 complete; E109 perfect target proxy gate ready',completed_stages=['E107','E108'],completed_NSG_calls=2287872,active_stage_reserved_NSG_calls=0,pending=['E109 prelocked fit information gate','evidence-derived next method only if justified','16:00 closeout']);dump(TB/'state.json',parent)
print(json.dumps(audit,ensure_ascii=False,indent=2))
