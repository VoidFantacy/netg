"""Audit complete-wall receipts, align physical GT, and compare depth policies."""
import csv
from decimal import Decimal, ROUND_CEILING
import hashlib
from pathlib import Path
import struct

import numpy as np
from drive import ARMS,BATCHES,DATASET,E213,E231,GRIDS,N,POINTS,RAW,ROOT,TARGETS,WINDOWS,config,digest,read,sealed,verify,write

A=ROOT/'analysis'
K=100


def emit(name,rows):
    if not rows:
        return
    with (A/f'{name}.csv').open('x') as f:
        out=csv.DictWriter(f,fieldnames=rows[0].keys()); out.writeheader(); out.writerows(rows)


def truth(rows):
    t=read(E213/'gt_eval.json')[DATASET]; p=Path(t['path'])
    assert digest(p)==t['expected_sha256'] and t['format']=='ivecs'
    vals=np.memmap(p,'<i4','r').reshape(-1,K+1)[rows]
    assert vals.shape==(N,K+1) and (vals[:,0]==K).all() and (np.diff(np.sort(vals[:,1:],axis=1),axis=1)>0).all()
    return vals[:,1:]


def packet(p):
    parts=[(p/'raw'/f).read_bytes() for f in RAW]
    assert list(map(len,parts))==[N*K*4,N*K*4,N*3*4,N*3*4]
    return hashlib.sha256(struct.pack('<QQ',N,K)+b''.join(parts)+bytes(N*16)).hexdigest(),parts


def actual(ids,gt):
    offset=np.arange(len(ids),dtype=np.int64)[:,None]*(1<<32)
    keys=(np.sort(ids,axis=1)+offset).ravel()
    probes=gt+offset
    at=np.minimum(np.searchsorted(keys,probes),len(keys)-1)
    hit=keys[at]==probes
    for row in np.linspace(0,len(ids)-1,64,dtype=int):
        matched=set(map(int,ids[row])).intersection(map(int,gt[row]))
        assert set(map(int,gt[row][hit[row]]))==matched
    return hit,hit.sum(axis=1)


def ratio(x,y): return 100*(x/y-1)


def measure():
    verify(ROOT/'inputs.json')
    receipt=read(ROOT/'timing_complete.json')
    assert receipt=={'status':'PASS_E243_TIMING','windows':list(WINDOWS),'points':POINTS,'batches':BATCHES}
    points=[]; rounds=[]; pairs=[]; parity=[]
    refs=read(E231/'seal.json')['files']
    for w in WINDOWS:
        c=read(config(w)); root=Path(c['output_dir']); r=read(root/'complete.json'); size=len(ARMS)*len(GRIDS[w])
        assert (r['status'],r['points'],r['batches'],r['qualified_queries'],r['public_GT_read'])==('PASS_E243_FORMAL',size,size*2,size*256,False)
        idx=np.fromfile(c['rows'],'<i4'); gt=truth(idx)
        for ordinal,l in enumerate(GRIDS[w]):
            here=root/f'K100_L{l}'; local={}; route=None
            for j,m in enumerate(ARMS):
                p=here/m; h,parts=packet(p)
                if route is None: route=parts[2:]
                assert route==parts[2:]
                refs_name=m if m in ARMS[:3] else None
                if refs_name and (E231/'data'/w/f'K100_L{l}'/refs_name/'raw').exists():
                    old=E231/'data'/w/f'K100_L{l}'/refs_name/'raw'
                    checks={f:sealed(old/f,E231,refs).read_bytes()==b for f,b in zip(RAW,parts)}
                    parity.append(dict(window=w,L=l,method=m,**checks))
                rs=[read(p/f'round{i}.json') for i in range(2)]
                slot=(j-ordinal)%len(ARMS)
                for i,t in enumerate(rs):
                    order=slot+1 if i==0 else 2*len(ARMS)-slot
                    assert (t['method'],t['K'],t['L'],t['n'],t['order'],t['cpu'],t['threads'],t['rep'],t['sha256'])==(m,K,l,N,order,15,1,i,h)
                    assert t['seconds']>0 and abs(t['qps']-N/t['seconds'])<1e-8
                    rounds.append(dict(window=w,**t))
                ids=np.frombuffer(parts[0],'<i4').reshape(N,K); assert ids.min()>=0 and ids.max()<c['base']['n']
                hits,counts=actual(ids,gt); exact=np.fromfile(p/'work.i8','u1'); assert len(exact)==256
                n=int(counts.sum()); qs=[t['qps'] for t in rs]
                point=dict(window=w,L=l,method=m,hits=n,recall_pct=100*n/(N*K),qps=float(np.mean(qs)),
                           qps0=qs[0],qps1=qs[1],wall_us=1e6*float(np.mean([t['seconds'] for t in rs]))/N,
                           exact_mean=float(exact.mean()),under_10=int((counts<10).sum()),sha256=h)
                points.append(point); local[m]=(point,hits,exact)
            for m in ARMS[1:]:
                for b in ('B32','B64-old','Far52','Mixed64'):
                    if m==b: continue
                    x,xh,xw=local[b]; y,yh,yw=local[m]
                    if b=='B32': assert (xw<=yw).all()
                    if b=='B64-old' and m=='Far52': assert (yw<=xw).all()
                    if b=='Mixed64' and m=='Mixed52': assert (yw<=xw).all()
                    g=int(np.count_nonzero(yh & ~xh)); lost=int(np.count_nonzero(xh & ~yh))
                    assert g-lost==y['hits']-x['hits']
                    pairs.append(dict(window=w,L=l,method=m,control=b,rescued=g,lost=lost,
                        recall_delta_pp=100*(g-lost)/(N*K),qps_delta_pct=ratio(y['qps'],x['qps']),
                        slow_vs_fast_pct=ratio(min(y['qps0'],y['qps1']),max(x['qps0'],x['qps1'])),
                        wall_delta_us=y['wall_us']-x['wall_us'],exact_delta=float(yw.mean()-xw.mean())))
    assert len(points)==POINTS and len(rounds)==BATCHES
    for key,value in [('points',points),('rounds',rounds),('same_L',pairs),('historical_parity',parity)]:emit(key,value)
    return points,pairs


