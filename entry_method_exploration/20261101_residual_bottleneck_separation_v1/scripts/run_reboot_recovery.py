from checkpoint_storage import *
import os
freeze=read(R/'formal_freeze.json');plan=read(R/'storage/reboot_recovery/plan.json')
lookup={(x['dataset'],x['window']):x for x in plan['original_complete_windows']}
records=read(R/'reviews/reboot_recovery_progress.json') if (R/'reviews/reboot_recovery_progress.json').exists() else []
durable=Path('/root/acsg-e197-disk');assert durable.is_dir()
started=time.perf_counter()
def identities():
    for x in freeze['files']:assert sha(x['path'])==x['sha256'],x['path']
def invoke(ds,stage,binary,mode,config):
    argv=['taskset','-c','15',str(binary)]+([mode] if mode else [])+[str(config)]
    began=time.perf_counter();log=R/'reviews'/f'{ds}.{stage}.reboot.log'
    assert not log.exists(),('preserve/inspect partial recovery attempt before retry',log)
    with log.open('w') as output:
        p=subprocess.Popen(argv,cwd=REPO,stdout=output,stderr=subprocess.STDOUT)
        dump(R/'live_process.json',dict(dataset=ds,stage=stage,pid=p.pid,argv=argv,started_unix=time.time()))
        code=p.wait()
    rec=dict(dataset=ds,stage=stage,returncode=code,seconds=time.perf_counter()-began,argv=argv,log=str(log))
    records.append(rec);dump(R/'reviews/reboot_recovery_progress.json',records)
    print('REBOOT_STAGE',ds,stage,code,rec['seconds'],flush=True);assert code==0,(ds,stage)

for ds in DS:
    for w in ['A','B']:
        identities();c=read(R/'configs'/f'{ds}.{w}.json')
        for suffix,tag in [('',w),('.full_diagnosis',w+'-full')]:
            root=R/'storage/diagnosis'/ds/tag
            if not (root/'complete.json').exists():
                assert not root.exists(),('partial diagnosis',root)
                invoke(ds,'diagnosis-'+tag,R/'storage/formal_benchmark','diagnose',R/'configs'/f'{ds}.{w}{suffix}.json')
            checkpoint=checkpoint_tree(root,durable/'diagnosis'/ds/tag)
            dump(root/'durable_checkpoint.json',checkpoint);copy_verified(root/'durable_checkpoint.json',durable/'diagnosis'/ds/tag/'durable_checkpoint.json')
        oldmask=R/'reviews'/f'{ds}.{w}.teacher_mask_freeze.json'
        if oldmask.exists():
            previous=read(oldmask)
            for f in previous['files']:assert sha(f['path'])==f['sha256'],('old teacher mask/model/GT identity changed',f['path'])
        else:
            dump(oldmask,dict(status='FROZEN_GT_PRIVILEGED_DIAGNOSTIC_MASKS_ONLY',no_model_or_point_policy_change=True,
                files=[dict(path=str(p),sha256=sha(p)) for p in [Path(c['teacher_masks']),Path(c['test_gt']['path']),R/'storage/models'/ds/'selected.json']]))
        root=Path(c['output_dir'])
        if not (root/'complete.json').exists():
            assert not root.exists(),('partial restore/formal needs inspection',root)
            if (ds,w) in lookup:
                expected=lookup[ds,w];assert sha(expected['expected_complete'])==expected['expected_sha256']
                config=dict(c,recovery_expected=expected['expected_complete'])
                path=R/'recovery_configs'/f'{ds}.{w}.json';dump(path,config)
                invoke(ds,'restore-'+w,R/'storage/recover_packets','',path)
                assert read(root/'recovery_complete.json')['status']=='PASS_ALL_ORIGINAL_TIMED_SIX_ARRAY_SHA_RESTORED'
            else:
                invoke(ds,'formal-'+w,R/'storage/formal_benchmark','formal',R/'configs'/f'{ds}.{w}.json')
        v=read(root/'complete.json');assert v['points']==len(c['points']) and v['batches']==3*len(c['points'])
        saved=compact(root,durable/'results'/ds/w)
        print('WINDOW_DURABLE',ds,w,v['points'],saved['packet_archive_bytes'],flush=True)
        assert shutil.disk_usage('/root').free>=150*(1<<20)

original=read(R/'storage/reboot_recovery/pre_reboot_public_progress.json')
formal_records=original+[x for x in records if x['stage'].startswith('formal-')]
points=batches=restored=0
for ds in DS:
    for w in ['A','B']:
        c=read(R/'configs'/f'{ds}.{w}.json');root=Path(c['output_dir']);v=read(root/'complete.json')
        points+=v['points'];batches+=v['batches'];restored+=(root/'recovery_complete.json').exists()
        assert (durable/'results'/ds/w/'durable_checkpoint.json').exists()
assert points==freeze['points'] and batches==freeze['batches'] and restored==11
dump(R/'formal_complete.json',dict(status='PASS_FROZEN_FORMAL_MATRIX_COMPLETE',points=points,batches=batches,
    records=formal_records,outer_process_seconds=time.perf_counter()-started,all_28_candidate_bank_diagnoses_complete=True,
    model_or_policy_retuned=False,packet_evidence_origins=dict(original_durable_windows=1,old_timed_packet_SHA_restored_windows=11,new_post_boot_GIST_windows=2),
    reconstruction_process_records=records,old_GIST_incomplete_result_not_used=True,
    work_seeds_witnesses_for_restored_windows_replayed=True,every_window_durable_before_next=True))
dump(R/'reviews/reboot_recovery_complete.json',dict(status='PASS_11_HASH_RESTORED_2_GIST_NEW_ALL_14_DURABLE',
    points=points,batches=batches,seconds=time.perf_counter()-started,records=records))
print('ALL_WINDOWS_DURABLE_AND_FROZEN_MATRIX_COMPLETE',points,batches,flush=True)
