# NETG / ACSG 当前实现规格

> 最后核对：2026-08-30。本文件只记录当前有效的代码入口、数据/metric 契约、artifact、评测协议和重跑依赖。研究判断与 go/no-go 见 `summary.md`；旧 ACO/Router 诊断与结果历史见 `aco_router_fast_entry.md`。

## 权威性与工作区保护

实现事实的证据优先级：

1. 当前源码、dataset config、manifest 和机器可读结果；
2. 本文件；
3. `summary.md`、历史日志、旧 README 和旧结果。

工作区包含大量未提交源码、构建文件和历史 artifact。禁止擅自执行 `git reset --hard`、`git clean`，禁止删除或覆盖旧索引、日志、结果、`*.bak` 和论文材料。新 variant 必须写入隔离目录。

## 当前主方法

当前论文主线不是旧 Neural Router，而是：

```text
frozen NSG
  + independent 5K QGT-train queries and exact top-100 GT
      -> spherical k-means
      -> one unique GT base node per query cluster
      -> QGT-Cover raw hubs
  + independent 30K prototype-train queries and top-1 GT vectors
      -> assign GT vector to nearest raw-hub basin
      -> normalized query mean + raw-hub prior
      -> closed-form prototypes
  + online query
      -> Micro-HNSW over prototypes
      -> top-3 base entry IDs
      -> original ACSG::search_new on frozen NSG
```

Fast 主路径不读取 ACO weights、DPC centers、probe labels 或 Neural Router bins，不运行 optimizer/MLP，也不修改 NSG 邻接边。当前 Fast artifact 仍依赖 exact train GT。

固定的 C++ 任务名 `Asym-Neural/NETG_AsymHNSW` 在 Fast 结果中承载 closed-form prototype；读结果时必须结合 manifest，不得据槽名误报成神经网络。

## 当前代码入口

| 目的 | 文件 |
| --- | --- |
| Fast variant 构建 | `benches/run/build_fast_entry_variants.py` |
| 单/多 seed 验证 | `benches/run/run_fast_entry_validation.sh`、`run_yandex_qgt_fast_light.sh` |
| 双数据集正式复验 | `benches/run/run_two_dataset_fast_benchmark.sh` |
| LAION 下载/准备/冻结图 | `download_laion10m_acsg_v1.sh`、`prepare_laion10m_acsg_v1.py`、`run_laion10m_acsg_v1.sh` |
| Recall/QPS 搜索 | `benches/test.cpp` -> `build/benches/test` |
| 逐 query Recall@10 | `benches/bench_per_query_recall.cpp` -> `build/benches/bench_per_query_recall` |
| 汇总 | `summarize_fast_entry_multiseed.py`、`summarize_two_dataset_fast_benchmark.py` |
| 绘图 | `benches/run/plot_two_dataset_qps_recall.py` |
| 一键命令 | `command.md` |

旧链仍保留用于历史复现：

```text
NSG -> metric-aware ACO -> DPC -> probe labels -> Neural Router -> evaluation
```

其入口是 `bench_ACO_TEST`、`kph_dpc_clustering`、`bench_generate_labels`、`train_router.py`。旧链不是当前默认方法，不得无条件重跑或覆盖 Fast artifact。

## 构建环境

当前服务器：Ubuntu 22.04、16 vCPU、约 123 GiB RAM、无 swap、无 GPU；项目位于 `/data/netg/ACSG`。Python 环境为 `.venv_cpu/`。

CPU 构建入口：

```bash
source .venv_cpu/bin/activate
cmake -S . -B build -G Ninja \
  -DFAISS_ENABLE_GPU=OFF \
  -DFAISS_ENABLE_PYTHON=OFF \
  -DBUILD_TESTING=OFF
cmake --build build -j 16
```

使用根工程，不使用 `SSG/build`。大文件只写入 `/data`。

## 正式数据集契约

### WebVid-2.5M

