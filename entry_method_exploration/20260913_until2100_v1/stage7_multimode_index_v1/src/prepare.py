from common import *
threads();resources()
assert not (O/'reviews/prebuild_freeze.json').exists()
deps=set();configs={}
for ds in DS:
    c=read(C/'stage4_zero_hit_mass_v1/inputs'/ds/'config.json');configs[ds]=c
    folder=O/'inputs'/ds;folder.mkdir()
    dump(folder/'construction.json',c)
    for key in ['P','raw_hubs','queries_file','gt_file','row_ids','hub_ids']:
        deps.add(Path(c[key]))
    aux=read(C/'stage5_frozen_pool_aux_v1/inputs'/ds/'config.json')
    for key in ['queries_file','gt_file','row_ids']:deps.add(Path(aux[key]))
    deps.add(Path(aux['methods'][0]['graph_file']))
    dump(folder/'aux_source.json',aux)
    rows=np.fromfile(c['row_ids'],np.int64);assert np.array_equal(rows[:20000],np.arange(10000,30000))
    assert np.array_equal(np.fromfile(aux['row_ids'],np.int64),np.arange(2048,10000))
dump(O/'config.locked.json',dict(physical_profiles_per_hub=3,query_slots=7,k=3,iterations=20,parent_mass_min=8,parent_ESS_min=16,child_mass_min=2,child_ESS_min=8,
    NSG_cap=350000,planned_NSG=337248,planned_HNSW=336960,normal_new_builds=4,synthetic_build_cap=8,synthetic_HNSW_cap=1024,threads=1,query_cpu=15,
    latest_launch=1789271400,query_stop=1789272000,session_deadline=1789272798,output_cap_MiB=128,free_min_GiB=7))
dump(O/'reviews/base_graph_stat.json',dict(scope='Current stat linked to already verified E61 provenance; no new full hash claim',
    sources=[dict(dataset=ds,key=k,path=c[k],bytes=Path(c[k]).stat().st_size,mtime_ns=Path(c[k]).stat().st_mtime_ns) for ds,c in configs.items() for k in ['base_file','index_path']],
    inherited_manifest=str(C/'stage2_missing_targets_v1/reviews/prebuild_freeze.json')))
deps.update(p for folder in ['src','source_before','inputs'] for p in (O/folder).rglob('*') if p.is_file())
deps.update([O/'protocol.md',O/'config.locked.json',O/'reviews/base_graph_stat.json'])
dump(O/'reviews/prebuild_freeze.json',dict(epoch=time.time(),files=[identity(p) for p in sorted(deps)]))
dump(O/'state.json',dict(status='PROTOCOL_AND_SOURCES_FROZEN_BEFORE_BUILD',new_NSG=0,day_goal_complete=False))
print('PREPARE_PASS',len(deps),flush=True)
