from common import *
import subprocess
import signal
import shutil

lock = read(RUN/'config.locked.json')
assert not (RUN/'reviews/started.json').exists(), 'No automatic retry'
os.sched_setaffinity(0,{15})
preserve_check()
frozen = [identity(p) for p in (RUN/'src').rglob('*') if p.suffix in ['.py','.cpp','.hpp','.h']]
frozen += [identity(p) for p in (RUN/'models').rglob('*') if p.is_file()]
frozen += [identity(RUN/'protocol.md'),identity(RUN/'config.locked.json')]
dump(RUN/'reviews/started.json',dict(files=frozen,created_unix=time.time()))
jobs = []
start = time.monotonic()
def execute(argv,name,native=False):
    record = dict(name=name,argv=argv,started_unix=time.time())
    jobs.append(record)
    with (RUN/'logs'/f'{name}.log').open('x') as log:
        p = subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
            env=dict(os.environ,OMP_DYNAMIC='FALSE'))
        record.update(pid=p.pid)
        dump(RUN/'reviews/jobs.json',jobs)
        tasks_max=rss_max=0
        try:
            while p.poll() is None:
                assert time.time()-record['started_unix'] < (1800 if native else 120)
                assert time.monotonic()-start < 3720
                assert shutil.disk_usage(RUN).free > 6*(1<<30)
                if native:
                    path=Path('/proc')/str(p.pid)/'status'
                    if path.exists():
                        status=dict(s.split(':',1) for s in path.read_text().splitlines() if ':' in s)
                        tasks=int(status['Threads']);rss=int(status.get('VmRSS','0 kB').split()[0])
                        tasks_max=max(tasks_max,tasks);rss_max=max(rss_max,rss)
                        assert tasks==1 and os.sched_getaffinity(p.pid)=={15}
                        assert rss<40*(1<<20)
                time.sleep(.1)
        except BaseException:
            if p.poll() is None:
                os.killpg(p.pid,signal.SIGTERM)
                p.wait(timeout=10)
            record.update(exit_code=p.returncode,interrupted=True)
            dump(RUN/'reviews/jobs.json',jobs)
            raise
    record.update(exit_code=p.returncode,seconds=time.time()-record['started_unix'],actual_max_threads=tasks_max,maxrss_kib=rss_max)
    dump(RUN/'reviews/jobs.json',jobs)
    assert p.returncode==0, f'{name} failed; inspect log, preserve all outputs'
    print('DONE',name,round(record['seconds'],2),flush=True)

try:
    old_build = read(OLD/'reviews/jobs_v2.json')[0]['argv']
    build = [arg.replace(str(OLD/'src'),str(RUN/'src')).replace(str(OLD/'bin/evaluate'),str(RUN/'bin/benchmark')) for arg in old_build]
    build = [str(RUN/'src/benchmark.cpp') if arg==str(RUN/'src/evaluate.cpp') else arg for arg in build]
    build.insert(1,'-I/usr/include/x86_64-linux-gnu/openblas-pthread')
    execute(build,'build')
    dump(RUN/'reviews/binary.json',identity(RUN/'bin/benchmark'))
    for ds,cfg in lock['datasets'].items():
        stat=Path(cfg['native']['index']).stat()
        assert dict(bytes=stat.st_size,mtime_ns=stat.st_mtime_ns)==cfg['graph_stat']
        path=RUN/'reviews'/f'{ds}.json'
        dump(path,cfg)
        dump(RUN/'state.json',dict(status='TIMING',completed=False,dataset=ds,pending=['remaining_points','analysis','docs']))
        execute([str(RUN/'bin/benchmark'),str(path),str(RUN/'results'/ds)],ds,True)
    preserve_check()
    for item in frozen:
        assert identity(item['path'])==item
    assert sum(read(RUN/'results'/ds/'complete.json')['calls'] for ds in lock['datasets'])==lock['expected_calls']
    dump(RUN/'state.json',dict(status='MEASUREMENTS_COMPLETE',completed=False,active_processes=[],pending=['analysis','docs']))
except BaseException as error:
    dump(RUN/'state.json',dict(status='ERROR',completed=False,error=repr(error),pending=['diagnose preserved attempt']))
    raise
