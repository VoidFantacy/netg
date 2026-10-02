import datetime,hashlib,json,os,pathlib,shutil,signal,struct,subprocess,time,traceback
D=pathlib.Path(__file__).resolve().parent.parent;R=D.parent.parent;E=D.parent/'20260916_shared_span_batch4_v1'
read=lambda p:json.loads(p.read_text())
def save(p,x):
 t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');t.replace(p)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(16*1024**2),b''):h.update(b)
 return h.hexdigest()
start=time.time();calls=0;done=[];child=None;next_hour=start+3600
lock=read(D/'config.locked.json');env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',MPLCONFIGDIR=str(D/'mplconfig'))
def state(status,**kw):save(D/'state.json',dict(status=status,pid=os.getpid(),completed_search_calls=calls,updated_at=datetime.datetime.now().astimezone().isoformat(),elapsed_seconds=time.time()-start,**kw))
def progress(ds):
 b=D/'results'/ds;r={}
 for name in ['progress.json','timing_progress.json']:
  p=b/name
  if p.exists():
   v=read(p)
   if isinstance(v,list):r.update(plain_rounds=len(v),latest_round=v[-1] if v else None)
   else:r.update(v)
 return r
try:
 assert read(D/'reviews/conditional_gate.json')['status']=='GO_FULL_REMEASUREMENT'
 assert read(D/'reviews/build.json')['returncode']==0 and read(D/'reviews/git_backup.json')['status']=='PASS'
 assert read(E/'reviews/final_review.json')['status']=='PASS'
 assert sha(D/'src/kernels.hpp')==sha(E/'src/kernels.hpp')
 assert not (D/'reviews/frozen.json').exists(),'new run only; no automatic retry'
 assert shutil.disk_usage(D).free>=lock['min_free_gib']*1024**3
 assert 15 in os.sched_getaffinity(0)
 for p in pathlib.Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:args=(p/'cmdline').read_bytes().split(b'\0')
  except OSError:continue
  assert not any(str(E/'bin'/n).encode() in args for n in ['compare','compatibility']),'E102 still running'
 state('PREFLIGHT')
 code=[p for f in ['src','bin','configs','inputs'] for p in (D/f).rglob('*') if p.is_file() and '__pycache__' not in p.parts]+[D/'config.locked.json',D/'protocol.md']+[D/'reviews'/n for n in ['conditional_gate.json','root_docs_start.json','build.json','git_backup.json','source_review.json','inherited_validation.json']]
 frozen={str(p):sha(p) for p in code};save(D/'reviews/frozen.json',frozen)
 protected=read(E/'reviews/protected.json')
 for name,h in protected.items():assert sha(pathlib.Path(name))==h,name
 for p in E.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts:protected[str(p)]=sha(p)
 save(D/'reviews/protected.json',protected)
 assets=set();cfgs=[]
 for ds in lock['datasets']:
  c=read(D/'configs'/f'{ds}.json');cfgs.append(c);assert c['threads']==1 and c['n']==(1000 if ds.startswith('gist') else 10000)
  assert c['points']==[dict(K=K,L=L) for K in [1,100] for L in lock['L'][str(K)]]
  assert [x['name'] for x in c['methods']]==lock['methods'] and len(c['variants'])==5
  for name,rows,dim in [('base',c['base_n'],c['dimension']),('queries',c['n'],c['dimension'])]:
   p=pathlib.Path(c[name]);assert p.stat().st_size==rows*(dim+1)*4
   with p.open('rb') as f:assert struct.unpack('<i',f.read(4))[0]==dim
  with open(c['gt'],'rb') as f:w=struct.unpack('<i',f.read(4))[0]
  assert w>=100 and pathlib.Path(c['gt']).stat().st_size==c['n']*(w+1)*4
  assets.update(c[k] for k in ['index','base','queries','gt','hnsw_complete','hnsw_topology'])
  for m in c['methods']:
   if m['name'] not in ['NSG','HNSW']:
    assets.update(m[k] for k in ['W','ids']);assets.add(str(pathlib.Path(c['reference_results'])/'k100'/(m['name']+'.hnsw')))
   for point in c['points']:
    ref=pathlib.Path(c['reference_results'])/f'k{point["K"]}'/(m['name']+f'_L{point["L"]}')
    assets.update(str(ref/n) for n in ['ids.i32','distances.f32','entry_ids.i32','route_ndc.u64','graph_ndc.u64'])
 identities={p:dict(bytes=pathlib.Path(p).stat().st_size,sha256=sha(pathlib.Path(p))) for p in sorted(assets)}
 prior=read(E/'reviews/assets.json')
 for name,x in identities.items():
  if name in prior:assert x==prior[name],name
 save(D/'reviews/assets.json',identities)
 backup=read(D/'reviews/git_backup.json');assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==backup['main_head_unchanged'];assert sha(R/'.git/index')==backup['index_unchanged_sha256']
 save(D/'reviews/preflight.json',dict(status='PASS',assets=len(identities),frozen_code_files=len(frozen),real_search_calls=32800000,points=800,plain_rounds=2400,threads=1,cpu=15,boot_id=pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip(),library_threads={k:env[k] for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']},git_backup=backup['commit']))
 for c in cfgs:
  ds=c['dataset'];out=D/'results'/ds;assert not out.exists();job_start=time.time()
  with (D/'logs'/f'{ds}.log').open('w') as log:
   child=subprocess.Popen(['taskset','-c','15',str(D/'bin/evaluate'),str(D/'configs'/f'{ds}.json'),str(out)],cwd=R,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   state('MEASURING',dataset=ds,child_pid=child.pid,completed_datasets=[x['dataset'] for x in done])
   while child.poll() is None:
    try:child.wait(timeout=60)
    except subprocess.TimeoutExpired:pass
    q=progress(ds);state('MEASURING',dataset=ds,child_pid=child.pid,completed_datasets=[x['dataset'] for x in done],dataset_progress=q)
    if time.time()>=next_hour:
     with (D/'logs/hourly_checks.jsonl').open('a') as f:f.write(json.dumps(dict(at=datetime.datetime.now().astimezone().isoformat(),dataset=ds,progress=q,completed_search_calls=calls))+'\n')
     next_hour+=3600
    assert time.time()-start<lock['max_total_seconds'],'24-hour limit'
    assert time.time()-job_start<43200,'12-hour dataset limit'
    assert shutil.disk_usage(D).free>=2*1024**3,'disk floor'
   assert child.returncode==0,(ds,child.returncode)
  result=read(out/'complete.json');assert result['status']=='PASS' and result['search_calls']==800*c['n'] and result['wall_rounds']==480 and result['actual_batch4_count']
  calls+=result['search_calls'];done.append(dict(dataset=ds,**result));save(D/'results/completed_datasets.json',done)
  save(D/'reviews'/f'stage_formal_{ds}.json',dict(stage='formal_'+ds,seconds=time.time()-job_start,status='PASS',log=str(D/'logs'/f'{ds}.log')))
 assert calls==32800000
 state('VERIFYING_IDENTITIES')
 for group in [frozen,protected]:
  for name,h in group.items():assert sha(pathlib.Path(name))==h,name
 for name,x in identities.items():assert pathlib.Path(name).stat().st_size==x['bytes'] and sha(pathlib.Path(name))==x['sha256'],name
 save(D/'reviews/post_run_identity.json',dict(status='PASS',assets=len(identities),protected_files=len(protected),code_files=len(frozen)))
 state('MEASUREMENTS_COMPLETE',wall_rounds=2400,points=800)
 for name in ['analyze.py','report.py','finish.py']:
  t=time.time()
  with (D/'logs'/name.replace('.py','.log')).open('w') as log:subprocess.run([str(R/'.venv_cpu/bin/python'),str(D/'src'/name)],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
  save(D/'reviews'/('stage_'+name.replace('.py','')+'.json'),dict(stage=name,seconds=time.time()-t,status='PASS',log=str(D/'logs'/name.replace('.py','.log'))))
 print('E103 complete: results scored, figures generated, analysis written; manual figure review pending.',flush=True)
except BaseException as ex:
 if child and child.poll() is None:
  os.killpg(child.pid,signal.SIGTERM)
  try:child.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
 state('FAILED',error=repr(ex),dataset_progress=progress(c['dataset']) if 'c' in globals() else {},completed_datasets=[x['dataset'] for x in done]);traceback.print_exc();raise
