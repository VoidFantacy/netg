from common import *
from graph_reader import inspect_serialized
threads();resources();E66=C/'stage7_multimode_index_v1';E65=C/'stage6_development_wall_v1';check(E66/'reviews/final_artifact_freeze.json')
assert not (O/'reviews/prequery_freeze.json').exists();protected=set();roles=[];matrix={};selection={}
assert sha(O/'bin/evaluate')==sha(E66/'bin/evaluate')
for ds in DS:
    old=read(E65/'inputs'/ds/'config.json');fit=read(E66/'inputs'/ds/'fit.json');folder=O/'inputs'/ds;folder.mkdir()
    for key,file in [('queries_file','queries.f32'),('gt_file','gt.i64'),('row_ids','row_ids.i64')]:
        shutil.copy2(old[key],folder/file);protected.add(Path(old[key]))
    methods=[dict(m) for m in old['methods'] if m['L']==64 and m['model_name']!='best_new']
    for source,name in [('duplicate3P','duplicate3P'),('mode3P','best_new')]:
        m=dict(next(m for m in fit['methods'] if m['model_name']==source));m.update(model_name=name,selected_source_name=source)
        methods.append(m)
    ms=[dict(m,L=L,name=m['model_name']+f'_L{L}',component_wall=False) for L in [64,128,256,400,800] for m in methods]
    for m in methods:
        if m['family']!='nsg':
            for k in ['W','mapping','tie_ids','graph_file']:protected.add(Path(m[k]))
            mapping=np.fromfile(m['mapping'],np.int32);W=np.fromfile(m['W'],np.float32).reshape(len(mapping),old['dim'])
            inspect_serialized(m['graph_file'],W,np.arange(len(W)) if m.get('slot_labels') else mapping)
    cfg=dict(old,split='E67_historical_multimode_development2048',queries_file=str(folder/'queries.f32'),gt_file=str(folder/'gt.i64'),row_ids=str(folder/'row_ids.i64'),
        timing_repeats=5,methods=ms,real_call_cap=len(ms)*(7*2048+16))
    dump(folder/'config.json',cfg);matrix[ds]=cfg;selection[ds]=dict(best_new='E66_mode3P',best_all='baseline',E66_gate_pass=False,duplicate_not_selectable=True)
    roles.append(dict(dataset=ds,source_namespace=read(E66/'inputs'/ds/'construction.json')['namespace'],source_rows=[2048,4096],
        historical_development_exposed=True,E66_auxiliary_training=True,E34_final_input_access=False,actual_new='mode3P'))
dump(O/'inputs/matrix.json',matrix);dump(O/'results/frozen_selection.json',dict(datasets=selection))
dump(O/'reviews/input_roles.json',dict(status='PASS_DEVELOPMENT_ONLY',datasets=roles))
dump(O/'config.locked.json',dict(NSG_cap=800000,planned_NSG=789360,planned_HNSW=645120,points=55,timing_batches=275,threads=1,query_cpu=15,
    latest_launch=1789270800,query_stop=1789272000,final_validation_access=False,new_models=False,new_graphs=False,free_min_GiB=7,output_cap_MiB=192))
protected.update(p for folder in ['src','inputs','source_before','bin'] for p in (O/folder).rglob('*') if p.is_file())
protected.update([O/'protocol.md',O/'config.locked.json',O/'results/frozen_selection.json',E66/'reviews/final_artifact_freeze.json'])
dump(O/'reviews/prequery_freeze.json',dict(epoch=time.time(),files=[identity(p) for p in sorted(protected)]))
dump(O/'state.json',dict(status='FROZEN_BEFORE_MULTIMODE_WALL',new_NSG=0,day_goal_complete=False))
state=read(C/'state.json');state.update(status='E67_PREPARED',stage='E67',native_pids=[]);dump(C/'state.json',state);print('E67_PREPARE_PASS',flush=True)
