# GATE 适配与比较基线准备复盘

核对日期为 2026-09-08。本页区分已实际完成的本地 GATE 同图适配、依赖级检查、尚未执行的基线复验。论文作者报告、安装成功和本地端到端性能是三类不同证据。当前实施范围以 [s-target.md](../s-target.md)为准，历史准备文档中的“恢复/下一步”不构成当前执行授权。

## 1. GATE 同图适配：为何做、具体改了什么

GATE 是冻结图上 query-aware entry navigation 的直接相关工作。比较目的，是在相同 WebVid NSG 上检验学习 hub embedding 能否取得比 Fast 更好的入口质量，而不是用作者论文在不同 metric/机器上的速度替代本地对照。

[本地 analysis](../gate_baseline_artifacts/webvid2_5m_frozen_r64_v2/analysis.md)固定：WebVid-2.5M、raw IP、R64/L_build100/C512 的原 ACSG NSG，不修边、不重建图；512 个 balanced HBKM hubs，真实 base ID；每 hub 1,000 节点 topology-only 子图；Graph2Vec 为 WL(2)+PV-DBOW 512d、seed42。平衡分配采用文档化 Sinkhorn，Graph2Vec 采用 gensim WL+Doc2Vec，是可复现的项目适配，不声称与作者未公开产物逐位相同。

此前 `hbkm512_seed42` 使用了 stale-size batched penalty：虽然输出 512 个 hub，最终簇大小却为 1～11,376，没有遵循 Algorithm 2 动态更新的 balance state。其 [INVALID.md](../gate_baseline_artifacts/webvid2_5m_frozen_r64_v2/hbkm512_seed42/INVALID.md)明确禁止用于 GATE 结果或论文表；该旧目录保留，不与下文有效的 `hbkm512_sinkhorn_seed42_v2` 合并统计。后来的 Sinkhorn 是显式记录的适配修订，并不因此变成作者算法的逐位复现。

模型训练用旧独立 prototype-train 的前 10K、exact-IP GT1；validation 10K 用于 checkpoint 选择并用于结果评估。在线使用 exact dense cosine top-3 hub embedding routing，再把真实入口交给同一冻结图搜索。它不是目前新方案的后 20K fit / 前 10K pilot 协议，也不是同 20K paired Fast 的重新比较。

## 2. 实际训练与已测结果

训练 10,000 queries 中 915 no-hit、8,150 usable，652,600 triplets；validation 10,000 中 904 no-hit、8,146 usable。最大 200 epochs、patience20，best epoch68，epoch88 停止。usable validation RouteAcc=0.0963663，raw-hub cosine RouteAcc=0.2048858；这是该标签上的入口命中率，不等于下游 Recall。当前 16-vCPU CPU 主机训练 wall 46m41.73s。

实际 validation 10K、每点三次 graph-search runs；R@1/10 的 L64/128/200/400，R@100 的 L100/128/200/400，合计 12 点：

| K / L | GATE−Fast Recall | GATE−Medoid Recall | graph NDC 相对 Fast |
|---|---:|---:|---:|
| 1 / 64 | −3.230 pp | +2.580 pp | +16.59% |
| 1 / 128 | −2.560 pp | +2.080 pp | +8.77% |
| 1 / 200 | −1.970 pp | +1.300 pp | +5.79% |
| 1 / 400 | −1.360 pp | +0.910 pp | +2.83% |
| 10 / 64 | −2.219 pp | +1.993 pp | +16.59% |
| 10 / 128 | −1.899 pp | +1.513 pp | +8.77% |
| 10 / 200 | −1.336 pp | +1.015 pp | +5.79% |
| 10 / 400 | −0.802 pp | +0.785 pp | +2.83% |
| 100 / 100 | −0.828 pp | +0.908 pp | +11.06% |
| 100 / 128 | −0.817 pp | +0.835 pp | +8.77% |
| 100 / 200 | −0.563 pp | +0.577 pp | +5.79% |
| 100 / 400 | −0.330 pp | +0.485 pp | +2.83% |

GATE 比 Medoid 有效，但在全部 12 个点 Recall 低于 Fast、graph NDC 更高，按当时 gate 停在 WebVid，不复制到 Yandex。这个结果保留为 standalone baseline；没有完成 GATE 的 Yandex/新 paired20K/当前纯 wall 全路由+搜索成本复验。不能把原报告的“dominated”扩写成未测的端到端 QPS Pareto 结论。

