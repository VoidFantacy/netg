from pathlib import Path
import json,hashlib,shutil,subprocess,os,time,signal
TB=Path(__file__).resolve().parents[1];ROOT=Path('/data/netg/ACSG');R=TB/'research/router_work_identity_v1';E=TB/'stages/e115_score_topology_factorial'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
assert not (R/'config.locked.json').exists();assert read(E/'complete.json')['status']=='COMPLETE'
shutil.copy2(TB/'research/router_work_protocol.md',R/'protocol.md');shutil.copytree(E/'src/common/hnswlib',R/'hnswlib')
s=(TB/'research/router_work_main.cpp').read_text();assert s.count('// OBSERVED_METHOD_INSERT')==1;s=s.replace('// OBSERVED_METHOD_INSERT',(R/'observed_method.txt').read_text());(R/'evaluate.cpp').write_text(s)
datasets=[];sources=[ident(E/'complete.json'),ident(E/'config.locked.json'),ident(R/'protocol.md')]
for ds in read(E/'config.locked.json')['datasets']:
    x={k:ds[k] for k in ['dataset','dimension','H','queries']};x['methods']=[];sources.append(ident(ds['queries']))
    for m in ds['methods']:
        a={k:m[k] for k in ['name','W','ids','graph']};a['reference']=str(E/'results'/('main_'+ds['dataset'])/'k1'/(m['name']+'_L128'));x['methods'].append(a)
        sources.extend(ident(a[k]) for k in ['W','ids','graph']);sources.extend(ident(Path(a['reference'])/k) for k in ['entry_ids.i32','route_ndc.u64'])
    datasets.append(x)
sources.extend(ident(p) for p in R.rglob('*') if p.is_file());sources.extend([ident(__file__),ident(TB/'research/router_work_main.cpp')])
cfg=dict(datasets=datasets,ANN_calls=65536,NSG_calls=0,no_new_search_after_unix=1789901400,deadline_unix=1789902000,threads=1,cpu=15,source_files=sources);dump(R/'config.locked.json',cfg)
jobs=[]
def run(argv,kind,timeout):
    assert time.time()+timeout+5<cfg['deadline_unix'];assert kind!='routing' or time.time()<cfg['no_new_search_after_unix'];assert shutil.disk_usage(R).free>4*1024**3
    j=dict(argv=argv,kind=kind,started_unix=time.time(),timeout_seconds=timeout);jobs.append(j)
    with (R/(kind+'.log')).open('x') as f:
        p=subprocess.Popen(argv,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1'))
        j.update(pid=p.pid,pgid=os.getpgid(p.pid));dump(R/'jobs.json',jobs)
        try:p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGTERM)
            try:p.wait(timeout=3)
            except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
            j['timeout']=True
    j.update(exit_code=p.returncode,seconds=time.time()-j['started_unix'],finished_unix=time.time());dump(R/'jobs.json',jobs);assert p.returncode==0,j
run(['g++','-O3','-march=native','-std=c++17','-pthread','-I'+str(ROOT/'build/_deps/json-src/single_include'),str(R/'evaluate.cpp'),'-o',str(R/'evaluate')],'compile',120)
dump(R/'binary_pre_run.json',dict(binary=ident(R/'evaluate'),source=ident(R/'evaluate.cpp'),created_unix=time.time()))
run(['taskset','-c','15',str(R/'evaluate'),str(R/'config.locked.json'),str(R/'results')],'routing',120)
print(json.dumps(read(R/'results/complete.json'),indent=2))
