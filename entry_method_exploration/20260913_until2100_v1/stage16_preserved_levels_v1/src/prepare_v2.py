from common import *
import subprocess,struct
threads();resources();assert not (O/'config.locked.json').exists();E73=C/'stage14_compact_modes_v1'
paths=[O/'protocol.md',E73/'reviews/final_artifact_freeze.json']
for item in read(E66/'reviews/dependency_stat_verification.json')['sources']:
 s=Path(item['path']).stat();assert (s.st_size,s.st_mtime_ns)==(item['bytes'],item['mtime_ns'])
shutil.copy2(E66/'reviews/dependency_stat_verification.json',O/'reviews/base_graph_identity.json')
for name in ['evaluate.cpp','benchmark_with_nsg.cpp','legacy_reference.cpp']:
 shutil.copy2(E73/'src'/name,O/'src'/name)
assert sha(O/'bin/evaluate')==sha(E73/'bin/evaluate')
argv=['c++','-std=c++17','-O3','-march=native','-Wall','-Wextra','-I'+str(R),'-I'+str(R/'build/_deps/json-src/include'),str(O/'src/build_levels.cpp'),'-lpthread','-o',str(O/'bin/build_levels')]
tick=time.monotonic()
with (O/'logs/compile_v2.log').open('x') as f:p=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,timeout=180)
assert p.returncode==0,'compile failed'
dump(O/'bin/provenance.json',dict(argv=argv,seconds=time.monotonic()-tick,builder=identity(O/'bin/build_levels'),evaluator=identity(O/'bin/evaluate'),source_evaluator=identity(E73/'bin/evaluate')))
models={}
for di,ds in enumerate(DS):
 original=read(E73/'inputs'/ds/'aux.json');source=read(E73/'models'/ds/'manifest.json')['source'];m=dict(next(x for x in original['methods'] if x['model_name']=='compact10'));dest=O/'models'/ds;dest.mkdir()
 m.update(model_name='preserved10',name='preserved10_L128',graph_file=str(dest/'graph.hnsw'));dump(dest/'model.json',m);models[ds]=m
 config=dict(source_count=source['hub_count'],dim=original['dim'],seed=20260828,original_slots=str(E73/'models'/ds/'original_slots.i32'),source_graph=source['graph_file'],W=m['W']);dump(dest/'build_config.json',config)
 paths += [Path(source[k]) for k in ['W','mapping','tie_ids','graph_file']]+[Path(m[k]) for k in ['W','mapping','tie_ids']]+[Path(config['original_slots']),E73/'models'/ds/'old_to_compact.i32']
 paths += [Path(original[k]) for k in ['queries_file','gt_file','row_ids']]+[E73/'inputs'/ds/'aux.json']
 for x in original['methods']:paths += [Path(x[k]) for k in ['W','mapping','tie_ids','graph_file']]
dump(O/'config.locked.json',dict(datasets=DS,threads=1,CPU=15,NSG_expected=97152,HNSW_expected=96960,builds=2,synthetic_build_cap=4,synthetic_HNSW_cap=512,NSG_hard_cap=100000,output_cap_MiB=64,free_min_GiB=7,latest_launch=1789281600,query_hard_stop=1789282200,per_job_seconds=600,quality_gate='both P and compact: full net hits >0, halves >=0, failure count not increased',wall_measurement='only if at least one dataset passes; separate E76 all baselines and both datasets migration control'))
paths+=list((O/'src').glob('*'))+list((O/'bin').glob('*'))+list((O/'models').rglob('*.json'))+[O/'config.locked.json',R/'benches/hnswlib/hnswalg.h',R/'benches/hnswlib/hnswlib.h']
freeze(O/'reviews/prebuild_freeze.json',paths)
for ds in DS:
 dest=O/'models'/ds;p=subprocess.run([str(O/'bin/build_levels'),'inspect',str(dest/'build_config.json'),str(dest/'random_stream.json')],capture_output=True,text=True,timeout=120)
 (O/'logs'/('inspect_'+ds+'.log')).write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
 assert read(dest/'random_stream.json')['status']=='PASS'
dump(O/'reviews/random_stream_gate.json',dict(status='PASS',datasets=DS,builds=0,HNSW=0,NSG=0))
p=subprocess.run([str(O/'bin/build_levels'),'synthetic'],capture_output=True,text=True,timeout=120);(O/'logs/synthetic.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
dump(O/'reviews/synthetic.json',json.loads(p.stdout))
for ds in DS:
 dest=O/'models'/ds;p=subprocess.run([str(O/'bin/build_levels'),'build',str(dest/'build_config.json'),str(dest/'graph.hnsw')],capture_output=True,text=True,timeout=180)
 (O/'logs'/('build_'+ds+'.log')).write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
 r=json.loads(p.stdout);r['graph']=identity(dest/'graph.hnsw');dump(dest/'build.json',r)
for di,ds in enumerate(DS):
 original=read(E73/'inputs'/ds/'aux.json');inp=O/'inputs'/ds;inp.mkdir()
 for split,n in [('preflight',128),('aux',7952)]:
  methods=[dict(x) for x in original['methods'] if x['model_name'] in ['baseline10','compact10']]+[models[ds]]
  c=dict(original,methods=methods,split='E75_historical_aux_'+split,num_queries=n,input_total_rows=7952,dataset_order=di,real_call_cap=3*(2*n+16),timing_repeats=0);dump(inp/(split+'.json'),c)
paths+=list((O/'inputs').rglob('*.json'))+list((O/'models').rglob('*.hnsw'))+list((O/'models').rglob('random_stream.json'))+[O/'reviews/synthetic.json',O/'reviews/random_stream_gate.json']
freeze(O/'reviews/prequery_freeze.json',paths);dump(O/'logs/jobs.json',[]);dump(O/'state.json',dict(status='BUILT_UNQUERIED',NSG=0,HNSW=0,builds=2,day_goal_complete=False));resources();print('E75_PREPARED')
