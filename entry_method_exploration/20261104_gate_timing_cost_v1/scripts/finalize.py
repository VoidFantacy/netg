from common import *
import re
assert read(R/'reviews/formal_complete.json')['points']==736
assert read(R/'analysis/analysis_receipt.json')['points']==736
assert read(R/'analysis/stdlib_audit.json')['counts']['rounds']==2208
assert read(R/'reviews/pdf_visual_review.json')['status']=='PASS_ACTUAL_PDF_VISUAL_REVIEW'
assert read(R/'reviews/pdf_render.json')['pdf_sha256']==sha(R/'E199_残差门控时机与精排成本_20261104.pdf')
freeze=read(R/'formal_freeze.json')
for ref in freeze['sources']+freeze['configs']:assert sha(ref['path'])==ref['sha256'],ref['path']
for ref in read(R/'gate_training_freeze.json')['sources']:assert sha(ref['path'])==ref['sha256'],ref['path']
af=read(R/'assets_freeze.json');assert sha(R/'protocol.md')==af['protocol_sha256']
for ref in af['train_sources']+af['inputs']+af['configs']+[af['label_binary']]:assert sha(ref['path'])==ref['sha256'],ref['path']
old=read(R.parent/'20261102_conditional_residual_policy_v1/delivery_manifest.json');root_previous={x['path']:x['sha256'] for x in old['root_documents']};bridges=[]
old_root=R.parent/'20261102_conditional_residual_policy_v1'
for ref in old['files']:assert sha(old_root/ref['path'])==ref['sha256'],ref['path']
dump(R/'reviews/e198_preservation.json',dict(status='PASS_E198_DELIVERED_FILES_UNCHANGED',files=len(old['files']),prior_manifest_sha256=sha(old_root/'delivery_manifest.json')))
for p in sorted((R/'source_before').rglob('*')):
    if not p.is_file():continue
    target=REPO/p.relative_to(R/'source_before');before=sha(p)
    if str(target) in root_previous:assert root_previous[str(target)]==before,(str(target),'prior E198 exact-root bridge')
    bridges.append(dict(path=str(target),before_snapshot=str(p),before_sha256=before,after_sha256=sha(target)))
roots=['summary.md','spec.md','s-target.md','s-experiment.md','LOCAL_CODEX_START.md','experiment_history/README.md','experiment_history/199_gate_timing_cost_v1.md'];links=[]
for p in [R/'report_zh.md',R/'findings_zh.md']+[REPO/x for x in roots]:
    assert p.is_file(),str(p)
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if '://' in target or target.startswith('#'):continue
        q=(p.parent/target.split('#')[0]).resolve()
        if q==R/'delivery_validation.json':continue
        assert q.exists(),(str(p),target)
        links.append([str(p),target])
budget();v=os.statvfs('/data');assert v.f_bfree*v.f_frsize>10*2**30
state=read(R/'state.json');state.update(status='PASS_E199_LOCAL_PDF_DELIVERY',completed=['frozen four multimodal assets and gates','736 formal points and 2208 complete T1 batches','native NumPy and stdlib audits','stage and rerank cost analysis','16 page PDF actual render and visual review','root documents and history synchronization'],pending=[],default_changed=False,PDF_created=True)
dump(R/'state.json',state)
for name in ['live_process.json','reviews/postprocess_active.json']:
    p=R/name
    if p.exists():x=read(p);x.update(active=False,status='COMPLETED_DO_NOT_RESUME_BY_PID');dump(p,x)
files=[]
for p in sorted(R.rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts and p.name not in ['delivery_manifest.json','delivery_validation.json']:
        files.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)))
dump(R/'delivery_manifest.json',dict(status='FROZEN_LOCAL_DELIVERY',files=files,root_documents=[dict(path=str(REPO/x),sha256=sha(REPO/x)) for x in roots]))
result=dict(status='PASS_E199_LOCAL_PDF_DELIVERY',points=736,batches=2208,datasets=DS,K=[1,100],primary_L=200,default_changed=False,PDF=str(R/'E199_残差门控时机与精排成本_20261104.pdf'),PDF_pages=16,
    PDF_sha256=sha(R/'E199_残差门控时机与精排成本_20261104.pdf'),manifest_sha256=sha(R/'delivery_manifest.json'),source_before_bridges=bridges,links_checked=len(links),
    persistent_bytes=sum(x['bytes'] for x in files),actual_free_data_bytes=v.f_bfree*v.f_frsize,all_evidence_persistent=True,old_scientific_files_unchanged=read(R/'analysis/stdlib_audit.json')['historical_frozen_files_unchanged'],
    evidence_limits='Exposed A/B, fixed Q8 single-seed384 and L200 gate study, same graph/router, shared development, sparse K1. Profile is separate diagnostics; full normal batch wall governs QPS.',
    e198_delivered_files_unchanged=len(old['files']),independent_audit='same operator, distinct native NumPy stdlib implementations',head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip())
dump(R/'delivery_validation.json',result);print(json.dumps({k:v for k,v in result.items() if k!='source_before_bridges'},ensure_ascii=False),flush=True)
