"""Zstd ignores file symlink inputs; bind manifests to the verified durable physical file."""
from checkpoint_storage import *
assert STABLE.is_dir() and not STABLE.is_symlink()
identity=STABLE/'persistent_file_identity.json.gz';prior=json.load(gzip.open(identity,'rt'))
snapshot=STABLE/'reboot_recovery/persistent_identity_before_archive_path_resolution.json.gz'
assert not snapshot.exists();copy_verified(identity,snapshot)
rows=[]
for p in sorted(STABLE.rglob('packet_archive.json')):
    old=read(p);archive=Path(old['archive']);actual=archive.resolve()
    assert sha(actual)==old['archive_sha256']
    if str(actual)==str(archive):continue
    assert actual.is_relative_to(OVERFLOW)
    before=p.read_bytes();old_sha=hashlib.sha256(before).hexdigest()
    saved=p.parent/'packet_archive.before_resolved_path.json.gz';assert not saved.exists()
    with gzip.open(saved,'wb') as f:f.write(before)
    new=dict(old,archive=str(actual));dump(p,new)
    assert dict(new,archive=old['archive'])==old
    rows.append(dict(path=str(p.relative_to(STABLE)),old_sha256=old_sha,new_sha256=sha(p),
        snapshot=str(saved.relative_to(STABLE)),snapshot_sha256=sha(saved),
        previous_archive_path=str(archive),resolved_durable_archive=str(actual),payload_archive_sha256=sha(actual),
        only_archive_path_field_changed=True))
allowed={x['path']:x for x in rows}
for x in prior:
    actual=sha(STABLE/x['path'])
    if actual!=x['sha256']:
        bridge=allowed[x['path']];assert bridge['old_sha256']==x['sha256'] and bridge['new_sha256']==actual
        assert hashlib.sha256(gzip.decompress((STABLE/bridge['snapshot']).read_bytes())).hexdigest()==x['sha256']
files=[dict(path=str(p.relative_to(STABLE)),bytes=p.stat().st_size,sha256=sha(p))
       for p in sorted(STABLE.rglob('*')) if p.is_file() and p!=identity]
with gzip.open(identity,'wt') as out:json.dump(files,out,separators=(',',':'))
dump(R/'reviews/archive_path_resolution_bridge.json',dict(status='PASS_PATH_ONLY_DURABLE_ARCHIVE_BINDING',
    archives=rows,raw_payload_bytes_changed=False,original_archive_loader_changed=False,
    original_manifest_snapshot_identity_preserved=True))
print('ARCHIVE_PHYSICAL_PATHS_BOUND',len(rows),flush=True)
