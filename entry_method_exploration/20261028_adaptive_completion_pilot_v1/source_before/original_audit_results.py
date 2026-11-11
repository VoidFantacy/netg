#!/usr/bin/env python3
"""Second implementation: stdlib set/array counters, packet SHA, frozen inputs."""
import array,csv,hashlib,json,statistics,struct,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];A=R/'analysis';OLD=R.parent/'20261017_gt10_residual_comprehensive_v1'
def ints(path,kind='i'):
    a=array.array(kind)
    with Path(path).open('rb') as f:a.fromfile(f,Path(path).stat().st_size//a.itemsize)
    return a
def truth(d):
    a=ints(d['path'],'q' if d['format']=='raw_i64' else 'i');k=d.get('width',d.get('k',100));start=d.get('row_start',0)
    return [set(a[(start+i)*k:(start+i)*k+100]) for i in range(d['n'])]
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def main():
    start=time.perf_counter();pmap={(x['dataset'],x['method'],int(x['L'])):x for x in csv.DictReader((A/'points.csv').open())};paired={(x['dataset'],x['method'],int(x['L'])):x for x in csv.DictReader((A/'paired.csv').open())};checked=0;costs=[];historical_packets=0
    for ds in ['coco','deep10m_l2_v1']:
        cfg=json.loads((R/f'configs/{ds}.json').read_text());g=truth(cfg['test_gt']);n=len(g);complete=json.loads((R/f'results/{ds}/complete.json').read_text());masks={};packets={}
        source=set(ints(OLD/f"models/{ds}/compiled/{cfg['router']['name']}/source/global_ids.i32"))
        for r in complete['results']:
            p=Path(r['result_dir'])/'raw';ids=ints(p/'ids.i32');d=ints(p/'distances.f32','f');shape=struct.pack('<QQ',n,100);h=hashlib.sha256(shape)
            for filename in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:h.update((p/filename).read_bytes())
            h.update(bytes(n*16));assert all(x['packet_sha256']==h.hexdigest() for x in r['rounds'])
            if r['method'] in ['GT10','B32']:
                family=('GT10-hard' if cfg['router']['name']=='hard' else 'GT10-soft-t1') if r['method']=='GT10' else cfg['router']['name']+'-JOINT32'
                previous=OLD/f"results/{ds}/k100/{family}_L{r['L']}/raw"
                if previous.exists():
                    for filename in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:assert (p/filename).read_bytes()==(previous/filename).read_bytes(),(ds,r['method'],r['L'],filename)
                    historical_packets+=1
            hits=[]
            for i in range(n):
                out=ids[i*100:(i+1)*100];assert len(set(out))==100 and all(0<=x<cfg['base']['n'] for x in out)
                dd=d[i*100:(i+1)*100];assert all(x<=y for x,y in zip(dd,dd[1:]))
                hits.append(set(out)&g[i])
            masks[r['method'],r['L']]=hits;packets[r['method'],r['L']]=ids
            row=pmap[ds,r['method'],r['L']];total=sum(map(len,hits));assert total==int(row['hits']);assert sum(len(x)<10 for x in hits)==int(row['failed_lt10'])
            assert abs(100*total/(n*100)-float(row['recall_pct']))<1e-10
            assert abs(statistics.median(x['qps'] for x in r['rounds'])-float(row['qps']))<1e-9;checked+=1
        # Exact number of B32 scored candidates, from table and actual main packets.
        raw=Path(cfg['table']).read_bytes();header=struct.unpack_from('<8I',raw,8);H,b=header[1:3];labels=struct.unpack_from('<'+str(H)+'i',raw,40);off=40+4*H
        counts=raw[off:off+H];off+=H;targets=struct.unpack_from('<'+str(H*b)+'i',raw,off)
        rows={label:set(targets[i*b:i*b+counts[i]]) for i,label in enumerate(labels)}
        for L in [100,200,400]:
            ids=packets['GT10',L];routes=ints(R/f'results/{ds}/GT10_L{L}/raw/entry_ids.i32');nc=0
            for i in range(n):
                route=routes[i*3:(i+1)*3];assert all(x in rows for x in route)
                nc+=len(set.union(*(rows[x] for x in route))-set(ids[i*100:(i+1)*100]))
            costs.append(dict(dataset=ds,method='B32',L=L,extra_exact_scores_per_query=nc/n,source='independent reconstruction from actual main packets and frozen table'))
        for (method,L),hh in masks.items():
            if method=='GT10':continue
            base=masks['GT10',L];row=paired[ds,method,L];counts=dict(members_rescued=0,members_damaged=0,rescued_source_out=0,rescued_source_in=0,improved_queries=0,worsened_queries=0,full_recovered_queries=0,original_lt10=0,final_lt10=0,lt10_improved=0,lt10_escaped=0,new_lt10=0,rescued_from_original_lt10=0,rescued_from_original_ge10=0,members_missing=0)
            for a,z in zip(base,hh):
                new=z-a;lost=a-z;counts['members_rescued']+=len(new);counts['members_damaged']+=len(lost)
                counts['rescued_source_out']+=len(new-source);counts['rescued_source_in']+=len(new&source)
                counts['improved_queries']+=len(z)>len(a);counts['worsened_queries']+=len(z)<len(a);counts['full_recovered_queries']+=len(z)==100 and len(a)<100
                counts['original_lt10']+=len(a)<10;counts['final_lt10']+=len(z)<10;counts['lt10_improved']+=len(a)<10 and len(z)>len(a);counts['lt10_escaped']+=len(a)<10 and len(z)>=10;counts['new_lt10']+=len(a)>=10 and len(z)<10
                counts['rescued_from_original_lt10' if len(a)<10 else 'rescued_from_original_ge10']+=len(new);counts['members_missing']+=100-len(a)
            for k,v in counts.items():assert v==int(row[k]),(ds,method,L,k,v,row[k])
    frozen=json.loads((R/'freeze.json').read_text());assert all(sha(x['path'])==x['sha256'] for x in frozen['files'])
    for x in frozen['large_assets']:
        s=Path(x['path']).stat();assert (s.st_size,s.st_mtime_ns,s.st_ino)==(x['bytes'],x['mtime_ns'],x['inode'])
    receipt=dict(status='PASS_E187_STDLIB_SECOND_IMPLEMENTATION',points=checked,paired_points=len(paired),historical_full_10K_packets_bit_equal=historical_packets,packet_SHA_and_three_round_receipts_checked=True,all_frozen_inputs_unchanged=True,large_asset_stat_unchanged=True,seconds=time.perf_counter()-start,
        B32_exact_score_counts=costs,review_scope='second implementation by same operator; not independent personnel or blind replication')
    (R/'reviews/results_audit.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
