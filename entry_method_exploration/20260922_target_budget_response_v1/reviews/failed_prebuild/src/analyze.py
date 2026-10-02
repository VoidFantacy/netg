"""Re-score the complete old/new response matrix and test budget transfer."""
from common import *
import csv

def point_path(ds, method, K, L, cfg):
    root = RUN if L in cfg['missing'][str(K)] else OLD
    return root/'results'/('main_'+ds)/method/f'k{K}_L{L}'

def score(ids, gt, K):
    if K == 1:
        return (ids[:,0] == gt[:,0]).astype('i2')
    counts = []
    for start in range(0,len(ids),128):
        mask = (ids[start:start+128,:,None] == gt[start:start+128,None,:K]).any(1)
        counts.append(mask.sum(1).astype('i2'))
    return np.concatenate(counts)

def dataset(ds, cfg, lock):
    native = cfg['native']
    gt = np.fromfile(native['GT'],'<i4').reshape(4096,100)
    assert np.all(np.diff(np.sort(gt,axis=1),axis=1)>0)
    methods = [m['name'] for m in native['methods']]
    cols = [methods.index(m) for m in lock['actions']]
    arrays = dict(source_rows=np.fromfile(native['rows'],'<i8'))
    metrics = []
    for K in [1,100]:
        Ls = sorted(set(cfg['old_K_L'][str(K)]+cfg['missing'][str(K)]))
        for L in Ls:
            hits = []
            ndcs = []
            for method in methods:
                p = point_path(ds,method,K,L,cfg)
                done = read(p/'complete.json')
                assert done['plain_count_bit_parity'] and done['K'] == K and done['L'] == L and done['n'] == 4096
                ids = np.fromfile(p/'ids.i32','<i4').reshape(4096,K)
                dist = np.fromfile(p/'distances.f32','<f4').reshape(4096,K)
                ndc = np.fromfile(p/'ndc.u64','<u8')
                assert np.all((ids>=0)&(ids<native['base_n'])) and np.isfinite(dist).all()
                assert np.all(np.diff(dist,axis=1)>=0)
                assert K == 1 or np.all(np.diff(np.sort(ids,axis=1),axis=1)>0)
                h = score(ids,gt,K)
                hits.append(h)
                ndcs.append(ndc)
                metrics.append(dict(dataset=ds,method=method,K=K,L=L,recall=float(h.mean()/K),
                    graph_ndc_mean=float(ndc.mean()),source='new' if RUN in p.parents else 'E107',formal_QPS=False))
            arrays[f'K{K}_L{L}'] = np.stack(hits,axis=1)
            arrays[f'NDC_K{K}_L{L}'] = np.stack(ndcs,axis=1)
    np.savez_compressed(RUN/'analysis'/f'{ds}.npz',**arrays)
    transfers = []
    for K in [1,100]:
        low = arrays[f'K{K}_L128'][:,cols].astype('f8')/K
        low_choice = low.argmax(1)
        for L in sorted(set(cfg['old_K_L'][str(K)]+cfg['missing'][str(K)])):
            high = arrays[f'K{K}_L{L}'][:,cols].astype('f8')/K
            base = high[:,0]
            oracle = high.max(1)
            transfer = high[np.arange(len(high)),low_choice]
            oracle_delta = oracle-base
            transfer_delta = transfer-base
            optimum_overlap = ((low == low.max(1,keepdims=True)) & (high == oracle[:,None])).any(1)
            low_delta = low-low[:,:1]
            high_delta = high-high[:,:1]
            drift = np.max(np.abs(low_delta-high_delta),axis=1)
            regret = oracle-transfer
            assert np.all(regret <= 2*drift+1e-12)
            retention = float(transfer_delta.mean()/oracle_delta.mean()) if oracle_delta.mean()>0 else None
            transfers.append(dict(dataset=ds,K=K,L=L,target_endpoint=L in cfg['target'][str(K)],
                primary_upper=L == cfg['target'][str(K)][1],baseline_recall=float(base.mean()),
                oracle_gain_pp=float(100*oracle_delta.mean()),oracle_CI95_pp=bootstrap(100*oracle_delta),
                transferred_gain_pp=float(100*transfer_delta.mean()),transferred_CI95_pp=bootstrap(100*transfer_delta),
                regret_pp=float(100*regret.mean()),retention=retention,
                preserves_80pct=retention is not None and retention>=lock['transfer_retention_gate'],
                optimal_set_overlap=float(optimum_overlap.mean()),
                winner_agreement=float((low_choice == high.argmax(1)).mean()),
                low_positive_to_high_negative=int(((low_delta[:,1:]>0)&(high_delta[:,1:]<0)).sum()),
                low_negative_to_high_positive=int(((low_delta[:,1:]<0)&(high_delta[:,1:]>0)).sum()),
                transferred_rescue_queries=int((transfer_delta>0).sum()),
                transferred_harmed_queries=int((transfer_delta<0).sum())))
    return metrics,transfers

if __name__ == '__main__':
    assert read(RUN/'reviews/search_complete.json')['status'] == 'PASS'
    assert not (RUN/'analysis/response.json').exists()
    start = time.monotonic()
    lock = read(RUN/'config.locked.json')
    allmetrics, transfers = [], []
    for ds, cfg in lock['datasets'].items():
        m,t = dataset(ds,cfg,lock)
        allmetrics.extend(m)
        transfers.extend(t)
        print('SCORED',ds,flush=True)
    primary = [t for t in transfers if t['primary_upper']]
    headroom = all(t['oracle_gain_pp'] >= 100*lock['oracle_gain_gate'] for t in primary)
    mismatch = any(not t['preserves_80pct'] for t in primary if t['L'] != 128)
    eligible = headroom and mismatch
    dump(RUN/'analysis/response.json',dict(primary=primary,all_transfers=transfers,
        headroom_gate=headroom,budget_mismatch=mismatch,information_control_eligible=eligible,
        seconds=time.monotonic()-start,scope='finite seven-strategy Recall oracle; not all-H or QPS'))
    with (RUN/'analysis/metrics.csv').open('w') as f:
        writer = csv.DictWriter(f,fieldnames=list(allmetrics[0]))
        writer.writeheader()
        writer.writerows(allmetrics)
    dump(RUN/'state.json',dict(status='INFORMATION_CONTROL_ELIGIBLE' if eligible else 'STOP_TARGET_QUALITY_LEVER',
        completed=False,pending=(['fixed_information_control'] if eligible else [])+['audit','report','documentation']))
    print(json.dumps(dict(primary=primary,headroom_gate=headroom,budget_mismatch=mismatch,eligible=eligible),indent=2),flush=True)
