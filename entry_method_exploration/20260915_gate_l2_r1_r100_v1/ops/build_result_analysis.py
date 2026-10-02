"""Post-completion interpretation only; never launches training or evaluation."""
import csv
import hashlib
import json
import statistics
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RUN = Path(__file__).resolve().parents[1]
ORDER = [
    ("webvid2_5m_light_v1", "WebVid"),
    ("yandex_t2i_official10M_ip_v1", "Yandex"),
    ("deep10m_l2_v1", "Deep"),
    ("sift10m_bigann_l2_v1", "BIGANN-SIFT"),
    ("gist1m_l2_v1", "GIST"),
]
METHODS = ["NSG", "GT10-hard", "GT10-soft-t1", "GATE", "HNSW"]

def read_csv(name):
    with (RUN / "results" / name).open() as f:
        return list(csv.DictReader(f))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def table(headers, rows):
    return ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)] + [
        "| " + " | ".join(map(str, row)) + " |" for row in rows
    ]

rows = read_csv("metrics.csv")
targets = read_csv("recall_targets.csv")
paired = read_csv("paired_queries.csv")
walls = read_csv("wall_rounds.csv")
assert len(rows) == 800 and len(walls) == 2400
lookup = {(r["dataset"], int(r["K"]), r["method"], int(r["L"])): r for r in rows}

def best(ds, k, method, target):
    candidates = [r for r in rows if r["dataset"] == ds and int(r["K"]) == k
                  and r["method"] == method and float(r["recall"]) >= target]
    return max(candidates, key=lambda r: float(r["qps_mean"])) if candidates else None

threshold_rows = []
for t in targets:
    b = best(t["dataset"], int(t["K"]), t["method"], float(t["target_recall"]))
    assert (b is not None) == (t["achieved"] == "True")
    if b:
        assert b["L"] == t["L"] and float(b["qps_mean"]) == float(t["qps"])
    threshold_rows.append({**t, **({"qps_min": b["qps_min"], "qps_max": b["qps_max"],
                                  "failed_queries": b["failed_queries"]} if b else
                                 {"qps_min": "", "qps_max": "", "failed_queries": ""})})
with (RUN / "results" / "analysis_thresholds.csv").open("w") as f:
    writer = csv.DictWriter(f, fieldnames=list(threshold_rows[0]))
    writer.writeheader()
    writer.writerows(threshold_rows)

spreads = sorted((float(r["qps_max"]) / float(r["qps_min"]) - 1) * 100 for r in rows)
costs = json.loads((RUN / "results/offline_and_evaluation_costs.json").read_text())
cost_by_stage = {r["stage"]: r["seconds"] for r in costs}
formal_seconds = sum(r["seconds"] for r in costs if r["stage"].startswith("formal_"))
offline_seconds = sum(r["seconds"] for r in costs if not r["stage"].startswith("formal_"))
last = json.loads((RUN / "reviews/stage_formal_yandex_t2i_official10M_ip_v1_k100.json").read_text())
analysis_stage = json.loads((RUN / "reviews/stage_analysis.json").read_text())
finish = datetime.fromtimestamp(last["finished_unix"], ZoneInfo("Asia/Shanghai")).isoformat()
numeric = json.loads((RUN / "reviews/raw_results_verified.json").read_text())
model_rows = json.loads((RUN / "reviews/frozen_models.json").read_text())["datasets"]
models = {r["dataset"]: r for r in model_rows}
hard_soft = []
for ds, label in ORDER:
    for k in [1, 100]:
        h = {int(r["L"]): r for r in rows if r["dataset"] == ds and int(r["K"]) == k and r["method"] == "GT10-hard"}
        s = {int(r["L"]): r for r in rows if r["dataset"] == ds and int(r["K"]) == k and r["method"] == "GT10-soft-t1"}
        delta = [100 * (float(s[l]["recall"]) - float(h[l]["recall"])) for l in h]
        speed = [100 * (float(s[l]["qps_mean"]) / float(h[l]["qps_mean"]) - 1) for l in h]
        hard_soft.append(dict(dataset=ds, K=k, recall_delta_pp_min=min(delta), recall_delta_pp_max=max(delta),
                              qps_change_pct_min=min(speed), qps_change_pct_max=max(speed)))