- dataset key：`webvid2_5m_light_v1`
- artifact version：`roargraph-webvid2.5m-ip-v1`
- base：2,505,000 × 512，`base.webvid2_5m.fvecs`
- metric：inner product
- normalization：source vectors 近单位范数，不额外归一化
- QGT-train：5K，`query.aco_train.seed20260826.fvecs`
- prototype-train：30K，`query.router_train.seed20260826.fvecs`
- validation：10K，`query.validation.seed20260826.fvecs`
- held-out：public 10K，`query.test.public10K.fvecs`
- manifest：`benches/datasets/WebVid2.5M_light_v1/manifest.json`

manifest 记录训练源中排除的 duplicate 与 public-test overlap；最终四个输出 split 的六组两两 overlap 均为 0。

### Yandex T2I official 10M/IP

- dataset key：`yandex_t2i_official10M_ip_v1`
- artifact version：`yandex-t2i-official-first10m-ip-v1`
- base：官方 `base.1B.fbin` 前 10,000,000 条，200d
- metric：inner product
- normalization：none
- QGT-train：learn `[0,5000)`
- prototype-train：learn `[5000,35000)`
- validation：learn `[35000,45000)`
- held-out：public `[0,100000)`；当前正式评测取前 10K
- manifest：`benches/datasets/YandexT2I_official10M_ip_v1/manifest.json`

四个 split 的六组两两 overlap 均为 0，GT 为匹配 first-10M base 的 exact IP top-100。

### LAION-10M/IP（数据、GT、冻结 NSG 已完成）

- dataset key：`laion10m_acsg_v1`
- artifact version：`roargraph-laion10m-unit-ip-acsg-v1`
- base source：LAION-400M fp16 image shards `0..7,9,10`，严格按此顺序拼接
- base target：`10,004,480 × 512`，`base.roargraph_laion10m.unit.fvecs`
- metric：inner product
- normalization：base 与所有 query 显式逐行 L2-unit normalization
- historical query source：官方 `text_emb_0.npy`，`1,000,448 × 512` fp16
- QGT-train / prototype-train / validation：固定 seed `20260830` 去重抽取
  `5K / 30K / 10K`，并排除 public-test exact-row overlap
- held-out：RoarGraph Zenodo `laion.query.10k.fbin` 的 public 10K
- held-out GT：Zenodo `laion.gt.10k.ibin` 的 DiskANN truthset（top-500 IDs 后接
  top-500 float distances）截取 IDs top-100，并以 unit-normalized base/query 的 exact-IP
  抽样精确复算验证
- manifest：`benches/datasets/LAION10M_acsg_v1/manifest.json`

官方旧 `the-eye.eu` URL 当前证书失效且文件返回 404；下载脚本使用 LAION 官方部署地址
`deploy.laion.ai/.../embeddings/{img_emb,text_emb}/`。image NPY 每个必须是
`1,000,448 × 512, float16, 1,024,458,880 bytes`。公共 query/GT 固定 MD5 分别为
`af1343dc16554d87c43326cf4024493d` 和 `d76a89a9e05ce4a18a5ebdaa3e159796`。

LAION 与 WebVid public-query 源文件 MD5 相同。这不造成同一数据集内部 train/test 泄漏，
但意味着二者不是独立 held-out query workload；结果解释必须限定为不同 base corpus/scale
上的迁移。manifest、exact GT 与冻结 NSG 已通过终态验证；Fast 搜索结果仍未生成。

首轮 raw-vector 诊断已终态失败并保留：完整 base 上 first-32 public queries 的官方
top-100 set recall，raw-IP 为 `0.994375`、raw-L2 为 `0.9909375`；explicit-unit cosine/IP
为 `1.0`。因此不带 `.unit` / `.unit_ip` 的首轮 base/query/train-GT 禁止引用，原因见
`benches/datasets/LAION10M_acsg_v1/INVALID_RAW_IP.md`。这不是容忍近似 GT，而是据官方 GT
反推出并冻结正确预处理契约。

