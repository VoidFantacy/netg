from common import *
import csv, re, shutil, sys
os.sched_setaffinity(0,{8})
assert not (O/'reviews/completion_audit.json').exists()
check(O/'reviews/preconstruction_freeze.json');check(O/'reviews/prebuild_freeze.json');check(O/'reviews/prequery_freeze.json')
check(O/'reviews/analysis_source_freeze.json');check(O/'reviews/protected_before.json')
for x in read(O/'reviews/large_asset_stat.json'):
    s=Path(x['path']).stat();assert (s.st_size,s.st_mtime_ns)==(x['bytes'],x['mtime_ns'])
    x['after_stat_matches']=True
large=read(O/'reviews/large_asset_stat.json')
gate=read(O/'results/gate.json');assert gate['status']=='STOP_E95_NO_DEVELOPMENT_GATE'
assert len(gate['candidates'])==4 and all(not x['pass_development'] for x in gate['candidates'])
rows=list(csv.DictReader((O/'results/aux_paired.csv').open()));assert len(rows)==24
assert len([x for x in rows if x['group']=='full'])==8
assert all(int(x['net_hits'])<0 for x in rows)
assert all(int(x['delta_failures'])>0 for x in rows if x['group']=='full')
# Recheck the frozen acceptance arithmetic from independently exported aligned arrays.
checks=[]
for ds in DS:
    cfg=read(O/'inputs'/f'{ds}_aux.json');result=read(O/'results'/ds/'aux/results.json')
    assert result['physical_graph_calls']==95520 and result['timing_repeats']==0 and len(result['methods'])==6
    for name in ['full','diag']:
        for L in [64,128]:
            z=np.load(O/'results'/f'{ds}_{name}_L{L}.npz')
            d=z['new_hits'].astype(np.int64)-z['old_hits'].astype(np.int64)
            assert np.array_equal(d,z['delta'])
            for group,sl in [('full',slice(None)),('half0',slice(0,3976)),('half1',slice(3976,None))]:
                x=next(x for x in rows if x['dataset']==ds and x['model']==name and int(x['L'])==L and x['group']==group)
                dd=d[sl];old=z['old_hits'][sl];new=z['new_hits'][sl]
                assert int(dd.sum())==int(x['net_hits']) and abs(float(x['delta_recall_pp'])-int(dd.sum())*100/(10*len(dd)))<1e-12
                assert int((new==0).sum()-(old==0).sum())==int(x['delta_failures'])
                checks.append(dict(dataset=ds,model=name,L=L,group=group,net_hits=int(dd.sum()),delta_failures=int(x['delta_failures'])))
    for name in ['identity','full','diag']:
        m=read(O/'models'/ds/name/'model.json');P=np.fromfile(m['W'],np.float32).reshape(m['hub_count'],m['dim']);ids=np.fromfile(m['mapping'],np.int32)
        inspect_graph(m['graph_file'],P,ids)
    old=read(O/'models'/ds/'statistics.json');f=read(O/'inputs/sources.json')[ds]['fit']
    for key,field,count,dtype in [('queries_file','fit_query_prefix_sha256',20000*cfg['dim'],np.float32),('row_ids','fit_rows_prefix_sha256',20000,np.int64)]:
        arr=np.fromfile(f[key],dtype,count=count)
        assert hashlib.sha256(arr.tobytes()).hexdigest()==old[field]
jobs=read(O/'logs/jobs.json');assert len(jobs)==10
assert all(j['status']=='COMPLETE' and j['exit_code']==0 for j in jobs)
assert sum(j['reserved_NSG'] for j in jobs)==194304
assert sum(j['kind']=='build' for j in jobs)==6 and sum(j['kind']=='query' for j in jobs)==4
assert sum(j['native_build']['builds'] for j in jobs if j['kind']=='build')==6
live=[]
for j in jobs:
    path=Path('/proc')/str(j['pid'])/'cmdline'
    if path.exists() and str(O/'bin').encode() in path.read_bytes():live.append(j['pid'])
assert not live,'native job still live'
for phase,n,base in [('preflight',1536,256),('aux',95424,15904)]:
    v=read(O/'reviews'/f'{phase}_verification.json')
    assert v['status']=='PASS' and v['independent_set_mask_rows']==n and v['baseline_full_fields_regression_rows']==base and v['parity_samples']==192
roots=['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']
assert sha(R/'AGENTS.md')==sha(O/'source_before/AGENTS.md')
assert subprocess.check_output(['git','status','--short','--untracked-files=no'],cwd=R)==(O/'logs/git_before.txt').read_bytes(),'unexpected tracked status change'
docs=[R/x for x in roots]+[R/'experiment_history/87_query_moment_graph_and_branch_stop.md']+[O/x for x in ['protocol.md','research.md','report.md','decision.md']]
missing=[];links=0
for p in docs:
    t=p.read_text()
    assert not any(line.rstrip()!=line for line in t.splitlines()),('trailing whitespace',p)
    for target in re.findall(r'\]\(([^)]+)\)',t):
        if target.startswith(('http:','https:','mailto:','#')):continue
        target=target.split('#')[0].split(' "')[0]
        dest=(p.parent/target).resolve()
        if dest==O/'reviews/completion_audit.json':continue
        links+=1
        if not dest.exists():missing.append(dict(source=str(p),target=target))
