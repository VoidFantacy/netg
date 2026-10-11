#!/usr/bin/env python3
"""Post-audit E176 saved-field interpretation and honest cost supplement.

Creating/AST-parsing this source is not execution. Only after both native jobs
and the independent audit actually finish may it read small saved JSON/CSV.
No evaluator import, vector/raw GT/returns, ANN, fit, distance or bootstrap.
Original metrics/report and all frozen sources remain byte-identical.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ('webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1')
LABELS = dict(zip(DATASETS, ('WebVid2.5M', 'YandexT2I')))
MAX_SMALL_BYTES = 32 * 1024 * 1024


def require(ok, message):
    if not ok:
        raise ValueError(message)


def stat4(path):
    s = Path(path).stat()
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns]


class SmallSources:
    def __init__(self):
        self.bindings = {}

    def read(self, path):
        p = Path(path).resolve()
        before = stat4(p)
        require(before[2] <= MAX_SMALL_BYTES, f'refuse non-small artifact: {p}')
        data = p.read_bytes()
        require(stat4(p) == before, f'source changed while reading: {p}')
        record = {'sha256': hashlib.sha256(data).hexdigest(), 'stat4': before}
        require(str(p) not in self.bindings or self.bindings[str(p)] == record,
                f'source identity drift: {p}')
        self.bindings[str(p)] = record
        return data

    def json(self, path):
        return json.loads(self.read(path))

    def optional_json(self, path):
        p = Path(path)
        return self.json(p) if p.is_file() else None

    def stable(self):
        for path, r in self.bindings.items():
            require(stat4(path) == r['stat4'], f'input changed during supplement: {path}')


def point_key(p):
    return p['role'], p['dataset'], int(p['K']), int(p['L']), p['method']


def comparison_key(c):
    return point_key(c) + (int(c['reference_L']), c['reference'])


def finite_positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def elapsed(record, key='elapsed_seconds'):
    if record is None or key not in record or record[key] is None:
        return None
    value = record[key]
    require(isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= 0, 'actual elapsed field domain')
    return value


def read_csv(path, sources):
    return list(csv.DictReader(sources.read(path).decode().splitlines()))


def verify_comparison_csv(rows, comparisons):
    by_key = {comparison_key(r): r for r in comparisons}
    require(len(rows) == len(by_key) == 800, 'all original800 comparison CSV rows')
    seen = set()
    for row in rows:
        key = comparison_key(row)
        require(key in by_key and key not in seen, 'exact comparison CSV identity')
        seen.add(key)
        saved = by_key[key]
        for field, value in saved.items():
            require(field in row, f'saved comparison CSV field {field}')
            text = row[field]
            if isinstance(value, bool):
                require(text.lower() == str(value).lower(), 'saved flag CSV/JSON identity')
            elif isinstance(value, (dict, list)):
                require(json.loads(text) == value, 'saved list/CI CSV/JSON identity')
            elif isinstance(value, int):
                require(int(text) == value, 'saved integer CSV/JSON identity')
            elif isinstance(value, float):
                require(float(text) == value, 'saved float CSV/JSON identity')
            else:
                require(text == value, 'saved text CSV/JSON identity')


def interpretation(measured):
    points = {point_key(p): p for p in measured['points']}
    require(len(points) == len(measured['points']) == 160, 'all160 unique saved points')
    comparisons = measured['comparisons']
    require(len(comparisons) == len({comparison_key(c) for c in comparisons}) == 800,
            'all800 original unique comparisons')
    rows = []
    for saved in comparisons:
        a = points[point_key(saved)]
        bkey = saved['role'], saved['dataset'], saved['K'], saved['reference_L'], saved['reference']
        require(bkey in points, 'actual original reference point exists')
        b = points[bkey]
        require(finite_positive(a['qps_median']) and finite_positive(b['qps_median']),
                'positive saved point medians')
        require(math.isfinite(saved['recall_delta_pp']) and finite_positive(saved['paired_qps_ratio_median']),
                'finite already-audited comparison fields')
        ratio = a['qps_median'] / b['qps_median']
        recall_positive = saved['recall_delta_pp'] > 0
        paired_positive = saved['paired_qps_ratio_median'] > 1
        point_positive = ratio > 1
        require(saved['observed_joint_gain'] is (recall_positive and paired_positive),
                'preserve original strict paired gate identity')
        row = dict(saved)  # Keep every original paired flag/CI/field unchanged.
        row.update(candidate_saved_qps_median=a['qps_median'],
                   reference_saved_qps_median=b['qps_median'],
                   ratio_of_saved_point_qps_medians=ratio,
                   point_median_qps_change_pct=(ratio - 1) * 100,
                   recall_positive_saved=recall_positive,
                   paired_speed_positive_saved=paired_positive,
                   point_median_speed_positive=point_positive,
                   strict_joint_point_medians=recall_positive and point_positive,
                   strict_joint_both_definitions=saved['observed_joint_gain'] and recall_positive and point_positive,
                   speed_positive_flags_disagree=paired_positive != point_positive,
                   joint_flags_disagree=saved['observed_joint_gain'] != (recall_positive and point_positive),
                   comparison_scope='same_L' if saved['L'] == saved['reference_L'] else 'cross_L')
        rows.append(row)
    require(sum(r['comparison_scope'] == 'same_L' for r in rows) == 560
            and sum(r['comparison_scope'] == 'cross_L' for r in rows) == 240,
            'all prelocked560 sameL and240 crossL; no selection')
    summary = {'comparison_count': len(rows)}
    for scope in ('all', 'same_L', 'cross_L'):
        selected = rows if scope == 'all' else [r for r in rows if r['comparison_scope'] == scope]
        summary[scope] = {'rows': len(selected),
                         'original_paired_joint': sum(r['observed_joint_gain'] for r in selected),
                         'point_median_joint': sum(r['strict_joint_point_medians'] for r in selected),
                         'joint_both_definitions': sum(r['strict_joint_both_definitions'] for r in selected),
                         'speed_positive_flags_disagree': sum(r['speed_positive_flags_disagree'] for r in selected),
                         'joint_flags_disagree': sum(r['joint_flags_disagree'] for r in selected)}
    return rows, summary


def ledger(root, state, sources, lock):
    entries = []
    def add(cost_id, relative, key='elapsed_seconds', parent=None, additive=False, scope='', record=None, unknown=None):
        path = root / relative
        r = record if record is not None else sources.optional_json(path)
        value = elapsed(r, key)
        entries.append({'cost_id': cost_id, 'source_path': str(path), 'field_path': key,
                        'elapsed_seconds': value, 'parent_cost_id': parent, 'additive': additive,
                        'scope': scope, 'actual_status': None if r is None else r.get('status'),
                        'exit_code': None if r is None else r.get('exit_code'),
                        'unknown_reason': None if value is not None else (unknown or 'field/receipt not measured or not recorded; not zero')})
        return r
    add('fit_build', 'reviews/fit_build.json', additive=True,
        scope='actual FIT build receipt interval; complete external wrapper lifecycle not inferred')
    add('fit_preflight', 'reviews/fit_preflight.json', additive=True,
        scope='prepare_fit internal administrative/source-identity timer; excludes unmeasured earlier/later orchestration')
    fit_outer = sources.optional_json(root / 'reviews/fit_pipeline_execution.json')
    outer_is_run_fit = bool(fit_outer and any(str(a).endswith('/src/run_fit.py') for a in fit_outer.get('argv', [])))
    if fit_outer is not None:
        require(outer_is_run_fit, 'FIT outer receipt scope must explicitly identify run_fit process')
    add('fit_pipeline_outer', 'reviews/fit_pipeline_execution.json', additive=outer_is_run_fit,
        scope='complete run_fit process lifecycle, if actual external process receipt exists', record=fit_outer,
        unknown='no measured full run_fit process receipt; post-budget manifest hash/admin closing cost remains unknown')
    fit = sources.json(root / 'fit_state.json')
    require(fit['status'] == 'FIT_COMPLETE_ALL_MODELS_FROZEN' and fit.get('active') is None
            and len(fit['completed']) == 2 and {r['dataset'] for r in fit['completed']} == set(DATASETS),
            'actual both FIT phases complete')
    debts, resources, models, startup = [], [], [], []
    for ds in DATASETS:
        relative = f'reviews/fit_execution.{ds}.json'
        r = sources.json(root / relative)
        require(r == next(x for x in fit['completed'] if x['dataset'] == ds), 'FIT state/actual receipt identity')
        require(r['model_eligible'] and r['historical_cost_reset'] is False
                and r['cap_seconds'] == 900 and finite_positive(r['elapsed_seconds']) and r['elapsed_seconds'] <= 900,
                'actual perDS additional FIT cap and debt contract')
        parent = 'fit_pipeline_outer' if outer_is_run_fit else None
        cost_id = f'fit_budget_{ds}'
        add(cost_id, relative, parent=parent, additive=not outer_is_run_fit, record=r,
            scope='perDS900 budget timer: both native/compiler full child lifecycles; excludes later manifest load/hash and administrative receipt closing')
        for i, label in enumerate(('native', 'compiler')):
            add(f'{cost_id}_{label}', relative, key=f'stages[{i}].elapsed_seconds', parent=cost_id,
                record={'elapsed_seconds': r['stages'][i].get('elapsed_seconds'), 'status': 'actual nested subprocess',
                        'exit_code': r['stages'][i].get('exit_code')},
                scope='nested complete subprocess lifecycle; included in perDS FIT timer')
            entries[-1]['elapsed_seconds'] = elapsed(r['stages'][i])
            entries[-1]['unknown_reason'] = None if entries[-1]['elapsed_seconds'] is not None else 'nested elapsed not recorded'
        debts.append({'dataset': ds, 'historical_TRAIN_seconds': r['historical_TRAIN_seconds'],
                      'actual_additional_FIT_budget_seconds': r['elapsed_seconds'], 'additional_cap_seconds': r['cap_seconds'],
                      'cumulative_TRAIN_with_this_increment_seconds': r['cumulative_TRAIN_with_this_increment_seconds'],
                      'historical_cost_reset': r['historical_cost_reset'],
                      'unmeasured_old_teacher_graph_model_cost_seconds': None,
                      'scope': 'old recorded TRAIN debt retained; missing historical labels/construction/model costs not reconstructed or set to zero'})
        manifest_path=Path(r['model_manifest']).resolve()
        manifest = sources.json(manifest_path)
        require(sources.bindings[str(manifest_path)]['sha256']==r['model_manifest_sha256'],'actual FIT manifest SHA bound to successful receipt')
        for key, pair in manifest['models'].items():
            for family, m in pair.items():
                models.append({'dataset': ds, 'K': m['K'], 'L': m['L'], 'family': family,
                               'model_path': m['path'], 'model_sha256': m['sha256'], 'rows': m['shape'][0],
                               'eligible_key_count': m['eligible_key_count'], 'selected_key_target_pairs': m['selected_key_target_pairs'],
                               'bytes': m['bytes'], 'scope': 'saved compiler metadata; PAIR/WIDE online<=12 does not match offline capacity'})
        # Native/compiler breakdowns are illustrative metadata, never additive.
        entries.append({'cost_id': f'{cost_id}_compiler_internal', 'source_path': r['model_manifest'],
                        'field_path': 'compiler_elapsed_seconds/source_hash_seconds/label_decode_seconds/point_stages',
                        'elapsed_seconds': elapsed(manifest, 'compiler_elapsed_seconds'), 'additive': False,
                        'parent_cost_id': f'{cost_id}_compiler', 'scope': 'nested compiler internal timer and metadata; native_response_generation repeats prior native timer',
                        'saved_details': {k: manifest.get(k) for k in ('compiler_elapsed_seconds', 'native_response_generation_elapsed_seconds',
                                                                 'source_hash_seconds', 'label_decode_seconds', 'compiler_max_seconds_remainder')},
                        'unknown_reason': None})
    require(state['training_increment_seconds'] == sum(r['actual_additional_FIT_budget_seconds'] for r in debts),
            'recorded additional FIT total equals perDS actual budget increments')
    add('public_prepare', 'reviews/data_preflight.json', additive=True,
        scope='prepare_formal internal source/model freeze timer; not assumed full external process lifecycle')
    add('public_native_build', 'reviews/build.json', additive=True, scope='actual public benchmark build receipt interval')
    add('qualification_outer', 'reviews/qualification_execution.json', additive=True,
        scope='actual complete qualifier process lifecycle; frozen writer omits this outer receipt')
    qualification = add('qualification_inner', 'reviews/native_qualification.json', key='whole_elapsed_seconds',
                        parent='qualification_outer', scope='inner qualifier cutoff immediately before final receipt/state serialization; non-additive')
    if qualification:
        for i, r in enumerate(qualification.get('jobs', [])):
            entries.append({'cost_id': f'qualification_child_{i}', 'source_path': str(root / 'reviews/native_qualification.json'),
                            'field_path': f'jobs[{i}].elapsed_seconds', 'elapsed_seconds': elapsed(r),
                            'parent_cost_id': 'qualification_inner', 'additive': False,
                            'scope': 'complete owned serial child lifecycle; included in qualifier inner and outer',
                            'dataset': r['dataset'], 'exit_code': r.get('exit_code'),
                            'peak_rss_bytes_observed': r.get('peak_rss_bytes_observed'), 'rss_scope': r.get('rss_scope'),
                            'unknown_reason': None if elapsed(r) is not None else 'actual elapsed missing'})
    configs={}
    for job,digest in lock['jobs'].items():
        c=sources.json(job);require(sources.bindings[str(Path(job).resolve())]['sha256']==digest,'executed formal job source binding');configs[c['dataset']]=c
    for i, r in enumerate(state['completed']):
        require(r['exit_code'] == 0 and r['max_threads_observed'] == 1, 'actual formal native exit0/T1')
        entries.append({'cost_id': f'native_{r["dataset"]}', 'source_path': str(root / 'run_state.json'),
                        'field_path': f'completed[{i}].elapsed_seconds', 'elapsed_seconds': elapsed(r),
                        'parent_cost_id': None, 'additive': True,
                        'scope': 'complete owned formal native child execution/exit; includes startup/warm/oracle/count/serialization and timed batches',
                        'dataset': r['dataset'], 'exit_code': r['exit_code'], 'max_threads_observed': r['max_threads_observed'],
                        'unknown_reason': None if elapsed(r) is not None else 'native elapsed not recorded'})
        resources.append({'dataset': r['dataset'], 'peak_rss_bytes_observed': r.get('peak_rss_bytes_observed'),
                          'rss_scope': r.get('rss_scope'), 'max_threads_observed': r.get('max_threads_observed'),
                          'scope': 'sampled /proc VmRSS, not exact peak; perDS peaks are not summed'})
        env_path=Path(configs[r['dataset']]['out'])/'native_environment.json'
        env=sources.json(env_path)
        startup.append({'dataset':r['dataset'],'source_path':str(env_path),'startup_seconds':env.get('startup_seconds'),
                        'optimized_layouts':env.get('optimized_layouts',[]),'completion_tables':env.get('completion_tables',[]),
                        'complete_distinct_posting_resident_bytes':env.get('complete_distinct_posting_resident_bytes'),
                        'complete_posting_completion_layout_resident_bytes':env.get('complete_posting_completion_layout_resident_bytes'),
                        'parent_cost_id':f'native_{r["dataset"]}','additive':False,
                        'scope':'saved startup/layout scanning/trim/resident metadata; included in native job wall; resident not artifact size and no wall causal share'})
    for name, filename in [('evaluate_outer', 'evaluation_execution.json'), ('audit_outer', 'independent_audit_execution.json'),
                           ('plot_outer', 'plot_curves_wrapper_execution.json'), ('report_outer', 'report_wrapper_execution.json')]:
        add(name, 'reviews/' + filename, additive=True,
            scope='actual sequential post-native subprocess lifecycle; actual argv/source SHA identifies version')
    add('plot_inner', 'reviews/plot_curves_execution.json', parent='plot_outer',
        scope='internal plot timer before own receipt serialization; non-additive')
    add('report_inner', 'reviews/report_generation.json', parent='report_outer',
        scope='internal frozen writer timer before own receipt serialization; non-additive')
    for path in sorted((root / 'reviews').glob('administrative_failure*.json')):
        add('admin_failure_' + path.stem, str(path.relative_to(root)), additive=False,
            scope='only an actually recorded administrative failure; unmeasured elapsed stays null; no automatic addition without disjoint-scope evidence')
    for cost_id, scope in [('static_review_admin_unknown', 'unmeasured source review/lock/hash/orchestration work outside recorded timer boundaries'),
                           ('fit_postbudget_admin_unknown', 'manifest load/hash and closing writes after perDS FIT budget cutoff, unless included by measured FIT outer'),
                           ('supplement_outer_unknown', 'this supplement complete process lifecycle can only be supplied by later actual external execution receipt')]:
        entries.append({'cost_id': cost_id, 'source_path': None, 'field_path': None, 'elapsed_seconds': None,
                        'parent_cost_id': 'fit_pipeline_outer' if cost_id == 'fit_postbudget_admin_unknown' and outer_is_run_fit else None,
                        'additive': False, 'scope': scope, 'unknown_reason': 'not separately measured; null is not zero'})
    measured_subtotal = sum(e['elapsed_seconds'] for e in entries if e['additive'] and e['elapsed_seconds'] is not None)
    return {'entries': entries, 'per_dataset_TRAIN_debt': debts, 'formal_native_RSS': resources,
            'model_capacity_saved_metadata': models,'native_startup_layout_saved_metadata':startup, 'known_disjoint_interval_subtotal_seconds': measured_subtotal,
            'complete_activity_cost_seconds': None,
            'known_subtotal_scope': 'sum only additive measured disjoint intervals; mixes explicitly scoped internal and outer timers; not complete activity total',
            'unknown_costs_preserved': True, 'nested_doublecount_avoided': True,
            'frozen_writer_omission': {'outer_qualification_receipt_omitted': 'reviews/qualification_execution.json',
                                       'inner_timer_field_unrecognized': 'whole_elapsed_seconds',
                                       'original_writer_reports_inner_None': True, 'frozen_writer_and_report_modified': False},
            'limits': ['Existing TRAIN cost debt retained; formal no_training does not mean campaign0FIT.',
                       'Additional cap900/dataset is the frozen budget timer definition, not complete research activity wall.',
                       'Unknown/admin/historical costs remain null; known subtotal is not claimed exhaustive.',
                       'Qualifier child and inner timers, plot/report inner timers are included in outer stages; not additive.',
                       'Fixed256 count statistics do not give full wall causal shares; no R/C/X cost attribution from counts.',
                       'PAIR/WIDE <=12 online cap does not equalize offline rows/pairs/bytes/resident capacity.']}


def csv_write(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open('x', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in row.items()})


def cost_markdown(result):
    lines = ['# E176 费用补充：实际保存收据与未计量边界', '',
             '此附件保留原冻结 report/metrics，补入原writer遗漏的资格外层，并明确内部 whole_elapsed_seconds 的包含关系。', '',
             '| 项目 | 原件字段 | 实际秒 | 可加到已计量小计 | 父项 | 范围 |',
             '| --- | --- | --- | --- | --- | --- |']
    for e in result['cost_ledger']['entries']:
        value = 'null（未计量/未登记）' if e['elapsed_seconds'] is None else f"{e['elapsed_seconds']:.6f}"
        source = '未计量' if e['source_path'] is None else f"[{Path(e['source_path']).name}]({e['source_path']}) `{e['field_path']}`"
        lines.append(f"| {e['cost_id']} | {source} | {value} | {'是' if e['additive'] else '否'} | {e['parent_cost_id'] or '—'} | {e['scope']} |")
    lines += ['', f"已计量互不重复区间小计：{result['cost_ledger']['known_disjoint_interval_subtotal_seconds']:.6f} 秒。该小计包含明确边界的内部与外层计时，完整活动总价保持 null；没有把未知当0。", '',
              '每数据集继承 TRAIN 债、新增 FIT budget实际值和累计账：', '',
              '```json', json.dumps(result['cost_ledger']['per_dataset_TRAIN_debt'], ensure_ascii=False, indent=2), '```', '',
              'formal native RSS是约0.25秒采样峰值，不能称精确峰值或把两集峰值相加：', '',
              '```json', json.dumps(result['cost_ledger']['formal_native_RSS'], ensure_ascii=False, indent=2), '```', '',
              '原writer不认识 native_qualification.whole_elapsed_seconds，原表的None保留；本附件单列正确字段。qualification_execution外层包含内部资格与两个child，不重复加；900秒FIT范围不包含其后的manifest哈希和行政收据写入，未知边界保留。', '',
              '本附件只读已保存小型元数据。原metrics、report、冻结source和locks未改；没有ANN、向量/rawGT/返回读取、拟合、distance、GT生成或bootstrap。输入与本source的SHA绑定见同名JSON。']
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    require(root == ROOT, 'fixed campaign root')
    sources = SmallSources()
    sources.read(Path(__file__))
    state = sources.json(root / 'run_state.json')
    require(state['status'] == 'NATIVE_COMPLETE_PENDING_INDEPENDENT_GT_EVALUATION' and state.get('active') is None
            and len(state['completed']) == 2 and all(r['exit_code'] == 0 for r in state['completed'])
            and {(r['role'], r['dataset']) for r in state['completed']} == {('public_test', ds) for ds in DATASETS},
            'both actual native jobs must complete exit0 activeNone before any public output metadata read')
    audit_path = root / 'reviews/independent_result_audit/report.json'
    audit = sources.json(audit_path)
    require(audit['status'] == 'PASS_E176_INDEPENDENT_DYNAMIC_INTEGER_WALL_TRACE_AUDIT'
            and audit['point_count'] == 160 and audit['comparison_count'] == 800 and audit['formal_timed_batches'] == 480,
            'actual independent all160/800 audit PASS required')
    metrics_path = root / 'analysis/final_v1/metrics.json'
    measured = sources.json(metrics_path)
    binding = audit['source_sha256_and_stat4'][str(metrics_path)]
    require(sources.bindings[str(metrics_path)] == binding, 'metrics are exact audited bytes/stat')
    require(measured['status'] == 'COMPLETE_E176_DYNAMIC_FROZEN_EVALUATION' and measured['default_replacement'] is False,
            'actual completed saved evaluation and retained default')
    lock = sources.json(root / 'parameter_lock.json')
    sources.read(root / 'protocol.md')
    execution=sources.json(root / 'execution_lock.json')
    correction=sources.json(root / 'reviews/analysis_schema_correction_v2.json')
    require(correction['status'].startswith('PASS') and correction['administrative_interface_only'] is True
            and correction['original_execution_lock_sha256']==sources.bindings[str(root/'execution_lock.json')]['sha256'],'actual administrative v2 original execution lock binding')
    require(lock['protocol_sha256'] == sources.bindings[str(root / 'protocol.md')]['sha256'], 'original protocol binding')
    paths = [root / 'analysis/final_v1'/name for name in ('interpretation.csv', 'interpretation.json', 'cost_ledger_supplement.json', 'cost_ledger_supplement.md')]
    require(not any(p.exists() for p in paths), 'preserve any previous/partial supplements')
    for csv_name in ('points.csv', 'comparisons.csv'):
        p = root / 'analysis/final_v1'/csv_name
        sources.read(p)
        require(sources.bindings[str(p)] == audit['source_sha256_and_stat4'][str(p)], 'saved CSV exact audited bytes')
    verify_comparison_csv(read_csv(root / 'analysis/final_v1/comparisons.csv', sources), measured['comparisons'])
    original_report = root / 'analysis/final_v1/report.md'
    if original_report.exists():
        sources.read(original_report)
    else:
        require(False, 'preserved original report required before final delivery supplement')
    sources.read(root / 'src/evaluate.py')
    sources.read(root / 'src/write_report.py')
    for name in ('evaluate.py','write_report.py'):
        path=str(root/'src'/name);require(sources.bindings[path]['sha256']==execution['source_and_binary_sha256'][path],'original frozen source preserved')
    rows, summary = interpretation(measured)
    costs = ledger(root, state, sources, lock)
    report_receipt=sources.optional_json(root/'reviews/report_generation.json')
    if report_receipt is not None:require(report_receipt['report_sha256']==sources.bindings[str(original_report)]['sha256'],'original report writer receipt binding')
    sources.stable()
    common = {'source_sha256_and_stat4': dict(sources.bindings),
              'original_metrics_sha256': sources.bindings[str(metrics_path)]['sha256'],
              'original_report_sha256': sources.bindings[str(original_report)]['sha256'],
              'supplement_source_sha256': sources.bindings[str(Path(__file__).resolve())]['sha256'],
              'original_scientific_selection_and_defaults_unchanged': True,
              'scope': 'only all prelocked saved comparisons and actual small receipt metadata; no new scientific selection',
              'no_ANN_vectors_raw_GT_returns_new_fit_distance_GT_generation_bootstrap': True}
    interpreted = dict(common, status='COMPLETE_SAVED_FIELD_INTERPRETATION_SUPPLEMENT', summary=summary, comparisons=rows,
                       definitions={'original_primary_speed': 'median_r(qps_A_r / qps_B_r), unchanged saved paired fields',
                                    'point_curve_speed': 'saved point qps_median_A / saved point qps_median_B',
                                    'point_joint': 'saved recall_delta_pp>0 AND point median ratio>1; strict no tolerance',
                                    'intersection': 'original saved observed_joint_gain AND point_joint; no replacement of prelocked gate'},
                       limits=['The two median ratio definitions are not generally equal.',
                               'SameL sequential methods share round index; crossL round pairing descriptive only.',
                               'All800 retained including disagreement; no interpolation, selection, semantic IID or fresh confirmation.'])
    cost_result = dict(common, status='COMPLETE_SAVED_RECEIPT_COST_SUPPLEMENT_WITH_UNKNOWN_SCOPE', cost_ledger=costs)
    csv_write(paths[0], rows)
    with paths[1].open('x') as f:
        json.dump(interpreted, f, indent=2, ensure_ascii=False, allow_nan=False); f.write('\n')
    with paths[2].open('x') as f:
        json.dump(cost_result, f, indent=2, ensure_ascii=False, allow_nan=False); f.write('\n')
    with paths[3].open('x') as f:
        f.write(cost_markdown(cost_result))
    sources.stable()
    print(json.dumps({'status': 'COMPLETE_SAVED_OUTPUT_DELIVERY_SUPPLEMENTS', 'comparisons': len(rows),
                      'outputs': [str(p) for p in paths], 'original_metrics_report_preserved': True}))


if __name__ == '__main__':
    main()
