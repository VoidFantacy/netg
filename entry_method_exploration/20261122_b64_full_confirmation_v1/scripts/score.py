"""Verify complete-wall receipts and score exact query-aligned top-100 outputs."""
import csv
import hashlib
from pathlib import Path
import struct

import numpy as np

from drive import DATASETS,E183,K,LGRID,N,RAW,ROOT,START,TARGETS,TOTAL,config,read,sealed,truth,vectors,verify,write

A=ROOT/'analysis'
METHODS=('B32','B64')


def output(name, rows):
    assert rows
    with (A/f'{name}.csv').open('x') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def score(ids, truth):
    hits=(ids[:,:,None]==truth[:,None,:]).any(axis=2)
    check=[set(map(int,row)).intersection(target) for row,target in zip(ids,truth)]
    assert all(set(map(int,row[m]))==s for row,m,s in zip(ids,hits,check))
    assert int(hits.sum())==sum(map(len,check))
    return int(hits.sum()),check


def packet(path,n):
    dig=hashlib.sha256(struct.pack('<QQ',n,K))
    for f in RAW:
        dig.update((path/'raw'/f).read_bytes())
    dig.update(bytes(n*16))
    return dig.hexdigest()


def verify_full_webvid_fit():
    ds=DATASETS[1]
    c=read(config(ds))
    source=read(E183/'configs'/f'{ds}.teacher.json')['queries']
    fit=vectors(dict(source,n=source['total_n'],row_start=0))
    official={hashlib.sha256(row.tobytes()).digest() for row in fit}
    rows=np.fromfile(c['rows'],'<i4')
    queries=vectors(c['queries'])[rows]
    test={hashlib.sha256(row.tobytes()).digest() for row in queries}
    assert len(test)==N and not test.intersection(official)
    write(A/'webvid_full_fit_overlap.json',{'fit_queries':len(fit),'holdout_queries':len(test),
        'shared_exact_vectors':0,'byte_comparison':'SHA-256','fit_path':source['path']})


def measure():
    e227=ROOT.parent/'20261122_b32_cutoff_two_tower_v1'
    prior=read(e227/'seal.json')['files']
    receipts=[read(ROOT/'data'/ds/'complete.json') for ds in DATASETS]
    assert all(r['status']=='PASS_E228_FORMAL' and r['points']==40 and r['batches']==80
               and r['E226_prefix_parity_points']==6 and not r['public_GT_read'] for r in receipts)
    verify_full_webvid_fit()
    points,rounds,pairs,historic=[],[],[],[]
    for ds in DATASETS:
        c=read(config(ds)); croot=Path(c['output_dir'])
        rows=np.fromfile(c['rows'],'<i4'); assert len(rows)==N
        gt=truth(ds,START,TOTAL-START,formal=True)[rows-START]
        gt_unique=[len(set(x)) for x in gt]; assert all(x==K for x in gt_unique)
        shared=rows<START+N
        for j,l in enumerate(LGRID):
            key=croot/f'K100_L{l}'
            per_arm=[]
            for arm,m in enumerate(METHODS):
                p=key/m
                h=packet(p,N)
                reps=[read(p/f'round{i}.json') for i in range(2)]
                for i,r in enumerate(reps):
                    order=1+i*2+((arm-i-j)%2)
                    observed=(r['K'],r['L'],r['n'],r['cpu'],r['threads'],r['rep'],r['order'],r['sha256'],r['method'])
                    assert observed==(K,l,N,15,1,i,order,h,m)
                    assert r['seconds']>0 and abs(N/r['seconds']-r['qps'])<1e-8
                    rounds.append(dict(dataset=ds,**r))
                ids=np.fromfile(p/'raw/ids.i32','<i4').reshape(N,K)
                num,hitsets=score(ids,gt)
                counts=np.array([len(s) for s in hitsets])
                work=np.fromfile(p/'work.i8','u1')
                assert work.size==256 and (work<=int(m[1:])*3).all()
                qos=[r['qps'] for r in reps]
                qps=float(np.mean(qos))
                row=dict(dataset=ds,L=l,method=m,queries=N,hits=num,recall=num/(N*K),
                    qps=qps,qps0=qos[0],qps1=qos[1],wall_us=float(np.mean([r['seconds'] for r in reps]))*1e6/N,
                    failures_under_10=int((counts<10).sum()),mean_exact_256=float(work.mean()))
                points.append(row)
                per_arm.append((row,hitsets,work))
                if arm==0:
                    old=e227/'data'/ds/'formal'/key.name/m/'raw'
                    if old.exists():
                        vals={}
                        for f in RAW:
                            u=K if f in RAW[:2] else 3
                            former=np.frombuffer(sealed(old/f,e227,prior).read_bytes(),'<u4').reshape(N,u)
                            current=np.fromfile(p/'raw'/f,'<u4').reshape(N,u)
                            vals[f]=int(np.all(former[rows[shared]-START]==current[shared],axis=1).sum())
                        historic.append(dict(dataset=ds,L=l,shared_queries=int(shared.sum()),**vals))
            for name in RAW[-2:]:
                assert (key/'B32'/'raw'/name).read_bytes()==(key/'B64'/'raw'/name).read_bytes()
            (b,bh,bw),(t,th,tw)=per_arm
            assert (bw<=tw).all()
            rescued=sum(len(y-x) for x,y in zip(bh,th)); lost=sum(len(x-y) for x,y in zip(bh,th))
            assert rescued-lost==t['hits']-b['hits']
            pairs.append(dict(dataset=ds,L=l,rescued=rescued,lost=lost,net=rescued-lost,
                recall_delta_pp=100*(t['recall']-b['recall']),qps_delta_pct=100*(t['qps']/b['qps']-1),
                wall_delta_us=t['wall_us']-b['wall_us'],mean_added_exact_256=t['mean_exact_256']-b['mean_exact_256'],
                improved_failures=sum(len(x)<10 and len(y)>len(x) for x,y in zip(bh,th)),
                recovered_failures=sum(len(x)<10<=len(y) for x,y in zip(bh,th))))
    output('points',points); output('rounds',rounds); output('same_L',pairs); output('E227_baseline_parity',historic)
    return points,pairs


