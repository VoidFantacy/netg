from common import *
import subprocess
threads();resources();assert not (O/'reviews/pretraining_freeze.json').exists();E73=C/'stage14_compact_modes_v1';paths=[O/'protocol.md',C/'session8_resource_protocol.json'];started=time.monotonic()
for x in read(E73/'reviews/base_graph_identity.json')['sources']:
 s=Path(x['path']).stat();assert (s.st_size,s.st_mtime_ns)==(x['bytes'],x['mtime_ns'])
shutil.copy2(E73/'reviews/base_graph_identity.json',O/'reviews/base_graph_identity.json')
for ds in DS:
 src=read(E73/'inputs'/ds/'aux.json');fit=read(E66/'inputs'/ds/'fit.json');method=next(m for m in src['methods'] if m['model_name']=='compact10');inp=O/'inputs'/ds;inp.mkdir()
 for label,sc,n,total in [('fit',fit,20000,22048),('route_regression',src,128,7952)]:
  cfg=dict(dataset=ds,role='P-fit graph supervision' if label=='fit' else 'aux prefix routing identity only; excluded from votes',method=method,num_queries=n,input_total_rows=total,queries_file=sc['queries_file'],row_ids=sc['row_ids'],dim=sc['dim'],threads=1,query_cpu=15);assert Path(sc['queries_file']).stat().st_size==total*sc['dim']*4;dump(inp/(label+'.json'),cfg);paths += [Path(sc['queries_file']),Path(sc['row_ids'])]
 paths += [Path(method[k]) for k in ['W','mapping','tie_ids','graph_file']]+[E73/'inputs'/ds/'aux.json',E66/'inputs'/ds/'fit.json',C/'stage9_profile_ranking_diagnosis_v1/results'/ds/'fit.npz']
 paths += [E73/'results'/ds/'aux/compact10_L128'/x for x in ['entry_ids.i32','candidate_slots.i32','candidate_distances.f32','route_ndc.u32']]
args=read(E73/'bin/provenance.json')['builds'][1]['argv'];args=[str(O/'src/route_only.cpp') if x==str(E73/'src/build_graph.cpp') else str(O/'bin/route_only') if x==str(E73/'bin/build_graph') else x for x in args]
# Lock source/inputs before compiling or route labels.
paths += [Path(x) for x in args if Path(x).is_file()]+[E73/'src'/x for x in ['benchmark_with_nsg.cpp','legacy_reference.cpp']]+list((O/'src').glob('*.py'))+[O/'src/route_only.cpp']+list((O/'inputs').rglob('*.json'))
freeze(O/'reviews/precompile_freeze.json',paths)
tick=time.monotonic()
with (O/'logs/compile.log').open('x') as f:proc=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=180)
assert proc.returncode==0,'compile failed'
dump(O/'bin/provenance.json',dict(argv=args,compile_seconds=time.monotonic()-tick,binary=identity(O/'bin/route_only'),evaluator=identity(O/'bin/evaluate'),source_evaluator=identity(E73/'bin/evaluate')))
paths+=[O/'bin/route_only',O/'bin/provenance.json'];freeze(O/'reviews/pretraining_freeze.json',paths);dump(O/'logs/route_jobs.json',[]);dump(O/'state.json',dict(status='PREPARED_QUERY_SHORTCUT_TRAINING',HNSW=0,NSG=0,builds=0,day_goal_complete=False));print('E84_PREPARED',read(O/'bin/provenance.json')['compile_seconds'])
