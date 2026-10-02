from common import *
import subprocess,difflib
threads();resources();assert not (O/'config.locked.json').exists()
old=C/'stage11_width_control_v1'
paths=[old/'reviews/final_artifact_freeze.json',C/'stage12_width_wall_v1/reviews/final_artifact_freeze.json']
for f in paths:check(f)
for x in read(E66/'reviews/dependency_stat_verification.json')['sources']:
 s=Path(x['path']).stat();assert (s.st_size,s.st_mtime_ns)==(x['bytes'],x['mtime_ns'])
shutil.copy2(E66/'reviews/dependency_stat_verification.json',O/'reviews/base_graph_identity.json')
for di,ds in enumerate(DS):
 inp=O/'inputs'/ds;inp.mkdir();original=read(E66/'inputs'/ds/'aux.json');paths.append(E66/'inputs'/ds/'aux.json')
 for split,n in [('preflight',128),('aux',7952)]:
  c={k:v for k,v in original.items() if k!='methods'};c.update(split='E72_historical_aux_'+split,num_queries=n,input_total_rows=7952,dataset_order=di,real_call_cap=6*(2*n+16),timing_repeats=0);methods=[]
  for m in original['methods']:
   for variant in ['10','D10']:
    mm=dict(m,model_name=m['model_name']+variant,name=m['model_name']+variant+'_L128',ef_search=10,reference_graph=True,distinct_hub_width=10 if variant=='D10' else 0)
    methods.append(mm)
   paths += [Path(m[k]) for k in ['W','mapping','tie_ids','graph_file']]
  c['methods']=methods;dump(inp/(split+'.json'),c)
 for k in ['queries_file','gt_file','row_ids']:paths.append(Path(original[k]))
builds=[]
for name in ['evaluate','synthetic']:
 if name=='evaluate':
  argv=read(old/'bin/provenance.json')['argv'];argv=[str(O/'src/evaluate.cpp') if x==str(old/'src/evaluate.cpp') else str(O/'bin/evaluate') if x==str(old/'bin/evaluate') else x for x in argv]
 else:argv=['c++','-std=c++17','-O3','-march=native','-I'+str(R/'benches'),str(O/'src/synthetic.cpp'),'-o',str(O/'bin/synthetic')]
 tick=time.monotonic()
 with (O/'logs'/('build_'+name+'.log')).open('x') as f:p=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,timeout=180)
 assert p.returncode==0,name
 builds.append(dict(argv=argv,seconds=time.monotonic()-tick,returncode=0,binary=identity(O/'bin'/name)))
 paths += [Path(x) for x in argv if Path(x).is_file()]
dump(O/'bin/provenance.json',dict(builds=builds,seconds=sum(x['seconds'] for x in builds)))
diff=''
for name in ['benchmark_with_nsg.cpp','evaluate.cpp','legacy_reference.cpp']:
 diff+=''.join(difflib.unified_diff((old/'src'/name).read_text().splitlines(True),(O/'src'/name).read_text().splitlines(True),fromfile='E70/'+name,tofile='E72/'+name))
(O/'reviews/source_diff.txt').write_text(diff)
dump(O/'config.locked.json',dict(datasets=DS,distinct_width=10,models=MODELS,threads=1,CPU=15,NSG_expected=194304,HNSW_expected=193920,builds=0,synthetic_build_cap=4,synthetic_HNSW_cap=1000,NSG_hard_cap=200000,output_cap_MiB=64,free_min_GiB=7,latest_launch=1789277700,query_hard_stop=1789278300,per_job_seconds=600,quality_gate='modeD10 beats P10 full; >=mode10/mode30 full; all three nonnegative halves/no failure increase; routeNDC < mode30'))
paths += list((O/'src').glob('*'))+list((O/'inputs').rglob('*.json'))+list((O/'bin').glob('*'))+list((R/'ACSG').glob('*.h'))+list((R/'benches/hnswlib').glob('*.h'))+[O/'protocol.md',O/'config.locked.json',O/'reviews/source_diff.txt']
freeze(O/'reviews/prequery_freeze.json',paths);dump(O/'logs/jobs.json',[])
tick=time.monotonic();p=subprocess.run([str(O/'bin/synthetic')],capture_output=True,text=True,timeout=60)
(O/'logs/synthetic.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
s=json.loads(p.stdout);s['seconds']=time.monotonic()-tick;dump(O/'reviews/synthetic.json',s)
dump(O/'state.json',dict(status='PREPARED_DISTINCT_CONTROL_SYNTHETIC_PASS',NSG=0,day_goal_complete=False));resources();print('PREPARED_E72',s)