text = """# E97 五集 Recall@1 / Recall@100 结果分析

2026-09-16 完成。WebVid、Yandex、Deep、BIGANN-SIFT、GIST 全部测完，排除 LAION。五方法、两种真实返回 K、每种 K 16 个预算、每点三次单线程计时，共 800 点和 2400 次计时。图表已实际打开检查，原始返回、精确 GT 评分、计时记录及冻结资产核验通过。

## 当前判断与 hard / soft 选择

若后续需要统一一条 GT10 研究主线，继续使用预先指定的 **GT10-hard**，保留固定 soft-t1 作辅助对照。理由是本轮没有显示 soft 跨数据集稳定优于 hard；hard 不需要 soft 温度规则。这是主线选择建议，不是宣布 hard 在全部曲线上最优。WebVid 旧 soft 默认、Yandex 旧 hard 默认均未改动，也没有按公开测试挑新温度或按预算拼接方法。

**WebVid：GT10 的 Recall@1 收益最清楚，hard/soft 几乎相同；Recall@100 的完整 HNSW 更有竞争力。** 80% Recall@1 门槛下，hard 是 80.56% / 1355 QPS，NSG 是 80.38% / 1015 QPS，GATE 是 81.78% / 1003 QPS；90% 门槛下，hard 是 90.73% / 353 QPS，NSG 是 90.65% / 281 QPS，约快 25.5%。但 Recall@100 达到 90% 时，HNSW 是 90.37% / 283 QPS，GT10 soft 是 90.69% / 239 QPS。K1 与 K100 不能混为一个赢家。所有方法在本预算上限内均未达到 95% 的 K1 或 K100。

**Yandex：hard 在中高 Recall@1 区域有价值，最高召回的 hard/soft 差异受门槛离散化影响。** 95% Recall@1 门槛下，hard 在 L256 达到 95.02% / 1127 QPS；soft 同预算只有 94.85%，需 L320 达到 95.77% / 906 QPS；GATE 为 95.59% / 890 QPS，HNSW 为 95.25% / 960 QPS。这支持当前实测网格上的 hard 取舍，不代表整个区间快 24%。99% 门槛则反过来：L1250 的 soft 为 99.00%、hard 为 98.99%，相差恰好 1 / 10000 个查询；soft 的 256 QPS 与 hard 下一档的 216 QPS 不能解释成稳定的大幅方法收益。K100 在 95% 门槛下 HNSW 634 QPS、hard 582 QPS，但实际召回分别是 95.0001% 和 95.3330%；这也不是严格相同 Recall 的比较。K100 所有方法均未达到 99%。

**Deep：hard 与 soft 的区别基本消失，GT10 比 NSG 更快，但没有统一超过完整 HNSW。** K1 在 99% 门槛下，hard/soft 为 2461/2473 QPS，NSG 为 2287、GATE 为 2419、HNSW 为 2596；实际召回均在 99.04%–99.11%。K100 同门槛下 HNSW 为 772 QPS（99.2340%），soft 为 701 QPS（99.3081%），NSG 为 676 QPS（99.3124%）。HNSW 的速度伴随略低的实际 Recall，不能宣称整条曲线支配。最小预算的 K1 已超过 93%、K100 已超过 91%，因此低召回区域没有覆盖。

**BIGANN-SIFT：soft 与 hard 同样接近，K100 中等召回区域 GT10 有用，高召回门槛又会交叉。** 95% K100 门槛下 soft 是 95.0181% / 2339 QPS，HNSW 需下一档达到 96.4864% / 1749 QPS；HNSW 的前一档 94.9540% 仅差 0.046 个百分点未过门槛，所以不能把约 34% 的门槛速度差扩展到整个区间。99% K100 时 HNSW 是 99.0260% / 958 QPS，soft 是 99.2701% / 926 QPS。99% K1 时 HNSW 2728 QPS、soft 2584 QPS。新 SIFT 是 BIGANN 首 10M，不能与旧 11.16M、本库抽 query 的历史版本直接拼接。

**GIST：完整 HNSW 更适合本轮 K100，K1 高召回保留 NSG/GT10 的价值。** 95% K100 门槛下 HNSW 达到 95.139% / 288 QPS，hard/soft 为 254/255 QPS；99% 时 HNSW 为 99.135% / 99 QPS，GT10 为 99.215% / 86–87 QPS。K1 在 90% 门槛下 HNSW 最快；95% 时 NSG 为 95.0% / 651 QPS，hard 为 95.9% / 544 QPS，HNSW 为 95.2% / 515 QPS。GIST 只有 1000 个查询，一个命中相差 0.1 个百分点；L128 时 NSG 与 hard 的 95.0% 对 94.8% 仅相差 2 个查询。HNSW 的 K1 曲线在高预算存在回落，原样保留，本轮最大实测 Recall@1 未达到 99%，不做平滑或补点。

**修正后的 GATE 没有显示出跨五集稳定优于 GT10 的证据。** 修正使正负冲突和同 query 正负配对归零，五集重新训练、导出一致；这是实现正确性改善，不保证检索性能提升。GATE 的方法适配仍包括 1000 节点子图上限、Sinkhorn 聚类近似、release cosine triplet 训练与统一查询 kernel。因此本轮结论只针对这份受限适配；不能推出原论文完整方法无效，也不能把旧 K10 与新 K1/K100 的差异解释成修复的因果增益。

## 图与计量口径

![Recall@1 与 QPS](figures/recall_qps_k1.png)

![Recall@100 与 QPS](figures/recall_qps_k100.png)

每条线保留 16 个实测点，阴影为三次 QPS 的 min–max；连线只辅助阅读，不是中间点的测量结果。横轴是对应 K 的真实 Recall，纵轴是同机 CPU15 单线程完整在线 QPS，包含路由、归一化、ID 映射、图搜索和写入预分配返回数组；不包含磁盘加载、构图、训练、GT 评分或落盘。显示 QPS 为三次 QPS 算术均值；CSV 同时保留总 wall 推导的 QPS。

Recall@1 按返回首 ID 与 GT 首 ID 比较；Recall@100 为返回前 100 与精确 GT 前 100 的交集比例，再对查询平均。GT10 名字中的 10 仍指训练目标数。严格 ID 口径保留了等距离候选换序的影响。跨 K 检查允许的首 ID 差异均限定为 HNSW 等距候选，首距离位与入口一致，并另验原向量 float64 距离；这不改变公开评分口径。

## 同召回门槛的最快实测点

单元格格式为 **QPS / 实际 Recall 百分比 / L或ef**。以下统一列出事先锁定门槛中的 90%、95%、99%；全部 50%、60%、70%、80%、90%、95%、99% 门槛及三次计时范围见 [门槛审阅 CSV](results/analysis_thresholds.csv)。未达到表示 16 个预算点中均无合格点，不外推。不在真实测试上选新预算或混合曲线。

""".splitlines()
for k in [1, 100]:
    text += [f"### Recall@{k}", ""]
    cells = []
    for ds, label in ORDER:
        for target in [.9, .95, .99]:
            values = []
            for method in METHODS:
                b = best(ds, k, method, target)
                values.append("未达到" if b is None else
                              f"{float(b['qps_mean']):.1f} / {float(b['recall']) * 100:.4f}% / {b['L']}")
            cells.append([label, f"{target*100:.0f}%", *values])
    text += table(["数据集", "门槛", *METHODS], cells) + [""]

