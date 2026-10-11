#!/usr/bin/env python3
"""Write E175's Chinese report from independently audited saved fields only.

No evaluator import, GT/return/vector read, ANN, fit, distance, bootstrap or
intermediate-L estimate. Run only after native, evaluation, independent audit
and plotting have actually completed. Source creation is not execution.
"""
import argparse
import hashlib
import json
import math
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ('webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1')
LABELS = dict(zip(DATASETS, ('WebVid2.5M', 'YandexT2I')))
METHODS = ('NSG', 'GT', 'M5', 'M5REG96')
L_VALUES = (200, 400, 800, 1000, 1200)
SAME_PAIRS = (('GT', 'NSG'), ('M5', 'GT'), ('M5', 'NSG'),
              ('M5REG96', 'GT'), ('M5REG96', 'M5'), ('M5REG96', 'NSG'))
THREAD_ENV = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
              'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read_json(path):
    path = Path(path)
    require(path.stat().st_size < 64 * 1024 * 1024, 'bounded JSON metadata only')
    return json.loads(path.read_text())


def stat4(path):
    s = Path(path).stat()
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns]


def small_sha(path):
    path = Path(path)
    before = stat4(path)
    require(before[2] < 64 * 1024 * 1024, 'refuse large hash')
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    require(stat4(path) == before, 'small source changed while hashing')
    return h.hexdigest()


def pk(p):
    return p['dataset'], p['K'], p['L'], p['method']


def ck(c):
    return c['dataset'], c['K'], c['L'], c['method'], c['reference_L'], c['reference']


def link(label, path):
    return f'[{label}]({Path(path).resolve()})'


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |',
                      '| ' + ' | '.join('---' for _ in headers) + ' |'] +
                     ['| ' + ' | '.join(str(x) for x in row) + ' |' for row in rows])


def fmt(value, places=4, signed=False):
    return format(value, ('+' if signed else '') + f'.{places}f')


def interval(c):
    return f"[{fmt(c['delta_ci']['low_pp'])}, {fmt(c['delta_ci']['high_pp'])}]"


def flag(v):
    return '是' if v else '否'


def select(comparisons, name, reference, same=True):
    return [c for c in comparisons.values() if c['method'] == name
            and c['reference'] == reference and ((c['L'] == c['reference_L']) is same)]


def counts(rows, field):
    return tuple(sum((r[field] > 0, r[field] == 0, r[field] < 0)[i]
                     for r in rows) for i in range(3))


