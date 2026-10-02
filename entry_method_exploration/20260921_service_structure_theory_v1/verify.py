"""Separate Gram-matrix reconstruction and provenance audit of saved results."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
import hashlib
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=HERE/'results'
result=json.loads((OUT/'analysis.json').read_text())
manifest=json.loads((OUT/'input_manifest.json').read_text())
assert hashlib.sha256((HERE/'protocol.md').read_bytes()).hexdigest()==manifest['protocol_sha256']
assert hashlib.sha256((HERE/'analyze.py').read_bytes()).hexdigest()==manifest['script_sha256']
for item in manifest['sources']:
    p=ROOT/item['path']
    assert p.stat().st_size==item['bytes']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256']
checks=[]
for di,(dataset,ls) in enumerate(result['datasets'].items()):
    sub=OUT/dataset
    split=json.loads((sub/'split.json').read_text())
    tr,te=split['train_local_rows'],split['test_local_rows']
    ac,tc=split['anchor_local_hubs'],split['target_local_hubs']
    assert set(tr).isdisjoint(te) and set(tr+te)==set(range(512))
    assert set(ac).isdisjoint(tc) and set(ac+tc)==set(range(len(ac+tc)))
    for L,report in ls.items():
        arr=np.load(sub/f'L{L}_blocks.npz')
        src=ROOT/'fast_router_diagnosis/20260908_v1/results/run_v1/main'/dataset
        cfg=json.loads((src/'config.json').read_text())
        original=np.fromfile(src/f'L{L}/all_single.hitcount.u8',dtype='u1').reshape(cfg['num_queries'],cfg['hub_count'])[:512]/10.
        for key,rows,cols in [('a',tr,ac),('b',tr,tc),('c',te,ac),('d',te,tc)]:
            assert np.array_equal(arr[key],original[np.ix_(rows,cols)])
        a,b,c,d=[arr[k] for k in ['a','b','c','d']]
        aa=a-a.mean(1)[:,None]-a.mean(0)[None,:]+a.mean()
        bb=b-a.mean(1)[:,None]-b.mean(0)[None,:]+a.mean()
        cc=c-c.mean(1)[:,None]-a.mean(0)[None,:]+a.mean()
        lam,u=np.linalg.eigh(aa@aa.T)
        eig=lam[-8:];basis=u[:,-8:]
        # Gram eigenvectors give A_8^+ independently of the saved thin SVD.
        extra=cc@aa.T@basis@((basis.T@bb)/eig[:,None])
        baseline=c.mean(1)[:,None]+b.mean(0)[None,:]-a.mean()
        pred=baseline+extra
        max_error=float(abs(pred-arr['prediction']).max())
        assert max_error<1e-10
        ix=arr['choice']; bx=arr['baseline_choice'];rr=np.arange(256)
        assert np.array_equal(ix,arr['prediction'].argmax(1))
        assert np.all(bx==b.mean(0).argmax())
        delta=d[rr,ix]-d[rr,bx]
        assert abs(100*delta.mean()-report['block']['delta_pp'])<1e-10
        assert abs(1-np.mean((d-pred)**2)/np.mean((d-baseline)**2)-report['block']['mse_reduction'])<1e-10
        dc=original-original.mean(1)[:,None]-original.mean(0)[None,:]+original.mean()
        eigen=np.maximum(np.linalg.eigvalsh(dc@dc.T),0.)
        rank8=float(eigen[-8:].sum()/np.square(dc).sum())
        assert abs(rank8-report['spectra']['double_centered']['fraction']['8'])<1e-10
        rng=np.random.default_rng(20260922+di)
        estimates=[]
        for _ in range(8192):
            ids=rng.integers(0,256,size=256)
            estimates.append(100*np.bincount(ids,minlength=256)@delta/256)
        ci=np.quantile(estimates,[.00625,.99375])
        assert np.max(abs(ci-report['block']['delta_ci98_75_pp']))<1e-10
        checks.append({'dataset':dataset,'L':int(L),'max_prediction_error':max_error,
                       'split_source_metric_spectrum_bootstrap_pass':True})
audit={'status':'PASS','source_files_unchanged':len(manifest['sources']),
       'checks':checks,'auditor':'separate numerical implementation, same agent',
       'no_new_searches':True}
(OUT/'verification.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps(audit,indent=2))
