import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='8'
os.sched_setaffinity(0,range(8))
import hashlib,json,sys,time
from pathlib import Path
import numpy as np
from sklearn.tree import DecisionTreeRegressor
from threadpoolctl import threadpool_info
from common import cheap_inputs,assignment,tree_record,FEATURE_NAMES,dump,ident
def main():
    start=time.perf_counter();c=json.loads(Path(sys.argv[1]).read_text());method='EnergyTree'
    assert c['method']=='EnergyTree';p=Path(c['output']);out=p/'selection';out.mkdir()
    x=cheap_inputs(c);order=np.random.default_rng(c['pilot_seed']).permutation(c['fit_n']);pilot,rest=order[:1024],order[1024:]
    assert np.array_equal(pilot,np.fromfile(p/'exact_rows.i32','<i4'))
    gt=np.fromfile(p/'pilot1024.ids.i64','<i8').reshape(1024,11)
    a=assignment(x['base'],gt,x['h'],x['temp']);energy=((a-x['b'][pilot])**2*x['tq'][pilot])@(1/x['norm']**2)
    scale=float(np.sqrt(np.mean(energy**2))) or 1.;shuffle=np.random.default_rng(c['shuffle_seed']).permutation(1024)
    y=energy if method=='EnergyTree' else energy[shuffle]
    tree=DecisionTreeRegressor(max_depth=2,min_samples_leaf=128,random_state=2026093013)
    tree.fit(x['features'][pilot],y/scale);prediction=tree.predict(x['features'])*scale
    added=rest[np.argsort(-prediction[rest],kind='stable')[:1024]].astype('<i4');selected=np.r_[pilot,added].astype('<i4')
    assert len(np.unique(selected))==2048 and np.isfinite(prediction).all()
    selected.tofile(out/'selected_rows.i32');added.tofile(out/'added_rows.i32')
    np.savez_compressed(out/'selection.npz',features=x['features'],pilot_energy=energy,predictions=prediction,shuffle=shuffle,proxy_gaps=x['gaps'])
    dump(out/'selection.json',{'method':method,'temperature':x['temp'],'tree':tree_record(tree,scale),'feature_names':FEATURE_NAMES,
        'approx_assignment_sha256':hashlib.sha256(x['b'].tobytes()).hexdigest(),'seconds':time.perf_counter()-start,
        'tree_count':1,'exact_fit_labels_read':1024,'approx_labels_read':20000,'affinity':sorted(os.sched_getaffinity(0)),
        'threadpools':threadpool_info(),'old_reference_inputs_read':False})
    dump(out/'selection_frozen.json',{'unix':time.time(),'files':{str(t):ident(t) for t in [out/'selection.json',out/'selection.npz',out/'selected_rows.i32',out/'added_rows.i32']}})
    print(c['dataset'],method,'SELECTED',time.perf_counter()-start,flush=True)
if __name__=='__main__':main()
