from common import *
from graph_reader import inspect_serialized
threads();resources();E73=C/'stage14_compact_modes_v1';E71=C/'stage12_width_wall_v1';check(E73/'reviews/final_artifact_freeze.json');assert read(E73/'reviews/verification.json')['status']=='PASS'
assert not (O/'reviews/prequery_freeze.json').exists();paths=set();roles=[];matrix={};selection={};assert sha(O/'bin/evaluate')==sha(E73/'bin/evaluate')
for x in read(E73/'reviews/base_graph_identity.json')['sources']:
 s=Path(x['path']).stat();assert (s.st_size,s.st_mtime_ns)==(x['bytes'],x['mtime_ns'])
shutil.copy2(E73/'reviews/base_graph_identity.json',O/'reviews/base_graph_identity.json')
for ds in DS:
 old=read(E71/'inputs'/ds/'config.json');dev=read(E73/'inputs'/ds/'aux.json');folder=O/'inputs'/ds;folder.mkdir();paths.add(E71/'inputs'/ds/'config.json');paths.add(E73/'inputs'/ds/'aux.json')
 methods=[dict(m,reference_graph=True,ef_search=10) for m in old['methods'] if m['L']==64 and m['model_name'] not in ['p30','best_new']]
 for m in methods:
  if m['model_name']=='mode10':m['selected_source_name']='mode10'
 new=dict(next(m for m in dev['methods'] if m['model_name']=='compact10'),model_name='best_new',selected_source_name='compact10');methods.append(new)
 for m in methods:
  if m['family']!='nsg':
   for k in ['W','mapping','tie_ids','graph_file']:paths.add(Path(m[k]))
   mapping=np.fromfile(m['mapping'],np.int32);W=np.fromfile(m['W'],np.float32).reshape(len(mapping),old['dim']);inspect_serialized(m['graph_file'],W,np.arange(len(W)) if m.get('slot_labels') else mapping)
 ms=[dict(m,L=L,name=m['model_name']+f'_L{L}',component_wall=False) for L in [64,128,256,400,800] for m in methods]
 c=dict(old,split='E74_historical_compact_development2048',timing_repeats=5,methods=ms,real_call_cap=len(ms)*(7*2048+16))
 for k in ['queries_file','gt_file','row_ids']:paths.add(Path(c[k]))
 dump(folder/'config.json',c);matrix[ds]=c;selection[ds]=dict(best_new='E73_compact_mode10',best_all='not_reselected',E73_quality_gate_pass=read(E73/'results/gate.json')['datasets'][ds]['passed'],mode10='same full E66 mode bank ef10')
 roles.append(dict(dataset=ds,source_namespace=next(x['source_namespace'] for x in read(E71/'reviews/input_roles.json')['datasets'] if x['dataset']==ds),source_rows=[2048,4096],historical_development_exposed=True,E73_auxiliary_training=True,E34_final_input_access=False,actual_new='compact mode3P ef10'))
assert sum(c['real_call_cap'] for c in matrix.values())==789360
dump(O/'inputs/matrix.json',matrix);dump(O/'results/frozen_selection.json',dict(datasets=selection));dump(O/'reviews/input_roles.json',dict(status='PASS_DEVELOPMENT_ONLY',datasets=roles));dump(O/'logs/jobs.json',[])
dump(O/'config.locked.json',dict(NSG_cap=800000,planned_NSG=789360,planned_HNSW=645120,points=55,timing_batches=275,threads=1,query_cpu=15,latest_launch=1789278600,query_stop=1789279500,per_job_seconds=1200,final_validation_access=False,new_models=False,new_graphs=False,free_min_GiB=7,output_cap_MiB=64))
dump(O/'bin/provenance.json',dict(source_binary=identity(E73/'bin/evaluate'),copied_binary=identity(O/'bin/evaluate'),compile_seconds=0))
paths.update(p for folder in ['src','inputs','source_before','bin'] for p in (O/folder).rglob('*') if p.is_file());paths.update([O/'protocol.md',O/'config.locked.json',O/'results/frozen_selection.json',E73/'reviews/final_artifact_freeze.json'])
dump(O/'reviews/prequery_freeze.json',dict(epoch=time.time(),files=[identity(p) for p in sorted(paths)]));dump(O/'state.json',dict(status='FROZEN_BEFORE_COMPACT_WALL',new_NSG=0,day_goal_complete=False));s=read(C/'state.json');s.update(status='E74_PREPARED',stage='E74',native_pids=[]);dump(C/'state.json',s);print('E74_PREPARED')
