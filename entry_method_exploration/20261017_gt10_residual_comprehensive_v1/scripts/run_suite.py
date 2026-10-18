#!/usr/bin/env python3
"""Sequential E183 execution with input/binary binding and persistent receipts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()


def save(path,value):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(value,f,indent=2,ensure_ascii=False);f.write('\n')


def state(**changes):
    p=ROOT/'state.json';v=json.loads(p.read_text());v.update(changes,updated_unix=time.time())
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n');tmp.replace(p)


def collect_paths(value):
    found=set()
    if isinstance(value,dict):
        for v in value.values():found.update(collect_paths(v))
    elif isinstance(value,list):
        for v in value:found.update(collect_paths(v))
    elif isinstance(value,str) and value.startswith('/') and Path(value).is_file():found.add(value)
    return found


def prior(stage,dataset):
    original=ROOT/'reviews'/f'{stage}_{dataset}.execution.json'
    correction=ROOT/'reviews'/f'{stage}_{dataset}.execution.corrected.json'
    path=correction if correction.exists() else original
    rr=json.loads(path.read_text())
    if path==correction:assert rr['supersedes_receipt_sha256']==sha(original),'Correction binds preserved original receipt'
    assert rr['status']=='PASS_NATIVE_EXECUTION' and not rr['input_drift'],f'Successful actual prior stage: {stage} {dataset}'
    lock=json.loads((ROOT/'reviews'/f'{stage}_{dataset}.execution_lock.json').read_text())
    for path,value in {**lock['files'],**rr['outputs']}.items():
        s=Path(path).stat()
        if path==str(Path(__file__).resolve()) and sha(path)!=value['sha256']:
            archived=ROOT/'source_before/run_suite_pre_status_fix.py'
            assert sha(archived)==value['sha256'] and correction.exists(),'Only the preserved status-spelling launcher correction is accepted'
            continue
        assert (s.st_size,s.st_mtime_ns)==(value['bytes'],value['mtime_ns']),f'Prior stage identity drift: {path}'
        if s.st_size<128*1024*1024:assert sha(path)==value['sha256'],f'Prior stage SHA drift: {path}'
    return rr


def run(mode,config,binary):
    c=json.loads(config.read_text());dataset=c['dataset'];tag=f'{mode}_{dataset}'
    log=ROOT/'logs'/f'{tag}.log';receipt=ROOT/'reviews'/f'{tag}.execution.json'
    lock=ROOT/'reviews'/f'{tag}.execution_lock.json'
    assert not any(p.exists() for p in (log,receipt,lock)),f'Attempt already exists: {tag}'
    paths=collect_paths(c)|{str(config),str(binary),str(ROOT/'protocol.md'),str(Path(__file__).resolve())}
    build_path=ROOT/'bin'/f'build_{binary.name}.json'
    build=json.loads(build_path.read_text())
    assert build['status']=='PASS_E183_NATIVE_BUILD' and sha(binary)==build['binary_sha256'],'Native build identity'
    for path,digest in build['input_sha256'].items():
        assert sha(path)==digest,f'Compiled input drift: {path}'
        paths.add(path)
    paths.add(str(build_path))
    assert c.get('protocol_sha256')==sha(ROOT/'protocol.md'),'Frozen protocol identity'
    expected=json.loads((ROOT/'reviews/input_freeze.json').read_text())['files']
    identities={}
    for p in sorted(paths):
        s=Path(p).stat();observed={'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
        if p in expected:
            assert observed=={k:expected[p][k] for k in observed},f'Frozen source stat drift: {p}'
            h=expected[p]['sha256']
            if s.st_size<128*1024*1024:assert sha(p)==h,f'Frozen source SHA drift: {p}'
        else:h=sha(p)
        identities[p]={**observed,'sha256':h}
    save(lock,{'status':'FROZEN_BEFORE_NATIVE_EXECUTION','mode':mode,'config':str(config),
               'files':identities,'created_unix':time.time(),'large_SHA_scope':'full suite source SHA was recomputed once before any training; per stage unchanged size/mtime binding; small files rehashed'})
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',OMP_DYNAMIC='FALSE')
    argv=['taskset','-c','15',str(binary),mode,str(config)];started=time.monotonic()
    state(status='RUNNING_'+mode.upper(),active_dataset=dataset,active_stage=mode)
    with log.open('x') as f:
        child=subprocess.Popen(argv,stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
        save(ROOT/'reviews'/f'{tag}.launch.json',{'pid':child.pid,'argv':argv,'started_unix':time.time(),'log':str(log)})
        print(json.dumps({'event':'launch','dataset':dataset,'mode':mode,'pid':child.pid}),flush=True)
        try:code=child.wait()
        except BaseException:
            if child.poll() is None:os.killpg(child.pid,signal.SIGTERM);child.wait()
            raise
    drift=[]
    for p,v in identities.items():
        s=Path(p).stat()
        if (s.st_size,s.st_mtime_ns)!=(v['bytes'],v['mtime_ns']) or (s.st_size<128*1024*1024 and sha(p)!=v['sha256']):drift.append(p)
    complete=Path(c['output_dir'])/'complete.json'
    result=json.loads(complete.read_text()) if complete.exists() else None
    statuses={'teacher':'PASS_E183_TRAIN_TEACHERS','compile':'PASS_E183_COMPILE',
              'benchmark':'PASS_E183_FORMAL_FULL_TIMED_OUTPUT_ORACLES','qualification':'PASS_E183_QUALIFICATION'}
    native_pass=bool(result and result.get('status')==statuses[mode] and result.get('config')==c)
    if mode in ('teacher','benchmark','qualification'):native_pass=native_pass and result.get('dataset')==dataset
    if mode in ('benchmark','qualification'):
        count=len(c['methods'])*sum(map(len,c['K_L'].values()))
        native_pass=native_pass and result.get('points')==count and len(result.get('results',[]))==count
        native_pass=native_pass and all(r.get('timing_repeats')==c['timing_repeats'] and len(r.get('rounds',[]))==c['timing_repeats'] for r in result.get('results',[]))
    outputs={}
    if code==0 and native_pass:
        for p in sorted(Path(c['output_dir']).rglob('*')):
            if p.is_file():
                s=p.stat();outputs[str(p)]={'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'sha256':sha(p)}
    info={'status':'PASS_NATIVE_EXECUTION' if code==0 and not drift and native_pass else 'FAIL_NATIVE_EXECUTION',
          'argv':argv,'pid':child.pid,'exit_code':code,'elapsed_seconds':time.monotonic()-started,
          'input_drift':drift,'outputs':outputs,'native_complete':str(complete),'native_status':result.get('status') if result else None,
          'cost_scope':'Complete native child lifecycle. Contains any inner timing and audit; do not sum nested times twice.'}
    save(receipt,info);print(json.dumps(info),flush=True)
    assert info['status']=='PASS_NATIVE_EXECUTION',f'Native failed, original attempt preserved: {tag}'
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['offline','formal'],required=True)
    ap.add_argument('--dataset',action='append');a=ap.parse_args()
    suite=json.loads((ROOT/'reviews/dataset_catalogue.json').read_text())
    datasets=a.dataset or list(suite['datasets']);started=time.monotonic();points=0
    if a.stage=='formal':
        gt=json.loads((ROOT/'reviews/gt_sample_audit.json').read_text())
        assert gt['status']=='PASS_EXHAUSTIVE_FLOAT64_SAMPLE_GT_AUDIT' and len(gt['rows'])==224 and all(r['acceptable'] for r in gt['rows']),'GT sample audit before formal'
        assert {r['dataset'] for r in gt['rows']}==set(suite['datasets']),'All dataset GT audit scope'
        qr=json.loads((ROOT/'reviews/qualification_regression.json').read_text())
        assert qr['status']=='PASS_SMALL_ACTUAL_RUN_FULL_WORD_HISTORICAL_REGRESSION','Historical runtime qualification'
        for ds in suite['datasets']:
            cc=json.loads((ROOT/'models'/ds/'compiled/complete.json').read_text())
            assert cc['status']=='PASS_E183_COMPILE' and cc['config']==json.loads((ROOT/'configs'/f'{ds}.compile.json').read_text()),f'Offline must finish first: {ds}'
            for stage in ('teacher','compile','qualification'):
                prior(stage,ds)
    for dataset in datasets:
        assert dataset in suite['datasets']
        if a.stage=='offline':
            for stage in ('teacher','compile'):
                rp=ROOT/'reviews'/f'{stage}_{dataset}.execution.json'
                if rp.exists():
                    prior(stage,dataset)
                    print(json.dumps({'event':'reuse_verified_completed_stage','dataset':dataset,'stage':stage}),flush=True)
                else:run(stage,ROOT/'configs'/f'{dataset}.{stage}.json',ROOT/'bin/residual_tools')
        else:
            r=run('benchmark',ROOT/'configs'/f'{dataset}.benchmark.json',ROOT/'bin/benchmark')
            points+=len(r.get('results',[]));state(completed_points=points)
    state(status='OFFLINE_MODELS_COMPLETE' if a.stage=='offline' else 'FORMAL_MATRIX_COMPLETE_ANALYSIS_PENDING',
          active_dataset=None,active_stage=None,**({'completed_points':points} if a.stage=='formal' else {}))
    save(ROOT/'reviews'/f'{a.stage}_suite.execution.json',{'status':'PASS_SUITE_STAGE','stage':a.stage,'datasets':datasets,
           'elapsed_seconds':time.monotonic()-started,'points':points if a.stage=='formal' else None})


if __name__=='__main__':main()
