"""Independent standard-library-only integer, hash, wall, branch and frontier audit."""
import array,csv,hashlib,json,math,statistics,struct,subprocess,sys,tarfile,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];OLD=R.parent/'20261101_residual_bottleneck_separation_v1'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def ints(b):
    a=array.array('i');a.frombytes(b)
    if sys.byteorder!='little':a.byteswap()
    return a
def close(a,b):assert math.isclose(float(a),float(b),rel_tol=1e-10,abs_tol=1e-10),(a,b)
started=time.perf_counter();counts=dict(points=0,rounds=0,old_compatible_packets=0,branch_queries=0,frontiers=0);wall=0.
with open(R/'analysis/points.csv') as f:reported={(r['dataset'],r['window'],int(r['K']),int(r['L']),r['method']):r for r in csv.DictReader(f)}
with open(R/'analysis/frontier.csv') as f:frontier={(r['dataset'],r['window'],int(r['K']),int(r['L']),r['method']):r for r in csv.DictReader(f)}
for ds in ['coco','flickr30k','webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']:
 for window in ['A','B']:
    cfg=read(R/'configs'/f'{ds}.{window}.formal.json');root=Path(cfg['output_dir']);info=read(root/'complete.json');manifest=read(root/'packet_archive.json');assert sha(manifest['archive'])==manifest['archive_sha256'];refs={x['member']:x for x in manifest['files']};raw={};seen=set()
    proc=subprocess.Popen(['zstd','-q','-d','-c',manifest['archive']],stdout=subprocess.PIPE)
    with tarfile.open(fileobj=proc.stdout,mode='r|') as tf:
        for item in tf:
            b=tf.extractfile(item).read();ref=refs[item.name];assert hashlib.sha256(b).hexdigest()==ref['payload_sha256'] and len(b)==ref['payload_bytes'];seen.add(item.name)
            if '/raw/' in item.name or item.name.endswith(('/decisions.i32','/work.u64')):raw[item.name]=b
    assert proc.wait()==0 and seen==set(refs)
    n=cfg['queries']['n'];GT=ints(Path(cfg['test_gt']['path']).read_bytes());old=read(OLD/'storage/results'/ds/window/'complete.json');oldrows={(x['K'],x['L'],x['method']):x for x in old['results']};metrics={};outputs={}
    for p in info['results']:
        K,L,m=p['K'],p['L'],p['method'];prefix=f'k{K}/{m}_L{L}';r=reported[ds,window,K,L,m];I=ints(raw[prefix+'/raw/ids.i32']);good=[set(I[q*K:(q+1)*K])&set(GT[q*100:q*100+K]) for q in range(n)];hits=sum(map(len,good));close(r['hits'],hits);close(r['recall_pct'],100*hits/(n*K))
        if K==100:close(r['failed_lt10'],sum(len(x)<10 for x in good))
        h=hashlib.sha256(struct.pack('<QQ',n,K))
        for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:h.update(raw[prefix+'/raw/'+name])
        h.update(bytes(16*n));hh=h.hexdigest()
        for rr in p['rounds']:assert rr['threads']==1 and rr['packet_sha256']==hh;close(rr['qps'],n/rr['wall_seconds']);wall+=rr['wall_seconds'];counts['rounds']+=1
        qp=statistics.median(x['qps'] for x in p['rounds']);close(r['qps'],qp);close(r['mean_us'],1e6/qp);metrics[K,L,m]=(hits,qp);outputs[K,L,m]=(I,raw[prefix+'/raw/distances.f32'],ints(raw[prefix+'/decisions.i32']),good,raw[prefix+'/work.u64']);counts['points']+=1
        if m in ['GT10','OPT-B32','Q8-B32','REUSE-SQ'] and (K,L,m) in oldrows:
            assert all(x['packet_sha256']==hh for x in oldrows[K,L,m]['rounds']);counts['old_compatible_packets']+=1
    for (K,L,m),(hits,qps) in metrics.items():
        if m.startswith(('F-','N-')):
            a=outputs[K,L,m];on=outputs[K,L,'ALWAYS'];off=outputs[K,L,'GT10' if m.startswith('F-') else 'Q8-B32']
            for q in range(n):
                ex=on if a[2][q*7+6] else off;assert a[0][q*K:(q+1)*K]==ex[0][q*K:(q+1)*K] and a[1][q*K*4:(q+1)*K*4]==ex[1][q*K*4:(q+1)*K*4];counts['branch_queries']+=1
        if (ds,window,K,L,m) in frontier:
            r=frontier[ds,window,K,L,m];base=[v for k,v in metrics.items() if k[0]==K and k[2] in ['GT10','OPT-B32','REUSE-SQ']];covered=any(h>=hits and q>=qps and (h>hits or q>qps) for h,q in base);assert str(covered)==r['covered'];counts['frontiers']+=1
            qs=[q for h,q in base if h>=hits]
            if qs:close(r['quality_threshold_QPS_change_pct'],100*(qps/max(qs)-1))
    for K in [1,100]:
        for family in ['F','N']:
            a=outputs[K,200,f'{family}-PRE90'];b=outputs[K,200,f'{family}-PRE90-LATE'];assert a[0]==b[0] and a[1]==b[1] and a[4]==b[4]
            for q in range(n):
                for j in [0,1,2,3,4,6]:assert a[2][q*7+j]==b[2][q*7+j]
    print('STDLIB_AUDITED',ds,window,flush=True)
close(read(R/'analysis/analysis_receipt.json')['formal_complete_batch_seconds'],wall)
freeze=read(R/'formal_freeze.json')
for ref in freeze['sources']+freeze['configs']:assert sha(ref['path'])==ref['sha256'],ref['path']
identity=read(R/'inherited_identity.json')
for ref in identity['files']:assert sha(ref['path'])==ref['sha256'],ref['path']
for ref in identity['large']:
    st=Path(ref['path']).stat();assert st.st_size==ref['bytes'] and st.st_mtime_ns==ref['mtime_ns']
receipt=dict(status='PASS_STDLIB_INTEGERS_HASH_WALL_BRANCHES_AND_FRONTIER',counts=counts,formal_wall_seconds=wall,historical_frozen_files_unchanged=len(identity['files']),large_stat_checks=len(identity['large']),seconds=time.perf_counter()-started,independent_implementation_same_operator=True)
(R/'analysis/stdlib_audit.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps(receipt),flush=True)
