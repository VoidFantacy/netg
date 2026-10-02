import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='8'
os.sched_setaffinity(0,range(8))
import hashlib,importlib.util,itertools,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('reconstruction_for_audit',R.parent/'directional_error_v1/analyze.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
METHODS=['Uniform','LeaveOneOutTree','SelfIncludedTree','EnergyTree','ShuffledLeaveOneOutTree']
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def mathematical_audit():
    g=np.array([[2,1,-1],[1,-2,0],[-2,0,1],[0,1,2],[1,0,-2],[-1,1,1]],dtype='f8');n=len(g);b=g.sum(0);e=np.sum(g*g,axis=1);f=2/n
    subsets=np.array(list(itertools.product([0,1],repeat=n)));pi=np.linspace(.15,.7,n);prob=np.prod(np.where(subsets,pi,1-pi),axis=1)
    measured=np.sum(prob*np.sum((subsets@g-b)**2,axis=1));formula=np.sum(((1-pi)@g)**2)+np.sum(pi*(1-pi)*e)
    np.testing.assert_allclose(measured,formula,rtol=1e-14)
    vv=2*(1-f)*(g@b)-(1-2*f)*e;derivative_checks=0
    def enumerated_risk(p):return np.sum(np.prod(np.where(subsets,p,1-p),axis=1)*np.sum((subsets@g-b)**2,axis=1))
    for i in range(n):
        p=np.full(n,f);step=np.zeros(n);step[i]=1e-5
        observed=(enumerated_risk(p+step)-enumerated_risk(p-step))/(2e-5)
        np.testing.assert_allclose(observed,-vv[i],rtol=1e-8,atol=1e-8);derivative_checks+=1
    fixed=np.array([z for z in subsets if z.sum()==2]);weights=np.arange(1,len(fixed)+1,dtype='f8');weights/=weights.sum()
    inclusion=weights@fixed;joint=(fixed.T*weights)@fixed
    value=b@b-2*np.sum(inclusion*(g@b))+np.sum(joint*(g@g.T))
    np.testing.assert_allclose(value,np.sum(weights*np.sum((fixed@g-b)**2,axis=1)),rtol=1e-14)
    conditional_cases=0
    for i in range(n):
        m=3;rest=np.array([j for j in range(n) if j!=i]);est=[];naive=[]
        for other in itertools.combinations(rest,m-1):
            ids=np.array([i,*other]);total=g[ids].sum(0)
            estimate=g[i]+(n-1)/(m-1)*(total-g[i]);est.append(2*(1-f)*(estimate@g[i])-(1-2*f)*e[i])
            naive.append(2*(1-f)*(n/m*total@g[i])-(1-2*f)*e[i]);conditional_cases+=1
        np.testing.assert_allclose(np.mean(est),vv[i],rtol=1e-14,atol=1e-14)
        variance=4*(1-f)**2*(n-1)**2*(1-(m-1)/(n-1))*np.var(g[rest]@g[i],ddof=1)/(m-1)
        np.testing.assert_allclose(np.var(est),variance,rtol=1e-14,atol=1e-13)
        naive_mean=2*(1-f)*(n/m)*(g[i]@g[i]+(m-1)/(n-1)*((b-g[i])@g[i]))-(1-2*f)*e[i]
        np.testing.assert_allclose(np.mean(naive),naive_mean,rtol=1e-14,atol=1e-14)
    return {'Bernoulli_subsets':len(subsets),'fixed_size_designs':1,'conditional_pilot_subsets':conditional_cases,'risk_derivatives':derivative_checks}
def manual_predict(tree,features):
    x=features.astype('f4');nodes=np.zeros(len(x),dtype='i4');left=np.asarray(tree['children_left']);right=np.asarray(tree['children_right']);feat=np.asarray(tree['feature']);cut=np.asarray(tree['threshold']);value=np.asarray(tree['values'])
    for depth in range(3):
        active=np.flatnonzero(left[nodes]>=0)
        if not len(active):break
        loc=nodes[active];nodes[active]=np.where(x[active,feat[loc]]<=cut[loc],left[loc],right[loc])
    assert (left[nodes]<0).all();return value[nodes]
def main():
    start=time.perf_counter();math=mathematical_audit();summary=json.loads((R/'results/summary.json').read_text())
    predictions_checked=score_checks=resultants=identity_count=0;max_chord_difference=0.
    for di,ds in enumerate(old.CONFIG['datasets']):
        q,h,a,b=old.reconstruct(ds);n=len(q);delta=a-b
        reference=np.load(R.parent/'directional_error_v1/results'/f'{ds}.npz');truth=reference['v'];approx=reference['vp'];norms=np.linalg.norm(approx,axis=1);pp=approx/norms[:,None];truthnorm=np.linalg.norm(truth,axis=1);tp=truth/truthnorm[:,None]
        features=np.load(R.parent/'cheap_residual_information_v1/models'/f'{ds}.npz')['features'];energy=np.load(R.parent/'cheap_residual_information_v1/results'/f'{ds}.npz')['energy']
        with np.load(R/'models'/f'{ds}.npz') as packed:models={key:packed[key] for key in packed.files}
        trees=json.loads((R/'models'/f'{ds}.json').read_text())['trees'];res=np.load(R/'results'/f'{ds}.npz');f=2048/n
        for rep in range(16):
            order=np.random.default_rng(2026093002+di+1000*rep).permutation(n);pilot,rest=order[:1024],order[1024:];assert np.array_equal(pilot,models['pilot_rows'][rep])
            assert np.array_equal(models['selected'][rep,0],order[:2048]);projection=q[pilot]@pp.T
            expected_shuffle=np.random.default_rng(2026093013+di+1000*rep).permutation(1024);assert np.array_equal(expected_shuffle,models['shuffles'][rep])
            np.testing.assert_array_equal(models['targets'][rep,3],models['targets'][rep,0][expected_shuffle]);np.testing.assert_array_equal(models['targets'][rep,2],energy[pilot])
            for offset in [0,341,682,1023]:
                i=pilot[offset];qi=q[i];weighted=delta[pilot]*delta[i][None,:]/norms[None,:]**2
                pair_inner=np.sum(weighted*((q[pilot]@qi)[:,None]-projection*(pp@qi)[None,:]),axis=1)
                np.testing.assert_allclose(pair_inner[offset],energy[i],rtol=1e-8,atol=1e-13)
                loo=energy[i]+2*(1-f)*(n-1)/1023*(pair_inner.sum()-pair_inner[offset])
                naive=2*(1-f)*n/1024*pair_inner.sum()-(1-2*f)*energy[i]
                np.testing.assert_allclose([loo,naive],models['targets'][rep,:2,offset],rtol=1e-8,atol=1e-12);score_checks+=1
            for mi in range(4):
                pred=manual_predict(trees[rep][mi],features);np.testing.assert_allclose(pred,models['predictions'][rep,mi],rtol=1e-14,atol=1e-15);predictions_checked+=n
                chosen=np.r_[pilot,rest[np.argsort(-pred[rest],kind='stable')[:1024]]]
                assert np.array_equal(chosen,models['selected'][rep,mi+1]) and len(np.unique(chosen))==2048
            if rep in [0,5,10,15]:
                for mi in range(5):
                    rows=models['selected'][rep,mi];mixed=b.copy();mixed[rows]=a[rows];v=h+mixed.T@q;err=v-truth;vn=np.linalg.norm(v,axis=1)
                    chord=float(np.sum((v/vn[:,None]-tp)**2));max_chord_difference=max(max_chord_difference,abs(chord-res['chord'][rep,mi]))
                    np.testing.assert_allclose(chord,res['chord'][rep,mi],rtol=1e-10,atol=1e-12)
                    approximate_projected=(err-np.sum(err*pp,axis=1)[:,None]*pp)/norms[:,None]
                    truth_projected=(err-np.sum(err*tp,axis=1)[:,None]*tp)/truthnorm[:,None]
                    np.testing.assert_allclose([np.sum(approximate_projected**2),np.sum(truth_projected**2),np.sum(err**2)],
                        [res['approx_tangent'][rep,mi],res['truth_tangent'][rep,mi],res['raw'][rep,mi]],rtol=1e-10,atol=1e-10)
                    radial=np.sum(v*tp,axis=1)/truthnorm;np.testing.assert_allclose(radial.min(),res['radial'][rep,mi],rtol=1e-12)
                    assert np.sum(radial<=0)==res['flips'][rep,mi];resultants+=1
        for mi,name in enumerate(METHODS):
            rec=summary['datasets'][ds]['methods'][name];chord=res['chord'];ratio=chord[:,mi]/chord[:,0]
            np.testing.assert_allclose(rec['chord2_mean'],chord[:,mi].mean(),rtol=1e-14)
            np.testing.assert_allclose(rec['ratio_of_mean_chord2_to_Uniform'],chord[:,mi].mean()/chord[:,0].mean(),rtol=1e-14)
            np.testing.assert_allclose(rec['mean_paired_chord2_ratio'],ratio.mean(),rtol=1e-14)
            assert rec['replicates_better_than_Uniform']==int(np.sum(chord[:,mi]<chord[:,0]))
        chord=res['chord'];checks={'mean_at_least_5percent_better':chord[:,1].mean()<=.95*chord[:,0].mean(),
            'both_halves_better':all(chord[s,1].mean()<chord[s,0].mean() for s in [slice(0,8),slice(8,16)]),
            'better_than_energy':chord[:,1].mean()<chord[:,3].mean(),'better_than_shuffled':chord[:,1].mean()<chord[:,4].mean()}
        assert checks==summary['gate'][ds]['checks'] and all(checks.values())==summary['gate'][ds]['pass']
        for p,v in json.loads((R/'reviews'/f'{ds}.prediction_frozen.json').read_text())['files'].items():assert ident(p)==v;identity_count+=1
    for p,v in json.loads((R/'reviews/frozen.json').read_text())['files'].items():assert ident(p)==v;identity_count+=1
    assert summary['gate_pass']==all(v['pass'] for v in summary['gate'].values())
    elapsed=time.perf_counter()-start;assert elapsed<180 and resultants==40 and predictions_checked==2560000
    out={'status':'PASS','seconds':elapsed,'source':ident(__file__),'identities':identity_count,'mathematical_checks':math,
        'scalar_tree_predictions':predictions_checked,'explicit_pilot_pair_inner_products':score_checks,
        'independent_mixed_assignment_resultants':resultants,'maximum_chord2_difference':max_chord_difference,
        'new_GT':0,'new_NSG':0,'new_ANN':0,'new_exported_profiles':0,'default_changed':False}
    with (R/'reviews/independent_audit.json').open('x') as fh:json.dump(out,fh,indent=2,allow_nan=False);fh.write('\n')
    print('AUDIT PASS',elapsed,flush=True)
if __name__=='__main__':main()
