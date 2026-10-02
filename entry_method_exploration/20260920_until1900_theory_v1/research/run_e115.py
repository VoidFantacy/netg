from pathlib import Path
import json,hashlib,subprocess,os,time,signal,shutil,struct
ROOT=Path('/data/netg/ACSG');TB=Path(__file__).resolve().parents[1];R=TB/'stages/e115_score_topology_factorial'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ident(p):
 p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
C=read(R/'config.locked.json');T=read(TB/'config.locked.json');jobs=[];started=time.time()
assert not (R/'reviews/execution_started.json').exists();assert ident(R/'protocol.md')==C['protocol']
for x in C['source_files']:assert ident(x['path'])==x,x['path']
def large_check():
 for x in C['large_files']:
  s=Path(x['path']).stat();assert s.st_size==x['bytes'] and s.st_mtime_ns==x['mtime_ns'],x['path']
large_check();dump(R/'reviews/execution_started.json',dict(started_unix=started,runner=ident(__file__),config=ident(R/'config.locked.json')))
def execute(argv,name,kind,timeout,calls=0,ann=0):
 assert time.time()<T['no_new_search_after_unix'] if calls else True
 assert time.time()+timeout+5<T['deadline_unix'];assert sum(j['reserved_NSG'] for j in jobs)+calls<=C['expected_diagnostic_NSG']
 assert shutil.disk_usage(R).free>=4*1024**3
 job=dict(argv=argv,kind=kind,started_unix=time.time(),timeout_seconds=timeout,reserved_NSG=calls,reserved_ANN=ann);jobs.append(job);dump(R/'reviews/jobs.json',jobs)
 with (R/'logs'/name).open('x') as f:
  p=subprocess.Popen(argv,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',OMP_DYNAMIC='FALSE'))
  job.update(pid=p.pid,pgid=os.getpgid(p.pid));dump(R/'reviews/jobs.json',jobs)
  try:p.wait(timeout=timeout)
  except subprocess.TimeoutExpired:
   assert os.getpgid(p.pid)==p.pid;os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=3)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
   job['timeout']=True
 job.update(exit_code=p.returncode,finished_unix=time.time(),seconds=time.time()-job['started_unix']);dump(R/'reviews/jobs.json',jobs);assert p.returncode==0,job
 return job
def masked_index(p,dim,ids,target):
 a=bytearray(Path(p).read_bytes());header=struct.unpack_from('<6QiI3QdQ',a,0);start=struct.calcsize('<6QiI3QdQ');offset0,maxel,n,row,label_offset,data_offset,maxlevel,ep,maxM,maxM0,M,mult,efc=header
 assert n==len(ids) and M==16 and efc==200 and data_offset+dim*4==label_offset
 for i,idv in enumerate(ids):
  pos=start+i*row;assert struct.unpack_from('<Q',a,pos+label_offset)[0]==idv
  assert bytes(a[pos+data_offset:pos+data_offset+dim*4])==target[i*dim*4:(i+1)*dim*4]
  a[pos+data_offset:pos+data_offset+dim*4]=b'\0'*(dim*4)
 return hashlib.sha256(a).hexdigest()
try:
 execute(C['compile_argv'],'compile.log','compile',120)
 pc=R/'reviews/prepare_config.json';dump(pc,dict(datasets=C['datasets']))
 execute(['taskset','-c','15',str(R/'bin/evaluate'),'prepare',str(pc),str(R/'reviews/hybrids_prepared.json')],'prepare.log','serialization',60)
 records=[];models=[]
 for ds in C['datasets']:
  for m in ds['methods']:
   if not m['hybrid']:continue
   b=Path(m['ids']).read_bytes();ids=struct.unpack('<'+'i'*(len(b)//4),b)
   before=masked_index(m['before'],ds['dimension'],ids,Path(m['source_W']).read_bytes());after=masked_index(m['graph'],ds['dimension'],ids,Path(m['W']).read_bytes());assert before==after
   models.extend([ident(m['before']),ident(m['graph'])]);records.append(dict(dataset=ds['dataset'],method=m['name'],all_nonvector_serialized_bytes_sha256=before,all_vector_rows=len(ids),external_IDs_verified=True))
 dump(R/'reviews/model_identity_gate.json',dict(status='PASS',records=records,files=models,ordinary_builds=0,hybrid_copies=4))
 freeze=[ident(p) for p in (R/'src').rglob('*') if p.is_file()]+[ident(R/'bin/evaluate'),ident(R/'config.locked.json'),ident(R/'protocol.md')]+models
 dump(R/'reviews/search_source_freeze.json',dict(created_unix=time.time(),files=freeze,query_computation_started=False))
 for smoke in [True,False]:
  for ds in C['datasets']:
   cfg=dict(ds,smoke=smoke,n=16 if smoke else 4096)
   if smoke:cfg['points']=[dict(K=k,L=128) for k in [1,100]]
   cfg['expected_NSG_calls']=cfg['n']*4*len(cfg['points'])*(3 if smoke else 1);cfg['expected_ANN_calls']=cfg['n']*4*(2 if smoke else 1)
   kind='smoke' if smoke else 'main';cp=R/'reviews'/(kind+'_'+ds['dataset']+'.json');dump(cp,cfg);out=R/('reviews' if smoke else 'results')/(kind+'_'+ds['dataset'])
   dump(R/'state.json',dict(status='RUNNING_'+kind.upper(),dataset=ds['dataset'],pending=['remaining four-cell matrix','analysis','decision']))
   j=execute(['taskset','-c','15',str(R/'bin/evaluate'),str(cp),str(out)],kind+'_'+ds['dataset']+'.log',kind,900 if not smoke else 120,cfg['expected_NSG_calls'],cfg['expected_ANN_calls'])
   done=read(out/'complete.json');assert done['NSG_calls']==cfg['expected_NSG_calls'] and done['ANN_calls']==cfg['expected_ANN_calls'] and done['threads']==1 and done['cpu']==15;j['complete']=done;dump(R/'reviews/jobs.json',jobs)
   assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<=C['max_new_bytes']
   assert sum(p.stat().st_size for root in [TB,Path(T['previous_phase'])] for p in root.rglob('*') if p.is_file())<=T['resources']['max_combined_new_bytes']
   print(kind,ds['dataset'],'PASS',round(j['seconds'],3),flush=True)
  if smoke:dump(R/'reviews/smoke_gate.json',dict(status='PASS',all_four_cells_linked_parity=True,original_two_controls_restored=True))
 for x in C['source_files']+freeze:assert ident(x['path'])==x,x['path']
 large_check();assert sum(j['reserved_NSG'] for j in jobs)==C['expected_diagnostic_NSG'];assert sum(j['reserved_ANN'] for j in jobs)==C['expected_diagnostic_ANN']
 dump(R/'reviews/diagnostic_complete.json',dict(status='PASS',NSG_calls=C['expected_diagnostic_NSG'],ANN_calls=C['expected_diagnostic_ANN'],seconds=time.time()-started,new_GT=0,new_training=0,ordinary_graph_builds=0,hybrid_router_copies=4,formal_QPS=False))
 dump(R/'state.json',dict(status='DIAGNOSTIC_COMPLETE',pending=['independent scoring','factorial attribution','candidate gate','report']))
 print('DIAGNOSTIC_COMPLETE',flush=True)
except Exception as e:
 dump(R/'state.json',dict(status='STOP_EXECUTION_ERROR',error=repr(e),pending=['inspect preserved error, no blind restart']));raise
