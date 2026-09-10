"""Run only after timing: rehash upstream/frozen assets and independently audit selection."""
import time
from pathlib import Path
from common import DATASETS, ROOT, RUN, check_lock, dump, identity, read, sha

lock=check_lock();started=time.monotonic()
jobs=read(RUN/'reviews/search_jobs.json')
assert all(j['status']=='COMPLETE' for j in jobs)
assert sum(j['reserved_calls'] for j in jobs)<=lock['total_real_call_cap']
assert sum(j['actual_calls'] for j in jobs)==543296 if read(RUN/'results/summary.json')['completed_validation'] else True
assert all(j['max_observed_process_threads']==1 for j in jobs)
allowed_docs={str(ROOT/p) for p in ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']}
verified=[]
for item in read(RUN/'reviews/protected_before.json'):
    now=identity(item['path'])
    if item['path'] in allowed_docs:
        snap=RUN/'source_before'/Path(item['path']).relative_to(ROOT)
        assert sha(snap)==item['sha256'],'original document snapshot lost'
        now['role']='authorized main-document update; original snapshot checked'
    else:
        assert now['sha256']==item['sha256'] and now['bytes']==item['bytes'],item['path']
        now['role']='unchanged upstream source or artifact'
    verified.append(now)
frozen=[]
for name in ['frozen_before_cal.json','frozen_before_audit.json','frozen_before_validation.json']:
    file=RUN/'models'/name
    if not file.exists():continue
    for item in read(file)['files']:
        assert sha(item['path'])==item['sha256'],item['path']
    frozen.append({'manifest':str(file),'files_checked':len(read(file)['files']),'status':'PASS'})
choices=[]
for ds in DATASETS:
    selection=read(RUN/'models'/ds/'selection.json')
    table=read(RUN/'diagnostics'/ds/'cal/results.json')['methods']
    hnsw=[x for x in table if not x['configuration']['exact']]
    candidates=[]
    for family in ['gt10_hard','gt1_soft','gt10_soft']:
        group=[x for x in hnsw if x['family']==family]
        group.sort(key=lambda x:(-x['total_hits'],x['mean_graph_ndc'],x['configuration']['temperature'] or 0))
        assert group[0]['configuration']['model_name']==selection['selected_families'][family]['name']
        candidates.append(group[0])
    ranks={'gt10_hard':0,'gt1_soft':1,'gt10_soft':2}
    candidates.sort(key=lambda x:(-x['total_hits'],x['mean_graph_ndc'],ranks[x['family']],x['configuration']['temperature'] or 0))
    assert candidates[0]['configuration']['model_name']==selection['primary']['name']
    baseline=next(x for x in hnsw if x['family']=='gt1_hard')
    assert (candidates[0]['total_hits']>baseline['total_hits'])==selection['cal_gate_pass']
    choices.append({'dataset':ds,'primary':selection['primary']['name'],'rule_recomputed_from_raw_cal':True})
dump(RUN/'reviews/immutable_integrity.json',{'status':'PASS','seconds':time.monotonic()-started,
     'upstream':verified,'frozen_manifests':frozen,'selection_checks':choices,
     'physical_real_calls':sum(j['actual_calls'] for j in jobs),'heldout_opened':False,
     'scope':'all bound upstream base/graphs/train inputs/source/libs and all frozen profiles/selection/binary; never opens held-out'})
print('IMMUTABLE_AND_SELECTION_AUDIT_PASS',len(verified),'upstream records',flush=True)
