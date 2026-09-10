#!/usr/bin/env python3
"""Event-wait for the current evaluation, then compare NSG/Fast/A+B together."""
import hashlib
import json
import os
import select
import signal
import subprocess
import time
from pathlib import Path

import run_models_eval as runner

OUT=Path(__file__).resolve().parents[1]
RUN=OUT/'baseline_comparison_v1'
ROOT=OUT.parents[1]
WAIT_PID=5513
WAIT_START_TICKS='91040'
CHOSEN={'fast30k_3','fast20k_3','joint'}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8<<20),b''):h.update(block)
    return h.hexdigest()


def dump(path,obj):Path(path).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')


def ticks(pid):
    try:
        fields=Path(f'/proc/{pid}/stat').read_text().split(') ',1)[1].split()
        return None if fields[0]=='Z' else fields[19]
    except FileNotFoundError:return None


def synthetic_acceptance():
    config=json.loads((OUT/'reviews/synthetic_benchmark_single_thread_config.json').read_text())
    for L in [64,128]:
        config['methods'].append({'name':f'nsg_medoid_L{L}','family':'nsg_medoid','L':L,'seed':20260828,'k':1})
    path=OUT/'reviews/synthetic_with_nsg_config.json';assert not path.exists();dump(path,config)
    dest=OUT/'reviews/synthetic_with_nsg'
    runner.command('nsg_synthetic_benchmark',[OUT/'bin/benchmark_single_thread_nsg',path,dest],threads=1)
    result=json.loads((dest/'results.json').read_text())
    assert result['status']=='COMPLETE' and result['threads']==1 and len(result['methods'])==16
    count=0
    for old in (OUT/'reviews/synthetic_benchmark_single_thread').glob('*/*'):
        if old.is_file() and old.suffix in ['.u8','.u16','.u32','.i32','.i64','.f32']:
            assert old.read_bytes()==(dest/old.relative_to(OUT/'reviews/synthetic_benchmark_single_thread')).read_bytes()
            count+=1
    for metric in result['methods']:
        if metric['name'].startswith('nsg_medoid'):
            assert metric['mean_route_ndc']==0 and metric['configuration']['k']==1
            assert not (dest/(metric['name']+'.hnsw')).exists()
    runner.command('nsg_synthetic_native_parity',[OUT/'bin/nsg_native_parity',path,OUT/'reviews/nsg_native_synthetic'],threads=1)
    assert json.loads((OUT/'reviews/nsg_native_synthetic/acceptance.json').read_text())['status']=='PASS'
    bad=dict(config);bad['threads']=2
    badpath=OUT/'reviews/nsg_reject_threads2.json';dump(badpath,bad)
    rejected=OUT/'reviews/nsg_multithread_must_not_exist'
    proc=subprocess.run([str(OUT/'bin/benchmark_single_thread_nsg'),str(badpath),str(rejected)],capture_output=True,text=True)
    assert proc.returncode!=0 and 'requires explicit threads=1' in proc.stderr and not rejected.exists()
    dump(OUT/'reviews/nsg_synthetic_acceptance.json',{'status':'PASS','prior_query_output_files_identical':count,
        'actual_threads':1,'fixed_entry_reference_checks':32,'multithread_rejected':True,'NSG_router_ndc':0})


