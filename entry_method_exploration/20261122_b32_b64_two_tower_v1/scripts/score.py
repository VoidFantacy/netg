"""Verify native receipts and score returned IDs. Formal GT is opened only after both runs."""
import csv
import hashlib
from pathlib import Path
import struct
import sys

import numpy as np

from run import ARMS, DATASETS, K, LGRID, N, OFF, RAW, ROOT, SHORT, cfg, digest, read, truth, verify, write

ANALYSIS = ROOT/'analysis'


def table(name, rows):
    assert rows
    with (ANALYSIS/f'{name}.csv').open('x') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def rows(file, length, width=1, dtype='<i4'):
    a = np.fromfile(file, dtype).reshape(-1, width)
    assert a.shape == (length, width), file
    return a


def score(raw, gt):
    n = len(gt)
    output = rows(raw/'ids.i32', n, K)
    joined = (output[:, :, None] == gt[:, None, :]).any(axis=2)
    expected = [set(map(int, v)).intersection(answer) for v, answer in zip(output, gt)]
    observed = [set(map(int, v[m])) for v, m in zip(output, joined)]
    assert expected == observed
    return output, expected, int(joined.sum())


def changed(before, after):
    rescued = sum(len(b-a) for a,b in zip(before,after))
    damaged = sum(len(a-b) for a,b in zip(before,after))
    return rescued, damaged


def ledger(path, n):
    candidates = rows(path/'candidates.i8', n, dtype='u1').ravel()
    exact = rows(path/'exact.i8', n, dtype='u1').ravel()
    assert (exact <= candidates).all()
    selected = np.fromfile(path/'selected.i32', '<i4')
    assert selected.size == exact.sum()
    offsets = np.r_[0,np.cumsum(exact)]
    sets = [set(map(int, selected[a:b])) for a,b in zip(offsets[:-1],offsets[1:])]
    assert all(len(s)==count for s,count in zip(sets,exact))
    return candidates, exact, sets


def replay():
    out = []
    for ds in DATASETS:
        c = read(cfg(ds,'replay'))
        directory = Path(c['output_dir'])
        cal = np.fromfile(c['cal_rows'],'<i4')
        gt = truth(ds,N,N)[cal]
        receipt = read(directory/'complete.json')
        assert receipt['status']=='PASS_E226_REPLAY' and receipt['points']==56
        assert receipt['query_merge_checks']==56*len(gt)
        for l in OFF:
            key = f'K100_L{l}'
            p = directory/key
            main = rows(Path(c['teacher_cache'])/key/'GT10/raw/ids.i32',N,K)[cal]
            main_hits = [set(map(int,r)).intersection(target) for r,target in zip(main,gt)]
            ref_hit, pool_sets, pool_counts = {}, {}, {}
            for name, cap in [('B32',96),('B64',192),*((arm,b) for arm in SHORT for b in (16,32,48))]:
                full = name in {'B32','B64'}
                width = name[-2:]
                method = p/(name if full else f'{name}-{cap}')
                _, hits, count = score(method/'raw',gt)
                candidates, exact, selected = ledger(method,len(gt))
                assert (exact==np.minimum(candidates,cap)).all()
                if full:
                    pool_sets[width], pool_counts[width] = selected, candidates
                    if width=='64':
                        assert all(a<=b for a,b in zip(pool_sets['32'],selected))
                else:
                    assert (pool_counts[width]==candidates).all()
                    assert all(a<=b for a,b in zip(selected,pool_sets[width]))
                ref_hit[name,cap] = hits
                against_b32 = changed(ref_hit['B32',96],hits)
                against_pool = changed(ref_hit[f'B{width}',96 if width=='32' else 192],hits)
                against_pca = changed(ref_hit.get((f'PCA-B{width}',cap),hits),hits)
                gained_from_main = changed(main_hits,hits)
                selected_gt = sum(len(s.intersection(t)) for s,t in zip(selected,gt))
                out.append(dict(dataset=ds,L=l,method=name,cap=cap,queries=len(gt),hits=count,
                    recall=count/(len(gt)*K),mean_pool=float(candidates.mean()),mean_exact=float(exact.mean()),
                    p90_exact=float(np.quantile(exact,.9)),gt_members_in_scored_candidates=selected_gt,
                    main_rescued=gained_from_main[0],main_damaged=gained_from_main[1],
                    B32_rescued=against_b32[0],B32_damaged=against_b32[1],
                    own_pool_rescued=against_pool[0],own_pool_damaged=against_pool[1],
                    PCA_rescued=against_pca[0],PCA_damaged=against_pca[1]))
    table('replay',out)