text += ["## hard 与 soft 的差距有多大", "",
         "下表是全部 16 个同预算点的 soft − hard 范围；Recall 用百分点、QPS 用相对百分比。这里只描述相似程度，同 L 并不等工作量，也不是独立的部署胜负检验。", ""]
names = dict(ORDER)
text += table(["数据集", "K", "Recall差（百分点）", "QPS差（%）"],
              [[names[r['dataset']], r['K'], f"{r['recall_delta_pp_min']:+.4f} 至 {r['recall_delta_pp_max']:+.4f}",
                f"{r['qps_change_pct_min']:+.2f} 至 {r['qps_change_pct_max']:+.2f}"] for r in hard_soft])
text += ["", "Deep/SIFT 的微小 Recall 差和多数不到 1% 的速度差不足以证明 soft 值得成为统一主线；WebVid hard/soft 的整条曲线也非常接近。Yandex 的某些 QPS 差受个别计时波动影响，不能只比较一个均值。", "",
         "## 三次计时的波动与结论边界", "",
         f"800 点的 (QPS最大值 / 最小值 − 1) 中位数为 {statistics.median(spreads):.3f}%，95分位数（nearest rank）为 {spreads[759]:.3f}%，最大为 {max(spreads):.3f}%。这是观察到的重复范围，不是统计置信区间，也没有覆盖跨机器、跨时段、跨随机种子的变化。", "",
         "最大波动出现在 Yandex K1 / soft / L128：三次分别为 1970.5、1991.4、1725.6 QPS，均值 1895.8。该点原样保留，没有删慢轮、换成最好轮或补跑。hard 在同门槛的 1914.4 QPS 与它的微小差距不应作强结论。WebVid 80% K1 的 hard 范围为 1353.4–1356.6 QPS；与 NSG 相应合格点之间的约 33.5% 差距明显大于本轮重复波动，但仍限定于这一数据与预锁实测网格。", "",
         "单个门槛的最快点不等于整条曲线支配。尤其 Yandex 的 99%、SIFT K100 的 95%、GIST K1 的 95% 都受离散预算与少量命中变化影响。本文保留实际 Recall 和预算，并分别报告 K1/K100，不用同 L 的 Recall、NDC 或单个 QPS 差宣布普遍收益。", "",
         "## 查询失败和高预算端", "",
         "K1 的零命中就是首邻居未命中；K100 的零命中表示一个 GT100 邻居也没找回，不能把其补数当作 Recall@100。下表为最大预锁预算 L/ef=1500 的实际 Recall 与零命中查询数，格式为 Recall百分比 / 失败数。", ""]
