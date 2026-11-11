#!/usr/bin/env python3
"""Strict per-query Recall@100 < 10% from retained E183 packets; no ANN."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
from pathlib import Path
import csv, hashlib, json, shutil, time
import numpy as np

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
OLD=REPO/'entry_method_exploration/20261017_gt10_residual_comprehensive_v1'
GEOM=REPO/'entry_method_exploration/20261024_residual_geometry_diagnosis_v1'
DATA=[('deep10m_l2_v1','Deep10M','soft'),('sift10m_bigann_l2_v1','SIFT10M','soft'),
      ('gist1m_l2_v1','GIST1M','hard'),('webvid2_5m_light_v1','WebVid','soft'),
      ('yandex_t2i_official10M_ip_v1','Yandex','hard'),('coco','COCO','hard'),('flickr30k','Flickr30k','hard')]
LS=[100,128,200,400,800,1000,1200]
INPUTS={}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def remember(p):
    p=Path(p);r={'bytes':p.stat().st_size,'sha256':sha(p)}
    if str(p) in INPUTS: assert INPUTS[str(p)]==r
    INPUTS[str(p)]=r
    return p
def readcsv(p): return list(csv.DictReader(remember(p).open()))
def dump(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def writecsv(p,rows):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def pct(a,b):return 100*a/b if b else None

def gtload(d):
    n=d['n'];total=d.get('total_n',n);w=d.get('width',d.get('k',100));start=d.get('row_start',0)
    p=remember(d['path']);fmt=d['format'];dt='<i8' if fmt=='raw_i64' else '<i4'
    cols=w+1 if fmt=='ivecs' else w
    assert p.stat().st_size==total*cols*np.dtype(dt).itemsize
    a=np.fromfile(p,dt).reshape(total,cols)
    if fmt=='ivecs': assert np.all(a[:,0]==w);a=a[:,1:]
    else: assert fmt in ('raw_i64','raw_i32')
    g=a[start:start+n,:100]
    assert g.shape==(n,100) and np.all(np.diff(np.sort(g,axis=1),axis=1)>0)
    return g

def mask(ds,method,L,g,N):
    p=remember(OLD/f'results/{ds}/k100/{method}_L{L}/raw/ids.i32')
    r=np.fromfile(p,'<i4').reshape(len(g),100)
    assert np.all((r>=0)&(r<N)) and np.all(np.diff(np.sort(r,axis=1),axis=1)>0)
    out=np.empty(g.shape,dtype=bool)
    for lo in range(0,len(g),128):out[lo:lo+128]=(g[lo:lo+128,:,None]==r[lo:lo+128,None,:]).any(2)
    return out

def comparison(ds,label,rt,L,kind,a,b,am,bm):
    low=a<10;out=b<10;n=len(a);den=int(low.sum());delta=b.astype(int)-a.astype(int)
    rescued=~am&bm;damaged=am&~bm;exit_=low&~out;enter=~low&out
    total_gain=int(rescued.sum());tail_gain=int(rescued[low].sum())
    missing=int((~am[low]).sum())
    return dict(dataset=ds,label=label,router=rt,L=L,comparison=kind,n=n,reference_low_count=den,
        result_low_count=int(out.sum()),reference_low_pct=pct(den,n),result_low_pct=pct(out.sum(),n),
        exit_low_count=int(exit_.sum()),enter_low_count=int(enter.sum()),
        exit_rate_pct=pct(exit_.sum(),den),low_net_improved_count=int((low&(delta>0)).sum()),
        low_net_improved_pct=pct((low&(delta>0)).sum(),den),low_improved_still_low_count=int((low&out&(delta>0)).sum()),
        low_unchanged_count=int((low&(delta==0)).sum()),low_worsened_count=int((low&(delta<0)).sum()),
        low_rescued_members=tail_gain,low_damaged_members=int(damaged[low].sum()),low_missing_members=missing,
        low_member_repair_pct=pct(tail_gain,missing),total_rescued_members=total_gain,
        share_rescued_members_from_low_pct=pct(tail_gain,total_gain),
        low_average_recall_before_pct=float(a[low].mean()) if den else None,
        low_average_recall_after_pct=float(b[low].mean()) if den else None,
        low_average_recall_gain_pp=float(delta[low].mean()) if den else None)

def main():
    start=time.perf_counter()
    assert not (ROOT/'analysis_receipt.json').exists(),'sealed analysis exists'
    for name in ['summary.md','spec.md','s-target.md','s-experiment.md','readme.md','LOCAL_CODEX_START.md',
                 'experiment_history/184_residual_geometry_diagnosis_v1.md']:
        dest=ROOT/'source_before'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(REPO/name,dest)
    points=readcsv(OLD/'analysis/final_v1/points.csv')
    pointmap={(r['dataset'],r['method'],int(r['L'])):r for r in points if r['K']=='100'}
    geom=readcsv(GEOM/'analysis/query_metrics.csv')
    summaries=[];comp=[];tail=[];hists=[];cross=[];geo=[];saved={}
    for ds,label,rt in DATA:
        cfg=json.loads(remember(OLD/f'configs/{ds}.analysis.json').read_text())
        c=cfg['catalogue_entry'];g=gtload(c['test_gt']);n=len(g);N=c['base']['n']
        gm='GT10-soft-t1' if rt=='soft' else 'GT10-hard';post=rt+'-JOINT32'
        methods=[('NSG','NSG'),('GT10',gm),('B32',post)]
        hh={};mm={}
        for L in LS:
            for short,method in methods:
                m=mask(ds,method,L,g,N);h=m.sum(1).astype(np.uint8);mm[short,L]=m;hh[short,L]=h
                p=pointmap[ds,method,L];assert int(h.sum())==int(p['hits'])
                assert n==int(p['n']) and abs(float(p['recall_pct'])-float(h.mean()))<1e-9
                saved[f'{ds}__{short}__L{L}']=h
                summaries.append(dict(dataset=ds,label=label,router=rt,method=short,source_method=method,L=L,n=n,
                    low_count=int((h<10).sum()),low_pct=pct((h<10).sum(),n),zero_count=int((h==0).sum()),
                    exactly10_count=int((h==10).sum()),incomplete_count=int((h<100).sum()),
                    recall_pct=float(p['recall_pct']),qps=float(p['qps']),qps_min=float(p['qps_min']),qps_max=float(p['qps_max'])))
                for hit,count in enumerate(np.bincount(h,minlength=101)):
                    hists.append(dict(dataset=ds,method=short,L=L,hits=hit,count=int(count)))
            for kind,a,b in [('GT10_vs_NSG','NSG','GT10'),('B32_vs_GT10','GT10','B32')]:
                r=comparison(ds,label,rt,L,kind,hh[a,L],hh[b,L],mm[a,L],mm[b,L])
                assert r['reference_low_count']-r['exit_low_count']+r['enter_low_count']==r['result_low_count']
                assert r['low_net_improved_count']==r['exit_low_count']+r['low_improved_still_low_count']
                comp.append(r)
            ns,gt,ps=hh['NSG',L],hh['GT10',L],hh['B32',L]
            for qi in np.flatnonzero((ns<10)|(gt<10)|(ps<10)):
                tail.append(dict(dataset=ds,L=L,query_row=int(qi),NSG_hits=int(ns[qi]),GT10_hits=int(gt[qi]),B32_hits=int(ps[qi])))
        for method,_ in methods:
            for L0,L1 in zip(LS,LS[1:]):
                a=hh[method,L0]<10;b=hh[method,L1]<10
                cross.append(dict(dataset=ds,label=label,method=method,L_from=L0,L_to=L1,
                    low_from=int(a.sum()),low_to=int(b.sum()),exited=int((a&~b).sum()),entered=int((~a&b).sum()),
                    shared=int((a&b).sum())))
        gr=[r for r in geom if r['dataset']==ds];assert len(gr)==n
        z=np.array([float(r['background_separation_z']) for r in gr])
        for L in LS:
            h=hh['GT10',L];delta=hh['B32',L].astype(int)-h.astype(int);low=h<10
            for group,sel in [('low',low),('at_least10',~low)]:
                geo.append(dict(dataset=ds,label=label,L=L,group=group,n=int(sel.sum()),
                    background_z_median=float(np.median(z[sel])) if sel.any() else None,
                    mean_GT_hits=float(h[sel].mean()) if sel.any() else None,
                    residual_improved=int((sel&(delta>0)).sum())))
        print(label, 'GT10<10%:',[int((hh['GT10',L]<10).sum()) for L in LS],
            'B32:',[int((hh['B32',L]<10).sum()) for L in LS],flush=True)
    np.savez_compressed(ROOT/'per_query_hits.npz',**saved)
    for name,rr in [('failure_by_L',summaries),('paired_rescue_by_L',comp),('low_query_rows',tail),
                    ('hit_distributions',hists),('cross_L_query_transitions',cross),('geometry_low_cohort',geo)]:
        writecsv(ROOT/(name+'.csv'),rr)
    for p,r in INPUTS.items():assert sha(p)==r['sha256']
    dump(ROOT/'inputs_manifest.json',INPUTS)
    dump(ROOT/'analysis_receipt.json',dict(status='PASS_RAW_PACKET_RECOMPUTATION',K=100,
        definition='Recall@100 < 0.10 iff exact GT100 intersection count is 0..9; exactly10 excluded',
        datasets=7,L=LS,points=len(summaries),unique_queries=56000,query_point_evaluations=1176000,
        whole_input_sha_verified=True,input_files=len(INPUTS),new_ANN=0,new_GT=0,new_timing=0,
        seconds=time.perf_counter()-start))
    print('PASS',time.perf_counter()-start,flush=True)

if __name__=='__main__':main()