def packet_sha(path, length):
    digest = hashlib.sha256(struct.pack('<QQ',length,K))
    for file in RAW:
        digest.update((path/file).read_bytes())
    digest.update(bytes(length*16))
    return digest.hexdigest()


def ratio(a,b):
    return 100*(a/b-1)


def formal():
    configs = {ds:read(cfg(ds,'formal')) for ds in DATASETS}
    receipts = {ds:read(Path(c['output_dir'])/'complete.json') for ds,c in configs.items()}
    assert all(r['status']=='PASS_E226_FORMAL' and r['points']==66 and r['batches']==132 and
               r['public_GT_read'] is False for r in receipts.values())
    points, rounds, contrasts, parity = [], [], [], []
    old = ROOT.parent/'20261122_p64_candidate_probe_v1'
    specs = read(old/'seal.json')['files']
    for ds,c in configs.items():
        root = Path(c['output_dir'])
        gt = truth(ds,0,N,formal=True)
        dataset = []
        for l in LGRID:
            point = root/f'K100_L{l}'
            works, hitsets, orders, by_arm = {}, {}, [], {}
            for arm in ARMS:
                path = point/arm
                rs = [read(path/f'round{i}.json') for i in range(2)]
                sha = packet_sha(path/'raw',N)
                if ds=='coco' and arm=='B32':
                    prior = old/'data'/'coco'/point.name/'B32'/'raw'
                    match = {}
                    for file in RAW:
                        former = prior/file
                        assert digest(former)==specs[str(former.relative_to(old))]['sha256']
                        match[file] = (former.read_bytes()==(path/'raw'/file).read_bytes())
                    parity.append(dict(L=l,**match))
                routes = [(path/'raw'/file).read_bytes() for file in RAW[-2:]]
                if arm=='B32':
                    expected_routes=routes
                assert routes==expected_routes
                assert all(t['L']==l and t['K']==K and t['n']==N and t['method']==arm and
                           t['cpu']==15 and t['threads']==1 and t['rep']==i and t['sha256']==sha and
                           abs(N/t['seconds']-t['qps'])<1e-8 for i,t in enumerate(rs))
                orders.extend(t['order'] for t in rs)
                rounds.extend(dict(dataset=ds,**t) for t in rs)
                _, hitsets[arm], count = score(path/'raw',gt)
                work = rows(path/'qualification.i8',256,2,dtype='u1')
                works[arm] = work
                width=arm[-2:]
                candidate_limit = 3*int(width)
                cap = candidate_limit if arm in ('B32','B64') else 48
                assert (work[:,0] <= candidate_limit).all()
                assert (work[:,1] == np.minimum(work[:,0],cap)).all()
                if arm in SHORT:
                    assert (work[:,0]==works[f'B{width}'][:,0]).all()
                qps = [t['qps'] for t in rs]
                seconds = [t['seconds'] for t in rs]
                record = dict(dataset=ds,L=l,method=arm,hits=count,recall=count/(N*K),
                    low_recall_queries=sum(len(s)<10 for s in hitsets[arm]),
                    qps=float(np.mean(qps)),qps0=qps[0],qps1=qps[1],
                    wall_us=float(np.mean(seconds))*1e6/N,
                    mean_pool_256=float(work[:,0].mean()),mean_exact_256=float(work[:,1].mean()))
                dataset.append(record)
                by_arm[arm]=record
            assert sorted(orders)==list(range(1,13))
            assert (works['B64'][:,0]>=works['B32'][:,0]).all()
            for method in ARMS[1:]:
                item=by_arm[method]
                r,d=changed(hitsets['B32'],hitsets[method])
                if method.startswith('TT-'):
                    pr,pd=changed(hitsets[f'PCA-{method[-3:]}'],hitsets[method])
                    net_pca=pr-pd
                else:
                    pr=pd=net_pca=None
                assert r-d==item['hits']-by_arm['B32']['hits']
                contrasts.append(dict(dataset=ds,L=l,method=method,B32_rescued=r,B32_damaged=d,B32_net=r-d,
                    PCA_rescued=pr,PCA_damaged=pd,PCA_net=net_pca,
                    improved_low_recall=sum(len(a)<10 and len(b)>len(a)
                                            for a,b in zip(hitsets['B32'],hitsets[method])),
                    left_low_recall=sum(len(a)<10 and len(b)>=10
                                        for a,b in zip(hitsets['B32'],hitsets[method])),
                    qps_pct_vs_B32=ratio(item['qps'],by_arm['B32']['qps']),
                    wall_us_delta_vs_B32=item['wall_us']-by_arm['B32']['wall_us']))
        points.extend(dataset)
    table('points',points)
    table('rounds',rounds)
    table('same_L',contrasts)
    table('E225_coco_B32_packet_parity',parity)
    matched, outcomes = frontier(points)
    table('matched',matched)
    write(ANALYSIS/'outcomes.json',outcomes)


