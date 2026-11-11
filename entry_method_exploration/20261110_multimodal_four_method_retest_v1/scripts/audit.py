"""Independent stdlib-only audit of every measurement and GT intersection."""
from pathlib import Path
from array import array
import json,csv,gzip,hashlib,struct,sys,math,time,argparse
RUN=Path(__file__).resolve().parents[1];ROOT=RUN.parents[1]
def read(p):return json.loads(Path(p).read_text())
def words(data,code):
    a=array(code);a.frombytes(data)
    if sys.byteorder!='little':a.byteswap()
    return a
def payload(p):
    p=Path(p)
    if p.exists():return p.read_bytes()
    with gzip.open(str(p)+'.gz','rb') as f:return f.read()
def main(out):
    started=time.time();lock=read(RUN/'config.locked.json')
    with (out/'points.csv').open() as f:points=list(csv.DictReader(f))
    with (out/'rounds.csv').open() as f:rounds=list(csv.DictReader(f))
    expected={(ds,K,L,m) for ds in lock['datasets'] for K in [1,100] for L in lock['K_L'][str(K)] for m in lock['methods']}
    actual={(p['dataset'],int(p['K']),int(p['L']),p['method']) for p in points}
    assert len(points)==640 and actual==expected and len(rounds)==1280
    checked=0;queries=0;payloads=0;by_key={};paired_expected={}
    for ds in lock['datasets']:
        c=read(ROOT/'entry_method_exploration/20261017_gt10_residual_comprehensive_v1/configs'/f'{ds}.analysis.json')['eval_gt']
        n=c['n'];gt_data=words(Path(c['path']).read_bytes(),'q' if c['format']=='raw_i64' else 'i');stride=101 if c['format']=='ivecs' else 100
        skip=1 if stride==101 else 0;start=c.get('row_start',0)
        gt=[set(gt_data[(start+i)*stride+skip:(start+i)*stride+skip+100]) for i in range(n)]
        gt1=[gt_data[(start+i)*stride+skip] for i in range(n)]
        for K in [1,100]:
            for L in lock['K_L'][str(K)]:
                actual_sets={};counts={}
                for m in lock['methods']:
                    row=next(p for p in points if p['dataset']==ds and int(p['K'])==K and int(p['L'])==L and p['method']==m)
                    point=Path(row['point_dir']);meta=read(point/'result.json')
                    b=[payload(point/'raw'/name) for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']]
                    h=hashlib.sha256(struct.pack('<QQ',n,K))
                    for x in b:h.update(x)
                    h.update(bytes(16*n));digest=h.hexdigest();assert digest==row['packet_sha256']
                    ids=words(b[0],'i');assert len(ids)==n*K
                    target_sets=[{gt1[i]} if K==1 else gt[i] for i in range(n)]
                    correct=[set(ids[i*K:(i+1)*K])&target_sets[i] for i in range(n)]
                    hits=[len(x) for x in correct];total=sum(hits);assert total==int(row['hits'])
                    assert math.isclose(total/(n*K),float(row['recall']),rel_tol=1e-13)
                    if K==100:assert sum(x<10 for x in hits)==int(row['severe_queries'])
                    assert sum(x==0 for x in hits)==int(row['zero_hit_queries'])
                    assert len(meta['rounds'])==2 and all(x['threads']==1 and x['cpu']==15 and x['packet_sha256']==digest for x in meta['rounds'])
                    wall=[x['wall_seconds'] for x in meta['rounds']];qps=[n/x for x in wall]
                    assert math.isclose(sum(qps)/2,float(row['qps_mean']),rel_tol=1e-13)
                    assert math.isclose(sum(wall)/2,float(row['wall_mean_seconds']),rel_tol=1e-13)
                    assert math.isclose(2*n/sum(wall),float(row['qps_pooled']),rel_tol=1e-13)
                    key=(ds,K,L,m);by_key[key]=(wall,qps,digest,n);actual_sets[m]=correct;counts[m]=hits
                    checked+=1;queries+=2*n;payloads+=4
                for m,ref in [('GT10','NSG'),('GT10+Residual','GT10'),('GATE','NSG')]:
                    a,b=actual_sets[m],actual_sets[ref];ah,bh=counts[m],counts[ref]
                    value={'rescued_members':sum(len(x-y) for x,y in zip(a,b)),'lost_members':sum(len(y-x) for x,y in zip(a,b)),
                      'improved_queries':sum(x>y for x,y in zip(ah,bh)),'degraded_queries':sum(x<y for x,y in zip(ah,bh))}
                    if K==100:value.update(severe_rescued=sum(y<10<=x for x,y in zip(ah,bh)),new_severe=sum(x<10<=y for x,y in zip(ah,bh)))
                    paired_expected[(ds,K,L,m,ref)]=value
        print('AUDITED',ds,checked,flush=True)
    for r in rounds:
        key=(r['dataset'],int(r['K']),int(r['L']),r['method']);wall,qps,digest,n=by_key[key];i=int(r['round'])
        assert i in [0,1] and r['packet_sha256']==digest and int(r['n'])==n
        assert math.isclose(float(r['wall_seconds']),wall[i],rel_tol=1e-13) and math.isclose(float(r['qps']),qps[i],rel_tol=1e-13)
    assert len({(r['dataset'],r['K'],r['L'],r['method'],r['round']) for r in rounds})==1280
    with (out/'paired.csv').open() as f:pairs=list(csv.DictReader(f))
    assert len(pairs)==480
    for p in pairs:
        key=(p['dataset'],int(p['K']),int(p['L']),p['method'],p['reference'])
        for name,v in paired_expected[key].items():assert int(p[name])==v,(key,name)
    with (out/'targets.csv').open() as f:targets=list(csv.DictReader(f))
    assert len(targets)==96
    for t in targets:
        pool=[p for p in points if p['dataset']==t['dataset'] and p['K']==t['K'] and p['method']==t['method'] and float(p['recall'])>=float(t['target_recall'])]
        assert (t['reached']=='True')==bool(pool)
        if pool:
            best=max(pool,key=lambda p:float(p['qps_mean']))
            assert best['L']==t['L'] and float(best['recall'])==float(t['actual_recall']) and float(best['qps_mean'])==float(t['qps_mean'])
    with (out/'frontier.csv').open() as f:frontier=list(csv.DictReader(f))
    assert len(frontier)==640
    for p in frontier:
        group=[q for q in points if q['dataset']==p['dataset'] and q['K']==p['K']]
        a=next(q for q in group if q['method']==p['method'] and q['L']==p['L'])
        dom=[q for q in group if q['method']!=a['method'] and int(q['hits'])>=int(a['hits']) and float(q['qps_mean'])>=float(a['qps_mean']) and (int(q['hits'])>int(a['hits']) or float(q['qps_mean'])>float(a['qps_mean']))]
        assert (p['covered_by_other_method']=='True')==bool(dom)
        assert set(p['covering_points'].split(';'))- {''}=={q['method']+':L'+q['L'] for q in dom}
    archive_files=0
    for ds in lock['datasets']:
        for K in [1,100]:
            job=RUN/'results'/ds/f'k{K}_run';manifest=read(job/'archive_manifest.json');assert len(manifest['files'])==320
            for rec in manifest['files']:
                path=job/rec['file'];body=payload(path)
                assert len(body)==rec['bytes'] and hashlib.sha256(body).hexdigest()==rec['payload_sha256']
                assert hashlib.sha256(Path(str(path)+'.gz').read_bytes()).hexdigest()==rec['gzip_sha256'];archive_files+=1
    assert checked==640 and queries==11200000 and archive_files==payloads==2560
    result={'status':'PASS_INDEPENDENT_STDLIB_ALL_POINTS','points':checked,'rounds':1280,'formal_queries':queries,'paired_comparisons':480,'threshold_rows':96,'frontier_rows':640,'actual_packet_payload_files':payloads,'archive_files_roundtrip_verified':archive_files,'seconds':time.time()-started,'scope':'All GT intersections, packet SHA, both timing rounds, arithmetic/pooled QPS, severe counts, paired members, thresholds, frontier coverage, matrix and archives; same operator, different implementation.','visual_review_pending':True}
    with (out/'independent_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=RUN/'analysis/final_v1');a=p.parse_args();main(a.out)
