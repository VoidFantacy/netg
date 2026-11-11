from checkpoint_storage import *
started=time.perf_counter();rows=[]
assert not STABLE.is_symlink()
for p in sorted((R/'storage').rglob('packet_archive.json')):
    v=compact(p.parent);rows.append(dict(root=v['canonical_root'],files=len(v['files']),archive_bytes=v['packet_archive_bytes']))
    print('INITIAL_DURABLE_COMPACT',rows[-1],flush=True)
for x in read(R/'formal_freeze.json')['files']:assert sha(x['path'])==x['sha256']
dump(R/'reviews/reboot_initial_compaction.json',dict(status='PASS_INITIAL_EVIDENCE_DURABLE_COMPACT',roots=rows,
    seconds=time.perf_counter()-started,root_free_bytes=shutil.disk_usage('/root').free))