def frontier(points):
    detail = []
    summary = {}
    for ds in DATASETS:
        base = sorted([p for p in points if p['dataset']==ds and p['method']=='B32'],key=lambda p:p['hits'])
        unique = {p['hits']:max(q['qps'] for q in base if q['hits']==p['hits']) for p in base}
        xs = sorted(unique)
        for arm in ARMS[1:]:
            own = [p for p in points if p['dataset']==ds and p['method']==arm]
            entries = []
            for p in own:
                eligible = [b for b in base if b['hits']>=p['hits']]
                comparator = max(eligible,key=lambda b:b['qps']) if eligible else None
                interp = float(np.interp(p['hits'],xs,[unique[x] for x in xs])) if xs[0]<=p['hits']<=xs[-1] else None
                entry = dict(dataset=ds,method=arm,L=p['L'],recall=p['recall'],qps=p['qps'],
                    B32_L=comparator['L'] if comparator else None,
                    B32_recall=comparator['recall'] if comparator else None,
                    B32_qps=comparator['qps'] if comparator else None,
                    qps_pct=ratio(p['qps'],comparator['qps']) if comparator else None,
                    slow_vs_fast_pct=ratio(min(p['qps0'],p['qps1']),max(comparator['qps0'],comparator['qps1'])) if comparator else None,
                    interp_pct=ratio(p['qps'],interp) if interp is not None else None,
                    B32_point_dominates=bool(comparator and comparator['qps']>=p['qps']))
                entries.append(entry)
            valid=[x for x in entries if x['qps_pct'] is not None]
            interpolation=[x for x in entries if x['interp_pct'] is not None]
            summary.setdefault(ds,{})[arm]={
                'points':len(entries),'eligible':len(valid),'dominated':sum(x['B32_point_dominates'] for x in entries),
                'faster_than_discrete':sum(x['qps_pct']>0 for x in valid),
                'slow_faster_than_fast':sum(x['slow_vs_fast_pct']>0 for x in valid),
                'overlap':len(interpolation), 'faster_than_B32_line':sum(x['interp_pct']>0 for x in interpolation),
                'best_discrete':max(valid,key=lambda x:x['qps_pct']) if valid else None,
                'interpolated_gain_minmax':[min(x['interp_pct'] for x in interpolation),max(x['interp_pct'] for x in interpolation)] if interpolation else None}
            detail.extend(entries)
    return detail,summary


if __name__=='__main__':
    for kind in ('input','pools','models'):
        verify(ROOT/f'{kind}_freeze.json')
    {'replay':replay, 'formal':formal}[sys.argv[1]]()
