#!/usr/bin/env python3
"""Separate stdlib/set/Counter verification, without importing analyzer or NumPy."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import struct
import time

R=Path(__file__).resolve().parent
E=R.parent/'20261017_gt10_residual_comprehensive_v1'

def readcsv(p):return list(csv.DictReader(p.open()))
def truth(desc):
    raw=Path(desc['path']).read_bytes();width=desc.get('width',desc.get('k',100));start=desc.get('row_start',0)
    fmt=desc['format'];code='q' if fmt=='raw_i64' else 'i';extra=int(fmt=='ivecs')
    row=struct.Struct('<'+str(width+extra)+code)
    values=[]
    for i in range(start,start+desc['n']):
        v=row.unpack_from(raw,i*row.size)
        if extra:assert v[0]==width
        values.append(v[extra:extra+100])
    return values

def response(ds,m,k,n):
    p=E/f'results/{ds}/k{k}/{m}_L200/raw/ids.i32'
    rr=list(struct.iter_unpack('<'+str(k)+'i',p.read_bytes()));assert len(rr)==n
    return rr

def main():
    t=time.time();ss=readcsv(R/'analysis/dataset_summary.csv');qq=readcsv(R/'analysis/query_metrics.csv')
    checks=[]
    for s in ss:
        ds=s['dataset'];cfg=json.loads((E/f'configs/{ds}.analysis.json').read_text());c=cfg['catalogue_entry']
        gt=truth(c['test_gt']);tg=truth(c['train_gt']);n=len(gt);rt=s['router'];gm='GT10-soft-t1' if rt=='soft' else 'GT10-hard';post=rt+'-JOINT32'
        br=response(ds,gm,100,n);pr=response(ds,post,100,n);b1=response(ds,gm,1,n);p1=response(ds,post,1,n)
        metrics=[r for r in qq if r['dataset']==ds];assert len(metrics)==n
        missing=rescued=damaged=improved=full=below90=cross90=0
        failed1=saved1=0
        for i,(g,b,p,qr) in enumerate(zip(gt,br,pr,metrics)):
            gs=set(g);bs=set(b)&gs;ps=set(p)&gs
            assert int(qr['query_row'])==i
            assert int(qr['GT_K100_hits'])==len(bs) and int(qr['B32_K100_hits'])==len(ps)
            assert int(qr['K100_rescued'])==len(ps-bs) and int(qr['K100_damaged'])==len(bs-ps)
            assert int(qr['K100_net_delta'])==len(ps)-len(bs)
            f1=b1[i][0]!=g[0];r1=f1 and p1[i][0]==g[0]
            assert int(qr['K1_failed'])==f1 and int(qr['K1_rescued'])==r1
            missing+=100-len(bs);rescued+=len(ps-bs);damaged+=len(bs-ps);improved+=len(ps)>len(bs)
            full+=len(bs)<100 and len(ps)==100;below90+=len(bs)<90;cross90+=len(bs)<90 and len(ps)>=90
            failed1+=f1;saved1+=r1
        expected={'K100_missing_members':missing,'K100_rescued_members':rescued,'K100_improved_queries':improved,
            'K100_full_repairs':full,'GT_K100_below90':below90,'K100_cross90':cross90,'GT_K1_failed':failed1,'B32_K1_rescued':saved1}
        for k,v in expected.items():assert int(s[k])==v,(ds,k,s[k],v)
        source=Path(cfg['models'][rt]['source_dir'])
        ts=[v[0] for v in struct.iter_unpack('<i',(source/'token_targets.i32').read_bytes())];fc=Counter(ts)
        gtcounts=Counter(v for row in tg for v in row)
        assert len(ts)==int(s['train_missing_tokens']) and len(fc)==int(s['train_missing_unique_targets'])
        assert abs(float(s['train_residual_singleton_token_pct'])-100*sum(v==1 for v in fc.values())/len(ts))<1e-10
        global_seen=training_seen=0
        for g,b in zip(gt,br):
            miss=set(g)-set(b)
            global_seen+=sum(v in fc for v in miss);training_seen+=sum(v in gtcounts for v in miss)
        chain=next(v for v in readcsv(R/'analysis/coverage_chain.csv') if v['dataset']==ds)
        assert global_seen==int(chain['in_global_source']) and training_seen==int(chain['in_train_GT'])
        assert int(chain['unseen_source'])+int(chain['route_lost'])+int(chain['capacity_lost'])+rescued==missing
        checks.append({'dataset':ds,'query_rows':n,'all_query_integer_fields':'PASS','source_recomputed_Counter':'PASS',
            'coverage_partition':'PASS','damaged_members_L200':damaged})
    out={'status':'PASS_SEPARATE_STDLIB_INTEGER_IMPLEMENTATION','executor':'same agent; separate implementation, not separate reviewer',
        'numpy_used':False,'analyzer_imported':False,'datasets':checks,'elapsed_seconds':time.time()-t,
        'scope':'all selected L200 query integers, K1 transitions, training/source frequencies and coverage partition; not geometry or inferential statistics',
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (R/'analysis/integer_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(out,ensure_ascii=False))

if __name__=='__main__':main()
