# NETG / ACSG 当前研究状态与投稿路线

> 最后核对：2026-08-30。本文件只保留当前有效的研究判断、结果边界和下一步。实现路径、数据契约与重跑依赖见 `spec.md`；ACO/Router 历史诊断见 `aco_router_fast_entry.md`；完整双数据集结果见 `fast_entry_benchmark_results/benchmark_summary.md`。

## 当前结论

项目当前主方法已从旧的 `ACO -> DPC -> probe labels -> Neural Router` 转为：

> **QGT-Cover + closed-form GT-basin prototype：冻结 NSG 上的超低成本 query-guided 多入口层。**

它使用独立训练 query 的 exact GT 选择少量 base nodes 作为入口，并用另一组独立训练 query 生成闭式 prototype；在线从 prototype Micro-HNSW 选择 top-3 entry，再搜索原 NSG。它不修改底图，不运行 ACO、DPC、逐 hub probe labels、optimizer 或 MLP。

当前证据支持：

- WebVid-2.5M：Fast Prototype 相对 Formal Neural 同时改善 Recall、Medoid 归一化 QPS 和逐 query tail。
- official Yandex T2I-10M/IP：Fast Prototype 基本复现 Formal Neural 的 Recall，并获得小幅 QPS 优势。
- 两个数据集、全部测试 `L` 和预注册 tail 阈值上，Fast 相对 Medoid 都是正净救回；但 newly-harmed 始终非零。
- Selective reroute 的 L10 failure detector 有效，但静态、frontier 和冻结图一/二跳 topology-aware alternate chooser 均严格失败；该改进分支已停止，不进入 held-out test。
- standalone GATE 已在同一 WebVid 冻结图、raw-IP、独立 prototype-train/validation 上完成可复现适配；它在全部 12 个 validation 点优于 Medoid，但 Recall 全部低于 Fast 且 graph NDC 更高，因此按预注册 gate 不同步 Yandex。
- 第三数据集 LAION-10M 的 unit-cosine 数据、独立 split、exact GT、manifest 与冻结 NSG 已完成；尚无 Fast 结果，不能提前计作第三数据集证据。
- 这些结果证明 query-guided entry layer 有效，尚未证明 TailRisk-Cover 等下一代方法有效，也不能保证 A/B 类录用。

## 已解决的问题

以下问题只属于旧配置或旧流水线，不再是当前正式实验的待办：

1. **监督 query 与 test query 重合：已解决。** WebVid 和 official Yandex 均使用物理分离的 ACO/QGT-train、Router/prototype-train、validation、held-out test 文件；manifest 的六组两两 query overlap 均为 0。
2. **Yandex metric 混乱：已解决。** 当前正式键 `yandex_t2i_official10M_ip_v1` 使用官方 first-10M base、inner product、无归一化和匹配的 exact-IP GT。旧 `yandex_t2i` custom-L2 只保留为历史数据，禁止混用。
3. **逐 query 身份丢失：已解决。** 当前 Medoid、Raw、Neural/Fast 分支均保存排序前的 `per_query_recalls_aligned`；rescued/newly-harmed 只从对齐数组计算。
4. **只有单次轻量结果：已解决。** 当前权威批次是 Formal 每点 3 runs、Fast 三个 build seeds 且每 seed 3 timing runs，统一使用 held-out 10K。
5. **ACO 的 IP 数值语义：历史链已修复并完成 sanity 回归。** 但 Fast 主方法不依赖 ACO，因此不再把继续优化 ACO 作为主线。

旧五数据集配置、旧 Yandex-L2 图表和早期单次 `*_light.json` 仍可用于追溯，不能进入新论文主结果。

## 当前正式数据契约

| 数据集 | metric / normalization | QGT-train | prototype-train | validation | held-out test |
| --- | --- | ---: | ---: | ---: | ---: |
| WebVid-2.5M | IP / source near-unit, no extra normalization | 5K | 30K | 10K | public 10K |
| Yandex T2I official 10M | IP / none | 5K | 30K | 10K | public 100K 文件；当前评测固定前 10K |
| LAION-10M（底图完成） | cosine/IP / explicit L2-unit base+queries | 5K | 30K | 10K | public 10K |

