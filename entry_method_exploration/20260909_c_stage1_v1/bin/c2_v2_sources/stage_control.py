#!/usr/bin/env python3
"""Gate, budget and provenance checks. This controller never opens GT."""
import datetime,hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
V=Path(__file__).resolve().parents[1];R=Path('/data/netg/ACSG')
def read(p):return json.loads(p.read_text())
def dump(p,j):p.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def verify_lock():
 lock=read(V/'protocol_lock.json')
 assert sha(V/'config.locked.json')==lock['config_sha256'] and sha(V/'protocol.md')==lock['protocol_sha256']
 for rec in lock['bound_files']:assert sha(Path(rec['path']))==rec['sha256'],rec['path']
 # Current method source is authoritative and must still match its pre-C snapshot.
 m=read(V/'source_manifest.json')
 for rec in m['protected_sources']:
  if rec['path'] in ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/09_research_designs_not_experiments.md']:continue
  assert sha(R/rec['path'])==rec['sha256'],rec['path']
 return lock
def call_upper_bound():
 total=512 # C0 native searches
 for name in ['c1_synthetic_v1','c1_synthetic_v2','c1_webvid_v2','c1_yandex_v2']:
  p=V/'results'/(name+'.json')
  if p.exists():
   j=read(p);total+=j.get('conservative_search_execution_upper_bound',2*j['native_or_branch_calls']+100)
   if 'action_edges' in j:total+=9
 total+=5 # Independent supplemental harness; exact reported separately.
 for p in (V/'results').glob('c2_*/complete.json'):total+=read(p)['physical_search_executions']
 return total
def c1_gate():
 verify_lock();names=['c1_synthetic_v2','c1_webvid_v2','c1_yandex_v2'];records=[]
 for name in names:
  p=V/'results'/(name+'.json');j=read(p);assert j['status']=='PASS';records.append({'path':str(p),'sha256':sha(p)})
 rev=read(V/'reviews/kernel_review.json');assert rev['status']=='PASS'
 code_sha=sha(V/'src/state_machine.hpp');assert rev['reviewed_state_machine_sha256']==code_sha
 build=read(V/'bin/parity_v2.build.json')
 assert build['binary_sha256']==sha(V/'bin/parity_v2')
 for rec in build['source_and_dependencies']:
  if rec['path'].endswith('/state_machine.hpp'):assert rec['sha256']==code_sha
 p=V/'reviews/kernel_supplemental_v1.json';assert read(p)['status']=='PASS'
 gate={'status':'PASS','utc':utc(),'state_machine_sha256':code_sha,'parity_files':records,
       'independent_review_sha256':sha(V/'reviews/kernel_review.json'),'supplement_sha256':sha(p),
       'C2_authorized_by_user':True,'C3_authorized':False,'calls_upper_bound_before_C2':call_upper_bound()}
 assert not (V/'results/c1_gate.json').exists();dump(V/'results/c1_gate.json',gate)
 s=read(V/'state.json');s.update({'status':'C1_PASS_C2_SMOKE_PENDING','C1':'PASS','C2':'AUTHORIZED_PENDING_SMOKE','state_machine_implemented':True});dump(V/'state.json',s)
 print(json.dumps(gate))
