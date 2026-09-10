#!/usr/bin/env python3
"""Run the four fixed Fast diagnostic jobs sequentially with owned process handles."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

ROOT=Path('/data/netg/ACSG')
VERSION=ROOT/'fast_router_diagnosis/20260908_v1'
DATASETS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']

def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_json(p,v):
    p=Path(p);tmp=p.with_name(p.name+'.tmp');tmp.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n');tmp.replace(p)
def identity(pid):
    stat=(Path('/proc')/str(pid)/'stat').read_text()
    rest=stat[stat.rindex(')')+2:].split()
    return {'pid':pid,'pgid':int(rest[2]),'start_ticks':int(rest[19])}
def rss(pid):
    for line in (Path('/proc')/str(pid)/'status').read_text().splitlines():
        if line.startswith('VmRSS:'):return int(line.split()[1])*1024
    return 0
def stop_owned(proc,ident):
    if proc.poll() is not None:return
    if identity(proc.pid)!=ident:raise RuntimeError('owned process identity changed')
    os.killpg(ident['pgid'],signal.SIGTERM)
    try:proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        if proc.poll() is None and identity(proc.pid)==ident:os.killpg(ident['pgid'],signal.SIGKILL)
        proc.wait()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.prepared=args.prepared.resolve();args.output=args.output.resolve()
    if json.loads((args.prepared/'completion.json').read_text())['status']!='PASS_ALL_INPUTS_PREPARED':raise ValueError('inputs not ready')
    args.output.mkdir(parents=True,exist_ok=False)
    binary=VERSION/'bin/fast_router_diagnosis'
    frozen=[VERSION/'protocol.md',VERSION/'src/fast_router_diagnosis.cpp',binary,
            VERSION/'tools/prepare_inputs.py',Path(__file__),VERSION/'inputs/source_paths.json',
            ROOT/'ACSG/ACSG.cpp',ROOT/'ACSG/ACSG.h',ROOT/'ACSG/IndexACSG.cpp',ROOT/'ACSG/IndexACSG.h',
            ROOT/'build/ACSG/libACSG.a',ROOT/'build/MRNN_Descent/libmrnndescent.a',ROOT/'build/faiss/faiss/libfaiss.a']
    for dataset in DATASETS:
        frozen.append(args.prepared/dataset/'runner_config.json')
        sm=json.loads((args.prepared/dataset/'sample_manifest.json').read_text())
        frozen += [Path(x['path']) for x in sm['artifacts'].values()]
    freeze={str(p):digest(p) for p in frozen}
    write_json(args.output/'execution_freeze.json',freeze)
    start=time.monotonic();search_calls=0;jobs=[]
    base_state=json.loads((VERSION/'state.json').read_text())
    for dataset in DATASETS:
        for phase in ['parity','main']:
            if time.monotonic()-start>=14400:raise RuntimeError('four hour task budget reached')
            if any(digest(p)!=sha for p,sha in freeze.items()):raise RuntimeError('frozen execution identity changed')
            job_id=dataset+'_'+phase
            out=args.output/phase/dataset
            log=VERSION/'logs'/(job_id+'_v1.log')
            command=[str(binary),'--config',str(args.prepared/dataset/'runner_config.json'),
                     '--output',str(out),'--parity-queries','8' if phase=='parity' else '0']
            if phase=='parity':command.append('--parity-only')
            if phase=='main':
                previous=json.loads((args.output/'parity'/dataset/'parity.json').read_text())
                if previous['status']!='PASS':raise RuntimeError('parity not passed')
            with log.open('xb') as lf:
                env=os.environ.copy();env.update(OMP_NUM_THREADS='16',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
                proc=subprocess.Popen(command,cwd=ROOT,env=env,stdout=lf,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
                ident=identity(proc.pid)
                record={'job_id':job_id,'dataset':dataset,'phase':phase,'started_utc':now(),'command':command,'log':str(log),
                        'output':str(out),'process':ident,'status':'RUNNING','peak_rss_bytes':0}
                jobs.append(record);write_json(args.output/'jobs.json',jobs)
                base_state.update(status='DIAGNOSTIC_EXPERIMENT_RUNNING',active_job=record,updated_utc=now(),
                                  experiment_output=str(args.output),inputs=str(args.prepared))
                write_json(VERSION/'state.json',base_state)
                print('STARTED',job_id,ident,flush=True)
                job_start=time.monotonic();last_print=0
                try:
                    while proc.poll() is None:
                        try:mem=rss(proc.pid)
                        except FileNotFoundError:continue
                        record['peak_rss_bytes']=max(record['peak_rss_bytes'],mem)
                        elapsed=time.monotonic()-start
                        artifact_bytes=sum(p.stat().st_size for p in VERSION.rglob('*') if p.is_file())
                        reason=None
                        if mem>80*2**30:reason='RSS_LIMIT'
                        if shutil.disk_usage(ROOT).free<10*2**30:reason='DISK_RESERVE'
                        if artifact_bytes>2*2**30:reason='ARTIFACT_LIMIT'
                        if elapsed>=14400:reason='TIME_LIMIT'
                        if reason:
                            record['stop_reason']=reason;stop_owned(proc,ident)
                            raise RuntimeError(reason)
                        if time.monotonic()-last_print>=15:
                            print('LIVE',job_id,'seconds',round(time.monotonic()-job_start,1),'RSS_GiB',round(mem/2**30,2),flush=True)
                            write_json(args.output/'jobs.json',jobs);last_print=time.monotonic()
                        time.sleep(1)
                except BaseException:
                    stop_owned(proc,ident);record['status']='STOPPED_OR_FAILED';record['exit_code']=proc.returncode
                    record['ended_utc']=now();write_json(args.output/'jobs.json',jobs)
                    base_state.update(status='DIAGNOSTIC_EXECUTION_STOPPED',active_job=None,last_failed_job=record,updated_utc=now())
                    write_json(VERSION/'state.json',base_state)
                    raise
            record.update(ended_utc=now(),exit_code=proc.returncode,wall_seconds=time.monotonic()-job_start)
            if proc.returncode!=0:
                record['status']='FAILED';write_json(args.output/'jobs.json',jobs)
                base_state.update(status='DIAGNOSTIC_EXECUTION_FAILED',active_job=None,last_failed_job=record,updated_utc=now())
                write_json(VERSION/'state.json',base_state)
                raise RuntimeError('job failed: '+job_id)
            meta=json.loads((out/'metadata.json').read_text())
            expected='PARITY_ONLY_COMPLETE' if phase=='parity' else 'COMPLETE'
            if meta['status']!=expected:raise RuntimeError('missing terminal result: '+job_id)
            calls=meta['graph_search_calls_including_parity'];search_calls+=calls
            record.update(status='COMPLETE',graph_search_calls=calls)
            write_json(args.output/'jobs.json',jobs)
            if search_calls>3_000_000:raise RuntimeError('search call budget exceeded')
            print('FINISHED',job_id,'calls',calls,'wall_seconds',round(record['wall_seconds'],2),flush=True)
    result={'status':'COMPLETE_DIAGNOSTIC_SEARCH','jobs':len(jobs),'graph_search_calls':search_calls,
            'instrumented_wall_seconds':time.monotonic()-start,'completed_utc':now(),'interpretation':'analysis pending; no deployable performance claim'}
    write_json(args.output/'completion.json',result)
    base_state.update(status='EXPERIMENTS_COMPLETE_ANALYSIS_PENDING',active_job=None,updated_utc=now(),search_completion=result)
    write_json(VERSION/'state.json',base_state)
    print(json.dumps(result),flush=True)

if __name__=='__main__':main()
