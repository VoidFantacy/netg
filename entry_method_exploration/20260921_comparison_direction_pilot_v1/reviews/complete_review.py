"""Closeout identities and documentation checks after all measured work."""
import json,hashlib,time,re,subprocess
from pathlib import Path
from urllib.parse import unquote

run=Path(__file__).resolve().parents[1]; root=run.parents[1]
read=lambda p:json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def ident(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def dump(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')

checked=[]
for name in ('native_frozen.json','python_frozen.json','models_frozen.json','preserved_assets.json'):
    for x in read(run/'reviews'/name)['files']:
        p=Path(x['path']); assert p.stat().st_size==x['bytes'] and sha(p)==x['sha256'],p
        checked.append(x)
for x in read(run/'reviews/before_final_closeout/identity.json')['files']:
    assert sha(Path(x['snapshot']))==x['sha256']
lock=read(run/'config.locked.json')
for c in lock['datasets'].values():
    s=Path(c['index']).stat(); expected=c['index_stat']
    assert s.st_size==expected['bytes'] and s.st_mtime_ns==expected['mtime_ns']
audit=read(run/'reviews/independent_final_audit.json')
assert audit['status']=='PASS' and audit['points']==140 and audit['wall_rounds']==420
for name in audit['required_audits']: assert read(run/'reviews'/name)['status']=='PASS'
assert read(run/'reviews/review_diagnostics.json')['status']=='PASS'
for j in read(run/'reviews/continuation_jobs.json'):assert j['exit_code']==0
# Verify absence by command identity, not an old PID that could be reused.
active=[]
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit():continue
    try:args=(proc/'cmdline').read_bytes().split(b'\0')
    except (FileNotFoundError,PermissionError,ProcessLookupError):continue
    if any(str(run/'src'/f).encode() in args for f in ('stage1.py','stage2.py','after_labels.py','analyze.py','final_audit.py','report.py')) or str(run/'bin/experiment').encode() in args:
        active.append(int(proc.name))
assert not active,active
fig=read(run/'reviews/figure_manifest.json')
for x in fig['files']+fig['data_files']:
    assert ident(Path(x['path']))==x
assert len(fig['files'])==6
dump(run/'reviews/figure_review.json',{'status':'PASS','reviewed_unix':time.time(),'png_visual_review':True,
    'checks':['three PNGs viewed; labels and legends visible','four panels and K scopes match measured data','paired intervals and repeated-wall ranges labeled separately','fit/CV/acceptance roles labeled; no clipping observed'],
    'files':fig['files'],'data_files':fig['data_files']})
docs=[root/f for f in ('summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/121_comparison_direction_pilot.md')]+[run/'report.md',run/'decision.md']
boundaries={'summary.md':'2026-09-21 **GT10服务结构理论与旧缓存检验完成**',
            'spec.md':'2026-09-21新增隔离[服务结构缓存分析器]',
            's-target.md':'2026-09-21 **本轮理论与检验完成',
            's-experiment.md':'2026-09-21 **GT10服务结构理论与旧缓存检查',
            'README.md':'最新理论记录：'}
links=0
for p in docs:
    s=p.read_text();boundary=boundaries.get(p.name)
    if boundary: s=s.split(boundary)[0]
    assert not any(line.endswith(' ') or line.endswith('\t') for line in s.splitlines()),p
    for url in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',s):
        if url.startswith(('http://','https://','#','mailto:')):continue
        target=unquote(url.strip('<>').split('#')[0]);assert (p.parent/target).exists(),(p,url)
        links+=1
subprocess.run(['git','diff','--check','--',*[str(p.relative_to(root)) for p in docs]],cwd=root,check=True)
paired=read(run/'results/paired.json'); primary=[x for x in paired if x['method']=='GraphCost' and x['reference']=='GT10']
assert len(primary)==20 and all(x['improved_queries']==0 and x['harmed_queries']==0 and x['qps_ranges_separated_negative'] for x in primary)
cost=read(run/'reviews/cost_ledger.json');assert cost['NSG_calls']==50541782 and cost['NSG_calls']<lock['max_search_calls']
size=sum(p.stat().st_size for p in run.rglob('*') if p.is_file());assert size<lock['max_new_bytes']
dump(run/'reviews/report_review.json',{'status':'PASS','reviewed_unix':time.time(),'report':ident(run/'report.md'),'decision':ident(run/'decision.md'),
    'scope':'complete curves, controls, CV, oracle limits, timing noise and errors reviewed; no new training or tuning'})
state={'status':'COMPLETED_NO_DEFAULT_CHANGE','completed_unix':time.time(),'pending':[],'active_processes':[],
       'decision':'This fixed E118 version has no measured net gain; shared-direction research is not ruled out.',
       'default_changed':False,'report':'report.md','reviewed_decision':'decision.md','completion_audit':'reviews/final_completion.json'}
dump(run/'state.json',state)
result={'status':'COMPLETE','completed_unix':time.time(),'points':140,'wall_rounds':420,'NSG_calls':cost['NSG_calls'],
        'source_model_protected_identity_records':len(checked),'original_measurement_audit':audit,
        'visual_review':'PASS','report_review':'PASS','document_current_sections_local_links':links,'source_snapshot_checks':'PASS',
        'active_processes':active,'artifact_bytes_before_completion_manifest':size,'new_searches_in_manual_review':0,'new_fits_in_manual_review':0,
        'default_changed':False,'decision':'COMPLETED_NO_DEFAULT_CHANGE','files':[ident(p) for p in docs]+[ident(run/'state.json'),ident(run/'reviews/review_diagnostics.json'),ident(run/'reviews/figure_review.json'),ident(run/'reviews/report_review.json'),ident(Path(__file__))]}
dump(run/'reviews/final_completion.json',result)
print(json.dumps({k:v for k,v in result.items() if k not in ('files','original_measurement_audit')},indent=2))
