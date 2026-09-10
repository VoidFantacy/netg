#!/usr/bin/env python3
"""Read existing small results and configs; no vectors, GT, search or training."""
import hashlib
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = ROOT / 'entry_method_exploration/20260909_ab_experiment_v1'
identities = {}


def read(path):
    raw = path.read_bytes()
    identities[str(path.relative_to(ROOT))] = {
        'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()
    }
    return json.loads(raw)


result = {
    'date': '2026-09-10',
    'scope': 'static extraction of existing seed20260828 L128 model/results',
    'new_training_search_labels_or_evaluations': 0,
    'parameter_counts': [], 'models': [], 'historical_webvid_validation10k_L128': []
}
profile = read(OLD / 'exploration_5point_v1/reviews/frozen_model_profile.json')
for item in profile:
    dataset = item['dataset']
    seed = read(OLD / 'inputs' / dataset / 'seed20260828/config.json')
    runner = read(OLD / 'inputs' / dataset / 'runner_config.json')
    h, d = seed['hub_count'], runner['dim']
    result['parameter_counts'].append({
        'dataset': dataset, 'H': h, 'd': d, 'full_W_parameters': h*d,
        'rank8_factor_parameters': 8*(h+d), 'float32_W_bytes': h*d*4,
        'float32_W_MiB': h*d*4/2**20
    })
    families = {}
    for family in ('joint', 'w_only', 'mapping_only'):
        model = read(OLD / 'models' / dataset / 'seed20260828/L128' / family / 'selection.json')
        families[family] = {
            'best_including_fast': model['best_including_fast'],
            'best_new_candidate': model['best_new_candidate'],
            'initial': model['checkpoints'][0],
            'selected': model['selected']['metrics'],
            'candidate': model['candidate']['metrics']
        }
    result['models'].append({'dataset': dataset, 'frozen_profile': item, 'families': families})
old_result = read(OLD / 'single_thread_v1/results/validation/webvid2_5m_light_v1/seed20260828/results.json')
for row in old_result['methods']:
    if row['L'] != 128:
        continue
    family = row['configuration']['family']
    if family not in ('fast20k_1', 'fast30k_3', 'joint', 'w_only', 'mapping_only'):
        continue
    result['historical_webvid_validation10k_L128'].append({
        'name': row['name'], 'family': family, 'queries': row['queries'],
        'recall_at_10': row['recall_at_10'], 'mean_graph_ndc': row['mean_graph_ndc'],
        'mean_route_ndc': row['mean_route_ndc'], 'timings': row['timings'],
        'median_timings': {
            key: statistics.median(t[key] for t in row['timings'])
            for key in ('qps', 'end_to_end_seconds', 'graph_only_seconds', 'route_only_seconds')
        }
    })
result['source_identities'] = identities
(HERE / 'evidence.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
print(json.dumps({'models': len(result['models']),
                  'historical_rows': len(result['historical_webvid_validation10k_L128']),
                  'source_files': len(identities), 'new_experiments': 0}))
