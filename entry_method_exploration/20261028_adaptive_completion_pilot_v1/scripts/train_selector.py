#!/usr/bin/env python3
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[key]='1'
import hashlib,json,sys,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def gt(d):
    n=d['n'];total=d.get('total_n',n);k=d.get('width',d.get('k',100));start=d.get('row_start',0)
    assert d['format'] in ['raw_i32','raw_i64']
    return np.memmap(d['path'],dtype='<i8' if d['format']=='raw_i64' else '<i4',mode='r',shape=(total,k))[start:start+n,:100]
def main():
    t=time.perf_counter();ds=sys.argv[1];c=json.loads((R/f'configs/{ds}.json').read_text());p=Path(c['backend']);n=16000
    assert not (p/'models.json').exists()
    f=np.fromfile(p/'features.f64','<f8').reshape(n,8,10)
    regions=np.fromfile(p/'training_regions.i32','<i4').reshape(n,8)
    id_region=np.fromfile(p/'id_region.i32','<i4');truth=gt(c['train_gt'])
    ids=np.fromfile(Path(c['teacher_dir'])/'raw/ids.i32','<i4').reshape(n,100)
    y=np.zeros((n,8),np.int32);missing=np.empty(n,np.int32)
    for i in range(n):
        absent=np.setdiff1d(truth[i],ids[i],assume_unique=True);missing[i]=len(absent)
        rr=id_region[absent]
        y[i]=(rr[:,None]==regions[i][None,:]).sum(axis=0)
    assert np.isfinite(f).all();y.astype('<i4').tofile(p/'training_labels.i32')
    models={};receipt={}
    for key,nf in [('REG-Q',5),('REG-R',10)]:
        x=f[:12000,:,:nf].reshape(-1,nf);z=y[:12000].ravel().astype(float)
        mu=x.mean(axis=0);scale=x.std(axis=0);scale[scale<1e-12]=1.;x=(x-mu)/scale
        intercept=z.mean();coef=np.linalg.solve(x.T@x+10*np.eye(nf),x.T@(z-intercept))
        m=dict(n_features=nf,mean=mu.tolist(),scale=scale.tolist(),coef=coef.tolist(),intercept=float(intercept))
        models[key]=m
        pred=np.maximum(0,((f[12000:,:,:nf]-mu)/scale)@coef+intercept)
        picks=np.argsort(-pred,axis=1,kind='stable')[:,:2]
        captured=np.take_along_axis(y[12000:],picks,axis=1).sum(axis=1)
        receipt[key]=dict(calibration_mse=float(np.mean((pred-y[12000:])**2)),
            selected_missing_GT_members=int(captured.sum()),
            selected_fraction_of_all_missing=float(captured.sum()/missing[12000:].sum()),
            selected_mean_coarse_rank=float(picks.mean()))
    dump(p/'models.json',models)
    receipt.update(status='PASS_E187_FIXED_RIDGE',fit_n=12000,calibration_n=4000,alpha=10,
        label='count of train GT100 omitted by fixed L200 teacher per coarse region',
        calibration_used_for_selection=False,test_or_test_GT_read=False,
        calibration_missing_GT_members=int(missing[12000:].sum()),
        top8_region_coverage=float(y[12000:].sum()/missing[12000:].sum()),
        REG_NN_selected_fraction=float(y[12000:,:2].sum()/missing[12000:].sum()),
        seconds=time.perf_counter()-t,threads=1)
    dump(p/'training.json',receipt);print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
