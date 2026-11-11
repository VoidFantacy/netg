from common import *
import re
assert read(R/'reviews/formal_complete.json')['status']=='PASS_FROZEN_FOUR_WINDOW_MATRIX'
assert read(R/'analysis/analysis_receipt.json')['points']==1480
assert read(R/'analysis/stdlib_audit.json')['counts']['rounds']==4440
freeze=read(R/'formal_freeze.json')
for ref in freeze['sources']+freeze['configs']:assert sha(ref['path'])==ref['sha256'],ref['path']
lf=read(R/'labels_freeze.json');assert sha(R/'protocol.md')==lf['protocol_sha256'] and sha(R/'storage/labels_benchmark')==lf['binary_sha256']
for ref in lf['configs']:assert sha(ref['path'])==ref['sha256'],ref['path']
lb=read(R/'reviews/build_labels.json')
for ref in lb['sources']:
    path=R/'src/labels_frozen.cpp' if Path(ref['path']).name=='benchmark.cpp' else Path(ref['path'])
    assert sha(path)==ref['sha256'],str(path)
for ref in read(R/'training_freeze.json')['sources']:assert sha(ref['path'])==ref['sha256'],ref['path']
inference=[json.loads(p.read_text().splitlines()[-1]) for p in (R/'reviews').glob('*.inference.log')]
assert len(inference)==8 and all(x['status']=='PASS_NATIVE_NUMPY_ALL_LABEL_PREDICTIONS' for x in inference)
prior=read(R/'state.json')['source_before'];bridges=[]
for rel,h in prior.items():
    before=R/'source_before'/rel
    assert before.is_file() and sha(before)==h,(rel,str(before))
    bridges.append(dict(path=str(REPO/rel),before_snapshot=str(before),before_sha256=h,after_sha256=sha(REPO/rel)))
roots=['summary.md','spec.md','s-target.md','s-experiment.md','LOCAL_CODEX_START.md','experiment_history/README.md','experiment_history/198_conditional_residual_policy_v1.md']
links=[];preexisting_missing=[]
for p in [R/'report_zh.md',R/'method_zh.md',R/'findings_zh.md']+[REPO/x for x in roots]:
    assert p.is_file(),str(p)
    previous=R/'source_before'/p.relative_to(REPO) if p.is_relative_to(REPO) else None
    old_targets=set(re.findall(r'\]\(([^)]+)\)',previous.read_text())) if previous and previous.exists() else set()
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if '://' in target or target.startswith('#'):continue
        target=target.split('#')[0]
        if not target:continue
        q=(p.parent/target).resolve()
        if q==R/'delivery_validation.json':continue
        if not q.exists() and target in old_targets:
            preexisting_missing.append([str(p),target]);continue
        assert q.exists(),(str(p),target)
        links.append([str(p),target])
budget();v=os.statvfs('/data');actual_free=v.f_bfree*v.f_frsize
states=read(R/'state.json');states.update(status='PASS_E198_LOCAL_DELIVERY',completed=['8 state labels and models','qualification and complete wall calibration','1480 formal points and 4440 T1 batches','independent inference merge policy and stdlib checks','report method explanation and root document synchronization'],pending=[],default_changed=False,new_PDF=False)
dump(R/'state.json',states)
live=read(R/'live_process.json');live.update(active=False,status='COMPLETED_DO_NOT_RESUME_BY_PID');dump(R/'live_process.json',live)
required=[]
for p in sorted(R.rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts and p.name not in ['delivery_validation.json','delivery_manifest.json']:
        required.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)))
dump(R/'delivery_manifest.json',dict(status='FROZEN_LOCAL_DELIVERY_FILES',files=required,root_documents=[dict(path=str(REPO/x),sha256=sha(REPO/x)) for x in roots]))
rec=dict(status='PASS_E198_LOCAL_DELIVERY',points=1480,batches=4440,new_policy_methods=7,default_changed=False,new_PDF=False,
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
    report=str(R/'report_zh.md'),method=str(R/'method_zh.md'),manifest_sha256=sha(R/'delivery_manifest.json'),
    source_before_bridges=bridges,local_link_checks=len(links),preexisting_missing_links=preexisting_missing,persistent_new_bytes=sum(x['bytes'] for x in required),actual_data_free_bytes=actual_free,
    temporary_RAM_required_for_existing_results=False,old_scientific_files_unchanged=read(R/'analysis/stdlib_audit.json')['historical_frozen_files_unchanged'],
    evidence_scope='COCO/WebVid, true K1/K100, exposed A/B, same graph and metric; finite grids and descriptive multiple comparisons',
    independent_audit='same operator, distinct native NumPy and stdlib implementations; no independent personnel replication')
rec.update(native_numpy_prediction_rows=sum(x['rows'] for x in inference),native_numpy_max_abs_error=max(x['max_absolute_error'] for x in inference),label_source_exact_snapshot_bridge=True)
dump(R/'delivery_validation.json',rec);print(json.dumps({k:v for k,v in rec.items() if k!='source_before_bridges'}),flush=True)
