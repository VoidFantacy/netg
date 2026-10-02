from common import *
assert read(O/'state.json')['status']=='TRAINING_READY'
freeze(O/'reviews/training_controller.json',[Path(__file__)])
t=time.time();peak=0;nt=0
with (O/'logs/training.log').open('x') as f:
 p=subprocess.Popen([str(R/'.venv_cpu/bin/python'),str(O/'src/train.py')],env=env(),stdout=f,stderr=subprocess.STDOUT)
 while p.poll() is None:
  try:
   a=dict(line.split(':',1) for line in Path(f'/proc/{p.pid}/status').read_text().splitlines() if ':' in line);peak=max(peak,int(a.get('VmRSS','0 kB').split()[0]));nt=max(nt,int(a['Threads']))
  except FileNotFoundError:pass
  if time.time()-t>7260 or peak>40*(1<<20) or nt>1:p.kill();p.wait();raise RuntimeError('training resource cap')
  time.sleep(.2)
dump(O/'reviews/training_job.json',dict(exit_code=p.returncode,seconds=time.time()-t,peak_RSS_KiB=peak,peak_threads=nt,NSG_calls=0));assert p.returncode==0,'training.log'
assert read(O/'state.json')['status']=='TRAINING_COMPLETE_VERIFY_PENDING';print('TRAINING_PROCESS_COMPLETE',time.time()-t,flush=True)
