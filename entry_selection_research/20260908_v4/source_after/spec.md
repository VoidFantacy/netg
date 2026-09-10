# NETG / ACSG 当前实现规格

> 最后核对：2026-09-08。本文件只记录当前实现、数据/metric 契约、artifact、评测口径和重跑依赖。研究结论见 [summary.md](summary.md)，当前任务与验证顺序统一从 [s-target.md](s-target.md) 阅读，历史过程见 `aco_router_fast_entry.md`。Fast根因诊断已完成，契约/产物见第18节；新效用树调研已完成但未实现未训练，设计身份/边界见第20节。第16–17节保留历史设计，不覆盖当前方案。

## 1. 权威性与保护边界

实现事实的证据顺序是：当前源码／配置／manifest／机器结果 > 本文件 > 总结、日志、旧 README、旧结果和远端分支。发现冲突时先报告，以验证后的当前实现为准；不能因远端提交时间较新而覆盖本地工作。

工作区含大量未提交源码和历史 artifact。禁止擅自 `git reset --hard`、`git clean`，禁止删除或覆盖旧索引、日志、结果、`*.bak` 和论文材料；新 variant 必须写入隔离目录。

文档职责固定：`spec.md` 管实现与复现契约；`summary.md` 管研究判断、结论与停止边界；`s-target.md` 是当前方案主入口，管拟议方法、验证顺序、阶段gate、接续状态和交付。版本目录中的recommendation保留推荐论证，minimum_gate保存对应版本的详细验证契约；后续改变方案/gate另立版本并同步三份交接，不覆盖旧调研记录。任何改变数据、split、GT、metric、图、方法、artifact schema 或结论的工作，都要同步核对 `spec.md` 与 `summary.md`。

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
      -> sum of unit queries + unit raw-hub prior (weight 1), then normalize
      -> closed-form GT-basin prototypes
  + online query
      -> Micro-HNSW over prototypes
      -> top-3 real base entry IDs
      -> ACSG::search_new on the unchanged NSG