### Legacy 配置边界

`sift10M`、`sift10M_skewed`、`deep10M`、`gist1M` 和旧 `yandex_t2i` 的历史配置/结果不属于当前正式协议；其中部分旧配置曾共用 train/test query 或混用 custom-L2 语义。禁止把这些旧 key、旧 GT、旧图或旧结果并入当前 WebVid/Yandex artifact。

## 冻结底图

两个正式数据集当前共用参数：

```text
R=64, L_build=100, C=512
```

| 数据集 | NSG | info |
| --- | --- | --- |
| WebVid | `indices/webvid2_5m_light_v1_index/acosp_nsg.json` | 同目录 `.info` |
| Yandex | `indices/yandex_t2i_official10M_ip_v1_index/acosp_nsg.json` | 同目录 `.info` |
| LAION | `indices/laion10m_acsg_v1_index/acosp_nsg.json` | 同目录 `.info` |

实测构建 wall time 约 WebVid 14:40、Yandex 48:33。当前研究计划不要求重建 `L_build=500`；此前把 RoarGraph 的 `L_pjpq=500` 对应成 NSG `L_build=500` 不可靠。

WebVid 固定宽度邻接数组共有 160,320,000 slots，其中 110,707,547 个 `-1` 是未使用的
padding，而不是“少量坏边”；有效边 49,612,453，平均有效 degree `19.8`、范围 `1..64`，
无零度节点。导出 GATE variable-degree NSG 时只过滤 padding，保留 49,995 个有效重复 slots；
完整 parser 验证节点数、ID 范围与 exact EOF。该事实不改变 Fast/Formal 的同图比较。

## Fast artifact

每个 seed 的隔离目录：

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

正式 seeds：`20260828/20260829/20260830`。

Hub budget：

- WebVid：815
- Yandex：821

`manifest.json` schema version 2 保存 dataset/artifact version、QGT/prototype query 与 GT 的路径/checksum、base、seed、hub budget、输出 checksum 和 build wall time。`--qgt-only --target-hubs` 路径不得读取 DPC/labels/ACO/Neural artifact。

早期探索文件 `fast_entry_variants/webvid2_5m_light_v1/eval_qgt_vs_prototype_r1.json` 的 raw task 曾发生 vector/ID 错配，标记为 INVALID，禁止引用。

## 在线搜索与计时

`benches/test.cpp`：

- `--top_k 1` 测 Recall@1；`--top_k 100` 测 Recall@100。
- `--test_scope comparison` 只运行 Medoid、Raw 和 prototype/Neural comparison slots。
- Router 通过 Micro-HNSW 选择 top-3 entry IDs。
- Raw routing metric 从 dataset config 读取；IP 数据使用 IP。
- QPS 计时只包含当前进程的在线搜索，不包含后续 tail 汇总。

`benches/bench_per_query_recall.cpp`：

- 固定生成逐 query Recall@10。
- Medoid、Raw、prototype/Neural 均保存排序前的 `per_query_recalls_aligned`。
- 排序数组只用于分位数/CDF；rescued、still-failed、newly-harmed 必须使用 aligned 数组。

QPS 与 tail 是两个串行、独立进程；tail 阈值与转移统计不会污染 QPS 计时。

## 当前权威结果

`fast_entry_benchmark_results/`：

- `benchmark_summary.md`：权威可读报告
- `benchmark_summary.json`：完整机器汇总
- `search_metrics.csv`：Recall/QPS
- `tail_metrics.csv`：Mean Recall@10、失败率与 rescued/harmed
- `raw/<dataset>/`：原始 JSON 与 timing
- `figures/{webvid,yandex}_qps_recall.{png,pdf}`

协议：

- held-out 10K；
- Formal 每点 3 timing runs；
- Fast 3 build seeds × 每 seed 3 timing runs；
- Recall 确定性方差来自 build seeds；
- QPS 方差来自 timing runs 与 seeds；
- 跨 invocation 比较优先使用同次 Medoid 归一化 QPS；
- tail 阈值固定 `0.1/0.2/0.5/0.8`。

