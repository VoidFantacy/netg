# NETG / ACSG 当前实现规格

> 最后核对：2026-09-07。本文件只记录当前实现、数据/metric 契约、artifact、评测口径和重跑依赖。研究结论见 `summary.md`，本批协议与终局见 `s-target.md`，历史过程见 `aco_router_fast_entry.md`。

## 1. 权威性与保护边界

实现事实的证据顺序是：当前源码／配置／manifest／机器结果 > 本文件 > 总结、日志、旧 README、旧结果和远端分支。发现冲突时先报告，以验证后的当前实现为准；不能因远端提交时间较新而覆盖本地工作。

工作区含大量未提交源码和历史 artifact。禁止擅自 `git reset --hard`、`git clean`，禁止删除或覆盖旧索引、日志、结果、`*.bak` 和论文材料；新 variant 必须写入隔离目录。

文档职责固定：`spec.md` 管实现与复现契约；`summary.md` 管方法、结论与停止边界；`s-target.md` 管长期计划、阶段 gate、接续状态和交付。任何改变数据、split、GT、metric、图、方法、artifact schema 或结论的工作，都要同步核对 `spec.md` 与 `summary.md`。

## 2. 当前方法与调用链

### 2.1 Fast v1

```text
frozen NSG
  + 5K QGT-train queries + exact top-100 GT
      -> spherical k-means
      -> each cluster selects one unique real GT base node
      -> QGT-Cover raw hubs
  + independent 30K prototype-train queries + top-1 GT
      -> assign query to the nearest raw-hub GT basin
      -> normalized query mean + raw-hub prior
      -> closed-form GT-basin prototypes
  + online query
      -> Micro-HNSW over prototypes
      -> top-3 real base entry IDs
      -> ACSG::search_new on the unchanged NSG
```

QGT 是项目内术语 Query Ground-Truth；QGT-Cover 是 query-clustering 启发式，不是严格 set cover。prototype 是入口的“查询画像”，不是入口节点向量的复制。

Fast 不读取 ACO weights、DPC centers、probe labels 或 Neural Router bins，不运行 optimizer/MLP，不修改 NSG；但依赖 exact train GT。结果槽名 `Asym-Neural/NETG_AsymHNSW` 在 Fast manifest 中承载 closed-form prototype，不能据名称误报为神经模型。

### 2.2 Multi-view Target-Basin Routing（已完成成本否决）

当前 validation 版本把 seeds `20260828/20260829/20260830` 的三个 Fast build 作为一个模型的三个 view：保留 seed-20260828 Fast rank-0 作为 anchor；每个 view 取 top-8，重复 entry 按最高 cosine 合并；从并集选两个补充入口，最终仍以 top-3 搜索同一 frozen NSG。

在线不读取 GT、probe label 或 held-out。三个 view 是一个 ensemble instance，不是三次独立重复。E0 已统一路由、anchor、计数和计时契约；E1 的 dense 后端成本失败后，E1b 将后两 view 固定为 `M16/efConstruction200/efSearch32` Micro-HNSW、top-8 exact rerank。

E1b 在双数据集 train-10K 的四个等 total-NDC 点均低于 paired Fast Recall，已按停止规则定为 `NO_GO_ROUTING_COST`。该扩展不进入独立构建、tail、归因或 held-out；当前部署方法仍为 Fast v1。

## 3. 当前代码入口

新主线 `hierarchical_target_search/20260907_v1` 目前按用户要求暂停，依赖已准备，P0/P1 未通过。已保存修改前 checksum/源码快照，新增 `ACSG/RegionalSearch.h` 和 `benches/test_regional_search.cpp`；测试 target 已编译但尚未运行。分层区域、路由、区域池和新计时器尚未完成验收，不能视为已实现方法。新契约见第 13 节。

