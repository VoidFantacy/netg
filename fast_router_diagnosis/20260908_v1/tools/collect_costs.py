#!/usr/bin/env python3
"""Collect existing diagnostic costs; no new search or model computation."""
import argparse
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    v = args.version.resolve()
    jobs = read(v / 'results/run_v1/jobs.json')
    result = {
        'status': 'RECORDED_DIAGNOSTIC_COSTS',
        'timing_contract': 'Observed instrumented diagnostic wall time; never deployable QPS or full training time.',
        'preparation_runs': {}, 'datasets': {},
        'search_process_wall_seconds': sum(x['wall_seconds'] for x in jobs),
        'graph_search_calls': sum(x['graph_search_calls'] for x in jobs),
        'peak_search_rss_bytes': max(x['peak_rss_bytes'] for x in jobs),
        'historical_exact_gt_seconds': None,
        'historical_exact_gt_reason': 'Existing training-side GT reused; original generation timing not established here.',
        'historical_qgt_hub_build_seconds': None,
        'historical_qgt_hub_build_reason': 'Existing QGT5K artifacts reused, not rebuilt or timed here.',
        'historical_nsg_build_seconds': None,
        'historical_nsg_build_reason': 'Frozen existing NSG reused; original build timing not established here.',
        'cold_cache_control': False,
        'cache_note': 'Input hashing and preparation read files before searches; this is not a cold-cache benchmark.',
    }
    for prep in sorted((v / 'inputs').glob('prepared_v*')):
        result['preparation_runs'][prep.name] = {}
        for ds in sorted(p for p in prep.iterdir() if p.is_dir()):
            if not (ds / 'completion.json').is_file():
                continue
            ids = read(ds / 'verified_identities.json')
            result['preparation_runs'][prep.name][ds.name] = {
                'total_seconds_including_hash_reproduction_selection_io': read(ds / 'completion.json')['seconds'],
                'file_identity_hash_seconds_sum': sum(x.get('seconds', 0) for x in ids.values()),
                'prototype_reproduction_seconds': read(ds / 'prototype_reconstruction.json')['seconds'],
                'purpose': 'Input verification only; prepared_v2 is the search input, prepared_v1 retained.',
            }
    for ds in ('webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1'):
        output = v / 'results/run_v1/main' / ds
        route_event = next(json.loads(line) for line in (v / 'logs' / f'{ds}_main_v1.log').read_text().splitlines()
                           if line.startswith('{') and json.loads(line).get('stage') == 'route')
        result['datasets'][ds] = {
            'jobs': [x for x in jobs if x['dataset'] == ds],
            'main_elapsed_at_routing_start_seconds': route_event['elapsed_instrumented_seconds'],
            'main_elapsed_at_routing_start_includes': 'Index and input loading before both HNSW construction and routing; stage=route is a start marker.',
            'hnsw_build_and_route_joint_seconds': None,
            'hnsw_build_separate_seconds': None,
            'route_only_separate_seconds': None,
            'separate_timer_missing_reason': 'Runner has no direct end timer for HNSW construction/routing, jointly or separately; cannot infer pure costs after the fact.',
            'budgets': {str(L): read(output / f'L{L}/complete.json') for L in (64, 128)},
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')
    print(args.output)


if __name__ == '__main__':
    main()
