# 入口 oracle、失败检测与 probe/reroute 历史

本页保存“既有入口还有多少搜索空间 → 能否识别需要改道的 query → 支付小 probe 后能否选好另一个入口”的完整链条。整理于 2026-09-08，仅核对既有分析、源码、配置与结果。当前方法与计划仍见根目录 `summary.md`、`s-target.md`、`spec.md`；本页不授权重开已停止分支。

## 1. Existing-hub oracle：先确认候选里存在搜索收益

### 问题、实现和评测集合

Fast 的 top-3 是几何路由结果。初始 oracle 问的是：在**相同冻结图和已经存在的 hub 集合**里，如果知道 GT，能否换入口改善有限预算搜索？它不增加 hub、不修底图，也不是枚举所有 base 节点。

WebVid 主诊断使用 seed 20260828 的 815 个现有 hub、validation 1K、L=64/128/200/400、K=1/10/100。每个 query/entry/L 都执行真实单入口搜索；选最佳单入口时以 Recall 优先、NDC 次之、入口 ID 决胜。另有 greedy hit-mask union-3：由各单入口命中集合贪心选三个入口，随后把所选入口作为真正的多入口初始化重放搜索。后者不是枚举所有三元组的最优解，也不能用单入口命中集合的并集直接冒充真实多入口结果。

| L，K=10 | Fast top-3 Recall | 最佳单入口 Recall | greedy union-3 真实重放 Recall | graph NDC：Fast / 单入口 / union-3 |
| --- | --- | --- | --- | --- |
| 64 | 65.23% | 80.24% | 76.17% | 923.564 / 913.376 / 907.980 |
| 128 | 73.89% | 85.38% | 82.35% | 1654.797 / 1639.833 / 1643.858 |
| 200 | 78.72% | 88.31% | 86.04% | 2427.676 / 2420.721 / 2412.956 |
| 400 | 84.81% | 91.61% | 89.86% | 4473.503 / 4473.654 / 4468.807 |

这些结果确认候选内有明显空间，但不能称为可部署路由：oracle 选择使用 GT，表中 NDC 是被选搜索的成本，不包含为寻找该 oracle 而枚举全部 hub 的成本。真实多入口搜索的共享候选池会改变轨迹，单入口 oracle 也不必被 greedy union-3 支配。三次运行使用同一 1K query，不能解释成独立 3K 或三次入口构建。

原始结果含 K=100/L=64 行；由于 K>L，本页排除该行。后续训练还生成过 WebVid `drl_train` 5K、L64/K10、815 hubs 的单入口标签，供 [search-aware centroid](04_utility_and_representation.md) 使用。较小 smoke 是链路检查，不应合并为额外研究证据。

证据：[oracle benchmark](../benches/bench_entry_oracle.cpp)、[validation 1K 原始结果](../oracle_entry_diagnostics/webvid_validation_1k_current_hubs_v1/results.json)、[train 5K 原始结果](../oracle_entry_diagnostics/webvid_router_train5k_l64_r10_current_hubs_v1/results.json)。

## 2. 失败检测：L10 trace 能否找到具有改道空间的 query

### 标签与特征

候选缩为 Fast geometry top-32。检测器正标签不是“当前结果 Recall 低”，也不是“某个替代入口已可预测”，而是：候选内单入口 Recall 先对 L64/128 取平均，再取候选最大值，减去 Fast3 跨 L 平均 Recall；差值至少 0.1（10 pp）。这个离线 GT/oracle 标签只用于监督和诊断。

比较 20 维静态路由特征与加入小预算搜索 trace 后的特征。早期文件采集 L10/16/32 三档 probe；后来有效成本协议明确只付 L10，因此最终检测器 `max_probe_L=10`，报告 `used_probe_Ls=[10]`。文件可包含较大 L 的 trace，不意味着模型被允许使用它们。L16/32 信息若用于模型而只计 L10 成本，结论必须排除；不能把早期更强 detector 的效果混入最终预算比较。

### 数据与结果