```

QGT 是项目内术语 Query Ground-Truth；QGT-Cover 是 query-clustering 启发式，不是严格 set cover。prototype 是入口的“查询画像”，不是入口节点向量的复制。

Fast 不读取 ACO weights、DPC centers、probe labels 或 Neural Router bins，不运行 optimizer/MLP，不修改 NSG；但依赖 exact train GT。结果槽名 `Asym-Neural/NETG_AsymHNSW` 在 Fast manifest 中承载 closed-form prototype，不能据名称误报为神经模型。

### 2.2 Multi-view Target-Basin Routing（已完成成本否决）

该历史 validation 版本把 seeds `20260828/20260829/20260830` 的三个 Fast build 作为一个模型的三个 view：保留 seed-20260828 Fast rank-0 作为 anchor；每个 view 取 top-8，重复 entry 按最高 cosine 合并；从并集选两个补充入口，最终仍以 top-3 搜索同一 frozen NSG。

在线不读取 GT、probe label 或 held-out。三个 view 是一个 ensemble instance，不是三次独立重复。E0 已统一路由、anchor、计数和计时契约；E1 的 dense 后端成本失败后，E1b 将后两 view 固定为 `M16/efConstruction200/efSearch32` Micro-HNSW、top-8 exact rerank。

E1b 在双数据集 train-10K 的四个等 total-NDC 点均低于 paired Fast Recall，已按停止规则定为 `NO_GO_ROUTING_COST`。该扩展不进入独立构建、tail、归因或 held-out；当前已验证基线为 Fast v1。

## 3. 当前代码入口

已停止版本 `hierarchical_target_search/20260907_v1` 的P0/P1、区域搜索/独立计数/纯计时及P3的256叶区新P1均通过。新增 `ACSG/RegionalSearch.h`、`benches/test_regional_search.cpp` 和三个分层评测/门户入口，修改前源码/checksum已保存。P2的64区域、P3的16×16结构与门户模型均完成双数据集pilot；P3搜索收益gate为NOPASS，三项失败诊断完成。P4层次预测尚未实现和启动。实现正确不等于方法有效；原契约见第13节，历史复审见第15节，当前入口调研边界见第16节。

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

旧 Multi-view 已按 E0 → E1 → E1b 提前终止；当前 `s-target.md` 正文为第20节真实效用树的拟议方案与验证顺序。固定主入口三入口联合选择是第17节历史提案，已被第18节诊断撤下其默认限制；原R0–R2及已停止分层P0–P8由快照保留，不自动排队。旧oracle、utility ranker、BTG、probe-reroute、finite-beam和GATE细节保留，不作为新方案GO证据。

## 12. 辅助入口

- 当前研究结论：`summary.md`
- 当前方案、入口选择流程与下一步：[s-target.md](s-target.md)；其中链接到完整历史快照
- 历史入口调研指令：`entry_selection_research/20260908_v1/next_dialogue_prompt.md`；当前报告、方法与未运行gate：`entry_selection_research/20260908_v4/{report.md,method.md,minimum_gate.md,state.json}`
- 历史方法与失败分支：`aco_router_fast_entry.md`、对应 `*_diagnostics/`
- 复现命令：`command.md`
- 相关工作历史提案：`papers/related_work_2026-08-29/README.md`
- 核心源码快照：Git ref `research/core-source-20260830`，bundle `/data/netg/ACSG_core_source_20260830_v3.bundle`

历史提案和旧日志不能覆盖本文件、当前源码或 `summary.md` 的停止边界。

## 13. 新分层搜索协议（实现验收通过，P3完整pilot为NOPASS）

- 输入复用正式 raw-IP base/图、独立 QGT 5K raw hubs；拟合 router_train `[10000,30000)`，开发 pilot `[0,10000)`。paired Fast 重建同 20K prototype，旧 30K prototype 不能进入新训练链。
- 图分区只对辅助对称邻接使用 METIS v5.2.1/i64；搜索继续用原 directed NSG。P2 为 64 区域、每区 2 门户、激活 4；P3 完整版本 16×16、λ=1/0、1.2 容量上限与两轮确定性下降移动。
- 路由 API 无 GT：query/model → region IDs、概率、真实 entry IDs、provenance；搜索 API 无 GT：query/graph/route/workspace → top-K。oracle 在评测层独立适配且仅训练诊断。
- 总候选容量为 L：共享 25%，区域余量按概率最大余数分配、每区至少 4；区域 ID 破同分。默认入口为共享种子例外，重复 ID 首次归属；跨区域边不筛除。加权轮转扩展，所有保留候选已扩展才终止。
- 全局 visited 保证每节点最多一次真实距离；独立全局 top-K 在共享池与区域池两对照一致。原 search_new mode 2 的三入口上限不作新 top-m 路径，新路径必须实际消费 m 并正确处理 HNSW maxheap 顺序。
- 新 wall 路径在 timer 前分配 workspace/输出；timer 内归一化、路由、重置、队列调度、搜索和结果写入，timer 外 GT 评分/hash/trace/JSON。count/trace 使用独立运行，必须与 plain IDs 一致。
- runner 显式 stage/split/measurement/output，独占新输出、验证上游 gate。P0/P1 不声明性能；P2 oracle 不进入部署 frontier；P6 通过冻结后才允许 held-out。版本状态、证据和任务句柄写 state.json。
- 新 artifact 预算 8 GiB，/data 保留 ≥10 GiB；不复制 base/图，仅一个重数据集进程。完整成本记录 exactGT、partition、portal、router，缺失项 null＋原因。
- 改区域/门户/拟合 split 必须重建模型与全部下游评测；改队列/路由必须重过 P1 和下游；改计时必须重测 wall；辅助图是独立改搜索图版本，重新 P1–P7。详细矩阵、统计及停止规则以 s-target.md 和版本 protocol.json 为准。

## 14. 已结束夜间执行的依赖与历史交接

依赖安装的权威记录为 `hierarchical_target_search/20260907_v1/dependencies/{README.md,manifest.json}`。此前准备轮只做依赖准备和安装检查，没有真实数据实验；当时核心源码、新草稿、旧 gate、原 Python 包版本保护检查均通过。后续夜间恢复授权已于截止结束，`state.json` 为 `TIMEBOX_STOPPED_REPORT_COMPLETE_P3_NOPASS`；该批独立证据已通过P0/P1，依赖就绪本身不算方法验收。

- `tools/local` 提供 METIS v5.2.1（提交 f5ae915a84d3bbf1508b529af90292dd7085b9ec）、64 位 idx_t 和 GKlib；C API 六节点检查通过。链接 `-lmetis -lGKlib -lm`。
- `tools/env.sh` 是当前 shell 的环境入口；核心解释器仍为 `.venv_cpu/bin/python`。`tools/python/bin/python` 单独提供 Faiss 1.9.0、h5py、transformers、prettytable，并用 `.pth` 只读复用已有 CPU 科学计算包；原环境未升级。
- `tools/gp-ann/build` 已构建 MIPS 版本和所需子模块；`tools/RoarGraph/build` 已构建索引/搜索和 DiskANN exact-GT 工具。版本 checksum 见 manifest。LIRA 的 CPU/数据契约适配、gp-ann 计数协议审计仍是后续工作，不能声称基线正式复验完成。
- RoarGraph 的 MKL/OpenMP 在局部 `tools/mkl-sysroot`，仅由 `tools/roargraph-env.sh` 启用；不能将其环境混入原 ACSG 的构建与计时。系统仅新增 15 个依赖包，未升级或删除已有包。
- 复用现有 GATE 二进制及 gensim Graph2Vec CSV 适配；不得因可选 karateclub 缺失而静默退化成均值池化。
- 版本目录 `overnight_prompt.md` 为已结束的夜间授权原文，其方法开发与实验截止北京时间 2026-09-08 07:00；当前新对话使用第16节的[入口调研指令](entry_selection_research/20260908_v1/next_dialogue_prompt.md)。本次截止watchdog已完成停止核验并退出；无截止中断任务，早期失败产物保留原状态。停止后只整理既有证据和文档，已创建[实验总结](实验总结.md)：标题后首段用 3–5 句、约 150 字以内概括整晚成果，后文详细说明实现/验证、设置/结果/gate、证据、资源/安全、复现/下一步。若路径已存在，保留旧文档，在新时间戳 artifact 子目录保存同名文件并报告实际路径。

### 本次夜间实现与证据（核对于北京时间 2026-09-08 07:10）

产物根目录：`hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/`。完整结论及数值见[当前研究判断](hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/current_findings.md)，当前状态见[机器台账](hierarchical_target_search/20260907_v1/state.json)。P0/P1/P2 PASS，P3新增P1 PASS、完整pilot搜索收益NOPASS；P4–P8未启动。

- 输入与保护：P0完整SHA/split隔离/图内base抽样通过；20K fit、10K历史开发pilot和paired Fast同20K。原ACSG.cpp/h、旧Fast默认评测源码保持开始快照身份，CMake只增加三个目标；既有未提交改动与历史产物保留。保护复核见[preclose记录](hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/source_protection_preclose_v1.json)。
- 搜索入口：`RegionalSearch.h`实现统一/区域池、共享visited/全局top-K、容量分配、加权轮转和trace；`bench_hierarchical_eval.cpp`为P2，`bench_hierarchical_eval_p3.cpp`为256叶区评测，`bench_hierarchical_portals.cpp`生成固定离线覆盖代理。真实路由API无GT，oracle仅评测层诊断。纯wall计入实际路由/重置/搜索/结果写入，排除GT评分/hash/JSON；count与trace独立。
- 正确性：合成、边界、tie、sanitizer及两数据集512查询L64/128与旧同入口搜索parity通过；m4/6/8实际消费通过。P3再做P2兼容性、256叶区真实模型count/plain和trace验收，具体覆盖见各P1 gate。纠正了新paired Fast HNSW入口顺序；同入口kernel parity不代表旧端到端入口顺序相同。
- P2：严格64区1.2容量。METIS内部额外容差曾令WebVid12区各超2节点，保留失败，补偿库容差后原硬上限通过。P2完整预注册23查询trace已全部补齐并独立重放，原gate及[补充记录](hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/trace_completion_addendum_v1.json)分别保留时序。
- P3：冻结共同16×16初始化，原directed叶区域J，λ0/1各两轮严格下降；粗/细全局1.2容量，每叶3门户总768，frequency3/greedy3固定2×2。全部8模型验收通过，结构子条件通过、主搜索条件失败；不能继续P4或事后改主对照。
- 只读诊断：门户暴露仅消费既有count/portal摘要；目标泛化读取受限fit/pilot GT10及保存标签/返回ID；局部尺度只读原邻接、fit GT10、3份保存标签。后者全索引SHA中的嵌入向量字节只作身份核验，没有数值计算。实现、独立合成验收、完成标记和解释审查都在`p3/`；无新ANN评测点、模型、CI或gate。
- 测量解释：旧Fast部分frontier计数是未测量占位；P3嵌套bootstrap初始status由独立文件/CI核对澄清，原产物不改。完整成本中的exactGT和原NSG构建为复用且历史耗时未知；P3分区记录含两λ分支和共享初始化，门户probe缓存不能在frequency/greedy各算一次。

`control/taskctl.py`记录独立PGID、PID启动身份、命令、日志、超时、资源；`stage_run.py`强制上游gate与split访问边界。当前无研究进程，06:59检查点与07:00停止核验完成，watchdog已退出。最终进程核验和[实验总结](实验总结.md)均已写入；截止后只有既有证据核查与文档，报告最终复核已完成。

局部尺度的[纯代数补充](hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/objective_lexicographic_addendum_v1.md)进一步证明：固定当前状态、考虑的候选与可行性，当前λ1先按整数GT分散变化ΔS、再按切边变化ΔC比较；全部fit目标满足严格界，unseen对所有候选ΔS恒为0。与stay零同分保持原标签，严格改善移动同分才按叶ID。图仍影响候选和同ΔS比较，容量及更新顺序仍重要；这不证明全局最优或Recall退化原因。

输入访问口径澄清：validation未用于拟合/选择或ANN性能评测，但P0已读取其query/GT做文件头、全SHA、查询逐行指纹去重/跨split重叠及finite检查、GT ID范围/行内重复检查；held-out文件未打开。此前笼统的“validation/held-out未读”由此收窄，既有日志保留，详见[P0访问补充](hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p0/validation_access_scope_addendum_v1.json)。

北京时间2026-09-08 03:02已提前关闭本次新实验入口（`control/CLOSED.json`）：P3负结果及有限诊断完成，当前任务进程为零；截止监控保留至07:00，07:00最终停止核验通过，报告已于07:06在截止后创建。期间等待不计作训练/实验时间。

### 截止后交付核验（北京时间 2026-09-08 07:14）

07:00:00.312截止核验及07:01:24独立全进程身份核验均通过，无活跃任务，无终止信号，无截止中断。34个已启动重任务区间无重叠；源码/CMake/settings保护通过，主动删除文件无。见[最终停止](hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/control/final_process_verification_v1.json)、[最终保护与资源](hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/final_protection_resources_v1.md)和[实验总结](实验总结.md)。报告已完成并通过独立复核；研究结论仍P3 NOPASS，长期目标未完成。

[实验总结](实验总结.md)最终独立复核PASS，0项实质/阻断问题，证据见[报告复核](hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/final_report_independent_review_v1.md)。本次有截止的执行与报告交付已完成；长期研究仍未完成，当前P3 NOPASS及后续gate边界不变。

## 15. 历史文献与计划复审（2026-09-08，R0–R2未运行且已被替代）

新增 `research_direction_review/20260908_v1/`：复审前文档/state快照与SHA、14篇核心论文的方法/实验核对、独立本地假设审查、[综合报告](research_direction_review/20260908_v1/report.md)。只读论文及已有小型证据，未打开原始query/GT/base/图，未改搜索/分区源码、二进制、配置、模型或统计产物；原夜间报告、P3 gate、state和CLOSED控制边界保持。

该次复审曾将R0–R2列为优先级，状态`DESIGN_REVIEWED_NOT_RUN`，不注册为通过gate：先核验paired Fast/同入口统一池/GATE受约束适配的可比性，并优先评估PyANNS完整系统基线；再以固定P2表示/入口和六个核心搜索点检验实际成本空间。历史筛查预定统一池/区域池QPS比[1.00,1.02]的近似匹配容差；具体统计处理/输入绑定/资源限制当时尚未冻结。该建议未执行，现已由第16节入口选择调研替代，不是前置必跑阶段。基线可比性与完整成本原则保留；依赖安装不等于baseline验收，论文速度不等于本地结果。

复审不改变raw-IP、原NSG、20K fit、历史10K pilot、该分层夜间版本validation仅完整性检查或held-out冻结边界；其他旧分支已使用validation做性能评测，不能推广为全项目从未使用。原P3仍NOPASS；GT占比oracle不是最优调度oracle；P4未实现不能写成所有层次预测失败。新方法若改变图、标签或搜索规则，按第10节联动重跑对应阶段，不能沿旧已关闭runner绕过gate。

## 16. 入口选择方向建立时的调研交接（2026-09-08，当前完成状态见第17节）

用户已指定“改进入口选择方法”为主要方向。当时新增 `entry_selection_research/20260908_v1/`：`direction.md`记录问题、当前实现与历史证据边界；`next_dialogue_prompt.md`为下一对话指令；`state.json`标记`DIRECTION_SET_RESEARCH_PENDING`；`source_before/`与`manifest.json`保存本次文档变更前快照及受保护小文件身份。该方向建立轮只修改文档/交接状态，未修改方法源码、二进制、配置、模型、原始数据或实验gate，未运行新实验。

实现仍为第2节Fast和已验收的独立搜索组件。当时约定下一轮首先查（现已完成，见第17节） `benches/run/build_fast_entry_variants.py` 中的候选构造、top-1 GT basin平均prototype和真实路由链；候选池、短名单/排序、少量入口组合仅为研究轴，不是已实现的新算法。固定图和搜索语义用于隔离入口收益；改入口数须验证`search_new` mode 2三入口上限、实际消费/顺序/去重，新路径不能以旧输出顺序冒充parity。

历史oracle入口为 `oracle_entry_diagnostics/webvid_validation_1k_current_hubs_v1/results.json`，仅取K≤L的有效行；它是旧30K Fast、815候选、validation 1K、免费穷举入口和graph-only统计，不与新20K paired Fast及新纯wall结果混用。`CurrentHub_Diverse_Top3_GreedyProxy`是单入口命中并集后重放，不是最优联合入口。关联负证据为 `sparse_utility_ranker_results/analysis.md`、`probe_reroute_results/analysis.md`、`trace_conditioned_rerouter_results/webvid_probe10_top32_topology_v4/report.json`；旧报告的下一步不覆盖当前停止边界。

当时下一对话的范围为源码/已有结果复核、一手文献及作者实现调研、2–3个机制比较、一个推荐与最小证伪协议草案。允许只读证据/联网查文献和写新调研文档；不训练、构图、ANN性能评测、扫参、新GT或依赖安装，不改方法源码，不读取原始validation/held-out查询与GT，不自动进入实验执行。旧 `overnight_prompt.md` 只作已结束的授权原文；旧截止、P0–P8 runner、state/gate/CLOSED均不用于新调研。

未来实验仍需另立协议，绑定原始IP、冻结NSG/base/GT、独立QGT5K、router_train后20K fit/前10K历史pilot和同20K paired Fast。不得以旧30K prototype作为新训练输入。validation已有历史性能使用（如旧oracle、ranker、Multi-view），分层夜间版本只做了完整性检查；必须分别记录使用历史，不能宣称全项目validation从未使用。held-out须在方法冻结及相应验证通过后按10K×3执行，不用于新调参。

完整计时包括候选检索、打分/组合选择、归一化、重置/去重、搜索和结果写入；GT/hash/trace/JSON在外，count/plain独立验收；完整离线成本包含exactGT、额外标签/轨迹、候选构造、模型训练与路由索引。强基线、两数据集、三独立构建、尾部与最终性能门槛不降低；具体比较族/成本匹配/资源预算在新协议冻结。若改变hub、标签或路由，按第10节重建相应模型与下游；若改变搜索语义，需重新正确性/计时验收，不能混作纯入口改进。

## 17. 历史入口调研与未执行设计（20260908_v2，当前诊断见第18节）

本节记录当时的设计，固定anchor/三入口预设已由第18节实测撤下，40维组合模型未实现未执行。当前主入口为[s-target.md](s-target.md)；v2 recommendation及minimum_gate保留原调研论证/契约。v2文件、completion、delivery_manifest及原独立复核SHA保持交付时身份；其中三份交接的SHA对应当时快照，不冒充本次当前文件SHA。

当前交付为 `entry_selection_research/20260908_v2/` 的report、related_work、recommendation、minimum_gate、protocol_draft和state。状态`RESEARCH_COMPLETE_DESIGN_ONLY`，新命令/API为`DRAFT_NOT_IMPLEMENTED_NOT_RUN`；本轮只读源码/已有结果、联网原文与作者源码并写调研文档，没有运行方法/性能实验、安装依赖或访问原始validation/held-out query/GT。三份交接同步；v1 direction/prompt/state、旧夜间runner/state/gate/CLOSED和实验总结保留。

已核对的实现补充：`search_new` mode2真实常量为3，先截断再去重、随后按raw query–base距离排种子；同三个唯一ID且无距离tie时不能把HNSW输出反转直接解释为性能差。`hnswalg.h`使用`max(ef,k)`再截断，ef10的top3/top8搜索池规模相同，但成本/前缀parity仍须验收。旧oracle的greedy3来自独立single命中并集后真实重放，不是联合三入口穷举。

作者实现核对独立存于v2/reviews和sources：GATE release v0.0.1/229f18d在线原query直接搜离线hub embedding，无query MLP；论文与release的正样本轴、启用loss和hop定义有差别。本地GATE rawIP/10K/dense适配与作者原件分列；这些核查不修改既有baseline结果或方法代码。

推荐机制只改变入口决策单元：单view C8包含同paired Fast3/anchor，主方法固定21个三入口动作；29个含anchor的一至三入口集合是诊断。未来wrapper固定anchor先、补入口按C8 rank，实际消费与原search_new、count/plain逐ID/NDC一致；不能以区域global-topK实现替代原kernel。主模型每dataset一套固定40维ridge、两L共享系数，16个显式特征点积及pair表成本计入；在线API没有GT/标签/Fast搜索结果/D_F输入。

未来最小gate草案绑定独立QGT5K、20K fit与历史10K pilot、同20K paired Fast；fit2048标签，互斥D1/D2各512，D1嵌套pool128/anchor64。固定动作标签和G3合计2,861,056次搜索，余138,944用于验收/暖机等，总300万；4小时、8GiB新产物、/data留10GiB、RSS80GiB、单重进程CPU16线程。G3固定16点/数据集、独立count与五轮纯wall；先对96项固定质量/成本对比建同时区间，再做最多3%差异QPS匹配，同时检查相对Fast和可加模型的增量。具体公式/停止/统计/未实现命令以minimum_gate为准；protocol_draft不是可运行配置或实验GO。

原始IP/base/GT/图与20K split未变；若未来更改hub/画像/路由，按第10节重建相应下游。候选覆盖、single排序和组合损失是有限家族诊断，oracle不贡献部署点。新pilot不降低三独立构建、强基线、尾部、双相邻工作点实质门槛及方法冻结后held-out10K×3要求。当前无待续实验进程，不从文档设计自动转入执行。

## 18. Fast根因诊断实验（20260908_v1，已完成并独立复核）

用户已明确授权查Fast为何未选到最好入口的实际实验。隔离版本 `fast_router_diagnosis/20260908_v1/` 的[protocol.md](fast_router_diagnosis/20260908_v1/protocol.md)定义本轮诊断；不是v2组合模型gate的自动执行，也不恢复旧夜间runner/deadline。此前源码、静态库、旧文档/状态/报告身份保存于新版本source_before；新增诊断代码只写该版本，方法源码/原二进制保持。

复用原NSG/raw-IP、QGT5K hubs和20K paired Fast画像；Fast实际把raw query送入Micro-HNSW，不能把区域路由的归一化误记为Fast在线步骤。ANN和exact画像排序调用同一HNSW距离函数；HNSW固定M16/efConstruction200/ef10，主seed20260828，旧默认seed100作已预定对照。搜索直接调用原search_new mode2，共享visited和容量L，评分在GT-free搜索返回之后，不能拿RegionalSearch独立global-topK替代。

每数据集从router_train前10K按协议哈希取512pilot；前128pilot在后20K找cosine最近fit查询，并取128随机fit控制，去重后总≤768行。所有行全H single，K10/L64、128；pilot另有C8内28pair/56triple、Fast/exact1/2/3及seed100三入口。辅助fit行用于count/plain/重复正确性，GT只在诊断层关联，不训练新部署模型。

准备脚本显式绑定输入与源码身份，复算现有20K画像只作一致性验收；small query/GT副本输出headerless f32/i64、原行ID i64，hub ID i32，附shape/dtype/SHA。结果按L保存all_single与pilot的hitcount u8、GT10 hitmask u16、NDC u32、top10 ID i32及动作/局部hub到真实base映射；approx/exact排序与basin标签独立保存。原始validation/held-out不访问，base/graph/训练侧全SHA重核，GT身份与旧有效输入绑定。

固定实际行数WebVid767/Yandex768，pilot各512。四个真实job顺序完成，调用合计2,770,770（含87,072验收调用），控制器跨度150.676秒、进程wall和150.557秒、峰值RSS约10.01GiB；均在300万/4小时/16线程/80GiB/2GiB新增/10GiB余量预算内。控制器调用限额在job完成后核对，固定shape事前有界，不宣称任意规模job内实时截断。

最终输入为`inputs/prepared_v2`，base/raw-hub字节一致、20K画像完整复算逐字节一致、训练侧身份检查通过；prepared_v1保留。原kernel真实parity WebVid14,464组、Yandex14,560组通过；实际入口数、顺序、count/plain/repeat及路由前缀一致。main单独不重复parity，消费已完成的辅助fit验收，不把main的NOT_RUN误记为失败。

原始矩阵在`results/run_v1/main/{dataset}/L{64,128}`，身份与实际命令分别在`execution_freeze.json`、`jobs.json`。正式统计为`analysis/v2`：32项主对比、10,000次query配对bootstrap、PCG64 seed20260908，同dataset/样本数的两L共享行抽样；普通95%和Bonferroni32区间均保存。区间是bootstrap近似，每端极尾约8个draw；不宣称严格有限样本覆盖。独立核对全部返回ID→GTmask、32均值、4个抽样流、128区间端点和512行邻近映射通过，见[统计复核](fast_router_diagnosis/20260908_v1/reviews/independent_analysis_review.md)。

analysis/v1保留，v2修正nearest−random NDC差的uint32减法并补齐exact C8 oracle NDC；全部Recall、主对比区间、图相同，无新搜索。独立`collect_costs.py`汇总正式[costs_v2.json](fast_router_diagnosis/20260908_v1/results/costs_v2.json)：全H single/组合/scoring-I/O分别记录，stage=route是HNSW构建/路由开始前事件，4.18/11.04秒只包含此前装载。构建与路由均无直接联合或独立结束计时，字段为null并说明；原exactGT/QGT/NSG构建历史时间同样未知。costs_v1的stage事件误读保留并由v2更正，总进程时间未变。缓存已受输入hash预热，任何上述时间均不能发布方法QPS/Pareto。

交付[报告](fast_router_diagnosis/20260908_v1/report.md)、[复现](fast_router_diagnosis/20260908_v1/README.md)、完整JSON/CSV和四张PNG；当前方法源码/库/原二进制及94个受保护历史文件身份保持。所有原始validation/held-out均未打开，没有新模型训练、部署性能点或旧计划恢复。“最优”仅限当前H/L/入口数，保留全部ties；研究结论见summary，有限矩阵不能证明理论不可学习。

## 19. 离线模型与在线推理成本澄清（20260908_v3，仅研究范围更新）

用户明确允许离线重量模型，在线预测必须轻量以控制QPS损失。新增[澄清说明](entry_selection_research/20260908_v3/clarification.md)及三份交接修改前快照；当前API、代码、输入/图/GT、模型和统计均未变，没有新训练或搜索，不触发旧产物重跑。此前diagnosis/v1及调研v2的交付SHA对应当时快照，保留原记录，不冒充本次三份当前交接的SHA。

未来可在离线使用重教师、丰富训练信号、复杂入口表示及预计算，并独立检验其样本外效用与压缩后在线效用；不要求训练模型本身轻量，也不强制teacher/student结构。GT/完整搜索标签/轨迹若仅用于训练，不能作为当前query免费在线输入；部署输入和计算图必须另行明确。最终在线wall包括query特征提取、模型推理、候选检索/打分、入口选择和主图搜索；离线另计GT/搜索标签生成、重模型训练、压缩/蒸馏、入口预计算和路由索引。只有实测的端到端Recall–QPS能验证在线收益。

两个已有诊断对照的定义保持：exact prototype对全部既有画像用同一距离函数精确排序，不使用目标query的GT；GT1 basin则用已知真实GT1向量与raw hubs的cosine选一个hub，是原builder几何标签的oracle，既不直接使用GT1节点作入口，也不按真实搜索效用选最优hub。该解释不改变原矩阵/统计。

## 20. 真实效用斜切树调研（20260908_v4，仅设计，未实现未运行）

交付目录[entry_selection_research/20260908_v4](entry_selection_research/20260908_v4)：report记录推荐与备选，method定义逐行收益目标/TAO式更新/多叶同hub及在线契约，minimum_gate是拟议验证草案，reviews保存本地源码、原论文/作者代码及独立审查，sources保留只读引用副本，source_before保存本轮前交接与受保护文件身份。状态`RESEARCH_COMPLETE_DESIGN_ONLY`、新接口身份`DRAFT_NOT_IMPLEMENTED_NOT_RUN`、`method_go=false`；没有新方法代码、配置、模型、搜索、GT或依赖安装，原始validation/held-out未访问。

拟议动作是原NSG/raw-IP、K10、L64/128的单入口；两个L分别建模型，叶子可从815/821现有hubs中选任意真实base ID，不要求叶到hub一一对应。主训练目标为sum真实Recall regret，NDC只作累计Recall同分时次序。分支比较当前两棵子树实际输出的收益差，用绝对差加权二分类，并对真实经验目标执行接受检查；代理损失下降不等于真实目标改善。节点更新后重算受影响路径与叶支持量，不准在线遍历两个子树或使用目标GT。

拟议student范围是depth8/10×每节点64非零/全维、min_leaf32，query-only单路径，原图搜索和初始化语义不变。在线完整计时包含所有query处理、节点推理、ID映射/初始化及搜索。query-only重模型是可学习性参照，不是理论上界；学生直接优化实测效用，未规定必须蒸馏教师。任何未来教师软标签/新特征/回退/组合都需另建对照与成本契约。

草案使用后20K拟合、前10K历史开发池中1024校准/1024审计，排除本轮诊断512不改变历史开发属性。全H标签算术为72,141,056次；拟议首轮≤80M搜索、CPU16线程/80GiB、搜索wall4h/模型拟合8h。具体模型、统计、资源、计时匹配点和可执行入口尚须在实现轮另冻结，不把草案当实验已授权或已通过。正式三独立构建及held-out10K×3另列预算，原强基线、双数据集、相邻点和尾部要求不降低。

旧v2/v3/diagnosis交付保持历史身份；本轮发现第11节仍把固定anchor三入口写作当前方案，已按现有诊断与新推荐修正。文档变更不触发已有数据重跑；未来改图/base/hubs/split/metric或标签kernel时按第10节重建相应全动作标签、模型与下游结果。
