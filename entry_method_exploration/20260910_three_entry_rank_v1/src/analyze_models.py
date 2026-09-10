#!/usr/bin/env python3
"""Static post-run model, label, and measured-route inspection; no new searches."""
import numpy as np
from common import DATASETS, RUN, dump, read

reports=[]
for ds in DATASETS:
    prep=read(RUN/'inputs'/ds/'prepared.json');h,d=prep['H'],prep['dim']
    p=np.fromfile(RUN/'inputs'/ds/'P0.f32',dtype='<f4').reshape(h,d)
    selected=read(RUN/'models'/ds/'selection.json')['selected_new_candidates']
    profiles={}
    for family in ['full','rank8']:
        model=selected[family];w=np.fromfile(model['W'],dtype='<f4').reshape(h,d)
        training=read(model['training_report'])
        delta=w.astype('float64')-p.astype('float64')
        singular=np.linalg.svd(delta,compute_uv=False)
        entry_file=RUN/'results'/ds/f'{family}_L128/entry_ids.i32'
        entries=np.fromfile(entry_file,dtype='<i4').reshape(2000,3)
        fast=np.fromfile(RUN/'results'/ds/'fast20k_3_L128/entry_ids.i32',dtype='<i4').reshape(2000,3)
        changed=(entries!=fast).any(axis=1)
        row_norm=np.linalg.norm(delta,axis=1)
        profiles[family]={'model_name':model['name'],'lambda':model['lambda'],
            'training_objective':training['objective'],'training_data_loss':training['data_loss'],
            'residual_Fro_norm':float(np.linalg.norm(delta)),'relative_residual_Fro_norm':float(np.linalg.norm(delta)/np.linalg.norm(p)),
            'row_residual_median':float(np.median(row_norm)),'row_residual_max':float(row_norm.max()),
            'residual_top8_singular_energy_fraction':float((singular[:8]**2).sum()/max((singular**2).sum(),1e-30)),
            'validation_queries_with_changed_triple':int(changed.sum()),'validation_queries':2000,
            'validation_unique_selected_real_entries':int(np.unique(entries).size),
            'full_objective_optimality_gap_upper_bound':training['full_objective_optimality_gap_upper_bound']}
    # Count preference reversals for exactly the same q,a,b when both pairs occur in distinct contexts.
    options=np.fromfile(RUN/'inputs'/ds/'fit/options.i32',dtype='<i4').reshape(20000,4,6)
    hits=np.fromfile(RUN/'labels'/ds/'hits.u8',dtype='u1').reshape(20000,4,6).astype('int16')
    repeated=0;conflicts=0;conflict_queries=0;covered_queries=0
    for i in range(20000):
        seen={}
        for c in range(4):
            for a in range(6):
                for b in range(a+1,6):
                    difference=int(hits[i,c,a]-hits[i,c,b])
                    if difference==0:continue
                    ea,eb=int(options[i,c,a]),int(options[i,c,b]);sign=1 if difference>0 else -1
                    if ea>eb:ea,eb=eb,ea;sign=-sign
                    seen.setdefault((ea,eb),[]).append(sign)
        shared=[signs for signs in seen.values() if len(signs)>1]
        bad=sum(min(signs)<0<max(signs) for signs in shared)
        repeated+=len(shared);conflicts+=bad;conflict_queries+=bad>0;covered_queries+=bool(shared)
    reports.append({'dataset':ds,'selected_models':profiles,'context_preference_reversals':{
        'fit_queries':20000,'queries_with_repeated_nonzero_pair':covered_queries,
        'repeated_nonzero_query_action_pairs':repeated,'conflicting_query_action_pairs':conflicts,
        'queries_with_any_conflict':conflict_queries,
        'scope':'only repeated nonzero pairs among these sampled four contexts; not full-H global prevalence'}})
dump(RUN/'reviews/model_behavior.json',{'status':'STATIC_ANALYSIS_COMPLETE','new_searches':0,'datasets':reports})
print('MODEL_BEHAVIOR_ANALYZED',flush=True)