def load_and_gate(metrics):
    # Administrative metadata gate precedes reading saved numerical fields.
    state = read_json(ROOT / 'run_state.json')
    require(state['status'] == 'NATIVE_COMPLETE_PENDING_INDEPENDENT_GT_EVALUATION'
            and state.get('active') is None, 'native-complete stable state required')
    jobs = state['completed']
    require(len(jobs) == 2 and all(j['exit_code'] == 0 for j in jobs)
            and {(j['role'], j['dataset']) for j in jobs}
            == {('public_test', ds) for ds in DATASETS}, 'both native jobs exit0')
    audit_path = ROOT / 'reviews/independent_result_audit/report.json'
    audit = read_json(audit_path)
    require(audit['status'] == 'PASS_INDEPENDENT_80_POINT_INTEGER_WALL_TRACE_AUDIT'
            and audit['point_count'] == 80 and audit['formal_timed_batches'] == 240
            and audit['comparison_count'] == 200 and audit['full_region_trace_points'] == 20
            and audit['primary_full_region_trace_points'] == 20, 'actual independent audit scope')
    require(audit['default_replacement'] is False and audit['new_training_seconds'] == 0,
            'retain default and zero new TRAIN')
    binding = audit['source_sha256_and_stat4'].get(str(metrics))
    require(binding is not None and binding['stat4'] == stat4(metrics)
            and binding['sha256'] == small_sha(metrics), 'selected metrics are audited bytes')
    for path, record in audit['source_sha256_and_stat4'].items():
        require(stat4(path) == record['stat4'], 'audited source current metadata closure: ' + path)
    plot_path = ROOT / 'reviews/plot_curves_execution.json'
    plot = read_json(plot_path)
    require(plot['status'] == 'PASS_E175_80_POINT_PRECOMPUTED_BUDGET_CURVES'
            and plot['metrics'] == str(metrics) and plot['plotted_point_count'] == 80
            and plot['saved_point_fields_exactly_equal'] is True
            and plot['metrics_audited_sha256_and_stat4'] == binding, 'actual bound 80-point plot')
    measured = read_json(metrics)
    require(measured['status'] == 'COMPLETE_E175_FROZEN_80_POINT_EVALUATION'
            and measured['default_replacement'] is False
            and measured['training_increment_seconds'] == 0
            and measured['primary_method'] == 'M5REG96', 'completed saved evaluation')
    points = {pk(p): p for p in measured['points']}
    expected_points = {(ds, K, L, method) for ds in DATASETS for K in (1, 100)
                       for L in L_VALUES for method in METHODS}
    require(len(measured['points']) == 80 and set(points) == expected_points, 'exact 80 point matrix')
    for p in points.values():
        require(p['role'] == 'public_test' and p['n'] == 10000 and p['count_audit_n'] == 256
                and len(p['wall_seconds']) == len(p['qps_rounds']) == 3, 'saved point scope')
        require(all(math.isfinite(p[f]) for f in ('recall_pct', 'qps_median', 'qps_min', 'qps_max'))
                and 0 <= p['recall_pct'] <= 100
                and 0 < p['qps_min'] <= p['qps_median'] <= p['qps_max'], 'saved field domain')
    comparisons = {ck(c): c for c in measured['comparisons']}
    expected_comparisons = {(ds, K, L, a, L, b) for ds in DATASETS for K in (1, 100)
                            for L in L_VALUES for a, b in SAME_PAIRS}
    expected_comparisons.update((ds, K, small, method, big, 'GT')
                                for ds in DATASETS for K in (1, 100)
                                for i, small in enumerate(L_VALUES) for big in L_VALUES[i + 1:]
                                for method in ('M5', 'M5REG96'))
    require(len(measured['comparisons']) == 200 and set(comparisons) == expected_comparisons,
            '120 same-L and 80 cross-L saved comparisons')
    mechanisms = {pk(m): m for m in measured['mechanisms']}
    require(len(measured['mechanisms']) == 20
            and set(mechanisms) == {k for k in expected_points if k[-1] == 'M5REG96'}, '20 full traces')
    for m in mechanisms.values():
        require(all(isinstance(m[f], int) and m[f] >= 0 for f in
                    ('new_rescues_vs_M5', 'new_rescues_outside_original_M5_U',
                     'new_rescues_outside_original_TRAIN_GT100_U', 'new_damage_vs_M5',
                     'new_damage_outside_original_M5_U', 'new_damage_outside_original_TRAIN_GT100_U')),
                'both rescue and actual damage, including outside-U scope')
    plotted = {pk(p): p for p in plot['plotted_point_fields']}
    require(len(plot['plotted_point_fields']) == 80 and set(plotted) == set(points)
            and all(r == {f: points[k][f] for f in r} for k, r in plotted.items()),
            'plot records contain precisely saved fields')
    for path, record in plot['outputs'].items():
        require(Path(path).is_file() and stat4(path) == record['stat4']
                and small_sha(path) == record['sha256'], 'actual figure byte identity')
    return state, audit, plot, measured, points, comparisons, mechanisms