权威 manifest：

- `benches/datasets/WebVid2.5M_light_v1/manifest.json`
- `benches/datasets/YandexT2I_official10M_ip_v1/manifest.json`

- `benches/datasets/LAION10M_acsg_v1/manifest.json`

LAION manifest 已通过 shape、checksum、六组 overlap 和官方 GT 抽样复算；冻结 NSG
也已完成并验证 identity/连通性，但 Fast 尚未构建/评测，因此不能引用 Fast 搜索结论。

任何 base、metric、normalization、split、GT 或底图变化都会产生新 artifact identity，并使受影响的 hub/prototype/结果失效。

## 当前权威结果

完整数值、原始 JSON、CSV 和图统一位于 `fast_entry_benchmark_results/`。以下只保留结论范围：

### WebVid-2.5M

- Recall@1：Fast Prototype 相对 Formal Neural 提高约 `+0.0080 ~ +0.0131`。
- Recall@100：提高约 `+0.0021 ~ +0.0032`。
- Medoid 归一化 QPS：Recall@1 曲线提高约 `+1.15% ~ +9.67%`；Recall@100 曲线提高约 `+1.83% ~ +8.89%`。
- Recall@10 tail：Fast 在所有 `L`、阈值 `0.1/0.2/0.5/0.8` 上均为正净救回，并总体优于 Formal Neural。

### Yandex T2I official 10M/IP

- Recall@1：相对 Formal Neural 差值约 `-0.00213 ~ +0.00003`，属于基本等效而非全面超过。
- Recall@100：差值约 `-0.00020 ~ +0.00018`。
- Medoid 归一化 QPS：Recall@1 曲线提高约 `+1.34% ~ +7.16%`；Recall@100 曲线提高约 `+1.14% ~ +5.53%`。
- Recall@10 tail：相对 Medoid 所有测试点均为正净救回；与 Formal Neural 总体接近。

原 ACO+DPC+labels+Router 的 query-dependent 阶段在 WebVid 合计约 `6501.94s`；Fast 冷构建约 `12~17s`。该倍率**不包含 exact train-GT 的生成成本**，论文必须单独报告 GT 成本与 break-even。

## LAION-10M 接入：数据、GT 与冻结 NSG 已完成

2026-08-30 实测服务器有约 `123 GiB` RAM（约 `120 GiB` available）和 `93 GiB`
可用数据盘；`/data/netg.tar.gz` 约 `49.5 GiB`。采用 10 个 fp16 image shards、1 个
text shard 和流式 fvecs 转换后，现有空间足够，因此压缩包暂未删除。

后台流水线 `benches/run/run_laion10m_acsg_v1.sh` 的 PID 写在
`logs/laion10m_acsg_v1/pipeline.pid`。下载已在约 19 分钟完成；正式 unit-cosine prepare
用时 `26:12`、最大 RSS 约 `58.4 GiB`，manifest 的六组 query overlap 均为 0，官方
first-32 exact set Recall@100 为 `1.0`。`R64/L_build100/C512` NSG 随后以 wall
`1:04:22`、max RSS 约 `73.1 GiB`、exit 0 完成；图覆盖 `10,004,480/10,004,480`
nodes 且 connectivity repair 后完全连通。索引为 `23,130,357,863 bytes`，`.info` 的
IP、explicit-unit normalization 和 artifact version 均与 manifest 一致；NSG SHA256 为
`7040cd0a2b8f5d34b3e3affbbcb30ce19c947731a8a81c40ec64f0e0d99bb238`。

当前需要写清的研究结论是：

- RoarGraph 官方所谓 LAION-10M 实际按 shards `0..7,9,10` 拼接，共
  `10,004,480 × 512` image vectors；本项目保持这一精确顺序，不擅自裁成 10,000,000。
- LAION fp16 vectors 只是近单位范数。raw-IP 对官方 top-100 的 32-query 复算为
  `0.994375`，raw-L2 为 `0.9909375`；对 base/query 显式逐行 L2-normalize 后 cosine/IP
  为 `1.0`。因此正式契约是 explicit-unit cosine/IP；首轮 raw-IP base/GT 已标记 INVALID，
  不能与正式图或结果混用。
