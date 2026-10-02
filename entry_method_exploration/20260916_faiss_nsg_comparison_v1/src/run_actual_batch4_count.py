import pathlib,subprocess,os,json,time,hashlib,datetime
D=pathlib.Path(__file__).resolve().parent.parent;R=D.parent.parent
assert json.loads((D/'postprocess_state.json').read_text())['status']=='REPORTS_READY_FOR_MANUAL_REVIEW'
flags=json.loads((D/'reviews/build.json').read_text())[0]['command'];pos=flags.index(str(D/'src/regression.cpp'));cmd=flags[:pos]+[str(D/'src/actual_batch4_count.cpp')]+flags[pos+1:];cmd[-1]=str(D/'bin/actual_batch4_count')
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1');start=time.time()
with (D/'logs/build_actual_batch4_count.log').open('w') as f:subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[D/'src/actual_batch4_count.cpp',D/'src/kernels.hpp',D/'src/run_actual_batch4_count.py',D/'bin/actual_batch4_count',D/'config.json',D/'actual_batch4_count_protocol.md']
frozen={str(p):sha(p) for p in paths};(D/'reviews/actual_batch4_count_frozen.json').write_text(json.dumps(frozen,indent=2)+'\n')
with (D/'logs/actual_batch4_count.log').open('w') as f:
 p=subprocess.Popen(['taskset','-c','15',str(D/'bin/actual_batch4_count'),str(D/'config.json'),str(D/'results/actual_batch4_count')],env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
 (D/'reviews/actual_batch4_count_process.json').write_text(json.dumps({'pid':p.pid,'runner_pid':os.getpid(),'started_at':datetime.datetime.now().astimezone().isoformat()},indent=2)+'\n')
 try:code=p.wait(timeout=1800)
 except subprocess.TimeoutExpired:p.terminate();p.wait();raise
 assert code==0,code
for name,h in frozen.items():assert sha(pathlib.Path(name))==h,name
x=json.loads((D/'results/actual_batch4_count/complete.json').read_text());assert x['status']=='PASS' and x['search_calls']==80000;x['compile_and_run_seconds']=time.time()-start
(D/'reviews/actual_batch4_count_audit.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(x),flush=True)
