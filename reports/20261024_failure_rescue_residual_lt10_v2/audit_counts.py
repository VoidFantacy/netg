#!/usr/bin/env python3
"""Separate stdlib set-based GT/packet reader, validates all 147 point counts."""
from pathlib import Path
import array,ast,csv,hashlib,json,struct,sys,time,zipfile

R=Path(__file__).resolve().parent;REPO=R.parents[1]
OLD=REPO/'entry_method_exploration/20261017_gt10_residual_comprehensive_v1'
def read(p):return list(csv.DictReader(p.open()))
def ints(p,code='i'):
    a=array.array(code);assert a.itemsize in (4,8)
    with p.open('rb') as f:a.fromfile(f,p.stat().st_size//a.itemsize)
    if sys.byteorder!='little':a.byteswap()
    return a
def main():
    start=time.perf_counter();rr=read(R/'failure_by_L.csv');cc=read(R/'paired_rescue_by_L.csv')
    compressed=zipfile.ZipFile(R/'per_query_hits.npz')
    cases={};queries=0
    for ds in dict.fromkeys(x['dataset'] for x in rr):
        cfg=json.loads((OLD/f'configs/{ds}.analysis.json').read_text());d=cfg['eval_gt'];n=d['n']
        w=d.get('width',d.get('k',100));total=d.get('total_n',n);offset=d.get('row_start',0)
        raw=ints(Path(d['path']),'q' if d['format']=='raw_i64' else 'i')
        stride=w+1 if d['format']=='ivecs' else w;head=1 if d['format']=='ivecs' else 0
        assert len(raw)==total*stride
        gt=[]
        for i in range(offset,offset+n):
            if head:assert raw[i*stride]==w
            g=set(raw[i*stride+head:i*stride+head+100]);assert len(g)==100;gt.append(g)
        for L in dict.fromkeys(int(x['L']) for x in rr if x['dataset']==ds):
            hitsets={};hits={}
            for row in (x for x in rr if x['dataset']==ds and int(x['L'])==L):
                name=row['method'];p=OLD/f"results/{ds}/k100/{row['source_method']}_L{L}/raw/ids.i32"
                ids=ints(p);assert len(ids)==n*100
                ss=[gt[i].intersection(ids[i*100:(i+1)*100]) for i in range(n)]
                h=[len(v) for v in ss];hitsets[name]=ss;hits[name]=h;queries+=n
                stored=compressed.read(f'{ds}__{name}__L{L}.npy')
                assert stored[:8]==b'\x93NUMPY\x01\x00'
                header_len=struct.unpack_from('<H',stored,8)[0]
                header=ast.literal_eval(stored[10:10+header_len].decode('latin1'))
                assert header=={'descr':'|u1','fortran_order':False,'shape':(n,)}
                assert list(stored[10+header_len:])==h,'per-query NPZ misalignment'
                assert sum(x<10 for x in h)==int(row['low_count'])
                assert sum(x==10 for x in h)==int(row['exactly10_count'])
                assert sum(x==0 for x in h)==int(row['zero_count'])
                assert sum(h)/n==float(row['recall_pct'])
            for row in (x for x in cc if x['dataset']==ds and int(x['L'])==L):
                a,b=('NSG','GT10') if row['comparison']=='GT10_vs_NSG' else ('GT10','B32')
                ah,bh=hits[a],hits[b];low=[i for i in range(n) if ah[i]<10]
                verify={'reference_low_count':len(low),'result_low_count':sum(x<10 for x in bh),
                    'exit_low_count':sum(bh[i]>=10 for i in low),
                    'enter_low_count':sum(ah[i]>=10 and bh[i]<10 for i in range(n)),
                    'low_net_improved_count':sum(bh[i]>ah[i] for i in low),
                    'low_improved_still_low_count':sum(ah[i]<bh[i]<10 for i in low),
                    'low_unchanged_count':sum(ah[i]==bh[i] for i in low),
                    'low_worsened_count':sum(ah[i]>bh[i] for i in low),
                    'low_rescued_members':sum(len(hitsets[b][i]-hitsets[a][i]) for i in low),
                    'low_damaged_members':sum(len(hitsets[a][i]-hitsets[b][i]) for i in low),
                    'low_missing_members':sum(100-ah[i] for i in low),
                    'total_rescued_members':sum(len(hitsets[b][i]-hitsets[a][i]) for i in range(n))}
                for key,val in verify.items():assert val==int(row[key]),(ds,L,key,val,row[key])
                cases[ds+':'+str(L)+':'+row['comparison']]='PASS'
        print('AUDIT',ds,flush=True)
    for path,meta in json.loads((R/'inputs_manifest.json').read_text()).items():
        p=Path(path);assert p.stat().st_size==meta['bytes']
        assert hashlib.sha256(p.read_bytes()).hexdigest()==meta['sha256'],path
    receipt=dict(status='PASS_STDLIB_SET_RECOMPUTATION',points=len(rr),paired_comparisons=len(cc),
        query_point_evaluations=queries,source_SHA_unchanged=True,numpy_imported=False,
        independent_implementation_same_author=True,seconds=time.perf_counter()-start,cases=cases)
    (R/'integer_audit.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(receipt['status'],receipt['seconds'])
if __name__=='__main__':main()
