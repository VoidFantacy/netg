"""Wait for the existing benchmark, then compile/run compatibility and reports."""
import pathlib,subprocess,time,os,json,hashlib,datetime,sys
D=pathlib.Path(__file__).resolve().parent.parent;R=D.parent.parent;X=D/'compatibility';E=D.parent/'20260916_nsg_search_optimization_v1'
def read(p):return json.loads(p.read_text())
def save(p,x):
 t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(x,indent=2)+'\n');t.replace(p)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
 return h.hexdigest()
def state(**x):save(X/'state.json',dict(x,pid=os.getpid(),updated_at=datetime.datetime.now().astimezone().isoformat()))
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',MPLCONFIGDIR=str(D/'reviews/mplconfig'))
start=time.time();initial=read(D/'state.json');parent_pid=initial.get('pid');parent_cmd=pathlib.Path('/proc')/str(parent_pid)/'cmdline'
try:
 state(status='WAITING_FOR_EXISTING_MAIN',main_pid=parent_pid)
 if initial['status']!='MEASUREMENTS_COMPLETE':
  assert parent_cmd.exists() and any(pathlib.Path(os.fsdecode(a)).resolve()==D/'src/run.py' for a in parent_cmd.read_bytes().split(b'\0') if a),'main process missing before wait'
  while parent_cmd.exists() and parent_cmd.read_bytes():
   assert time.time()-start<10800,'main wait timeout'
   time.sleep(10)
  assert read(D/'state.json')['status']=='MEASUREMENTS_COMPLETE',read(D/'state.json')
 assert read(D/'results/benchmark/complete.json')['status']=='PASS'
 for path in pathlib.Path('/proc').iterdir():
  if not path.name.isdigit():continue
  try:args=(path/'cmdline').read_bytes().split(b'\0')
  except OSError:continue
  assert str(D/'bin/compare').encode() not in args,'benchmark still live'
 state(status='BUILDING_COMPATIBILITY');buildstart=time.time()
 flags=['c++','-std=c++17','-O3','-g','-march=native','-fopenmp','-fPIC','-I'+str(R/'build/_deps/json-src/include'),'-I'+str(D/'src'),'-I'+str(D/'src/common'),'-I'+str(R),'-I'+str(R/'faiss')]
 libs=[str(E/'bin/libACSG.optimized.a'),str(R/'build/faiss/faiss/libfaiss.a'),str(R/'build/MRNN_Descent/libmrnndescent.a'),'-lopenblas','-llapack','-lz','-lpthread','-ldl']
 cmd=flags+[str(D/'src/compatibility.cpp'),*libs,'-o',str(D/'bin/compatibility')]
 with (D/'logs/build_compatibility.log').open('w') as f:subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
 save(X/'build.json',{'command':cmd,'seconds':time.time()-buildstart})
 frozen={str(p):sha(p) for p in [D/'src/compatibility.cpp',D/'src/kernels.hpp',D/'src/finish_pipeline.py',D/'bin/compatibility',X/'protocol.md',*(X/'configs').glob('*.json')]};save(X/'frozen.json',frozen)
 runstart=time.time();calls=0;records=[];identities={}
 datasets=['yandex_t2i_official10M_ip_v1','deep10m_l2_v1','sift10m_bigann_l2_v1','gist1m_l2_v1']
 for name in datasets:
  cp=X/f'configs/{name}.json';c=read(cp);paths={pathlib.Path(c[k]) for k in ['index','queries','gt']}
  for m in c['methods']:
   if m['name']=='HNSW':continue
   if m['name']!='NSG':paths.update(pathlib.Path(m[k]) for k in ['ids','W']);paths.add(pathlib.Path(c['reference_results'])/'k100'/(m['name']+'.hnsw'))
   for pt in c['points']:
    rp=pathlib.Path(c['reference_e99'])/(m['name']+f'__optimized_K{pt["K"]}_L{pt["L"]}')
    paths.update(rp/n for n in ['ids.i32','distances.f32','entry_ids.i32','route_ndc.u64','graph_ndc.u64'])
  state(status='FREEZING_DATASET',dataset=name,search_calls=calls)
  frozen_assets={str(p):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(paths)};identities[name]=frozen_assets;save(X/'assets.json',identities)
  with (D/f'logs/compatibility_{name}.log').open('w') as f:
   proc=subprocess.Popen(['taskset','-c','15',str(D/'bin/compatibility'),str(cp),str(X/'results'/name)],env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
   state(status='CHECKING',dataset=name,search_calls=calls,child_pid=proc.pid)
   try:code=proc.wait(timeout=3600)
   except subprocess.TimeoutExpired:proc.terminate();proc.wait();raise
  assert code==0,(name,code)
  rec=read(X/'results'/name/'complete.json');assert rec['status'] in ['PASS','COMPLETE_WITH_MISMATCH'];calls+=rec['search_calls'];assert calls<=500000
  records.append(dict(dataset=name,**rec))
  for p,v in frozen_assets.items():assert pathlib.Path(p).stat().st_size==v['bytes'] and sha(pathlib.Path(p))==v['sha256'],p
  save(X/'completed_datasets.json',records)
 assert calls==496000
 for p,h in frozen.items():assert sha(pathlib.Path(p))==h,p
 mismatch=sum(x['mismatched_configurations'] for x in records)
 save(X/'complete.json',{'status':'PASS' if not mismatch else 'COMPLETE_WITH_MISMATCH','search_calls':calls,'configurations':64,'mismatched_configurations':mismatch,'seconds_including_load_and_identity':time.time()-runstart,'datasets':records,'new_formal_qps':0})
 state(status='COMPATIBILITY_COMPLETE',search_calls=calls,mismatched_configurations=mismatch)
 for script in ['analyze.py','plot.py','write_report.py']:
  with (D/'logs'/f'{script}.log').open('w') as f:subprocess.run([sys.executable,str(D/'src'/script)],env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
 save(D/'postprocess_state.json',{'status':'REPORTS_READY_FOR_MANUAL_REVIEW','compatibility_status':read(X/'complete.json')['status'],'real_search_calls':2496000,'main_points':40,'main_plain_rounds':120,'completed_at':datetime.datetime.now().astimezone().isoformat(),'manual_review':False})
 print(json.dumps(read(D/'postprocess_state.json')),flush=True)
except Exception as e:
 state(status='FAILED',error=str(e));raise