assert not missing,missing
assert 'STOP_CURRENT_FIXED_H_PROFILE_GRAPH_BRANCH' in (R/'s-target.md').read_text()
assert 'E95' in (R/'summary.md').read_text() and 'E95' in (R/'spec.md').read_text()
assert '87_query_moment_graph_and_branch_stop.md' in (R/'s-experiment.md').read_text()
for name in roots+['experiment_history/87_query_moment_graph_and_branch_stop.md']:
    dest=O/'root_after'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/name,dest)
for name in ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:
    result=subprocess.run(['git','diff','--no-index','--check',str(O/'source_before'/name),str(R/name)],capture_output=True,text=True)
    assert result.returncode in [0,1] and not result.stdout and not result.stderr,(name,result.stdout,result.stderr)
decision=dict(status='STOP_CURRENT_FIXED_H_PROFILE_GRAPH_BRANCH',user_objective='持续推进，最后给出结论，要么有更好的方法，要么停止当前分支',better_method_established=False,branch_stopped=True,default_changed=False,defaults={'webvid':'GT10-soft-t1','yandex':'GT10-hard'},new_experiment='E95',reason='All four new candidate-dataset development gates failed; existing optimization, support, transfer and final frontier evidence reviewed.',stop_scope=['current parameter-perturbation RL','current fixed-H profile augmentation and grouping','current shortcut and parent-restoration local repairs','E95 full/diag query-moment construction'],pending_experiments=[],not_claimed=['all RL impossible','all entry learning impossible','whole ACSG terminated','new QPS gain'])
dump(O/'decision.json',decision)
state=read(O/'state.json');state.update(branch_status=decision['status'],branch_stopped=True,pending_native_jobs=[],pending_experiments=[],default_changed=False);dump(O/'state.json',state)
resources()
audit=dict(status='PASS_OBJECTIVE_STOP_BRANCH_VERIFIED',objective=decision['user_objective'],requirements=[
    dict(requirement='Make substantive progress beyond a status restatement',evidence=['research.md','protocol.md','logs/jobs.json','results/construction.json'],verified='Three mechanism families assessed and E95 actually ran six builds and four serial query jobs.'),
    dict(requirement='Obtain a better method or stop the current branch',evidence=['decision.json','decision.md','results/gate.json','results/aux_paired.csv','../../s-target.md'],verified='Stop alternative explicitly adopted; all four new development gates failed, supported by older results and scoped to the current branch.'),
    dict(requirement='Freeze hypothesis and gates before testing',evidence=['reviews/preconstruction_freeze.json','reviews/prebuild_freeze.json','reviews/prequery_freeze.json','reviews/analysis_source_freeze.json'],verified='All original hashes rechecked; no post-outcome changes to construction or gates.'),
    dict(requirement='Verify actual construction and complete scoped experiment',evidence=['results/construction.json','reviews/preflight_verification.json','reviews/aux_verification.json','logs/jobs.json'],verified='2 datasets, 3 policies, 2 L, 128 preflight and 7952 main; 96960 independently scored outputs, 16160 original baseline rows, 384 original kernel checks.'),
    dict(requirement='Protect data, defaults and preserve old work',evidence=['reviews/protected_before.json','reviews/large_asset_stat.json','source_before','root_after'],verified='Small inputs/source/models SHA unchanged; fit prefix SHA stable; large graph size/mtime unchanged with inherited identity. All online P/labels match originals; GT10 defaults unchanged.'),
    dict(requirement='Respect single-thread query and finite budget',evidence=['logs/jobs.json','results/cost.json'],verified='6 builds, 194304 NSG/193920 HNSW; CPU15/process and numerical-library 1 thread; no retries, no new GT, compiler, dependencies or wall/QPS.'),
    dict(requirement='Do not run conditional performance phase after failed gate',evidence=['results/gate.json','results/cost.json','state.json'],verified='All four gates fail; no conditional wall is required or pending.'),
    dict(requirement='Synchronize architecture, results, target, history and close handoff',evidence=['root_after','report.md','decision.md'],verified='Root documents and history87 synchronized, local links and scoped whitespace checked; original before snapshots preserved.'),
    dict(requirement='Leave no live or queued native work',evidence=['logs/jobs.json','state.json','decision.json'],verified='All ten launched native handles completed with exit0 and original PIDs no longer refer to this experiment; no successor queue.')
],recomputed_comparisons=checks,protected_small_files=len(read(O/'reviews/protected_before.json')),large_asset_check='stat + inherited identity, not new full hash',local_links_checked=links,missing_links=[],whitespace_checks='PASS',live_native_pids=live,scientific_superiority_claimed=False,objective_stop_alternative_complete=True,pending_required_work=[],new_QPS_points=0)
dump(O/'reviews/completion_audit.json',audit)
freeze(O/'final_seal.json',[p for p in O.rglob('*') if p.is_file() and p.name!='final_seal.json' and '__pycache__' not in p.parts])
print(json.dumps(dict(status=audit['status'],comparisons=len(checks),links=links,protected_files=audit['protected_small_files'],live_native_pids=live,branch_status=decision['status']),ensure_ascii=False))