## Artifact 重跑依赖

| 变化 | 可复用 | 必须重跑 |
| --- | --- | --- |
| base、metric、normalization、底图参数/后端 | 原始下载与兼容 checksum 记录 | GT（若语义变）、NSG、Fast hubs/prototypes、全部评测 |
| QGT/prototype query split 或 train GT | 兼容 base 与冻结 NSG | Fast hubs/prototypes、全部评测 |
| hub budget、QGT clustering、prototype 公式 | base、GT、NSG | Fast builder、全部评测 |
| top-m、Micro-HNSW、search_L、top_k | NSG 与 Fast bins | 对应评测 |
| 只改汇总/绘图且 schema 兼容 | 原始 JSON/CSV | 仅汇总/绘图 |

所有新 artifact 必须记录 source checksum、split、metric、normalization、底图 checksum、seed、参数、代码版本、CPU/线程和生成时间。

## 当前已知限制

1. Fast 构建倍率未包含 exact train-GT 生成成本；论文必须补充 GT 成本和 break-even。
2. 当前 top-3 依据 prototype 相似度，不显式优化 entry 的共同失败或边际覆盖。
3. WebVid validation 1K 已完成 current-hub single 与 greedy top-3 proxy；broad candidates、top-5、Yandex 和 validation 10K 尚未完成。
4. WebVid standalone GATE 已完成同图、raw-IP、独立 split 和 graph NDC/latency 适配；旧 GATE 日志仍禁止引用，Yandex 复制按 WebVid no-go gate 停止。
5. `test.cpp` 的 legacy ACO-Max 在释放 weight 后仍会回退到 medoid；Fast comparison scope 不运行它，修复前不得作为有效 ACO 基线。
6. LAION-10M 下载、unit conversion、split、GT、manifest 和冻结 NSG 已完成；尚无 Fast 结果，也没有完整的 RoarGraph/RobustVamana 同机端到端结果。
7. current Fast 依赖 exact train GT；需评估更少 GT、top-1/10/100 和 trace-only 版本。

## LAION 持久流水线与续接

启动命令：

```bash
setsid bash benches/run/run_laion10m_acsg_v1.sh \
  > logs/laion10m_acsg_v1/pipeline.stdout.log 2>&1 < /dev/null &
```

2026-08-30 流水线已终态完成。prepare 以 wall
`26:12`、max RSS `61,211,168 KiB`、exit 0 完成；manifest 记录 base
`(10004480,512)`、六组 overlap=0、official first-32 set Recall@100=1.0。NSG 以 wall
`1:04:22`、construction `3816.927s`、max RSS `76,627,580 KiB`、exit 0 完成；保存
`10,004,480 × 512` vectors，图全连通，索引大小 `23,130,357,863 bytes`，SHA256
`7040cd0a2b8f5d34b3e3affbbcb30ce19c947731a8a81c40ec64f0e0d99bb238`；`.info` SHA256
`28c77e5e2b2e6b42d382c9ec9807cef6e4d397cca95f815f59c5b3f832e25f58`。下一会话先验证：

```bash
tail -n 1 logs/laion10m_acsg_v1/build_nsg.time.txt
cat indices/laion10m_acsg_v1_index/acosp_nsg.json.info
test -f indices/laion10m_acsg_v1_index/acosp_nsg.json && echo NSG_PRESENT
```

阶段日志和 `/usr/bin/time -v` 分别在 `logs/laion10m_acsg_v1/{download,prepare,build_nsg}.{log,time.txt}`；
顶层只记录 stage start/done。脚本以 `flock` 防止并发双跑，并自行刷新 PID；它可重入：
完整且大小正确的下载会复用，`.part` 会续传，已有转换/GT 会复用。初始磁盘 93 GiB
available；底图完成后约 22 GiB available，足够当前 Fast artifact/validation，因此
`/data/netg.tar.gz` 暂未删除。若后续实际空间不足，用户已授权删除该单一压缩包，删除前仍应
再次核对准确路径与 `df`。

