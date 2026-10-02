"""Bounded serial missing-budget measurements; never resumes an old runner."""
from common import *
import difflib
import shutil
import signal
import subprocess

lock = read(RUN/'config.locked.json')
assert not (RUN/'reviews/execution_started.json').exists(), 'Preserve previous execution'
os.sched_setaffinity(0, {15})
protected_check()
oldtext = (OLD/'src/evaluate.cpp').read_text()
newtext = (RUN/'src/evaluate.cpp').read_text()
assert oldtext.replace('L>=K&&L<=800', 'L>=K&&L<=1250', 1) == newtext
for p in (RUN/'src').rglob('*'):
    if p.suffix in ['.cpp','.hpp'] and p.name != 'evaluate.cpp':
        assert sha(p) == sha(OLD/'src'/p.relative_to(RUN/'src'))
dump(RUN/'reviews/source_diff.json', dict(diff=list(difflib.unified_diff(oldtext.splitlines(),newtext.splitlines())), kernel_changed=False))
frozen = [identity(p) for p in (RUN/'src').rglob('*') if p.suffix in ['.py','.cpp','.hpp']]
frozen += [identity(RUN/p) for p in ['protocol.md','config.locked.json']]
dump(RUN/'reviews/execution_started.json', dict(created_unix=time.time(),files=frozen))
start = time.time()
jobs = []

def execute(argv, label, timeout, reserved=0, native=False):
    assert shutil.disk_usage(RUN).free >= lock['min_free_gib']*(1<<30)
    assert sum(j['reserved_calls'] for j in jobs)+reserved <= lock['max_NSG_calls']
    record = dict(argv=argv, name=label, started_unix=time.time(), reserved_calls=reserved)
    jobs.append(record)
    dump(RUN/'reviews/jobs.json',jobs)
    with (RUN/'logs'/f'{label}.log').open('x') as log:
        p = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT,
            env=dict(os.environ,OMP_DYNAMIC='FALSE'), start_new_session=True)
        record.update(pid=p.pid, pgid=os.getpgid(p.pid))
        dump(RUN/'reviews/jobs.json',jobs)
        max_tasks = 0
        max_rss = 0
        try:
            while p.poll() is None:
                assert time.time()-record['started_unix'] <= timeout, 'job timeout'
                assert time.time()-start <= lock['total_search_seconds_cap']+120, 'total timeout'
                if native:
                    proc = Path('/proc')/str(p.pid)
                    if (proc/'status').exists():
                        status = dict(line.split(':',1) for line in (proc/'status').read_text().splitlines() if ':' in line)
                        tasks = int(status['Threads'])
                        rss = int(status.get('VmRSS','0 kB').split()[0])
                        max_tasks, max_rss = max(max_tasks,tasks), max(max_rss,rss)
                        assert tasks == 1, 'actual native threads'
                        assert os.sched_getaffinity(p.pid) == {15}, 'native affinity'
                        assert rss <= lock['max_rss_gib']*(1<<20), 'RSS cap'
                time.sleep(.1)
        except BaseException:
            if p.poll() is None:
                assert os.getpgid(p.pid) == p.pid
                os.killpg(p.pid, signal.SIGTERM)
                try:
                    p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid, signal.SIGKILL)
                    p.wait()
            record.update(exit_code=p.returncode, interrupted=True, seconds=time.time()-record['started_unix'])
            dump(RUN/'reviews/jobs.json',jobs)
            raise
    record.update(exit_code=p.returncode,seconds=time.time()-record['started_unix'],
        observed_max_tasks=max_tasks,observed_max_rss_kib=max_rss)
    dump(RUN/'reviews/jobs.json',jobs)
    assert p.returncode == 0, f'{label}: inspect preserved log'
    print('DONE',label,round(record['seconds'],2),'seconds',flush=True)
    return record

try:
    build = [arg.replace(str(OLD),str(RUN)) for arg in read(OLD/'reviews/jobs.json')[0]['argv']]
    execute(build,'build',120)
    binary = identity(RUN/'bin/evaluate')
    dump(RUN/'reviews/binary.json',binary)
    calls = 0
    search_start = time.time()
    for smoke in [True,False]:
        for ds, cfg in lock['datasets'].items():
            current = dict(cfg['native'])
            points = {K:sorted(set(Ls+([128] if smoke else []))) for K,Ls in cfg['missing'].items()}
            current.update(n=16 if smoke else 4096,smoke=smoke,K_L=points,
                deadline_unix=search_start+lock['total_search_seconds_cap'],seconds_cap=lock['job_seconds_cap'],
                max_search_calls=lock['max_NSG_calls'])
            count = current['n']*len(current['methods'])*sum(map(len,points.values()))*(3 if smoke else 2)
            current['expected_search_calls'] = count
            label = ('smoke_' if smoke else 'main_')+ds
            path = RUN/'reviews'/f'{label}.json'
            output = RUN/('reviews' if smoke else 'results')/label
            dump(path,current)
            dump(RUN/'state.json',dict(status='RUNNING_'+('SMOKE' if smoke else 'MISSING_BUDGETS'),
                completed=False,dataset=ds,pending=['remaining_points','response_analysis','conditional_information','audit_report_docs']))
            job = execute([str(RUN/'bin/evaluate'),str(path),str(output)],label,lock['job_seconds_cap'],count,True)
            done = read(output/'complete.json')
            assert done['calls'] == count and done['threads'] == 1 and done['cpu'] == 15
            assert job['observed_max_tasks'] == 1
            job['complete'] = done
            dump(RUN/'reviews/jobs.json',jobs)
            calls += count
            for method in current['methods']:
                a = np.fromfile(output/method['name']/'entries.i32','<i4').reshape(current['n'],3)
                b = np.fromfile(OLD/'results'/('main_'+ds)/method['name']/'entries.i32','<i4').reshape(4096,3)
                assert np.array_equal(a,b[:current['n']]), 'all-budget entry identity'
            assert sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file()) <= lock['max_new_bytes']
        if smoke:
            dump(RUN/'reviews/smoke_gate.json',dict(status='PASS',old_and_target_budget_native_parity=True))
    assert calls == lock['planned_NSG_calls']
    assert time.time()-search_start <= lock['total_search_seconds_cap']
    protected_check()
    for item in frozen+[binary]:
        assert identity(item['path']) == item
    dump(RUN/'reviews/search_complete.json',dict(status='PASS',calls=calls,
        seconds=time.time()-start,query_job_seconds=sum(j['seconds'] for j in jobs if j['reserved_calls']),
        formal_QPS=False,default_changed=False))
    dump(RUN/'state.json',dict(status='MEASUREMENTS_COMPLETE',completed=False,
        active_processes=[],pending=['response_analysis','conditional_information_control','audit_report_docs']))
except BaseException as error:
    dump(RUN/'state.json',dict(status='EXECUTION_ERROR',completed=False,error=repr(error),
        pending=['inspect owned process and preserved error before any retry']))
    raise
