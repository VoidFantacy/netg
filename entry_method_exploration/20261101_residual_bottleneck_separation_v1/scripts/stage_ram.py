"""Storage-only recovery; frozen methods, models and query points stay unchanged."""
from common import *
import gzip, io, os, shutil, tarfile

disk = Path('/root/acsg-e197-storage')
backup = Path('/root/acsg-e197-disk')
ram = Path('/dev/shm/acsg-e197-output')
assert disk.is_dir() and not disk.is_symlink() and not backup.exists() and not ram.exists()
live = read(R/'live_process.json')
assert not (Path('/proc')/str(live['pid'])).exists(), 'native attempt must have ended'
assert not (disk/'results/coco/B/complete.json').exists()
for name in ['pipeline_progress.json', 'public_progress.json']:
    shutil.copy2(R/'reviews'/name, R/'reviews'/('before_storage_recovery.'+name))
shutil.copy2(R/'reviews/coco.formal-B.log', R/'reviews/coco.formal-B.storage_attempt1.log')
started = time.perf_counter()
shutil.copytree(disk, ram, copy_function=shutil.copy2)
files=[]
for p in sorted(x for x in disk.rglob('*') if x.is_file()):
    q=ram/p.relative_to(disk)
    digest=sha(p)
    assert q.stat().st_size==p.stat().st_size and sha(q)==digest
    assert q.stat().st_mtime_ns==p.stat().st_mtime_ns
    files.append(dict(path=str(p.relative_to(disk)),bytes=p.stat().st_size,sha256=digest))
with gzip.open(ram/'storage_copy_identity.json.gz','wt') as out:
    json.dump(files,out,separators=(',',':'))

# Preserve the stopped attempt as opaque bytes, including any interrupted gzip wrapper.
attempt=ram/'results/coco/B'
failed=ram/'attempts/coco.B.storage_peak'
failed.mkdir(parents=True)
dest=failed/'original_files.tar.zst'
members=[]
with dest.open('wb') as output:
    proc=subprocess.Popen(['zstd','-q','-15','-T1','-c'],stdin=subprocess.PIPE,stdout=output)
    with tarfile.open(fileobj=proc.stdin,mode='w|') as tar:
        for p in sorted(x for x in attempt.rglob('*') if x.is_file()):
            payload=p.read_bytes();rel=str(p.relative_to(attempt))
            inf=tarfile.TarInfo(rel);inf.size=len(payload);inf.mtime=0
            tar.addfile(inf,io.BytesIO(payload));members.append(dict(path=rel,bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest()))
    proc.stdin.close();assert proc.wait()==0
expected={x['path']:x for x in members};seen=set()
proc=subprocess.Popen(['zstd','-q','-d','-c',str(dest)],stdout=subprocess.PIPE)
with tarfile.open(fileobj=proc.stdout,mode='r|') as tar:
    for item in tar:
        b=tar.extractfile(item).read();ref=expected[item.name]
        assert len(b)==ref['bytes'] and hashlib.sha256(b).hexdigest()==ref['sha256'];seen.add(item.name)
assert proc.wait()==0 and seen==set(expected)
dump(failed/'archive_identity.json',dict(status='PASS_STOPPED_ATTEMPT_ALL_ORIGINAL_BYTES_ROUNDTRIP',
    archive=dest.name,archive_sha256=sha(dest),files=members,not_formal_results=True))

# Keep a durable copy of the complete stopped attempt before reclaiming its raw temporary form.
persist=disk/'attempts/coco.B.storage_peak';persist.parent.mkdir(parents=True,exist_ok=True)
shutil.copytree(failed,persist)
for p in failed.iterdir():assert sha(p)==sha(persist/p.name)
shutil.rmtree(attempt)
shutil.rmtree(disk/'results/coco/B')
shutil.copy2(ram/'storage_copy_identity.json.gz',disk/'storage_copy_identity.json.gz')
disk.rename(backup)
disk.symlink_to(ram,target_is_directory=True)
frozen=read(R/'formal_freeze.json')
for x in frozen['files']:assert sha(x['path'])==x['sha256'],x['path']
for x in frozen['large_inherited_inputs']:
    s=Path(x['path']).stat();assert s.st_size==x['bytes'] and s.st_mtime_ns==x['mtime_ns']
receipt=dict(status='PASS_BYTE_IDENTICAL_RAM_STAGING_AFTER_STORAGE_ATTEMPT_STOP',
    copied_files=len(files),copied_bytes=sum(x['bytes'] for x in files),
    copied_file_identities=str(R/'storage/storage_copy_identity.json.gz'),
    durable_pre_staging_copy=str(backup),RAM_working_copy=str(ram),
    stopped_attempt_preserved=str(R/'storage/attempts/coco.B.storage_peak/archive_identity.json'),
    stopped_attempt_original_bytes=sum(x['bytes'] for x in members),
    stopped_attempt_archive_bytes=dest.stat().st_size,
    all_frozen_bytes_and_large_stats_unchanged=True,models_configs_points_changed=False,
    queries_or_measurements_running_during_copy=False,seconds=time.perf_counter()-started,
    root_free_bytes=shutil.disk_usage('/root').free,
    final_persistent_storage_delivery_still_required=True)
dump(R/'reviews/storage_RAM_staging.json',receipt)
assert receipt['root_free_bytes']>=150*(1<<20)
print(json.dumps(receipt),flush=True)