def main():
    source_names=['src/benchmark_with_nsg.cpp','src/benchmark_single_thread_nsg.cpp','src/nsg_native_parity.cpp',
                  'src/run_baseline_comparison_after_single.py','src/analyze_baseline_comparison.py','baseline_comparison_amendment.md']
    hashes={name:sha(OUT/name) for name in source_names}
    assert ticks(WAIT_PID)==WAIT_START_TICKS, 'registered single-thread controller not live'
    descriptor=os.pidfd_open(WAIT_PID)
    assert ticks(WAIT_PID)==WAIT_START_TICKS, 'controller changed during registration'
    queue={'status':'WAITING_FOR_REGISTERED_SINGLE_THREAD_CONTROLLER','supervisor_pid':os.getpid(),
           'registered_pid':WAIT_PID,'registered_start_ticks':WAIT_START_TICKS,'execution_sha256':hashes,
           'wait_mechanism':'pidfd process-exit event; no repeated experiment progress reads',
           'next':'Compile and verify NSG extension after current evaluation finishes, then matched single-thread comparison'}
    queuepath=OUT/'baseline_pipeline.json';assert not queuepath.exists();dump(queuepath,queue)
    poller=select.poll();poller.register(descriptor,select.POLLIN);poller.poll();os.close(descriptor)
    state=json.loads((OUT/'state.json').read_text())
    assert state['status']=='MEASUREMENTS_AND_ANALYSIS_COMPLETE_ROOT_REVIEW_PENDING', 'prior evaluation not complete; no restart'
    for name,expected in hashes.items():assert sha(OUT/name)==expected,name
    assert json.loads((OUT/'single_thread_v1/results/analysis_v1/verification.json').read_text())['status']=='PASS'
    assert not RUN.exists();RUN.mkdir();(RUN/'inputs').mkdir();(RUN/'results').mkdir()
    dump(RUN/'state_before.json',state)
    manifest={'status':'PREPARING_NSG_COMPARISON','threads':1,'completed':[],'execution_sha256':hashes,
              'methods':['nsg_medoid','fast30k_3','fast20k_3','joint'],
              'same_frozen_models':True,'QGT_builds':3,'NSG_graphs':1,'timing_repeats_per_batch':3}
    dump(RUN/'manifest.json',manifest)
    runner.state=state
    runner.state.update(status='NSG_BASELINE_COMPARISON_PREPARING',controller_pid=os.getpid(),active_process=None,
                        active_stage=None,evaluation_threads=1,next='Compile/check NSG and complete matched single-thread baselines')
    runner.save()
    queue.update(status='NSG_BASELINE_COMPARISON_RUNNING');dump(queuepath,queue)
    for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:
        os.environ[name]='1'
    os.environ['OMP_DYNAMIC']='FALSE';os.environ['MPLCONFIGDIR']=str(OUT/'logs/matplotlib_cache')
    try:
        for name in ['benchmark_single_thread_nsg','nsg_native_parity']:
            runner.command('nsg_build_'+name,['bash',ROOT/'fast_router_diagnosis/20260908_v1/src/build.sh',OUT/'src'/f'{name}.cpp',OUT/'bin'/name],threads=1)
        synthetic_acceptance()
        for ds in ['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']:
            runner.command('nsg_native_'+ds,[OUT/'bin/nsg_native_parity',OUT/'inputs'/ds/'runner_config.json',OUT/'reviews'/('nsg_native_'+ds)],threads=1)
            assert json.loads((OUT/'reviews'/('nsg_native_'+ds)/'acceptance.json').read_text())['status']=='PASS'
        frozen=json.loads((OUT/'inputs/evaluation/heldout/models_frozen_before_evaluation.json').read_text())
        for record in frozen['files']:assert sha(record['path'])==record['sha256'],record['path']
        manifest['frozen_model_files_verified']=len(frozen['files'])
        manifest['binary_sha256']={name:sha(OUT/'bin'/name) for name in ['benchmark_single_thread_nsg','nsg_native_parity']}
        manifest['status']='MATCHED_BASELINES_RUNNING';dump(RUN/'manifest.json',manifest)
        runner.state['status']='NSG_BASELINE_COMPARISON_RUNNING';runner.save()
        for split in ['validation','heldout']:
            for original in sorted((OUT/'single_thread_v1/inputs'/split).glob('*/*.json')):
                config=json.loads(original.read_text());assert config['threads']==1 and len(config['methods'])==28
                config['methods']=[m for m in config['methods'] if m['family'] in CHOSEN]
                seed=config['methods'][0]['seed']
                for L in [64,128]:config['methods'].append({'name':f'nsg_medoid_L{L}','family':'nsg_medoid','L':L,'seed':seed,'k':1})
                assert len(config['methods'])==8
                config['baseline_amendment']=str(OUT/'baseline_comparison_amendment.md')
                path=RUN/'inputs'/split/original.parent.name/original.name;path.parent.mkdir(parents=True,exist_ok=True);dump(path,config)
                dest=RUN/'results'/split/original.parent.name/original.stem
                name=f'nsg_matched_{split}_{original.parent.name}_{original.stem}'
                start=time.monotonic();runner.command(name,[OUT/'bin/benchmark_single_thread_nsg',path,dest],threads=1)
                result=json.loads((dest/'results.json').read_text());assert result['status']=='COMPLETE' and result['threads']==1 and len(result['methods'])==8
                assert json.loads((dest/'thread_contract.json').read_text())['observed_openmp_threads']==1
                manifest['completed'].append({'path':str(dest),'seconds':time.monotonic()-start,'threads':1});dump(RUN/'manifest.json',manifest)
        runner.command('nsg_matched_analyze',[runner.PY,OUT/'src/analyze_baseline_comparison.py'],threads=1)
        review=json.loads((RUN/'analysis_v1/verification.json').read_text());assert review['status']=='PASS'
        manifest['status']='MATCHED_BASELINES_COMPLETE_ROOT_REVIEW_PENDING';dump(RUN/'manifest.json',manifest)
        queue['status']='MATCHED_BASELINES_COMPLETE_ROOT_REVIEW_PENDING';dump(queuepath,queue)
        runner.state.update(status='MATCHED_BASELINES_COMPLETE_ROOT_REVIEW_PENDING',active_stage=None,active_process=None,
                            next='Review NSG/Fast/A+B three metrics and controls; finalize plots, provenance, history and root docs')
        runner.save()
    except BaseException as error:
        if runner.child and runner.child.poll() is None:
            os.killpg(runner.child.pid,signal.SIGTERM);runner.child.wait()
        runner.state.update(status='NSG_BASELINE_COMPARISON_STOPPED_REQUIRES_INSPECTION',active_process=None,error=repr(error));runner.save()
        queue.update(status='STOPPED_REQUIRES_INSPECTION',error=repr(error));dump(queuepath,queue)
        manifest.update(status='STOPPED_REQUIRES_INSPECTION',error=repr(error));dump(RUN/'manifest.json',manifest)
        raise


if __name__=='__main__':
    signal.signal(signal.SIGTERM,runner.stop);signal.signal(signal.SIGINT,runner.stop)
    try:main()
    except BaseException as error:
        path=OUT/'baseline_pipeline.json'
        if path.exists():
            stopped=json.loads(path.read_text());stopped.update(status='STOPPED_REQUIRES_INSPECTION',error=repr(error));dump(path,stopped)
        raise
