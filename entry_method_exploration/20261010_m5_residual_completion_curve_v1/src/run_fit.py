"""Two serial fitting pipelines; one additional 900s allowance per dataset."""
from pathlib import Path
import hashlib,json,os,subprocess,time
ROOT=Path(__file__).resolve().parents[1]
ENV=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
         NUMEXPR_NUM_THREADS='1',OMP_DYNAMIC='FALSE')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp')
 t.write_text(json.dumps(x,indent=2)+'\n');t.replace(p)
def execute(argv,remaining,log):
 before=time.monotonic()
 with log.open('x') as f:
  process=subprocess.Popen(argv,env=ENV,stdout=f,stderr=subprocess.STDOUT,
                           preexec_fn=lambda:os.sched_setaffinity(0,{15}))
  try:code=process.wait(timeout=remaining)
  except BaseException:
   process.terminate()
   try:process.wait(timeout=5)
   except subprocess.TimeoutExpired:process.kill();process.wait()
   raise
 return {'argv':argv,'exit_code':code,'elapsed_seconds':time.monotonic()-before,'log':str(log)}
def main():
 os.sched_setaffinity(0,{14})
 scope=load(ROOT/'fit_scope_lock.json');lock=load(ROOT/'fit_execution_lock.json')
 for p,h in lock['sha256'].items():assert sha(p)==h,'FIT source changed '+p
 assert sha(ROOT/'protocol.md')==scope['protocol_sha256']
 assert load(ROOT/'reviews/fit_preflight.json')['status'].startswith('PASS')
 state={'status':'RUNNING_SERIAL_FIT_900S_PER_DATASET','completed':[],'active':None,'started_unix':time.time()}
 save(ROOT/'fit_state.json',state)
 for ds in scope['datasets']:
  job_path=ROOT/'fit_jobs'/f'{ds}.json';assert sha(job_path)==scope['jobs'][str(job_path)]
  job=load(job_path);start=time.monotonic();stages=[]
  state['active']={'dataset':ds,'phase':'native_original_M5_training_responses'};save(ROOT/'fit_state.json',state)
  try:
   native=execute([str(ROOT/'bin/fit'),str(job_path)],900-(time.monotonic()-start),ROOT/'logs'/f'fit.{ds}.native.log')
   stages.append(native);assert native['exit_code']==0,'training response generation failed'
   remaining=900-(time.monotonic()-start);assert remaining>0,'additional dataset budget exhausted'
   state['active']['phase']='residual_pair_and_route_table_compilation';save(ROOT/'fit_state.json',state)
   compiler=execute([str(ROOT.parents[1]/'.venv_cpu/bin/python'),str(ROOT/'src/compile_residual.py'),
                     str(job_path),'--max-seconds',str(remaining)],remaining,ROOT/'logs'/f'fit.{ds}.compiler.log')
   stages.append(compiler);assert compiler['exit_code']==0,'residual compilation failed'
   elapsed=time.monotonic()-start;assert elapsed<=900,'shared extra budget exceeded'
   manifest=load(Path(job['models_out'])/'compile_manifest.json')
   assert manifest['status']=='FROZEN_TRAIN_ONLY_POST_M5_RESIDUAL_COMPLETION_ALL_10_POINTS'
   receipt={'dataset':ds,'status':'PASS_ADDITIONAL_FIT_COMPLETE_WITHIN_900S','stages':stages,
     'elapsed_seconds':elapsed,'cap_seconds':900,'historical_TRAIN_seconds':job['historical_TRAIN_seconds'],
     'cumulative_TRAIN_with_this_increment_seconds':job['historical_TRAIN_seconds']+elapsed,
     'historical_cost_reset':False,'model_manifest':str(Path(job['models_out'])/'compile_manifest.json'),
     'model_manifest_sha256':sha(Path(job['models_out'])/'compile_manifest.json'),
     'model_eligible':True,'full_process_lifecycle_included':True}
   save(ROOT/'reviews'/f'fit_execution.{ds}.json',receipt);state['completed'].append(receipt)
  except BaseException as error:
   state['status']='FAILED_FIT_PARTIAL_PRESERVED';state['error']=repr(error)
   state['failed_dataset']={'dataset':ds,'stages':stages,'elapsed_seconds':time.monotonic()-start,'model_eligible':False}
   state['active']=None;save(ROOT/'fit_state.json',state);raise
  state['active']=None;save(ROOT/'fit_state.json',state)
 state['status']='FIT_COMPLETE_ALL_MODELS_FROZEN';state['finished_unix']=time.time();save(ROOT/'fit_state.json',state)
 print(json.dumps({'status':state['status'],'elapsed_seconds':[x['elapsed_seconds'] for x in state['completed']]}))
if __name__=='__main__':main()