| 目的 | 入口 |
| --- | --- |
| Fast 构建 | `benches/run/build_fast_entry_variants.py` |
| 单／多 seed 验证 | `benches/run/run_fast_entry_validation.sh`、`benches/run/run_yandex_qgt_fast_light.sh` |
| 双数据集正式复验 | `benches/run/run_two_dataset_fast_benchmark.sh` |
| Three-view Python reference | `benches/run/route_multiseed_target_basin_ensemble.py` |
| Three-view C++ 路由／搜索 | `benches/bench_entry_oracle.cpp` -> `build/benches/bench_entry_oracle` |
| 部署一致的路由／计数／计时 | `benches/bench_target_basin_eval.cpp` -> `build/benches/bench_target_basin_eval` |
| Three-view merge reference | `benches/run/route_target_basin_reference.py` |
| 正式化阶段 runner | `benches/run/run_target_basin_protocol.py` |
| E1b 校验／汇总 | `benches/run/summarize_target_basin_e1b.py` |
| Recall/QPS | `benches/test.cpp` -> `build/benches/test` |
| 逐 query Recall@10 | `benches/bench_per_query_recall.cpp` -> `build/benches/bench_per_query_recall` |
| 汇总／绘图 | `summarize_fast_entry_multiseed.py`、`summarize_two_dataset_fast_benchmark.py`、`plot_two_dataset_qps_recall.py` |
| LAION 准备／验证 | `benches/run/{download,prepare,run}_laion10m_acsg_v1.*`、`run_laion_fast_{validation,heldout}.sh` |
| 复现命令 | `command.md` |

旧链 `NSG -> ACO -> DPC -> probe labels -> Neural Router` 只作历史复现，入口为 `bench_ACO_TEST`、`kph_dpc_clustering`、`bench_generate_labels`、`train_router.py`。它不是默认方法；legacy ACO-Max 的 weight 生命周期问题修复前不能作为有效基线。

## 4. 构建环境

最后核对环境：Ubuntu 22.04、16 vCPU、约 123 GiB RAM、无 swap、无 GPU；项目在 `/data/netg/ACSG`，Python 环境为 `.venv_cpu/`。

```bash
source .venv_cpu/bin/activate
cmake -S . -B build -G Ninja \
  -DFAISS_ENABLE_GPU=OFF \
  -DFAISS_ENABLE_PYTHON=OFF \
  -DBUILD_TESTING=OFF
cmake --build build -j 16
```

必须配置根工程，不使用 `SSG/build`。复用旧命令前先运行目标程序的 `--help`；大文件只写入 `/data`。

## 5. 正式数据集契约

| 数据集 | WebVid-2.5M | Yandex official 10M/IP | LAION-10M/IP |
| --- | --- | --- | --- |
| key | `webvid2_5m_light_v1` | `yandex_t2i_official10M_ip_v1` | `laion10m_acsg_v1` |
| artifact version | `roargraph-webvid2.5m-ip-v1` | `yandex-t2i-official-first10m-ip-v1` | `roargraph-laion10m-unit-ip-acsg-v1` |
| base | 2,505,000 × 512 | first 10,000,000 × 200 | 10,004,480 × 512 |
| metric | inner product | inner product | inner product |
| normalization | source 近单位范数，不额外归一化 | none | base/query 逐行 L2-unit |
| QGT / prototype / validation | 5K / 30K / 10K | learn `[0,5K)` / `[5K,35K)` / `[35K,45K)` | seed 20260830 去重抽取 5K / 30K / 10K |
| held-out | public 10K | public 前 10K | public 10K |
| manifest | `benches/datasets/WebVid2.5M_light_v1/manifest.json` | `benches/datasets/YandexT2I_official10M_ip_v1/manifest.json` | `benches/datasets/LAION10M_acsg_v1/manifest.json` |

补充边界：

- WebVid、Yandex 四个 split 的六组两两 overlap 均为 0；Yandex GT 必须对应 first-10M base 的 exact IP top-100。
- LAION held-out GT 来自 DiskANN truthset top-100 IDs，并以 unit-normalized exact IP 抽样复核；未带 `.unit`／`.unit_ip` 的首轮 raw artifact 已失效，见 `INVALID_RAW_IP.md`。
- LAION 与 WebVid public-query 源文件 MD5 相同，因此 LAION 只能算不同 base corpus/scale 的迁移控制，不是独立第三 query workload。
- `sift10M`、`sift10M_skewed`、`deep10M`、`gist1M` 和旧 `yandex_t2i` 不属于当前正式协议。

## 6. 冻结底图

三个正式数据集均使用 `R=64, L_build=100, C=512`：

| 数据集 | NSG |
| --- | --- |
| WebVid | `indices/webvid2_5m_light_v1_index/acosp_nsg.json` |
| Yandex | `indices/yandex_t2i_official10M_ip_v1_index/acosp_nsg.json` |
| LAION | `indices/laion10m_acsg_v1_index/acosp_nsg.json` |