WebVid、Yandex official-IP，各 `drl_train` 10K fit、validation 10K，seed 20260828；以下来自 `l10_only_gain01_v2` 实际报告。

| 数据 | 静态 AUROC → 静态+L10 trace | 静态 AP → 静态+L10 trace | trace 风险最高 10% 的正标签率 |
| --- | --- | --- | --- |
| WebVid | 0.584258 → 0.659906 | 0.467514 → 0.557227 | 65.6% |
| Yandex | 0.619535 → 0.759084 | 0.336776 → 0.469471 | 55.3% |

L10 trace 对识别“哪里有 oracle 空间”有增量信号，Yandex 尤其明显。这只回答是否值得考虑改道，尚未回答改到哪个入口以及能否抵消 probe 成本；AUROC/AP 不是搜索 Recall 或端到端效率。

证据：[检测器源码与标签定义](../benches/run/train_probe_failure_detector.py)、[WebVid 最终报告](../probe_failure_detector_results/webvid_l10_only_gain01_v2/report.json)、[Yandex 最终报告](../probe_failure_detector_results/yandex_l10_only_gain01_v2/report.json)。报告保存实际使用的 probe L、特征名、来源校验和与模型产物位置。

## 3. 支付 probe 后的选择性改道：预算与 oracle 上限

### 执行语义

每个 query 先付一次 Fast3 L10 probe。按 detector 风险排序，仅对预定比例 query 从 top-32 选择替代入口；其余走 Fast restart。第二次搜索使用缩小的 L，以便与未 probe 的 Fast3 target-L 比较。最终返回结果将 probe 与第二阶段搜索的 top-K 合并、按距离排序去重，再算 Recall@10。没有可恢复搜索状态；probe 和第二次搜索是两笔已经支付的图成本。

| 数据 | Fast 目标 L | L10 probe 后第二阶段 L |
| --- | --- | --- |
| WebVid | 64 / 128 | 46 / 108 |
| Yandex | 64 / 128 | 40 / 104 |

`total_graph_NDC = probe_graph_NDC + second_search_graph_NDC`。L 值相加本身不代表 NDC 对齐，必须看实际 NDC。该字段仍未包含 Fast router、风险模型、候选打分、topology 特征提取、结果合并等全部线上时间，不能称为总延迟或完整 QPS。

固定风险子集之后，alternate oracle 在每条被选 query 的 top-32 内用真实 merged result 选择替代入口；此选择有 GT 特权，仅用于证明“付了 probe 以后尚有可用空间”。未选择改道的 query 也已支付 probe 并经历较短 restart，所以改道比例过小时可能无法弥补整体损失。

### 观测

WebVid 风险最高 20% 的 alternate oracle，相对完整 Fast target-L，Recall@10 在 L64/128 为 +0.103/+1.286 pp。旧版预算报告的 graph NDC 为 -0.441%/-0.779%；最终含 topology 的 v4 chooser 报告对应 -0.455%/-0.779%，应按版本引用，不能混作完全相同的数值。Yandex 高预算 20% 的 oracle 为 +1.359 pp、NDC -0.589%；低预算要到 30% 才见 +0.459 pp、NDC -3.362%。这些说明 selective oracle 有空间，没有证明学习器可实现该空间。

证据：[阶段综合分析](../probe_reroute_results/analysis.md)。预算原始结果保留在 `budget_reroute_diagnostics/`：WebVid validation 的 `probe10_top32_v1`、`v2` 和 `probe10_top32_topology_v3`，Yandex 的 `probe10_top32_v1`、`v2`；最终训练标签为同目录两数据集 `train10k_probe10_top32_*` 产物。`smoke_webvid_v1`、`smoke_webvid_topology_v2` 仅为执行检查。

## 4. Trace-conditioned chooser：识别失败并不足以选好入口

### 目标、模型与特征演进

候选选择器回归已经支付 probe 的 merged utility：

`U_merged = merged_Recall@10 - 0.05 × total_graph_NDC / baseline_Fast_NDC`。