- 官方旧 `the-eye.eu` 下载地址已失效；当前使用 LAION 官方部署镜像，公共 query/GT 仍取
  RoarGraph Zenodo record 11090378，并通过大小、NPY shape/dtype、MD5/SHA256 和官方 GT
  抽样复算验证。
- ACSG 只需 45K 历史 query，因此从官方 `text_emb_0.npy` 的 1,000,448 rows 中固定种子
  去重抽取 5K/30K/10K；不会伪装成使用 RoarGraph 全 10M training-query workload。
- **LAION public 10K query 与 WebVid public 10K query 的 MD5 完全相同
  (`af1343dc...`)。** 因而 LAION 是新的 10M image corpus / frozen-index control，能检验
  base corpus 与规模迁移，但不是完全独立的 held-out query workload。即使 Fast 在 LAION
  成功，也只能增强跨 corpus 证据，不能单独满足 A 类所需“第三个独立任务”；仍需强基线、
  成本消融，最好再补独立 query workload。
- 当前只有数据/GT/底图结论，没有 LAION Fast Recall/QPS/tail 结论；不得把“底图完成”写成方法有效。

## Git 源码备份状态

为避开当前本地 `main` 历史中误纳入的数 GB 数据/build blobs，源码快照从干净的
`origin/main` 单独生成，local ref 为 `research/core-source-20260830`。快照覆盖 ACSG/MRNN
C++、全部实验 C++/Python/shell、dataset settings、GATE baseline 适配、测试和交接文档，
共 221 files / 约 1.65 MB；明确不含数据、索引、模型、结果、日志、PDF、图片或 build。
用户指定并授权的新目标仓库是 `https://github.com/VoidFantacy/netg.git`，本地 remote 名为
`voidfantacy`。GitHub 连接账号 `VoidFantacy` 的 admin/push 权限已验证；221-file tree 通过
Git Data API 上传到独立远端分支 `research/core-source-20260830`，远端 tree SHA 与本地快照
完全一致。仓库 `main` 未改动，也未上传数据/build 历史。服务器 CLI 仍无凭据，但不影响
已完成的 GitHub connector 上传；后续更新继续只操作独立分支。

## 方法定位与相关工作边界

最接近的方法是 GATE（KDD 2025）：HBKM hubs、hub 子图拓扑特征、历史 query×hub 搜索生成正负样本、双塔增强 hub 和高层导航图。因此，“query-aware hubs”或“在冻结图上加一个入口导航层”本身不再新颖。

其他边界：

- RoarGraph、RobustVamana/OOD-DiskANN：利用历史 OOD query 修改底图，是端到端强基线，不是本项目的方法方向。
- Steiner-Hardness：提供图原生 query hardness，可用于独立分层。
- SOAR：启发多个入口应互补失败，而不是只取最相似的 top-3。
- 文献 PDF 与详细比较：`papers/related_work_2026-08-29/README.md`。

论文核心保持为：

> **不修改冻结底图，通过 query-aware、tail-aware、budget-aware entry selection 改善 OOD/cross-modal 图搜索。**

Graph repair 只作为相关工作、竞争基线或 future work，不是 oracle 失败后的自动转向。

## Selective Reroute 最终结论：停止当前改进分支

current-hub oracle、静态 listwise 和 budgeted probe 实验表明：候选中有上限，L10 trace
能判断“是否需要换”，但当前方法不能判断“应换到哪里”。最后的冻结图 topology gate
进一步加入候选相对 L10 probe frontier 的一/二跳邻接、重叠、rank-weighted hit、hop proxy
与 degree，共 7 维 GT-free 候选特征；训练/validation 仍为独立 10K，预算与风险模型不变。

WebVid top-risk 20% 的结果：

| Chooser | Target L=64: Recall / NDC delta | Target L=128: Recall / NDC delta |
| --- | ---: | ---: |
| topology-conditioned | `-3.577 pp / +2.402%` | `-1.381 pp / +0.860%` |
| frontier + topology | `-3.371 pp / +2.668%` | `-1.416 pp / +1.036%` |
| alternate oracle | `+0.103 pp / -0.455%` | `+1.286 pp / -0.779%` |

