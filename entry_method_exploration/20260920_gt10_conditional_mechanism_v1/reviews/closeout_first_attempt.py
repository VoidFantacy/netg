import sys,csv,re,shutil,urllib.parse,ast
from pathlib import Path
RUN=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(RUN/'src'))
from common import *
assert not (RUN/'reviews/completion_audit.json').exists()
assert read(RUN/'reviews/decision.json')['status']=='STOP_GROUPMEAN_CANDIDATE'
assert read(RUN/'reviews/search_complete.json')['status']=='PASS'
assert read(RUN/'reviews/analysis_complete.json')['status']=='PASS'
assert read(RUN/'reviews/action_effects_complete.json')['status']=='PASS'
protected_check();protected=read(RUN/'reviews/protected_before.json')
search=read(RUN/'reviews/search_source_freeze.json')
for p,digest in search['files'].items():assert sha(p)==digest,p
models=read(RUN/'reviews/models_frozen.json')
for r in models['files']:assert sha(r['path'])==r['sha256'],r['path']
prefit=read(RUN/'reviews/pre_fit_lock.json')
assert prefit['created_unix']<models['created_unix']<search['created_unix']
for p,digest in prefit['files'].items():assert sha(p)==digest,p
raw_count=0
for ds in read(RUN/'reviews/numeric_verification.json')['datasets']:
    for r in ds['files']:assert sha(r['path'])==r['sha256'],r['path'];raw_count+=1
for ds in LOCK['datasets']:
    p=RUN/'inputs'/ds;manifest=read(p/'manifest.json')
    assert manifest['created_unix']>models['created_unix']
    for name,digest in manifest['files'].items():assert sha(p/name)==digest
for phase in ['analysis','action_effects']:
    lock=read(RUN/'reviews'/(phase+'_source_lock.json'))['source'];assert sha(lock['path'])==lock['sha256']
jobs=read(RUN/'reviews/jobs.json')
assert len(jobs)==4 and all(j['exit_code']==0 and j['complete']['threads']==1 and j['complete']['cpu']==15 for j in jobs)
assert all(jobs[i]['finished_unix']<=jobs[i+1]['started_unix'] for i in range(3))
calls=sum(j['complete']['search_calls'] for j in jobs);ann=sum(j['complete']['ann_calls'] for j in jobs)
assert calls==361856 and calls<=LOCK['max_NSG_calls'] and ann==16448
assert sum(j['seconds'] for j in jobs)<=LOCK['search_seconds']
assert max(j['complete']['maxrss_kib'] for j in jobs)*1024<=LOCK['max_rss_gib']*1024**3
assert models['seconds']<=LOCK['prepare_seconds']
for j in jobs:
    p=Path('/proc')/str(j['pid'])/'cmdline'
    assert not p.exists() or str(RUN/'bin/evaluate').encode() not in p.read_bytes(),'search process still live'
before=read(RUN/'reviews/closeout_before.json')
for kind in ['source_before','source_before_closeout']:
    for r in before[kind]:assert sha(r['path'])==r['sha256'],r['path']
docs=[ROOT/n for n in ['AGENTS.md','spec.md','summary.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/101_gt10_conditional_mechanism.md']]+[RUN/n for n in ['report.md','protocol.md','research.md']]
links=[]
for p in docs:
    txt=p.read_text();assert txt.count('\\[')==txt.count('\\]'),p
    for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',txt):
        target=link.strip().strip('<>')
        if urllib.parse.urlsplit(target).scheme or target.startswith('#'):continue
        dest=urllib.parse.unquote(target.split('#')[0]);q=(p.parent/dest).resolve()
        assert q.exists(),(str(p),link)
        links.append(dict(source=str(p),target=str(q)))