完成判据不是进程退出本身，而是同时满足：

1. `manifest.json` 存在，unit-normalized base shape 为 `(10004480,512)`，六组 split overlap 均为 0；
2. official GT sample `set_recall_at_100=1.0`，所有源/输出 checksum 已记录；
3. NSG 与 `.info` 存在，`.info` 明确 `ip`、`R64/L_build100/C512` 和 artifact version；
4. 日志无 traceback/FATAL，time 文件记录 exit status 0；
5. 之后才可构建 Fast variants 并在 validation 10K 上做 `L=64/128/200/400`、
   Recall@1/10/100（Recall@100 的首点必须 `L>=100`）和 3-run 评测。

## Git 核心源码快照

当前普通 Git index/working tree 保留用户的历史脏状态，没有执行 `git add -A`、clean 或
reset。为绕开本地 `main` 的大文件历史，使用独立临时 index 从 `origin/main` 生成：

```text
local ref: research/core-source-20260830
base:      origin/main (92861d954b1cce41e134d85dc22d54c7ece61a52)
snapshot:  221 files, 1,652,896 tree bytes
content:   ACSG/MRNN/benches/GATE source, scripts, configs, tests, docs, faiss gitlink
excluded:  data, GT, index, model, result, log, PDF/image, build
```

用户授权目标为 `https://github.com/VoidFantacy/netg.git`，本地 remote 名为
`voidfantacy`，公开 fetch/ls-remote 正常。本机 `gh` 不存在，HTTPS credential helper 无
条目，SSH 对 GitHub 返回 `Permission denied (publickey)`，实际 HTTPS push 返回无法读取
Username，因此 remote push 尚未发生。GitHub 插件连接已建议安装/授权。包含最终底图交接的
本地可搬运备份保存为 `/data/netg/ACSG_core_source_20260830_v2.bundle`。取得 GitHub 凭据后只推独立 ref：

```bash
git push voidfantacy research/core-source-20260830:research/core-source-20260830
```

不得直接 push 本地 `main`：它的两个旧提交包含数 GB dataset/build blobs，会触发 GitHub
大文件限制并污染远端历史。

## 冻结图 oracle evaluator（首个 pilot 已完成）

新增 `benches/bench_entry_oracle.cpp`（`build/benches/bench_entry_oracle`）和
`benches/run/run_webvid_entry_oracle_pilot.sh`，只读取既有 NSG、validation split、
QGT hub IDs 与 Fast prototypes，不重建或修改 NSG。

首个 pilot 固定为 WebVid validation 前 1K queries、current 815 hubs、
`search_L=64/128/200/400`、Recall@1/10/100。single oracle 对每个 query/hub
执行真实冻结图搜索并选择命中最多者；diverse top-3 是按这些单入口结果的 GT
命中集合做边际覆盖贪心，再以真实三入口搜索复验，不是组合穷举 oracle。
候选选择只执行一次；Medoid、当前 Fast prototype top-3、single oracle 和 diverse
top-3 的最终搜索各执行 3 runs，并报告平均 Recall、graph NDC 和 graph latency。
隔离输出为 `oracle_entry_diagnostics/webvid_validation_1k_current_hubs_v1/`。

完成结果的 `status=complete`，共 12 个 `L×K` 点。每点聚合 3 runs 的 graph-only
Recall、NDC 与 latency，并保存每条 validation query 的 single/top-3 selected entry IDs。
关键结果是 single oracle 相对 Fast 在 Recall@1/10/100 的全部 12 个点均有正增益；
greedy top-3 在全部 12 个点均弱于 single oracle。结果没有保存每个 run 的独立统计、
搜索结果 ID 或逐 query recall，routing NDC/latency 也未计入；因此当前 JSON 只用于
current-hub headroom gate，不是投稿级端到端结果。

