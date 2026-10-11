#!/usr/bin/env python3
"""Render E174's completed metrics and existing small receipts only.

This script never opens raw packets, GT, vector/base/index/model payloads, never
hashes inputs, and never runs inference, fitting or a new statistical resample.
Matplotlib is imported only by main(), after the complete-matrix gate.

Optional --costs JSON schema:
  {"stages": [{"stage": "evaluation", "elapsed_seconds": 1.0,
                "scope": "...", "receipt": "/path/to/receipt.json"}]}
Use stage="independent_audit" for that separately measured wall interval.
Missing intervals are disclosed; they are never silently treated as zero.
"""
import argparse
import csv
import json
import math
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ("webvid2_5m_light_v1", "yandex_t2i_official10M_ip_v1")
DS_NAME = dict(zip(DATASETS, ("WebVid", "Yandex")))
ROLES = ("confirm_a", "confirm_b")
ROLE_NAME = {"confirm_a": "pilot a", "confirm_b": "confirm b"}
PILOT = ("GT", "M5", "M5REG24", "M5REG96", "M5FIRST96", "MFDIRECT",
         "MFREG96", "GEODIRECT", "GEOREG96")
CONFIRM = ("GT", "M5", "M5REG96", "MFREG96", "GEOREG96")
L_VALUES = {DATASETS[0]: (800, 1000), DATASETS[1]: (1000, 1200)}
AUDIT_PASS = "PASS_INDEPENDENT_112_POINT_INTEGER_WALL_TRACE_AUDIT"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path, optional=False):
    path = Path(path)
    if optional and not path.exists():
        return {}
    require(path.stat().st_size <= 64 * 1024 * 1024,
            f"report refuses large payload: {path}")
    return json.loads(path.read_text())


def point_key(row):
    return row["role"], row["dataset"], int(row["K"]), int(row["L"]), row["method"]


def comparison_key(row):
    return (*point_key(row), int(row["reference_L"]), row["reference"])


