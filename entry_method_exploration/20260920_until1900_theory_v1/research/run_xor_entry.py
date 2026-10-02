from pathlib import Path
import json,subprocess,time,os,signal,hashlib
TB=Path(__file__).resolve().parents[1];R=TB/'research/xor_entry_expressivity_v1';OLD=TB/'research/query_branch_stability_v1'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not (R/'jobs.json').exists();c=read(R/'config.locked.json');jobs=[]
for x in c['sources']:assert hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()==x['sha256']
argv=read(OLD/'config.locked.json')['compile_argv'];argv=[str(R/'verify.cpp') if a==str(OLD/'verify.cpp') else str(R/'verify') if a==str(OLD/'verify') else a for a in argv];assert str(R/'verify.cpp') in argv and str(R/'verify') in argv
def run(a,kind,timeout):
 assert time.time()+timeout+5<c['deadline_unix'];assert kind!='synthetic' or time.time()<c['no_new_search_after_unix']
 j=dict(argv=a,kind=kind,started_unix=time.time(),timeout_seconds=timeout);jobs.append(j)
 with (R/(kind+'.log')).open('x') as f:
  p=subprocess.Popen(a,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1'));j.update(pid=p.pid,pgid=os.getpgid(p.pid));dump(R/'jobs.json',jobs)
  try:p.wait(timeout=timeout)
  except subprocess.TimeoutExpired:
   os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=3)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
   j['timeout']=True
 j.update(exit_code=p.returncode,seconds=time.time()-j['started_unix'],finished_unix=time.time());dump(R/'jobs.json',jobs);assert p.returncode==0,j
run(argv,'compile',120)
dump(R/'binary_pre_run.json',dict(binary_sha256=hashlib.sha256((R/'verify').read_bytes()).hexdigest(),created_unix=time.time(),source_sha256=hashlib.sha256((R/'verify.cpp').read_bytes()).hexdigest()))
run(['taskset','-c','15',str(R/'verify'),str(R/'result.json')],'synthetic',30)
print(json.dumps({k:v for k,v in read(R/'result.json').items() if k not in ['base','edges','observations']},indent=2))