### Oracle-label prototype predictability gate

`benches/run/build_search_aware_prototypes.py` 从已完成的独立 `drl_train` oracle JSON
读取 `selected_single_entry_ids`，按 hub 聚合归一化 query，并加入 raw QGT hub prior；
输出 prototype、IDs、checksum 和 manifest。`bench_entry_oracle` 新增：

- `--skip_oracle`：只运行 Medoid/Fast/额外 prototype 对比；
- `--extra_prototype_hubs/--extra_prototype_ids/--extra_method`；
- `--extra_top_m=1..3`；Fast 基线仍固定 top-3。

已完成 artifact：

- train oracle：`oracle_entry_diagnostics/webvid_router_train5k_l64_r10_current_hubs_v1/results.json`
- prototypes：`search_aware_entry_variants/webvid_train5k_l64_r10_prior1_v1/`
- top-3 validation：`search_aware_entry_results/webvid_train5k_l64_r10_prior1_v1/validation_1k_3run.json`
- top-1 validation：`search_aware_entry_results/webvid_train5k_l64_r10_prior1_top1_v1/validation_1k_3run.json`
- decision report：`search_aware_entry_results/webvid_train5k_l64_r10_prior1_v1/analysis.md`

该 gate 使用 prototype-train 前 5K、`L=64/Recall@10` hard labels，validation 前 1K、
四个 `L`、三个 Recall@K、3 runs。hard-label centroid 已判定 no-go：top-3 仅有弱增益，
top-1 对 Recall@1/100 退化。后续 artifact schema 必须保存 shortlist 内每个 candidate 的
连续 Recall/NDC utility；不得只保存 argmax class。

### Sparse continuous utility 与静态 ranker gate

`bench_entry_oracle` 还新增：

- `--generate_sparse_utility --utility_shortlist N`：对当前 Fast prototype top-N 的每个
  single entry 保存 Recall、graph NDC，并保存 Medoid/Fast-top3 对照；
- `--extra_routes FILE --extra_top_m M`：读取逐 validation-query 的 raw-int32 route matrix，
  进行真实冻结图复验；不能与 `--extra_prototype_hubs` 同时使用。

构建脚本：

- `benches/run/build_utility_residual_prototypes.py`：signed query-centered continuous
  utility residual 的闭式 prototype；
- `benches/run/train_sparse_utility_ranker.py`：Fast top-32 上的三 seed、cost-aware
  listwise diagonal interaction reranker。训练/early-stop 只用 prototype-train 的
  80%/20%；validation utility 值只用于报告，route scoring 不读取它们。

双数据集 sparse utility：

- `sparse_utility_datasets/webvid_{train10k,validation10k}_top32_l64_128_r10_v1/`
- `sparse_utility_datasets/yandex_{train10k,validation10k}_top32_l64_128_r10_v1/`

模型与结果：

- `utility_residual_entry_variants/webvid_train10k_top32_l64_128_r10_a025_c005_t1_v1/`
- `utility_residual_entry_results/webvid_train10k_top32_l64_128_r10_a025_c005_t1_v1_validation10k/`
- `sparse_utility_ranker_variants/{webvid,yandex}_train10k_top32_l64_128_r10_diag_v1/`
- `sparse_utility_ranker_results/{webvid,yandex}_diag_v1_seed*/`
- 完整判断：`sparse_utility_ranker_results/analysis.md`

静态 ranker 已判定跨数据集 no-go：WebVid 等成本仅有小正增益，Yandex 等成本失败。
下一实现若继续，必须是固定总预算的 early-probe trace + selective reroute；不得继续扫
当前 ranker 超参或无证据扩大成通用 MLP/双塔。

### Probe trace 与 budgeted reroute gate

`bench_entry_oracle` 新增两个只读模式：

