from pathlib import Path
import os,json,time,subprocess,signal,shutil,hashlib
R=Path(__file__).resolve().parents[1];TB=R.parents[1];OLD=TB.parent/'20260920_until1600_theory_v1'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(16<<20),b''):h.update(b)
    return h.hexdigest()
cfg=read(R/'config.locked.json');assert not (R/'reviews/job.json').exists()
def check():
    assert shutil.disk_usage(R).free>=cfg['min_free_gib']*2**30
    assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<=cfg['max_new_bytes']
    assert sum(p.stat().st_size for r in [OLD,TB] for p in r.rglob('*') if p.is_file())<=cfg['max_combined_bytes']
    for x in read(R/'reviews/protected_before.json'):assert sha(x['path'])==x['sha256']
    for c in cfg['datasets'].values():
        s=Path(c['index']).stat();assert s.st_size==c['index_stat']['bytes'] and s.st_mtime_ns==c['index_stat']['mtime_ns']
check();assert time.time()+cfg['wall_timeout_seconds']+5<cfg['deadline_unix']
env=os.environ.copy()
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:env[key]='1'
argv=['taskset','-c','15','/data/netg/ACSG/.venv_cpu/bin/python',str(R/'src/analyze.py')]
j=dict(argv=argv,started_unix=time.time(),kind='readonly_graph_numeric_audit',NSG_calls=0)
with (R/'logs/analysis.log').open('x') as f:
    p=subprocess.Popen(argv,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=env)
    j.update(pid=p.pid,pgid=os.getpgid(p.pid));dump(R/'reviews/job.json',j)
    try:p.wait(timeout=cfg['wall_timeout_seconds'])
    except subprocess.TimeoutExpired:
        assert os.getpgid(p.pid)==p.pid;os.killpg(p.pid,signal.SIGTERM)
        try:p.wait(timeout=3)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
        j['timed_out']=True
j.update(exit_code=p.returncode,seconds=time.time()-j['started_unix'],finished_unix=time.time());dump(R/'reviews/job.json',j)
assert p.returncode==0,j
check();print(json.dumps(j,indent=2));print((R/'results/summary.json').read_text())
