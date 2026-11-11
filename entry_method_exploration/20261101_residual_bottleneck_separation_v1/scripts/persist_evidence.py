"""After all query work: compact only new evidence, verify, and restore durable paths."""
from common import *
import gzip, io, os, shutil, tarfile

assert read(R/'reviews/pipeline_complete.json')['status']=='PASS_FROZEN_EXPERIMENT_AND_NUMERICAL_ANALYSIS'
ram=Path('/dev/shm/acsg-e197-output')
disk=Path('/root/acsg-e197-storage')
back=Path('/root/acsg-e197-disk')
assert disk.is_symlink() and disk.resolve()==ram and back.is_dir()
started=time.perf_counter()
freeze=read(R/'formal_freeze.json')
protected={Path(x['path']).resolve() for x in freeze['files']}
for x in freeze['files']:assert sha(x['path'])==x['sha256']

def tar_digest(path):
    proc=subprocess.Popen(['zstd','-q','-d','-c',str(path)],stdout=subprocess.PIPE)
    h=hashlib.sha256()
    for b in iter(lambda:proc.stdout.read(8<<20),b''):h.update(b)
    assert proc.wait()==0
    return h.hexdigest()

def verify_metadata(archive,records):
    expected={v['member']:v for v in records};seen=set()
    proc=subprocess.Popen(['zstd','-q','-d','-c',str(archive)],stdout=subprocess.PIPE)
    with tarfile.open(fileobj=proc.stdout,mode='r|') as tar:
        for item in tar:
            payload=tar.extractfile(item).read();ref=expected[item.name]
            assert len(payload)==ref['bytes'] and hashlib.sha256(payload).hexdigest()==ref['sha256']
            seen.add(item.name)
    assert proc.wait()==0 and seen==set(expected)