def protect_existing(audit):
    preflight = read_json(ROOT / 'reviews/data_preflight.json')
    execution = read_json(ROOT / 'execution_lock.json')
    paths = set(audit['source_sha256_and_stat4']) | set(preflight['registered_input_files'])
    for path, expected in execution['input_stats'].items():
        require(stat4(path) == expected, 'frozen execution input metadata')
        paths.add(path)
    paths.update(str(p) for p in (ROOT / 'reviews').rglob('*.json') if p.is_file())
    paths.update(str(ROOT / name) for name in ('protocol.md', 'parameter_lock.json', 'execution_lock.json',
                                              'auxiliary_lock.json', 'run_state.json',
                                              'analysis/final_v1/metrics.json', 'analysis/final_v1/points.csv',
                                              'analysis/final_v1/comparisons.csv', 'analysis/final_v1/mechanisms.csv'))
    if (ROOT / 'README.md').exists():
        paths.add(str(ROOT / 'README.md'))
    paths.add(str(Path(__file__).resolve()))
    return {path: stat4(path) for path in sorted(paths)}


def comparison_table(rows, points):
    out = []
    for c in sorted(rows, key=lambda c: (DATASETS.index(c['dataset']), c['K'], c['L'], c['reference_L'], c['method'])):
        ds, K, L, method, refL, reference = ck(c)
        point, ref = points[(ds, K, L, method)], points[(ds, K, refL, reference)]
        ids = link(f'{method}/L{L}', point['source_complete']) + ' − ' + link(f'{reference}/L{refL}', ref['source_complete'])
        out.append((LABELS[ds], K, ids, fmt(c['recall_delta_pp'], signed=True), interval(c),
                    f"{c['rescue_members']}/{c['damage_members']}",
                    f"{c['queries_net_improved']}/{c['queries_net_damaged']}",
                    fmt(c['paired_qps_change_pct'], 3, True), flag(c['observed_joint_gain']),
                    flag(c['all_rounds_faster']) + '/' + flag(c['speed_ranges_separated'])))
    return table(('数据集', 'K', '候选−参考原 point', 'ΔRecall pp', '保存 CI pp', '救回/损伤成员',
                  '净升/净降查询', '配对 QPS Δ%', '观察双升', '三轮皆快/范围分离'), out)


def summary_rows(comparisons):
    rows = []
    for ds in DATASETS:
        for K in (1, 100):
            for name, reference in (('M5REG96', 'M5'), ('M5REG96', 'GT'), ('M5', 'GT')):
                selected = [c for c in select(comparisons, name, reference) if c['dataset'] == ds and c['K'] == K]
                require(len(selected) == 5, 'five saved same-L points per summary')
                rp, re, rm = counts(selected, 'recall_delta_pp')
                qp, qe, qm = counts(selected, 'paired_qps_change_pct')
                rows.append((LABELS[ds], K, name + '−' + reference, f'{rp}/{re}/{rm}', f'{qp}/{qe}/{qm}',
                             sum(c['observed_joint_gain'] for c in selected),
                             f"{sum(c['rescue_members'] for c in selected)}/{sum(c['damage_members'] for c in selected)}"))
    return table(('数据集', 'K', '同 L 比较', 'Recall 升/平/降', 'QPS 升/平/降', '观察双升/5',
                  '五 L 救回/损伤成员和'), rows)


def costs(state):
    stages = (('编译', 'reviews/build.json'), ('输入预检/固定窗口', 'reviews/data_preflight.json'),
              ('资格 smoke/旧词回归', 'reviews/smoke_regression.json'),
              ('评价', 'reviews/evaluation_execution.json'), ('独立结果审计', 'reviews/independent_audit_execution.json'),
              ('曲线渲染', 'reviews/plot_curves_execution.json'))
    rows, records = [], {}
    for label, relative in stages:
        path = ROOT / relative
        receipt = read_json(path)
        require(receipt.get('status', '').startswith('PASS') or receipt.get('exit_code') == 0,
                'stage receipt must show actual successful execution: ' + relative)
        elapsed = receipt.get('elapsed_seconds')
        require(elapsed is None or (isinstance(elapsed, (int, float)) and math.isfinite(elapsed) and elapsed >= 0),
                'actual elapsed or explicit unavailable')
        records[relative] = {'status': receipt.get('status'), 'elapsed_seconds': elapsed, 'sha256': small_sha(path)}
        rows.append((label, '未计（非0）' if elapsed is None else fmt(elapsed, 6), link('实际收据', path)))
    for job in state['completed']:
        elapsed = job.get('elapsed_seconds')
        require(elapsed is not None and math.isfinite(elapsed) and elapsed > 0, 'actual native job whole elapsed')
        rows.append(('正式 native ' + LABELS[job['dataset']], fmt(elapsed, 6), link('run_state completed', ROOT / 'run_state.json')))
    # Failed attempts cannot disappear into a zero-cost or complete-total claim.
    for path in sorted((ROOT / 'reviews').glob('administrative_failure_*.json')):
        receipt = read_json(path)
        elapsed = receipt.get('elapsed_seconds')
        require(elapsed is None or (math.isfinite(elapsed) and elapsed >= 0), 'failed elapsed validity')
        records[str(path.relative_to(ROOT))] = {'status': receipt.get('status'), 'elapsed_seconds': elapsed,
                                               'sha256': small_sha(path)}
        rows.append(('行政失败 ' + path.stem, '未计（非0）' if elapsed is None else fmt(elapsed, 6), link('原失败收据', path)))
    rows.append(('本报告生成', '见实际收据（报告写完后保存）', link('report_execution.json', ROOT / 'reviews/report_execution.json')))
    return table(('阶段', '实际 elapsed 秒', '费用证据'), rows), records


