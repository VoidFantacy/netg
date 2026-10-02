from common import *
import ast,sys
assert os.sched_getaffinity(0)=={8};resources();assert not (O/'config.locked.json').exists()
for name in ['inputs','results','reviews','logs','figures','source_before','bin']:(O/name).mkdir(exist_ok=True)
assert read(E54/'reviews/final_audit.json')['status']=='PASS';check(E54/'reviews/final_artifact_freeze.json')
freeze(O/'reviews/protected.json',[p for root in [E47,E52,E53,E54] for p in root.rglob('*') if p.is_file()])
check(E54/'reviews/native_dependencies.json');shutil.copy2(E54/'reviews/native_dependencies.json',O/'reviews/native_dependencies.json')
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:shutil.copy2(R/name,O/'source_before'/name.replace('/','__'))
shutil.copy2(E37/'bin/evaluate',O/'bin/evaluate');assert sha(O/'bin/evaluate')==sha(E34/'bin/evaluate')
upstream=[];isolation=[];pool={}
for ds in DS:
 c=read(E37/'inputs'/ds/'config.json');dump(O/'inputs'/ds/'config.json',c)
 base=dict(c['original_policy'],model_name='baseline',graph_file=str(E37/'results'/ds/'baseline.hnsw'),W=c['P'],mapping=c['hub_ids'],tie_ids=c['hub_ids'])
 mm=[dict(base,prior_raw=str(E37/'results'/ds/'baseline.npz'))]
 for arm in ARMS:
  for seed in SEEDS:
   p=E47/'models'/ds/f'{arm}_{seed}';st=read(p/'model.json')['selected_step']
   mm.append(dict(base,model_name=f'E47_{arm}_{seed}',W=str(p/'selected/W.f32'),graph_file=str(p/'selected/graph.hnsw'),prior_raw=str(p/'checkpoints'/f'{st:04}.npz')))
 for rec in [x for x in read(E54/'inputs/contexts.json') if x['dataset']==ds]:
  for cell in ['A','S','T']:
   p=E54/'results'/ds/rec['key']/cell
   mm.append(dict(base,model_name=rec['key']+'_'+cell,W=str(p/'W.f32'),graph_file=str(p/'graph.hnsw'),prior_raw=str(p/'raw.npz')))
 assert len(mm)==17;pool[ds]=mm
 v=read(E34/'inputs'/ds/'config.json');vq=np.fromfile(v['queries_file'],np.float32).reshape(2000,c['dim']);vs={row.tobytes() for row in vq};assert len(vs)==2000
 prep=read(E24/'inputs'/ds/'prepared.json');prov=read(E24/'inputs'/ds/'validation/provenance.json')
 assert 'router_train' in prep['source_train']['query_train']['path'] and 'validation' in prov['source_original_files'][0] and prov['slice_checked']==[0,2000]
 out=dict(dataset=ds,validation_source=prov['source_original_files'],train_source=prep['source_train']['query_train']['path'],source_namespace_distinct=True,validation_vector_unique=2000,phase_checks=[])
 for phase,src in [('train_monitor',c),('cal',{k:str(E37/'inputs'/ds/'cal'/n) for k,n in [('queries_file','queries.f32'),('gt_file','gt.i64'),('row_ids','row_ids.i64')]}),('audit',{k:str(E37/'inputs'/ds/'audit'/n) for k,n in [('queries_file','queries.f32'),('gt_file','gt.i64'),('row_ids','row_ids.i64')]})]:
  a=np.fromfile(src['queries_file'],np.float32).reshape(-1,c['dim']);overlap=sum(row.tobytes() in vs for row in a);assert overlap==0
  out['phase_checks'].append(dict(phase=phase,queries=len(a),exact_vector_overlap=overlap));upstream.extend(Path(src[k]) for k in ['queries_file','gt_file','row_ids'])
 for phase in ['fit_parity','cal','validation']:
  dest=O/'inputs'/ds/phase;dest.mkdir(parents=True);source=c if phase=='fit_parity' else (v if phase=='validation' else {k:str(E37/'inputs'/ds/'cal'/n) for k,n in [('queries_file','queries.f32'),('gt_file','gt.i64'),('row_ids','row_ids.i64')]})
  inds=np.r_[np.arange(64),np.arange(4096,4160)] if phase=='fit_parity' else np.arange(2000 if phase=='validation' else 1024)
  for key,dt,width,name in [('queries_file',np.float32,c['dim'],'queries.f32'),('gt_file',np.int64,100,'gt.i64'),('row_ids',np.int64,1,'row_ids.i64')]:
   f=Path(source[key]);a=np.fromfile(f,dt).reshape(-1,width);a[inds].tofile(dest/name);upstream.append(f)
   if phase=='validation':assert sha(f)==sha(E24/'inputs'/ds/'validation'/name)==sha(dest/name)
  dump(dest/'source.json',dict(source_namespace='validation' if phase=='validation' else 'router_train',files=[identity(source[k]) for k in ['queries_file','gt_file','row_ids']],original_full_validation_opened=False,heldout_opened=False))
 for m in mm:upstream.extend(Path(m[k]) for k in ['W','mapping','tie_ids','graph_file','prior_raw'])
 for m in [x for x in v['methods'] if x['L']==64 and x['model_name'] in ['nsg','fast30k','gt10_hard']]:
  if m['family']!='nsg':upstream.extend(Path(m[k]) for k in ['W','mapping','tie_ids','graph_file'])
 upstream.extend([E34/'inputs'/ds/'config.json',E24/'inputs'/ds/'prepared.json',E24/'inputs'/ds/'validation/provenance.json']);isolation.append(out)
dump(O/'inputs/candidate_pool.json',pool);dump(O/'reviews/split_isolation.json',dict(status='PASS',datasets=isolation,warning='Local row IDs use different source namespaces; exact vectors and source provenance jointly verified'))
freeze(O/'reviews/upstream.json',upstream)
dump(O/'config.locked.json',dict(candidate_models_per_dataset=17,fit_points=34,cal_points=34,final_points=45,NSG_calls=710144,NSG_cap=750000,wall_repeats=225,threads=1,LS=LS,selection='max mean_U; lower total NDC; lower fixed pool index; default first',query_stop=QUERY_STOP))
for p in (O/'src').rglob('*.py'):ast.parse(p.read_text())
freeze(O/'reviews/prequery_freeze.json',[p for name in ['src','inputs','bin'] for p in (O/name).rglob('*') if p.is_file()]+[O/'protocol.md',O/'config.locked.json'])
dump(O/'state.json',dict(status='PREPARED_FINAL_COMPARISON',NSG_calls=0,selection_frozen=False));print('E55 PREPARED 710144 NSG',flush=True)
