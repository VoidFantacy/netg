"""Independently score physical query rows and compare the actual full-wall points."""
import csv
from decimal import Decimal, ROUND_CEILING
from hashlib import sha256
from pathlib import Path
import struct

import numpy as np

from drive import BATCHES,COCO,DATASETS,E213,E228,FLICKR,GRID,N,POINTS,RAW,ROOT,TARGETS,WEBVID,YANDEX,config,digest,read,sealed,verify,write

A=ROOT/'analysis'
ARMS=('B32','B64')


def output(name, rows):
    assert rows
    with (A/f'{name}.csv').open('x') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def truth(spec,rows,base_n):
    p=Path(spec['path'])
    assert spec['k']==spec['width']==100 and digest(p)==spec['expected_sha256']
    if spec['format']=='raw_i64':
        a=np.memmap(p,'<i8','r').reshape(spec['n'],100)[rows]
    else:
        assert spec['format']=='ivecs'
        data=np.memmap(p,'<i4','r').reshape(spec['n'],101)[rows]
        assert (data[:,0]==100).all()
        a=data[:,1:]
    assert a.shape==(N,100) and a.min()>=0 and a.max()<base_n
    assert np.all(np.diff(np.sort(a,axis=1),axis=1)>0)
    return a


def counts(ids,gt):
    included=(ids[:,:,None]==gt[:,None,:]).any(axis=2)
    checked=[set(map(int,row)).intersection(target) for row,target in zip(ids,gt)]
    assert all(set(map(int,row[mask]))==s for row,mask,s in zip(ids,included,checked))
    assert included.sum()==sum(map(len,checked))
    return checked,np.count_nonzero(included,axis=1)


def packet(p,k):
    parts=[(p/'raw'/f).read_bytes() for f in RAW]
    assert tuple(map(len,parts))==(N*k*4,N*k*4,N*3*4,N*3*4)
    h=sha256(struct.pack('<QQ',N,k)+b''.join(parts)+bytes(N*16)).hexdigest()
    return h,parts


def history(ds,k,l,arm,parts,archived):
    if ds in (FLICKR,YANDEX) and arm=='B32':
        experiment=E213
        prior=experiment/'data'/ds/f'K{k}_L{l}'/'GT10-B32-SPAN4'/'raw'
    elif ds in (COCO,WEBVID) and k==100:
        experiment=E228
        prior=experiment/'data'/ds/f'K{k}_L{l}'/arm/'raw'
    else:
        return None
    if not prior.exists():
        return None
    return dict(dataset=ds,K=k,L=l,method=arm,experiment=experiment.name,
                **{f:sealed(prior/f,experiment,archived[experiment]).read_bytes()==b for f,b in zip(RAW,parts)})


def measure():
    timing=read(ROOT/'timing_complete.json')
    assert timing=={'status':'PASS_E229_TIMING','datasets':list(DATASETS),'points':POINTS,'batches':BATCHES}
    archive={E213:read(E213/'seal.json')['experiment_files'],E228:read(E228/'seal.json')['files']}
    specs=read(E213/'gt_eval.json')
    points=[]; rounds=[]; pairs=[]; parity=[]
    for ds in DATASETS:
        c=read(config(ds)); r=read(ROOT/'data'/ds/'complete.json')
        expected_pairs=sum(len(GRID[ds,k]) for k in (1,100))
        assert (r['status'],r['points'],r['batches'],r['qualified_queries'],r['public_GT_read'])==(
            'PASS_E229_FORMAL',2*expected_pairs,4*expected_pairs,512*expected_pairs,False)
        assert r['peak_rss_kib']>0 and r['binding']['N']==c['base']['n'] and r['binding']['metric_id']==0
        by_row=np.fromfile(c['rows'],'<i4')
        assert by_row.shape==(N,) and (np.diff(by_row)>0).all()
        all_gt=truth(specs[ds],by_row,c['base']['n'])
        ordinal=0
        for k in (1,100):
            gt=all_gt[:,:k]
            for l in GRID[ds,k]:
                base=ROOT/'data'/ds/f'K{k}_L{l}'
                result=[]
                for i,m in enumerate(ARMS):
                    p=base/m
                    h,raw=packet(p,k)
                    old=history(ds,k,l,m,raw,archive)
                    if old is not None:
                        parity.append(old)
                    if i==0:
                        baseline_route=raw[2:]
                    else:
                        assert raw[2:]==baseline_route
                    rs=[read(p/f'round{rep}.json') for rep in range(2)]
                    for rep,t in enumerate(rs):
                        expected_order=1+2*rep+((i-rep-ordinal)%2)
                        assert (t['K'],t['L'],t['n'],t['rep'],t['order'],t['method'],t['cpu'],t['threads'],t['sha256'])==(
                            k,l,N,rep,expected_order,m,15,1,h)
                        assert t['seconds']>0 and abs(t['qps']-N/t['seconds'])<1e-8
                        rounds.append(dict(dataset=ds,**t))
                    ids=np.frombuffer(raw[0],'<i4').reshape(N,k)
                    assert ids.min()>=0 and ids.max()<c['base']['n']
                    hits,per_query=counts(ids,gt)
                    work=np.fromfile(p/'work.i8','u1')
                    assert work.shape==(256,) and (work<=3*int(m[1:])).all()
                    exact=int(per_query.sum())
                    point=dict(dataset=ds,K=k,L=l,method=m,queries=N,hits=exact,recall_pct=100*exact/(N*k),
                        qps=float(np.mean([t['qps'] for t in rs])),qps0=rs[0]['qps'],qps1=rs[1]['qps'],
                        wall_us=1e6*float(np.mean([t['seconds'] for t in rs]))/N,mean_exact_256=float(work.mean()),
                        failures_under_10=int((per_query<10).sum()) if k==100 else None,packet_sha256=h)
                    points.append(point)
                    result.append((point,hits,per_query,work))
                (b,bh,bl,bw),(t,th,tl,tw)=result
                assert (bw<=tw).all()
                gain=sum(len(y-x) for x,y in zip(bh,th)); loss=sum(len(x-y) for x,y in zip(bh,th))
                assert gain-loss==t['hits']-b['hits']
                pairs.append(dict(dataset=ds,K=k,L=l,base_hits=b['hits'],wide_hits=t['hits'],rescued=gain,lost=loss,
                    recall_delta_pp=100*(gain-loss)/(N*k),qps_delta_pct=pct(t['qps'],b['qps']),
                    wall_delta_us=t['wall_us']-b['wall_us'],mean_added_exact_256=t['mean_exact_256']-b['mean_exact_256'],
                    improved_failures=int(((bl<10)&(tl>bl)).sum()) if k==100 else None,
                    recovered_failures=int(((bl<10)&(tl>=10)).sum()) if k==100 else None,
                    new_failures=int(((bl>=10)&(tl<10)).sum()) if k==100 else None))
                ordinal+=1
    assert len(points)==POINTS and len(rounds)==BATCHES
    output('points',points); output('rounds',rounds); output('same_L',pairs); output('historical_parity',parity)
    return points,pairs


