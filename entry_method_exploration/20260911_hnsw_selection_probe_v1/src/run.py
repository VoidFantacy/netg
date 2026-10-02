from common import *
assert read(O/'state.json')['status']=='PREPARED';check(O/'reviews/before_queries.json')
jobs=[]
for ds in DS:
 assert shutil.disk_usage(O).free>=10*(1<<30)
 c=O/'inputs'/ds/'config.json';out=O/'results'/ds;log=O/'logs'/(ds+'.log');t=time.time();peak=0;threads=0
 with log.open('x') as f:
  p=subprocess.Popen([str(O/'bin/probe'),str(c),str(out)],env=env(),stdout=f,stderr=subprocess.STDOUT)
  while p.poll() is None:
   try:
    vals=dict(line.split(':',1) for line in Path(f'/proc/{p.pid}/status').read_text().splitlines() if ':' in line)
    peak=max(peak,int(vals.get('VmRSS','0 kB').split()[0]));threads=max(threads,int(vals['Threads']))
   except FileNotFoundError:pass
   if time.time()-t>1200 or peak>40*(1<<20) or threads>1:p.kill();p.wait();raise RuntimeError('resource stop')
   time.sleep(.1)
 assert p.returncode==0,log
 done=read(out/'complete.json');assert done['NSG_calls']==7600
 jobs.append(dict(dataset=ds,seconds=time.time()-t,peak_RSS_KiB=peak,peak_threads=threads,**done));dump(O/'reviews/jobs.json',jobs)
 print(ds,'COMPLETE',jobs[-1]['seconds'],flush=True)
dump(O/'state.json',dict(status='QUERY_COMPLETE_ANALYSIS_PENDING',new_NSG_calls=15200,HNSW_calls=3072,training_calls=0,QPS_calls=0,validation_read=False,heldout_read=False))
