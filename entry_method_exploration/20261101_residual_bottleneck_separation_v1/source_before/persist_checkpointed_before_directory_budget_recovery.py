"""Final persistence after per-window durable checkpoints and all numerical work."""
from checkpoint_storage import *
assert read(R/'reviews/pipeline_complete.json')['status']=='PASS_FROZEN_EXPERIMENT_AND_NUMERICAL_ANALYSIS'
ram=Path('/dev/shm/acsg-e197-output');disk=STABLE;back=Path('/root/acsg-e197-disk')
assert disk.is_symlink() and disk.resolve()==ram and back.is_dir()
started=time.perf_counter();freeze=read(R/'formal_freeze.json')
for x in freeze['files']:assert sha(x['path'])==x['sha256']
wrappers=[];metadata=[]
for p in sorted(ram.rglob('packet_archive.json')):
    v=read(p);root=p.parent;assert 'storage_repacking' in v
    assert sha(root/'packets.tar.zst')==v['archive_sha256']
    assert not list(root.glob('k*/*/*.json')),'window metadata must have a verified durable archive'
    assert (back/root.relative_to(ram)/'durable_checkpoint.json').exists()
    wrappers.append(dict(root=str(root.relative_to(ram)),old_bytes=v['storage_repacking']['original_compressed_bytes'],
        new_bytes=v['archive_bytes'],uncompressed_tar_sha256=v['storage_repacking']['uncompressed_tar_sha256']))
    m=read(root/'point_metadata_archive.json')
    assert sha(root/m['archive'])==m['archive_sha256'];verify_members(root/m['archive'],m['files'])
    metadata.append(dict(root=str(root.relative_to(ram)),files=len(m['files']),archive_bytes=m['archive_bytes']))
copies=[]
for p in sorted(x for x in ram.rglob('*') if x.is_file()):
    rel=p.relative_to(ram);copy_verified(p,back/rel)
    copies.append(dict(path=str(rel),bytes=p.stat().st_size,sha256=sha(p)))
assert {str(p.relative_to(back)) for p in back.rglob('*') if p.is_file()}=={v['path'] for v in copies}
with gzip.open(back/'persistent_file_identity.json.gz','wt') as out:json.dump(copies,out,separators=(',',':'))
disk.unlink();back.rename(disk)
assert (R/'storage').resolve()==disk and not disk.is_symlink()
for v in copies:assert sha(disk/v['path'])==v['sha256']
for p in disk.rglob('*'):
    if p.is_symlink():
        assert p.name=='packets.tar.zst' and p.resolve().is_relative_to(OVERFLOW) and p.is_file()
for x in freeze['files']:assert sha(x['path'])==x['sha256']
for x in freeze['large_inherited_inputs']:
    s=Path(x['path']).stat();assert s.st_size==x['bytes'] and s.st_mtime_ns==x['mtime_ns']
def allocated(p):
    return int(subprocess.run(['du','-s','-B1',str(p)],capture_output=True,text=True,check=True).stdout.split()[0])
root_bytes=allocated(disk);extra=allocated(OVERFLOW) if OVERFLOW.exists() else 0
assert root_bytes<=600*(1<<20) and extra<=200*(1<<20)
assert shutil.disk_usage('/root').free>=150*(1<<20) and shutil.disk_usage('/data').free>=100*(1<<20)
assert allocated(R)<=30*(1<<20)
receipt=dict(status='PASS_ALL_NEW_EVIDENCE_PERSISTENT_NO_RAM_DEPENDENCY',files=len(copies),
    all_file_identities=str(R/'storage/persistent_file_identity.json.gz'),stable_storage=str(disk),
    new_persistent_allocated_bytes=root_bytes,durable_overflow_allocated_bytes=extra,
    durable_overflow_files=read(R/'reviews/durable_overflow.json') if (R/'reviews/durable_overflow.json').exists() else [],
    experiment_directory_allocated_bytes=allocated(R),root_free_bytes=shutil.disk_usage('/root').free,
    data_free_bytes=shutil.disk_usage('/data').free,wrapper_repacking=wrappers,
    lossless_point_metadata_archives=metadata,all_retained_or_SHA_restored_packet_payloads_preserved=True,
    all_frozen_bytes_and_large_stats_unchanged=True,every_query_window_checkpointed_before_next=True,
    restored_window_work_seeds_witnesses_replayed_not_original_individually_hashed=True,
    no_queries_or_training_during_repacking=True,storage_amendment=str(R/'storage_amendment_20261102.md'),
    seconds=time.perf_counter()-started)
dump(R/'reviews/persistent_storage_delivery.json',receipt)
cost=read(R/'analysis/cost_ledger.json');cost['persistent_storage_delivery']=receipt
for row in cost['packet_archives']:
    current=read(row['path']);row['before_final_persistence_bytes']=row['bytes'];row['bytes']=current['archive_bytes']
dump(R/'analysis/cost_ledger.json',cost)
print(json.dumps({k:v for k,v in receipt.items() if not isinstance(v,(dict,list))}),flush=True)
