import sys,csv,re,shutil,urllib.parse,ast
from pathlib import Path
RUN=Path(__file__).resolve().parents[1];sys.path.insert(0,str(RUN/'src'))
from common import *
assert not (RUN/'reviews/completion_audit.json').exists()
assert read(RUN/'reviews/search_complete.json')['status']=='PASS'
assert read(RUN/'reviews/analysis_complete.json')['status']=='PASS'
protected_check()
freeze=read(RUN/'reviews/search_source_freeze.json')['files'];models=read(RUN/'reviews/frozen_models.json')['files'];raw=read(RUN/'reviews/numeric_verification.json')['raw_files']
for r in freeze+models+raw+read(RUN/'reviews/closeout_before.json'):assert sha(r['path'])==r['sha256'],r['path']
for name in ['analysis_lock','report_source']:
 r=read(RUN/'reviews'/(name+'.json'))['source'];assert sha(r['path'])==r['sha256']
jobs=read(RUN/'reviews/jobs.json');assert len(jobs)==6 and all(j['exit_code']==0 for j in jobs)
assert all(a['finished_unix']<=b['started_unix'] for a,b in zip(jobs,jobs[1:]))
searches=[j for j in jobs if j['reserved_calls']];assert sum(j['reserved_calls'] for j in searches)==1181184
assert all(j['complete']['threads']==1 and j['complete']['cpu']==15 for j in searches)
for j in jobs:
 proc=Path('/proc')/str(j['pid'])/'cmdline';assert not proc.exists() or str(RUN/'bin/evaluate').encode() not in proc.read_bytes()
metrics=list(csv.DictReader((RUN/'results/metrics.csv').open()));pairs=list(csv.DictReader((RUN/'results/paired.csv').open()));interaction=list(csv.DictReader((RUN/'results/interactions.csv').open()))
assert len(metrics)==144 and len(pairs)==270 and len(interaction)==36
assert all(x['K'] in ['1','100'] and x['formal_QPS']=='False' and (x['K']!='100' or int(x['L'])>=100) for x in metrics)
figs=[identity(RUN/'figures'/(n+'.'+ext)) for n in ['factorial_quality_cost','entry_count_effect'] for ext in ['png','pdf']];assert all(r['bytes']>1000 for r in figs)
dump(RUN/'reviews/visual_inspection.json',dict(status='PASS',figures=figs,method='Both PNG figures viewed in tool output, axes and all four panels compared with numerical tables; PDFs exported from same figures.',notes=['NDC axis explicitly not online QPS.','GT10 one-to-three means mostly negative; no CI significance implied by line plot.','All eight methods visible in quality-work comparison.']))
docs=[ROOT/n for n in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/102_initialization_factorial.md']]+[RUN/n for n in ['report.md','protocol.md','research.md','reviews/interpretation_notes.md']]+list((TB/'research').glob('*.md'))
links=[]
for p in docs:
 for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',p.read_text()):
  target=link.strip().strip('<>')
  if urllib.parse.urlsplit(target).scheme or target.startswith('#'):continue
  q=(p.parent/urllib.parse.unquote(target.split('#')[0])).resolve();assert q.exists() or q==RUN/'reviews/completion_audit.json',(str(p),link);links.append(dict(source=str(p),target=str(q)))
for p in list((RUN/'src').glob('*.py'))+list((RUN/'postprocess').glob('*.py')):ast.parse(p.read_text())
new_bytes=sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file());assert new_bytes<=LOCK['max_new_bytes'] and shutil.disk_usage(RUN).free>=LOCK['min_free_gib']*1024**3
state=dict(status='COMPLETE_INITIALIZATION_FACTORIAL',completed_unix=time.time(),pending=[],default_changed=False,production_changed=False,new_formal_QPS=False,full_GT10_causal_explanation=False,timebox_research_continues=True)
dump(RUN/'state.json',state)
dump(RUN/'reviews/document_checks.json',dict(status='PASS',documents=[identity(p) for p in docs],links=links))
after=RUN/'source_after';after.mkdir()
for n in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/102_initialization_factorial.md']:
 d=after/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,d)
audit=dict(status='PASS_STAGE_COMPLETE',state=state,protected_SHA_files=len(read(RUN/'reviews/protected_before.json')),NSG_stat_checks=2,frozen_source_files=len(freeze),frozen_models=len(models),raw_result_files=len(raw),NSG_calls=1181184,ANN_routes=sum(j['complete']['ann_calls'] for j in searches),synthetic_calls=2,new_GT=0,new_graphs=0,new_training=0,new_formal_QPS=0,points=144,paired_contrasts=270,interaction_contrasts=36,threads=1,search_seconds=sum(j['seconds'] for j in searches),max_rss_gib=max(j['complete']['maxrss_kib'] for j in searches)/1024**2,new_bytes=new_bytes,local_links=len(links),visual_inspection='PASS',report=identity(RUN/'report.md'),source=identity(Path(__file__)))
dump(RUN/'reviews/completion_audit.json',audit)
assert all(Path(x['target']).exists() for x in links)
dump(RUN/'complete.json',dict(status='COMPLETE',audit=identity(RUN/'reviews/completion_audit.json'),report=identity(RUN/'report.md')))
parent=read(TB/'state.json');parent.update(stage='E107 complete; deriving ordinary UnitHub ANN control',completed_stages=['E107'],completed_NSG_calls=1181184,pending=['E108 frozen ordinary small-graph comparison','proxy-information gate if justified','16:00 closeout']);dump(TB/'state.json',parent)
print(json.dumps(audit,ensure_ascii=False,indent=2))
