from shared import *
threads();resources();started=time.monotonic();check(E61/'reviews/final_artifact_freeze.json')
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:
    dest=O/'source_before'/name;dest.parent.mkdir(exist_ok=True);shutil.copy2(R/name,dest)
shutil.copy2(R/'experiment_history/README.md',O/'source_before/history_README.md')
cfg=dict(models=LABELS,sources=SOURCES,threads=1,CPU=15,total_NSG_cap=90000,per_dataset_NSG_cap=45000,per_dataset_HNSW=88704,builds=4,installations=2,latest_launch=1789264200,query_stop=1789264800,
    selection='cal S/T net>0; zero-hit count<=C; totalNDC<=C*1.01; order by net desc, NDC asc, S first; otherwise C',audit_selectable=False,final_validation_access=False)
dump(O/'config.locked.json',cfg)
deps=[O/'protocol.md',O/'config.locked.json',E61/'reviews/final_artifact_freeze.json',O/'bin/environment.so']+list((O/'src').glob('*.py'))
for ds in DS:
    c=read(E61/'inputs'/ds/'config.json');c.update(native_call_cap=45000,native_hnsw_cap=89000)
    dump(O/'inputs'/ds/'config.json',c)
    shutil.copy2(E61/'inputs'/ds/'baseline.npz',O/'inputs'/ds/'baseline.npz')
    for model in LABELS:
        wname,tname=SOURCES[model];folder=O/'models'/ds/model;folder.mkdir(parents=True)
        shutil.copy2(E61/'models'/ds/wname/'W.f32',folder/'W.f32')
        shutil.copy2(E61/'results'/ds/tname/'topology.npz',folder/'topology.npz')
    deps += list((O/'inputs'/ds).glob('*'))+list((O/'models'/ds).glob('*/*'))
    deps += [Path(c[k]) for k in ['queries_file','gt_file','row_ids','parity_rows','hub_ids']]
dump(O/'reviews/models_before_queries.json',dict(status='FROZEN_BEFORE_E62_QUERY',files=[identity(p) for p in sorted(set(deps))]))
dump(O/'reviews/input_audit.json',dict(status='REUSES_VERIFIED_E61_INPUTS',source=identity(E61/'reviews/input_audit.json'),query_roles='same source router_train fit10000:30000 cal0:1024 audit1024:2048, historical exposure',no_E34=True,prepare_seconds=time.monotonic()-started,available_GiB=shutil.disk_usage('/data').free/(1<<30)))
print('E62_FROZEN',time.monotonic()-started,flush=True)