两个 learned chooser 在 `10/20/30/50%` 四个比例、两个预算上全部同时降低 Recall、增加
NDC，故不是阈值问题。按预注册 gate 不再运行 Yandex chooser，停止 resumable search、
更多通用树/MLP/双塔、broad hubs 和 graph repair。该 topology chooser 结果本身不等于
GATE 结果；下述 standalone GATE 已通过另一条同图、独立 split、raw-IP 流水线单独验证。

## Standalone GATE 强基线：WebVid 已完成，停止同步 Yandex

GATE 已适配到当前 `R64/L_build100/C512` 冻结图：精确导出 2,505,000-node NSG，修复
inner-product distance contract；512 个 HBKM hubs 使用可扩展 Sinkhorn balanced assignment，
每个 hub 采样严格 1,000-node topology-only 子图，再用确定性的 WL(2)+Doc2Vec(512d)
Graph2Vec。Graph2Vec 独立重复的 `.npy` SHA256 完全一致。需注意：上游将 Graph2Vec 留作
外部步骤，HBKM 论文伪代码是顺序 assignment；因此这是完整、可复现的工程适配，不宣称与
作者私有产物 bitwise identical。

训练使用独立 prototype-train 前 10K 与 exact-IP top-1 GT，validation 10K 只用于选
checkpoint；10K 中可用 triplet query 为 8,150，形成 652,600 pairs。原逐 triplet 前向
1 epoch 需 `9m49s`，按 batch 内唯一 hub 合并等价重复计算后为约 35s。正式配置
`max=200/patience=20` 在 88 epochs 早停，最佳 epoch 68，validation RouteAcc
`9.64%`；raw hub cosine 的同口径 RouteAcc 为 `20.49%`，显示 learned embedding 未超过
原始 hub 几何。

冻结图 validation 10K × 3 runs 的最终结果（GATE/Fast 均 top-3）：

| Recall | L | GATE - Fast | GATE - Medoid | GATE vs Fast graph NDC |
| --- | ---: | ---: | ---: | ---: |
| @1 | 64 / 128 / 200 / 400 | `-3.230 / -2.560 / -1.970 / -1.360 pp` | `+2.580 / +2.080 / +1.300 / +0.910 pp` | `+16.59 / +8.77 / +5.79 / +2.83%` |
| @10 | 64 / 128 / 200 / 400 | `-2.219 / -1.899 / -1.336 / -0.802 pp` | `+1.993 / +1.513 / +1.015 / +0.785 pp` | 同上 |
| @100 | 100 / 128 / 200 / 400 | `-0.828 / -0.817 / -0.563 / -0.330 pp` | `+0.908 / +0.835 / +0.577 / +0.485 pp` | `+11.06 / +8.77 / +5.79 / +2.83%` |

结论：GATE 在当前冻结图上是有效入口层，但严格被 Fast 支配；继续训练也不能解释
current-hub oracle headroom。按计划停止 Yandex GATE 复制，把它保留为 WebVid 强基线和
方法边界证据。完整 provenance、实现差异和路径见
`gate_baseline_artifacts/webvid2_5m_frozen_r64_v2/analysis.md`。

## 实现前的 oracle gate

不重建 `L_build=500` 底图。此前把 RoarGraph 的 `L_pjpq=500` 等同于 NSG `L_build=500` 是不可靠的参数对应；当前正式 NSG `R64/L_build100/C512` 继续冻结使用。

先在 validation 上、同一冻结图中比较：

1. Medoid；
2. 当前 QGT/Fast；
3. current-hub single oracle；
4. current-hub diverse top-3/top-5 oracle；
5. broad sparse-candidate single oracle；
6. broad sparse-candidate diverse top-3/top-5 oracle。

Oracle 只改变搜索起点，不添加、删除或重连底图边。比较必须计入 routing 和多个初始入口的成本，并同时报告等 `search_L`、等总 NDC、等端到端 latency。

结果解释：

- current-hub oracle 有上限：改 router/utility。
- current-hub 无上限、broad oracle 有上限：改 hub coverage。
- single 无上限、diverse 有上限：支持互补多入口主线。
- broad diverse 也无上限：该数据集/底图/预算下 entry-only 无法继续改善，应收窄论断或停止该改进；**不自动转成 graph repair**。