def render(state, audit, measured, points, comparisons, mechanisms):
    reg_m5 = select(comparisons, 'M5REG96', 'M5')
    reg_gt = select(comparisons, 'M5REG96', 'GT')
    old_m5 = select(comparisons, 'M5', 'GT')
    cross = [c for c in comparisons.values() if c['L'] < c['reference_L']]
    require(len(reg_m5) == len(reg_gt) == len(old_m5) == 20 and len(cross) == 80, 'report scopes')
    joint = [c for c in cross if c['observed_joint_gain']]
    rr = counts(reg_m5, 'recall_delta_pp')
    qr = counts(reg_m5, 'paired_qps_change_pct')
    cost_table, cost_records = costs(state)
    blocks = [
        '# E175：M5 residual → region → newID 五档预算曲线',
        'GT10 默认保持，M5 与 M5REG96 保持研究状态；本次冻结的 80 点公共预算扫描完成后停止，不因曲线形状追加 L、训练或选点。'
        'WebVid 使用 GT10-soft-t1，Yandex 使用 GT10-hard。',
        f"相对同 L 原 M5，区域扩展的 20 点 Recall 升/平/降为 {rr[0]}/{rr[1]}/{rr[2]}，"
        f"配对 QPS 升/平/降为 {qr[0]}/{qr[1]}/{qr[2]}；观察到 {sum(c['observed_joint_gain'] for c in reg_m5)} 个同 L 双升点。"
        f"全部 80 个冻结跨 L 比较中观察双升 {len(joint)} 个，详细候选与较大 L GT 的原 point 身份保留在下表。"
        '这些是历史已曝光 public_test 上的离散实测观察，不构成独立确认或默认替换证据。',
        f"两数据集各固定 10,000 查询，真实 K=1/100，L=200/400/800/1000/1200，NSG/GT/M5/M5REG96，"
        f"共 80 点、240 轮正式 complete wall、120 同 L 与 80 跨 L 比较、20 个全 10K region trace。"
        '每点同一 CPU15 单线程三轮，所有线程环境为1；各方法在本轮同条件重跑。'
        'Recall 采用既有精确 GT 的成员集合，QPS 采用完整搜索及正常输出释放结束的 wall。',
        '## 曲线与数据',
        link('PNG 曲线', ROOT / 'analysis/final_v1/figures/recall_qps_budget_curves.png') + ' · ' +
        link('SVG 曲线', ROOT / 'analysis/final_v1/figures/recall_qps_budget_curves.svg'),
        f"![四方法五档 Recall–QPS 曲线]({ROOT / 'analysis/final_v1/figures/recall_qps_budget_curves.png'})",
        '横轴 Recall%，纵轴三轮完整 wall 所得 QPS 中位数，误差线为已保存三轮 min–max。'
        '每条线只连接五个真实 L 点；没有拟合、平滑、jitter 或中间 L 性能推断。'
        '本轮原 NSG/GT/M5 是匹配对照，旧 E173/E174 的不同角色或计时不拼入曲线。',
        link('全部80点 CSV', ROOT / 'analysis/final_v1/points.csv') + ' · ' +
        link('全部200比较 CSV', ROOT / 'analysis/final_v1/comparisons.csv') + ' · ' +
        link('全部20机制 CSV', ROOT / 'analysis/final_v1/mechanisms.csv') + ' · ' +
        link('已独审 metrics.json', ROOT / 'analysis/final_v1/metrics.json'),
        '## 同 L：区域增量、原 M5 贡献与默认比较',
        summary_rows(comparisons),
        '升/平/降按保存的 ΔRecall 与配对 QPS Δ% 符号统计。五 L 成员和属于不同搜索工作点的查询成员 incidence，'
        '不是唯一查询或唯一 base ID。观察双升仅指正 ΔRecall 与正配对 QPS 变化；三轮皆快与范围分离另外显示。',
        '### M5REG96 − 原 M5：区域扩展的20点净贡献', comparison_table(reg_m5, points),
        '### M5REG96 − GT：相对当前默认的20点', comparison_table(reg_gt, points),
        '### 原 M5 − GT：旧 posting 在本轮已有的20点贡献', comparison_table(old_m5, points),
        'ΔRecall 单位 pp；救回/损伤按同一查询既有 GTK 成员集的差集统计，净变化为救回减损伤。'
        'CI 引用评价保存的 descriptive paired query bootstrap 数值；独审核其元数据与 CSV/JSON 一致，'
        '没有独立重生成随机 CI 端点。QPS Δ% 是三轮配对比值的中位数变化，不能替换为两组 QPS 中位数之比。',
        '## 跨 L：全部预锁比较中的观察双升',
        '候选为较小 L 的原 M5 或 M5REG96，参考为较大 L 的 GT。'
        '80 个比较均事前固定，保存所有结果；下表列出 observed_joint_gain=true 的实际组合。'
        '跨 L 只按轮号配对，是顺序实测的描述性比例，不是同时运行或随机配对。',
        comparison_table(joint, points) if joint else '保存的80个跨 L 比较没有观察双升。',
        'M5 与 M5REG96 两种较小 L 候选均单独列出，不能把原 M5 已有收益归因于新区域扩展；'
        '精确 small/big L 和两端 complete.json 链接保留，不插值到其它预算。',
        '## 机制：是否越过旧支持集并实际救回/损伤',
        '保留原 GT 搜索与全量原 M5 C≤24；在原路由行中选最多3个 query-best residual seed，'
        '按实际图邻接物理 slot 轮转，跳过已见 main/C/X，最多96个新 X 距离；没有新 fit 或表。'
        '完整 region trace 是每点10,000×128 i32。以下都是逐查询 incidence；U 是旧 M5 表全局 ID 并集，'
        'TRAIN U 是合法旧20K TRAIN GT100 ID 并集，不是新 teacher 或新训练。',
    ]
    mrows = []
    for k in sorted(mechanisms, key=lambda k: (DATASETS.index(k[0]), k[1], k[2])):
        m = mechanisms[k]
        mrows.append((LABELS[k[0]], k[1], k[2], fmt(m['C_mean'], 3), fmt(m['X_mean'], 3),
                      m['X_outside_original_M5_U'], m['X_outside_original_TRAIN_GT100_U'],
                      f"{m['new_rescues_vs_M5']}/{m['new_damage_vs_M5']}",
                      f"{m['new_rescues_outside_original_M5_U']}/{m['new_damage_outside_original_M5_U']}",
                      f"{m['new_rescues_outside_original_TRAIN_GT100_U']}/{m['new_damage_outside_original_TRAIN_GT100_U']}",
                      m['extension_aborted']))
    blocks += [table(('数据集', 'K', 'L', 'C均值', 'X均值', 'X在M5 U外', 'X在TRAIN U外',
                      '相对M5救回/损伤', 'M5 U外救回/损伤', 'TRAIN U外救回/损伤', 'X中止查询'), mrows),
               'damage=(原 M5 返回−实际扩展返回)∩既有 GTK，无条件逐查询统计，未发生扩展也不以常量0替代。'
               '全量实际损伤、旧 M5 U 外损伤和旧 TRAIN U 外损伤分别报告。新 X、U 外覆盖或实际 rescue '
               '表明固定 ID 支持已扩展；它们不单独证明跨模态几何、模态 gap 因果效用或独立泛化。'
               'seed 最小评分与 X 有序生成由原生全量 scalar oracle 验证，独立整数审计不重新计算距离。',
               '## 全部80个实际工作点',
               table(('数据集', 'K', 'L', '方法/原 point', 'Recall%', 'QPS median', 'QPS min–max', '三轮 wall 秒'),
                     [(LABELS[ds], K, L, link(method, points[(ds, K, L, method)]['source_complete']),
                       fmt(points[(ds, K, L, method)]['recall_pct']), fmt(points[(ds, K, L, method)]['qps_median'], 3),
                       f"{fmt(points[(ds, K, L, method)]['qps_min'], 3)}–{fmt(points[(ds, K, L, method)]['qps_max'], 3)}",
                       ', '.join(fmt(x, 6) for x in points[(ds, K, L, method)]['wall_seconds']))
                      for ds in DATASETS for K in (1, 100) for L in L_VALUES for method in METHODS]),
               '## 费用与保存范围', cost_table,
               '费用表逐项引用实际收据；失败未保存耗时保留未计（非0），没有宣称上述记录等于完整项目总成本。'
               'native job elapsed 包括加载、warm、审计、正式批次和保存，不可与其包含的正式 wall 再相加。'
               '查询 whole wall 包含原搜索、原 M5 R/C 评分与合并、X扩展、正常输出生命周期；'
               '不能把全部 M5/region 额外 wall 归为100次 dot。离线字节校验、评价/CI、审计、绘图另计。'
               '本轮新 TRAIN 为0；旧 M5 监督/构建与历史跨方法 TRAIN 费用债保留，不计作本轮 fresh 费用或消失。',
               '协议资源上限为64GiB RSS、512MiB campaign 保存、至少1GiB磁盘剩余；'
               '资源判断以实际执行/终态收据为准。未登记 peak RSS 时不编造峰值。',
               '## 来源、审计与结论边界',
               link('预锁协议', ROOT / 'protocol.md') + ' · ' + link('参数锁', ROOT / 'parameter_lock.json') + ' · ' +
               link('执行锁', ROOT / 'execution_lock.json') + ' · ' + link('输入预检', ROOT / 'reviews/data_preflight.json') + ' · ' +
               link('独立结果审计', ROOT / 'reviews/independent_result_audit/report.json'),
               '独审实际覆盖80点、240正式轮、200比较、20全量region机制及CSV身份。'
               '原 NSG 是固定 graph enterpoint，route=[ep,-1,-1]、profile +0、route NDC0，无 M5/post字段；'
               '它不按 GT route 或 GT main/post 分拆核等。GT/M5/REG保留原 GT route/profile。',
               '原 public fvecs/GT ivecs 与固定 raw 窗口有双来源身份。独审逐ID检查原 GT100 前10K与 derived GT、'
               'row0..9999一致并保留重复/顺序；向量值不在评价/独审/绘图/本报告中重读。'
               '原/derived query和原GT完整SHA沿用实际预检并核当前stat，不能称为本报告 fresh 大件SHA。',
               'NDC/费用计数只覆盖固定256查询；plain/replay与region scalar oracle/trace覆盖全10K。'
               '正式计时输出未保留，不能声称独审了每个 timed round 的返回 bits。'
               '仅一个历史已曝光 public_test role；200比较CI为描述性区间，无语义IID、同时多重比较保证或独立确认。'
               '本轮没有新 MF/GEO/FIRST 强控，旧强控不能冒充本轮同角色对照；callback/native绑定的既有限制沿用原始收据，'
               '代码或审计PASS不自动解除未决绑定。',
               '本报告只汇集已保存字段与点数/符号统计，没有新的质量计算、训练、距离、GT、bootstrap或选点。'
               '有限 E175 扫描到此结束，当前默认保持；未来独立确认须另立角色与冻结协议。',
               'English scope: 80 real points / 240 timed batches / 200 frozen comparisons / 20 full region traces. '
               'Historically exposed public_test only; descriptive observations, no independent confirmation or intermediate-L claim. '
               'GT10 remains the default.']
    return '\n\n'.join(blocks) + '\n', cost_records


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser()
    parser.add_argument('--metrics', type=Path, default=ROOT / 'analysis/final_v1/metrics.json')
    parser.add_argument('--out', type=Path, default=ROOT / 'analysis/final_v1/report.md')
    args = parser.parse_args()
    require(args.metrics.is_absolute() and args.out.is_absolute(), 'absolute input/output paths required')
    metrics, out = args.metrics.resolve(), args.out.resolve()
    require(metrics == ROOT / 'analysis/final_v1/metrics.json'
            and out == ROOT / 'analysis/final_v1/report.md', 'fixed E175 report identity')
    receipt_path = ROOT / 'reviews/report_execution.json'
    require(not out.exists() and not receipt_path.exists(), 'preserve existing report and receipt')
    os.sched_setaffinity(0, {14})
    require(all(os.environ.get(name) == '1' for name in THREAD_ENV), 'report execution env1')
    state, audit, plot, measured, points, comparisons, mechanisms = load_and_gate(metrics)
    protected = protect_existing(audit)
    protected.update({path: stat4(path) for path in plot['outputs']})
    text, cost_records = render(state, audit, measured, points, comparisons, mechanisms)
    require(all(stat4(path) == before for path, before in protected.items()), 'all existing files unchanged before report')
    out.write_text(text)
    require(all(stat4(path) == before for path, before in protected.items()), 'all existing files unchanged after report')
    receipt = {'status': 'PASS_E175_AUDITED_SAVED_FIELD_REPORT', 'stage': 'report',
               'source': str(Path(__file__).resolve()), 'source_sha256': small_sha(__file__),
               'metrics': str(metrics), 'metrics_audited_sha256_and_stat4': audit['source_sha256_and_stat4'][str(metrics)],
               'audit': str(ROOT / 'reviews/independent_result_audit/report.json'),
               'audit_sha256': small_sha(ROOT / 'reviews/independent_result_audit/report.json'),
               'plot_receipt_sha256': small_sha(ROOT / 'reviews/plot_curves_execution.json'),
               'point_count': 80, 'formal_timed_batches': 240, 'comparison_count': 200,
               'same_L_comparison_count': 120, 'cross_L_comparison_count': 80, 'full_region_trace_points': 20,
               'reported_cross_L_observed_joint_points': [list(ck(c)) for c in comparisons.values()
                                                        if c['L'] < c['reference_L'] and c['observed_joint_gain']],
               'actual_cost_receipt_fields': cost_records, 'protected_existing_file_count': len(protected),
               'protected_existing_stat4_unchanged': True, 'TRAIN_increment_seconds': 0,
               'default_replacement': False, 'base_query_GT_return_values_read': False,
               'new_distance_GT_fit_bootstrap_or_quality_calculation': False,
               'CPU_affinity': sorted(os.sched_getaffinity(0)),
               'thread_env': {name: os.environ[name] for name in THREAD_ENV},
               'outputs': {str(out): {'sha256': small_sha(out), 'stat4': stat4(out)}},
               'elapsed_scope': 'monotonic main start through report write and provenance checks; final receipt serialization/print excluded',
               'scope': 'presentation of actually audited saved fields; signs/counts across frozen comparisons only'}
    receipt['elapsed_seconds'] = time.monotonic() - started
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'status': receipt['status'], 'elapsed_seconds': receipt['elapsed_seconds'], 'report': str(out)}))


if __name__ == '__main__':
    main()
