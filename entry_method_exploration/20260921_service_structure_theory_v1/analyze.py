"""Frozen cache-only structural diagnostic; no ANN, GT, or online model fit."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
import hashlib
import json
import time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCES = ROOT / 'fast_router_diagnosis/20260908_v1/results/run_v1/main'
DATASETS = ['webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1']
RANKS = [1, 2, 4, 8, 16, 32, 64]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(p, value):
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def centered(x):
    return x - x.mean(1, keepdims=True) - x.mean(0, keepdims=True) + x.mean()


def spectrum(x):
    s = np.linalg.svd(x, compute_uv=False)
    e = s * s
    total = float(e.sum())
    if total < 1e-24:
        return {'energy': total, 'fraction': {str(r): 0.0 for r in RANKS}, 'rank90': 0}
    c = np.cumsum(e) / total
    return {'energy': total, 'fraction': {str(r): float(c[min(r, len(c))-1]) for r in RANKS},
            'rank90': int(np.searchsorted(c, .9) + 1)}


def block_predict(a, b, c, rank):
    grand = a.mean()
    amr, amc = a.mean(1, keepdims=True), a.mean(0, keepdims=True)
    bm, cm = b.mean(0, keepdims=True), c.mean(1, keepdims=True)
    ac = a - amr - amc + grand
    bc, cc = b - amr - bm + grand, c - cm - amc + grand
    u, s, vt = np.linalg.svd(ac, full_matrices=False)
    r = min(rank, int(np.count_nonzero(s > max(s[0], 1.) * 1e-12)))
    d0 = cm + bm - grand
    pred = d0 + ((cc @ vt[:r].T) / s[:r]) @ (u[:, :r].T @ bc)
    return d0, pred, s


def assess(x, train_rows, test_rows, anchors, targets, boot=None):
    a, b = x[np.ix_(train_rows, anchors)], x[np.ix_(train_rows, targets)]
    c, d = x[np.ix_(test_rows, anchors)], x[np.ix_(test_rows, targets)]
    d0, pred, s = block_predict(a, b, c, 8)
    # Baseline ties use B column means, avoiding irrelevant floating-point row shifts.
    base_choice = np.full(len(test_rows), int(b.mean(0).argmax()), dtype=np.int64)
    choices = pred.argmax(1)
    rows = np.arange(len(test_rows))
    base, got = d[rows, base_choice], d[rows, choices]
    delta = got - base
    mse0, mse = float(np.mean((d-d0)**2)), float(np.mean((d-pred)**2))
    result = {'mse_additive': mse0, 'mse_rank8': mse, 'mse_reduction': 1-mse/mse0,
              'baseline_recall': float(base.mean()), 'rank8_recall': float(got.mean()),
              'delta_pp': float(100*delta.mean()), 'rescued': int((delta>1e-10).sum()),
              'harmed': int((delta < -1e-10).sum()), 'tied': int((abs(delta)<=1e-10).sum()),
              'oracle_recall': float(d.max(1).mean()),
              'rank8_regret_pp': float(100*(d.max(1)-got).mean()),
              'baseline_regret_pp': float(100*(d.max(1)-base).mean()),
              'anchor_singular_values_top8': s[:8].tolist()}
    if boot is not None:
        bs = 100*delta[boot].mean(1)
        result['delta_ci98_75_pp'] = np.quantile(bs, [.00625, .99375]).tolist()
    arrays = dict(a=a, b=b, c=c, d=d, additive=d0, prediction=pred,
                  baseline_choice=base_choice, choice=choices, delta=delta)
    return result, arrays


def synthetic():
    rng = np.random.default_rng(120)
    z, v = rng.normal(size=(48,3)), rng.normal(size=(64,3))
    x = rng.normal(size=(48,1)) + rng.normal(size=(1,64)) + z@v.T
    _, pred, _ = block_predict(x[:24,:32], x[:24,32:], x[24:,:32], 3)
    err = float(abs(pred-x[24:,32:]).max())
    assert err < 1e-10
    trap = .5*np.ones((64,64)) + .01*np.eye(64)
    raw, residual = spectrum(trap), spectrum(centered(trap))
    assert raw['fraction']['1'] > .999 and residual['fraction']['8'] < .13
    # Different underlying query types collapse to the same observable phi(q).
    hidden = np.tile([-1., 1.], 32)
    u = .5 + .4*hidden[:,None]*np.array([-1., 1.])[None,:]
    assert np.linalg.matrix_rank(centered(u), tol=1e-10) == 1
    oracle, observable_best = float(u.max(1).mean()), float(u.mean(0).max())
    assert abs(oracle-.9)<1e-12 and abs(observable_best-.5)<1e-12
    q = rng.normal(size=(50,8)); q /= np.linalg.norm(q,axis=1,keepdims=True)
    prior = rng.normal(size=8); prior /= np.linalg.norm(prior)
    weights = rng.uniform(size=50)
    vec = prior + weights@q
    p = vec / np.linalg.norm(vec)
    draws = rng.normal(size=(5000,8)); draws /= np.linalg.norm(draws,axis=1,keepdims=True)
    assert (draws@vec).max() <= p@vec+1e-12
    truth = rng.uniform(size=(1000,15))
    estimate = truth + rng.uniform(-.1,.1,size=truth.shape)
    regret = truth.max(1)-truth[np.arange(1000),estimate.argmax(1)]
    bound = 2*np.max(abs(estimate-truth),axis=1)
    assert np.all(regret <= bound+1e-12)
    return {'exact_rank3_block_max_error': err, 'raw_rank_trap': raw,
            'decision_interaction_rank_trap': residual,
            'rank1_unobservable_example': {'oracle':oracle, 'best_observable_policy':observable_best},
            'centroid_objective':float(p@vec), 'centroid_norm':float(np.linalg.norm(vec)),
            'regret_bound_cases_checked':1000, 'passed':True}


def main():
    start = time.perf_counter()
    out = HERE / 'results'
    out.mkdir(exist_ok=False)
    manifest = {'protocol_sha256':sha(HERE/'protocol.md'), 'script_sha256':sha(Path(__file__)),
                'sources':[], 'dtype':'float64', 'new_searches':0, 'new_router_models':0,
                'response_factorizations':True, 'metric':'historical Recall@10; not current R1/R100'}
    results = {'synthetic':synthetic(), 'datasets':{}}
    for di, dataset in enumerate(DATASETS):
        src = SOURCES / dataset
        cp = src / 'config.json'
        cfg = json.loads(cp.read_text())
        assert cfg['pilot_count']==512 and cfg['top_k']==10
        n,h = cfg['num_queries'],cfg['hub_count']
        row_path = Path(cfg['row_ids'])
        row_ids = np.fromfile(row_path,dtype='<i8')
        assert row_ids.size == n and np.unique(row_ids[:512]).size==512
        rng = np.random.default_rng(20260921+di)
        rp,hp = rng.permutation(512),rng.permutation(h)
        tr,te,ac,tc = rp[:256],rp[256:],hp[:h//2],hp[h//2:]
        boot=np.random.default_rng(20260922+di).integers(0,256,size=(8192,256))
        sub = out / dataset; sub.mkdir()
        dump(sub/'split.json', {'train_local_rows':tr.tolist(),'test_local_rows':te.tolist(),
             'train_source_rows':row_ids[tr].tolist(),'test_source_rows':row_ids[te].tolist(),
             'anchor_local_hubs':ac.tolist(),'target_local_hubs':tc.tolist()})
        dataset_results={}
        for pth in [cp,row_path,src/'metadata.json']:
            manifest['sources'].append({'path':str(pth.relative_to(ROOT)), 'bytes':pth.stat().st_size,'sha256':sha(pth)})
        meta=json.loads((src/'metadata.json').read_text()); assert meta['status']=='COMPLETE'
        for L in [64,128]:
            lp=src/f'L{L}'
            counts=np.fromfile(lp/'all_single.hitcount.u8',dtype=np.uint8).reshape(n,h)
            masks=np.fromfile(lp/'all_single.hitmask.u16',dtype='<u2').reshape(n,h)
            assert counts.max()<=10 and masks.max()<1024
            pop=np.array([i.bit_count() for i in range(1024)],dtype=np.uint8)
            assert np.array_equal(counts,pop[masks])
            for pth in [lp/'all_single.hitcount.u8',lp/'all_single.hitmask.u16',lp/'complete.json']:
                manifest['sources'].append({'path':str(pth.relative_to(ROOT)), 'bytes':pth.stat().st_size,'sha256':sha(pth)})
            x=counts[:512].astype(np.float64)/10
            dc=centered(x)
            metric, arrays = assess(x,tr,te,ac,tc,boot)
            sps={'raw':spectrum(x),'row_centered':spectrum(x-x.mean(1,keepdims=True)),
                 'double_centered':spectrum(dc)}
            nulls=[]
            for ni in range(8):
                nrng=np.random.default_rng(20261921+100*di+ni)
                nx=np.stack([row[nrng.permutation(h)] for row in x])
                ns=spectrum(centered(nx))
                nm,_=assess(nx,tr,te,ac,tc)
                nulls.append({'seed':20261921+100*di+ni, 'spectrum':ns,'block':nm})
            checks={'rank8_energy_at_least_50_percent':sps['double_centered']['fraction']['8']>=.5,
                    'mse_reduction_at_least_10_percent':metric['mse_reduction']>=.1,
                    'policy_gain_at_least_1pp':metric['delta_pp']>=1}
            item={'n':512,'h':h,'constant_query_fraction':float(np.mean(np.ptp(x,axis=1)==0)),
                  'spectra':sps, 'block':metric,'nulls':nulls,'strong_prediction':checks}
            np.savez_compressed(sub/f'L{L}_blocks.npz',**arrays)
            dataset_results[str(L)]=item
            print(json.dumps({'dataset':dataset,'L':L,'raw_rank1':sps['raw']['fraction']['1'],
                  'residual_rank8':sps['double_centered']['fraction']['8'],'rank90':sps['double_centered']['rank90'],
                  **metric,'checks':checks}),flush=True)
        results['datasets'][dataset]=dataset_results
    results['all_strong_predictions_met']=all(all(it['strong_prediction'].values())
        for ds in results['datasets'].values() for it in ds.values())
    results['analysis_wall_seconds']=time.perf_counter()-start
    dump(out/'input_manifest.json',manifest)
    dump(out/'analysis.json',results)
    print(json.dumps({'status':'COMPLETE','all_strong_predictions_met':results['all_strong_predictions_met'],
                      'analysis_wall_seconds':results['analysis_wall_seconds']}),flush=True)


if __name__=='__main__':
    main()
