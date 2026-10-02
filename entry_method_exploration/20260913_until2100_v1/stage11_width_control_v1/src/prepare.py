from common import *
import subprocess
threads();resources();assert not (O/'config.locked.json').exists();check(C/'stage10_exact_triple_utility_v1/reviews/final_artifact_freeze.json')
assert read(C/'stage10_exact_triple_utility_v1/results/gate.json')['next_width_diagnosis_supported']
paths=[E66/'bin/provenance.json',C/'stage10_exact_triple_utility_v1/reviews/final_artifact_freeze.json']
for x in read(E66/'reviews/dependency_stat_verification.json')['sources']:
 s=Path(x['path']).stat();assert (s.st_size,s.st_mtime_ns)==(x['bytes'],x['mtime_ns'])
shutil.copy2(E66/'reviews/dependency_stat_verification.json',O/'reviews/base_graph_identity.json')
for di,ds in enumerate(DS):
 inp=O/'inputs'/ds;inp.mkdir();original=read(E66/'inputs'/ds/'aux.json');paths.append(E66/'inputs'/ds/'aux.json')
 for split,n in [('preflight',128),('aux',7952)]:
  c={k:v for k,v in original.items() if k!='methods'};c.update(split='E70_historical_aux_'+split,num_queries=n,input_total_rows=7952,dataset_order=di,real_call_cap=6*(2*n+16),timing_repeats=0);methods=[]
  for m in original['methods']:
   for ef in [10,30]:
    mm=dict(m,model_name=m['model_name']+str(ef),name=m['model_name']+str(ef)+'_L128',ef_search=ef,reference_graph=True)
    methods.append(mm)
   paths += [Path(m[k]) for k in ['W','mapping','tie_ids','graph_file']]
  c['methods']=methods;dump(inp/(split+'.json'),c)
 for k in ['queries_file','gt_file','row_ids']:paths.append(Path(original[k]))
argv=read(E66/'bin/provenance.json')['builds'][0]['argv'];argv=[str(O/'src/evaluate.cpp') if x==str(E66/'src/evaluate.cpp') else str(O/'bin/evaluate') if x==str(E66/'bin/evaluate') else x for x in argv]
tick=time.monotonic()
with (O/'logs/build.log').open('x') as f:p=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,timeout=180)
assert p.returncode==0
assert (O/'src/evaluate.cpp').read_bytes()==(E66/'src/evaluate.cpp').read_bytes()
dump(O/'bin/provenance.json',dict(argv=argv,seconds=time.monotonic()-tick,returncode=0,binary=identity(O/'bin/evaluate'),source_diff=str(O/'reviews/source_diff.txt'),unchanged_evaluate=True,unchanged_legacy=(O/'src/legacy_reference.cpp').read_bytes()==(E66/'src/legacy_reference.cpp').read_bytes()))
paths += [Path(x) for x in argv if Path(x).is_file()]+list((R/'ACSG').glob('*.h'))+list((R/'benches/hnswlib').glob('*.h'))
dump(O/'config.locked.json',dict(datasets=DS,ef_values=[10,30],models=MODELS,threads=1,CPU=15,NSG_expected=194304,HNSW_expected=193920,builds=0,NSG_hard_cap=200000,output_cap_MiB=48,free_min_GiB=7,latest_launch=1789274700,query_hard_stop=1789275300,per_job_seconds=600,quality_gate='mode30 beats both P10 and P30 in full hits, halves nonnegative, failure nonincrease; >=mode10 hits; quality only no speed claim'))
paths += list((O/'src').glob('*'))+list((O/'inputs').rglob('*.json'))+list((O/'bin').glob('*'))+[O/'protocol.md',O/'config.locked.json',O/'reviews/source_diff.txt']
freeze(O/'reviews/prequery_freeze.json',paths);dump(O/'logs/jobs.json',[]);dump(O/'state.json',dict(status='PREPARED_WIDTH_CONTROL',NSG=0,day_goal_complete=False));resources();print('PREPARED_E70')
