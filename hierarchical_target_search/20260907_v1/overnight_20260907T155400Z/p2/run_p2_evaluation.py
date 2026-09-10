#!/usr/bin/env python3
"""Run one fixed P2 dataset sequentially: independent count, wall and bounded trace."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT=Path('/data/netg/ACSG')
RUN=Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset',required=True)
    p.add_argument('--model',type=Path,required=True)
    p.add_argument('--fast-manifest',type=Path,required=True)
    p.add_argument('--audit',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--evaluator',type=Path,default=ROOT/'build/benches/bench_hierarchical_eval')
    a=p.parse_args()
    if json.loads((RUN/'gates/P1.json').read_text())['status']!='PASS':raise ValueError('P1 required')
    if time.time()>=dt.datetime(2026,9,7,22,59,tzinfo=dt.timezone.utc).timestamp():raise RuntimeError('Deadline closed')
    audit=json.loads(a.audit.read_text());ds=next(x for x in audit['datasets'] if x['dataset']==a.dataset)
    model=json.loads(a.model.read_text());fast=json.loads(a.fast_manifest.read_text())
    if model['status']!='COMPLETE' or model['dataset']!=a.dataset or model['fit_range']!=[10000,30000]:raise ValueError('Wrong model contract')
    if fast['status']!='COMPLETE' or fast['dataset']!=a.dataset or fast['fit_queries']!=20000 or fast['pilot_queries_used']!=0:raise ValueError('Wrong paired Fast contract')
    if model['fit_query_values_sha256']!=fast['fit_query_values_sha256'] or model['fit_gt_values_sha256']!=fast['fit_gt_values_sha256']:raise ValueError('Fit datasets do not match')
    if model['graph_sha256']!=ds['graph']['sha256']:raise ValueError('Graph mismatch')
    a.output.mkdir(parents=True,exist_ok=False)
    command=[str(a.evaluator.resolve()),'--stage','P2','--split','pilot','--dataset',a.dataset,
             '--index-file',ds['graph']['path'],'--model',str(a.model.resolve()),
             '--fast-hubs',fast['hubs_file'],'--fast-ids',fast['ids_file'],'--fast-m','3',
             '--search-ls','64,128','--top-k','10','--query-offset','0','--hnsw-seed','100']
    methods='fast,geom_unified,geom_uniform,geom_probability,oracle_unified,oracle_probability'
    invocations=[('count',['--measurement','count','--rounds','1','--methods',methods,'--max-queries','10000','--threads','16','--warmup-queries','128']),
                 ('timing',['--measurement','timing','--rounds','5','--methods',methods,'--max-queries','10000','--threads','16','--warmup-queries','128']),
                 ('trace',['--measurement','trace','--rounds','1','--methods',methods.removeprefix('fast,'),'--max-queries','16','--threads','1','--warmup-queries','16'])]
    record={'stage':'P2','status':'INCOMPLETE','dataset':a.dataset,'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'model':str(a.model.resolve()),'model_sha256':sha(a.model),'fast_manifest':str(a.fast_manifest.resolve()),'fast_manifest_sha256':sha(a.fast_manifest),
            'evaluator_sha256':sha(a.evaluator),'runner_sha256':sha(Path(__file__)),'protocol_sha256':sha(RUN/'protocol.json'),
            'heldout_accessed':False,'validation_accessed':False,'actual_trace_query_ids':list(range(16)),
            'trace_scope':'Preselected first16 pilot IDs; other preregistered diagnostic IDs not run unless needed',
            'invocations':[]}
    def save():
        x=a.output/'execution.tmp.json';x.write_text(json.dumps(record,indent=2)+'\n');x.replace(a.output/'execution.json')
    save()
    try:
        for name,args in invocations:
            if time.time()>=dt.datetime(2026,9,7,22,59,tzinfo=dt.timezone.utc).timestamp():raise RuntimeError('Deadline closed between phases')
            cmd=command+args+['--output',str((a.output/(name+'.json')).resolve())]
            item={'name':name,'command':cmd,'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'RUNNING'}
            record['invocations'].append(item);save();print('P2_BEGIN',a.dataset,name,flush=True)
            with (a.output/(name+'.log')).open('xb') as f:
                child=subprocess.Popen(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
                item.update(pid=child.pid,pgid=os.getpgid(child.pid));save();item['returncode']=child.wait()
            item.update(status='COMPLETE' if item['returncode']==0 else 'FAILED',ended_utc=dt.datetime.now(dt.timezone.utc).isoformat());save()
            if item['returncode']!=0:raise RuntimeError('P2 '+name+' failed; retain diagnostic log/checkpoints')
            print('P2_DONE',a.dataset,name,flush=True)
        record['status']='COMPLETE_DATASET_MEASUREMENTS'
    except BaseException as e:
        record['error']=repr(e);raise
    finally:
        record['ended_utc']=dt.datetime.now(dt.timezone.utc).isoformat();save()
    print(json.dumps({'status':record['status'],'path':str(a.output/'execution.json')}),flush=True)

if __name__=='__main__':main()
