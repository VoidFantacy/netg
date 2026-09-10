# 搜索效用监督与表示改造历史

本页归档已经执行的 sparse utility ranker、search-aware centroid、utility residual、target-basin modes 和 Basin Transition Graph（BTG）。整理日期为 2026-09-08；本次仅阅读既有源码、配置、分析及结果，不生成实验。当前方法、活动计划和执行契约分别以根目录 `summary.md`、`s-target.md`、`spec.md` 为准。本页的 NO-GO 是对应配置和证据范围内的历史判定，不是对整类模型的不可能性证明。

## 1. 共用背景与阅读边界

这些尝试都想解决同一缺口：Fast 的原型相似度能找到语义上相关的入口，但未直接预测“从该入口出发，在固定有限搜索预算内实际能找到多少近邻”。图固定为既有 NSG；大部分实验沿用 seed 20260828 的 Fast 入口集，因此优化器的三个 seed 或同一批查询的三次运行，不等于三次独立 Fast 构建。

除特别说明，Recall 指 Recall@10；`pp` 是百分数的百分点变化，NDC 是距离计算次数。这里多数结果来自离线生成入口、随后计量图搜索的诊断程序。相同 L 的 Recall、graph NDC 的改善，都不能直接写成包含路由的端到端 Recall–QPS 改善。`validation` 与最终 `held-out` 是不同集合；已经用于筛选多个版本的 validation 不能重新包装为全新评测。

## 2. Sparse utility ranker：显式学习候选入口效用

### 目标与机制

保留 Fast geometry top-32 作为候选，对每个 `(q, entry)` 运行真实单入口 NSG 搜索，取得 L=64/128 的 Recall@10 与 NDC。目标为两档 L 平均的

`U(q,e) = mean_L Recall@10(q,e,L) - 0.05 × mean_L[NDC(q,e,L) / max(NDC_Fast3(q,L),1)]`。

模型用 query 与 prototype/raw-entry 的逐维加权内积，加入口 bias 和 geometry-rank bias，预测候选分数；不是新的图，也不是读取在线搜索轨迹的模型。训练用温度 0.05 的 utility soft target、listwise cross entropy，另有 1e-4 对角参数正则；按 `1 + (1 - mean Recall_Fast3)` 加权难查询。Adam 学习率 0.02、batch 256、最多 50 epoch、early-stop patience 8。

### 数据、预算与实际执行

- WebVid、Yandex official-IP；冻结 NSG（R=64、Lbuild=100、C=512）与 Fast seed 20260828。
- `drl_train` 前 10K 按 8K fit / 2K dev 划分；验证为已有 validation 10K。每条训练候选只有 top-32 内的单入口 L64/128 标签。
- 优化器 seed 为 20260828/29/30；WebVid 停于 epoch 15/13/11，Yandex 为 22/24/24。三 seed 共用同一 Fast 构建。
- 预测 top-3 时不强制保留原 Fast anchor；另外跑较小 L 尝试匹配 graph NDC。

### 结果与判定

| 数据与比较 | Recall@10 变化 | graph NDC 变化 | 含义 |
| --- | --- | --- | --- |
| WebVid，同 L | +0.197～+0.329 pp | +0.47%～+1.03% | 小幅 Recall 增益伴随成本增加 |
| WebVid，L63 对 Fast L64 | +0.027～+0.100 pp | -0.26%～-0.62% | 低预算局部正信号 |
| WebVid，L127 对 Fast L128 | +0.125～+0.218 pp | 两 seed 降低，一 seed +0.088% | 非全部 seed 一致降成本 |
| Yandex，同 L | -0.042～+0.202 pp | +1.78%～+3.31% | 不稳定且更贵 |
| Yandex，L62 对 Fast L64 | -0.158～-0.402 pp | +0.46%～+0.89% | 匹配尝试仍失败 |
| Yandex，L126 对 Fast L128 | -0.070～+0.016 pp | +0.46%～+0.63% | 未形成跨数据稳定收益 |

WebVid validation 的预测 top-1 utility 为 0.645703～0.646656，低于 Fast 0.649449，候选内 oracle 为 0.740194。这说明“候选集中存在更好入口”与“该低容量模型能可靠选出它”是两个命题。历史结论是该 ranker 未通过跨数据集成本收益门槛，停止继续按同一路线加种子或扩大网格。没有端到端 QPS、尾延迟或独立构建方差证据，不能把 WebVid 的小正值升级为最终方法结果。

### 证据

