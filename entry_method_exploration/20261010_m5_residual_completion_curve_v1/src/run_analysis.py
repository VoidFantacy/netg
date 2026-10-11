"""Execute frozen evaluation/audit/plot/report sequentially after formal closure."""
from pathlib import Path
import hashlib,json,os,subprocess,time
ROOT=Path(__file__).resolve().parents[1]
ENV=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',OMP_DYNAMIC='FALSE')
STAGES=[('evaluate.py','evaluation_execution.json'),('independent_audit.py','independent_audit_execution.json'),('plot_curves_v2.py','plot_curves_wrapper_execution.json'),('write_report.py','report_wrapper_execution.json')]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def stat(p):
 s=Path(p).stat();return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]
def stable(execution):
 for p,s in execution['input_stats'].items():assert stat(p)==s,'frozen analysis input changed '+p
def main():
 os.sched_setaffinity(0,{14})
 state=load(ROOT/'run_state.json')
 assert state['status']=='NATIVE_COMPLETE_PENDING_INDEPENDENT_GT_EVALUATION' and state.get('active') is None
 assert len(state['completed'])==2 and all(x['exit_code']==0 for x in state['completed'])
 execution=load(ROOT/'execution_lock.json')
 stable(execution)
 for p,h in execution['source_and_binary_sha256'].items():assert sha(p)==h,'frozen execution source changed '+p
 reviews=load(ROOT/'reviews/analysis_source_review.json')
 assert reviews['status'].startswith('PASS')
 assert set(reviews['source_sha256_at_review'])=={str(ROOT/'src'/s) for s,_ in STAGES}
 for p,h in reviews['source_sha256_at_review'].items():assert sha(p)==h
 for script,receipt_name in STAGES:
  receipt=ROOT/'reviews'/receipt_name;log=ROOT/'logs'/f'{script}.execution.log'
  assert not receipt.exists() and not log.exists(),'stage already attempted; preserve'
  argv=[str(ROOT.parents[1]/'.venv_cpu/bin/python'),str(ROOT/'src'/script)]
  started=time.monotonic()
  with log.open('x') as f:child=subprocess.run(argv,env=ENV,stdout=f,stderr=subprocess.STDOUT)
  record={'status':'PASS_E176_'+script[:-3].upper()+'_PROCESS' if child.returncode==0 else 'FAILED_E176_ANALYSIS_STAGE_PRESERVED',
   'argv':argv,'exit_code':child.returncode,'elapsed_seconds':time.monotonic()-started,'log':str(log),
   'source_sha256':sha(ROOT/'src'/script),'scope':'sequential post-native saved-output analysis, no concurrent ANN/FIT'}
  receipt.write_text(json.dumps(record,indent=2)+'\n')
  assert child.returncode==0,'analysis stage failed; preserve '+str(log)
  stable(execution)
  print(json.dumps({'script':script,'status':record['status'],'elapsed_seconds':record['elapsed_seconds']}),flush=True)
if __name__=='__main__':main()