def pct(a,b):
    return 100*(a/b-1)


def fastest(points,min_hits):
    return max((x for x in points if x['hits']>=min_hits),key=lambda x:x['qps'],default=None)


def target_results(ds,k,b,t):
    for target in TARGETS[ds,k]:
        needed=int((Decimal(str(target))*N*k/100).to_integral_value(rounding=ROUND_CEILING))
        p=fastest(b,needed); r=fastest(t,needed)
        row=dict(dataset=ds,K=k,target_pct=target,target_hits=needed)
        for mode,point in zip(ARMS,(p,r)):
            row.update({f'{mode}_{key}':point[key] if point else None for key in ('L','recall_pct','qps','qps0','qps1')})
        row['qps_delta_pct']=pct(r['qps'],p['qps']) if r and p else None
        row['slow_vs_fast_pct']=pct(min(r['qps0'],r['qps1']),max(p['qps0'],p['qps1'])) if r and p else None
        yield row


def all_matches(ds,k,b,t):
    lut={x:max(p['qps'] for p in b if p['hits']==x) for x in sorted({p['hits'] for p in b})}
    hits=list(lut)
    for p in t:
        match=fastest(b,p['hits'])
        interp=float(np.interp(p['hits'],hits,list(lut.values()))) if hits[0]<=p['hits']<=hits[-1] else None
        rival=any(q['qps']>=p['qps'] and q['hits']>=p['hits'] and
                  (q['qps']>p['qps'] or q['hits']>p['hits']) for q in b)
        yield dict(dataset=ds,K=k,B64_L=p['L'],B64_recall_pct=p['recall_pct'],B64_QPS=p['qps'],
            B32_L=match['L'] if match else None,B32_recall_pct=match['recall_pct'] if match else None,
            B32_QPS=match['qps'] if match else None,qps_delta_pct=pct(p['qps'],match['qps']) if match else None,
            line_delta_pct=pct(p['qps'],interp) if interp else None,is_dominated_by_B32=rival)


def evaluate(points,pairs):
    matched=[]; goals=[]; out={}
    for ds in DATASETS:
        for k in (1,100):
            b,t=([p for p in points if p['dataset']==ds and p['K']==k and p['method']==m] for m in ARMS)
            fixed=list(target_results(ds,k,b,t))
            each=list(all_matches(ds,k,b,t))
            comp=[x for x in fixed if x['qps_delta_pct'] is not None]
            line=[x['line_delta_pct'] for x in each if x['line_delta_pct'] is not None]
            changes=[x for x in pairs if x['dataset']==ds and x['K']==k]
            gain=[x['recall_delta_pp'] for x in changes]
            out.setdefault(ds,{})[k]=dict(targets_total=len(fixed),targets_both=len(comp),
                targets_faster=sum(x['qps_delta_pct']>0 for x in comp),
                targets_slow_faster=sum(x['slow_vs_fast_pct']>0 for x in comp),
                targets_smaller_L=sum(x['B64_L']<x['B32_L'] for x in comp),
                line_both=len(line),line_faster=sum(x>0 for x in line),line_delta_median=float(np.median(line)) if line else None,
                same_L_recall_range_pp=[min(gain),max(gain)],same_L_positive=sum(x>0 for x in gain),
                same_L_lost_total=sum(x['lost'] for x in changes),
                same_L_qps_delta_median=float(np.median([x['qps_delta_pct'] for x in changes])),
                same_L_mean_added_exact=float(np.mean([x['mean_added_exact_256'] for x in changes])),
                best_target=max(comp,key=lambda x:x['qps_delta_pct']) if comp else None)
            goals.extend(fixed); matched.extend(each)
    output('targets',goals); output('matched',matched); write(A/'outcome.json',out)


if __name__=='__main__':
    verify(ROOT/'inputs.json')
    evaluate(*measure())