- [原始分析](../sparse_utility_ranker_results/analysis.md)。
- [训练实现](../benches/run/train_sparse_utility_ranker.py)；标签来自 [真实入口 oracle benchmark](../benches/bench_entry_oracle.cpp)。
- [WebVid 配置与来源](../sparse_utility_ranker_variants/webvid_train10k_top32_l64_128_r10_diag_v1/manifest.json)、[Yandex 配置与来源](../sparse_utility_ranker_variants/yandex_train10k_top32_l64_128_r10_diag_v1/manifest.json)。
- [WebVid seed 20260828 原始验证](../sparse_utility_ranker_results/webvid_diag_v1_seed20260828/validation_10k_l64_128_r10_3run.json)、[Yandex 同 seed 原始验证](../sparse_utility_ranker_results/yandex_diag_v1_seed20260828/validation_10k_l64_128_r10_3run.json)；同级目录保留另两 seed 与 matched-L 结果。

## 3. Search-aware centroid：用搜索获胜入口重建原型

### 假设与实现

如果以搜索中真正有效的入口给训练 query 分组，替代几何标签聚合原型，可能弥补纯相似度路由。实现对 WebVid `drl_train` 5K 查询枚举全部 815 个既有 hub，执行单入口 L64/K10 oracle，给每个 query 分配唯一获胜 hub；Recall 并列按 NDC、再按 ID 决胜。新原型为归一化 query 向量之和加 `prior_weight=1` 的 raw hub 向量，再归一化。没有增加 hub，也没有改底图。

5K 查询只覆盖 809/815 个 hub，单 hub 获胜样本最多 21、最少 1；这样的标签分配相当稀疏。配置为 `webvid_train5k_l64_r10_prior1_v1`。验证使用 validation 1K，L64/128/200/400，分别检查 top-1/top-3；三次 timing 重复的 `samples=3000` 仍是相同 1K 查询，不是独立 3K。

| L | Fast top-3 Recall@10 | 新原型 top-3 Recall@10 | graph NDC：Fast → 新原型 |
| --- | --- | --- | --- |
| 64 | 65.23% | 65.80% | 923.564 → 926.906 |
| 128 | 73.89% | 74.71% | 1654.797 → 1666.548 |
| 200 | 78.72% | 79.22% | 2427.676 → 2437.009 |
| 400 | 84.81% | 85.16% | 4473.503 → 4497.461 |

top-3 有 +0.35～+0.82 pp 的 Recall@10 改善，同时 NDC 增加。top-1 的 Recall@1 下降 0.2～0.7 pp，Recall@10 为 0～+0.61 pp，NDC 增加约 0.95%～3.08%。未证明成本优势，也没有跨数据验证。由单入口硬标签得到一个 centroid 的路线因此未被继续提升为主方法；这不等于多模态表示普遍不可学习。

原始文件还含 K=100/L=64 行，因 K>L 不符合有效输出宽度契约，本页不采用其结果，也不能用它扩大 Recall@100 结论。

证据：[分析](../search_aware_entry_results/webvid_train5k_l64_r10_prior1_v1/analysis.md)、[manifest](../search_aware_entry_variants/webvid_train5k_l64_r10_prior1_v1/manifest.json)、[构建代码](../benches/run/build_search_aware_prototypes.py)、[top-1 验证](../search_aware_entry_results/webvid_train5k_l64_r10_prior1_top1_v1/validation_1k_3run.json)。top-3 数据及原始获胜入口诊断见相应结果目录和 [oracle 结果](../oracle_entry_diagnostics/webvid_validation_1k_current_hubs_v1/results.json)；oracle 空间说明见 [05](05_probe_reroute.md)。

## 4. Utility residual：从硬标签改为有正负权重的原型残差

这一步保留旧原型，把 query 对每个候选的相对效用作为残差权重。WebVid `drl_train` 10K、Fast top-32、L64/128，计算 `U = mean Recall - 0.05 × mean NDC / row_mean_candidate_NDC`；此处 NDC 分母是每条 query 的候选平均，**不是上一节 ranker 的 Fast3 NDC**。中心化 advantage 为 `U - mean_candidate U`，再乘 Fast3 Recall 定义的 hardness；每个 hub 的 signed query 残差按绝对权重和归一化。新原型为 `normalize(old_prototype + 0.25 × residual)`，覆盖 811/815 个 hub。

既有执行包括 validation 1K 和后续 10K；10K top-3 的实际结果如下，不能把它叙述成“所有测量均为负”。

| L | Recall@10：Fast → residual | 变化 | graph NDC：Fast → residual |
| --- | --- | --- | --- |
| 64 | 65.505% → 65.615% | +0.110 pp | 922.3222 → 921.9428 |
| 128 | 74.606% → 74.683% | +0.077 pp | 1655.3978 → 1654.3766 |
| 200 | 79.325% → 79.439% | +0.114 pp | 2439.7695 → 2438.7214 |
| 400 | 85.421% → 85.506% | +0.085 pp | 4505.3522 → 4504.5161 |

观测是 WebVid 上很小的正收益，缺乏 Yandex 对照、独立构建稳定性与完整路由 QPS 门槛。该分支被保留为未提升到主方法的局部信号；不应写成已证实的跨数据失败，也不能当作发布级 Pareto 增益。