46m42s 只覆盖模型训练，不包括 GT/搜索标签、聚类、子图、Graph2Vec、索引准备。dense 路由也有在线成本，graph NDC 不等于 total NDC。本地失败说明当前静态拓扑/triplet embedding 未兑现该契约下的入口选择空间，不说明所有 query-aware entry 方法已耗尽潜力。

## 3. 作者原件与本地适配的区别

2026-09-08 已完成的[原文/作者源码核查](../entry_selection_research/20260908_v2/reviews/entry_papers_and_author_code.md)绑定 GATE release v0.0.1、commit `229f18dadb791ddede22597e44d5ceb028b104ba`，保留小型源码与 SHA 于 [download manifest](../entry_selection_research/20260908_v2/sources/author_entry/download_manifest.json)。本次整理复用该已完成审计，没有重新联网复验作者性能。

- 所核 release 在线直接把原 query 送入离线 hub embedding 的 cosine HNSW，没有在线 query MLP。因此 Fast 相对 GATE 不能笼统声称免去作者实现中的在线神经推理。
- 论文正样本阈值相对固定 hub 跨 query 的最小 hop；release 样本脚本实际按每 query 的最小 hub hop，未命中标为 999。release 启用 cosine triplet loss，InfoNCE 调用被注释。
- release hop 是有限搜索的首次发现路径长度，不是 NDC，也没有最短路径松弛，不能把它替换成严格最短路径或真实有限预算 Recall@10 效用。
- release 测试硬编码 L2，部分脚本有 CUDA 假设；本地 CPU/raw-IP、Sinkhorn、gensim Graph2Vec、10K 训练和 dense 路由均需明确标为适配。上述差异不否定作者论文结果，也不允许声称本地已完整重现作者实验。

## 4. 2026-09-07 比较依赖准备：完成的是环境与小检查

[准备 README](../hierarchical_target_search/20260907_v1/dependencies/README.md)与[manifest](../hierarchical_target_search/20260907_v1/dependencies/manifest.json)记录 `READY_FOR_PLAN_RESUMPTION`、`research_execution=PAUSED_BY_USER`、`research_experiments_run_this_preparation=false`。该准备轮仅下载/安装/编译及依赖级检查，没有真实分区、拟合、ANN pilot、validation 或 held-out。后来夜间批次在独立授权和目录中通过 P0/P1/P2、P3 NOPASS 后结束；不能让准备 README 的旧暂停/截止说明覆盖后来的最终 state。

下列路径均从项目根 `/data/netg/ACSG` 解析。现场已确认 `hierarchical_target_search/20260907_v1/tools/env.sh` 和 `hierarchical_target_search/20260907_v1/tools/roargraph-env.sh` 存在；项目根的 `tools/env.sh` 和 `tools/roargraph-env.sh` 不存在。为避免歧义，本表与环境说明统一写完整项目相对路径。

| 工具 | 已完成证据 | 尚缺的本地研究验收 |
|---|---|---|
| METIS v5.2.1 / GKlib | METIS commit `f5ae915a84d3bbf1508b529af90292dd7085b9ec`；idx_t64/real_t32；C API 六节点 smoke PASS；二进制与库在 `hierarchical_target_search/20260907_v1/tools/local/` | 安装 smoke 本身不等于分区/搜索收益；后续 P2/P3 独立记录 |
| 核心 Python | `.venv_cpu/bin/python` 原包版本未改，CPU 科学计算包可导入 | 不应为其他 baseline 覆盖该环境 |
| 基线 Python | `hierarchical_target_search/20260907_v1/tools/python/bin/python`；Faiss1.9.0、h5py3.14.0、transformers4.46.3、prettytable3.16.0；pip check/CPU 算子 PASS | `.pth` 只读复用核心大包，不意味着模型已适配；不能解析 symlink 后改用系统 Python |
| LIRA | commit `7beeee52d5b9a880f443876e24563713146ef581`；模型 CPU 合成 forward 可执行；源码在 `hierarchical_target_search/20260907_v1/tools/LIRA/` | 原主程序 CUDA 假设；CPU/raw-IP/数据与测量合同适配未完成，没有正式本地性能 |
| kRt / gp-ann | commit `df5efb4a6b303011c795666ed267f29d994b558c`；`MIPS_DISTANCE=ON` 构建与所需子模块；二进制在 `hierarchical_target_search/20260907_v1/tools/gp-ann/build/` | 原 README 的 HNSW metric increments 修改未应用；计数、raw-IP 与完整协议仍需审计，无正式性能复验 |
| RoarGraph | commit `7c9ef95dcb9b1022a2e3b8dfee55409ad73c605e`；build/search 帮助入口可执行；`hierarchical_target_search/20260907_v1/tools/RoarGraph/build/tests/` | 没有在当前两数据集完成本地端到端比较 |
| DiskANN exact GT 工具 | RoarGraph 内 `build/thirdparty/DiskANN/tests/utils/compute_groundtruth` 已编译，help 可用 | 准备轮未计算项目新 GT；不能由工具存在推出 GT 已生成 |
| GATE | 复用 `GATE/`、`GATE/build/tests/` 与现有 gensim 适配；动态依赖核验 | 上述 WebVid 项目适配以外的正式比较未完成 |
| RobustVamana / OOD-DiskANN、PyANNS 等后续建议 | 存在相关工作/基线讨论 | 当前材料不提供本地同机、同完整成本合同的正式结果；论文数字与建议不计入已完成实验 |