同目录 `.info` 必须匹配 dataset version、metric 和参数。不得把 RoarGraph 的 `L_pjpq=500` 当成重建 NSG `L_build=500` 的依据。WebVid 固定宽度图中的 `-1` 是未用 padding，不是坏边；导出 variable-degree 图时只过滤 padding。所有方法比较必须绑定相同图 checksum。

## 7. Artifact 与 provenance

单 seed Fast 目录：

```text
fast_entry_variants/<dataset>_seed<seed>/
  manifest.json
  qgt_cover_hubs.bin
  qgt_cover_hub_ids.bin
  qgt_gt_basin_prototype_hubs.bin
  eval_r1_3run.json
  eval_r100_3run.json
  per_query_r10.json
```

正式 Fast seeds 为 `20260828/20260829/20260830`；hub budget 为 WebVid 815、Yandex/LAION 821。manifest schema v2 至少记录 dataset/artifact version、split、metric、normalization、query/GT/base/graph path 与 checksum、seed、hub budget、参数、输出 checksum、代码版本、CPU/线程和时间。

现有 manifest 的 base 字段只是路径，新正式批次必须补 base 与图 checksum。seed 位于 `variants.qgt_cover.seed`；不同 seed 只改变相同训练样本上的 k-means 初始化，不是 query bootstrap。builder 会写入已有目录，外层 runner 必须预先拒绝冲突。

`build_wall_seconds` 只计已有 exact GT 后的 builder，不含 exact GT 和 evaluator 内构建的 Micro-HNSW。完整离线成本必须分项：

```text
T_offline_single = T_exact_train_GT + T_QGT + T_prototype + T_router_index
T_offline_ensemble = T_exact_train_GT + sum_views(T_QGT + T_prototype + T_router_index)
```

三 view 共用 train GT 时只计一次；缺失阶段写 `null + reason`。不得把 post-GT 秒级时间称为完整训练。

已知无效 artifact：`fast_entry_variants/webvid2_5m_light_v1/eval_qgt_vs_prototype_r1.json` 的 raw task 曾发生 vector/ID 错配；LAION 首轮 raw-IP/raw-L2 也已失效。两者禁止进入新汇总。

## 8. 在线搜索与评测

`benches/test.cpp` 的 `--query_split drl_test|validation` 显式选择 split，默认 `drl_test`；结果必须记录实际 split。`--test_scope comparison` 只运行 Medoid、Raw 和 prototype comparison slots。IP 数据的 Raw routing 使用 IP。

Recall@K 为返回 top-K 与 exact top-K 的集合交集数除以 K；必须 `search_L >= K`，因此 Recall@100 首点为 `L=100`，禁止 `K=100/L=64`。

正式 Fast 协议：held-out 10K；Formal 每点 3 timing runs；Fast 3 build seeds × 每 seed 3 timing runs；Recall 方差来自 build seeds，QPS 方差来自 timing runs 与 seeds；跨 invocation QPS 优先使用同次 Medoid 归一化；tail 阈值固定 `0.1/0.2/0.5/0.8`。

逐 query 数据必须按 query ID 保存未排序 aligned 数组。CDF/分位数可排序，但 rescued、newly_harmed、still_failed 和 paired bootstrap 只能使用 aligned 数据；timing runs 不是独立 Recall 样本。

计时／计数契约：

- 分别记录 routing、graph、total 的 NDC 与 latency，`total_ndc = routing_ndc + graph_ndc`；
- QPS 用单方法独立整批 wall，不能由 16-thread 逐 query latency 均值倒推；
- tail、GT 评分、hash 和 JSON 写盘不进入计时；
- 若计数 instrumentation 有开销，以结果一致的独立计数进程提供 NDC；
- 固定 warm-up、轮换方法顺序，并记录线程、CPU 和 cache condition。

旧 Three-view JSON 仍是 graph-only、单 run；routing batch wall 与线程内 graph mean latency 不可相加。`bench_target_basin_eval` 已分离 count/timing 接口，并在 E0 与旧 search 的 entry IDs、result IDs、Recall 和 graph NDC 一致；但后续源码审计确认 `evaluate_query` 的 GT 评分仍在整批 timer 内，线程工作区也在 timer 内创建，旧 E0 未覆盖这两项。旧 count 文件的 QPS 不可发布，新协议必须通过独立纯计时审计。旧 E1/E1b 的 NDC no-go 不因此改变。