### WebVid current-hub pilot 结果（validation 1K）

结果：`oracle_entry_diagnostics/webvid_validation_1k_current_hubs_v1/results.json`。在
`L=64/128/200/400` 上，single oracle 相对当前 Fast 的绝对 Recall 增益分别为：

| Recall | L=64 | L=128 | L=200 | L=400 |
| --- | ---: | ---: | ---: | ---: |
| @1 | +27.50 pp | +19.40 pp | +16.00 pp | +11.70 pp |
| @10 | +15.01 pp | +11.49 pp | +9.59 pp | +6.80 pp |
| @100 | +6.74 pp | +6.24 pp | +5.08 pp | +3.55 pp |

Recall@1 的 oracle graph NDC 还比 Fast 低 `2.31%~10.26%`；Recall@10 基本等 NDC；
Recall@100 则多用 `3.68%~12.45%` graph NDC。12 个点上 greedy top-3 均低于
single oracle，下降 `1.75~4.86 pp`，说明固定 `L` pool 内存在明显多入口预算干扰，
尚不支持当前 diverse top-3 实现。每个点选中的 single hubs 有 `506~563` 个，最热
hub 只覆盖 `0.6%~1.0%` queries，说明不是少数全局热入口，而是细粒度 query-entry
匹配问题。

因此 current-hub gate 已通过：不需要先扩 broad candidates，更没有理由修底图；下一步
应做 search-aware single-entry utility learning。该 pilot 是使用 GT 逐 query 选择的上限，
不是可部署结果；只有 validation 1K，未保存逐 run 方差/逐 query tail，routing cost 也未
计入，不能直接进入论文主结果。

### Search-aware hard-label prototype gate

随后使用独立 prototype-train 前 5K，在 `L=64/Recall@10` 对 current 815 hubs 穷举
single oracle；809 个 hubs 获得至少一个标签。按 oracle hard label 对 query 求球面均值，
加入与当前 Fast 相同的 raw-hub prior=1，得到闭式 search-aware prototypes。

在 validation 1K 全 12 点上：

- prototype top-3 相对 Fast top-3，Recall@1/10 的 8 个点全部提高 `+0.35~+0.82 pp`，
  graph NDC 增加 `0.36%~0.71%`；Recall@100 仅 `-0.078~+0.189 pp`。
- prototype top-1 的 Recall@1 全部下降 `0.2~0.7 pp`，Recall@100 全部下降
  `0.066~0.379 pp`；只有 Recall@10 为 `0~+0.61 pp`，且 NDC 增加 `0.95%~3.08%`。

结论是：真实搜索 oracle 标签有信号，但压成单个 hard class 再求 centroid 只能取得弱增益，
无法解释前述巨大 oracle headroom。top-3 对不完美预测器仍起容错作用；这不推翻 exact
single oracle 的上限结论。**停止 oracle-label centroid 路线，不继续扫 prior 或扩大通用
分类器。** 下一方法必须保留 shortlist 上的连续 Recall/NDC utility，学习 cost-aware
listwise ranking/边际收益；不能退回单标签分类，也不转 graph repair。

### Continuous utility prototype 与静态 listwise gate

在 WebVid 和 Yandex 的独立 prototype-train/validation 各前 10K 上，对 Fast top-32
记录 `L=64/128, Recall@10` 的 single-entry Recall/NDC utility。闭式 signed
utility-residual prototype 在 WebVid validation 10K 的 12 点均为正，但只提高
`0.030~0.114 pp`，NDC 降低不足 `0.08%`，判定幅度不足。

随后使用三 seed 对角 query/prototype/raw-hub interaction listwise reranker：

- WebVid 等成本近似对齐后仍有小幅正增益：`L=63 vs Fast L=64` 为
  `+0.027~+0.100 pp`，`L=127 vs Fast L=128` 为 `+0.125~+0.218 pp`。
- Yandex 同 `L` 仅 `-0.042~+0.202 pp`，却增加 `1.78%~3.31%` NDC；降至
  `L=62/126` 后，低预算三 seed 全部同时低 Recall、高 NDC，高预算也基本无增益。

