from control import *
import re

start=time.monotonic()
resources()
for path in ['prequery_freeze.json','old_directories.json','native_dependencies.json']:
    check(O/'reviews'/path)
old=read(O/'reviews/old_directories.json')['files']
assert {f['path'] for f in old}=={str(f) for f in files(E)+files(D)}
jobs=read(O/'logs/jobs.json')
assert len(jobs)==2 and all(j['status']=='COMPLETE' for j in jobs)
assert sum(j['actual'] for j in jobs)==38592
assert sum(j['reserved'] for j in jobs)<=40000
assert all(j['native']['actual_threads']==1 for j in jobs)
verification=read(O/'reviews/independent_verification.json');assert verification['status']=='PASS'
decision=read(O/'results/diagnosis.json');assert not decision['all_four_stable']
assert decision['optimizer_updates']==0 and decision['builds']==36
assert len(list((O/'models').glob('*/*/*/graph.hnsw')))==36
assert len(list((O/'models').glob('*/*/*/W.f32')))==36
assert len(list((O/'results').glob('*/*/*.npz')))==36
assert read(O/'reviews/visual_review.json')['status']=='PASS'
docs=[R/p for p in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md',
                    'experiment_history/README.md','experiment_history/28_fixed_profile_batch_diagnosis.md']]+list(O.glob('*.md'))
broken=[];links=0
for p in docs:
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if '://' in target or target.startswith('#'): continue
        target=target.split('#')[0]
        resolved=(p.parent/target).resolve()
        if not resolved.exists() and resolved!=O/'reviews/final_audit.json':broken.append((str(p),target))
        links+=1
assert not broken,broken
status='COMPLETE_FIXED_PROFILE_BATCH_DIAGNOSIS_STOP_BUDGET_EXPANSION'
dump(O/'state.json',dict(status=status,completed_at=time.time(),NSG_calls=38592,HNSW_calls=38016,
     builds=36,optimizer_updates=0,new_GT=0,new_validation_heldout_raw_access=False,
     dataset_stable=decision['dataset_stable'],default_changed=False,queued_jobs=0,
     next_cached_payoff_attribution='DESIGNED_UNRUN'))
audit=dict(status='PASS',old_files_preserved=len(old),E37_files=sum(str(E) in f['path'] for f in old),
     E38_files=sum(str(D) in f['path'] for f in old),native_dependencies=len(read(O/'reviews/native_dependencies.json')['files']),
     local_links=links,NSG_calls=38592,HNSW_calls=38016,builds=36,optimizer_updates=0,
     independent_verification=verification,artifact_bytes=sum(p.stat().st_size for p in files(O)),
     disk_free_bytes=shutil.disk_usage(O).free,seconds=time.monotonic()-start)
dump(O/'reviews/final_audit.json',audit)
freeze(O/'reviews/final_artifact_freeze.json',files(O)+docs)
print(json.dumps(audit,ensure_ascii=False,indent=2))
