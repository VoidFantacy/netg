from common import *
import datetime
v=read(R/'analysis/verdict.json');assert v['formal_points']==256 and v['formal_batches']==768
assert read(R/'reviews/postcheck.json')['status'].startswith('PASS_')
assert read(R/'state.json')['status']=='COMPLETED_EQUIVALENT_OPTIMIZATION_STABILITY_NO_DEFAULT_CHANGE'
frozen=read(R/'formal_freeze.json')['files']
for a in frozen:assert sha(a['path'])==a['sha256'],a['path']
assets=read(R/'inherited_assets.json')
for a in assets:
    p=Path(a['path']);s=p.stat();assert s.st_size==a['bytes'] and s.st_mtime_ns==a['mtime_ns'],str(p)
    if 'sha256' in a:assert sha(p)==a['sha256'],str(p)
prev=R.parent/'20261029_adaptive_completion_gate_v1';bridges=[];direct=0
for a in read(prev/'delivery_manifest.json')['files']:
    p=Path(a['path'])
    if p.exists() and p.stat().st_size==a['bytes'] and sha(p)==a['sha256']:direct+=1;continue
    rel=p.relative_to(REPO)
    candidates=[R/'source_before'/rel,REPO/'experiment_history/_maintenance/20261029_residual_positive_evidence_sync_v1/source_before'/rel]
    if rel==Path('experiment_history/README.md'):candidates.insert(0,R/'source_before/experiment_history_README.md')
    m=next((x for x in candidates if x.exists() and sha(x)==a['sha256']),None)
    assert m is not None,str(p)
    bridges.append(dict(old=a,snapshot=str(m),current=ident(p)))
dump(R/'reviews/E193_seal_after.json',dict(status='PASS_OLD_SCIENCE_AND_SNAPSHOT_BRIDGES',direct_matches=direct,root_bridges=bridges))
dump(R/'reviews/formal_freeze_after.json',dict(status='PASS_ALL_FORMAL_FROZEN_FILES_UNCHANGED',count=len(frozen),inherited_asset_count=len(assets)))
paths=[REPO/x for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','LOCAL_CODEX_START.md','experiment_history/README.md','experiment_history/194_residual_optimization_stability_v1.md']]
paths += [p for p in R.rglob('*') if p.is_file() and '__pycache__' not in str(p) and p.name not in ['delivery_manifest.json','delivery_validation.json']]
paths += [p for p in (R/'storage').resolve().rglob('*') if p.is_file() and '__pycache__' not in str(p)]
unique={str(p.resolve()):p.resolve() for p in paths};files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(unique.values())]
dump(R/'delivery_manifest.json',dict(status='SEALED_E194_LOCAL_DELIVERY',files=files))
receipt=dict(status='PASS_E194_LOCAL_DELIVERY',completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),formal_points=256,formal_batches=768,qualification_points=20,files=len(files),bytes=sum(x['bytes'] for x in files),default_changed=False,old_scientific_files_unchanged=True,formal_freeze_files_unchanged=True,new_PDF=False)
dump(R/'delivery_validation.json',receipt);print(json.dumps(receipt),flush=True)
