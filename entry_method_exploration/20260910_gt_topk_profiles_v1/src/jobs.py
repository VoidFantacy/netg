"""Sequential single-CPU evaluator launcher with pre-reserved real-search budgets."""
import os
import shutil
import subprocess
import time
from pathlib import Path
from common import ROOT, RUN, check_lock, dump, identity, read, sha


def model_method(dataset, model, L=128, exact=False, components=False):
    inp=RUN/'inputs'/dataset
    return {'name':model['name']+('_exact' if exact else '_hnsw')+f'_L{L}',
            'family':model['family'],'model_name':model['name'],'K_gt':model.get('K_gt'),
            'temperature':model.get('temperature'),'L':L,'seed':20260828,'hnsw_seed':20260828,
            'hub_count':read(inp/'prepared.json')['H'],'k':3,'W':model['W'],
            'mapping':str(inp/'hub_ids.i32'),'tie_ids':str(inp/'hub_ids.i32'),
            'slot_labels':False,'exact':exact,'legacy_heap_order':False,
            'canonical_entry_order':True,'component_wall':components}


def planned_calls(config):
    n=config['num_queries'];measured=config['measure_wall']
    return sum((3 if measured else 2)*n+32+(2*n if x.get('component_wall',False) else 0)
               for x in config['methods'])


def folder_bytes(folder):
    return sum(p.stat().st_size for p in Path(folder).rglob('*') if p.is_file())


def run_job(job_name, config, output, synthetic=False, repair=False):
    lock=check_lock()
    ledger_path=RUN/'reviews'/('synthetic_jobs.json' if synthetic else 'search_jobs.json')
    ledger=read(ledger_path) if ledger_path.exists() else []
    assert not any(x['status']=='RUNNING' for x in ledger),'one search job at a time'
    assert not any(x['name']==job_name for x in ledger),'refuse overwriting job evidence'
    calls=planned_calls(config)
    spent=sum(x['reserved_calls'] for x in ledger)
    cap=lock['synthetic_call_cap'] if synthetic else lock['total_real_call_cap']
    assert spent+calls<=cap, 'frozen call budget exhausted'
    if not synthetic:
        kind_spent=sum(x['reserved_calls'] for x in ledger if x.get('repair',False)==repair)
        assert kind_spent+calls<=lock['repair_real_call_cap' if repair else 'normal_real_call_cap']
    assert sum(x.get('process_seconds',0) for x in ledger)<lock['total_search_seconds']
    assert folder_bytes(RUN)<=lock['output_limit_bytes'],'new artifact cap exceeded'
    assert shutil.disk_usage(ROOT).free>=lock['min_free_bytes'],'free disk below limit'
    config={**config,'threads':1,'query_cpu':lock['query_cpu'],'real_call_cap':calls,
            'protocol_sha256':lock['protocol_sha256']}
    config_path=RUN/'configs'/f'{job_name}.json';assert not config_path.exists()
    dump(config_path,config)
    binary=RUN/'bin/evaluate';build=read(RUN/'bin/evaluate.build.json')
    assert sha(binary)==build['binary']['sha256']
    for mc in config['methods']:
        if 'W' in mc:
            assert Path(mc['W']).is_file() and Path(mc['mapping']).is_file()
    command=['taskset','-c',str(lock['query_cpu']),str(binary),str(config_path),str(output)]
    env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1',
         'OMP_DYNAMIC':'FALSE','MKL_DYNAMIC':'FALSE','NUMEXPR_NUM_THREADS':'1'}
    record={'name':job_name,'argv':command,'reserved_calls':calls,'synthetic':synthetic,
            'repair':repair,'status':'RUNNING','start_unix':time.time(),
            'config':identity(config_path),'binary_sha256':sha(binary),'cpu':lock['query_cpu']}
    ledger.append(record);dump(ledger_path,ledger)
    started=time.monotonic();max_rss=0;max_threads=0;stop_reason=None
    with (RUN/'logs'/f'{job_name}.log').open('w') as log:
        proc=subprocess.Popen(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        record['pid']=proc.pid;dump(ledger_path,ledger)
        dump(RUN/'state.json',{'status':'SEARCH_RUNNING','job':record,'validation_opened':config['split'].startswith('validation'),'heldout_opened':False})
        while proc.poll() is None:
            try:
                fields={k:v.strip() for k,v in (x.split(':',1) for x in Path(f'/proc/{proc.pid}/status').read_text().splitlines() if ':' in x)}
                rss=int(fields.get('VmRSS','0 kB').split()[0])*1024
                threads=int(fields.get('Threads','0'));max_rss=max(max_rss,rss);max_threads=max(max_threads,threads)
                if rss>lock['rss_limit_bytes']:stop_reason='RSS_LIMIT'
            except (FileNotFoundError,ProcessLookupError):
                pass
            if time.monotonic()-started>lock['job_timeout_seconds']:stop_reason='JOB_TIME_LIMIT'
            if sum(x.get('process_seconds',0) for x in ledger)+time.monotonic()-started>lock['total_search_seconds']:stop_reason='TOTAL_TIME_LIMIT'
            if stop_reason:
                proc.terminate()
                try:proc.wait(timeout=10)
                except subprocess.TimeoutExpired:proc.kill();proc.wait()
                break
            time.sleep(.2)
        rc=proc.wait()
    record.update({'exit_code':rc,'process_seconds':time.monotonic()-started,'max_observed_rss_bytes':max_rss,
                   'max_observed_process_threads':max_threads,'stop_reason':stop_reason,
                   'status':'COMPLETE' if rc==0 else 'FAILED_RESERVED_CALLS_RETAINED'})
    dump(ledger_path,ledger)
    assert rc==0,f'{job_name} failed; original output and reservation retained'
    result=read(Path(output)/'results.json')
    assert result['status']=='COMPLETE' and result['physical_graph_calls']==calls
    assert max_threads==1,'unexpected actual process thread count'
    assert read(Path(output)/'thread_contract.json')['process_threads']==1
    record['actual_calls']=result['physical_graph_calls'];record['results']=identity(Path(output)/'results.json')
    dump(ledger_path,ledger)
    assert folder_bytes(RUN)<=lock['output_limit_bytes'],'new artifact cap exceeded'
    print(job_name,'COMPLETE',calls,'calls',round(record['process_seconds'],2),'s',flush=True)
    return result