- `--generate_probe_trace --probe_Ls ...`：保存 router top-32 距离，以及每个 probe L
  的 top-10 IDs/distances、Recall 和 graph NDC；
- `--generate_budget_reroute --probe_L P --budget_pairs target:reroute`：运行 Fast
  baseline、probe+Fast restart、probe+每个 top-32 single alternate，将两次结果按距离
  合并成 top-10，并保存每个 candidate 的 merged Recall/total NDC。

budget reroute schema 现额外保存每个 candidate 的 7 维
`candidate_topology_features`：probe-result membership、与 probe frontier 的一跳邻接、
entry-neighbor/probe 的重叠比例、probe-neighbor union 重叠比例、rank-weighted hit、
0/1/2/3-hop proxy 和有效 degree。它们只读取已加载的冻结 NSG 与实际 L10 结果，
不修改邻接、不执行额外搜索，也不读取 validation GT。

训练脚本：

- `benches/run/train_probe_failure_detector.py`：router-only 与 GT-free probe trace 的
  actionable-reroute detector；`--max-probe-L` 限制可用在线信息；
- `benches/run/train_trace_conditioned_rerouter.py`：连续 merged utility alternate chooser，
  包括 candidate-static、query-level trace、candidate-to-probe-result frontier affinity、
  topology-only 和 frontier+topology；topology-aware report schema version 为 2。

有效预算协议只允许 `max_probe_L=10`，并实际计入 L10 probe NDC。独立 L10/16/32
搜索都作为特征、但只计 L10 成本的早期结果标记为 INVALID。有效 artifact：

- trace：`probe_trace_datasets/{webvid,yandex}_{train10k,validation10k}_l10_16_32_v1/`
- L10 detector：`probe_failure_detector_results/{webvid,yandex}_l10_only_gain01_v2/`
- budget matrices：`budget_reroute_diagnostics/{webvid,yandex}_{train10k,validation10k}_probe10_top32_v2/`
- WebVid chooser：`trace_conditioned_rerouter_results/webvid_probe10_top32_frontier_v3/`
- topology matrices：`budget_reroute_diagnostics/webvid_{train10k,validation10k}_probe10_top32_topology_v3/`
- topology chooser：`trace_conditioned_rerouter_results/webvid_probe10_top32_topology_v4/`
- 决策：`probe_reroute_results/analysis.md`

当前结论：L10 failure detector 跨数据集有效，learned-risk + oracle-alternate 在固定 NDC
下有上限；但 frontier-conditioned 以及新增的一/二跳 topology-aware chooser 均在 WebVid
严格失败。topology-only 和 frontier+topology 在两个预算、四个风险比例上全部降低 Recall、
增加 NDC，故当前 probe-reroute 改进分支最终 no-go，未继续 Yandex chooser。不得为该分支
实现 resumable search、更多通用模型或正式 held-out test。本次 topology gate 不是 GATE；
standalone GATE 的独立适配与结果记录在下一节。

## Standalone GATE WebVid 契约与 artifact

本次只适配 WebVid validation；不读取 held-out test，不修改冻结图。主要代码：

- `benches/export_gate_nsg.cpp`：ACSG 固定宽度图到 GATE variable-degree NSG；
- `GATE/cluster/kmeans.py`：512-hub balanced HBKM 的 Sinkhorn scalable approximation；
- `GATE/cluster/subgraph2json.py`：精确 hub IDs、CSR 图加载、topology-only 且硬上限 1000 nodes；
- `GATE/cluster/graph2vec_embed.py`：确定性 WL(2)+PV-DBOW Graph2Vec；
- `GATE/tests/test_gate_generate_samples_contract.cpp`：读取 exact GT、显式 `ip|l2` metric；
- `GATE/cluster/model/train/{dataset.py,fusion.py,__main__.py}`：严格 CSV、batch-first、独立 validation、固定 seed、早停；
- `GATE/cluster/model/train/export_routes.py`：exact dense-cosine top-3 raw-int32 graph routes。

