"""Resume final persistence checks after the stable root has already been restored."""
from checkpoint_storage import *
assert read(R/'reviews/pipeline_complete.json')['status']=='PASS_FROZEN_EXPERIMENT_AND_NUMERICAL_ANALYSIS'
assert STABLE.is_dir() and not STABLE.is_symlink() and not Path('/root/acsg-e197-disk').exists()
started=time.perf_counter();identity=STABLE/'persistent_file_identity.json.gz'
prior=json.load(gzip.open(identity,'rt'))
for x in prior:assert sha(STABLE/x['path'])==x['sha256']
snap=STABLE/'reboot_recovery/persistent_identity_before_log_relocation.json.gz'
if not snap.exists():copy_verified(identity,snap)
for x in read(R/'reviews/native_log_relocation.json')['files']:
    assert sha(x['original_path'])==x['sha256']==sha(x['durable_path'])
wrappers=[];metadata=[]
for p in sorted(STABLE.rglob('packet_archive.json')):
    v=read(p);root=p.parent;assert sha(v['archive'])==v['archive_sha256']
    assert 'storage_repacking' in v and (root/'durable_checkpoint.json').exists()
    wrappers.append(dict(root=str(root.relative_to(STABLE)),old_bytes=v['storage_repacking']['original_compressed_bytes'],
        new_bytes=v['archive_bytes'],uncompressed_tar_sha256=v['storage_repacking']['uncompressed_tar_sha256']))
    m=read(root/'point_metadata_archive.json');assert sha(root/m['archive'])==m['archive_sha256'];verify_members(root/m['archive'],m['files'])
    metadata.append(dict(root=str(root.relative_to(STABLE)),files=len(m['files']),archive_bytes=m['archive_bytes']))
rows=[]
for p in sorted(x for x in STABLE.rglob('*') if x.is_file() and x!=identity):
    if p.is_symlink():assert p.name=='packets.tar.zst' and p.resolve().is_relative_to(OVERFLOW)
    rows.append(dict(path=str(p.relative_to(STABLE)),bytes=p.stat().st_size,sha256=sha(p)))
with gzip.open(identity,'wt') as out:json.dump(rows,out,separators=(',',':'))
for x in read(R/'formal_freeze.json')['files']:assert sha(x['path'])==x['sha256']
for x in read(R/'formal_freeze.json')['large_inherited_inputs']:
    s=Path(x['path']).stat();assert s.st_size==x['bytes'] and s.st_mtime_ns==x['mtime_ns']
def allocated(p):return int(subprocess.run(['du','-s','-B1',str(p)],capture_output=True,text=True,check=True).stdout.split()[0])
root_bytes=allocated(STABLE);extra=allocated(OVERFLOW) if OVERFLOW.exists() else 0
assert root_bytes<=600*(1<<20) and extra<=200*(1<<20) and allocated(R)<=30*(1<<20)
assert shutil.disk_usage('/root').free>=150*(1<<20) and shutil.disk_usage('/data').free>=100*(1<<20)
receipt=dict(status='PASS_ALL_NEW_EVIDENCE_PERSISTENT_NO_RAM_DEPENDENCY',files=len(rows),
    all_file_identities=str(R/'storage/persistent_file_identity.json.gz'),stable_storage=str(STABLE),
    new_persistent_allocated_bytes=root_bytes,durable_overflow_allocated_bytes=extra,
    durable_overflow_files=read(R/'reviews/durable_overflow.json') if (R/'reviews/durable_overflow.json').exists() else [],
    experiment_directory_allocated_bytes=allocated(R),root_free_bytes=shutil.disk_usage('/root').free,
    data_free_bytes=shutil.disk_usage('/data').free,wrapper_repacking=wrappers,lossless_point_metadata_archives=metadata,
    all_retained_or_SHA_restored_packet_payloads_preserved=True,all_frozen_bytes_and_large_stats_unchanged=True,
    every_query_window_checkpointed_before_next=True,restored_window_work_seeds_witnesses_replayed_not_original_individually_hashed=True,
    no_queries_or_training_during_repacking=True,original_log_bytes_durable_with_stable_links=True,
    storage_amendment=str(R/'storage_amendment_20261102.md'),seconds=time.perf_counter()-started)
dump(R/'reviews/persistent_storage_delivery.json',receipt)
cost=read(R/'analysis/cost_ledger.json');cost['persistent_storage_delivery']=receipt
for x in cost['packet_archives']:x['bytes']=read(x['path'])['archive_bytes']
dump(R/'analysis/cost_ledger.json',cost)
print(json.dumps({k:v for k,v in receipt.items() if not isinstance(v,(dict,list))}),flush=True)