证据：[manifest](../utility_residual_entry_variants/webvid_train10k_top32_l64_128_r10_a025_c005_t1_v1/manifest.json)、[构建实现](../benches/run/build_utility_residual_prototypes.py)、[validation 10K 原始结果](../utility_residual_entry_results/webvid_train10k_top32_l64_128_r10_a025_c005_t1_v1_validation10k/validation_10k_top3_3run.json)。目录中保留先前 1K 及各路由变体，不覆盖旧结果。

## 5. Target-basin modes：为一个入口增加目标分布模式

### 机制、拆分与两版区别

冻结 Fast hub，用训练 query 的 GT@1 对应 base 向量分配最近 raw hub；在每个 basin 内按 query 方向构造两个 spherical modes。fit 使用 `drl_train[10000:30000]`，少于 8 条的 basin 回退为重复原型。评分为

`max(q·primary_h, max_m[q·mode_hm + log(prior_hm)/dimension])`。

仅在 geometry top-32 内重排 top-3，每 query 最多增加 64 次 mode 内积，无在线图 probe。需要严格区分：

- **v1**：primary score 是分数回退，但不强制保留原 Fast rank-0 入口。WebVid 619/815 个 hub 形成两模式；训练报告中 top-3 集合变化率 37.05%，top-1 变化率 16.51%。
- **v2_anchored**：固定保留 Fast rank-0，再从原 rank 1～31 中选择两个，因此才有 anchor 的集合保留契约。

先评估 `drl_train[0:10000]`，既有产物还包括 validation 10K。本节 target-basin modes 的 fit 使用后 20K，与前 10K 不相交；这不包括第4节用前 10K 标签构建的 utility residual。基础 Fast primary 原型原本用过训练 30K，因此不能声称整个路由系统从未见过前 10K query。

train10K 阶段的 Recall@10 相对 Fast 均为正：v1 的 WebVid L64/128 为 +0.216/+0.159 pp、Yandex 为 +0.143/+0.095 pp；v2 anchored 分别为 +0.229/+0.167 pp 和 +0.122/+0.075 pp。它们与随后 validation 的 Yandex L128 微负属于不同阶段；这些 Recall 正值本身不替代 utility/非零改道等其余 gate 条件，也不是额外独立构建。

**以下表格为 validation10K 结果**，不是上述 train10K gate 的数值：

| 版本 | WebVid Recall@10 Δ，L64 / L128 | Yandex Recall@10 Δ，L64 / L128 | 结果边界 |
| --- | --- | --- | --- |
| v1 | +0.172 / +0.072 pp | +0.032 / -0.003 pp | NDC 约降低 0.054%～0.414%，收益很小 |
| v2 anchored | +0.176 / +0.085 pp | +0.017 / -0.017 pp | NDC 小幅降低，Yandex L128 未满足严格 Recall 不退化 |

原始 route 已离线生成，验证为单次、16 threads 的 graph-search 计量；新增 64 次内积没有计入端到端在线成本。结果未支持继续提升该特定模式校正分支；并不否定后来的固定 multi-view 主方法，也不等价于 confidence-attention 的实验。

证据：[v1 design](../target_basin_mode_diagnostics/v1/design.md)、[v2 anchored design](../target_basin_mode_diagnostics/v2_anchored/design.md)、[构建实现](../benches/run/build_target_basin_modes.py)、[v1 路由](../benches/run/route_target_basin_modes.py)、[anchored 路由](../benches/run/route_anchored_target_basin_modes.py)。结果目录 `target_basin_mode_diagnostics/v1/eval/` 保存两数据集 train/validation 10K；`v2_anchored/` 保存相应 `*_train_eval.json`、`*_validation_eval.json` 与构建/路由报告。

## 6. Basin Transition Graph：从原始图连通性推断入口效用

### 原始假设与实现

BTG 希望用 hub/basin 间的转移结构估计“从入口能否走到 query 的目标区域”，避免在线试遍候选。实现对冻结 NSG 做以全部 hub 为种子的确定性 multi-source outgoing BFS，把节点分配到 basin；FIFO 与 hub 次序决定并列。再统计有向跨 basin 边，构造保留/去除 self-transition 的转移矩阵。

query geometry top-32 形成 soft target，经有限步扩散得到 reachability 分数；候选分数为标准化几何分数加 `gamma × 标准化 log-reachability`，仅在相对原 rank-0 的 margin 达标时切换单入口。监督仍是保存的 top-32 单入口 L64/128 效用，`U = mean Recall - 0.05 × mean(NDC / Fast3_NDC)`。这是原始图拓扑扩散，不是在真实有限 beam、候选保留、访问去重、rewind 语义下计算成功概率。

