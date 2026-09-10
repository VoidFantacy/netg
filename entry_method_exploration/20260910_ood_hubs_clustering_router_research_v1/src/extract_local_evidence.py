#!/usr/bin/env python3
"""Read existing source/manifests/aggregate JSON only; never search or fit a model."""
import hashlib
import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]
consumed = {}


def read(rel):
    path = ROOT / rel
    data = path.read_bytes()
    consumed[rel] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    return json.loads(data)


old = read('fast_router_diagnosis/20260908_v1/analysis/v2/analysis.json')
e23 = read('entry_method_exploration/20260910_three_entry_rank_v1/results/summary.json')
behavior = read('entry_method_exploration/20260910_three_entry_rank_v1/reviews/model_behavior.json')
datasets = {}
for d in old['datasets']:
    name = d['dataset']
    fast = read(f'fast_entry_variants/{name}_seed20260828/manifest.json')
    paired = read(f'entry_method_exploration/20260909_ab_experiment_v1/inputs/{name}/seed20260828/config.json')
    b = next(x for x in behavior['datasets'] if x['dataset'] == name)
    selected_names = {'fast20k_3'} | {x['model_name'] for x in b['selected_models'].values()}
    diagnostics = {}
    for split in ['cal', 'audit']:
        diagnostics[split] = [
            {k: row[k] for k in ['name', 'family', 'L', 'queries', 'recall_at_10', 'mean_route_ndc', 'qps']}
            for row in e23['diagnostics'][name][split]
            if row['configuration']['model_name'] in selected_names
        ]
    datasets[name] = {
        'qgt': fast['variants']['qgt_cover'],
        'qgt_mean_queries_per_cluster_arithmetic_only': 5000 / fast['variants']['qgt_cover']['selected_hubs'],
        'prototype30k': fast['variants']['qgt_gt_basin_prototype'],
        'prototype20k': paired['prototype_details'],
        'e20_L128_single_entry_recall': {
            m: d['budgets']['128']['methods'][m]['recall_at_10']['mean']
            for m in ['fast_top1', 'exact_top1', 'gt1_basin', 'all_h_single_oracle']
        },
        'e20_hnsw_top1_exact_set_recall': d['router_diagnostics']['fast']['1']['exact_topk_set_recall']['mean'],
        'e20_nearest_query_gt10_overlap': d['budgets']['128']['neighbor_transfer']['density']['nearest_gt10_overlap'],
        'e23_selected_model_behavior': b['selected_models'],
        'e23_selected_diagnostics': diagnostics,
        'e23_existing_validation_metrics': [x for x in e23['metrics'] if x['dataset'] == name],
    }

result = {
    'status': 'EXISTING_AGGREGATES_EXTRACTED_NO_NEW_EXPERIMENT',
    'new_searches': 0, 'new_labels': 0, 'new_model_fits': 0,
    'raw_validation_or_heldout_opened': False,
    'notes': [
        'Validation numbers below are copied from an existing E23 aggregate, not recomputed.',
        'E20 is historical 512-query development diagnosis; oracle is free quality headroom, not deployment.',
        'E23 cal/audit have null QPS; routing NDC is not wall time.',
        'QGT arithmetic mean is not measured cluster-size distribution.',
    ],
    'datasets': datasets,
    'consumed_aggregate_files': consumed,
}
(RUN / 'local_evidence.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'datasets': len(datasets), 'existing_json_files': len(consumed), 'new_searches': 0}))
