"""Lossless E197 packet/payload archive. Never touches earlier experiment files."""
from common import *
import gzip, io, tarfile

def archive(root):
    root=Path(root).resolve()
    assert root.is_relative_to((R/'storage').resolve())
    manifest=root/'packet_archive.json'
    if manifest.exists():return read(manifest)
    paths=sorted(p for p in root.rglob('*') if p.is_file() and
                 ('raw' in p.parts or p.suffix in ['.u64','.i32','.f64'] or p.name in ['witness.bin.gz','selection.bin.gz']))
    assert paths,root
    began=time.perf_counter(); destination=root/'packets.tar.zst'; assert not destination.exists()
    records=[]
    with destination.open('wb') as output:
        proc=subprocess.Popen(['zstd','-q','-15','-T1','-c'],stdin=subprocess.PIPE,stdout=output)
        with tarfile.open(fileobj=proc.stdin,mode='w|') as tar:
            for p in paths:
                original=p.read_bytes(); payload=gzip.decompress(original) if p.name in ['witness.bin.gz','selection.bin.gz'] else original
                rel=str(p.relative_to(root));member=rel[:-3] if p.name in ['witness.bin.gz','selection.bin.gz'] else rel
                info=tarfile.TarInfo(member);info.size=len(payload);info.mtime=0
                tar.addfile(info,io.BytesIO(payload))
                records.append(dict(path=rel,member=member,original_bytes=len(original),
                    original_sha256=hashlib.sha256(original).hexdigest(),payload_bytes=len(payload),
                    payload_sha256=hashlib.sha256(payload).hexdigest(),
                    transform='gzip_payload' if p.name in ['witness.bin.gz','selection.bin.gz'] else 'identity'))
        proc.stdin.close();assert proc.wait()==0
    expected={x['member']:x for x in records};seen=set()
    proc=subprocess.Popen(['zstd','-q','-d','-c',str(destination)],stdout=subprocess.PIPE)
    with tarfile.open(fileobj=proc.stdout,mode='r|') as tar:
        for item in tar:
            data=tar.extractfile(item).read();ref=expected[item.name]
            assert len(data)==ref['payload_bytes'] and hashlib.sha256(data).hexdigest()==ref['payload_sha256']
            seen.add(item.name)
    assert proc.wait()==0 and seen==set(expected)
    result=dict(status='PASS_LOSSLESS_PACKET_AND_WITNESS_PAYLOAD_ARCHIVE',archive=str(destination),
        archive_sha256=sha(destination),archive_bytes=destination.stat().st_size,
        original_bytes=sum(x['original_bytes'] for x in records),
        logical_payload_bytes=sum(x['payload_bytes'] for x in records),files=records,
        raw_timed_arrays_byte_exact=True,witness_uncompressed_payload_byte_exact=True,
        gzip_container_bytes_not_claimed_preserved=True,seconds=time.perf_counter()-began)
    dump(manifest,result)
    # Only new E197 files, after complete round-trip verification. Original hash is retained.
    for p,record in zip(paths,records):
        assert sha(p)==record['original_sha256'];p.unlink()
    return result

def load_packets(root):
    root=Path(root)
    manifest=read(root/'packet_archive.json');data={}
    proc=subprocess.Popen(['zstd','-q','-d','-c',manifest['archive']],stdout=subprocess.PIPE)
    with tarfile.open(fileobj=proc.stdout,mode='r|') as tar:
        for item in tar:data[item.name]=tar.extractfile(item).read()
    assert proc.wait()==0
    for ref in manifest['files']:
        assert hashlib.sha256(data[ref['member']]).hexdigest()==ref['payload_sha256']
    return {ref['path']:data[ref['member']] for ref in manifest['files']}

if __name__=='__main__':
    value=archive(sys.argv[1]);print(json.dumps({k:v for k,v in value.items() if k!='files'}),flush=True)
