"""Second, stdlib-only check of integer quality, actual packets and complete wall."""
import array,csv,hashlib,json,math,statistics,struct,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
start=time.perf_counter();rows=list(csv.DictReader((R/'analysis/points.csv').open()));groups={};checked=0;queries=0;wall=0
def load(p):return json.loads(Path(p).read_text())
def ints(p):
    a=array.array('i');a.frombytes(Path(p).read_bytes());assert a.itemsize==4;return a
for row in rows:groups.setdefault((row['dataset'],row['window']),[]).append(row)
for (ds,w),pp in groups.items():
    c=load(R/'configs'/f'{ds}.{w}.json');root=Path(c['output_dir']);n=c['queries']['n'];gt=ints(c['test_gt']['path']);packets={}
    for row in pp:
        K,L=int(row['K']),int(row['L']);m=row['method'];d=root/f'k{K}/{m}_L{L}';packets[K,L,m]=ints(d/'raw/ids.i32')
    for row in pp:
        K,L=int(row['K']),int(row['L']);m=row['method'];d=root/f'k{K}/{m}_L{L}';ids=packets[K,L,m];main=packets[K,L,'GT10'];base=packets[K,L,'B32'];hits=rescue=lost=brescue=blost=improved=harmed=failed=0
        for i in range(n):
            G=set(gt[i*100:i*100+K]);F=set(ids[i*K:(i+1)*K]);M=set(main[i*K:(i+1)*K]);B=set(base[i*K:(i+1)*K]);assert len(F)==K and all(0<=x<c['base']['n'] for x in F)
            f=F&G;a=M&G;b=B&G;hits+=len(f);rescue+=len(f-a);lost+=len(a-f);brescue+=len(f-b);blost+=len(b-f);improved+=len(f)>len(b);harmed+=len(f)<len(b);failed+=len(f)<10
        for key,value in [('hits',hits),('rescued_vs_GT',rescue),('lost_vs_GT',lost),('rescued_vs_B32',brescue),('lost_vs_B32',blost),('improved_queries_vs_B32',improved),('harmed_queries_vs_B32',harmed)]:assert int(row[key])==value,(ds,w,K,L,m,key)
        assert math.isclose(float(row['recall_pct']),100*hits/(n*K),abs_tol=1e-12)
        if K==100:assert int(row['failed_lt10'])==failed
        h=hashlib.sha256();h.update(struct.pack('<QQ',n,K))
        for filename in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:h.update((d/'raw'/filename).read_bytes())
        h.update(bytes(n*8));h.update(bytes(n*8));rounds=[load(d/f'round{i}.json') for i in range(3)]
        assert all(x['packet_sha256']==h.hexdigest() and x['threads']==1 for x in rounds)
        assert all(math.isclose(x['qps'],n/x['wall_seconds'],rel_tol=1e-13) for x in rounds)
        expected=n/statistics.median(x['wall_seconds'] for x in rounds);assert math.isclose(float(row['qps']),expected,rel_tol=1e-13)
        wall+=sum(x['wall_seconds'] for x in rounds);queries+=n;checked+=1
    print('STDLIB_AUDITED',ds,w,len(pp),flush=True)
assert checked==1260 and queries==642960
out=dict(status='PASS_STDLIB_1260_POINTS_3780_HASH_WALL_INTEGER_AUDIT',points=checked,formal_rounds=checked*3,query_point_instances=queries,formal_batch_wall_seconds=wall,seconds=time.perf_counter()-start,imports='stdlib only; no analyzer or numpy',same_executor_different_implementation=True)
(R/'analysis/stdlib_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(out['status'],flush=True)