def disk_bytes():return sum(p.stat().st_size for p in V.rglob('*') if p.is_file())
def run_c2(label,ds,N):
 assert N in (4,2000) and label.startswith('c2_') and '/' not in label
 verify_lock();gate=read(V/'results/c1_gate.json');assert gate['status']=='PASS' and sha(V/'src/state_machine.hpp')==gate['state_machine_sha256']
 build=read(V/'bin/c2_v2.build.json');assert sha(V/'bin/c2_v2')==build['binary_sha256']
 for rec in build['source_and_dependencies']:
  if rec['path'].endswith('/state_machine.hpp'):assert rec['sha256']==gate['state_machine_sha256']
 if N==2000:
  smoke=read(V/'results/c2_smoke_gate.json');assert smoke['status']=='PASS'
 used=call_upper_bound();reservation=N*2*20
 assert used+reservation<=200000,(used,reservation)
 output=V/'results'/label;assert not output.exists();assert disk_bytes()<5*1024**3
 argv=[str(V/'bin/c2_v2'),str(V/'inputs'/ds/'config.json'),str(V/'config.locked.json'),str(output),str(N)]
 env=os.environ.copy();limits={k:'1' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']};env.update(limits)
 record={'label':label,'argv':argv,'cwd':str(R),'env_overrides':limits,'started_utc':utc(),'call_upper_bound_before':used,'call_reservation':reservation}
 with (V/'logs/commands.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
 prior_wall=sum(read(p)['wall_seconds'] for p in (V/'logs').glob('c2_*.command.json'))
 start=time.monotonic();peak=0;reason=None;last_disk=0
 with (V/'logs'/(label+'.log')).open('x') as log,(V/'logs'/(label+'.resources.jsonl')).open('x') as resource:
  p=subprocess.Popen(argv,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  while p.poll() is None:
   elapsed=time.monotonic()-start
   try:
    status=Path(f'/proc/{p.pid}/status').read_text();rss=int(next(x.split()[1] for x in status.splitlines() if x.startswith('VmRSS:')))*1024
   except (OSError,StopIteration):rss=0
   peak=max(peak,rss)
   if elapsed-last_disk>=10:
    last_disk=elapsed
    if disk_bytes()>5*1024**3:reason='new disk cap'
   if rss>32*1024**3:reason='RSS cap'
   if prior_wall+elapsed>7200:reason='cumulative C2 stage wall cap'
   resource.write(json.dumps({'utc':utc(),'elapsed_seconds':elapsed,'rss_bytes':rss})+'\n');resource.flush()
   if reason:os.killpg(p.pid,signal.SIGTERM);break
   time.sleep(2)
  rc=p.wait()
 record.update({'finished_utc':utc(),'wall_seconds':time.monotonic()-start,'exit_code':rc,'peak_rss_bytes':peak,'stop_reason':reason})
 dump(V/'logs'/(label+'.command.json'),record)
 with (V/'logs/commands.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
 assert rc==0 and not reason,record
 done=read(output/'complete.json');assert done['status']=='COMPLETE' and done['queries']==N and done['physical_search_executions']<=reservation
 print(json.dumps(record),flush=True)
def smoke_gate():
 records=[]
 for ds,label in [('webvid2_5m_light_v1','c2_smoke_webvid_v1'),('yandex_t2i_official10M_ip_v1','c2_smoke_yandex_v1')]:
  out=V/'results'/label;done=read(out/'complete.json');assert done['queries']==4 and done['rows']==8 and done['GT_accessed'] is False
  rows=[json.loads(s) for s in (out/'branches.jsonl').read_text().splitlines()];assert len(rows)==8
  ids=read(V/'inputs'/ds/'config.json');B=read(V/'config.locked.json')['B']
  for i,row in enumerate(rows):
   assert row['sample_index']==i//2 and row['L']==[64,128][i%2] and len(row['branches'])==9
   for b in row['branches']:
    assert b['suffix_graph_ndc']<=B and b['graph_ndc']==row['prefix_ndc']+b['suffix_graph_ndc']
    assert len(b['ids'])==len(b['distances'])==10 and b['natural_finished']!=b['cap_exhausted']
   assert (out/row['prefix_state']).exists()
  records.append({'directory':str(out),'complete_sha256':sha(out/'complete.json'),'raw_sha256':sha(out/'branches.jsonl')})
 dump(V/'results/c2_smoke_gate.json',{'status':'PASS','utc':utc(),'GT_accessed':False,'quality_viewed':False,'checks':records})
 print('C2_SMOKE_SCHEMA_BUDGET_PASS_GT_UNOPENED')
if __name__=='__main__':
 command,*args=sys.argv[1:]
 if command=='c1-gate':c1_gate()
 elif command=='c2-run':run_c2(args[0],args[1],int(args[2]))
 elif command=='smoke-gate':smoke_gate()
