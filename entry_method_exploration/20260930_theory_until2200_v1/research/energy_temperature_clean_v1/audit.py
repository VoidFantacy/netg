import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='8'
os.sched_setaffinity(0,range(8))
import hashlib,json,time
from pathlib import Path
import numpy as np
from common import R,CONFIG,METHODS,ident,dump,unit,assignment,cheap_inputs
def manual_predict(tree,features):
    x=features.astype('f4');nodes=np.zeros(len(x),dtype='i4');left=np.asarray(tree['children_left']);right=np.asarray(tree['children_right'])
    feat=np.asarray(tree['feature']);cut=np.asarray(tree['threshold']);value=np.asarray(tree['values'])
    for _ in range(3):
        active=np.flatnonzero(left[nodes]>=0)
        if not len(active):break
        loc=nodes[active];nodes[active]=np.where(x[active,feat[loc]]<=cut[loc],left[loc],right[loc])
    assert (left[nodes]<0).all();return value[nodes],nodes
def main():
    start=time.perf_counter();summary=json.loads((R/'results/summary.json').read_text());prediction_checks=energy_checks=aggregate_checks=leaf_checks=0
    max_chord_difference=0.;identities=0;recovered=[]
    for di,ds in enumerate(CONFIG['datasets']):
        x=cheap_inputs(ds);q=x['q'];n=len(q);gt=np.memmap(x['config']['fit_source']['gt_file'],'<i8',mode='r',shape=(n,100))
        with np.load(R/'models'/f'{ds}.npz') as f:model={k:f[k] for k in f.files}
        meta=json.loads((R/'models'/f'{ds}.json').read_text());result=np.load(R/'results'/f'{ds}.npz');chord=result['chord']
        assert meta['feature_names']==['query_norm','mean_top10_distance_per_qnorm','gap10_11_per_qnorm','spread1_10_per_qnorm',
            'assignment_entropy','assignment_l2_squared','approx_tangent_leverage','weighted_inverse_resultant']
        np.testing.assert_array_equal(model['features'],x['features']);np.testing.assert_array_equal(model['proxy_gaps'],x['gaps'])
        assert hashlib.sha256(x['b'].tobytes()).hexdigest()==meta['approx_assignment_sha256']
        if x['temp'] is not None:
            z=np.sort(model['proxy_gaps']);assert (z[n//2-1]+z[n//2])/2==x['temp']==meta['temperature']
            assert x['temp']==.01631888747215271
        else:assert meta['temperature'] is None
        truth=np.fromfile(R.parent/'default_demand_full_build_v1/results'/ds/'v.f64','<f8').reshape(x['h'].shape)
        same=x['h'].astype('f8')+assignment(x['base'],np.asarray(gt),x['h'],x['temp']).T@q
        refs=[truth,same]
        for rep in range(16):
            order=np.random.default_rng(2026093002+di+1000*rep).permutation(n);pilot,rest=order[:1024],order[1024:]
            np.testing.assert_array_equal(pilot,model['pilot_rows'][rep]);np.testing.assert_array_equal(order[:2048],model['selected'][rep,0])
            shuffle=np.random.default_rng(2026093015+di+1000*rep).permutation(1024);np.testing.assert_array_equal(shuffle,model['shuffles'][rep])
            pilot_assignment=assignment(x['base'],np.asarray(gt[pilot]),x['h'],x['temp'])
            for local in [0,341,682,1023]:
                row=pilot[local];g=(pilot_assignment[local]-x['b'][row])[:,None]*(q[row]-np.outer(x['pp']@q[row],np.ones(q.shape[1]))*x['pp'])/x['norm'][:,None]
                np.testing.assert_allclose(np.sum(g*g),model['pilot_energy'][rep,local],rtol=1e-10,atol=1e-15);energy_checks+=1
            for mi in range(2):
                tree=meta['trees'][rep][mi];pred,nodes=manual_predict(tree,model['features']);prediction_checks+=n
                np.testing.assert_allclose(pred,model['predictions'][rep,mi],rtol=1e-14,atol=1e-15)
                chosen=np.r_[pilot,rest[np.argsort(-pred[rest],kind='stable')[:1024]]];np.testing.assert_array_equal(chosen,model['selected'][rep,mi+1])
                assert len(np.unique(chosen))==2048
                y=model['pilot_energy'][rep] if mi==0 else model['pilot_energy'][rep][shuffle]
                scale=float(np.sqrt(np.mean(y*y)));np.testing.assert_allclose(scale,tree['scale'],rtol=1e-14)
                for leaf in np.unique(nodes[pilot]):
                    values=y[nodes[pilot]==leaf];assert len(values)>=128 and len(values)==tree['samples'][leaf]
                    np.testing.assert_allclose(values.mean(),tree['values'][leaf],rtol=1e-12,atol=1e-15);leaf_checks+=1
            if rep in [0,7,8,15]:
                for mi in range(3):
                    rows=model['selected'][rep,mi];a=assignment(x['base'],np.asarray(gt[rows]),x['h'],x['temp'])
                    # Independent aggregation: original approximate vector plus selected corrections.
                    v=x['vp']+(a-x['b'][rows]).T@q[rows]
                    if rep==0 and mi==0:np.testing.assert_allclose(v,np.load(R/'results'/f'{ds}.r0_uniform_v.npy'),rtol=1e-12,atol=1e-12)
                    for ri,ref in enumerate(refs):
                        rp=ref/np.linalg.norm(ref,axis=1)[:,None];rn=np.linalg.norm(ref,axis=1);e=v-ref
                        measured=np.sum((v/np.linalg.norm(v,axis=1)[:,None]-rp)**2);max_chord_difference=max(max_chord_difference,abs(measured-chord[rep,mi,ri]))
                        projection=e-np.einsum('ij,ij->i',e,rp)[:,None]*rp
                        vals=[measured,np.sum(projection**2/rn[:,None]**2),np.sum(e*e)]
                        np.testing.assert_allclose(vals,[chord[rep,mi,ri],result['tangent'][rep,mi,ri],result['raw'][rep,mi,ri]],rtol=1e-10,atol=1e-10)
                        rad=np.einsum('ij,ij->i',v,rp)/rn;np.testing.assert_allclose(rad.min(),result['radial'][rep,mi,ri],rtol=1e-12)
                        assert np.sum(rad<=0)==result['flips'][rep,mi,ri]
                    aggregate_checks+=1
        for mi,name in enumerate(METHODS):
            rec=summary['datasets'][ds]['methods'][name];ratio=chord[:,mi]/chord[:,0]
            np.testing.assert_allclose(rec['mean_chord2'],chord[:,mi].mean(0),rtol=1e-14)
            np.testing.assert_allclose(rec['ratio_of_mean_chord2_to_Uniform'],chord[:,mi].mean(0)/chord[:,0].mean(0),rtol=1e-14)
            np.testing.assert_allclose(rec['halves_ratio_to_Uniform'],[chord[s,mi].mean(0)/chord[s,0].mean(0) for s in [slice(0,8),slice(8,16)]],rtol=1e-14)
            np.testing.assert_allclose(rec['r0_ratio_to_Uniform'],ratio[0],rtol=1e-14)
            assert rec['replicates_better_than_Uniform']==np.sum(chord[:,mi]<chord[:,0],axis=0).tolist()
        checks={'both_reference_means_at_least_5percent_better':bool(np.all(chord[:,1].mean(0)<=.95*chord[:,0].mean(0))),
            'default_reference_both_halves_better':bool(all(chord[s,1,0].mean()<chord[s,0,0].mean() for s in [slice(0,8),slice(8,16)])),
            'default_reference_better_than_shuffled':bool(chord[:,1,0].mean()<chord[:,2,0].mean())}
        assert checks==summary['gate'][ds]['checks'] and all(checks.values())==summary['gate'][ds]['pass']
        identity=summary['datasets'][ds]['identity'];v=np.load(R/'results'/f'{ds}.r0_uniform_v.npy');old=np.fromfile(identity['old_W'],'<f4').reshape(v.shape)
        assert np.array_equal(unit(v).astype('f4').view('u4'),old.view('u4'));assert identity['r0_uniform_bits_restored'];recovered.append(ds)
        for p,v in json.loads((R/'reviews'/f'{ds}.prediction_frozen.json').read_text())['files'].items():assert ident(p)==v;identities+=1
    frozen=json.loads((R/'reviews/frozen.json').read_text())
    for p,v in frozen['files'].items():assert ident(p)==v;identities+=1
    for p,v in frozen['large_base_stat_only'].items():st=Path(p).stat();assert {'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}==v
    assert summary['gate_pass']==all(g['pass'] for g in summary['gate'].values())
    elapsed=time.perf_counter()-start;assert elapsed<180 and prediction_checks==1280000 and energy_checks==128 and aggregate_checks==24
    dump(R/'reviews/independent_audit.json',{'status':'PASS','seconds':elapsed,'identities':identities,'source':ident(__file__),
        'manual_tree_predictions':prediction_checks,'explicit_residual_energy_checks':energy_checks,'leaf_target_mean_checks':leaf_checks,
        'independent_correction_aggregations':aggregate_checks,'maximum_chord2_difference':max_chord_difference,'r0_uniform_bit_recovery':recovered,
        'new_GT':0,'new_NSG':0,'new_ANN':0,'new_exported_profiles':0,'new_graphs':0,'default_changed':False})
    print('AUDIT PASS',elapsed,flush=True)
if __name__=='__main__':main()
