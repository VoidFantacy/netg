"""Durable postprocessing only: no new searches, builds, or parameter selection."""
import json,pathlib,subprocess,time,os,sys,datetime
D=pathlib.Path(__file__).resolve().parent.parent
P='/data/netg/ACSG/.venv_cpu/bin/python'
def status(phase,**extra):
 p=D/'postprocess_state.json';t=p.with_suffix('.tmp')
 t.write_text(json.dumps({'phase':phase,'timestamp':datetime.datetime.now().isoformat(),**extra},indent=2)+'\n');t.replace(p)
status('WAITING_FOR_FROZEN_MEASUREMENTS')
while True:
 try:s=json.loads((D/'state.json').read_text())
 except (FileNotFoundError,json.JSONDecodeError):s={}
 if s.get('status')=='MEASUREMENTS_COMPLETE':break
 if s.get('status')=='VALIDATION_FAILED':status('STOPPED_MEASUREMENT_FAILED',details=s);sys.exit(1)
 # Original runner identity is checked rather than trusting PID alone.
 try:cmd=pathlib.Path('/proc/269421/cmdline').read_bytes()
 except FileNotFoundError:cmd=b''
 if b'run_validation.py' not in cmd:status('STOPPED_RUNNER_EXITED_WITHOUT_COMPLETE',details=s);sys.exit(1)
 time.sleep(30)
# Give the query process a chance to exit and make sure no native benchmark remains.
for pid in pathlib.Path('/proc').iterdir():
 if not pid.name.isdigit():continue
 try:args=(pid/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if str(D/'bin/benchmark').encode() in args:status('STOPPED_NATIVE_PROCESS_STILL_PRESENT');sys.exit(1)
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',MPLCONFIGDIR=str(D/'reviews/mplconfig'))
for name in ['postprocess.py','plot_results.py','check_plot_files.py','write_report.py','close_docs.py','close_artifacts.py']:
 status('POSTPROCESSING',script=name)
 with (D/'logs'/f'{name}.log').open('w') as f:
  rc=subprocess.run(['taskset','-c','0',P,str(D/'src'/name)],env=env,stdout=f,stderr=subprocess.STDOUT).returncode
 if rc:status('POSTPROCESS_FAILED',script=name,returncode=rc);sys.exit(rc)
status('COMPLETE_RESULTS_REPORT_PLOTS',manual_visual_review=False)