### 执行序列与成本

保留 `btg_falsification_v1`、`v2`、`v3`、`v4` 全部报告。它们是诊断规则/选择门槛演进的版本，不是四次独立重复。超参数在同一训练 10K 的后 2K 上选择，随后读取两数据集 validation 10K；多版本反复使用 validation，最终 held-out 未访问。v1 共享选择为 h=1、temperature=0.5、gamma=0.5、margin=0.1；最终 v4 共享参数为 `cross_stay=0, horizon=4, temperature=0.25, gamma=0.1, margin=0`。

| 版本 | 原报告中的修订与结果 |
| --- | --- |
| v1 | 使用上述 h1 共享配置；WebVid validation ΔU=+0.001896，Yandex=-0.001343，跨数据 gate 失败。 |
| v2 | 显式采用 shared minimax 选择：先最大化两训练 dev 中较小的 utility 增益，再比较平均增益、较低 NDC 与改道率。选择改为 h4/temp0.25/gamma0.1/margin0；两数据集 validation ΔU 都微负。 |
| v3 | 主 gate 改为各数据集分别 train-only 选择配置；shared 配置单列为更严格的迁移诊断。WebVid 单独 PASS、Yandex FAIL，最终仍 NO-GO。 |
| v4 | 与 v3 小型 report 的数值、配置、decision 及 routes SHA 一致；记录差别是 analysis_script SHA、输出版本路径和 wall。它保留最终版本身份，不是新的性能提升或独立重复证据。 |

这些版本的 `report.json` 中 `framework_version` 仍沿用 `btg_falsification_v1`。识别版本时应同时看目录、analysis、具体 gate 与 implementation SHA，不能仅凭沿用字段把 v2–v4 合并；旧 report 不回写覆盖。

最终 v4 预设 gate 为 utility 增益 > 0.0001、每档 L Recall 不下降、各数据集平均 NDC 增幅不超过 0.5%。

| v4 选择方式 | WebVid | Yandex | 判定 |
| --- | --- | --- | --- |
| 两数据集共享参数 | ΔU=-0.000081；切换 3.58%；Recall Δ=+0.002/-0.010 pp；NDC Δ=+0.064/+0.029% | ΔU=-0.000049；切换 4.41%；Recall Δ=-0.010/+0.009 pp；NDC Δ=+0.066/+0.032% | 共享 gate 失败 |
| 各数据集按各自训练集选择 | ΔU=+0.001896；切换 22.74%；Recall Δ=+0.163/+0.185 pp；NDC Δ=-0.327/-0.131% | ΔU=-0.001831；切换 43.14%；Recall Δ=-0.210/-0.102 pp；NDC Δ=+0.483/+0.317% | WebVid PASS、Yandex FAIL，仍非跨数据方案 |

WebVid 转移图构建报告约 32.66 s，其中加载约 31.27 s、BFS 0.787 s、计边 0.597 s；815 个 hub 覆盖约 2.505M 个 base 节点，最大 BFS hop 为 8。报告里的大量 invalid slots 是固定邻接数组的 padding 计数，不能解释成已发现大量错误图边。分析脚本 wall time 或离线扩散耗时也不是部署搜索 QPS。

### 结论与承接

四版最终均没有建立可迁移的成本收益。BTG 分支收束为 NO-GO；局部 WebVid 有效不够支持共享机制。证据更具体地指出：raw graph basin connectivity 与有限预算实际搜索效用之间仍有错位，下一步若研究可达性，应直接检查候选池截断、拒绝插入、rewind 等有限 beam 事件，而不是继续扩大同一扩散参数网格。对应后续诊断见 [06](06_finite_beam_and_atlas.md)。

证据：[BTG 构建代码](../benches/build_basin_transition_graph.cpp)、[诊断实现](../benches/run/run_basin_transition_falsification.py)、[v1 分析](../basin_transition_diagnostics/btg_falsification_v1/analysis.md)、[v2 分析](../basin_transition_diagnostics/btg_falsification_v2/analysis.md)、[v3 分析](../basin_transition_diagnostics/btg_falsification_v3/analysis.md)、[v4 分析](../basin_transition_diagnostics/btg_falsification_v4/analysis.md)。同目录 report/manifest 保留选择配置、指标与来源校验和；精确来源以实际文件为准。

## 7. 可沿用与不可沿用的结论

可沿用的是：候选内存在效用空间；单 centroid、低容量效用 ranker、局部模式校正、raw-topology 扩散均未给出一致的跨数据成本收益；utility residual 有窄范围微弱正信号。不可沿用的是：所有表示都失败、oracle 已可部署、三次 timing 等于三次构建、graph NDC 降低就证明 QPS 提高，或在改了原型/候选/度量/GT 后复用不兼容的旧标签。这些历史产物保留用于追溯，不自动授权重启实验。
