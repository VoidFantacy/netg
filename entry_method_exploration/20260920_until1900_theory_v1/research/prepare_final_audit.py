from pathlib import Path
import json,hashlib,shutil,time,re,urllib.parse,sys,ast,subprocess
ROOT=Path('/data/netg/ACSG');TB=Path(__file__).resolve().parents[1];OLD=Path(json.loads((TB/'config.locked.json').read_text())['previous_phase'])
OUT=TB/sys.argv[1];assert not OUT.exists();OUT.mkdir(parents=True)
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(16<<20),b''):h.update(b)
    return h.hexdigest()
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
refs={};origins={};stats={};jobs=[];stages=[]
def add(x,origin):
    if isinstance(x,list):
        for v in x:add(v,origin)
    elif isinstance(x,dict):
        if 'path' in x and 'sha256' in x:
            p=x['path'];assert p not in refs or refs[p]['sha256']==x['sha256'],(p,origin,'hash conflict')
            refs[p]=dict(path=p,sha256=x['sha256']);origins.setdefault(p,[]).append(str(origin))
        for v in x.values():
            if isinstance(v,(dict,list)):add(v,origin)
def addfile(p):add(read(p),p)
addfile(TB/'reviews/config_identity.json');addfile(TB/'reviews/previous_phase_complete.json')
for st in sorted((TB/'stages').iterdir()):
    cc=read(st/'complete.json');assert cc['status']=='COMPLETE';add(cc,st/'complete.json');stages.append(dict(stage=st.name,complete=ident(st/'complete.json'),NSG_calls=cc['NSG_calls'],ANN_calls=cc['ANN_calls'],decision=cc['decision']))
    for n in ['protected_before.json','input_sources.json','search_source_freeze.json','source_freeze.json','numeric_verification.json','model_identity_gate.json','closeout_identity.json']:
        p=st/'reviews'/n
        if p.exists():addfile(p)
    c=read(st/'config.locked.json');ds=c['datasets'];ds=ds.values() if isinstance(ds,dict) else ds
    for d in ds:
        if 'index_stat' in d:stats[d['index']]=d['index_stat']
    for x in c.get('large_files',[]):stats[x['path']]=dict(bytes=x['bytes'],mtime_ns=x['mtime_ns'])
    jf=st/'reviews/jobs.json';rows=read(jf) if jf.exists() else [read(st/'reviews/job.json')]
    for j in rows:jobs.append(dict(stage=st.name,**j))
for n in ['source_branch_completion.json','statistical_review_complete.json','routing_review_complete.json','representation_scope_complete.json']:
    p=TB/'reviews'/n;add(read(p)['files'],p)
for n in ['source_support_v1','objective_quantization_v1','score_anchor_geometry_v1']:
    p=TB/'research'/n/'complete.json';addfile(p);cfg=TB/'research'/n/'config.locked.json';addfile(cfg)
addfile(TB/'reviews/comparison_scope.json')
plot=TB/'research/net_gain_figure_v1';addfile(plot/'complete.json');pc=read(plot/'complete.json');assert pc['status']=='COMPLETE' and not (Path('/proc')/str(pc['pid'])).exists()
router=TB/'research/router_work_identity_v1';addfile(router/'complete.json');addfile(router/'completion_audit.json')
for j in read(router/'jobs.json'):jobs.append(dict(stage='router_work_identity',**j))
xor=TB/'research/xor_entry_expressivity_v1';addfile(xor/'complete.json');addfile(xor/'completion_audit.json')
for j in read(xor/'jobs.json'):jobs.append(dict(stage='synthetic_xor_entry',**j))
syn=TB/'research/query_branch_stability_v1';addfile(syn/'config.locked.json')
for j in read(syn/'jobs.json'):
    jobs.append(dict(stage='synthetic_query_branch',finished_unix=j['started_unix']+j['seconds'],finish_derived_from_recorded_elapsed=True,**j))
sc=read(syn/'complete.json');assert sha(syn/'verify.cpp')==sc['source_sha256'] and sha(syn/'result.json')==sc['result_sha256']
# Old phase was sealed independently. Recheck its actual identities; do not edit it.
oldident=read(OLD/'reviews/identity_verification.json');add(oldident['files'],OLD/'reviews/identity_verification.json')
for p,v in oldident['NSG_stat_checks'].items():stats[p]=v
for p,x in refs.items():assert sha(p)==x['sha256'],('identity mismatch',p)
for p,v in stats.items():s=Path(p).stat();assert s.st_size==v['bytes'] and s.st_mtime_ns==v['mtime_ns'],('stat mismatch',p)
for r in [TB,OLD]:
    for x in read(r/'config.locked.json')['source_before']:assert sha(x['snapshot'])==x['sha256'],x['snapshot']
assert sha(ROOT/'AGENTS.md')==read(TB/'config.locked.json')['source_before'][0]['sha256']
for j in jobs:
    assert j['exit_code']==0 and j['seconds']>=0 and j['finished_unix']>=j['started_unix']
    pid=Path('/proc')/str(j['pid'])/'cmdline';assert not pid.exists() or str(TB).encode() not in pid.read_bytes(),('live owned process',j['pid'])
