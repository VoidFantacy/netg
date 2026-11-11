"""Lossless per-window durable checkpoints. Run only between native query processes."""
from common import *
from archive import archive
import gzip,io,shutil,tarfile
STABLE=Path('/root/acsg-e197-storage')
OVERFLOW=Path('/data/acsg-e197-durable-overflow')

def ensure_disk_capacity(required):
    # Storage-only amendment: leave root220MiB headroom; overflow <=200MiB, /data free >=100MiB.
    durable=Path('/root/acsg-e197-disk') if Path('/root/acsg-e197-disk').exists() else STABLE
    while shutil.disk_usage('/root').free < required+220*(1<<20):
        candidates=[p for p in durable.rglob('packets.tar.zst') if p.is_file() and not p.is_symlink()]
        assert candidates,'No eligible completed evidence archive to relocate'
        p=max(candidates,key=lambda p:p.stat().st_size);rel=p.relative_to(durable);target=OVERFLOW/rel
        used=sum(q.stat().st_size for q in OVERFLOW.rglob('*') if q.is_file()) if OVERFLOW.exists() else 0
        allowed=used+p.stat().st_size<=200*(1<<20) and shutil.disk_usage('/data').free-p.stat().st_size>=100*(1<<20)
        if not allowed and shutil.disk_usage('/root').free>=required+170*(1<<20):
            return # Keep the hard150MiB floor plus20MiB, even when preferred220MiB headroom cannot be extended.
        assert allowed,('persistent storage capacity',used,required,shutil.disk_usage('/root').free)
        assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True)
        digest=sha(p);shutil.copy2(p,target);assert sha(target)==digest
        p.unlink();p.symlink_to(target)
        ledger=R/'reviews/durable_overflow.json';v=read(ledger) if ledger.exists() else []
        v.append(dict(canonical_relative_path=str(rel),durable_path=str(target),sha256=digest,bytes=target.stat().st_size))
        dump(ledger,v)

def tar_sha(p):
    process=subprocess.Popen(['zstd','-q','-d','-c',str(Path(p).resolve())],stdout=subprocess.PIPE)
    h=hashlib.sha256()
    for b in iter(lambda:process.stdout.read(8<<20),b''):h.update(b)
    assert process.wait()==0
    return h.hexdigest()

def verify_members(p,records):
    expected={x['member']:x for x in records};seen=set()
    process=subprocess.Popen(['zstd','-q','-d','-c',str(Path(p).resolve())],stdout=subprocess.PIPE)
    with tarfile.open(fileobj=process.stdout,mode='r|') as tar:
        for item in tar:
            data=tar.extractfile(item).read();v=expected[item.name]
            assert item.name not in seen and len(data)==v['bytes'] and hashlib.sha256(data).hexdigest()==v['sha256']
            seen.add(item.name)
    assert process.wait()==0 and seen==set(expected)

def copy_verified(source,target):
    source=Path(source);target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    digest=sha(source)
    if source.resolve()!=target.resolve() and (not target.exists() or sha(target)!=digest):
        if str(target.resolve()).startswith('/root/'):
            ensure_disk_capacity(source.stat().st_size)
        temp=target.with_name(target.name+'.checkpoint_tmp')
        assert not temp.exists();shutil.copy2(source,temp);assert sha(temp)==digest;temp.replace(target)
    assert sha(target)==digest

