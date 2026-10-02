import numpy as np
from common import RUN,E25,DATASETS,LS,read,dump,identity
from effect_stats import effect_stats


def main():
    jobs=read(RUN/'reviews/search_jobs.json');assert len(jobs)==8 and all(j['status']=='COMPLETE' for j in jobs)
    analysis=read(RUN/'results/analysis.json')
    costs={'real_graph_calls':sum(j['actual_calls'] for j in jobs),'repair_calls':sum(j['reserved_calls'] for j in jobs if j['repair']),
        'synthetic_calls':2268,'search_process_wall_seconds':sum(j['process_seconds'] for j in jobs),
        'process_wall_boundary':'load/build/warm/count/verification/I/O included; not query QPS',
        'max_observed_RSS_bytes':max(j['max_observed_rss_bytes'] for j in jobs),
        'input_preparation_seconds':read(RUN/'inputs/preflight.json')['seconds'],
        'profile_construction':read(RUN/'models/construction_costs.json'),
        'new_fit_search_labels':0,'new_learned_parameters':0,'new_alpha_W_matrices':6,
        'phases':{},'datasets':{},'components_are_not_added_to_derive_QPS':True,
        'from_scratch_upstream_costs':{'exact_GT':None,'QGT':None,'NSG':None,'E24_profiles':None,'reason':'not rebuilt or newly timed'}}
    for stage in ['recovery','cal','audit','validation']:
        group=[j for j in jobs if j['name'].startswith(stage+'_')]
        costs['phases'][stage]={'calls':sum(j['actual_calls'] for j in group),'process_seconds':sum(j['process_seconds'] for j in group)}
    cross={}
    for ds in DATASETS:
        points=analysis['datasets'][ds]['measured_points'];folder=RUN/'results'/ds
        components={}
        for p in points:
            if p['L']==128:components[p['family']]={'route_us_per_query':p['route_only_seconds']*1e6/2000,
                'graph_us_per_query':p['graph_only_seconds']*1e6/2000,'total_median_us_per_query':1e6/p['qps'],
                'mean_route_ndc':p['mean_route_ndc'],'mean_graph_ndc':p['mean_graph_ndc'],
                'policy_build_seconds':p['policy_build_seconds'],'count_policy_load_seconds':p['count_policy_load_seconds']}
        costs['datasets'][ds]={'L128':components,'all_point_policy_build_seconds':sum(p['policy_build_seconds'] for p in points),
            'all_point_count_policy_load_seconds':sum(p['count_policy_load_seconds'] for p in points),
            'L128_micro_graph_files':[identity(p) for p in sorted(folder.glob('*_L128.hnsw'))],
            'deployment':'one selected W and one Micro-HNSW; no gate or second route'}
        h={name:np.column_stack([np.fromfile(folder/f'{name}_L{L}/hits.u8',dtype='u1') for L in LS]).astype('int16') for name in ['fast20k','e24','shrink']}
        entries={name:np.fromfile(folder/f'{name}_L64/entry_ids.i32',dtype='<i4').reshape(2000,3) for name in h}
        rows=np.fromfile(folder/'row_ids.i64',dtype='<i8');d1=h['e24']-h['fast20k'];da=h['shrink']-h['fast20k']
        p1=np.maximum(d1,0);pa=np.maximum(da,0);n1=np.maximum(-d1,0);na=np.maximum(-da,0)
        categories={'largest_original_gain_lost':(p1-np.minimum(p1,pa)).sum(axis=1),
            'largest_new_or_aggravated_loss':np.maximum(na-n1,0).sum(axis=1),
            'largest_original_loss_avoided':np.maximum(n1-na,0).sum(axis=1),
            'largest_net_gain_vs_A1':(da-d1).sum(axis=1)}
        cases={}
        for name,weight in categories.items():
            selected=sorted(np.flatnonzero(weight>0),key=lambda i:(-int(weight[i]),int(rows[i])))[:5]
            cases[name]=[{'row_id':int(rows[i]),'array_position':int(i),'selection_weight':int(weight[i]),
                'hits_by_L':{k:v[i].tolist() for k,v in h.items()},'entries':{k:v[i].tolist() for k,v in entries.items()}} for i in selected]
        dump(RUN/'results/mechanism'/ds/'illustrative_cases.json',{'L_order':LS,'cases':cases,
            'selection':'posthoc explanation only, no change to frozen alpha'})
        # The fixed raw query/graph/GT allow exact quality joins. Timings stay in their own independent runs.
        old=E25/'results'/ds
        for name in ['fast20k','e24']:
            previous=np.column_stack([np.fromfile(old/f'{name}_L{L}/hits.u8',dtype='u1') for L in LS]).astype('int16')
            assert np.array_equal(h[name],previous)
        rules={}
        for kind in ['base_gate','dual_gate']:
            previous=np.column_stack([np.fromfile(old/f'{kind}_L{L}/hits.u8',dtype='u1') for L in LS]).astype('int16')
            rules['E25_'+kind]={'pooled_L64_L128':effect_stats(h['fast20k'][:,:2],h['e24'][:,:2],previous[:,:2]),
                'five_L_descriptive':effect_stats(h['fast20k'],h['e24'],previous)}
        rules['E26_shrink']={'pooled_L64_L128':effect_stats(h['fast20k'][:,:2],h['e24'][:,:2],h['shrink'][:,:2]),
                'five_L_descriptive':effect_stats(h['fast20k'],h['e24'],h['shrink'])}
        cross[ds]=rules
    dump(RUN/'results/costs.json',costs)
    dump(RUN/'results/cross_experiment_quality_only.json',{'status':'PASS','datasets':cross,
        'same_original_query_GT_A0_A1_results_verified':True,'QPS_combined_across_runs':False,
        'no_new_model_selection_or_NSG_calls':True})
    print('E26_COSTS_CASES_AND_QUALITY_JOIN_COMPLETE',flush=True)


if __name__=='__main__':main()
