from common import *
from graph_reader import inspect_serialized
import subprocess
threads();resources();assert read(O/'results/offline.json')['status']=='PASS';assert not (O/'reviews/prebuild_freeze.json').exists()
check(O/'reviews/offline_freeze.json');check(O/'reviews/offline_models_freeze.json')
E73=C/'stage14_compact_modes_v1';E80=C/'stage21_hub_conditioned_targets_v1'
paths=[O/'protocol.md',O/'config.locked.json',O/'reviews/offline_freeze.json',O/'reviews/offline_models_freeze.json',O/'results/offline.json']+list((O/'src').glob('*.py'))+list((O/'models').rglob('*.*'))
for n in ['evaluate','build_graph']:assert sha(O/'bin'/n)==sha(E73/'bin'/n);paths.append(O/'bin'/n)
for x in read(O/'reviews/base_graph_identity.json')['sources']:
 s=Path(x['path']).stat();assert (s.st_size,s.st_mtime_ns)==(x['bytes'],x['mtime_ns'])
bytes_now=sum(p.stat().st_size for p in O.rglob('*') if p.is_file() and not p.is_symlink())
graph_bound=sum(Path(m['W']).stat().st_size+int(m['hub_count'])*160+4096 for m in [read(p) for p in (O/'models').rglob('model.json')])
raw_bound=2*((128+7952)*(115+3*171)+16384)
future=graph_bound+raw_bound+9*(1<<20)
assert bytes_now+future<64*(1<<20),(bytes_now,graph_bound,raw_bound)
assert shutil.disk_usage('/data').free-future>=6.8*(1<<30)+68*(1<<20)
dump(O/'reviews/phaseB_budget.json',dict(status='PASS',bytes_now=bytes_now,graph_bound=graph_bound,raw_bound=raw_bound,derived_and_seal_bound=9*(1<<20),projected_total=bytes_now+future,free_bytes=shutil.disk_usage('/data').free,resource_contract='new E81 floor6.8GiB plus68MiB; old7GiB contracts untouched'))
dump(O/'bin/provenance.json',dict(compile_seconds=0,link_reuse=True,evaluator=identity(O/'bin/evaluate'),builder=identity(O/'bin/build_graph'),sources=[identity(E73/'src'/n) for n in ['evaluate.cpp','benchmark_with_nsg.cpp','build_graph.cpp']]))
for di,ds in enumerate(DS):
 old=read(E73/'inputs'/ds/'aux.json');variants=[read(O/'models'/ds/name/'model.json') for name in ['joint10']]
 global_model=read(E80/'models'/ds/'conditional10/model.json');global_model=dict(global_model,model_name='conditional10',name='conditional10_L128')
 methods=[dict(m) for m in old['methods'] if m['model_name'] in ['baseline10','compact10']]+[global_model]+variants
 for split,n in [('preflight',128),('aux',7952)]:
  c=dict(old,methods=methods,split='E81_historical_aux_'+split,num_queries=n,input_total_rows=7952,dataset_order=di,real_call_cap=4*(2*n+16),timing_repeats=0);dump(O/'inputs'/ds/(split+'.json'),c)
 paths += [Path(old[k]) for k in ['queries_file','gt_file','row_ids']]
 for m in methods[:3]:paths += [Path(m[k]) for k in ['W','mapping','tie_ids','graph_file']]
paths+=list((O/'inputs').rglob('*.json'))+[O/'bin/provenance.json',O/'reviews/phaseB_budget.json'];freeze(O/'reviews/prebuild_freeze.json',paths)
builds=[]
for ds in DS:
 for name in ['joint10']:
  folder=O/'models'/ds/name;m=read(folder/'model.json');assert not Path(m['graph_file']).exists();tick=time.monotonic()
  argv=[str(O/'bin/build_graph'),str(folder/'model.json'),m['graph_file']]
  with (O/'logs'/('build_'+ds+'_'+name+'.log')).open('x') as f:p=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,timeout=180)
  assert p.returncode==0,(ds,name)
  rec=read(O/'logs'/('build_'+ds+'_'+name+'.log'));rec.update(dataset=ds,model=name,seconds=time.monotonic()-tick,argv=argv,returncode=p.returncode)
  W=np.fromfile(m['W'],np.float32).reshape(m['hub_count'],m['dim']);rec['independent_graph']=inspect_serialized(m['graph_file'],W,np.arange(len(W)))
  builds.append(rec);paths.append(Path(m['graph_file']));dump(folder/'build.json',rec);resources()
dump(O/'results/builds.json',builds);freeze(O/'reviews/prequery_freeze.json',paths+[O/'results/builds.json']);dump(O/'logs/jobs.json',[])
dump(O/'state.json',dict(status='MODELS_BUILT_UNQUERIED',NSG=0,HNSW=0,builds=2,day_goal_complete=False));print('E81_QUERIES_READY',json.dumps(builds),flush=True)
