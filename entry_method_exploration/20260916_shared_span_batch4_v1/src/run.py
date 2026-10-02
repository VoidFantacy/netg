import datetime, hashlib, json, os, pathlib, subprocess, time
D=pathlib.Path(__file__).resolve().parent.parent;R=D.parent.parent;P=D.parent/'20260916_faiss_nsg_comparison_v1'
def read(p):return json.loads(p.read_text())
def save(p,x):
 t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');t.replace(p)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
 return h.hexdigest()
start=time.time();calls=0;completed=[]
def state(status,**kw):save(D/'state.json',dict(status=status,pid=os.getpid(),search_calls=calls,updated_at=datetime.datetime.now().astimezone().isoformat(),**kw))
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
def run_job(binary,config,output,logname,timeout):
 assert not output.exists(),str(output)
 with (D/'logs'/logname).open('w') as log:
  proc=subprocess.Popen(['taskset','-c','15',str(D/'bin'/binary),str(config),str(output)],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  state('MEASURING' if binary=='compare' else 'CHECKING_COMPATIBILITY',dataset=read(config)['dataset'],child_pid=proc.pid)
  try:code=proc.wait(timeout=timeout)
  except subprocess.TimeoutExpired:proc.terminate();proc.wait();raise
 assert code==0,(binary,code)
 return read(output/'complete.json')
try:
 assert read(D/'reviews/git_backup.json')['status']=='PASS'
 assert read(D/'reviews/build.json')['returncode']==0
 assert read(D/'reviews/inherited_validation.json')['status']=='PASS'
 assert not (D/'reviews/frozen.json').exists(),'new run only'
 assert sha(D/'src/kernels.hpp')==sha(P/'src/kernels.hpp')
 assert sha(D/'bin/compatibility')==sha(P/'bin/compatibility')
 configs=[D/'configs'/f'{n}.json' for n in ['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1','deep10m_l2_v1','sift10m_bigann_l2_v1','gist1m_l2_v1']]
 state('FREEZING')
 files=[p for f in ['bin','configs','src/common'] for p in (D/f).rglob('*') if p.is_file()]+[D/'src'/n for n in ['compare.cpp','compatibility.cpp','kernels.hpp','run.py']]+[D/'protocol.md']
 frozen={str(p):sha(p) for p in files};save(D/'reviews/frozen.json',frozen)
 protected=read(P/'reviews/protected.json')
 for name,h in protected.items():assert sha(pathlib.Path(name))==h,name
 for p in P.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts:protected[str(p)]=sha(p)
 save(D/'reviews/protected.json',protected)
 assets=set()
 for i,cp in enumerate(configs):
  c=read(cp);assert c['threads']==1 and {p['K'] for p in c['points']}=={1,100}
  assets.update(c[k] for k in ['index','queries','gt'])
  if i==0:assets.update(c[k] for k in ['base','hnsw_topology','hnsw_complete'])
  for m in c['methods']:
   name=m['name']
   if name not in ['NSG','HNSW']:
    assets.update(m[k] for k in ['ids','W']);assets.add(str(pathlib.Path(c['reference_results'])/'k100'/(name+'.hnsw')))
   if i and name=='HNSW':continue
   for p in c['points']:
    ref=pathlib.Path(c['reference_e99'])/(name+('__reference' if name=='HNSW' else '__optimized')+f'_K{p["K"]}_L{p["L"]}')
    assets.update(str(ref/n) for n in ['ids.i32','distances.f32','entry_ids.i32','route_ndc.u64','graph_ndc.u64'])
 identities={p:{'bytes':pathlib.Path(p).stat().st_size,'sha256':sha(pathlib.Path(p))} for p in sorted(assets)};save(D/'reviews/assets.json',identities)
 prior=read(P/'reviews/assets.json')
 for group in read(P/'compatibility/assets.json').values():prior.update(group)
 for name,x in identities.items():
  if name in prior:assert x==prior[name],name
 save(D/'reviews/environment.json',{'boot_id':pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'cpu':15,'threads':1,'library_threads':{k:env[k] for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']},'started_at':datetime.datetime.fromtimestamp(start).astimezone().isoformat()})
 main=run_job('compare',configs[0],D/'results/webvid2_5m_light_v1','webvid.log',7200)
 assert main['status']=='PASS' and main['search_calls']==1800000 and main['wall_rounds']==108
 calls+=main['search_calls'];completed.append(dict(dataset='webvid2_5m_light_v1',**main));save(D/'results/completed_datasets.json',completed)
 for cp in configs[1:]:
  c=read(cp);done=run_job('compatibility',cp,D/'results'/c['dataset'],c['dataset']+'.log',1800)
  assert done['search_calls']==16*c['n'] and done['configurations']==16
  calls+=done['search_calls'];completed.append(dict(dataset=c['dataset'],**done));save(D/'results/completed_datasets.json',completed)
 assert calls==2296000
 state('VERIFYING_IDENTITIES')
 for group in [frozen,protected]:
  for name,h in group.items():assert sha(pathlib.Path(name))==h,name
 for name,x in identities.items():
  p=pathlib.Path(name);assert p.stat().st_size==x['bytes'] and sha(p)==x['sha256'],name
 save(D/'reviews/post_run_identity.json',{'status':'PASS','code_files':len(frozen),'protected_files':len(protected),'assets':len(identities)})
 state('MEASUREMENTS_COMPLETE',wall_rounds=108,seconds_total=time.time()-start,compatibility_status='PASS' if all(x['status']=='PASS' for x in completed[1:]) else 'COMPLETE_WITH_MISMATCH')
 for name in ['analyze.py','plot.py','report.py']:
  with (D/'logs'/name.replace('.py','.log')).open('w') as log:subprocess.run([str(R/'.venv_cpu/bin/python'),str(D/'src'/name)],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 save(D/'postprocess_state.json',{'status':'REPORTS_READY_FOR_MANUAL_REVIEW','real_search_calls':calls,'completed_at':datetime.datetime.now().astimezone().isoformat(),'manual_review':False})
 print('Measurements and automatic reports complete',flush=True)
except BaseException as e:
 state('FAILED',error=repr(e),seconds_total=time.time()-start);raise
