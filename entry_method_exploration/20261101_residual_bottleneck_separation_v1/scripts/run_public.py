from common import *
from archive import archive
freeze=read(R/'formal_freeze.json')
assert freeze['status']=='FROZEN_BEFORE_PUBLIC_DIAGNOSIS_AND_FORMAL_MATRIX'
for x in freeze['files']:assert sha(x['path'])==x['sha256'],x['path']
records=read(R/'reviews/public_progress.json') if (R/'reviews/public_progress.json').exists() else []
started=time.perf_counter()
def invoke(ds,stage,mode,config):
    argv=['taskset','-c','15',str(R/'storage/formal_benchmark'),mode,str(config)]
    t=time.perf_counter()
    with (R/'reviews'/f'{ds}.{stage}.log').open('w') as log:
        p=subprocess.Popen(argv,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
        dump(R/'live_process.json',dict(stage=stage,dataset=ds,pid=p.pid,argv=argv,started_unix=time.time()))
        code=p.wait()
    records.append(dict(dataset=ds,stage=stage,pid=p.pid,argv=argv,returncode=code,seconds=time.perf_counter()-t))
    dump(R/'reviews/public_progress.json',records)
    print(ds,stage,code,records[-1]['seconds'],flush=True)
    assert code==0,(ds,stage)
for ds in DS:
    for window in ['A','B']:
        for suffix in ['', '.full_diagnosis']:
            tag=window+('-full' if suffix else '')
            path=R/'configs'/f'{ds}.{window}{suffix}.json'
            output=R/'storage/diagnosis'/ds/tag
            if (output/'complete.json').exists():
                assert read(output/'complete.json')['status']=='PASS_FULL_C_AND_STATE_CANDIDATE_DIAGNOSIS'
                print('REUSE_COMPLETED',ds,'diagnosis-'+tag,flush=True)
            else:
                assert not output.exists(),('partial stage needs inspection',output)
                invoke(ds,'diagnosis-'+tag,'diagnose',path)
        c=read(R/'configs'/f'{ds}.{window}.json')
        model=R/'storage/models'/ds/'selected.json'
        point_files=[Path(c['teacher_masks']),Path(c['test_gt']['path']),model]
        dump(R/'reviews'/f'{ds}.{window}.teacher_mask_freeze.json',dict(
            status='FROZEN_GT_PRIVILEGED_DIAGNOSTIC_MASKS_ONLY',
            no_model_or_point_policy_change=True,
            files=[dict(path=str(p),sha256=sha(p)) for p in point_files]))
        for x in freeze['files']:
            # Immutable source/model/config contract; full SHA check is outside timer.
            assert sha(x['path'])==x['sha256'],x['path']
        output=Path(c['output_dir'])
        if (output/'complete.json').exists():
            assert read(output/'complete.json')['status']=='PASS_FORMAL_BOTTLENECK_MATRIX'
            assert read(output/'complete.json')['points']==len(c['points'])
            print('REUSE_COMPLETED',ds,'formal-'+window,flush=True)
        else:
            assert not output.exists(),('partial native stage needs inspection',output)
            invoke(ds,'formal-'+window,'formal',R/'configs'/f'{ds}.{window}.json')
        a=archive(c['output_dir']);print(ds,window,'archived',a['archive_bytes'],flush=True)
        free=__import__('shutil').disk_usage('/root').free
        assert free>=150*(1<<20),('E197 storage floor',free)
actual_points=actual_batches=0
for ds in DS:
    for window in ['A','B']:
        c=read(R/'configs'/f'{ds}.{window}.json');v=read(Path(c['output_dir'])/'complete.json')
        actual_points+=v['points'];actual_batches+=v['batches']
assert actual_points==freeze['points'] and actual_batches==freeze['batches']
dump(R/'formal_complete.json',dict(status='PASS_FROZEN_FORMAL_MATRIX_COMPLETE',points=actual_points,
    batches=actual_batches,records=records,outer_process_seconds=time.perf_counter()-started,
    all_28_candidate_bank_diagnoses_complete=True,model_or_policy_retuned=False))
s=read(R/'state.json');s.update(status='FORMAL_COMPLETE_ANALYSIS_AND_REPORT_PENDING',pending_work=True);dump(R/'state.json',s)
