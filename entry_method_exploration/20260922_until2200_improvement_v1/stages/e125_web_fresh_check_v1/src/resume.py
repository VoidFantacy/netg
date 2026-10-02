from pathlib import Path
import os,time,json,subprocess,hashlib,shutil
R=Path(__file__).resolve().parents[1];ROOT=Path('/data/netg/ACSG');C=json.loads((R/'config.locked.json').read_text());start=time.perf_counter();jobs={}
def dump(p,x):assert not p.exists(),p;p.write_text(json.dumps(x,indent=2)+'\n')
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
dump(R/'reviews/resume_frozen.json',{'unix':time.time(),'file':ident(Path(__file__)),'reason':'monitor checked taskset before affinity was applied; original startup exited before evaluator created output, zero search calls'})
big={}
for k in ['index','base']:
 p=Path(C['datasets']['webvid2_5m_light_v1'][k]);s=p.stat();big[str(p)]={'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
def run(name,argv,nthreads=1,cpu=None):
 assert time.time()<C['deadline_unix'] and shutil.disk_usage(R).free>6*2**30
 env=os.environ.copy();env.update({k:str(nthreads) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']});env['OMP_DYNAMIC']='FALSE'
 t=time.perf_counter();mt=0;mr=0
 with (R/'logs'/f'{name}.log').open('x') as log:
  p=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT)
  try:
   while p.poll() is None:
    try:
     rows=Path(f'/proc/{p.pid}/status').read_text().splitlines();st={r.split(':',1)[0]:r.split(':',1)[1].strip() for r in rows if ':' in r};mt=max(mt,int(st['Threads']));mr=max(mr,int(st.get('VmRSS','0 kB').split()[0])*1024)
     exe=Path(f'/proc/{p.pid}/cmdline').read_bytes().split(b'\0')[0].decode()
     if cpu is not None and exe==str(R/'bin/evaluate'): assert int(st['Threads'])==1 and st['Cpus_allowed_list']==str(cpu)
    except FileNotFoundError:pass
    if time.time()>C['deadline_unix']:raise TimeoutError('frozen deadline')
    time.sleep(.25)
  except BaseException:
   p.terminate();p.wait(timeout=10);raise
  code=p.wait()
 job={'exit_code':code,'seconds':time.perf_counter()-t,'max_threads':mt,'maxrss_bytes':mr,'argv':argv};dump(R/'reviews'/f'{name}.job.json',job);jobs[name]=job;assert code==0,(name,code);print(name,'PASS',round(job['seconds'],3),flush=True)
py=str(ROOT/'.venv_cpu/bin/python')
for name in ['prepare','exact_gt','compile']:jobs[name]=json.loads((R/'reviews'/f'{name}.job.json').read_text())
run('evaluate_resume',['taskset','-c','15',str(R/'bin/evaluate'),str(R/'evaluate.json'),str(R/'results/evaluation')],1,15)
for p,i in json.loads((R/'reviews/models_before_source.json').read_text())['files'].items():assert ident(Path(p))==i
for p,v in big.items():s=Path(p).stat();assert {'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}==v
q=json.loads((R/'results/evaluation/complete.json').read_text());assert q['search_calls']==40992 and q['wall_rounds']==6 and q['threads']==1
dump(R/'reviews/jobs_complete.json',{'status':'PASS','seconds':time.perf_counter()-start,'jobs':jobs,'new_NSG_calls':40992,'new_ANN_calls':40960,'new_exact_GT_queries':4096,'independent_float64_GT_queries':8,'models_unchanged':True,'large_stat_unchanged':big,'default_changed':False});print('ALL COMPLETE',flush=True)