def compact(root,durable=None):
    began=time.perf_counter();root=Path(root).resolve();storage=(R/'storage').resolve()
    rel=root.relative_to(storage);durable=root if durable is None else Path(durable).resolve()
    assert str(durable).startswith(('/root/acsg-e197-storage/','/root/acsg-e197-disk/'))
    manifest=root/'packet_archive.json'
    if not manifest.exists():archive(root)
    v=read(manifest);p=Path(v['archive'])
    # Reboot recovery may have changed the alias, but archive member identity remains binding.
    if not p.exists():p=root/'packets.tar.zst'
    assert sha(p)==v['archive_sha256']
    if 'storage_repacking' not in v:
        previous=manifest.read_bytes();old_sha=sha(p);old_size=p.stat().st_size;before=tar_sha(p)
        temp=Path('/dev/shm')/('e197_recompress_'+str(time.time_ns())+'.zst')
        with temp.open('wb') as out:
            dec=subprocess.Popen(['zstd','-q','-d','-c',str(p)],stdout=subprocess.PIPE)
            enc=subprocess.Popen(['zstd','-q','-19','--long=27','-T1','-c'],stdin=dec.stdout,stdout=out)
            dec.stdout.close();assert enc.wait()==0 and dec.wait()==0
        assert tar_sha(temp)==before
        if temp.stat().st_size<old_size:copy_verified(temp,p)
        temp.unlink()
        prior=root/'packet_archive.before_checkpoint_repacking.json.gz'
        assert not prior.exists()
        with gzip.open(prior,'wb') as out:out.write(previous)
        v['storage_repacking']=dict(original_compressed_sha256=old_sha,original_compressed_bytes=old_size,
            uncompressed_tar_sha256=before,all_original_tar_bytes_equal=True,zstd_wrapper_bytes_may_change=True,
            prior_manifest=prior.name)
    durable_archive=durable/'packets.tar.zst'
    v['archive']=str(durable_archive.resolve()) if durable_archive.is_symlink() else str(STABLE/rel/'packets.tar.zst')
    v['archive_sha256']=sha(p);v['archive_bytes']=p.stat().st_size
    dump(manifest,v)

    receipt=root/'point_metadata_archive.json'
    paths=sorted(p for p in root.glob('k*/*/*.json') if p.is_file())
    if paths:
        protected={Path(x['path']).resolve() for x in read(R/'formal_freeze.json')['files']}
        assert not any(p.resolve() in protected for p in paths)
        assert not receipt.exists()
        records=[];outpath=root/'point_metadata.tar.zst';assert not outpath.exists()
        with outpath.open('wb') as out:
            process=subprocess.Popen(['zstd','-q','-15','-T1','-c'],stdin=subprocess.PIPE,stdout=out)
            with tarfile.open(fileobj=process.stdin,mode='w|') as tar:
                for p in paths:
                    data=p.read_bytes();member=str(p.relative_to(root));item=tarfile.TarInfo(member)
                    item.size=len(data);item.mtime=0;tar.addfile(item,io.BytesIO(data))
                    records.append(dict(member=member,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
            process.stdin.close();assert process.wait()==0
        verify_members(outpath,records)
        dump(receipt,dict(status='PASS_ALL_ORIGINAL_POINT_JSON_BYTES_ROUNDTRIP',archive=outpath.name,
            archive_sha256=sha(outpath),archive_bytes=outpath.stat().st_size,files=records,
            recovered_window=(root/'recovery_complete.json').exists(),
            complete_result_config_environment_and_packet_manifest_stay_readable=True))
        copy_verified(outpath,durable/outpath.name);copy_verified(receipt,durable/receipt.name)
        verify_members(durable/outpath.name,records)
        for p,record in zip(paths,records):
            q=durable/record['member']
            if p.resolve()!=q.resolve() and q.exists():assert sha(q)==record['sha256'];q.unlink()
            assert sha(p)==record['sha256'];p.unlink()
        for base in {root,durable}:
            dirs=[d for top in base.glob('k*') if top.is_dir() for d in [top,*top.rglob('*')] if d.is_dir()]
            for d in sorted(dirs,key=lambda x:len(x.parts),reverse=True):
                if not any(d.iterdir()):d.rmdir()
    result=checkpoint_tree(root,durable)
    result.update(packet_archive_bytes=v['archive_bytes'],seconds=time.perf_counter()-began,
        all_raw_packet_and_metadata_payloads_preserved=True)
    dump(root/'durable_checkpoint.json',result);copy_verified(root/'durable_checkpoint.json',durable/'durable_checkpoint.json')
    return result

def checkpoint_tree(root,durable):
    root=Path(root).resolve();durable=Path(durable).resolve();rows=[]
    assert str(durable).startswith(('/root/acsg-e197-storage/','/root/acsg-e197-disk/'))
    for p in sorted(x for x in root.rglob('*') if x.is_file() and x.name!='durable_checkpoint.json'):
        rel=p.relative_to(root);copy_verified(p,durable/rel)
        rows.append(dict(path=str(rel),bytes=p.stat().st_size,sha256=sha(p)))
    return dict(status='PASS_WINDOW_DURABLE_FILE_COPY_AND_HASH',files=rows,
        canonical_root=str(R/'storage'/root.relative_to((R/'storage').resolve())),
        durable_copy_path_at_checkpoint=str(durable),verified_before_next_query_stage=True)

if __name__=='__main__':
    root=Path(sys.argv[1]);target=Path(sys.argv[2]) if len(sys.argv)>2 else None
    result=compact(root,target)
    print('DURABLE_CHECKPOINT',result['canonical_root'],len(result['files']),result['packet_archive_bytes'],flush=True)