def finite(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def validate(measured, state):
    require(measured["status"] == "COMPLETE_E174_FROZEN_112_POINT_EVALUATION"
            and measured["primary_method"] == "M5REG96"
            and measured["training_increment_seconds"] == 0
            and measured["default_replacement"] is False,
            "complete frozen evaluation, zero new TRAIN, no default replacement")
    require(state.get("active") is None and len(state.get("completed", [])) == 4
            and all(x["exit_code"] == 0 for x in state["completed"]),
            "all four native jobs must finish before rendering")
    points = {point_key(p): p for p in measured["points"]}
    expected = {(r, d, k, l, m) for r in ROLES for d in DATASETS
                for k in (1, 100) for l in L_VALUES[d]
                for m in (PILOT if r == "confirm_a" else CONFIRM)}
    require(len(points) == len(measured["points"]) == 112 and set(points) == expected,
            "exact 112-point matrix, no missing or duplicated point")
    for p in points.values():
        require(p["n"] == 4096 and p["count_audit_n"] == 256
                and finite(p["recall_pct"]) and 0 <= p["recall_pct"] <= 100,
                "full native/quality and sampled-count scope")
        require(len(p["qps_rounds"]) == len(p["wall_seconds"]) == 3
                and all(finite(x) and x > 0 for x in p["qps_rounds"] + p["wall_seconds"])
                and all(finite(p[x]) and p[x] > 0 for x in
                        ("qps_median", "qps_min", "qps_max")),
                "three finite positive observed rounds")
    comparisons = {comparison_key(c): c for c in measured["comparisons"]}
    require(len(comparisons) == len(measured["comparisons"]), "unique comparisons")
    mechanisms = {point_key(m): m for m in measured["mechanisms"]}
    require(len(mechanisms) == len(measured["mechanisms"]) == 64,
            "complete 64 region mechanism rows")
    for c in comparisons.values():
        require(point_key(c) in points and
                (c["role"], c["dataset"], c["K"], c["reference_L"], c["reference"]) in points,
                "comparison references actual frozen points")
        require(finite(c["recall_delta_pp"]) and
                finite(c["delta_ci"]["low_pp"]) and finite(c["delta_ci"]["high_pp"])
                and c["delta_ci"]["low_pp"] <= c["delta_ci"]["high_pp"]
                and c["delta_ci"]["repeats"] == 2000
                and len(c["paired_qps_ratio_rounds"]) == 3,
                "existing descriptive CI and three speed ratios")
    return points, comparisons, mechanisms


def fmt(value, digits=3, signed=False):
    if value is None:
        return "未单列"
    return format(float(value), ("+" if signed else "") + f".{digits}f")


def esc(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def table(headers, rows):
    return "\n".join(["| " + " | ".join(map(esc, headers)) + " |",
                       "| " + " | ".join("---" for _ in headers) + " |"] +
                      ["| " + " | ".join(map(esc, row)) + " |" for row in rows])


def link(path, label=None):
    path = Path(path)
    return f"[{label or path.name}](<{path}>)"


def qps(p):
    return f'{fmt(p["qps_median"], 1)} [{fmt(p["qps_min"], 1)}, {fmt(p["qps_max"], 1)}]'


def delta(c):
    return (f'{fmt(c["recall_delta_pp"], 3, True)} '
            f'[{fmt(c["delta_ci"]["low_pp"], 3, True)}, '
            f'{fmt(c["delta_ci"]["high_pp"], 3, True)}]')


def speed(c):
    return fmt(c["paired_qps_change_pct"], 2, True) + "%"


def ratios(c):
    return "/".join(fmt(x, 4) for x in c["paired_qps_ratio_rounds"])


def rescue_damage(c):
    return f'{c["rescue_members"]}/{c["damage_members"]}'


def get_comparison(comparisons, role, ds, K, L, method, ref_L, reference):
    key = role, ds, K, L, method, ref_L, reference
    require(key in comparisons, f"required frozen comparison missing: {key}")
    return comparisons[key]


def pilot_match(c, comparisons):
    key = ("confirm_a", c["dataset"], c["K"], c["L"], c["method"],
           c["reference_L"], c["reference"])
    require(key in comparisons, f"matching pilot comparison missing: {key}")
    return comparisons[key]


def replicated(c, comparisons):
    # Both roles must explicitly have observed joint gain, as the frozen
    # protocol requires. CI.low > 0 is not used as a proxy for observed gain.
    # This stricter report gate additionally requires QPS range separation;
    # it is not a multiplicity-corrected test or default-replacement rule.
    # No favorable pair is selected to cancel b.
    return (c["role"] == "confirm_b" and c["method"] == "M5REG96"
            and c["observed_joint_gain"] is True
            and c["delta_ci"]["low_pp"] > 0
            and c["all_rounds_faster"] is True
            and c["speed_ranges_separated"] is True
            and pilot_match(c, comparisons)["observed_joint_gain"] is True)


def label(c, comparisons, audited):
    if replicated(c, comparisons):
        return "局部复现" if audited else "满足局部门，独审待完成"
    if c["observed_joint_gain"]:
        return "观测双升，未达更严格报告门" if c["role"] == "confirm_b" else "pilot 观测双升"
    if c["recall_delta_pp"] > 0 and c["paired_qps_change_pct"] < 0:
        return "Recall升/QPS降取舍"
    if c["recall_delta_pp"] < 0 and c["paired_qps_change_pct"] > 0:
        return "QPS升/Recall降取舍"
    return "未观察到双升"


def primary_comparisons(comparisons):
    return [c for c in comparisons.values() if c["method"] == "M5REG96"
            and c["reference"] in ("M5", "GT")]


def mechanism_details(root):
    path = root / "reviews/independent_result_audit/independent_mechanisms.csv"
    if not path.exists():
        return {}
    require(path.stat().st_size <= 64 * 1024 * 1024, "bounded detail CSV")
    with path.open(newline="") as f:
        return {point_key(row): row for row in csv.DictReader(f)}


def optional_integer(row, names):
    for name in names:
        if name in row and row[name] not in ("", None):
            return str(int(row[name]))
    return "未单列"


def costs(root, points, state, supplemental):
    rows, covered = [], set()
    def add(stage, value, scope, source):
        rows.append((stage, fmt(value, 3) if value is not None else "未留独立计时",
                     scope, link(source) if source else "无单独收据"))
    add("新增 TRAIN/拟合/模型或图构建", 0, "本轮增量；历史 TRAIN 债不重置", root / "protocol.md")
    large_path = root / "reviews/data_preflight_large_sha.receipt.json"
    large = load(large_path, True)
    add("四个大输入串行 SHA", large.get("elapsed_seconds"),
        "base/index；性能期前，非查询 wall", large_path)
    preflight_path = root / "reviews/data_preflight.json"
    preflight = load(preflight_path, True)
    add("其余身份预检小文件 SHA", preflight.get("current_identity", {}).get("metadata_small_hash_seconds"),
        "原收据字段；不含上列大 SHA，非完整人工审查时长", preflight_path)
    build_path = root / "reviews/build.json"
    build = load(build_path, True)
    add("成功编译", build.get("elapsed_seconds"), "工程成本，非 TRAIN/查询 wall", build_path)
    first_path = root / "reviews/build_attempt1_admin_failure.json"
    first = load(first_path, True)
    if first:
        add("首次编译及收据失败", first.get("compile_seconds"),
            first.get("timing_limit", "保留首次产物；计时未留"), first_path)
    smoke_path = root / "reviews/smoke_execution.json"
    smoke = load(smoke_path, True)
    for job in smoke.get("jobs", []):
        add(f'{job["variant"]}/{DS_NAME[job["dataset"]]}', job.get("elapsed_seconds"),
            "16-query程序/原M5回归，不是正式QPS资格", smoke_path)
    for job in state["completed"]:
        add(f'完整 native {ROLE_NAME[job["role"]]}/{DS_NAME[job["dataset"]]}',
            job["elapsed_seconds"],
            "含加载/基字核验/预热/正式wall/plain/replay/oracle/count/写盘/进程等待", root / "run_state.json")
    formal = sum(sum(p["wall_seconds"]) for p in points.values())
    add("其中336正式批次 owned wall", formal,
        "上列 native 已包含；单列构成，不可再次相加", root / "analysis/final_v1/points.csv")
    for row in supplemental.get("stages", []):
        require(finite(row["elapsed_seconds"]) and row["elapsed_seconds"] >= 0,
                "actual supplemental cost interval")
        covered.add(row["stage"])
        add(row["stage"], row["elapsed_seconds"], row["scope"], row.get("receipt"))
    for stage, scope in (("evaluation", "既有 exact GT评分、bootstrap、输出hash/存盘；不在QPS内"),
                         ("independent_audit", "独立整数/集合/trace/收据复核及bounded SHA；不在QPS内")):
        if stage not in covered:
            add(stage, None, scope + "；缺少独立wall记录，不能记零", None)
    return rows


def figures(points, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import ScalarFormatter
    colors = {"GT": "#111827", "M5": "#64748b", "M5REG96": "#dc2626",
              "M5REG24": "#f97316", "M5FIRST96": "#a16207", "MFDIRECT": "#93c5fd",
              "MFREG96": "#2563eb", "GEODIRECT": "#d8b4fe", "GEOREG96": "#7e22ce"}
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                         "svg.hashsalt": "E174-frozen-report-v1"})
    out.mkdir(parents=True, exist_ok=True)
    for role, filename in (("confirm_a", "pilot.svg"), ("confirm_b", "confirm.svg")):
        methods = PILOT if role == "confirm_a" else CONFIRM
        fig, axes = plt.subplots(2, 2, figsize=(13, 8.7))
        for row, ds in enumerate(DATASETS):
            for col, K in enumerate((1, 100)):
                ax = axes[row, col]
                for method in methods:
                    for li, L in enumerate(L_VALUES[ds]):
                        p = points[(role, ds, K, L, method)]
                        x = p["qps_median"]
                        ax.errorbar(x, p["recall_pct"],
                                    xerr=[[x - p["qps_min"]], [p["qps_max"] - x]],
                                    fmt="o" if li == 0 else "s", color=colors[method],
                                    markersize=5.5 if method == "M5REG96" else 4,
                                    capsize=2, elinewidth=.8, alpha=.95)
                        if method in ("GT", "M5", "M5REG96"):
                            ax.annotate(f"L{L}", (x, p["recall_pct"]),
                                        xytext=(4, 4 if li == 0 else -10),
                                        textcoords="offset points", fontsize=7,
                                        color=colors[method])
                ax.set_title(f'{DS_NAME[ds]} | Recall@{K} | n=4096')
                ax.set_xlabel("Complete-wall QPS (3-round median and range)")
                ax.set_ylabel(f"Recall@{K} (%)")
                ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
                ax.ticklabel_format(axis="y", style="plain", useOffset=False)
                ax.grid(alpha=.2)
        handles = [Line2D([0], [0], marker="o", color="none",
                          markerfacecolor=colors[m], markeredgecolor=colors[m],
                          label=m, markersize=5) for m in methods]
        fig.legend(handles=handles, loc="lower center", ncol=min(5, len(methods)),
                   frameon=False, bbox_to_anchor=(.5, .015), fontsize=8)
        fig.suptitle(f'E174 {ROLE_NAME[role]}: all frozen points; circle=lower L, square=upper L', fontsize=12)
        fig.tight_layout(rect=(0, .105, 1, .955))
        fig.savefig(out / filename, metadata={"Date": None, "Creator": "E174 frozen metrics renderer"})
        fig.savefig(out / Path(filename).with_suffix(".png"), dpi=160,
                    metadata={"Software": "E174 frozen metrics renderer"})
        plt.close(fig)


def render(root, analysis, measured, points, comparisons, mechanisms,
           state, audit, supplemental):
    audited = audit.get("status") == AUDIT_PASS
    primary = primary_comparisons(comparisons)
    confirmed = [c for c in primary if replicated(c, comparisons)]
    observed_b = [c for c in primary if c["role"] == "confirm_b" and c["observed_joint_gain"]]
    lines = ["# E174：冻结 M5 残差区域扩展实测报告", "",
             "本轮保留原 M5 的完整 C、fresh scalar 重评分与严格 TopK 合并；新增从 C 选 seed、沿原 NSG 一跳生成表外 X 的扩展。原 GT 主搜索、画像路由、rawIP 度量和默认 GT10 均保留。新增拟合、教师、模型/画像/主图构建为零；旧 TRAIN 超额不因此清零。", ""]
    if confirmed:
        lines += [f"主候选 M5REG96 有 {len(confirmed)} 个具体比较满足在冻结协议门上附加范围分离的更严格报告门" +
                  ("，已通过结果独审。" if audited else "；结果独审尚未完成，暂不标已审局部复现。") +
                  "该标签仅覆盖下表中的离散 dataset/K/L/reference，不能替代默认或外推其他预算。", ""]
    else:
        lines += [("主候选确认集有观测双升，但没有比较达到在冻结协议门上附加范围分离的更严格报告门。" if observed_b else
                   "主候选确认集没有观察到 Recall/QPS 双升。") +
                  "停止本冻结一跳/seed/预算版本；保留原 M5 与全部历史产物，不从 a/b 响应继续调参。", ""]
    lines += [f"完整矩阵：{len(points)} 点、{sum(len(p['wall_seconds']) for p in points.values())} 个正式批次；每点4096 query、真实K=1/100、CPU15单线程、三轮完整wall。WebVid L=800/1000；Yandex L=1000/1200。a 为72点pilot，b 为40点冻结确认，按原锁全部执行。", "",
              "更严格报告门：冻结协议的较强局部证据门要求两roles正、confirm Recall描述性区间下界>0且三轮更快。本报告显式要求同 dataset/K/L/reference 的 pilot a 与 confirm b 都实测双升，不用CI下界代理confirm实测正；在此基础上附加确认候选最慢轮仍快于参考最快轮的范围分离条件，该附加保守条件不是protocol原文。多比较未做总体/同时校正，角色字节排除不建立语义IID。", "",
              f"数据：{link(analysis / 'metrics.json')}、{link(analysis / 'points.csv')}、{link(analysis / 'comparisons.csv')}、{link(analysis / 'mechanisms.csv')}；结果独审状态：`{audit.get('status', 'MISSING/PENDING')}`。", ""]

    lines += ["## 同 L：主候选相对原 M5 与 GT", "",
              "ΔR 为百分点；方括号为描述性95% paired query bootstrap区间。QPS为三轮中位数[min,max]；ΔQPS为三轮按序比的中位数变化，救回/损伤是实际返回 GT 成员数量。相同 L 仍需支付全部附加工作，不能由候选覆盖推断双升。", ""]
    for role in ROLES:
        rows = []
        for ds in DATASETS:
            for K in (1, 100):
                for L in L_VALUES[ds]:
                    p = points[(role, ds, K, L, "M5REG96")]
                    for reference in ("M5", "GT"):
                        c = get_comparison(comparisons, role, ds, K, L, "M5REG96", L, reference)
                        ref = points[(role, ds, K, L, reference)]
                        rows.append((f'{DS_NAME[ds]}/K{K}/L{L}', reference,
                                     f'{fmt(p["recall_pct"])} / {fmt(ref["recall_pct"])}',
                                     delta(c), qps(p) + " / " + qps(ref), speed(c),
                                     ratios(c), rescue_damage(c), label(c, comparisons, audited)))
        lines += [f"### {ROLE_NAME[role]}", "", table(
            ("dataset/K/L", "参考", "REG/参考 R%", "ΔR pp [CI]", "REG/参考 QPS", "ΔQPS", "三轮速度比", "救回/损伤", "判定"), rows), ""]

    lines += ["## 跨 L：小预算 REG96 对大预算 GT及原 M5 归因", "",
              "跨L速度只按round index对齐，为描述性顺序比较，不是同时或随机配对。下表并列小L原M5，避免把原M5已具备的质量或速度优势全部归给区域扩展。REG−M5增量均来自同小L比较。", ""]
    rows = []
    for role in ROLES:
        for ds in DATASETS:
            small, big = L_VALUES[ds]
            for K in (1, 100):
                reg = points[(role, ds, K, small, "M5REG96")]
                m5 = points[(role, ds, K, small, "M5")]
                gt = points[(role, ds, K, big, "GT")]
                c = get_comparison(comparisons, role, ds, K, small, "M5REG96", big, "GT")
                base = get_comparison(comparisons, role, ds, K, small, "M5", big, "GT")
                inc = get_comparison(comparisons, role, ds, K, small, "M5REG96", small, "M5")
                if base["observed_joint_gain"]:
                    attribution = "原M5已有此跨档观测双升；REG贡献限于同L增量"
                elif base["recall_delta_pp"] >= 0:
                    attribution = "原M5已覆盖大GT质量差额；不能归因整个速度优势"
                elif c["recall_delta_pp"] > 0:
                    attribution = "REG跨过原M5质量缺口；仍按完整wall与确认门判定"
                else:
                    attribution = "REG尚未跨过大GT质量门"
                rows.append((f'{ROLE_NAME[role]}/{DS_NAME[ds]}/K{K}/{small}→{big}',
                             f'{fmt(gt["recall_pct"])}; {qps(gt)}',
                             f'{fmt(m5["recall_pct"])}; {qps(m5)}',
                             delta(base) + "; " + speed(base) + ("; 观测双升" if base["observed_joint_gain"] else "; 无观测双升"),
                             f'{fmt(reg["recall_pct"])}; {qps(reg)}',
                             delta(c) + "; " + speed(c) + "; " + ratios(c),
                             delta(inc) + "; " + speed(inc) + "; 救/损=" + rescue_damage(inc),
                             label(c, comparisons, audited), attribution))
    lines += [table(("role/dataset/K/L", "大L GT：R%;QPS", "小L M5：R%;QPS", "M5−大GT：ΔR;ΔQPS", "小L REG：R%;QPS", "REG−大GT：ΔR;ΔQPS;ratios", "REG−M5同L增量", "判定", "归因限界"), rows), ""]

    lines += ["## Pilot 强控制", "",
              "仅a拥有FIRST、24以及MF/GEO的direct配对，不能冒充b重复了这些控制。它们比较冻结完整策略：实际C/X数量、槽读取和费用可能不同，相同额外cap不等于同wall。GEO继承已学习GT10画像，不是全流程无监督。", ""]
    control_pairs = (("M5REG96", "M5FIRST96"), ("M5REG96", "M5REG24"),
                     ("MFREG96", "MFDIRECT"), ("GEOREG96", "GEODIRECT"),
                     ("M5REG96", "MFREG96"), ("M5REG96", "GEOREG96"))
    rows = []
    for ds in DATASETS:
        for K in (1, 100):
            for L in L_VALUES[ds]:
                for method, reference in control_pairs:
                    c = get_comparison(comparisons, "confirm_a", ds, K, L, method, L, reference)
                    rows.append((f'{DS_NAME[ds]}/K{K}/L{L}', method + " / " + reference,
                                 delta(c), speed(c), ratios(c), rescue_damage(c),
                                 "观测双升" if c["observed_joint_gain"] else "未观察到双升"))
    lines += [table(("dataset/K/L", "候选/参考", "ΔR pp [CI]", "ΔQPS", "三轮速度比", "救回/损伤", "观测"), rows), "",
              "若MF/GEO同样有效，解释应收缩为通用原图区域扩展；即使M5较强，也仅支持这些冻结来源/预算/角色的差异。query gap、不同posting行或产生表外ID，均不单独证明跨模态独有机制、不同basin或语义桥。", ""]

    lines += ["## 机制：新候选、支持集合外目标与实际救回/损伤", "",
              "U_M5是原冻结posting ID并集；U_TRAIN是原20K TRAIN GT100 ID并集。X及U外数量是按query的成员出现次数，不是全局distinct ID数。只有最终返回中的真成员差异才算救回/损伤；完整C保留不保证最终K个ID为原M5超集。", ""]
    detail = mechanism_details(root)
    rows = []
    for role in ROLES:
        for ds in DATASETS:
            for K in (1, 100):
                for L in L_VALUES[ds]:
                    key = role, ds, K, L, "M5REG96"
                    m = mechanisms[key]
                    c = get_comparison(comparisons, role, ds, K, L, "M5REG96", L, "M5")
                    d = detail.get(key, {})
                    damage_u = optional_integer(d, ("actual_true_damage_outside_original_M5_U_vs_M5", "new_damage_outside_original_M5_U", "damage_outside_original_M5_U"))
                    damage_t = optional_integer(d, ("actual_true_damage_outside_original_TRAIN_GT100_U_vs_M5", "new_damage_outside_original_TRAIN_GT100_U", "damage_outside_original_TRAIN_GT100_U"))
                    rows.append((f'{ROLE_NAME[role]}/{DS_NAME[ds]}/K{K}/L{L}',
                                 f'{fmt(m["C_mean"], 2)}/{fmt(m["X_mean"], 2)}/{fmt(m["selected_seeds_mean"], 2)}',
                                 f'{m["queries_with_X"]}/{m["n"]}', m["extension_aborted"],
                                 f'{m["X_outside_original_M5_U"]}/{m["X_outside_original_TRAIN_GT100_U"]}',
                                 f'{m["new_rescues_vs_M5"]}/{c["damage_members"]}',
                                 f'{m["new_rescues_outside_original_M5_U"]}/{damage_u}',
                                 f'{m["new_rescues_outside_original_TRAIN_GT100_U"]}/{damage_t}', delta(c)))
    lines += [table(("role/dataset/K/L", "C/X/seed均值", "有X query", "X abort", "U_M5/U_TRAIN外X", "相对M5救/损", "U_M5外实际救/损", "U_TRAIN外实际救/损", "净ΔR pp [CI]"), rows), "",
              "U外损伤若未在现有分析/独审明细中单列，则标未单列，不作零损伤假设。全量region trace与费用明细分离于固定256 count统计；NDC含main+R/C+X，不能从NDC或时间差精确归因某个单项操作。", ""]

    lines += ["## 全部实测点", "", "图仅画已测两档L的点；横条是三轮QPS范围，没有预算插值或绝对Recall区间。", "",
              "![全部pilot点](figures/pilot.svg)", "", "![全部confirm点](figures/confirm.svg)", "",
              "同图PNG： [pilot](figures/pilot.png)、[confirm](figures/confirm.png)。", ""]
    rows = []
    for role in ROLES:
        for ds in DATASETS:
            for K in (1, 100):
                for L in L_VALUES[ds]:
                    for method in (PILOT if role == "confirm_a" else CONFIRM):
                        p = points[(role, ds, K, L, method)]
                        rows.append((ROLE_NAME[role], DS_NAME[ds], K, L, method,
                                     fmt(p["recall_pct"]), qps(p),
                                     "/".join(fmt(x, 4) for x in p["wall_seconds"]),
                                     fmt(p["graph_ndc_sample_mean"], 2), fmt(p["route_ndc_sample_mean"], 2)))
    lines += [table(("role", "dataset", "K", "L", "method", "Recall%", "QPS median[min,max]", "三轮wall秒", "DC均值(256)", "route均值(256)"), rows), ""]

    lines += ["## 成本与身份核验边界", "", table(("阶段", "实际秒", "范围/重叠说明", "收据"), costs(root, points, state, supplemental)), "",
              "native总费用包含预热、完整plain、独立replay/oracle/count和写盘，正式wall已包含其中，不能重复相加。缺少独立计时的编译失败/分析/独审不记零，不能将已记录阶段小计宣称为完整项目总成本。现有模型的历史TRAIN费用未被本轮新增TRAIN=0免除。", ""]
    preflight = load(root / "reviews/data_preflight.json", True)
    smoke = load(root / "reviews/preexecution_acceptance.json", True)
    source = load(root / "reviews/native_source_independent_review.json", True)
    build = load(root / "reviews/build.json", True)
    lines += [f"身份预检：`{preflight.get('status', 'MISSING')}`，源审：`{source.get('status', 'MISSING')}`，编译：`{build.get('status', 'MISSING')}`。已有metrics绑定 {len(measured['source_sha256'])} 个源/返回文件SHA；本renderer复用收据，未重hash或打开任何raw/GT/base/index。", "",
              f"原GT/M5回归smoke：`{smoke.get('status', 'MISSING')}`；范围为“{smoke.get('scope', '未记录')}”。16-query smoke不证明正式QPS、全部输入分布或普遍Recall保全；source review也不是实测收益。", "",
              "正式证据为每点全4096 normal plain与独立replay逐位相等、direct全量线性oracle、region全量C/seed/X/fresh scalar/独立线性oracle，以及事前均匀256 query的plain/count词与计数核验。timed返回已释放，没有保存每个timing round的packet，因此不能宣称逐轮timed bits已离线核验。score words只在native untimed oracle内逐位核验，trace离线保存ID/status；整数独审不重新计算原图/visited/scalar。", "",
              "独立结果审计检查整数成员、paired rescue/damage、全矩阵wall和trace/收据身份；描述性bootstrap的seed/count/scope被检查，随机区间端点不由该确定性审计独立重采样。本renderer只显示已有端点。原GT tie成员定义保持，未新生成距离或tie-adjusted GT。", "",
              "输入角色排除仅覆盖注册字节/来源窗口及所查历史，不建立全项目未曝光或语义独立。a本轮打开后属于开发数据；b策略冻结且质量在全部native完成后打开。两个L/两K之外没有结果。", ""]
    if audit.get("teacher_support_sources"):
        rows = [(DS_NAME[ds], s["M5_U_size"], s["old_TRAIN_GT100_U_size"], link(s["path"]))
                for ds, s in audit["teacher_support_sources"].items()]
        lines += [table(("dataset", "|U_M5|", "|U_TRAIN|", "原支持标签身份"), rows), ""]
    lines += ["固定方法/身份/停止合同：" + link(root / "protocol.md") + "、" +
              link(root / "parameter_lock.json") + "、" + link(root / "execution_lock.json") + "。", "",
              "结论保留具体离散比较及其费用/不确定性；未满足门的双升记录为观察，一升一降记录为取舍。M5REG96的区域扩展与原M5的已有优势分开归因；本轮不替换GT10、不丢弃M5、不恢复旧队列。", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--metrics", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--costs", type=Path)
    parser.add_argument("--replace", action="store_true", help="replace only rendered report/figures")
    args = parser.parse_args()
    started = time.perf_counter()
    metrics = args.metrics or args.root / "analysis/final_v1/metrics.json"
    analysis = metrics.parent
    out = args.out or analysis
    state = load(args.root / "run_state.json")
    measured = load(metrics)
    points, comparisons, mechanisms = validate(measured, state)
    audit = load(args.root / "reviews/independent_result_audit/report.json", True)
    if audit:
        require(audit["status"] == AUDIT_PASS and audit["point_count"] == 112,
                "present independent audit must pass")
        # Bind the selected metrics to the actual audited file, using only
        # already-recorded identity and current metadata; never rehash here.
        selected_metrics = metrics.resolve()
        bindings = audit.get("source_sha256_and_stat4", {})
        require(str(selected_metrics) in bindings,
                "selected metrics file was not registered by independent audit")
        s = selected_metrics.stat()
        require(bindings[str(selected_metrics)].get("stat4") ==
                [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns],
                "selected metrics metadata changed since independent audit")
    supplemental = load(args.costs) if args.costs else {}
    for path in (out / "report.md", out / "figures/pilot.svg", out / "figures/confirm.svg",
                 out / "figures/pilot.png", out / "figures/confirm.png"):
        require(args.replace or not path.exists(), f"preserve rendered artifact: {path}")
    # Complete-matrix/receipt gate above precedes plotting or formatting values.
    figures(points, out / "figures")
    report = render(args.root, analysis, measured, points, comparisons, mechanisms,
                    state, audit, supplemental)
    render_seconds = time.perf_counter() - started
    report += ("\n本次报告/绘图生成截至最终Markdown写盘前耗时 " + fmt(render_seconds) +
               " 秒；该数包括小收据读取、格式化和SVG/PNG生成，不含最终Markdown写盘，未并入查询QPS。\n")
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text(report)
    print(json.dumps({"status": "RENDERED_COMPLETE_FROZEN_METRICS",
                      "report": str(out / "report.md"), "points": len(points),
                      "figures": [str(out / "figures" / filename) for filename in
                                  ("pilot.svg", "confirm.svg", "pilot.png", "confirm.png")],
                      "strict_local_gate_count": sum(replicated(c, comparisons) for c in primary_comparisons(comparisons)),
                      "default_replacement": False, "new_GT_or_raw_read": False,
                      "new_TRAIN": False, "new_hash": False}))


if __name__ == "__main__":
    main()
