"""Independent set/array/statistics implementation. Does not import primary analysis."""
import array,csv,hashlib,json,math,statistics,struct,subprocess,sys,tarfile,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
OLD=R.parent/'20261101_residual_bottleneck_separation_v1'
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
began=time.perf_counter();counts=dict(points=0,rounds=0,old_packet_parity=0,paired_rescue_loss=0,frontier_checks=0)
with open(R/'analysis/points.csv') as f:reported={(r['dataset'],r['window'],int(r['K']),int(r['L']),r['method']):r for r in csv.DictReader(f)}
with open(R/'analysis/comparisons.csv') as f:comparisons={(r['dataset'],r['window'],int(r['K']),int(r['L']),r['method']):r for r in csv.DictReader(f)}
walls=0.
for ds in ['coco','webvid2_5m_light_v1']:
  for window in ['A','B']:
    cfg=read(R/'configs'/f'{ds}.{window}.formal.json');n=cfg['queries']['n'];root=Path(cfg['output_dir']);info=read(root/'complete.json')
    archive=read(root/'packet_archive.json');assert sha(archive['archive'])==archive['archive_sha256']
    refs={x['member']:x for x in archive['files']};raw={};seen=set()
    proc=subprocess.Popen(['zstd','-q','-d','-c',archive['archive']],stdout=subprocess.PIPE)
    with tarfile.open(fileobj=proc.stdout,mode='r|') as tf:
        for item in tf:
            b=tf.extractfile(item).read();ref=refs[item.name];assert len(b)==ref['payload_bytes'] and hashlib.sha256(b).hexdigest()==ref['payload_sha256'];seen.add(item.name)
            if '/raw/' in item.name:raw[item.name]=b
    assert proc.wait()==0 and seen==set(refs)
    old=read(OLD/'storage/results'/ds/window/'complete.json')
    oldrows={(r['K'],r['L'],r['method']):r for r in old['results']}
    gt=ints(Path(cfg['test_gt']['path']).read_bytes());first=cfg['test_gt'].get('row_start',0);gt=gt[first*100:(first+n)*100]
    metrics={};correct={}
    for p in info['results']:
        K,L,m=p['K'],p['L'],p['method'];key=(K,L,m);r=reported[ds,window,K,L,m];prefix=f'k{K}/{m}_L{L}/raw/'
        ids=ints(raw[prefix+'ids.i32']);assert len(ids)==n*K
        good=[set(ids[q*K:(q+1)*K])&set(gt[q*100:q*100+K]) for q in range(n)]
        total=sum(map(len,good));close(r['hits'],total);close(r['recall_pct'],100*total/(n*K))
        if K==100:close(r['failed_lt10'],sum(len(g)<10 for g in good))
        h=hashlib.sha256(struct.pack('<QQ',n,K))
        for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:h.update(raw[prefix+name])
        h.update(bytes(16*n));packet=h.hexdigest()
        for rr in p['rounds']:
            assert rr['threads']==1 and rr['packet_sha256']==packet;close(rr['qps'],n/rr['wall_seconds']);walls+=rr['wall_seconds'];counts['rounds']+=1
        qps=statistics.median(x['qps'] for x in p['rounds']);close(r['qps'],qps);close(r['mean_us'],1e6/qps)
        metrics[key]=(total,qps);correct[key]=good
        if key in oldrows and m in ['GT10','OPT-B32','Q8-B32','REUSE-SQ','MODEL1','DIST1-FULL']:
            assert all(x['packet_sha256']==packet for x in oldrows[key]['rounds']),(ds,window,key)
            counts['old_packet_parity']+=1
        counts['points']+=1
    for (K,L,m),(hits,qps) in metrics.items():
        r=reported[ds,window,K,L,m]
        for bm,label in [('GT10','GT10'),('OPT-B32','fullB32'),('Q8-B32','Q8')]:
            if (K,L,bm) not in correct:continue
            g=sum(len(a-b) for a,b in zip(correct[K,L,m],correct[K,L,bm]));l=sum(len(b-a) for a,b in zip(correct[K,L,m],correct[K,L,bm]))
            close(r[f'rescued_vs_{label}'],g);close(r[f'lost_vs_{label}'],l);close(r[f'gain_vs_{label}_pp'],100*(g-l)/(n*K));counts['paired_rescue_loss']+=1
        if (ds,window,K,L,m) in comparisons:
            c=comparisons[ds,window,K,L,m];base=[v for k,v in metrics.items() if k[0]==K and k[2] in ['GT10','OPT-B32','REUSE-SQ']]
            dominated=any(h>=hits and q>=qps and (h>hits or q>qps) for h,q in base)
            assert str(dominated)==c['covered'];qualified=[q for h,q in base if h>=hits]
            if qualified:close(c['quality_threshold_QPS_gain_pct'],100*(qps/max(qualified)-1))
            counts['frontier_checks']+=1
    print('STDLIB_AUDITED',ds,window,len(metrics),flush=True)
close(read(R/'analysis/analysis_receipt.json')['formal_batch_wall_seconds'],walls)
freeze=read(R/'formal_freeze.json')
for ref in freeze['sources']+freeze['configs']:assert sha(ref['path'])==ref['sha256'],ref['path']
identity=read(R/'inherited_identity.json');assert sha(R/'inherited_identity.json')==freeze['inherited_identity_sha256']
for ref in identity['files']:assert sha(ref['path'])==ref['sha256'],ref['path']
for ref in identity['large']:
    st=Path(ref['path']).stat();assert st.st_size==ref['bytes'] and st.st_mtime_ns==ref['mtime_ns'],ref['path']
for ref in freeze['inherited_inputs']['inputs']:assert sha(ref['path'])==ref['sha256'],ref['path']
receipt=dict(status='PASS_INDEPENDENT_STDLIB_RECALL_HASH_WALL_FRONTIER_AND_PRIOR_PARITY',counts=counts,formal_wall_seconds=walls,seconds=time.perf_counter()-began,
    historical_frozen_files_unchanged=len(identity['files']),large_stat_checks=len(identity['large']),independent_implementation_same_operator=True,
    scope_exclusions=['not independent-person replication','does not retrain models or regenerate all graph labels','bootstrap descriptive intervals not independently repeated'])
(R/'analysis/stdlib_audit.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps(receipt),flush=True)