关键 artifact：

```text
gate_baseline_artifacts/webvid2_5m_frozen_r64_v2/
  nsg.graph
  hbkm512_sinkhorn_seed42_v2/
    hubs.fvecs
    hub_ids.int32
    manifest.json
    subgraphs_topology_h5_n1000_v4/{0..511}.json
    graph2vec_wl2_d512_e10_mc5_seed42_v1/
  gate_samples_router_train10k_ip_l64_k1_v1/
  gate_samples_validation10k_ip_l64_k1_v1/
  config_webvid_gate_uniquehub_max200_patience20_v4.json
  models_webvid_gate_uniquehub_max200_patience20_v4/
  routes_webvid_gate_max200_best_validation10k_top3_v1/
  eval_gate_max200_best_validation10k_r1_r10_3run_v1/
  eval_gate_max200_best_validation10k_r100_3run_v1/
  analysis.md
```

图导出 SHA256 为
`7964aa05de43954c7f280d922fe2005814fe51b97640e65b51938538291829e2`；
512 个 topology v4 子图严格各 1,000 nodes、共 3,276,735 directed edges，组合校验
`4d376e2224966c19264d693b76779008375fbdf906a9ca9644f8f4ebeb94ebab`。
Graph2Vec shape `(512,512)`，独立两次运行 `.npy` SHA256 均为
`07678e37bdbb0ac1d62179e5cf3d89e7445369269844304fc0a565e1f427917d`。

训练样本固定 `L=64/K=1`：prototype-train 10K 中 915 no-hit，按原 GATE filter 最终
8,150 usable queries、652,600 triplets；validation 10K 中 904 no-hit、8,146 usable。
正式训练 `hidden=2024/batch=16384/lr=1e-5/max_epochs=200/patience=20/seed=42`，在
epoch 88 早停，best epoch 68，usable validation RouteAcc `0.0963663`。batch 内唯一 hub
合并仅减少相同 hub 的重复前向；dropout mask 因此按 hub 共享，属于明确记录的计算适配，
不是作者私有训练产物的 bitwise reproduction。

最终 validation 10K×3 的 `status=complete` 结果：Recall@1/10 使用
`L=64/128/200/400`，Recall@100 使用合法的 `L=100/128/200/400`。GATE 相对 Fast
在 12 点全部低 `0.330..3.230 pp`，graph NDC 全部高 `2.83..16.59%`；相对 Medoid
全部高 `0.485..2.580 pp`。按 gate 不运行 Yandex。研究判断与完整表见 `summary.md` 和
上述 `analysis.md`。

候选层级：

- current hubs：现有 QGT IDs；
- broad candidates：仅从训练 GT、Medoid failure trace/frontier、QGT representatives 产生；
- oracle split：只在 validation 上选择最佳 single/top-3/top-5；首个 pilot 只做 single/top-3；
- held-out test 不得使用 oracle 选择结果调参。

输出至少保存：

```text
query_id
candidate_entry_ids
selected_entry_ids
top_m
search_L
Recall@1/10/100
routing_ndc / routing_latency
graph_ndc / graph_latency
total_ndc / total_latency
medoid_delta
```

Oracle 只改变初始入口集合，不得添加、删除或重连底图边。必须同时支持等 `search_L`、等总 NDC 和等端到端 latency 口径。

若 broad diverse oracle 没有 headroom，只能说明当前数据集/底图/预算下 entry-only 已饱和；项目不自动转为 graph repair。

## 历史与辅助材料

- 旧 ACO/Router 诊断、Fast 方法形成过程：`aco_router_fast_entry.md`
- 复现命令：`command.md`
- 相关论文与 TailRisk-Cover 研究设计：`papers/related_work_2026-08-29/README.md`
- 旧 neural graph/PCA/ONNX、SSG、LSH-APG、GATE 目录继续保留；除非明确进入对应基线任务，不得清理或覆盖。
