"""Read-only session6 handoff check. No NumPy, ANN, training, or final-query input."""
from pathlib import Path
import hashlib,json,shutil,time,os,re
C=Path(__file__).resolve().parents[1];R=C.parents[1]
STAGES=['stage1_support_v1','stage2_missing_targets_v1','stage3_missing_factorial_v1','stage4_zero_hit_mass_v1','stage5_frozen_pool_aux_v1','stage6_development_wall_v1','stage7_multimode_index_v1','stage8_multimode_wall_v1','stage9_profile_ranking_diagnosis_v1','stage10_exact_triple_utility_v1','stage11_width_control_v1','stage12_width_wall_v1','stage13_distinct_hub_width_v1','stage14_compact_modes_v1','stage15_compact_wall_v1','stage16_preserved_levels_v1','stage17_child_support_diagnosis_v1','stage18_child_shrink_factorial_v1','stage19_child_mass_norm_v1']
def read(p):return json.loads(Path(p).read_text())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(8<<20),b''):h.update(chunk)
    return h.hexdigest()
count=0;states=[]
for stage in STAGES:
    for row in read(C/stage/'reviews/final_artifact_freeze.json')['files']:
        assert sha(row['path'])==row['sha256'],row['path'];count+=1
    jobs=read(C/stage/'logs/jobs.json') if (C/stage/'logs/jobs.json').exists() else [];assert not any(j['status']=='RUNNING' for j in jobs)
    complete=[j for j in jobs if j['status']=='COMPLETE'];expected=6 if stage.startswith('stage7_') else (0 if stage.startswith(('stage9_','stage17_')) else (4 if stage.startswith(('stage11_','stage13_','stage14_','stage16_','stage18_','stage19_')) else 2));assert len(complete)==expected
    states.append(dict(stage=stage,status=read(C/stage/'state.json')['status'],complete_jobs=expected,failed_jobs=len(jobs)-expected))
for row in read(C/'stage4_zero_hit_mass_v1/reviews/correction.json')['files']:
    assert sha(row['path'])==row['sha256'];count+=1
for row in read(C/'stage2_missing_targets_v1/reviews/report_text_correction_v2.json')['files']:
    assert sha(row['path'])==row['sha256'];count+=1
for candidate in read(C/'candidate_inventory_v6.json')['candidates']:
    for key in [k for k in ['W','graph','mapping','tie_ids','evaluator','development_configuration','protocol'] if k in candidate]:
        row=candidate[key];assert sha(row['path'])==row['sha256'];count+=1
# Yesterday's frozen root/index bytes belong to their saved historical snapshot.
old=R/'entry_method_exploration/20260912_until2000_v1/closeout/final_artifact_freeze.json'
mapped={R/name:C/'source_before'/name for name in ['summary.md','spec.md','s-target.md','s-experiment.md','AGENTS.md']}
mapped[R/'experiment_history/README.md']=C/'source_before'/'experiment_history_README.md'
for row in read(old)['files']:
    path=Path(row['path']);target=mapped.get(path,path)
    if path==R/'experiment_history/README.md' and not target.exists():
        # Campaign's original snapshot may preserve the source directory path instead.
        possibilities=[C/'source_before'/'history_README.md',C/'source_before'/'experiment_history/README.md']
        target=next((p for p in possibilities if p.exists()),target)
    assert sha(target)==row['sha256'],str(target);count+=1
for session in [2,3,4,5,6]:
    session_seal=C/f'reviews/session{session}_final_artifact_freeze.json'
    if session_seal.exists():
        for row in read(session_seal)['files']:
            assert sha(row['path'])==row['sha256'],row['path'];count+=1
active=[]
for f in Path('/proc').glob('[0-9]*/cmdline'):
    try:
        args=f.read_bytes().split(b'\0');pid=int(f.parent.name)
        if pid==os.getpid() or not args:continue
        exe=Path(args[0].decode(errors='replace')).name
        if exe in ['bash','sh','timeout']:continue
        decoded=[a.decode(errors='replace') for a in args if a]
        command=' '.join(decoded)
        if 'entry_method_exploration/' not in command:continue
        native=exe in ['evaluate','build_graph','build_levels'] and 'entry_method_exploration/' in decoded[0]
        scripts=[Path(a).name for a in decoded[1:3] if a.endswith('.py') and 'entry_method_exploration/' in a]
        workload=exe.startswith('python') and any(re.fullmatch(r'(run|train|deploy|build|build_modes|prepare|analyze|verify_modes)(?:_v[0-9]+)?\.py',s) for s in scripts)
        if native or workload:active.append(dict(pid=pid,command=command))
    except (OSError,ProcessLookupError):pass
assert not active,active
free=shutil.disk_usage('/data').free/(1<<30);assert free>=7
print(json.dumps(dict(status='PASS_SESSION6_READ_ONLY_RESUME',epoch=time.time(),checked_files=count,free_GiB=free,active_native_or_training=active,stages=states,
    campaign_state=read(C/'state.json'),next_design=str(C/'next_stage_design_session6.md'),next_action='Use a new independent version and prospective protocol. Never rerun completed stage1..19 runners.',
    data_roles='All fit/cal/audit/aux7952 are historical and exposed; E64 aux is selection training; E65/E67/E71/E74 are development walls; E69 exact triples have measured L128 NSG utility; E70/E72/E73 quality is historical auxiliary, E73 compact has byte-invariant full per-hub scores but changed graph; E75/E77/E78 main gates failed and controls excluded from automatic promotion; E76 used cached returns only; final E34/heldout were not opened in session6.'),ensure_ascii=False,indent=2))
