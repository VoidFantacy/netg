import hashlib, json, os, signal, struct, subprocess, time
from pathlib import Path
import numpy as np

R=Path('/data/netg/ACSG')
O=Path(__file__).resolve().parents[1]
C=R/'entry_method_exploration/20260913_until2100_v1'
E73=C/'stage14_compact_modes_v1'
DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
def read(p): return json.loads(Path(p).read_text())
def dump(p,x): Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ident(p):
    p=Path(p);s=p.stat()
    return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(p))
def freeze(p,paths): dump(p,[ident(x) for x in sorted(set(map(Path,paths)))])
def check(p):
    for x in read(p):
        f=Path(x['path']);assert f.stat().st_size==x['bytes'] and sha(f)==x['sha256'],f
def resources():
    assert os.statvfs(O).f_bavail*os.statvfs(O).f_frsize >= 5*2**30,'free disk <5GiB'
    assert sum(p.stat().st_size for p in O.rglob('*') if p.is_file()) < 256*2**20,'output cap'
def native(kind,name,argv,calls=0):
    resources();ledger=read(O/'logs/jobs.json');assert name not in [x['name'] for x in ledger]
    assert sum(x['reserved_NSG'] for x in ledger)+calls<=200000
    assert sum(x['kind']=='build' for x in ledger)+(kind=='build')<=6
    assert sum(x.get('seconds',0) for x in ledger)<2400
    rec=dict(name=name,kind=kind,argv=list(map(str,argv)),reserved_NSG=calls,status='RESERVED',start=time.time())
    ledger.append(rec);dump(O/'logs/jobs.json',ledger)
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_DYNAMIC='FALSE',MKL_DYNAMIC='FALSE')
    log=O/'logs'/(name+'.log');begin=time.monotonic();rss=0;seen=[]
    with log.open('x') as f:
        p=subprocess.Popen(list(map(str,argv)),stdout=f,stderr=subprocess.STDOUT,env=env,preexec_fn=lambda:os.sched_setaffinity(0,{15}),start_new_session=True)
        rec['pid']=p.pid;rec['status']='RUNNING';dump(O/'logs/jobs.json',ledger)
        try:
            while p.poll() is None:
                assert time.monotonic()-begin<600,'native timeout'
                try:
                    lines=Path(f'/proc/{p.pid}/status').read_text().splitlines()
                    stat={x.split(':',1)[0]:x.split(':',1)[1].strip() for x in lines if ':' in x}
                    threads=int(stat['Threads']);assert threads==1,'process thread violation'
                    if 'VmRSS' in stat:rss=max(rss,int(stat['VmRSS'].split()[0]))
                    assert rss<32*2**20,'RSS >32GiB'
                    assert os.sched_getaffinity(p.pid)=={15}
                    if threads not in seen:seen.append(threads)
                except (FileNotFoundError,ProcessLookupError): pass
                time.sleep(.1)
        except BaseException:
            if p.poll() is None:os.killpg(p.pid,signal.SIGKILL)
            p.wait();rec['status']='KILLED';dump(O/'logs/jobs.json',ledger);raise
    rec.update(status='COMPLETE' if p.returncode==0 else 'FAILED',exit_code=p.returncode,seconds=time.monotonic()-begin,sampled_peak_RSS_KiB=rss,observed_threads=seen)
    if kind=='build' and p.returncode==0:
        rec['native_build']=json.loads(log.read_text().strip().splitlines()[-1])
    dump(O/'logs/jobs.json',ledger);print(name,rec['status'],round(rec['seconds'],3),flush=True)
    assert p.returncode==0,log
    resources()
    return rec
def inspect_graph(path,W,labels):
    data=Path(path).read_bytes();head=struct.unpack_from('<6QiI3QdQ',data)
    off,mx,n,size,label,coord,level,entry,M,M0,m,mult,ef=head
    assert off==0 and mx==n==len(W) and M==m==16 and M0==32 and ef==200
    assert label-coord==W.shape[1]*4 and coord==132
    start=96;cursor=start+n*size;levels=[];upper=[];edges=[]
    for i in range(n):
        nb=struct.unpack_from('<I',data,cursor)[0];cursor+=4;assert nb%68==0
        levels.append(nb//68);upper.append(data[cursor:cursor+nb]);cursor+=nb
    assert cursor==len(data) and max(levels)==level and 0<=entry<n
    for i in range(n):
        at=start+i*size
        assert struct.unpack_from('<Q',data,at+label)[0]==int(labels[i])
        assert data[at+coord:at+label]==W[i].tobytes()
        blocks=[data[at:at+132]]+[upper[i][j*68:(j+1)*68] for j in range(levels[i])]
        for lev,b in enumerate(blocks):
            count=struct.unpack_from('<H',b)[0];assert count<=(32 if lev==0 else 16)
            adj=np.frombuffer(b,'<u4',count=count,offset=4)
            assert (adj<n).all() and len(set(map(int,adj)))==count and i not in adj
            edges.append([i,lev,list(map(int,adj))])
    return dict(sha256=sha(path),nodes=n,level=level,entry=entry,levels=levels,edges=edges)
def install(source,old,new,labels,dest):
    assert not dest.exists() and old.shape==new.shape
    inspect_graph(source,old,labels)
    before=Path(source).read_bytes();data=bytearray(before)
    h=struct.unpack_from('<6QiI3QdQ',data);n,size,label,coord=h[2:6]
    for i in range(n):data[96+i*size+coord:96+i*size+label]=new[i].tobytes()
    restored=bytearray(data)
    for i in range(n):restored[96+i*size+coord:96+i*size+label]=old[i].tobytes()
    assert bytes(restored)==before
    dest.write_bytes(data);result=inspect_graph(dest,new,labels)
    result['all_nonvector_bytes_preserved']=True
    return result
