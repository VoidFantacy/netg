from common import *
assert not (O/'reviews/preflight.json').exists()
for x in ['inputs','bin','results','logs','reviews','source_before','figures']:(O/x).mkdir(exist_ok=True)
for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:
 dest=O/'source_before'/x;assert not dest.exists();shutil.copy2(R/x,dest)
assert read(E33/'reviews/final_audit.json')['status']=='PASS'
assert read(E33/'results/development_gate.json')['status']=='STOP_DEVELOPMENT_GATE'
expected={x['path']:x for x in read(E33/'reviews/protected_before.json')['files']}
expected.update({x['path']:x for x in read(E33/'reviews/frozen_analysis_before_final_audit.json')['files']})
for x in ['evaluate.cpp','benchmark_with_nsg.cpp','legacy_reference.cpp']:shutil.copy2(E33/'src'/x,O/'src'/x)
shutil.copy2(E33/'bin/evaluate',O/'bin/evaluate')
assert sha(O/'bin/evaluate')==sha(E33/'bin/evaluate')
dump(O/'bin/provenance.json',dict(source=str(E33/'bin/evaluate'),sha256=sha(O/'bin/evaluate'),build=read(E33/'bin/evaluate.build.json'),byte_identical=True,new_compile=False))
selection=read(E33/'results/cal_selection.json')['selection'];source_files=set()
for ds in DS:
 src=E30/'inputs'/ds/'validation/config.json';old=read(E30/'results'/f'validation_{ds}'/'results.json')
 c={k:v for k,v in read(src).items() if k not in ['methods','measure_wall','protocol_sha256','timing_repeats']}
 assert c['num_queries']==2000 and c['gt_k']==100
 c.update(timing_repeats=5,threads=1,query_cpu=15,dataset_order=DS.index(ds),split='historical_validation2000_E34',protocol_sha256=sha(O/'protocol.md'))
 inputs=O/'inputs'/ds;inputs.mkdir()
 for key in ['queries_file','gt_file','row_ids']:
  p=Path(c[key]);source_files.add(p);dest=inputs/p.name;shutil.copy2(p,dest);assert sha(p)==sha(dest);c[key]=str(dest)
 n,d=c['num_queries'],c['dim'];q=np.fromfile(c['queries_file'],np.float32).reshape(n,d);gt=np.fromfile(c['gt_file'],np.int64).reshape(n,100);rows=np.fromfile(c['row_ids'],np.int64)
 assert np.isfinite(q).all() and rows.size==len(np.unique(rows))==n and ((gt>=0)&(gt<c['base_count'])).all()
 fit=read(E33/'inputs'/ds/'config.json');assert not np.intersect1d(rows,np.fromfile(fit['row_ids'],np.int64)).size
 source_files.update([src,E30/'results'/f'validation_{ds}'/'results.json',Path(c['index_path']),Path(c['index_path']+'.info')])
 want=['nsg','fast30k','gt10_hard']+(['gt10_soft'] if ds==DS[0] else [])
 models=[]
 for key in want:
  p=copy.deepcopy(next(m['configuration'] for m in old['methods'] if m['model_name']==key and m['L']==64));p['component_wall']=False
  if key!='nsg':
   oldname=next(m['name'] for m in old['methods'] if m['model_name']==key and m['L']==64)
   p['graph_file']=str(E30/'results'/f'validation_{ds}'/(oldname+'.hnsw'))
   for field in ['W','mapping','tie_ids','graph_file']:source_files.add(Path(p[field]))
  if key=='fast30k':assert p['hnsw_seed']==100 and p['legacy_heap_order'] and not p['canonical_entry_order']
  models.append(p)
 basekey='gt10_soft' if ds==DS[0] else 'gt10_hard';p=copy.deepcopy(next(m for m in models if m['model_name']==basekey))
 assert sha(p['graph_file'])==sha(E33/'inputs'/ds/'base.hnsw')
 p.update(model_name='rl',graph_file=str(E33/'models'/ds/str(selection[ds])/'selected/graph.hnsw'),rl_seed=selection[ds],rl_base=basekey)
 source_files.add(Path(p['graph_file']));models.append(p)
 c['methods']=[dict(p,L=L,name=p['model_name']+f'_L{L}') for L in LS for p in models]
 c['real_call_cap']=len(c['methods'])*(7*n+16);dump(inputs/'config.json',c)
assert sum(read(O/'inputs'/ds/'config.json')['real_call_cap'] for ds in DS)==630720
source_files.update([R/'AGENTS.md',E33/'bin/evaluate',E33/'results/cal_selection.json',E33/'results/development_gate.json'])
source_files.update(Path(x['path']) for x in read(E33/'reviews/protected_before.json')['files'] if not str(x['path']).startswith(str(R/'entry_method_exploration')))
for p in source_files:
 if str(p) in expected:assert identity(p)==expected[str(p)],p
freeze(O/'reviews/upstream.json',source_files)
freeze(O/'reviews/E33_preserved.json',[p for p in E33.rglob('*') if p.is_file()])
freeze(O/'reviews/before_queries.json',[O/'protocol.md',O/'bin/evaluate',O/'bin/provenance.json']+list((O/'src').glob('*'))+[p for p in (O/'inputs').rglob('*') if p.is_file()])
resources();dump(O/'reviews/preflight.json',dict(status='PASS',selection=selection,RL_reselected=False,E33_stop_retained=True,points=45,calls=630720,threads=1,GT_rows=100,heldout_access=False,binary_byte_identical=True))
dump(O/'state.json',dict(status='READY',points=45,optimizer_updates=0,heldout_access=False));print('PREFLIGHT_PASS 45 points 630720 calls',flush=True)
