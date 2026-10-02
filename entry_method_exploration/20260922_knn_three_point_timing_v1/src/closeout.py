from common import *
import shutil

assert read(RUN/'state.json')['status']=='ANALYZED'
assert not (RUN/'seal.json').exists()
lock=read(RUN/'config.locked.json')
analysis=read(RUN/'analysis.json')
assert analysis['status']=='PASS' and len(analysis['comparisons'])==12
jobs=read(RUN/'reviews/jobs.json')
assert all(j['exit_code']==0 for j in jobs)
assert all(j['actual_max_threads']==1 for j in jobs if j['name']!='build')
rounds=calls=0
for ds,cfg in lock['datasets'].items():
    gt=np.fromfile(cfg['native']['GT'],'<i4').reshape(4096,100)
    complete=read(RUN/'results'/ds/'complete.json')
    calls+=complete['calls']
    timings=read(RUN/'results'/ds/'timings.json')
    assert len(timings)==36
    rounds+=len(timings)
    for row in timings:
        assert row['threads']==1 and abs(row['qps']*row['seconds']-4096)<1e-8
    for c in [x for x in analysis['comparisons'] if x['dataset']==ds]:
        for label,name in [('baseline','DefaultGT10'),('candidate','TargetKNN')]:
            samples=[r['qps'] for r in timings if r['method']==name and r['K']==c['K'] and r['L']==c['L']]
            assert len(samples)==3 and abs(float(np.median(samples))-c[label]['qps_median'])<1e-10
            K,L=c['K'],c['L']
            ids=np.fromfile(RUN/'results'/ds/f'{name}_k{K}_L{L}'/'ids.i32','<i4').reshape(4096,K)
            hits=0
            for begin in range(0,4096,128):
                hits+=int((ids[begin:begin+128,:,None]==gt[begin:begin+128,None,:K]).any(axis=1).sum())
            assert abs(hits/(4096*K)-c[label]['recall'])<1e-12
    stat=Path(cfg['native']['index']).stat()
    assert dict(bytes=stat.st_size,mtime_ns=stat.st_mtime_ns)==cfg['graph_stat']
assert calls==lock['expected_calls'] and rounds==72
preserve_check()
for item in read(RUN/'reviews/started.json')['files']+read(RUN/'reviews/reference_returns.json')['files']:
    assert identity(item['path'])==item
assert identity(RUN/'bin/benchmark')==read(RUN/'reviews/binary.json')
docs=['summary.md','spec.md','s-target.md','s-experiment.md','AGENTS.md',
    'experiment_history/README.md','experiment_history/125_knn_three_point_timing.md']
for name in docs:
    out=RUN/'source_after'/name
    out.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/name,out)
    assert (ROOT/name).read_bytes()==out.read_bytes()
size=sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())
assert size<lock['max_new_bytes'] and shutil.disk_usage(RUN).free>6*(1<<30)
dump(RUN/'reviews/completion.json',dict(status='PASS',wall_rounds=rounds,NSG_calls=calls,
    independently_rescored_points=24,
    native_parity=True,default_restored=True,repeated_output_identity=True,
    candidate_cached_points_restored=read(RUN/'reviews/reference_returns.json')['restored_candidate_points'],
    frozen_identity=True,old_E120_seal_preserved=True,new_bytes=size,active_processes=[]))
dump(RUN/'state.json',dict(status='COMPLETED_LIGHTWEIGHT_COMPARISON',completed=True,
    pending=[],active_processes=[],default_changed=False,complete_query_wall=True,
    formal_evaluation=False,report='report.md',completed_unix=time.time()))
files=[identity(p) for p in sorted(RUN.rglob('*')) if p.is_file() and '__pycache__' not in p.parts]
dump(RUN/'seal.json',dict(status='SEALED',files=files,excluded=['seal.json','__pycache__']))
for item in files:
    assert identity(item['path'])==item
print('COMPLETE',rounds,'rounds;',calls,'searches;',len(files),'sealed files',flush=True)
