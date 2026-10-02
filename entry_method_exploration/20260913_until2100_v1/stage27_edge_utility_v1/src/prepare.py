from common import *
import subprocess,struct
threads();resources();paths=list((O/'src').glob('*'))+[O/'protocol.md',C/'session9_resource_protocol.json'];assert not (O/'reviews/precompile_freeze.json').exists()
for ds in DS:
 inp=O/'inputs'/ds;inp.mkdir();cfg=read(E84/'inputs'/ds/'fit.json');fit=read(E66/'inputs'/ds/'fit.json')
 choices=sorted(read(E84/'models'/ds/'additions.json'),key=lambda x:(-x['votes'],x['slot'],x['shortcut_added'][0]))[:64]
 assert len(choices)==(64 if ds==DS[0] else 47);dump(inp/'candidates.json',choices);dump(inp/'routes.json',cfg)
 native=dict(read(C/'stage10_exact_triple_utility_v1/inputs'/ds/'native.json'),queries_file=cfg['queries_file'],num_queries=20000,native_call_cap=16384);dump(inp/'native.json',native)
 for key in ['queries_file','row_ids','gt_file']:paths.append(Path(fit[key]))
 assert np.array_equal(np.fromfile(fit['row_ids'],np.int64,count=20000),np.arange(10000,30000))
 for m in ['baseline','mode3P']:
  p=E66/'results'/ds/'fit'/(m+'_L128');paths.extend(p/f for f,dt,w in FIELDS.values())
 paths.extend(Path(cfg['method'][k]) for k in ['W','mapping','tie_ids','graph_file'])
 paths += list((E84/'results'/ds/'routes_fit').glob('*'))+[E84/'models'/ds/'additions.json',E66/'inputs'/ds/'fit.json']
 # Same complete query/GT/row identity and current large graph stat; no final inputs.
 for x in read(E73/'reviews/base_graph_identity.json')['sources']:
  st=Path(x['path']).stat();assert (st.st_size,st.st_mtime_ns)==(x['bytes'],x['mtime_ns'])
shutil.copy2(E73/'reviews/base_graph_identity.json',O/'reviews/base_graph_identity.json')
args=read(E73/'bin/provenance.json')['builds'][1]['argv'];args=[str(O/'src/routes.cpp') if x==str(E73/'src/build_graph.cpp') else str(O/'bin/routes.so') if x==str(E73/'bin/build_graph') else x for x in args];args.insert(1,'-shared')
paths += [Path(x) for x in args if Path(x).is_file()]+list((O/'inputs').rglob('*.json'))+[C/'stage10_exact_triple_utility_v1/bin/inject.so',E73/'bin/evaluate',E73/'src/benchmark_with_nsg.cpp',E73/'src/legacy_reference.cpp']
freeze(O/'reviews/precompile_freeze.json',paths)
tick=time.monotonic()
with (O/'logs/compile.log').open('x') as f:p=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=180)
dump(O/'bin/provenance.json',dict(argv=args,returncode=p.returncode,seconds=time.monotonic()-tick))
assert p.returncode==0
dump(O/'config.locked.json',dict(training_NSG_cap=32768,per_dataset_training_NSG_cap=16384,training_HNSW_cap=4700000,aux_NSG=161920,aux_HNSW=161600,NSG_hard_cap=194688,HNSW_hard_cap=4861600,latest_training_launch=1789293300,latest_aux_launch=1789293720,query_hard_stop=1789294200,output_cap_MiB=96,free_min_GiB=6.55,threads=1,CPU=15))
dump(O/'logs/training_jobs.json',[]);dump(O/'logs/jobs.json',[]);dump(O/'state.json',dict(status='COMPILED_TRAINING_SOURCE_PENDING',NSG=0,HNSW=0,day_goal_complete=False))
print('E86_COMPILED',read(O/'bin/provenance.json'),flush=True)