系统准备新增 15 个依赖包，原有包 0 升级/删除；局部 MKL2020.4/OpenMP 解包在 `hierarchical_target_search/20260907_v1/tools/mkl-sysroot`，没有安装为系统 BLAS。源码提交、二进制 checksum、包版本和保护结果以准备 manifest 为当时证据，不据旧记录推断当前机器所有环境从未变动。

## 5. 正确环境入口与成本边界

核心环境辅助脚本完整位置为 [env.sh](../hierarchical_target_search/20260907_v1/tools/env.sh)，只影响当前 shell；RoarGraph/DiskANN 的脚本是 [roargraph-env.sh](../hierarchical_target_search/20260907_v1/tools/roargraph-env.sh)，须仅在其独立子 shell 中启用。不要把局部 MKL/OpenMP 混入原 ACSG 构建与计时。原研究解释器仍是 `.venv_cpu/bin/python`，基线解释器另列。

GATE 必须显式提供现有 `cluster/graph2vec_embed.py` 的 gensim WL+Doc2Vec CSV，不能因为可选 karateclub 缺失而静默换成 mean pooling。依赖准备消耗、标签/模型离线成本、真实查询 wall 应分别报告；help/smoke/CPU forward 成功不构成方法或性能 PASS。

旧依赖 README 中磁盘余量、定时截止和继续安装说明均是 2026-09-07 准备阶段快照；本次文档整理没有安装、删除、重建或启动 baseline。新比较若获授权，仍须另冻结 metric/split/图/成本合同并按现有强基线要求执行。

## 6. 原始材料索引

- GATE：[analysis](../gate_baseline_artifacts/webvid2_5m_frozen_r64_v2/analysis.md)、[training report](../gate_baseline_artifacts/webvid2_5m_frozen_r64_v2/models_webvid_gate_uniquehub_max200_patience20_v4/training_report.json)、[route manifest](../gate_baseline_artifacts/webvid2_5m_frozen_r64_v2/routes_webvid_gate_max200_best_validation10k_top3_v1/manifest.json)。
- GATE 原始评测：[R@1/10](../gate_baseline_artifacts/webvid2_5m_frozen_r64_v2/eval_gate_max200_best_validation10k_r1_r10_3run_v1/results.json)、[R@100](../gate_baseline_artifacts/webvid2_5m_frozen_r64_v2/eval_gate_max200_best_validation10k_r100_3run_v1/results.json)；输入来源：[train samples manifest](../gate_baseline_artifacts/webvid2_5m_frozen_r64_v2/gate_samples_router_train10k_ip_l64_k1_v1/manifest.json)、[Graph2Vec manifest](../gate_baseline_artifacts/webvid2_5m_frozen_r64_v2/hbkm512_sinkhorn_seed42_v2/graph2vec_wl2_d512_e10_mc5_seed42_v1/manifest.json)。
- 环境准备：[README](../hierarchical_target_search/20260907_v1/dependencies/README.md)、[manifest](../hierarchical_target_search/20260907_v1/dependencies/manifest.json)、[历史夜间 state](../hierarchical_target_search/20260907_v1/state.json)、[夜间总结](../实验总结.md)。
- 作者与比较合同核查：[入口论文/源码审计](../entry_selection_research/20260908_v2/reviews/entry_papers_and_author_code.md)、[历史研究方向复审](../research_direction_review/20260908_v1/report.md)。