样本权重为 `1 + 2 × max(merged_Recall - restart_Recall, 0)`。实际使用 HistGradientBoostingRegressor，learning_rate=0.05、max_iter=200、max_leaf_nodes=31、min_samples_leaf=80、l2_regularization=1。模型比较候选静态信息、L10 query trace、probe frontier，以及额外 7 维一/二跳局部 topology 特征。所有候选均来自 Fast top-32，图、入口集合与 probe 成本协议不变。

先前 frontier chooser 在 WebVid 20% 改道下，L64/128 Recall 分别下降 3.412/1.426 pp，NDC 增加 2.593%/0.969%。最后一次扩展把局部 topology 加入选择器，形成 `webvid_probe10_top32_topology_v4`，继续用训练 10K、validation 10K。

### 最终 v4 结果

下表全部来自同一个最终 report；`20%` 指 detector 判定风险最高的 20% query，其余保留协议内的 probe + restart。

| 选择方式 | L64：Recall Δ / total graph NDC Δ | L128：Recall Δ / total graph NDC Δ |
| --- | --- | --- |
| candidate static | -3.581 pp / +2.363% | -1.520 pp / +0.817% |
| trace conditioned | -3.532 pp / +2.463% | -1.459 pp / +0.863% |
| frontier conditioned | -3.482 pp / +2.548% | -1.377 pp / +1.020% |
| topology conditioned | -3.577 pp / +2.402% | -1.381 pp / +0.860% |
| frontier + topology | -3.371 pp / +2.668% | -1.416 pp / +1.036% |
| alternate oracle | +0.103 pp / -0.455% | +1.286 pp / -0.779% |

最终两个 topology 学习变体在测试的 10/20/30/50% 选择比例、两个预算下均掉 Recall 且增 NDC，不是只挑错一个阈值。oracle 与学习器之间的差距说明，当前 L10 trace 与局部 topology 虽能定位有改善空间的 query，却没能可靠预测哪个替代入口能带来支付成本后的收益。

### 停止条件与未执行内容

WebVid gate 失败后，原定最终 topology chooser 的 Yandex 扩展**未运行**。早前 Yandex detector、budget-oracle 的结果不能冒充该最终模型已在 Yandex 验证。分支判定为 NO-GO：不继续堆叠通用 chooser、不实现 resumable search、不扩 hub 或修改底图来挽救本分支，也不据此启动 held-out。

这里不是完整发表版 GATE 的移植，不能推出 GATE 整体无效；最多说明本项目这个 L10 probe、top-32、给定特征和学习器组合没有成功。完整 GATE 若作为独立论文 baseline，应按其实际方法另做契约核对，不可借本分支的名字视作已经公平复现。

证据：[最终综合分析](../probe_reroute_results/analysis.md)、[chooser 源码](../benches/run/train_trace_conditioned_rerouter.py)、[最终完整报告](../trace_conditioned_rerouter_results/webvid_probe10_top32_topology_v4/report.json)、[最终 WebVid validation 预算标签](../budget_reroute_diagnostics/webvid_validation10k_probe10_top32_topology_v3/results.json)、[对应训练标签](../budget_reroute_diagnostics/webvid_train10k_probe10_top32_topology_v3/results.json)。最终报告记录 L10 限制、7 维 topology、模型与输入文件 SHA256。

## 5. 历史链条的可用结论

1. 固定 hub 内存在 oracle 提升空间，单入口和多入口真实搜索必须分别重放。
2. L10 trace 对失败/改善空间检测有用，但该信号不是替代入口效用的可预测性证明。
3. 付费 selective oracle 仍有局部空间，而最终 learned chooser 明显未实现该空间；不能把 oracle 收益当成方法收益。
4. 全部 probe 必须计入图成本；任何额外 L16/32 trace、候选打分与特征提取也必须支付，离线预计算计时不等于线上端到端计时。
5. 当前分支已停止。后续 finite-beam/Atlas 的监督诊断见 [06](06_finite_beam_and_atlas.md)，其研究问题与这里的在线 L10 选择器不同。
