import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='8'
os.sched_setaffinity(0,range(8))
import hashlib,importlib.util,json,shutil,time
from pathlib import Path
import numpy as np
from sklearn.tree import DecisionTreeRegressor
R=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('old_reconstruction',R.parent/'directional_error_v1/analyze.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
METHODS=['Uniform','LeaveOneOutTree','SelfIncludedTree','EnergyTree','ShuffledLeaveOneOutTree']
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def project(x,p,norm):return (x-np.sum(x*p,axis=1)[:,None]*p)/norm[:,None]
def unit(x):return x/np.linalg.norm(x,axis=1)[:,None]
def inner_rows(delta,q,tangent_sum,norm):return np.sum(delta*(q@(tangent_sum/norm[:,None]).T),axis=1)
def corr(a,b):
    ac=a-a.mean();bc=b-b.mean();den=np.linalg.norm(ac)*np.linalg.norm(bc)
    return float(ac@bc/den) if den>0 else None
def tree_record(tree,scale):
    t=tree.tree_
    return {'children_left':t.children_left.tolist(),'children_right':t.children_right.tolist(),
        'feature':t.feature.tolist(),'threshold':t.threshold.tolist(),'values':(t.value[:,0,0]*scale).tolist(),
        'samples':t.n_node_samples.tolist(),'scale':scale,'input_cast':'float32'}
def fit_pilot(n,pilot_delta,pilot_q,pilot_energy,profiles,norms,pilot_features,all_features,shuffle_seed):
    # The only exact supervision arguments are the 1024 pilot rows.
    m=len(pilot_q);f=2048/n;psum=project(pilot_delta.T@pilot_q,profiles,norms)
    inner=inner_rows(pilot_delta,pilot_q,psum,norms)
    loo=pilot_energy+2*(1-f)*(n-1)/(m-1)*(inner-pilot_energy)
    naive=2*(1-f)*n/m*inner-(1-2*f)*pilot_energy
    shuffle=np.random.default_rng(shuffle_seed).permutation(m)
    targets=np.stack([loo,naive,pilot_energy,loo[shuffle]])
    predictions=[];trees=[]
    for target in targets:
        scale=float(np.sqrt(np.mean(target*target)))
        if scale==0:scale=1.
        tree=DecisionTreeRegressor(max_depth=2,min_samples_leaf=128,random_state=2026093013)
        tree.fit(pilot_features,target/scale);predictions.append(tree.predict(all_features)*scale);trees.append(tree_record(tree,scale))
    return np.stack(predictions),targets,trees,shuffle
def main():
    for stage in ['fresh_transfer_v1','temperature_error_decomposition_v1']:
        assert json.loads((R.parent/stage/'reviews/independent_audit.json').read_text())['status']=='PASS'
    started=time.perf_counter();assert shutil.disk_usage(R).free>=6*(1<<30)
    for part in ['models','results','reviews']:(R/part).mkdir()
    paths=[Path(__file__),R/'protocol.md',R/'theory.md',R.parent/'directional_error_v1/analyze.py']
    for ds in old.CONFIG['datasets']:
        paths += [R.parent/'directional_error_v1/results'/f'{ds}.npz',R.parent/'cheap_residual_information_v1/models'/f'{ds}.npz',R.parent/'cheap_residual_information_v1/results'/f'{ds}.npz']
    frozen={str(p):ident(p) for p in paths};dump(R/'reviews/frozen.json',{'unix':time.time(),'files':frozen})
    records={};gate={}
    for di,ds in enumerate(old.CONFIG['datasets']):
        q,h,a,b=old.reconstruct(ds);n=len(q);delta=a-b
        prior=np.load(R.parent/'directional_error_v1/results'/f'{ds}.npz');truth=prior['v'];approx=prior['vp']
        np.testing.assert_allclose(h+b.T@q,approx,rtol=1e-13,atol=1e-12)
        norms=np.linalg.norm(approx,axis=1);profiles=approx/norms[:,None]
        features=np.load(R.parent/'cheap_residual_information_v1/models'/f'{ds}.npz')['features']
        energy=np.load(R.parent/'cheap_residual_information_v1/results'/f'{ds}.npz')['energy']
        predictions=[];targets=[];pilot_rows=[];selected=[];trees=[];shuffles=[]
        for rep in range(16):
            order=np.random.default_rng(2026093002+di+1000*rep).permutation(n);pilot=order[:1024];rest=order[1024:]
            pred,target,model,shuffle=fit_pilot(n,delta[pilot],q[pilot],energy[pilot],profiles,norms,features[pilot],features,2026093013+di+1000*rep)
            chosen=[order[:2048]]
            for values in pred:chosen.append(np.r_[pilot,rest[np.argsort(-values[rest],kind='stable')[:1024]]])
            predictions.append(pred);targets.append(target);pilot_rows.append(pilot);selected.append(chosen);trees.append(model);shuffles.append(shuffle)
        predictions=np.stack(predictions);targets=np.stack(targets);pilot_rows=np.stack(pilot_rows);selected=np.asarray(selected,dtype='i4')
        modelpath=R/'models'/f'{ds}.npz';jsonpath=R/'models'/f'{ds}.json'
        np.savez_compressed(modelpath,predictions=predictions,targets=targets,pilot_rows=pilot_rows,selected=selected,shuffles=np.stack(shuffles))
        dump(jsonpath,{'dataset':ds,'methods':METHODS,'trees':trees,'n':n,'pilot_n':1024,'total_exact_budget':2048,'replicates':16})
        dump(R/'reviews'/f'{ds}.prediction_frozen.json',{'unix':time.time(),'files':{str(p):ident(p) for p in [modelpath,jsonpath]},'accepted_labels_passed_to_fit':False})
        # Accepted truth is scored only after every predictor and selection is frozen.
        fullsum=project(delta.T@q,profiles,norms);truth_gain=2*(1-2048/n)*inner_rows(delta,q,fullsum,norms)-(1-2*2048/n)*energy
        truthdir=unit(truth);truthnorm=np.linalg.norm(truth,axis=1)
        chord=np.zeros((16,5));approx_risk=chord.copy();truth_risk=chord.copy();raw=chord.copy();radial=chord.copy();flips=np.zeros((16,5),dtype='i4');score=[]
        for rep in range(16):
            order=np.random.default_rng(2026093002+di+1000*rep).permutation(n);pilot=order[:1024];rest=order[1024:];parts=[rest,rest[:9488],rest[9488:]];sr={}
            for mi,name in enumerate(METHODS):
                rows=selected[rep,mi];assert len(np.unique(rows))==2048 and np.array_equal(rows[:1024],pilot)
                v=approx+delta[rows].T@q[rows];e=v-truth;chord[rep,mi]=np.sum((unit(v)-truthdir)**2)
                approx_risk[rep,mi]=np.sum(project(e,profiles,norms)**2);truth_risk[rep,mi]=np.sum(project(e,truthdir,truthnorm)**2);raw[rep,mi]=np.sum(e*e)
                rad=np.sum(v*truthdir,axis=1)/truthnorm;radial[rep,mi]=rad.min();flips[rep,mi]=np.sum(rad<=0)
                sr[name]={'added_true_gain_mean':float(truth_gain[rows[1024:]].mean())}
                if mi:
                    pred=predictions[rep,mi-1];target=targets[rep,mi-1]
                    sr[name].update(pilot_target_truth_correlation=corr(target,truth_gain[pilot]),
                        pilot_target_bias=float(np.mean(target-truth_gain[pilot])),pilot_target_MSE=float(np.mean((target-truth_gain[pilot])**2)),
                        accepted_prediction_truth_correlations=[corr(pred[p],truth_gain[p]) for p in parts],
                        accepted_prediction_truth_MSE=[float(np.mean((pred[p]-truth_gain[p])**2)) for p in parts])
            score.append(sr)
        out={}
        for mi,name in enumerate(METHODS):
            ratios=chord[:,mi]/chord[:,0]
            out[name]={'chord2_mean':float(chord[:,mi].mean()),'ratio_of_mean_chord2_to_Uniform':float(chord[:,mi].mean()/chord[:,0].mean()),
                'mean_paired_chord2_ratio':float(ratios.mean()),'paired_chord2_ratio_range':[float(ratios.min()),float(ratios.max())],
                'halves_ratio_of_mean_chord2_to_Uniform':[float(chord[s,mi].mean()/chord[s,0].mean()) for s in [slice(0,8),slice(8,16)]],
                'replicates_better_than_Uniform':int(np.sum(chord[:,mi]<chord[:,0])),'approx_tangent_risk_mean':float(approx_risk[:,mi].mean()),
                'truth_tangent_risk_mean':float(truth_risk[:,mi].mean()),'raw_risk_mean':float(raw[:,mi].mean()),'minimum_radial_ratio':float(radial[:,mi].min()),
                'nonpositive_radial_hub_replicates':int(flips[:,mi].sum()),'r0_chord2':float(chord[0,mi]),'r0_ratio_to_Uniform':float(ratios[0])}
        mainrec=out['LeaveOneOutTree'];checks={'mean_at_least_5percent_better':mainrec['ratio_of_mean_chord2_to_Uniform']<=.95,
            'both_halves_better':max(mainrec['halves_ratio_of_mean_chord2_to_Uniform'])<1,
            'better_than_energy':mainrec['chord2_mean']<out['EnergyTree']['chord2_mean'],
            'better_than_shuffled':mainrec['chord2_mean']<out['ShuffledLeaveOneOutTree']['chord2_mean']}
        gate[ds]={'checks':checks,'pass':all(checks.values())};records[ds]={'methods':out,'score_diagnostics':score,'truth_gain_quantiles':np.quantile(truth_gain,[0,.01,.5,.99,1]).tolist()}
        np.savez_compressed(R/'results'/f'{ds}.npz',chord=chord,approx_tangent=approx_risk,truth_tangent=truth_risk,raw=raw,radial=radial,flips=flips,truth_gain=truth_gain)
        for p,v in json.loads((R/'reviews'/f'{ds}.prediction_frozen.json').read_text())['files'].items():assert ident(p)==v
        print(ds,{name:out[name]['ratio_of_mean_chord2_to_Uniform'] for name in METHODS},flush=True)
    for p,v in frozen.items():assert ident(p)==v
    elapsed=time.perf_counter()-started;assert elapsed<180 and sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<=30*(1<<20)
    dump(R/'results/summary.json',{'status':'COMPUTED_PENDING_AUDIT','datasets':records,'gate':gate,'gate_pass':all(v['pass'] for v in gate.values()),'seconds':elapsed,
        'new_GT':0,'new_NSG':0,'new_ANN':0,'new_exported_profiles':0,'new_graphs':0,'new_performance':False,
        'RAM_hybrid_resultants':160,'small_trees':128,'exact_labels_consumed_per_simulated_builder':2048,'fixed_full_GT_temperature_control':True,'default_changed':False})
    print('ALL COMPUTED',elapsed,flush=True)
if __name__=='__main__':main()
