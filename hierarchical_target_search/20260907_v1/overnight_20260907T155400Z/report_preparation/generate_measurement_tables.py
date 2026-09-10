#!/usr/bin/env python3
"""Render frozen completed analysis metadata only; no raw measurements/data reads."""
from __future__ import annotations

import argparse
import copy
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys

RUN = Path(__file__).resolve().parents[1]
SOURCES = {
    'P2': ('p2/analysis_v1/analysis.json', 'e73a8d8c16a5bebb2404596b63d621b1780b1aab0f9eb29efce5281edfc04c1f'),
    'P3': ('p3/analysis_v1/analysis.json', '63da6a71425b0dbd6e186db1c608a564b9847c58168b6b56059a9ed2d2f901ae'),
    'P3_structure': ('p3/structure_analysis_v1/analysis.json', '8b0cec717a14382c5917504e560bcffd732146c517ea9a699b0bb1812463088e'),
}
FRONTIER = ('mean_expanded', 'mean_rejected', 'mean_evicted_unexpanded')
DATASETS = ('webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pointer(parts):
    return '/'+ '/'.join(str(p).replace('~','~0').replace('/','~1') for p in parts)


def cell(value):
    if value is None:
        return 'null'
    if isinstance(value, (dict, list, bool)):
        return json.dumps(value, separators=(',', ':'), allow_nan=False)
    return str(value)


def md_cell(value):
    return cell(value).replace('|','\\|').replace('\n','<br>')


def table(headers, rows):
    return '\n'.join(['| '+' | '.join(headers)+' |', '| '+' | '.join('---' for _ in headers)+' |']+
                     ['| '+' | '.join(md_cell(v) for v in row)+' |' for row in rows])+'\n'


def write_json(path, obj):
    with path.open('x') as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write('\n')


def write_csv(path, rows, preferred):
    keys = preferred + sorted(set(k for row in rows for k in row)-set(preferred))
    with path.open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: cell(row.get(key)) for key in keys})


def flatten(obj, parts=()):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from flatten(value, parts+(key,))
    elif isinstance(obj, list):
        if not obj:
            yield parts, []
        for idx, value in enumerate(obj):
            yield from flatten(value, parts+(idx,))
    else:
        yield parts, obj


def read_sources():
    loaded, bindings = {}, {}
    for name, (relative, expected_hash) in SOURCES.items():
        path = RUN/relative
        actual_hash = sha(path)
        require(actual_hash == expected_hash, 'Bound completed analysis changed: '+relative)
        obj = json.loads(path.read_text())
        require(obj['status'] == 'COMPLETE', 'Source analysis is not complete: '+relative)
        require([x['dataset'] for x in obj['datasets']] == list(DATASETS), 'Dataset order/coverage differs')
        loaded[name] = obj
        bindings[name] = {'path': str(path), 'sha256': actual_hash, 'status': obj['status']}
    return loaded, bindings