text += table(["数据集", "K", "查询数", *METHODS],
              [[label, k, lookup[(ds, k, 'NSG', 1500)]['queries'],
                *[f"{float(lookup[(ds,k,m,1500)]['recall'])*100:.4f}% / {lookup[(ds,k,m,1500)]['failed_queries']}" for m in METHODS]]
               for ds,label in ORDER for k in [1,100]])
text += ["", "例如 WebVid K100 在 L1500 的零命中已全部为 0，但平均 Recall@100 仍只有约 91.4%–91.8%。GIST/SIFT K100 在全部测试预算下零命中均为 0，同样不能由此宣称检索已完整。", "",
         "[K1 零命中图](figures/failed_query_rate_k1.png) · [K100 零命中图](figures/failed_query_rate_k100.png)。", "",
         "逐查询配对提供了机制证据：WebVid K1 / L200，hard 相对 NSG 救回 453 个、新增失败 160 个，净增 293 个；GATE 救回 357 个、新增失败 188 个，净增 169 个。GIST K1 / L128，hard 救回 0 个、新增失败 2 个，解释了前述 95% 门槛变化。Yandex K1 / L256，hard 救回 163 个、新增失败 109 个，净增 54 个。这些是同 L 的配对诊断，性能结论仍以完整 Recall–QPS 曲线为依据；没有据此挑查询、调模型。见 [全部 1280 行配对](results/paired_queries.csv)。", "",
         "在线成本也解释了 GATE 的局限：WebVid K1 / L200 的 hard 路由 NDC 为 118.2、图 NDC 为 2440.6；GATE 为 298.1 与 2588.9，总计分别 2558.8 与 2887.0。这里只能说明这个点的成本组成，NDC 不等价于实际 wall。", "",
         "## 修复、训练与离线成本", "",
         "五集 GATE 全部重训，正负 hub 重叠为 0、同 query 作正负配对为 0，选中 checkpoint 与导出画像最大误差均为 0。下表为训练内层实测时间；轮数包含早停前执行的全部 epoch，不把 monitor 路由准确率称为检索 Recall。", ""]
text += table(["数据集", "有效triplet", "轮数", "GATE训练秒"],
              [[label, f"{models[ds]['train_triplets']:,}", models[ds]['training_epochs'], f"{models[ds]['training_seconds']:.2f}"] for ds,label in ORDER])
text += ["", "新三集的以下数字来自互不重叠的阶段外层 wall，单位秒；它们包含该阶段加载、验证和写出。不可再与内部子项叠加。QGT/fit/monitor/cal/test 的精确 GT 在下一列单独合计。", ""]
text += table(["数据集", "NSG阶段", "完整HNSW阶段", "GATE结构特征", "GATE标签", "GT10画像", "五种角色精确GT"],
              [[label, *[f"{cost_by_stage[f'{stage}_{ds}']:.2f}" for stage in ['nsg','hnsw','features','labels','profiles']],
                f"{sum(cost_by_stage[f'gt_{role}_{ds}'] for role in ['qgt','fit','gate_monitor','cal','test']):.2f}"]
               for ds,label in ORDER[2:]])
