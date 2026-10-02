import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='8'
os.sched_setaffinity(0,range(8))
import hashlib,json,shutil,time
from pathlib import Path
import numpy as np
from sklearn.tree import DecisionTreeRegressor
from threadpoolctl import threadpool_info
from common import R,E125,CONFIG,METHODS,FEATURE_NAMES,ident,dump,unit,assignment,cheap_inputs,energy_on_rows,mixed_resultant,tree_record
def fit_pilot(pilot_features,pilot_energy,all_features,seed):
    # No full exact assignments, default temperature or reference vector are arguments.
    shuffle=np.random.default_rng(seed).permutation(len(pilot_energy));pred=[];trees=[]
    scale=float(np.sqrt(np.mean(pilot_energy**2))) or 1.
    for y in [pilot_energy,pilot_energy[shuffle]]:
        tree=DecisionTreeRegressor(max_depth=2,min_samples_leaf=128,random_state=2026093013)
        tree.fit(pilot_features,y/scale);pred.append(tree.predict(all_features)*scale);trees.append(tree_record(tree,scale))
    return np.stack(pred),trees,shuffle
def main():
    assert json.loads((R.parent/'default_demand_full_build_v1/reviews/independent_audit.json').read_text())['status']=='PASS'
    assert json.loads((R.parent/'replacement_alignment_v1/reviews/independent_audit.json').read_text())['status']=='PASS'
    start=time.perf_counter();assert shutil.disk_usage(R).free>=6*(1<<30)
    for part in ['models','results','reviews']:(R/part).mkdir()
    paths=[R/'protocol.md',R/'common.py',Path(__file__),R/'audit.py',E125/'config.locked.json'];base_stats={}
    for ds,dc in CONFIG['datasets'].items():
        c=dc['original'];paths += [Path(c['anchor']['ids']),Path(c['fit_source']['queries_file']),Path(c['fit_source']['gt_file']),
            E125/'results'/ds/'labels/ids.i32',E125/'results'/ds/'labels/distances.f32',
            R.parent/'default_demand_full_build_v1/results'/ds/'v.f64']
        st=Path(c['base']).stat();base_stats[c['base']]={'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}
    frozen={str(p):ident(p) for p in paths};dump(R/'reviews/frozen.json',{'unix':time.time(),'files':frozen,'large_base_stat_only':base_stats})
    records={};gates={}
    for di,ds in enumerate(CONFIG['datasets']):
        x=cheap_inputs(ds);n=len(x['q']);c=x['config'];gt=np.memmap(c['fit_source']['gt_file'],'<i8',mode='r',shape=(n,100))
        predictions=[];energies=[];pilots=[];selections=[];trees=[];shuffles=[]
        for rep in range(16):
            order=np.random.default_rng(2026093002+di+1000*rep).permutation(n);pilot,rest=order[:1024],order[1024:]
            energy=energy_on_rows(x,gt,pilot)
            pred,models,shuffle=fit_pilot(x['features'][pilot],energy,x['features'],2026093015+di+1000*rep)
            selected=[order[:2048]]+[np.r_[pilot,rest[np.argsort(-p[rest],kind='stable')[:1024]]] for p in pred]
            predictions.append(pred);energies.append(energy);pilots.append(pilot);selections.append(selected);trees.append(models);shuffles.append(shuffle)
        selections=np.asarray(selections,dtype='i4');modelpath=R/'models'/f'{ds}.npz';jsonpath=R/'models'/f'{ds}.json'
        np.savez_compressed(modelpath,predictions=np.stack(predictions),pilot_energy=np.stack(energies),pilot_rows=np.stack(pilots),
            selected=selections,shuffles=np.stack(shuffles),features=x['features'],proxy_gaps=x['gaps'])
        dump(jsonpath,{'dataset':ds,'methods':METHODS,'trees':trees,'n':n,'pilot_n':1024,'total_exact_budget':2048,
            'replicates':16,'temperature':x['temp'],'temperature_source':'all_approx_GT1_median' if x['temp'] is not None else 'hard',
            'feature_names':FEATURE_NAMES,'approx_assignment_sha256':hashlib.sha256(x['b'].tobytes()).hexdigest()})
        dump(R/'reviews'/f'{ds}.prediction_frozen.json',{'unix':time.time(),'files':{str(p):ident(p) for p in [modelpath,jsonpath]},
            'accepted_labels_passed_to_fit':False,'default_geometry_used_for_fit':False,'exact_temperature_used':False})
        # Every selector is now frozen. Full training truth and current default enter only here.
        truth=np.fromfile(R.parent/'default_demand_full_build_v1/results'/ds/'v.f64','<f8').reshape(x['h'].shape)
        same=x['h'].astype('f8')+assignment(x['base'],np.asarray(gt),x['h'],x['temp']).T@x['q']
        refs=[truth,same];dirs=[unit(v) for v in refs];norms=[np.linalg.norm(v,axis=1) for v in refs]
        chord=np.zeros((16,3,2));tangent=chord.copy();raw=chord.copy();radial=chord.copy();flips=np.zeros(chord.shape,dtype='i4');r0_hash=None
        for rep in range(16):
            for mi in range(3):
                rows=selections[rep,mi];assert len(np.unique(rows))==2048 and np.array_equal(rows[:1024],pilots[rep])
                v=mixed_resultant(x,gt,rows);p=unit(v)
                if rep==0 and mi==0:
                    np.save(R/'results'/f'{ds}.r0_uniform_v.npy',v);r0_hash=hashlib.sha256(p.astype('f4').tobytes()).hexdigest()
                for ri,(ref,rp,rn) in enumerate(zip(refs,dirs,norms)):
                    e=v-ref;projected=(e-np.sum(e*rp,axis=1)[:,None]*rp)/rn[:,None];r=np.sum(v*rp,axis=1)/rn
                    chord[rep,mi,ri]=np.sum((p-rp)**2);tangent[rep,mi,ri]=np.sum(projected**2);raw[rep,mi,ri]=np.sum(e*e)
                    radial[rep,mi,ri]=r.min();flips[rep,mi,ri]=np.sum(r<=0)
        out={}
        for mi,name in enumerate(METHODS):
            ratio=chord[:,mi]/chord[:,0]
            out[name]={'mean_chord2':chord[:,mi].mean(0).tolist(),'ratio_of_mean_chord2_to_Uniform':(chord[:,mi].mean(0)/chord[:,0].mean(0)).tolist(),
                'mean_paired_ratio':ratio.mean(0).tolist(),'ratio_range':[ratio.min(0).tolist(),ratio.max(0).tolist()],
                'halves_ratio_to_Uniform':[(chord[s,mi].mean(0)/chord[s,0].mean(0)).tolist() for s in [slice(0,8),slice(8,16)]],
                'replicates_better_than_Uniform':np.sum(chord[:,mi]<chord[:,0],axis=0).tolist(),'r0_chord2':chord[0,mi].tolist(),
                'r0_ratio_to_Uniform':ratio[0].tolist(),'minimum_radial_ratio':radial[:,mi].min(0).tolist(),
                'nonpositive_radial_hub_replicates':flips[:,mi].sum(0).tolist(),'mean_tangent_risk':tangent[:,mi].mean(0).tolist()}
        checks={'both_reference_means_at_least_5percent_better':bool(np.all(chord[:,1].mean(0)<=.95*chord[:,0].mean(0))),
            'default_reference_both_halves_better':bool(all(chord[s,1,0].mean()<chord[s,0,0].mean() for s in [slice(0,8),slice(8,16)])),
            'default_reference_better_than_shuffled':bool(chord[:,1,0].mean()<chord[:,2,0].mean())}
        if ds.startswith('webvid'):
            oldw=R.parent/'temperature_full_build_v1/results'/ds/'HybridApproxMedian/W.f32'
        else:oldw=R.parent/'hybrid_temperature_factorial_v1/models'/ds/'HybridFixedTemperature/W.f32'
        identity={'r0_uniform_W_sha256':r0_hash,'old_W':str(oldw),'old_W_sha256':ident(oldw)['sha256'],'r0_uniform_bits_restored':r0_hash==ident(oldw)['sha256']}
        if not ds.startswith('webvid'):
            previous=np.load(R.parent/'replacement_alignment_v1/models'/f'{ds}.npz')['selected'][:,3]
            identity['Energy_selection_equal_to_record153_by_rep']=[bool(np.array_equal(selections[j,1],previous[j])) for j in range(16)]
        gates[ds]={'checks':checks,'pass':all(checks.values())};records[ds]={'temperature':x['temp'],'methods':out,'identity':identity}
        np.savez_compressed(R/'results'/f'{ds}.npz',chord=chord,tangent=tangent,raw=raw,radial=radial,flips=flips)
        for p,v in json.loads((R/'reviews'/f'{ds}.prediction_frozen.json').read_text())['files'].items():assert ident(p)==v
        print(ds,{name:out[name]['ratio_of_mean_chord2_to_Uniform'] for name in METHODS},identity,flush=True)
        assert time.perf_counter()-start<180
    for p,v in frozen.items():assert ident(p)==v
    for p,v in base_stats.items():st=Path(p).stat();assert {'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}==v
    elapsed=time.perf_counter()-start;size=sum(p.stat().st_size for p in R.rglob('*') if p.is_file());assert elapsed<180 and size<=20*(1<<20)
    dump(R/'results/summary.json',{'status':'COMPUTED_PENDING_AUDIT','datasets':records,'gate':gates,'gate_pass':all(g['pass'] for g in gates.values()),
        'reference_order':['current_default','full_exact_at_proxy_temperature'],'seconds':elapsed,'new_GT':0,'new_NSG':0,'new_ANN':0,
        'RAM_hybrid_resultants':96,'small_trees':64,'new_exported_profiles':0,'new_graphs':0,'bytes_before_summary':size,
        'threadpools':threadpool_info(),'affinity':sorted(os.sched_getaffinity(0)),'default_changed':False})
    print('COMPUTED',elapsed,flush=True)
if __name__=='__main__':main()