def pct(x,y):
    return 100*(x/y-1)


def fastest(points,goal):
    return max((x for x in points if x['hits']>=goal),key=lambda x:x['qps'],default=None)


def evaluate(points,pairs):
    goals,matches,result=[],[],{}
    for ds in DATASETS:
        base=[p for p in points if p['dataset']==ds and p['method']=='B32']
        wide=[p for p in points if p['dataset']==ds and p['method']=='B64']
        baseline={hit:max(q['qps'] for q in base if q['hits']==hit) for hit in sorted({q['hits'] for q in base})}
        levels=list(baseline)
        rows=[]
        for target in TARGETS[ds]:
            goal=int(np.ceil(target*N*K/100-1e-10))
            b=fastest(base,goal); t=fastest(wide,goal)
            x=dict(dataset=ds,target_pct=target,target_hits=goal)
            for key,p in [('B32',b),('B64',t)]:
                x.update({f'{key}_{name}':p[name] if p else None for name in ('L','recall','qps','qps0','qps1')})
            x['QPS_delta_pct']=pct(t['qps'],b['qps']) if t and b else None
            x['slow_vs_fast_pct']=pct(min(t['qps0'],t['qps1']),max(b['qps0'],b['qps1'])) if t and b else None
            rows.append(x)
        local=[]
        for t in wide:
            b=fastest(base,t['hits'])
            lq=float(np.interp(t['hits'],levels,list(baseline.values()))) if levels[0]<=t['hits']<=levels[-1] else None
            local.append(dict(dataset=ds,B64_L=t['L'],B64_recall=t['recall'],B64_qps=t['qps'],
                B32_L=b['L'] if b else None,B32_recall=b['recall'] if b else None,B32_qps=b['qps'] if b else None,
                QPS_delta_pct=pct(t['qps'],b['qps']) if b else None,
                slow_vs_fast_pct=pct(min(t['qps0'],t['qps1']),max(b['qps0'],b['qps1'])) if b else None,
                QPS_delta_vs_B32_line_pct=pct(t['qps'],lq) if lq else None))
        both=[v for v in rows if v['QPS_delta_pct'] is not None]
        eligible=[v for v in local if v['QPS_delta_pct'] is not None]
        interp=[v['QPS_delta_vs_B32_line_pct'] for v in local if v['QPS_delta_vs_B32_line_pct'] is not None]
        effects=[p for p in pairs if p['dataset']==ds]
        result[ds]=dict(targets_both=len(both),targets_faster=sum(v['QPS_delta_pct']>0 for v in both),
            targets_slow_faster=sum(v['slow_vs_fast_pct']>0 for v in both),
            targets_smaller_L=sum(v['B64_L']<v['B32_L'] for v in both),
            discrete_both=len(eligible),discrete_faster=sum(v['QPS_delta_pct']>0 for v in eligible),
            line_both=len(interp),line_faster=sum(v>0 for v in interp),
            line_delta_median=float(np.median(interp)) if interp else None,
            same_L_recall_delta_pp=[min(p['recall_delta_pp'] for p in effects),max(p['recall_delta_pp'] for p in effects)],
            same_L_lost=[min(p['lost'] for p in effects),max(p['lost'] for p in effects)],
            same_L_qps_delta_median=float(np.median([p['qps_delta_pct'] for p in effects])),
            same_L_wall_delta_us_median=float(np.median([p['wall_delta_us'] for p in effects])),
            same_L_added_exact_mean=float(np.mean([p['mean_added_exact_256'] for p in effects])))
        goals.extend(rows); matches.extend(local)
    output('targets',goals); output('matched',matches); write(A/'outcome.json',result)


if __name__=='__main__':
    verify(ROOT/'inputs.json')
    evaluate(*measure())
