from common import *
import subprocess,shutil,resource
assert not (RUN/'reviews/search_source_freeze.json').exists(),'no runner restart'
protected_check();models=read(RUN/'reviews/models_frozen.json')
for f in models['files']:assert sha(f['path'])==f['sha256'],f['path']
files=[p for p in (RUN/'src').rglob('*') if p.is_file() and '__pycache__' not in str(p)]+[RUN/'bin/evaluate',RUN/'config.locked.json',RUN/'protocol.md',RUN/'research.md']
dump(RUN/'reviews/search_source_freeze.json',dict(created_unix=time.time(),files={str(p):sha(p) for p in files}))
start=time.time();jobs=[];methods=read(RUN/'models/methods.json');configs=[]
env=os.environ.copy();env['OMP_DYNAMIC']='FALSE'
def execute(c,out,kind):
    assert not out.exists();assert shutil.disk_usage(RUN).free>=LOCK['min_free_gib']*1024**3
    c['seconds_cap']=max(1,LOCK['search_seconds']-sum(x.get('seconds',0) for x in jobs))
    path=RUN/'reviews'/(kind+'_'+c['dataset']+'.config.json');dump(path,c)
    calls=c['n']*len(c['methods'])*4
    assert sum(x['reserved_calls'] for x in jobs)+calls<=LOCK['max_NSG_calls']
    cmd=['taskset','-c','15',str(RUN/'bin/evaluate'),str(path),str(out)]
    job=dict(kind=kind,dataset=c['dataset'],argv=cmd,reserved_calls=calls,started_unix=time.time());jobs.append(job);dump(RUN/'reviews/jobs.json',jobs)
    with (RUN/'logs'/(kind+'_'+c['dataset']+'.log')).open('x') as log:
        p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env);job['pid']=p.pid;dump(RUN/'reviews/jobs.json',jobs)
        try:p.wait(timeout=c['seconds_cap'])
        except subprocess.TimeoutExpired:p.kill();p.wait();job['timeout']=True
    job.update(exit_code=p.returncode,seconds=time.time()-job['started_unix'],finished_unix=time.time());dump(RUN/'reviews/jobs.json',jobs)
    assert p.returncode==0,job
    done=read(out/'complete.json');assert done['search_calls']==calls and done['threads']==1
    job['complete']=done;dump(RUN/'reviews/jobs.json',jobs);print(kind,c['dataset'],'complete',round(job['seconds'],2),flush=True)

try:
    for ds,c in LOCK['datasets'].items():
        gtmeta=read(c['evaluation_manifest']);assert sha(c['evaluation_queries'])==gtmeta['query_sha256'] and sha(c['evaluation_GT'])==gtmeta['GT_sha256']
        source=Path(c['evaluation_queries']).parent;source_manifest=read(source/'manifest.json')
        assert sha(c['source_rows'])==source_manifest['files']['source_rows.i64']
        # Revalidate the GT base before connecting it to new search outputs.
        assert sha(gtmeta['base'])==gtmeta['base_sha256']
        inp=RUN/'inputs'/ds;inp.mkdir(exist_ok=False)
        for name,src in [('queries.f32',c['evaluation_queries']),('gt.i32',c['evaluation_GT']),('source_rows.i64',c['source_rows'])]:shutil.copy2(src,inp/name)
        with (inp/'queries.f32').open('rb') as f:(inp/'smoke.f32').write_bytes(f.read(16*c['dimension']*4))
        config=dict(dataset=ds,dimension=c['dimension'],H=c['H'],n=4096,queries=str(inp/'queries.f32'),index=c['index'],base_n=c['base_n'],base=gtmeta['base'],threads=1,hub_ids=str(Path(c['fit_input'])/'hub_ids.i32'),methods=methods[ds],reference=c['evaluation_reference'],reference_method=c['default']['name'],max_search_calls=LOCK['max_NSG_calls'])
        dump(inp/'manifest.json',dict(created_unix=time.time(),n=4096,exposure='E105 exposed diagnostic/development queries; not new blind data',files={p.name:sha(p) for p in inp.iterdir() if p.is_file()},GT_base_sha256=gtmeta['base_sha256']))
        configs.append(config)
    for c in configs:execute(dict(c,n=16,queries=str(Path(c['queries']).parent/'smoke.f32')),RUN/'reviews'/('smoke_'+c['dataset']),'smoke')
    dump(RUN/'reviews/smoke_gate.json',dict(status='PASS',calls=sum(j['reserved_calls'] for j in jobs)))
    dump(RUN/'state.json',dict(status='RUNNING_MECHANISM',pending=['full mechanism outputs','independent analysis']))
    for c in configs:execute(c,RUN/'results'/c['dataset'],'main')
    protected_check()
    for p,s in read(RUN/'reviews/search_source_freeze.json')['files'].items():assert sha(p)==s,p
    assert sum(x['complete']['search_calls'] for x in jobs)==361856
    dump(RUN/'reviews/search_complete.json',dict(status='PASS',calls=361856,seconds=time.time()-start,child_seconds=sum(j['seconds'] for j in jobs),jobs=4,new_graph_builds=0,new_training=0,formal_QPS=False))
    dump(RUN/'state.json',dict(status='MECHANISM_SEARCH_COMPLETE',pending=['analysis','report','conditional next-stage decision']))
except Exception as e:
    dump(RUN/'state.json',dict(status='STOP_EXECUTION_ERROR',error=repr(e),pending=['inspect preserved error']))
    raise
