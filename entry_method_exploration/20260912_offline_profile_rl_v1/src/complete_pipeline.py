from common import *
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--training-pid',type=int);args=parser.parse_args()
logfile=O/'logs/continuation.json';assert not logfile.exists(),'refuse duplicate continuation controller'
events=[]
if args.training_pid:
 procpath=Path(f'/proc/{args.training_pid}/stat');assert procpath.exists(),'training process not live at attachment'
 start_ticks=procpath.read_text().split()[21];dump(logfile,dict(status='WAITING_FOR_LIVE_TRAINING',pid=args.training_pid,start_ticks=start_ticks))
 while procpath.exists():
  try:
   fields=procpath.read_text().split()
   if fields[21]!=start_ticks or fields[2]=='Z':break
  except FileNotFoundError:break
  time.sleep(2)
assert read(O/'state.json')['status']=='TRAINING_COMPLETE_VERIFICATION_PENDING'
for stage,timeout in [('audit_training',1800),('deploy',7200),('analyze',1800)]:
 if stage=='analyze':
  vendor=R/'entry_method_exploration/20260911_gt10_shared_transform_v1/src/vendor'
  freeze(O/'reviews/before_analysis.json',[O/'src/analyze.py',O/'src/common.py']+[p for p in vendor.rglob('*.py') if p.is_file()])
 argv=['taskset','-c','8',str(R/'.venv_cpu/bin/python'),str(O/'src'/f'{stage}.py')]
 rec=dict(stage=stage,status='RUNNING',start=time.time(),argv=argv);events.append(rec);dump(logfile,dict(status='RUNNING',events=events))
 with (O/'logs'/f'{stage}.log').open('x') as f:
  p=subprocess.Popen(argv,env=env(),stdout=f,stderr=subprocess.STDOUT);rec['pid']=p.pid;dump(logfile,dict(status='RUNNING',events=events))
  try:p.wait(timeout=timeout)
  except subprocess.TimeoutExpired:p.kill();p.wait();rec['timeout']=True
 rec.update(exit_code=p.returncode,seconds=time.time()-rec['start'],status='COMPLETE' if p.returncode==0 else 'FAILED');dump(logfile,dict(status=rec['status'],events=events))
 assert p.returncode==0,'see '+str(O/'logs'/f'{stage}.log')
 print('PIPELINE_STAGE_COMPLETE',stage,rec['seconds'],flush=True)
dump(logfile,dict(status='ANALYSIS_COMPLETE_REPORT_AUDIT_PENDING',events=events))