## 9. 权威结果入口

- WebVid/Yandex Fast：`fast_entry_benchmark_results/{benchmark_summary.md,benchmark_summary.json,search_metrics.csv,tail_metrics.csv}`，原始结果在 `raw/<dataset>/`。
- LAION：`fast_entry_variants/laion10m_acsg_v1_{validation,heldout}_report.md` 及对应 multiseed summary/seed 目录。
- Three-view：`target_basin_ensemble_diagnostics/v1/decision.json`。
- 正式化 E0：`target_basin_formalization/20260907_v1/audit/report.json`。
- 正式化总 gate：`target_basin_formalization/20260907_v1/{gate.json,report.md}`；E1b 细节为 `pilot/hnsw/report.json`。
- Confidence-attention：`target_basin_meta_diagnostics/v1/decision.json`。
- GATE WebVid：`gate_baseline_artifacts/webvid2_5m_frozen_r64_v2/analysis.md`。

结果数值与研究解释只在 `summary.md` 维护，本节只定义入口。

## 10. 重跑依赖

| 变化 | 可复用 | 必须重跑 |
| --- | --- | --- |
| base、metric、normalization、图参数/后端 | 原始下载与兼容 checksum | GT（语义受影响时）、NSG、Fast、全部评测 |
| QGT/prototype split 或 train GT | 兼容 base 与 NSG | hubs/prototypes、全部评测 |
| hub budget、clustering、prototype 公式 | base、GT、NSG | builder、全部评测 |
| top-m、router backend/参数 | base、GT、NSG、兼容 prototype | 路由与下游评测 |
| search_L、top_k、计时口径 | 上游 artifact | 对应评测 |
| 只改兼容的汇总/绘图 | 原始 JSON/CSV | 汇总/绘图 |

任何不兼容的 base、预处理、metric、图、split 或 GT 变化都会使下游 artifact 失效；不得靠文件名相似继续复用。

## 11. 当前实现缺口与停止边界

- Multi-view 已在 E1b 因等总 NDC Recall 失败而停止；三组独立构建、tail、归因与 held-out 是按 gate `NOT_RUN`，不是待补实验。
- E0 已统一 Python/C++ merge、真实 anchor assertion、routing/graph/total NDC 与分离计时接口；stage runner 会拒绝覆盖输出根目录，并在当前 gate 下拒绝 E2–E4。
- Fast/Three-view 依赖 exact train GT，完整 GT-inclusive 成本和 break-even 未完成。
- confidence margin 当前公式跨数据集 no-go，不得称为元学习。
- WebVid GATE 已同图适配但弱于 Fast；按 gate 未复制到 Yandex。仍缺 RoarGraph/RobustVamana 同机端到端比较。
- 本批未读取 Multi-view held-out，且失败后不得返回调参；若未来提出新方法，必须另立协议，不能沿用本批 validation/test 授权。

旧 Multi-view 已按 E0 → E1 → E1b 提前终止；当前 `s-target.md` 已替换为另获授权的长期分层搜索计划。旧 oracle、utility ranker、BTG、probe-reroute、finite-beam 和 GATE 细节保留在各自 artifact，不作为新方案 GO 证据。

## 12. 辅助入口

- 当前研究结论：`summary.md`
- 本批协议与终局：`s-target.md`
- 历史方法与失败分支：`aco_router_fast_entry.md`、对应 `*_diagnostics/`
- 复现命令：`command.md`
- 相关工作历史提案：`papers/related_work_2026-08-29/README.md`
- 核心源码快照：Git ref `research/core-source-20260830`，bundle `/data/netg/ACSG_core_source_20260830_v3.bundle`

历史提案和旧日志不能覆盖本文件、当前源码或 `summary.md` 的停止边界。

## 13. 新分层搜索协议（研究暂停，实现待验收）

