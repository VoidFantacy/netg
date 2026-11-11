from common import *
LS=[100,128,160,200,256,320,400,512,640,800,1000]
MAIN=['Q8-B32','AUX96','AUX384','CBRIDGE96','CBRIDGE384','SHARED96','SHARED384',
      'EARLY-MIX','EARLY-ALL','MODEL1','MODEL-GATE','MODEL-FULL','MODEL-GATE-FULL']
EXTRA=['REF-DIST384','REUSE-SQ','CBRIDGE384-FULL','SHARED384-FULL',
       'EARLY-MIX-FULL','EARLY-ALL-FULL','SHARED-FRONT3']
def points():
    rows=[]
    for K in [1,100]:
        for L in LS:
            for m in ['GT10','OPT-B32']:rows.append(dict(K=K,L=L,method=m))
        for L in [100,200,400]:
            for m in MAIN:rows.append(dict(K=K,L=L,method=m))
        for m in EXTRA:rows.append(dict(K=K,L=200,method=m))
    return rows
for ds in DS:
    c=read(R/'configs'/f'{ds}.labels.json')
    cal=dict(c,queries=dict(c['queries'],n=512,row_start=2048,total_n=3072),
             test_gt=dict(c['test_gt'],n=512,row_start=2048,total_n=3072),
             window='cal',output_dir=str(R/'storage/calibration'/ds),points=points())
    dump(R/'configs'/f'{ds}.calibration.json',cal)
    qualify=dict(cal,queries=dict(cal['queries'],n=16),test_gt=dict(cal['test_gt'],n=16),
                 window='qualification',output_dir=str(R/'storage/runtime_qualification'/ds))
    dump(R/'configs'/f'{ds}.runtime_qualification.json',qualify)
names=['C_rank_fraction','C_score','score_minus_Cbest','score_minus_main_best',
       'score_minus_main_worst','C_score_span','main_score_span','profile_best',
       'profile_gap','profile_span','query_norm_sq','main_seen','log_indegree',
       'log_outdegree','unseen_neighbor_slot_fraction','C_count_fraction','K_fraction',
       'L_fraction','in_route_row0','in_route_row1','in_route_row2','seed_norm_sq',
       'first4_valid_outslot_mean_norm_sq','is_C_rank0']
for prefix in ['q_projection','seed_projection','q_seed_product','out4_projection','q_out4_product']:
    names.extend(f'{prefix}_{j}' for j in range(16))
assert len(names)==104
dump(R/'feature_contract.json',dict(columns=names,cheap_prefix=24,strong_features=104,
     projection='fixed signed hash buckets from raw coordinates, seed19720261101; no task metric normalization',
     directed_graph_summary='first4 valid nonself out-slots, duplicate slots not silently deduplicated',
     graph_features_precomputed=True,GT_only_in_offline_labels=True,
     post_state='original R distances and visited; no future auxiliary trace',
     model_types=['standardized_ridge_alpha10','HGB128_leaf15_lr008_l2_10_no_early_stopping']))
print('PREPARED_MATRIX',len(points()),'points per dataset/stage')