def build(loaded, bindings):
    measurements, comparisons, costs, structures, source_flags = [], [], [], [], {}
    reconciliation = {'measurement_rows': {}, 'fixed_comparison_rows': {}, 'numeric_means_or_CIs_recomputed': False,
                      'source_measurement_fields_preserved_except_documented_Fast_sentinels': True,
                      'all_fixed_comparison_source_objects_preserved': True}
    for stage in ('P2', 'P3'):
        obj = loaded[stage]
        source_flags[stage] = {k: copy.deepcopy(v) for k,v in obj.items() if k != 'datasets'}
        for di, ds in enumerate(obj['datasets']):
            key = stage+'/'+ds['dataset']
            expected_measurements = 12 if stage == 'P2' else 24
            expected_comparisons = 14 if stage == 'P2' else 16
            require(len(ds['measurements']) == expected_measurements and len(ds['fixed_comparisons']) == expected_comparisons,
                    'Missing source measurement/comparison cells: '+key)
            for ri, raw in enumerate(ds['measurements']):
                row = copy.deepcopy(raw)
                require(len(row['qps_rounds']) == len(row['batch_wall_us_rounds']) == 5 and row['num_queries'] == 10000,
                        'Expected five rounds and 10K pilot queries')
                overridden = []
                for field in FRONTIER:
                    if row['method'] == 'fast':
                        if field in row:
                            require(row[field] == 0, 'Fast frontier field unexpectedly differs from documented zero sentinel')
                            overridden.append(field)
                        row[field] = None
                    elif field not in row:
                        row[field] = None
                for field, value in raw.items():
                    if field not in overridden:
                        require(row[field] == value, 'Source measurement numeric/string field changed')
                row.update({'stage': stage, 'source': bindings[stage],
                            'source_json_pointer': pointer(('datasets', di, 'measurements', ri)),
                            'qps_display_convention': 'qps_mean_of_five copied directly; arithmetic mean of the five saved round QPS values',
                            'qps_display_value': row['qps_mean_of_five'],
                            'frontier_counter_status': ('UNMEASURED_FAST_ZERO_SENTINEL_REPLACED_WITH_NULL' if row['method'] == 'fast' else
                                                        'MEASURED_ORACLE_COUNTERS' if stage == 'P3' else 'NOT_REPORTED_IN_BOUND_P2_ANALYSIS'),
                            'source_Fast_sentinel_fields_overridden': overridden,
                            'oracle_deployment_allowed': False if row['oracle_diagnostic_only'] else None,
                            'heldout_or_validation_result': False,
                            'P3_cross_model_wall_inference': 'DESCRIPTIVE_ONLY_FIXED_MODEL_ORDER' if stage == 'P3' else None,
                            'instrumented_time_is_plain_latency': False,
                            'standalone_routing_only_is_per_query_latency': False})
                measurements.append(row)
            for ri, raw in enumerate(ds['fixed_comparisons']):
                row = copy.deepcopy(raw)
                require(len(row['paired_query_bootstrap95_pp']) == 2, 'Missing saved comparison CI')
                qps = row['qps_pairing'] if stage == 'P2' else row['QPS_comparison']
                require(qps['ratio_CI'] is None, 'Unexpected QPS CI in frozen metadata')
                row.update({'stage': stage, 'source': bindings[stage],
                            'source_json_pointer': pointer(('datasets',di,'fixed_comparisons',ri)),
                            'CI_values_copied_without_recompute': True,
                            'CI_multiple_comparison_adjusted': False,
                            'timing_ratio_display_convention': 'ratio_of_mean_qps copied directly from source comparison',
                            'timing_ratio_display_value': qps['ratio_of_mean_qps'],
                            'comparison_direction': 'candidate minus reference for Recall/NDC; candidate divided by reference for QPS',
                            'P3_cross_model_wall_descriptive_only': stage == 'P3' and row['family'] == 'cross_model_2x2',
                            'oracle_deployment_allowed': False if row.get('oracle_involved', row.get('oracle_diagnostic_only')) else None})
                if stage == 'P3' and row['family'] == 'cross_model_2x2':
                    require(qps['cross_model_paired_inference_allowed'] is False and qps['paired_round_ratios'] is None,
                            'Cross-model wall cannot be treated as paired inference')
                for field, value in raw.items():
                    require(row[field] == value, 'Source comparison mean/CI/flag changed')
                comparisons.append(row)
            reconciliation['measurement_rows'][key] = expected_measurements
            reconciliation['fixed_comparison_rows'][key] = expected_comparisons
            costs.append({'stage': stage, 'dataset': ds['dataset'], 'source': bindings[stage],
                          'source_json_pointer': pointer(('datasets',di,'cost')), 'cost': copy.deepcopy(ds['cost']),
                          'cost_caution': ds.get('cost_caution'),
                          'reused_exact_GT_seconds': None,
                          'reused_exact_GT_reason': 'Existing compatible exact GT reused; historical compute time unavailable, not zero.',
                          'complete_training_cost_computed': False})
            source_flags[key] = {k: copy.deepcopy(v) for k,v in ds.items()
                                 if k not in ('dataset','evidence','measurements','fixed_comparisons','bootstrap_draws','cost','model_region_sizes')}
    structure = loaded['P3_structure']
    source_flags['P3_structure'] = {k: copy.deepcopy(v) for k,v in structure.items() if k != 'datasets'}
    for di, ds in enumerate(structure['datasets']):
        structures.append({'dataset': ds['dataset'], 'source': bindings['P3_structure'],
                           'source_json_pointer': pointer(('datasets',di)),
                           **{k: copy.deepcopy(ds[k]) for k in ('status','nodes','common_initial_labels_sha256','initial','branches',
                              'lambda1_minus_lambda0_final','objective_full_graph_GT_recomputation_by_this_analyzer',
                              'objective_recomputation_evidence','P3_gate_passed','search_gate_evaluated')}})
        costs.append({'stage':'P3_structure', 'dataset':ds['dataset'], 'source':bindings['P3_structure'],
                      'source_json_pointer':pointer(('datasets',di,'cost')), 'cost':copy.deepcopy(ds['cost']),
                      'reused_exact_GT_seconds':None, 'reused_exact_GT_reason':'Unknown reused exact GT time, not zero.',
                      'complete_training_cost_computed':False})
    require(len(measurements)==72 and len(comparisons)==60 and len(costs)==6 and len(structures)==2,
            'Final table coverage differs')
    return measurements, comparisons, costs, structures, source_flags, reconciliation


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output-prefix', required=True, help='New filename prefix, e.g. report_preparation/measurement_tables_v1')
    args = ap.parse_args()
    prefix = Path(args.output_prefix).resolve()
    prefix.parent.mkdir(parents=True, exist_ok=True)
    paths = {name: Path(str(prefix)+suffix) for name,suffix in
             (('json','.json'),('markdown','.md'),('measurements_csv','.csv'),('comparisons_csv','_comparisons.csv'),
              ('costs_csv','_costs.csv'),('structure_csv','_structure.csv'),('complete','_complete.json'))}
    require(all(not path.exists() for path in paths.values()), 'Refusing to overwrite any existing report artifact')
    loaded, bindings = read_sources()
    measurements, comparisons, costs, structures, source_flags, reconciliation = build(loaded,bindings)
    result = {'schema_version':1, 'status':'COMPLETE', 'scope':'Report preparation from three frozen completed metadata analyses only',
              'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(), 'generator':{'path':str(Path(__file__).resolve()),'sha256':sha(__file__)},
              'command':sys.argv, 'source_bindings':bindings, 'measurement_rows':measurements, 'fixed_comparison_rows':comparisons,
              'cost_records':costs, 'structure_records':structures, 'source_flags':source_flags, 'reconciliation':reconciliation,
              'semantics':{'QPS':'Use stored qps_mean_of_five, without recomputing. Median, pooled and five round values remain separate.',
                           'Recall':'Stored fraction unchanged; paired deltas and CIs are stored percentage points unchanged.',
                           'CI':'All saved pointwise ordinary 95% bootstrap intervals are exploratory and unadjusted; no new interval is computed.',
                           'Fast_frontier_counters':'Unmeasured zero sentinels replaced with null. Other missing P2 frontier counters are not reported by this source.',
                           'oracle':'Oracle methods use GT and are diagnostic; no deployment/performance improvement claim follows.',
                           'P3_cross_model_wall':'Fixed model order makes cross-model wall/QPS descriptive only, without paired timing inference.',
                           'instrumented_time':'Instrumented routing/graph time is not pure wall latency. A routing-only batch is not per-query latency.',
                           'reused_GT':'Historical exact-GT cost is null/unknown, never zero; no complete training-time sum is invented.',
                           'shared_cost':'P3 frequency/greedy model cost pointers share one probe run per lambda; never sum duplicates.',
                           'nested_bootstrap_status':'Copied source bootstrap metadata can contain initial INCOMPLETE invocation status despite completed top-level analysis; preserve it, do not reinterpret completion.',
                           'source_flags':'P2/P3 stage/gate fields here are copied analysis-scope flags; this table generator does not read or change current gate files.'},
              'access':{'read_files':list(bindings.values()),'rawdata':False,'count_rows':False,'GT':False,'labels':False,
                        'query_vectors':False,'base_vectors':False,'graph':False,'heldout':False,'validation':False},
              'experiment_run':False, 'new_statistics_or_scientific_gate':False}
    write_json(paths['json'],result)
    write_csv(paths['measurements_csv'],measurements,['stage','dataset','model','method','L','recall','qps_mean_of_five',
                                                    'mean_total_ndc','mean_expanded','mean_rejected','mean_evicted_unexpanded'])
    write_csv(paths['comparisons_csv'],comparisons,['stage','dataset','L','contrast','candidate_model','candidate_method','candidate',
                                                  'reference_model','reference_method','reference','recall_delta_pp','paired_query_bootstrap95_pp',
                                                  'timing_ratio_display_value','mean_total_ndc_delta'])
    cost_cells = []
    for record in costs:
        for parts,value in flatten(record['cost']):
            cost_cells.append({'stage':record['stage'],'dataset':record['dataset'],'cost_field':pointer(parts),'value':value,
                               'source_path':record['source']['path'],'source_sha256':record['source']['sha256'],
                               'source_json_pointer':record['source_json_pointer']+pointer(parts),
                               'complete_training_cost_computed':False})
    write_csv(paths['costs_csv'],cost_cells,['stage','dataset','cost_field','value','source_sha256','source_json_pointer'])
    structure_cells = []
    for record in structures:
        for key in ('initial','branches','lambda1_minus_lambda0_final'):
            for parts,value in flatten(record[key],(key,)):
                structure_cells.append({'dataset':record['dataset'],'field':pointer(parts),'value':value,
                                        'source_sha256':record['source']['sha256'],
                                        'source_json_pointer':record['source_json_pointer']+pointer(parts)})
    write_csv(paths['structure_csv'],structure_cells,['dataset','field','value','source_sha256','source_json_pointer'])
    lines = ['# P2/P3 measurement tables — preparation only','',
             'Values below are copied from three checksum-bound completed analysis JSON files. No raw data, count rows, GT, labels, search or new statistics were used. This is a report ingredient, not the final overnight report.','',
             'QPS uses the source **mean of five round QPS values**. Recall remains a fraction; paired Recall deltas and their pointwise 95% bootstrap intervals remain percentage points. Markdown prints round-trip float values, without rounding or recomputing means/CIs. CSV/JSON retain every original measurement/comparison field and all five round values.','',
             '**Semantics:** Fast expanded/rejected/evicted are unmeasured and shown as null. Missing P2 counters are unavailable in the bound analysis. Oracle methods are GT diagnostics and cannot be deployed. P3 cross-model QPS/wall comparisons are descriptive fixed-order results, without paired timing inference. Instrumented routing/graph times are not pure wall latency; routing-only batches are separate descriptive batches. All intervals are exploratory and unadjusted. Historical reused exact-GT time is null/unknown, never zero. P3 frequency/greedy probe-cost pointers are shared per lambda and must not be summed twice.','',
             'Nested bootstrap invocation status is copied as source metadata; top-level COMPLETE is the completion status. Analysis gate flags below do not replace the separately managed gate files.','',
             f'Coverage: {len(measurements)} measurement rows; {len(comparisons)} fixed-comparison rows; {len(costs)} full cost records; {len(structures)} full structure records.','',
             '## Bound sources','', table(['Source','SHA256','Path'],[[name,b['sha256'],b['path']] for name,b in bindings.items()]),
             '## All measurements','']
    for stage in ('P2','P3'):
        for dataset in DATASETS:
            selected=[r for r in measurements if r['stage']==stage and r['dataset']==dataset]
            lines.extend([f'### {stage}: {dataset}','',table(
                ['Model','Method','L','Recall fraction','QPS mean of five','Routing NDC','Graph NDC','Total NDC','Expanded','Rejected','Evicted','Oracle only'],
                [[r.get('model','P2_fixed_model'),r['method'],r['L'],r['recall'],r['qps_mean_of_five'],r['mean_routing_ndc'],r['mean_graph_ndc'],
                  r['mean_total_ndc'],r['mean_expanded'],r['mean_rejected'],r['mean_evicted_unexpanded'],r['oracle_diagnostic_only']] for r in selected]),''])
    lines += ['## All fixed comparisons','',
              'Every Recall/NDC delta is candidate minus reference. The displayed QPS ratio is the stored ratio of mean candidate QPS to mean reference QPS; no QPS interval is available. Same-model timing-pair details and all saved flags remain in JSON/CSV.','']
    for stage in ('P2','P3'):
        for dataset in DATASETS:
            selected=[r for r in comparisons if r['stage']==stage and r['dataset']==dataset]
            lines.extend([f'### {stage}: {dataset}','',table(
                ['Contrast','L','Candidate','Reference','Recall delta pp','Saved 95% CI pp','QPS ratio of means','Graph NDC delta','Total NDC delta','Improved/harmed/equal','P3 cross-model wall descriptive'],
                [[r['contrast'],r['L'],r.get('candidate',r.get('candidate_model','')+'/'+r.get('candidate_method','')),
                  r.get('reference',r.get('reference_model','')+'/'+r.get('reference_method','')),r['recall_delta_pp'],r['paired_query_bootstrap95_pp'],
                  r['timing_ratio_display_value'],r['mean_graph_ndc_delta'],r['mean_total_ndc_delta'],
                  f"{r['query_improved']}/{r['query_harmed']}/{r['query_equal']}",r['P3_cross_model_wall_descriptive_only']] for r in selected]),''])
    lines += ['## Costs and structure','',
              'The following cost cells preserve the source field names and numeric values exactly. Thread-seconds are not wall-seconds; phase subtotals and repeated shared pointers are not additive training totals. Unknown full initializer and exact-GT times remain null. No cost cells are fetched from outside the three sources.','']
    for record in costs:
        rows=[r for r in cost_cells if r['stage']==record['stage'] and r['dataset']==record['dataset']]
        lines += [f"### {record['stage']}: {record['dataset']} cost",'',table(['Source cost field','Value'],[[r['cost_field'],r['value']] for r in rows]),'']
    for record in structures:
        rows=[r for r in structure_cells if r['dataset']==record['dataset']]
        lines += [f"### P3: {record['dataset']} structure",'',table(['Source structure field','Value'],[[r['field'],r['value']] for r in rows]),'']
    lines += ['## Reproduce and machine-readable artifacts','',
              f'Generator: `{Path(__file__).resolve()}`; SHA256 `{sha(__file__)}`. The command must target a new prefix.','',
              '```bash',f'.venv_cpu/bin/python {Path(__file__).relative_to(RUN.parent.parent.parent)} --output-prefix /absolute/new/prefix','```','',
              table(['Artifact','Path'],[[name,str(path)] for name,path in paths.items() if name!='complete']),
              'The JSON preserves full measurement/comparison objects and the source flags; all references carry source SHA256 plus JSON Pointer. The CSV files flatten measurements, comparisons, individual cost cells, and individual structure cells for later excerpting.','']
    with paths['markdown'].open('x') as f:
        f.write('\n'.join(lines))
    completion={'status':'COMPLETE','generator':result['generator'],'source_bindings':bindings,'reconciliation':reconciliation,
                'outputs':{name:{'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size} for name,path in paths.items() if name!='complete'},
                'raw_inputs_read':False,'new_statistics_computed':False,'final_overnight_report_written':False}
    write_json(paths['complete'],completion)
    print(json.dumps(completion,indent=2))


if __name__=='__main__':
    main()
