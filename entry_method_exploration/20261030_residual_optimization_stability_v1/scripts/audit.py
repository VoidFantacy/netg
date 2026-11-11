"""Second implementation: stdlib arrays/sets/hashlib; no NumPy or main analyzer."""
import array,hashlib,json,math,struct,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
def a(p,code):
    v=array.array(code);v.frombytes(Path(p).read_bytes());return v
ds,window=sys.argv[1:];c=read(R/f'configs/{ds}.{window}.json');root=Path(c['output_dir']);done=read(root/'complete.json');g=a(c['test_gt']['path'],'i');n=c['queries']['n'];rows=[];packets={}
for p in done['results']:
    K=p['K'];d=Path(p['result_dir'])/'raw';ids=a(d/'ids.i32','i');D=a(d/'distances.f32','f');e=a(d/'entry_ids.i32','i');z=a(d/'profile_distances.f32','f')
    assert len(ids)==len(D)==n*K and len(e)==len(z)==n*3
    h=hashlib.sha256();h.update(struct.pack('<QQ',n,K))
    for f in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:h.update((d/f).read_bytes())
    h.update(bytes(n*8));h.update(bytes(n*8))
    assert all(x['packet_sha256']==h.hexdigest() and x['threads']==1 for x in p['rounds'])
    wall=sorted(x['wall_seconds'] for x in p['rounds']);assert abs(p['qps']-n/wall[len(wall)//2])<1e-8
    hits=[]
    for i in range(n):
        v=ids[i*K:(i+1)*K];dd=D[i*K:(i+1)*K]
        assert len(set(v))==K and all(0<=x<c['base']['n'] for x in v)
        assert all(math.isfinite(x) for x in dd) and all(dd[j]<=dd[j+1] for j in range(K-1))
        hits.append(len(set(v)&set(g[i*100:i*100+K])))
    key=(K,p['L'],p['method']);packets[key]=(h.hexdigest(),hits)
    rows.append(dict(K=K,L=p['L'],method=p['method'],hits=sum(hits),failed_lt10=sum(x<10 for x in hits) if K==100 else None,sha256=h.hexdigest()))
for (K,L,m),(h,hits) in packets.items():
    base={'OPT-B32':'B32','OPT-SQ':'REUSE-SQ'}.get(m)
    if base:assert packets[K,L,base][0]==h and packets[K,L,base][1]==hits
receipt=dict(status='PASS_E194_STDLIB_ALL_PACKETS',dataset=ds,window=window,points=len(rows),queries_checked=len(rows)*n,GT_role='evaluation_after_search',rows=rows)
(R/f'reviews/{ds}.{window}.audit.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('STDLIB_AUDIT_PASS',ds,window,len(rows),flush=True)
