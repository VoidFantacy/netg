from pathlib import Path
import json,time,hashlib,subprocess,os,shutil
RUN=Path(__file__).resolve().parents[1];ROOT=RUN.parents[1];LOCK=json.loads((RUN/'config.locked.json').read_text())
def dump(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,indent=2)+'\n');tmp.replace(p)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''):h.update(b)
 return h.hexdigest()
def frozen_check():
 for p in json.loads((RUN/'reviews/protected_before.json').read_text()):assert sha(p['path'])==p['sha256'],p['path']
 for c in LOCK['datasets'].values():
  s=Path(c['index']).stat();assert s.st_size==c['index_stat']['bytes'] and s.st_mtime_ns==c['index_stat']['mtime_ns']
assert json.loads((RUN/'reviews/gt_complete.json').read_text())['status']=='PASS'
assert not(RUN/'reviews/source_freeze.json').exists(),'runner may not restart'
frozen_check();files=[p for p in (RUN/'src').rglob('*') if p.is_file() and '__pycache__' not in str(p)]+[RUN/'bin/evaluate',RUN/'config.locked.json',RUN/'protocol.md']
dump(RUN/'reviews/source_freeze.json',dict(created_unix=time.time(),files={str(p):sha(p) for p in files}))
env=os.environ.copy()
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:env[k]='1'
env['OMP_DYNAMIC']='FALSE';jobs=[];start=time.time()
def execute(config,out,kind):
 assert not out.exists();assert shutil.disk_usage(RUN).free>=LOCK['min_free_gib']*1024**3
 cp=RUN/'reviews'/('config_'+kind+'_'+config['dataset']+'.json');dump(cp,config);cmd=['taskset','-c','15',str(RUN/'bin/evaluate'),str(cp),str(out)]
 job=dict(kind=kind,dataset=config['dataset'],argv=cmd,config_sha256=sha(cp),started_unix=time.time(),reserved_calls=config['n']*2*len(config['points'])*(config['repeats']+2));jobs.append(job);dump(RUN/'reviews/jobs.json',jobs)
 assert sum(j['reserved_calls'] for j in jobs)<=LOCK['max_search_calls']
 with (RUN/'logs'/(kind+'_'+config['dataset']+'.log')).open('x') as log:
  p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env);job['pid']=p.pid;dump(RUN/'reviews/jobs.json',jobs)
  try:p.wait(timeout=max(1,LOCK['search_seconds_cap']-(time.time()-start)))
  except subprocess.TimeoutExpired:p.kill();p.wait();job['timeout']=True
 job.update(exit_code=p.returncode,finished_unix=time.time(),seconds=time.time()-job['started_unix']);dump(RUN/'reviews/jobs.json',jobs)
 assert p.returncode==0,dict(kind=kind,dataset=config['dataset'],exit_code=p.returncode)
 done=json.loads((out/'complete.json').read_text());assert done['search_calls']==job['reserved_calls'] and done['threads']==1
 job['complete']=done;dump(RUN/'reviews/jobs.json',jobs);print('COMPLETE',kind,config['dataset'],round(job['seconds'],1),flush=True)
try:
 configs=[]
 for order,(ds,c) in enumerate(LOCK['datasets'].items()):
  old=json.loads(Path(c['pilot_config']).read_text());parity=RUN/'reviews'/('parity_input_'+ds+'.f32');rows=list(range(0,2048,128));d=c['dimension']
  with Path(old['splits'][0]['queries']).open('rb') as f,parity.open('xb') as dst:
   for j in rows:f.seek(j*d*4);dst.write(f.read(d*4))
  methods=[c['anchor'],c['learner']];base_dir=ROOT/'benches/datasets'/('WebVid2.5M_light_v1' if ds.startswith('webvid') else 'YandexT2I_official10M_ip_v1')
  base=base_dir/('base.webvid2_5m.fvecs' if ds.startswith('webvid') else 'base.official_first10M.fvecs')
  common=dict(dataset=ds,index=c['index'],base=str(base),dimension=d,base_n=c['base_n'],threads=1,methods=methods,dataset_order=order,max_search_calls=LOCK['max_search_calls'],seconds_cap=LOCK['search_seconds_cap'])
  pc=dict(common,formal=False,n=16,queries=str(parity),points=[dict(K=k,L=128) for k in [1,100]],repeats=1,normalize_anchor=True,pilot_rows=rows,pilot_reference=str(Path(c['pilot_config']).parent))
  execute(pc,RUN/'reviews'/('parity_'+ds),'parity')
  fc=dict(common,formal=True,n=LOCK['n'],queries=str(RUN/'inputs'/ds/'queries.f32'),points=[dict(K=int(k),L=l) for k,ls in LOCK['L'].items() for l in ls],repeats=LOCK['repeats'],normalize_anchor=False)
  configs.append(fc)
 dump(RUN/'reviews/parity_gate.json',dict(status='PASS',datasets=2,old_E104_output_and_NDC_restored=True,calls=sum(j['reserved_calls'] for j in jobs)))
 dump(RUN/'state.json',dict(status='RUNNING_FORMAL',started_unix=start,pending_actions=['formal','analysis','documentation']))
 for c in configs:execute(c,RUN/'results'/c['dataset'],'formal')
 frozen_check();freeze=json.loads((RUN/'reviews/source_freeze.json').read_text())
 for p,s in freeze['files'].items():assert sha(p)==s,p
 dump(RUN/'reviews/search_complete.json',dict(status='PASS',seconds=time.time()-start,calls=sum(j['reserved_calls'] for j in jobs),formal_calls=sum(j['reserved_calls'] for j in jobs if j['kind']=='formal'),formal_rounds=sum(j['complete']['wall_rounds'] for j in jobs if j['kind']=='formal'),protected_unchanged=True))
 dump(RUN/'state.json',dict(status='SEARCH_COMPLETE',pending_actions=['analysis','documentation']))
except Exception as e:
 dump(RUN/'state.json',dict(status='STOP_EXECUTION_ERROR',error=repr(e),pending_actions=['inspect preserved failure']));raise