def fastest(items,threshold): return max((a for a in items if a['hits']>=threshold),key=lambda a:a['qps'],default=None)


def analyze(points,pairs):
    goals=[]; matches=[]; summary={}
    for w in WINDOWS:
        own={a:[p for p in points if p['window']==w and p['method']==a] for a in ARMS}
        out=summary.setdefault(w,{})
        for a in ARMS:
            for b in ('B32','B64-old','Far52','Mixed64'):
                if a==b: continue
                base=own[b]; best={n:max(q['qps'] for q in base if q['hits']==n) for n in sorted({q['hits'] for q in base})}
                lev=list(best); val=list(best.values()); line=[]
                for q in own[a]:
                    baseline=fastest(base,q['hits'])
                    interpolated=float(np.interp(q['hits'],lev,val)) if lev[0]<=q['hits']<=lev[-1] else None
                    row=dict(window=w,method=a,control=b,L=q['L'],recall_pct=q['recall_pct'],qps=q['qps'],
                        control_L=baseline['L'] if baseline else None,control_qps=baseline['qps'] if baseline else None,
                        qps_discrete_delta_pct=ratio(q['qps'],baseline['qps']) if baseline else None,
                        qps_line_delta_pct=ratio(q['qps'],interpolated) if interpolated else None)
                    matches.append(row)
                    if row['qps_line_delta_pct'] is not None: line.append(row['qps_line_delta_pct'])
                goal=[]
                for target in TARGETS:
                    need=int((Decimal(str(target))*N*K/100).to_integral_value(rounding=ROUND_CEILING))
                    p=fastest(own[a],need); ref=fastest(base,need)
                    row=dict(window=w,target_pct=target,target_hits=need,method=a,control=b)
                    for prefix,v in [('a',p),('b',ref)]:
                        row.update({f'{prefix}_{k}':v[k] if v else None for k in ('L','recall_pct','qps','qps0','qps1')})
                    row.update(qps_delta_pct=ratio(p['qps'],ref['qps']) if p and ref else None,
                               slow_vs_fast_pct=ratio(min(p['qps0'],p['qps1']),max(ref['qps0'],ref['qps1'])) if p and ref else None)
                    goal.append(row)
                goals.extend(goal)
                elig=[r for r in goal if r['qps_delta_pct'] is not None]
                deltas=[p['qps_delta_pct'] for p in pairs if p['window']==w and p['method']==a and p['control']==b]
                out[f'{a}/{b}']=dict(comparable=len(elig),faster=sum(r['qps_delta_pct']>0 for r in elig),
                    slow_faster=sum(r['slow_vs_fast_pct']>0 for r in elig),line_overlap=len(line),line_faster=sum(v>0 for v in line),
                    line_median_pct=float(np.median(line)) if line else None,
                    same_L_qps_delta_median=float(np.median(deltas)) if deltas else None,
                    primary=next(r for r in goal if r['target_pct']==75.5))
    emit('targets',goals); emit('matched',matches); write(A/'outcome.json',summary)


if __name__=='__main__': analyze(*measure())