text += ["", "GT10 画像阶段只有约 2–3 秒不代表其全部构建成本：画像依赖独立 query、精确 GT、NSG 等上游资产；上游时间已分列。WebVid/Yandex 复用身份兼容的图、hub/结构特征、hop 标签缓存及完整 HNSW，旧成本未知或属于旧实验，不能记作零成本。两集这次 GATE 重新训练的成本照实保留。完整 HNSW 构建记录若已经包含中间保存时间，不再额外加一次 checkpoint 时间。", "",
         f"本轮记录的离线阶段总 wall 为 {offline_seconds:.2f} 秒（{offline_seconds/3600:.3f} 小时），正式评测阶段为 {formal_seconds:.2f} 秒（{formal_seconds/3600:.3f} 小时）。正式阶段结束于 {finish}，包括加载、warmup、三次计时、计数与返回落盘；不能用它倒算在线 QPS。自动评分与绘图另用 {analysis_stage['seconds']:.2f} 秒，最终冻结资产哈希核验另见 final_integrity.json。图文人工审阅时间未伪装成模型训练时间。", "",
         "2026-09-15 14:09 的前置检查发现 Yandex manifest 声明 10000 行，而路径仍指向原 100000 行文件；流水线在正式评测前停止。随后物化原文件固定前 10000 行，符合 E96 既定前缀，无结果驱动选样。15:19 前检通过，15:20 恢复正式测试，约 70 分钟的等待中断不计入训练或评测计算成本。原 100K 文件和 181 个原冻结资产保留；限定修订后的最终检查覆盖 183 个冻结资产，全部通过。", "",
         "[Yandex 修正记录](../../experiment_history/90a_yandex_test_prefix_fix.md) · [修正与身份审计](reviews/yandex_test_prefix_correction_v1/correction.json) · [阶段原始成本](results/offline_and_evaluation_costs.json)。", "",
         "## 可复核范围和当前结束状态", "",
         f"[数值审计](reviews/raw_results_verified.json)核验全部 800 点和 2400 次计时；每点额外抽取 8 个 query 检查返回距离与原向量 float64 距离。300 项跨 K 检查中共有 {sum(x['equal_distance_tie_ID_differences'] for x in numeric['cross_K_checks'])} 个首 ID 等距换序记录，按冻结规则核验；没有把它们藏起来或改写成更高 Recall。全部正式进程实际为单线程。四张总图经过实际视觉审查，28 个 PNG/PDF 文件有身份清单，单集图片和 PDF 未逐一人工视觉审阅。", "",
         "证据边界保留：GIST 缺少原始下载校验清单；WebVid/Yandex 公开测试已在历史实验使用；Deep/SIFT/GIST 为传统 L2 数据，不把它们统一包装成独立新 OOD 证据；GATE 保留前述合理适配；只有一次固定训练种子与三个计时重复。数值和实现检查通过不等于跨分布统计结论。", "",
         "当前授权范围内的修复、五集训练/测试、绘图、逐点核验和分析已完成。未启动 LAION、Recall@10、新网格或后续训练；未修改默认方法。若继续研究，需另行确定新的问题和独立验证范围，不能在本轮公共查询失败集上调参。", "",
         "[完整方法和训练流程](report.md) · [800点原始汇总](results/metrics.csv) · [2400次原始计时](results/wall_rounds.csv) · [图表清单](figures/manifest.json) · [视觉审查](reviews/figures_visual_check.json) · [最终身份核验](reviews/final_integrity.json)", ""]
(RUN / "analysis.md").write_text("\n".join(text))
review = dict(status="PASS", generated_at=datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
              metrics_sha256=sha(RUN / "results/metrics.csv"),
              thresholds_sha256=sha(RUN / "results/analysis_thresholds.csv"),
              all_350_threshold_selections_recomputed_and_matched=True,
              timing_spread_pct=dict(median=statistics.median(spreads), p95_nearest_rank=spreads[759], maximum=max(spreads)),
              hard_soft_same_budget_ranges=hard_soft,
              formal_seconds=formal_seconds, recorded_offline_seconds=offline_seconds,
              formal_finished_beijing=finish, analysis_sha256=sha(RUN / "analysis.md"))
(RUN / "reviews/analysis_evidence.json").write_text(json.dumps(review, indent=2) + "\n")
print(json.dumps({k:v for k,v in review.items() if k != "hard_soft_same_budget_ranges"}, indent=2))