- 输入复用正式 raw-IP base/图、独立 QGT 5K raw hubs；拟合 router_train `[10000,30000)`，开发 pilot `[0,10000)`。paired Fast 重建同 20K prototype，旧 30K prototype 不能进入新训练链。
- 图分区只对辅助对称邻接使用 METIS v5.2.1/i64；搜索继续用原 directed NSG。P2 为 64 区域、每区 2 门户、激活 4；P3 完整版本 16×16、λ=1/0、1.2 容量上限与两轮确定性下降移动。
- 路由 API 无 GT：query/model → region IDs、概率、真实 entry IDs、provenance；搜索 API 无 GT：query/graph/route/workspace → top-K。oracle 在评测层独立适配且仅训练诊断。
- 总候选容量为 L：共享 25%，区域余量按概率最大余数分配、每区至少 4；区域 ID 破同分。默认入口为共享种子例外，重复 ID 首次归属；跨区域边不筛除。加权轮转扩展，所有保留候选已扩展才终止。
- 全局 visited 保证每节点最多一次真实距离；独立全局 top-K 在共享池与区域池两对照一致。原 search_new mode 2 的三入口上限不作新 top-m 路径，新路径必须实际消费 m 并正确处理 HNSW maxheap 顺序。
- 新 wall 路径在 timer 前分配 workspace/输出；timer 内归一化、路由、重置、队列调度、搜索和结果写入，timer 外 GT 评分/hash/trace/JSON。count/trace 使用独立运行，必须与 plain IDs 一致。
- runner 显式 stage/split/measurement/output，独占新输出、验证上游 gate。P0/P1 不声明性能；P2 oracle 不进入部署 frontier；P6 通过冻结后才允许 held-out。版本状态、证据和任务句柄写 state.json。
- 新 artifact 预算 8 GiB，/data 保留 ≥10 GiB；不复制 base/图，仅一个重数据集进程。完整成本记录 exactGT、partition、portal、router，缺失项 null＋原因。
- 改区域/门户/拟合 split 必须重建模型与全部下游评测；改队列/路由必须重过 P1 和下游；改计时必须重测 wall；辅助图是独立改搜索图版本，重新 P1–P7。详细矩阵、统计及停止规则以 s-target.md 和版本 protocol.json 为准。

## 14. 夜间执行依赖与暂停交接

依赖安装的权威记录为 `hierarchical_target_search/20260907_v1/dependencies/{README.md,manifest.json}`。本轮只做依赖准备和安装检查，没有真实数据实验；现有核心源码、新草稿、旧 gate、原 Python 包版本保护检查均通过。`state.json` 为 `PAUSED_BY_USER`，下一对话明确恢复后才能继续，不能将依赖就绪算作 P0/P1 PASS。

- `tools/local` 提供 METIS v5.2.1（提交 f5ae915a84d3bbf1508b529af90292dd7085b9ec）、64 位 idx_t 和 GKlib；C API 六节点检查通过。链接 `-lmetis -lGKlib -lm`。
- `tools/env.sh` 是当前 shell 的环境入口；核心解释器仍为 `.venv_cpu/bin/python`。`tools/python/bin/python` 单独提供 Faiss 1.9.0、h5py、transformers、prettytable，并用 `.pth` 只读复用已有 CPU 科学计算包；原环境未升级。
- `tools/gp-ann/build` 已构建 MIPS 版本和所需子模块；`tools/RoarGraph/build` 已构建索引/搜索和 DiskANN exact-GT 工具。版本 checksum 见 manifest。LIRA 的 CPU/数据契约适配、gp-ann 计数协议审计仍是后续工作，不能声称基线正式复验完成。
- RoarGraph 的 MKL/OpenMP 在局部 `tools/mkl-sysroot`，仅由 `tools/roargraph-env.sh` 启用；不能将其环境混入原 ACSG 的构建与计时。系统仅新增 15 个依赖包，未升级或删除已有包。
- 复用现有 GATE 二进制及 gensim Graph2Vec CSV 适配；不得因可选 karateclub 缺失而静默退化成均值池化。
- 新对话提示词为版本目录 `overnight_prompt.md`，方法开发与实验截止北京时间 2026-09-08 07:00。当前未启动截止定时器；恢复后需对本次创建的任务设置可核验的停止机制，保留中断产物并标明 INCOMPLETE。停止后只整理既有证据和文档，交付 `/data/netg/ACSG/实验总结.md`：标题后首段用 3–5 句、约 150 字以内概括整晚成果，后文详细说明实现/验证、设置/结果/gate、证据、资源/安全、复现/下一步。若路径已存在，保留旧文档，在新时间戳 artifact 子目录保存同名文件并报告实际路径。