for p in (RUN/'postprocess').glob('*.py'):ast.parse(p.read_text())
figs=[identity(RUN/'figures'/(name+'.'+ext)) for name in ['groupmean_quality','conditional_correspondence'] for ext in ['png','pdf']]
assert all(f['bytes']>1000 for f in figs)
dump(RUN/'reviews/visual_inspection.json',dict(status='PASS',method='Both PNG figures viewed in tool output, labels/axes/point directions/intervals compared with decision JSON; PDFs exported from same figures.',figures=figs,notes=['All displayed intervals cross zero.','Candidate auxiliary Web hard separated from primary Web soft.','Permutation plot labels four fixed interventions and descriptive uncertainty.']))
metrics=list(csv.DictReader((RUN/'results/metrics.csv').open()));effects=list(csv.DictReader((RUN/'results/action_effects.csv').open()))
assert len(metrics)==44 and len(effects)==36 and all(r['formal_QPS']=='False' and r['K'] in ['1','100'] for r in metrics)
decision=read(RUN/'reviews/decision.json');assert len(decision['primary'])==4 and all(not r['quality_pass'] for r in decision['datasets'])
assert all(r['CI98_75'][0]<=0<=r['CI98_75'][1] for r in decision['primary'])
assert all(r['CI95_descriptive'][0]<=0<=r['CI95_descriptive'][1] for r in decision['mechanism'])
new_bytes=sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())
assert new_bytes<=LOCK['max_new_bytes'] and shutil.disk_usage(RUN).free>=LOCK['min_free_gib']*1024**3
state=dict(status='COMPLETE_CONDITIONAL_MECHANISM_STOP_GROUPMEAN',method_decision='STOP_GROUPMEAN_CANDIDATE',research_loop_complete=True,stable_improvement_found=False,full_GT10_causal_explanation=False,default_changed=False,production_changed=False,new_formal_QPS=False,conditional_ANN_wall_entered=False,pending=[],reason='Both prelocked exact quality gates failed; close this candidate without alpha/seed/group tuning. Mechanism contrasts remain inconclusive.',completed_unix=time.time())
dump(RUN/'state.json',state)
dump(RUN/'reviews/document_checks.json',dict(status='PASS',documents=[identity(p) for p in docs],local_links_checked=len(links),links=links))
after=RUN/'source_after';after.mkdir(exist_ok=False)
for n in ['AGENTS.md','spec.md','summary.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/101_gt10_conditional_mechanism.md']:
    dest=after/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,dest)
audit=dict(status='PASS_TASK_COMPLETE',scientific_decision=decision['status'],complete_loop=['exact mechanism decomposition','one derived candidate','frozen real search verification','paired analysis and hypothesis limitation','stop decision and synchronized report'],protected_old_sha_files=len(protected),NSG_stat_checks=2,NSG_new_full_hash=False,frozen_source_files=len(search['files']),frozen_model_files=len(models['files']),verified_raw_result_files=raw_count,models_frozen_before_evaluation_payload=True,calls=calls,ann_routes=ann,new_gradient_training=0,new_GT=0,new_graph_builds=0,new_K10=0,new_formal_QPS=0,method_points=len(metrics),posthoc_action_comparisons=len(effects),threads=1,serial_jobs=4,search_job_seconds=sum(j['seconds'] for j in jobs),max_rss_gib=max(j['complete']['maxrss_kib'] for j in jobs)/1024**2,new_artifact_bytes_before_final_manifests=new_bytes,free_gib=shutil.disk_usage(RUN).free/1024**3,local_document_links=len(links),visual_inspection='PASS',report=identity(RUN/'report.md'),source=identity(Path(__file__)),source_snapshots_preserved=True,default_changed=False,production_changed=False,pending=[],completed_unix=time.time())
dump(RUN/'reviews/completion_audit.json',audit)
dump(RUN/'complete.json',dict(status='COMPLETE',state=state,audit=identity(RUN/'reviews/completion_audit.json'),report=identity(RUN/'report.md')))
print(json.dumps(audit,ensure_ascii=False,indent=2))