query_jobs=sorted([j for j in jobs if j['kind'] in ['trace','fit_trace','smoke','main','routing']],key=lambda j:j['started_unix'])
assert all(a['finished_unix']<=b['started_unix'] for a,b in zip(query_jobs,query_jobs[1:]))
state=read(TB/'state.json');assert state['completed_NSG_calls']==sum(s['NSG_calls'] for s in stages)==328448 and state['active_stage_reserved_NSG_calls']==0
assert sum(s['ANN_calls'] for s in stages)+read(router/'complete.json')['ANN_calls']==98560
assert sc['synthetic_calls']==4 and read(xor/'complete.json')['synthetic_calls']==8
assert state['synthetic_calls']==sc['synthetic_calls']+read(xor/'complete.json')['synthetic_calls']==12
assert 328448+read(TB/'config.locked.json')['previous_phase_real_NSG_calls']==3125504<4000000
cost=dict(status='PASS',measured_unix=time.time(),scope='19:00 extension; old phase separately identified',real_NSG_calls=328448,synthetic_calls=12,synthetic_graphs=2,ANN_calls=98560,combined_real_NSG_calls=3125504,combined_synthetic_calls=18,combined_ANN_calls='not aggregated; 98560 is extension only',ordinary_router_graph_builds=0,hybrid_router_copies=4,before_serialization_copies=4,new_GT=0,new_bottom_graphs=0,new_gradient_or_profile_training=0,new_formal_QPS=False,heldout_payload_access=False,new_graph_derived_labels=True,new_offline_H_optimization=True,old_model_score_residual_calculations=True,
    stages=stages,E112=read(TB/'stages/e112_one_hop_hub_design/reviews/cost_ledger.json'),E113=read(TB/'stages/e113_comparison_support/reviews/cost_ledger.json'),E114=dict(native_seconds=read(TB/'stages/e114_terminal_peaks/reviews/numeric_verification.json')['seconds'],process_seconds=read(TB/'stages/e114_terminal_peaks/reviews/job.json')['seconds']),E115=read(TB/'stages/e115_score_topology_factorial/reviews/diagnostic_complete.json'),router_work=read(router/'results/complete.json'),job_records=jobs,
    additional_analyses=[dict(name=n,seconds=read(TB/'research'/n/'complete.json')['seconds']) for n in ['source_support_v1','objective_quantization_v1','score_anchor_geometry_v1']],
    old_phase_actual_directory_bytes=sum(p.stat().st_size for p in OLD.rglob('*') if p.is_file()),old_phase_audit_bytes_scope='The old audit measured before writing its final identity/document/receipt files; actual directory bytes are measured separately here. Its sealed files remain SHA-identical.',
    XOR=read(xor/'result.json'),geometry_arithmetic=read(TB/'reviews/routing_geometry_exact_arithmetic.json'),
    net_gain_plot=read(plot/'complete.json'),
    max_native_rss_GiB=max(read(TB/'stages/e112_one_hop_hub_design/reviews/cost_ledger.json')['max_rss_gib'],read(TB/'stages/e113_comparison_support/reviews/cost_ledger.json')['max_rss_gib'],read(TB/'stages/e115_score_topology_factorial/reviews/completion_audit.json')['maxrss_GiB']))
dump(OUT/'cost_ledger.json',cost)
dump(OUT/'identity.json',dict(status='PASS',files=[dict(**v,origins=origins[p]) for p,v in sorted(refs.items())],large_input_stats=stats,old_phase_identity_verified=True,source_before_snapshots_verified=True))
docs=[ROOT/n for n in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']]+[TB/'report.md']+sorted((TB/'research').glob('*.md'))+sorted((TB/'research').glob('*/report.md'))+sorted((TB/'stages').glob('*/report.md'))+[ROOT/'experiment_history'/n for n in ['108_one_hop_hub_design.md','109_source_support_and_query_branches.md','110_actual_comparison_support.md','111_terminal_local_optima.md','112_statistical_objective_review.md','113_score_topology_factorial.md','114_router_work_and_theory_scope.md','115_routing_representation_theory.md']]
if (ROOT/'experiment_history/116_theory_synthesis_1900.md').exists():docs.append(ROOT/'experiment_history/116_theory_synthesis_1900.md')
docs.append(TB/'reviews/theory_claim_review.md')
links=[]
for p in docs:
    assert p.exists(),p
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',p.read_text()):
        target=target.strip('<> ')
        if urllib.parse.urlsplit(target).scheme or target.startswith('#'):continue
        q=(p.parent/urllib.parse.unquote(target.split('#')[0])).resolve();assert q.exists() or q in {OUT/'audit.json',OUT/'documents.json'},(p,target);links.append(dict(source=str(p),target=str(q)))
dump(OUT/'documents.json',dict(status='PASS',documents=[ident(p) for p in docs],links=links))
for p in (TB/'research').rglob('*.py'):ast.parse(p.read_text())
dirty=subprocess.check_output(['git','status','--porcelain=v1','-uno'],cwd=ROOT,text=True);(OUT/'tracked_dirty_status.txt').write_text(dirty)
used=sum(p.stat().st_size for r in [TB,OLD] for p in r.rglob('*') if p.is_file());free=shutil.disk_usage(TB).free;assert used<2**31 and free>=4*2**30
deadline_reached=time.time()>=read(TB/'config.locked.json')['deadline_unix']
audit=dict(status='PASS_FINAL_AUDIT' if deadline_reached and OUT.name=='final_audit' else 'PASS_PREFLIGHT',measured_unix=time.time(),final_deadline_complete=deadline_reached and OUT.name=='final_audit',unique_SHA_files=len(refs),large_stat_files=len(stats),owned_jobs_closed=len(jobs),serial_query_jobs=len(query_jobs),local_links=len(links),combined_logical_bytes_at_measurement=used,free_GiB=free/2**30,tracked_dirty_paths=len(dirty.splitlines()),NSG_calls=328448,ANN_calls=98560,combined_NSG_calls=3125504,default_changed=False,production_changed=False,cost=ident(OUT/'cost_ledger.json'),identity=ident(OUT/'identity.json'),documents=ident(OUT/'documents.json'),audit_source=ident(__file__))
dump(OUT/'audit.json',audit);print(json.dumps(audit,indent=2))
