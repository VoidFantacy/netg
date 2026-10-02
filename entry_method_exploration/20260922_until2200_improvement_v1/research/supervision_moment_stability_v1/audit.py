import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
import json,hashlib,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;E=R.parents[2];OLD=E/'20260921_comparison_direction_pilot_v1'
summary=json.loads((R/'summary.json').read_text());cfg=json.loads((OLD/'config.locked.json').read_text());started=time.perf_counter()
identities=json.loads((R/'inputs.json').read_text())
for path,v in identities['small_files'].items():
    p=Path(path);assert p.stat().st_size==v['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256']
checks=[]
for ds,dc in cfg['datasets'].items():
    q=np.fromfile(OLD/'inputs'/ds/'fit/queries.f32','<f4').reshape(4096,dc['dimension']);q=(q/np.sqrt(np.sum(q*q,axis=1))[:,None]).astype('f8')
    roles=dict(np.load(R/f'{ds}.roles.npz'));a,b=roles['A'],roles['B'];targets=dict(np.load(R/f'{ds}.derived_labels.npz'))
    for centered in [False,True]:
        key='centered_covariance' if centered else 'uncentered_moment';xa,xb=q[a].copy(),q[b].copy();den=len(a)-1 if centered else len(a)
        if centered:xa-=xa.mean(0);xb-=xb.mean(0)
        kaa=xa@xa.T;kbb=xb@xb.T;kab=xa@xb.T
        for name,y in targets.items():
            ya,yb=y[a].copy(),y[b].copy()
            ya-=ya.mean(1,keepdims=True);yb-=yb.mean(1,keepdims=True)
            if centered:ya-=ya.mean(0);yb-=yb.mean(0)
            aa=float(np.einsum('ij,ij->',kaa,ya@ya.T))/(den*den)
            bb=float(np.einsum('ij,ij->',kbb,yb@yb.T))/(den*den)
            ab=float(np.einsum('ij,ij->',kab,ya@yb.T))/(den*den)
            old=summary['datasets'][ds]['labels'][name][key]['actual']
            errors=[abs(aa-old['norm_A_squared']),abs(bb-old['norm_B_squared']),abs(ab-old['inner_product'])]
            assert max(errors)<1e-11*max(aa,bb,1e-10),(ds,name,key,errors)
            assert abs(2*ab/(aa+bb)-old['replicability'])<1e-10
            checks.append({'dataset':ds,'label':name,'view':key,'dual_gram_max_abs_error':max(errors)})
    print(ds,'dual Gram audit passed',flush=True)
path=R/'independent_audit.json';assert not path.exists();path.write_text(json.dumps({'status':'PASS','checks':checks,'protected_input_files':len(identities['small_files']),'seconds':time.perf_counter()-started,'scope':'Same agent independent dual-Gram computation, not an independent reviewer; no new model/search.'},indent=2)+'\n')
