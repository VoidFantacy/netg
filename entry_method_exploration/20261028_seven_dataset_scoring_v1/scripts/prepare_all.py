import os,json,subprocess,time,sys,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];PY=REPO/'.venv_cpu/bin/python'
order=['coco','flickr30k','deep10m_l2_v1','gist1m_l2_v1','sift10m_bigann_l2_v1','webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
def job(ds):
 t=time.perf_counter();peak=threads=0
 with (R/f'reviews/prepare_aux_{ds}.log').open('x') as f:
  def pin():os.sched_setaffinity(0,set(range(8)))
  p=subprocess.Popen([str(PY),str(R/'scripts/prepare_aux.py'),ds],cwd=REPO,stdout=f,stderr=subprocess.STDOUT,preexec_fn=pin)
  while p.poll() is None:
   try:
    d={s.split(':',1)[0]:s.split(':',1)[1].strip() for s in Path(f'/proc/{p.pid}/status').read_text().splitlines() if ':' in s};peak=max(peak,int(d.get('VmRSS','0 kB').split()[0])*1024);threads=max(threads,int(d.get('Threads','0')))
   except FileNotFoundError:pass
   time.sleep(.25)
 rec=dict(dataset=ds,returncode=p.returncode,seconds=time.perf_counter()-t,peak_sampled_rss_bytes=peak,max_observed_threads=threads,scope='offline preparation, not QPS');(R/f'reviews/prepare_aux_{ds}.receipt.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps(rec),flush=True);assert p.returncode==0
for ds in order:
 assert shutil.disk_usage('/').free>.7*2**30
 job(ds)
 subprocess.run([str(PY),str(R/'scripts/run_native.py'),'prepare',ds],cwd=REPO,check=True)
 subprocess.run([str(PY),str(R/'scripts/run_native.py'),'qualification',ds],cwd=REPO,check=True)
print('ALL_SEVEN_PREPARED_AND_QUALIFIED',flush=True)
