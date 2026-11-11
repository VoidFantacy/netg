#!/usr/bin/env python3
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
import json,time,sys
from pathlib import Path
import numpy as np
from scipy.optimize import nnls
R=Path(__file__).resolve().parents[1]
def main():
 ds=sys.argv[1];p=R/'models'/ds;assert not (p/'selector.json').exists();t=time.perf_counter()
 x=np.fromfile(p/'rescue_features.f64','<f8').reshape(-1,12);y=np.fromfile(p/'rescue_gain.i32','<i4').astype(float);ops=np.fromfile(p/'region_ops.f64','<f8').reshape(-1,5);wall=np.fromfile(p/'region_seconds.f64','<f8')
 assert len(y)==12000*8 and np.isfinite(x).all() and (wall>0).all();mean=x.mean(0);scale=x.std(0);scale[scale<1e-12]=1.;z=(x-mean)/scale;intercept=y.mean();coef=np.linalg.solve(z.T@z+10*np.eye(12),z.T@(y-intercept))
 # Nonnegative work/time model; normalize columns solely for numerical conditioning.
 s=np.maximum(ops.mean(0),1.);beta,res=nnls(ops/s,wall);beta=beta/s
 model=dict(gain=dict(n_features=12,mean=mean.tolist(),scale=scale.tolist(),coef=coef.tolist(),intercept=float(intercept)),cost_coef=beta.tolist())
 (p/'selector.json').write_text(json.dumps(model,indent=2)+'\n')
 rec=dict(status='PASS_E188_TRAINED_RESCUE_COST',dataset=ds,fit_queries=12000,rows=len(y),cal_or_test_used=False,alpha=10,mean_label=float(y.mean()),positive_label_fraction=float(np.mean(y>0)),cost_nnls_residual=float(res),cost_predictors=['intercept','blocks','blocks_log2_blocks','scanned_codes','exact_scores'],seconds=time.perf_counter()-t)
 (p/'training.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps(rec),flush=True)
if __name__=='__main__':main()