wrappers=[];metadata=[]
for manifest in sorted(ram.rglob('packet_archive.json')):
    root=manifest.parent;v=read(manifest);archive=root/'packets.tar.zst'
    assert sha(archive)==v['archive_sha256'] and archive not in protected
    old_manifest=manifest.read_bytes();old_sha=sha(archive);old_bytes=archive.stat().st_size
    before=tar_digest(archive);temp=root/'packets.long.tmp.zst'
    assert not temp.exists()
    with temp.open('wb') as out:
        dec=subprocess.Popen(['zstd','-q','-d','-c',str(archive)],stdout=subprocess.PIPE)
        enc=subprocess.Popen(['zstd','-q','-19','--long=27','-T1','-c'],stdin=dec.stdout,stdout=out)
        dec.stdout.close();assert enc.wait()==0 and dec.wait()==0
    assert tar_digest(temp)==before # Also checks decoding with the unchanged default loader.
    if temp.stat().st_size<old_bytes:temp.replace(archive)
    else:temp.unlink()
    with gzip.open(root/'packet_archive.before_storage_repacking.json.gz','wb') as out:out.write(old_manifest)
    v['archive']=str(disk/root.relative_to(ram)/archive.name)
    v['archive_sha256']=sha(archive);v['archive_bytes']=archive.stat().st_size
    v['storage_repacking']=dict(original_compressed_sha256=old_sha,original_compressed_bytes=old_bytes,
        uncompressed_tar_sha256=before,all_original_tar_bytes_equal=True,
        zstd_wrapper_bytes_may_change=True,prior_manifest='packet_archive.before_storage_repacking.json.gz')
    dump(manifest,v)
    wrappers.append(dict(root=str(root.relative_to(ram)),old_bytes=old_bytes,new_bytes=v['archive_bytes'],
        old_sha256=old_sha,new_sha256=v['archive_sha256'],uncompressed_tar_sha256=before))

    # Per-point JSON is duplicated in complete.json, but preserve every original byte in an archive.
    paths=sorted(p for p in root.glob('k*/*/*.json') if p.is_file())
    if not paths:continue
    assert all(p.resolve() not in protected for p in paths)
    output=root/'point_metadata.tar.zst';assert not output.exists()
    records=[]
    with output.open('wb') as out:
        proc=subprocess.Popen(['zstd','-q','-15','-T1','-c'],stdin=subprocess.PIPE,stdout=out)
        with tarfile.open(fileobj=proc.stdin,mode='w|') as tar:
            for p in paths:
                b=p.read_bytes();name=str(p.relative_to(root));info=tarfile.TarInfo(name)
                info.size=len(b);info.mtime=0;tar.addfile(info,io.BytesIO(b))
                records.append(dict(member=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
        proc.stdin.close();assert proc.wait()==0
    verify_metadata(output,records)
    receipt=dict(status='PASS_ALL_ORIGINAL_POINT_JSON_BYTES_ROUNDTRIP',archive=output.name,
        archive_sha256=sha(output),archive_bytes=output.stat().st_size,files=records,
        complete_result_config_environment_and_packet_manifest_stay_readable=True)
    dump(root/'point_metadata_archive.json',receipt)
    # A durable verified archive precedes removal of any corresponding disk temporary copy.
    target=back/root.relative_to(ram);target.mkdir(parents=True,exist_ok=True)
    for source in [output,root/'point_metadata_archive.json']:
        dest=target/source.name;shutil.copy2(source,dest);assert sha(dest)==sha(source)
    verify_metadata(target/output.name,records)
    for p,ref in zip(paths,records):
        q=target/ref['member']
        if q.exists():assert sha(q)==ref['sha256'];q.unlink()
        assert sha(p)==ref['sha256'];p.unlink()
    for base in [root,target]:
        dirs=[p for top in base.glob('k*') if top.is_dir() for p in [top,*top.rglob('*')] if p.is_dir()]
        for p in sorted(dirs,key=lambda p:len(p.parts),reverse=True):
            if not any(p.iterdir()):p.rmdir()
    metadata.append(dict(root=str(root.relative_to(ram)),files=len(records),
        original_bytes=sum(x['bytes'] for x in records),archive_bytes=output.stat().st_size))
    print('COMPACTED',root.relative_to(ram),old_bytes,v['archive_bytes'],len(records),flush=True)

def allocated(path):
    p=subprocess.run(['du','-s','-B1',str(path)],capture_output=True,text=True,check=True)
    return int(p.stdout.split()[0])
projected=allocated(ram)
assert projected<=600*(1<<20),('compacted evidence exceeds persistent budget; do not discard',projected)
copies=[]
for p in sorted(x for x in ram.rglob('*') if x.is_file()):
    rel=p.relative_to(ram);q=back/rel;digest=sha(p)
    if not q.exists() or sha(q)!=digest:
        q.parent.mkdir(parents=True,exist_ok=True);temp=q.with_name(q.name+'.persist_tmp')
        assert not temp.exists();shutil.copy2(p,temp);assert sha(temp)==digest;temp.replace(q)
    assert sha(q)==digest and q.stat().st_size==p.stat().st_size
    copies.append(dict(path=str(rel),bytes=p.stat().st_size,sha256=digest))
assert {str(p.relative_to(back)) for p in back.rglob('*') if p.is_file()}=={v['path'] for v in copies}
with gzip.open(back/'persistent_file_identity.json.gz','wt') as out:json.dump(copies,out,separators=(',',':'))
assert allocated(back)<=600*(1<<20)
assert shutil.disk_usage('/root').free>=150*(1<<20)
disk.unlink();back.rename(disk)
assert (R/'storage').resolve()==disk and not disk.is_symlink()
for x in freeze['files']:assert sha(x['path'])==x['sha256'],x['path']
for x in freeze['large_inherited_inputs']:
    s=Path(x['path']).stat();assert s.st_size==x['bytes'] and s.st_mtime_ns==x['mtime_ns']
assert not any(p.is_symlink() for p in disk.rglob('*'))
for v in copies:assert sha(disk/v['path'])==v['sha256']
root_free=shutil.disk_usage('/root').free;data_free=shutil.disk_usage('/data').free
assert root_free>=150*(1<<20) and data_free>=300*(1<<20)
assert allocated(R)<=30*(1<<20)
receipt=dict(status='PASS_ALL_NEW_EVIDENCE_PERSISTENT_NO_RAM_DEPENDENCY',
    files=len(copies),all_file_identities=str(R/'storage/persistent_file_identity.json.gz'),
    new_persistent_allocated_bytes=allocated(disk),experiment_directory_allocated_bytes=allocated(R),
    root_free_bytes=root_free,data_free_bytes=data_free,wrapper_repacking=wrappers,
    lossless_point_metadata_archives=metadata,all_original_raw_and_metadata_payloads_preserved=True,
    all_frozen_bytes_and_large_stats_unchanged=True,no_queries_or_training_during_repacking=True,
    stable_storage=str(disk),seconds=time.perf_counter()-started)
dump(R/'reviews/persistent_storage_delivery.json',receipt)
cost=read(R/'analysis/cost_ledger.json');cost['persistent_storage_delivery']=receipt
for row in cost['packet_archives']:
    current=read(row['path']);row['before_repacking_bytes']=row['bytes'];row['bytes']=current['archive_bytes']
dump(R/'analysis/cost_ledger.json',cost)
print(json.dumps({k:v for k,v in receipt.items() if not isinstance(v,(dict,list))}),flush=True)