因此静态几何 listwise ranker **跨数据集 no-go**。不能据 WebVid 的小正值扩大成通用
MLP/双塔：这会接近 GATE 而没有新的实证机制。与此同时，两数据集 top-32 shortlist
oracle utility 均明显高于 Fast rank-0，说明失败的是静态可预测性，不是候选 headroom。
下一方向转为使用在线小预算 graph trace 的 selective probe-then-reroute；仍不修改底图。

### Budgeted probe-then-reroute v1

公平协议只使用实际付费的 `L_probe=10` trace。早期同时使用独立 `L=10/16/32`
trace、但只计 L10 成本的结果已作废，仅可作为诊断。有效结果：

- WebVid：router-only AUROC/AUPRC `0.584/0.468`，加入 L10 trace 后
  `0.660/0.557`；top-risk 10% 的 actionable 比例为 `65.6%`。
- Yandex：从 `0.620/0.337` 提高到 `0.759/0.469`；top-risk 10% actionable
  比例 `55.3%`。

learned risk + oracle alternate 的固定预算上限跨数据集存在：WebVid top-20% 在
低/高预算为 `+0.103/+1.286 pp` 且 NDC 均下降；Yandex 高预算 top-20% 为
`+1.359 pp, -0.589% NDC`，低预算需 top-30% 才转正。

但 learned alternate chooser 失败。WebVid frontier-conditioned 版本在 top-risk 20%：
低预算 `-3.412 pp, +2.593% NDC`，高预算 `-1.426 pp, +0.969% NDC`；同一批
query 的 oracle alternate 明显为正。即检测器会判断“该换”，但 prototype/raw-hub/
probe-result affinity 仍选不出正确入口。**probe-reroute v1 作为完整方法 no-go**；不继续
调当前树模型或扩大通用 MLP/双塔。有效组件是 failure detector，未解决瓶颈是 alternate
chooser。

## 下一步优先级

1. 冻结当前 QGT-Cover/Fast 方法，不再把 selective reroute 当作待调完整方法。
2. 在已完成的 LAION-10M 冻结 NSG 上构建 Fast，并先在 validation 验证；同时把它定位为同一 public-query、不同 image corpus 的 scale/corpus control，而非完全独立第三 workload。
3. 补齐 HNSW/NSG/LSH-APG 与 RoarGraph/RobustVamana 同机比较；WebVid standalone GATE 已完成。
4. 完成 hub budget、train-query 规模、GT top-1/10/100、prototype 必要性、hardness 分层和成本敏感性；重点验证结果显示 QGT-Cover 是主收益而 prototype 并非跨数据集稳定增益。
5. 补齐 exact train-GT 生成成本、index size、RSS、端到端 latency 与 break-even，再决定按 A 类完整方法还是 B 类低成本系统方案投稿。
6. graph repair 只作竞争基线/future work，不改论文“不修改冻结底图、只优化入口”的核心。

## 投稿级验收

冲击 KDD/VLDB/SIGMOD 等 A 类强度至少需要：

- 两个以上 OOD/cross-modal 主任务，在 held-out test、等 NDC/latency 下稳定优于当前 Fast 与 GATE；
- tail 改善不能由平均值掩盖，必须同时报告 rescued、newly-harmed、P1/P5 和 bottom-CVaR；
- 第三个任务或强 control、完整 build/search 成本、index size、RSS 和 break-even；
- 说明 exact train-GT 依赖，并提供 train-query/GT 成本消融或 trace-only 版本；
- 不修改底图的可插拔性和 query workload 适配成本形成明确 Pareto 优势。

若只能做到与 GATE/当前 Fast 效果相近但构建更快，更适合 B 类或系统/工业定位；不能仅凭现有结果承诺录用。

## 当前证据入口

- 实现与复现：`spec.md`、`command.md`
- ACO/Router 与 Fast 历史诊断：`aco_router_fast_entry.md`
- 双数据集结果：`fast_entry_benchmark_results/benchmark_summary.md`
- 机器表：`fast_entry_benchmark_results/search_metrics.csv`、`tail_metrics.csv`、`benchmark_summary.json`
- 相关工作与 TailRisk-Cover 设计：`papers/related_work_2026-08-29/README.md`
