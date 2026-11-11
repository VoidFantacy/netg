from common import *
import gzip,shutil
assert read(R/'reviews/recovery_qualification.json')['points']==60
assert read(R/'reviews/reboot_initial_compaction.json')['status']=='PASS_INITIAL_EVIDENCE_DURABLE_COMPACT'
disk=Path('/root/acsg-e197-storage');back=Path('/root/acsg-e197-disk');ram=Path('/dev/shm/acsg-e197-output')
assert disk.is_dir() and not disk.is_symlink() and not back.exists() and not ram.exists()
folder=disk/'reboot_recovery';folder.mkdir(exist_ok=True);expected=folder/'expected';expected.mkdir(exist_ok=True)
rows=[]
for ds in DS[:-1]:
    for w in ['A','B']:
        log=R/'reviews'/f'{ds}.formal-{w}.log';native=json.loads(log.read_text().splitlines()[-1])
        assert native['status']=='PASS_FORMAL_BOTTLENECK_MATRIX'
        for p in native['results']:assert len({v['packet_sha256'] for v in p['rounds']})==1 and len(p['rounds'])==3
        target=expected/f'{ds}.{w}.json';dump(target,native)
        rows.append(dict(dataset=ds,window=w,points=native['points'],original_log=str(log),
            original_log_sha256=sha(log),expected_complete=str(R/'storage/reboot_recovery/expected'/target.name),expected_sha256=sha(target)))
shutil.copy2(R/'reviews/public_progress.json',folder/'pre_reboot_public_progress.json')
shutil.copy2(R/'reviews/pipeline_progress.json',folder/'pre_reboot_pipeline_progress.json')
log=R/'reviews/gist1m_l2_v1.formal-A.log'
with gzip.open(folder/'gist.A.interrupted_native_log.gz','wb') as f:f.write(log.read_bytes())
live=read(R/'live_process.json')
dump(folder/'interrupted_GIST.json',dict(status='POWER_OFF_INTERRUPTED_NO_COMPLETE_PACKET_IDENTITIES',
    observed_seconds_lower_bound=max(0,log.stat().st_mtime-live['started_unix']),complete_process_seconds=None,
    raw_outputs_lost=True,used_as_formal_result=False,log_sha256=sha(log)))
dump(folder/'plan.json',dict(status='FROZEN_POST_REBOOT_HASH_RESTORATION_AND_GIST_REMEASUREMENT',
    original_complete_windows=rows,models_points_policy_changed=False,per_window_durable_checkpoint_required=True))
shutil.copytree(disk,ram,copy_function=shutil.copy2)
files=0
for p in disk.rglob('*'):
    if p.is_file():assert sha(p)==sha(ram/p.relative_to(disk));files+=1
disk.rename(back);disk.symlink_to(ram,target_is_directory=True)
for ds in DS:Path(read(R/'configs'/f'{ds}.A.json')['scratch']).mkdir(parents=True,exist_ok=True)
for x in read(R/'formal_freeze.json')['files']:assert sha(x['path'])==x['sha256']
dump(R/'reviews/reboot_RAM_working_copy.json',dict(status='PASS_BYTE_IDENTICAL_RAM_WORKING_COPY_WITH_WINDOW_CHECKPOINTS',
    copied_files=files,durable_root=str(back),RAM_root=str(ram),new_evidence_not_complete_until_durable=True))
print('REBOOT_RECOVERY_PREPARED',files,flush=True)
