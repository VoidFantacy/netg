"""Lossless solid archives of E191's own, already-audited timed packets."""
import collections,gzip,hashlib,json,os,subprocess,sys,tarfile,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];STORAGE=(R/'storage').resolve();ZSTD='/usr/bin/zstd'
NAMES=['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']
CACHE=collections.OrderedDict()
def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def readj(path):return json.loads(Path(path).read_text())
def writej(path,value):
    tmp=Path(str(path)+'.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');os.replace(tmp,path)
def root_for(path):
    p=Path(path).resolve();rel=p.relative_to(STORAGE)
    assert rel.parts[0] in ['results','dense_controls']
    return STORAGE/rel.parts[0]/rel.parts[1]
def decode(root,retain=False):
    meta=readj(root/'raw_packet_archive.json');archive=Path(meta['archive'])
    assert meta['status'].startswith('PASS') and digest(archive)==meta['archive_sha256']
    expected={x['name']:x for x in meta['files']};seen=set();data={}
    p=subprocess.Popen([ZSTD,'-d','-q','-c','-M256MB',str(archive)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        with tarfile.open(fileobj=p.stdout,mode='r|') as src:
            for member in src:
                assert member.isfile() and member.name in expected and member.name not in seen
                info=expected[member.name];assert member.size==info['bytes'];seen.add(member.name)
                h=hashlib.sha256();parts=[]
                with src.extractfile(member) as f:
                    for b in iter(lambda:f.read(8<<20),b''):
                        h.update(b)
                        if retain:parts.append(b)
                assert h.hexdigest()==info['sha256'],member.name
                if retain:data[member.name]=b''.join(parts)
        p.stdout.read();stderr=p.stderr.read();assert p.wait()==0,stderr.decode(errors='replace')
    finally:
        if p.poll() is None:p.kill();p.wait()
    assert seen==set(expected)
    return data
def read_bytes(path):
    p=Path(path)
    if p.exists():return p.read_bytes()
    if Path(str(p)+'.gz').exists():
        with gzip.open(str(p)+'.gz','rb') as f:return f.read()
    root=root_for(p);key=str(root)
    if key not in CACHE:
        CACHE[key]=decode(root,retain=True)
        while len(CACHE)>2:CACHE.popitem(last=False)
    CACHE.move_to_end(key)
    return CACHE[key][str(p.resolve().relative_to(root))]
def archive(stage,ds):
    assert stage in ['results','dense_controls'];root=STORAGE/stage/ds
    assert root.parent==(STORAGE/stage) and root.is_dir();t=time.perf_counter()
    audit=R/f"reviews/{'results_audit' if stage=='results' else 'dense_results_audit'}_{ds}.json"
    assert readj(audit)['status'].startswith('PASS') and readj(audit)['all_actual_packet_hashes_recomputed']
    meta_path=root/'raw_packet_archive.json'
    if meta_path.exists():
        meta=readj(meta_path);decode(root)
    else:
        done=readj(root/'complete.json');files=[]
        methods={'GT10':0,'B32':1,'REUSE-PQ':2,'REUSE-SQ':3,'MAIN-SQ':4}
        for point in sorted(done['results'],key=lambda x:(x['K'],x['L'],methods[x['method']])):
            for name in NAMES:
                path=Path(point['result_dir'])/'raw'/name
                assert path.resolve().is_relative_to(root)
                st=path.stat();files.append(dict(name=str(path.relative_to(root)),path=str(path),bytes=st.st_size,mtime_ns=st.st_mtime_ns,sha256=digest(path)))
        target=root/'raw_packets.tar.zst';tmp=Path(str(target)+'.partial');assert not target.exists() and not tmp.exists()
        stderr=R/f'reviews/archive_{stage}_{ds}.stderr.txt'
        with tmp.open('xb') as out,stderr.open('xb') as err:
            p=subprocess.Popen([ZSTD,'-6','-T1','--long=27','--check','-q','-c'],stdin=subprocess.PIPE,stdout=out,stderr=err)
            try:
                with tarfile.open(fileobj=p.stdin,mode='w|',format=tarfile.PAX_FORMAT) as tar:
                    for info in files:
                        item=tarfile.TarInfo(info['name']);item.size=info['bytes'];item.mode=0o644;item.mtime=info['mtime_ns']//10**9
                        with Path(info['path']).open('rb') as f:tar.addfile(item,f)
                p.stdin.close();assert p.wait()==0,stderr.read_text()
            finally:
                if p.poll() is None:p.kill();p.wait()
            out.flush();os.fsync(out.fileno())
        os.replace(tmp,target)
        meta=dict(status='PASS_SOLID_ARCHIVE_CREATED_PENDING_SOURCE_REMOVAL',stage=stage,dataset=ds,
                  archive=str(target),archive_sha256=digest(target),archive_bytes=target.stat().st_size,
                  raw_bytes=sum(x['bytes'] for x in files),files=files,source_audit=str(audit),source_audit_sha256=digest(audit),
                  format='POSIX tar stream + zstd level6, T1, long window27, checksum; original byte streams unchanged',
                  original_files_removed=False)
        writej(meta_path,meta);decode(root)
    for info in meta['files']:
        path=Path(info['path'])
        if path.exists():assert digest(path)==info['sha256'];path.unlink()
    meta.update(status='PASS_VERIFIED_LOSSLESS_TIMED_PACKET_ARCHIVE',original_files_removed=True,seconds=time.perf_counter()-t)
    writej(meta_path,meta)
    print(json.dumps(dict(status=meta['status'],stage=stage,dataset=ds,raw_MiB=meta['raw_bytes']/2**20,archive_MiB=meta['archive_bytes']/2**20,saved_MiB=(meta['raw_bytes']-meta['archive_bytes'])/2**20,seconds=meta['seconds'])),flush=True)
def restore(stage,ds,destination=None):
    root=STORAGE/stage/ds;meta=readj(root/'raw_packet_archive.json');data=decode(root,retain=True)
    out=Path(destination).resolve() if destination else root
    for info in meta['files']:
        p=out/info['name'];assert '..' not in Path(info['name']).parts
        if p.exists():assert digest(p)==info['sha256'];continue
        p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data[info['name']])
        os.utime(p,ns=(info['mtime_ns'],info['mtime_ns']))
    print('PASS exact raw files restored; solid archive retained',flush=True)
if __name__=='__main__':
    mode,stage,ds=sys.argv[1:4]
    if mode=='archive':archive(stage,ds)
    elif mode=='verify':decode(STORAGE/stage/ds);print('PASS all archived original file bytes')
    elif mode=='restore':restore(stage,ds,sys.argv[4] if len(sys.argv)>4 else None)
    else:raise ValueError(mode)
