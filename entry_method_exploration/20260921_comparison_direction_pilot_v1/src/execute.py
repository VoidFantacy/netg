"""Serial native jobs with process identity, resource guards and immutable inputs."""
from common import *
import subprocess,signal,fcntl

class Executor:
    def __init__(self,stage):
        self.stage=stage;self.start=time.time()
        self.global_start=read(RUN/'reviews/stage1_started.json')['unix'] if (RUN/'reviews/stage1_started.json').exists() else self.start
        self.lock=(RUN/'reviews/controller.lock').open('a+')
        fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        self.jobs=read(RUN/'reviews/jobs.json') if (RUN/'reviews/jobs.json').exists() else []
        # A surviving native child blocks another controller, including across parent death.
        for job in self.jobs:
            if 'exit_code' not in job and job.get('pid'):
                p=Path(f"/proc/{job['pid']}/cmdline")
                if p.exists() and str(RUN/'bin/experiment').encode() in p.read_bytes():
                    raise RuntimeError(f"prior native process is still alive: {job['pid']}")
        dump(RUN/'reviews'/f'{stage}_started.json',dict(pid=os.getpid(),unix=self.start,boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()))
    def check(self):
        assert shutil.disk_usage(RUN).free>=LOCK['min_free_gib']*1024**3
        for c in LOCK['datasets'].values():
            st=Path(c['index']).stat();assert st.st_size==c['index_stat']['bytes'] and st.st_mtime_ns==c['index_stat']['mtime_ns']
        for x in read(RUN/'reviews/native_frozen.json')['files']:assert ident(x['path'])==x
        assert sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())<=LOCK['max_new_bytes']
    def execute(self,cfg,out,kind):
        self.check();out=Path(out)
        cp=RUN/'reviews'/f"config_{kind}_{cfg.get('dataset','synthetic')}.json"
        if cp.exists():assert read(cp)==cfg
        else:dump(cp,cfg)
        if (out/'complete.json').exists():
            assert read(out/'config.json')==cfg and read(out/'complete.json')['status']=='PASS'
            return read(out/'complete.json')
        argv=['taskset','-c','15',str(RUN/'bin/experiment'),str(cp),str(out)]
        job=dict(kind=kind,dataset=cfg.get('dataset','synthetic'),argv=argv,started_unix=time.time(),stage=self.stage)
        attempt=sum(j['kind']==kind and j['dataset']==job['dataset'] for j in self.jobs)
        self.jobs.append(job);dump(RUN/'reviews/jobs.json',self.jobs)
        logpath=RUN/'logs'/f'{kind}_{job["dataset"]}_attempt{attempt}.log'
        samples=[]
        with logpath.open('x') as log:
            p=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy(),start_new_session=True)
            job.update(pid=p.pid,pgid=os.getpgid(p.pid),log=str(logpath));dump(RUN/'reviews/jobs.json',self.jobs)
            try:
                while p.poll() is None:
                    try:p.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        sp=Path(f'/proc/{p.pid}/status')
                        if not sp.exists():continue
                        data=dict(line.split(':',1) for line in sp.read_text().splitlines() if ':' in line)
                        rss=int(data.get('VmRSS','0 kB').split()[0])*1024;threads=int(data['Threads']);free=shutil.disk_usage(RUN).free
                        samples.append(dict(unix=time.time(),pid=p.pid,rss=rss,threads=threads,free_bytes=free,cpu=data['Cpus_allowed_list'].strip()))
                        dump(RUN/'reviews'/f'resources_{kind}_{job["dataset"]}_attempt{attempt}.json',samples)
                        assert rss<=LOCK['maxrss_gib']*1024**3 and threads==1 and data['Cpus_allowed_list'].strip()=='15'
                        assert free>=LOCK['min_free_gib']*1024**3 and time.time()-job['started_unix']<cfg['seconds_cap']
                        assert time.time()-self.global_start<LOCK['seconds_cap']
            except BaseException as err:
                job['error']=repr(err)
                if p.poll() is None:
                    os.killpg(p.pid,signal.SIGTERM)
                    try:p.wait(timeout=3)
                    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
                raise
            finally:
                job.update(exit_code=p.returncode,seconds=time.time()-job['started_unix'],finished_unix=time.time())
                dump(RUN/'reviews/jobs.json',self.jobs)
        assert p.returncode==0,(kind,job['dataset'],p.returncode,logpath.read_text()[-2000:])
        job['complete']=read(out/'complete.json');dump(RUN/'reviews/jobs.json',self.jobs);self.check()
        # Resumed labels report inherited calls separately; count actual new calls for this process.
        assert sum(j.get('complete',{}).get('new_search_calls',j.get('complete',{}).get('search_calls',0)) for j in self.jobs)<=LOCK['max_search_calls']
        print('COMPLETE',kind,job['dataset'],round(job['seconds'],2),flush=True)
        return job['complete']

def freeze_native():
    paths=[p for p in (RUN/'src').rglob('*') if p.is_file() and p.suffix in ('.cpp','.hpp','.h')]
    paths += [RUN/'bin/experiment',RUN/'config.locked.json',RUN/'protocol.md']
    build=read(RUN/'reviews/build.json')
    paths += [Path(s) for s in build['argv'] if s.endswith('.a')]
    frozen=dict(created_unix=time.time(),files=[ident(p) for p in dict.fromkeys(paths)])
    out=RUN/'reviews/native_frozen.json'
    if out.exists():
        for x in read(out)['files']:assert ident(x['path'])==x
    else:dump(out,frozen)
