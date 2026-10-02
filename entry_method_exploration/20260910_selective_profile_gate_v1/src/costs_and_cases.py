"""Measured cost boundaries, signal concentration and illustrative query records."""
import numpy as np
from common import RUN, DATASETS, LS, read, dump, identity
from gate_stats import load_pair
from verify_outputs import predict


def concentration(w):
    w=np.asarray(w,dtype=float);total=float(w.sum())
    return {'total':total,'nonzero_queries':int((w>0).sum()),
            'weight_ESS':total**2/float(w@w) if total else None,
            'maximum_query_weight':float(w.max()),
            'fraction_in_top_1_percent_all_queries':float(np.sort(w)[-max(1,int(np.ceil(.01*len(w)))):].sum()/total) if total else None}


def main():
    report=read(RUN/'results/analysis.json');jobs=read(RUN/'reviews/search_jobs.json')
    assert all(j['status']=='COMPLETE' for j in jobs)
    costs={'real_graph_calls':sum(j['actual_calls'] for j in jobs),
           'repair_calls':sum(j['reserved_calls'] for j in jobs if j['repair']),
           'search_process_wall_seconds':sum(j['process_seconds'] for j in jobs),
           'search_process_boundary':'includes loading, graph construction, warmup, count, checks and I/O; never converted to QPS',
           'max_observed_search_RSS_bytes':max(j['max_observed_rss_bytes'] for j in jobs),
           'actual_query_threads':[j['max_observed_process_threads'] for j in jobs],
           'input_prepare_seconds':read(RUN/'inputs/preflight.json')['seconds'],
           'phases':{},'datasets':{},
           'from_scratch_upstream_costs':{'exact_GT':None,'QGT':None,'NSG':None,'E24_W':None,
                                        'reason':'frozen upstream artifacts reused; this run did not measure their construction'},
           'component_walls_are_not_added_to_derive_QPS':True}
    for phase in ['recovery','fit','cal','audit','validation']:
        group=[j for j in jobs if j['name'].startswith(phase+'_')]
        costs['phases'][phase]={'calls':sum(j['actual_calls'] for j in group),
                                'process_seconds':sum(j['process_seconds'] for j in group)}
    for ds in DATASETS:
        _,x,h0,h1=load_pair(ds,'fit');d=h1-h0
        signal={'fit_positive_weights':concentration(np.maximum(d,0).sum(axis=1)),
                'fit_negative_weights':concentration(np.maximum(-d,0).sum(axis=1)),
                'fit_total_weights':concentration(np.abs(d).sum(axis=1)),
                'models':{}}
        model_seconds=0
        for kind in ['base_gate','dual_gate']:
            model=read(RUN/'models'/ds/f'{kind}.json')
            table=read(RUN/'models'/ds/f'{kind}_candidates.json')
            model_seconds+=sum(f['model_at_threshold_zero']['training_seconds'] for f in table['fits'])
            signal['models'][kind]={'candidate':model['candidate'],'lambda':model['lambda'],
                'bias':model['bias'],'threshold':model['threshold'],
                'ordered_standardized_coefficients':sorted([{'feature':n,'coefficient':b} for n,b in zip(model['features'],model['beta'])],key=lambda a:-abs(a['coefficient'])),
                'optimization_iterations':[len(f['optimization_trace'])-1 for f in table['fits']],
                'final_gradient_inf':[f['optimization_trace'][-1]['gradient_inf'] for f in table['fits']],
                'coefficient_directions_are_correlational_not_causal':True}
        dump(RUN/'results/mechanism'/ds/'signal_concentration.json',signal)
        points=report['datasets'][ds]['measured_points'];measured={}
        for p in points:
            if p['L']!=128:continue
            measured[p['kind']]={'route_only_us_per_query':p['route_only_seconds']*1e6/2000,
                'graph_only_us_per_query':p['graph_only_seconds']*1e6/2000,
                'end_to_end_median_us_per_query':1e6/p['qps'],
                'route_only_over_independent_total_ratio':p['route_only_seconds']/(2000/p['qps']),
                'mean_route_ndc':p['mean_route_ndc'],'mean_graph_ndc':p['mean_graph_ndc'],
                'mean_total_ndc':p['mean_total_ndc'],
                'policy_build_seconds':p['policy_build_seconds'],'count_policy_load_seconds':p['count_policy_load_seconds']}
        folder=RUN/'results'/ds
        graph_assets=[identity(p) for p in sorted(folder.glob('*_L128.*.hnsw'))]
        costs['datasets'][ds]={'six_weighted_logistic_fit_seconds':model_seconds,
             'fit_time_boundary':'per-model standardization and convex solve, excludes imports/selftest/cal candidate scoring/serialization',
             'L128':measured,'L128_graph_assets':graph_assets,
             'all_30_point_policy_build_seconds':sum(p['policy_build_seconds'] for p in points),
             'policy_graph_constructions_repeated_per_L_for_measurement':True,
             'single_deployment_base_or_dual_gate_requires_two_micrographs':True,
             'gate_model_json_bytes':{kind:(RUN/'models'/ds/f'{kind}.json').stat().st_size for kind in ['base_gate','dual_gate']}}
        # Cases are descriptive largest changes after freeze, never inputs to another rule.
        n=2000;v_x=np.fromfile(folder/'features.f64',dtype='<f8').reshape(n,13)
        rows=np.fromfile(folder/'row_ids.i64',dtype='<i8')
        h={kind:np.column_stack([np.fromfile(folder/f'{kind}_L{L}/hits.u8',dtype='u1') for L in LS]).astype('int16') for kind in ['fast20k','e24','base_gate','dual_gate']}
        entries={kind:np.fromfile(folder/f'{kind}_L64/entry_ids.i32',dtype='<i4').reshape(n,3) for kind in h}
        cases={}
        for kind in ['base_gate','dual_gate']:
            model=read(RUN/'models'/ds/f'{kind}.json');z,c=predict(v_x,model)
            vs_new=(h[kind]-h['e24']).sum(axis=1)
            primary_delta=h['e24']-h['fast20k']
            groups={'largest_recoveries_by_reverting':np.flatnonzero((~c)&(vs_new>0)),
                    'largest_benefits_lost_by_reverting':np.flatnonzero((~c)&(vs_new<0)),
                    'largest_remaining_harm':np.flatnonzero(c & (np.minimum(primary_delta,0).sum(axis=1)<0))}
            output={}
            for name,indices in groups.items():
                if name=='largest_recoveries_by_reverting':order=sorted(indices,key=lambda i:(-int(vs_new[i]),int(rows[i])))
                elif name=='largest_benefits_lost_by_reverting':order=sorted(indices,key=lambda i:(int(vs_new[i]),int(rows[i])))
                else:order=sorted(indices,key=lambda i:(int(np.minimum(primary_delta[i],0).sum()),int(rows[i])))
                output[name]=[{'row_id':int(rows[i]),'array_position':int(i),'choose_A1':bool(c[i]),'logit':float(z[i]),
                    'threshold':model['threshold'],'hits_in_L_order':{k:h[k][i].tolist() for k in h},
                    'entries':{k:entries[k][i].tolist() for k in entries},
                    'online_features':dict(zip(read(RUN/'config.locked.json')['feature_names'],v_x[i].tolist()))} for i in order[:5]]
            cases[kind]=output
        dump(RUN/'results/mechanism'/ds/'illustrative_validation_cases.json',{'L_order':LS,
             'selection':'posthoc largest positive/negative changes for explanation only; not used for fitting or threshold changes','cases':cases})
    dump(RUN/'results/costs.json',costs)
    print('COSTS_CONCENTRATION_AND_CASES_COMPLETE',flush=True)


if __name__=='__main__':main()
