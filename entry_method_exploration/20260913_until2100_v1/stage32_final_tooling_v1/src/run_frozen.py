from contracts import *
import subprocess,argparse

def disk_guard(run,lock):
 used=sum(p.stat().st_size for p in run.rglob('*') if p.is_file() and not p.is_symlink());cap=lock['output_cap_MiB']*2**20;assert used<cap;assert lock['free_min_GiB']>=6.45;assert shutil.disk_usage('/data').free-(cap-used)-8*2**20>lock['free_min_GiB']*2**30

def main():
 ap=argparse.ArgumentParser(description='Run one dataset from a separately frozen final matrix. This tool does not select candidates or prepare final data.');ap.add_argument('run_directory');ap.add_argument('dataset',choices=DS);args=ap.parse_args();threads();run=Path(args.run_directory).resolve();lock,totals=validate_frozen(run);disk_guard(run,lock);ds=args.dataset
 jobsfile=run/'logs/jobs.json';jobs=read(jobsfile);assert all(j['status']=='COMPLETE' for j in jobs);assert not any(j['dataset']==ds for j in jobs);assert [j['dataset'] for j in jobs]==DS[:DS.index(ds)],'Datasets must run serially in locked order'
 remaining=sum(lock['dataset_operation_budget_seconds'][d] for d in DS if d not in [j['dataset'] for j in jobs]);assert time.time()<lock['latest_launch'] and time.time()+remaining<lock['query_stop'],'Insufficient reserved time for complete remaining matrix'
 cp=run/'inputs'/ds/'config.json';c=read(cp);out=run/'results'/ds;assert not out.exists();assert sum(j['reserved_NSG'] for j in jobs)+c['real_call_cap']<=lock['planned_NSG'];job=dict(dataset=ds,status='RUNNING',reserved_NSG=c['real_call_cap'],started_at=time.time(),peak_threads=0,peak_RSS_KiB=0);jobs.append(job);dump(jobsfile,jobs)
 with (run/'logs'/('native_'+ds+'.log')).open('x') as log:
  proc=subprocess.Popen([str(E73/'bin/evaluate'),str(cp),str(out)],stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy(),preexec_fn=lambda:os.sched_setaffinity(0,{15}));job['pid']=proc.pid;state=read(C/'state.json');state.update(status='FINAL_NATIVE_RUNNING',native_pids=[proc.pid],dataset=ds,final_run_directory=str(run));dump(C/'state.json',state)
  try:
   while proc.poll() is None:
    try:
     st=dict(s.split(':',1) for s in Path(f'/proc/{proc.pid}/status').read_text().splitlines() if ':' in s);job['peak_threads']=max(job['peak_threads'],int(st['Threads']));job['peak_RSS_KiB']=max(job['peak_RSS_KiB'],int(st.get('VmRSS','0 kB').split()[0]));job['affinity']=sorted(os.sched_getaffinity(proc.pid));assert job['peak_threads']<=1 and job['affinity']==[15]
    except FileNotFoundError:pass
    disk_guard(run,lock);assert time.time()<lock['query_stop'] and time.time()-job['started_at']<lock['per_job_seconds'] and job['peak_RSS_KiB']<32*2**20;dump(run/'logs/active.json',job)
    try:proc.wait(timeout=2)
    except subprocess.TimeoutExpired:pass
   assert proc.returncode==0 and job['peak_threads']==1;result=read(out/'results.json');assert result['physical_graph_calls']==c['real_call_cap'];assert not list(out.glob('*.hnsw'));job.update(status='COMPLETE',actual_NSG=result['physical_graph_calls'],seconds=time.time()-job['started_at'],completed_at=time.time(),returncode=0)
  except BaseException as exc:
   if proc.poll() is None:proc.kill();proc.wait()
   job.update(status='FAILED_RESERVED_RETAINED',error=repr(exc),seconds=time.time()-job['started_at'],returncode=proc.returncode);raise
  finally:
   dump(jobsfile,jobs);state=read(C/'state.json');state.update(status='FINAL_NATIVE_SAFE_BOUNDARY',native_pids=[],last_native_status=job['status']);dump(C/'state.json',state)
 print('FINAL_DATASET_COMPLETE',ds,job)
if __name__=='__main__':main()
