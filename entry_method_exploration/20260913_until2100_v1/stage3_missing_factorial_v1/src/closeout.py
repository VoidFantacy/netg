from shared import *
import csv,re,ast
threads();resources();check(O/'reviews/models_before_queries.json')
assert read(O/'reviews/verification.json')['status']=='PASS'
for prev in [C/'stage1_support_v1',E61]:check(prev/'reviews/final_artifact_freeze.json')
check(E61/'reviews/report_text_correction_v2.json')
assert sha(O/'bin/environment.so')==sha(E48/'bin/environment.so')
assert sha(O/'src/native_factorial.py')==sha(E48/'src/native_factorial.py')
for ds in DS:assert read(O/'results'/ds/'query_complete.json')['actual_threads']==1
assert len(read(O/'logs/jobs.json'))==2 and all(x['status']=='COMPLETE' for x in read(O/'logs/jobs.json'))
historical=[]
for row in read(D/'20260912_until2000_v1/closeout/final_artifact_freeze.json')['files']:
    orig=Path(row['path']);p=orig
    if orig.parent==R and orig.name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:p=C/'source_before'/orig.name
    if orig==R/'experiment_history/README.md':p=C/'source_before/experiment_history_README.md'
    assert sha(p)==row['sha256'],str(p)
    historical.append(dict(frozen_path=str(orig),verified_path=str(p),sha256=row['sha256']))
dump(O/'reviews/yesterday_protection.json',dict(status='PASS',files=historical,mutable_live_docs='Current root documents and history README legally updated; original snapshots retained'))
roots=['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']
for name in roots:
    dest=O/'root_after'/name;dest.parent.mkdir(exist_ok=True);shutil.copy2(R/name,dest)
for name in ['README.md','49_fixed_action_support.md','50_missing_target_profiles.md','51_missing_profile_factorial.md']:
    dest=O/'root_after/experiment_history'/name;dest.parent.mkdir(exist_ok=True);shutil.copy2(R/'experiment_history'/name,dest)
links=0;docs=[R/n for n in roots]+[R/'experiment_history'/n for n in ['README.md','49_fixed_action_support.md','50_missing_target_profiles.md','51_missing_profile_factorial.md']]+[O/'report.md',O/'protocol.md',C/'next_stage_design.md',E61/'report_v2.md']
for p in docs:
    for href in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        href=href.split('#')[0]
        if not href or re.match(r'\w+://',href):continue
        target=p.parent/href;assert target.exists(),(str(p),href);links+=1
for p in (O/'src').glob('*.py'):ast.parse(p.read_text())
points=list(csv.DictReader((O/'results/points.csv').open()));candidates=[]
for ds in DS:
    config=read(O/'inputs'/ds/'config.json')
    for name in LABELS:
        pts=[x for x in points if x['dataset']==ds and x['model']==name]
        candidates.append(dict(dataset=ds,name='E62_'+name,kind='baseline' if name=='C' else 'new_method',recommended=name=='C',passed_new_cal_gate=False,
            W=identity(O/'models'/ds/name/'W.f32'),graph=identity(O/'results'/ds/name/'graph.hnsw'),mapping=identity(config['hub_ids']),
            load_contract='Load frozen physical graph; score vectors and ordered topology as serialized; do not rebuild from W' if name in ['S','T'] else 'Frozen ordinary HNSW graph',
            historical_development_points=pts,source_protocol=identity(O/'protocol.md')))
    candidates.append(dict(dataset=ds,name='E61_sham',kind='diagnostic_control',recommended=False,passed_new_cal_gate=False,
        W=identity(E61/'models'/ds/'sham_lambda05/W.f32'),graph=identity(E61/'results'/ds/'sham_lambda05/graph.hnsw'),mapping=identity(config['hub_ids']),load_contract='Ordinary frozen graph; target-identity control, not selection candidate'))
dump(C/'candidate_inventory.json',dict(status='FROZEN_ENDPOINT_INVENTORY_NOT_FINAL_SELECTION',candidates=candidates,final_selection='Use a new cal-only final protocol to freeze best_all and best_new; do not read E34 responses for selection'))
dump(C/'next_input_inventory.json',dict(status='EXISTING_HISTORICAL_DEVELOPMENT_SOURCES',datasets=[dict(dataset=ds,
    config=identity(O/'inputs'/ds/'config.json'),E61_input_audit=identity(E61/'reviews/input_audit.json'),baseline_output=identity(O/'results'/ds/'C/raw.npz'),baseline_model=identity(O/'models'/ds/'C/W.f32'),
    all_GT10_assignment_source=identity(E61/'reviews/profile_verification.json'),builder_reference=str(E61/'src/build.py'),
    roles='router_train local10000:30000 fit; 0:1024 cal;1024:2048 audit; all exposed. Do not compare numeric row IDs across source namespaces') for ds in DS],new_GT_required=False,final_validation_training_allowed=False))
dump(O/'state.json',dict(status='COMPLETE_MISSING_FACTORIAL_NO_CAL_GO',native_pids=[],formal_QPS_points=0,selected={ds:'C' for ds in DS},next='End current session safely; successor owns new independent protocol'))
dump(O/'reviews/closeout.json',dict(status='PASS',epoch=time.time(),E60_E61_frozen_files_unchanged=True,yesterday_files_checked=len(historical),links_checked=links,graph_visual_check='factorial_and_failures.png',native_jobs_all_complete=True,native_pids=[],execution_note=str(O/'reviews/execution_note.md'),free_GiB=shutil.disk_usage('/data').free/(1<<30)))
files=[p for p in O.rglob('*') if p.is_file() and p!=O/'reviews/final_artifact_freeze.json']
dump(O/'reviews/final_artifact_freeze.json',dict(status='COMPLETE_E62_FROZEN',epoch=time.time(),files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)]))
print('E62_CLOSEOUT_PASS',len(files),'files;',links,'links;',len(historical),'yesterday files',flush=True)
