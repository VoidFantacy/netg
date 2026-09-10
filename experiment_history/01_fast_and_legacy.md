# Fast v1 与旧 NETG / ACO 实验复盘

本页按原报告、manifest 和相关源码整理，核对日期为 2026-09-08。它保存历史实验及适用边界；当前研究判断见 [summary.md](../summary.md)，实现契约见 [spec.md](../spec.md)。本次整理没有新训练、ANN 评测或原始查询/GT 读取。下文 pp 表示 Recall 的绝对百分点，NDC 表示实际距离计算次数。

## 1. 为什么从旧 NETG 转向 Fast

旧 NETG 的链路是冻结 NSG → ACO 信息素/节点权重 → DPC hubs → 对每个 query×hub 做真实搜索标签 → Neural Router 离线变换 hub → 在线小索引选入口。它已经使用图搜索可达性监督，不能把“使用真实搜索监督”写成后续方案首次提出。线上使用离线导出的 hub 表示也不意味着完全没有路由成本。

[ACO / Neural Folding 原审计](../aco_router_fast_entry.md)记录 WebVid 正式运行：

| 阶段 | 实测 wall | 范围 |
|---|---:|---|
| NSG | 879.86 s | 公共底图；不计入入口层替换倍率 |
| ACO | 1591.43 s | 50 轮 |
| DPC | 307.12 s | 依赖 ACO 权重 |
| 逐 hub 标签 | 2755.44 s | 30K 查询遍历约 815 hubs，约 2445 万次 query×hub 探测 |
| Neural Router | 1847.95 s | 155 epochs、约 90,985 optimizer steps |

四个查询相关阶段合计 6501.94 s，约 108 分 22 秒，不含 exact train-GT。最大单项是标签生成，不能仅归咎于 ACO 或神经训练。[机器审计](../logs/webvid2_5m_light_v1/training_bottleneck_audit.json)显示 ACO 无非有限 loss/空路径，但第 5→50 轮 avg error 只改善约 0.332%；zero-error rate 85.294%→88.434%，avg hops 却 3202.33→3412.25。

原审计据源码提出的机制解释包括：零误差奖励主项约 10^6，精英集合大量同为零误差；400 个随机初始化节点也进入被强化的 path；信息素指数 10、启发式指数 0.01 易强化已有选择。这些解释支持目标和路径定义存在问题，不是严格因果消融结果，也不是数值发散。

30K Router labels 仅 25,067 有效；最优 hub 的 raw 几何 rank 中位数 207，hit@64 仅 26.57%，因此简单几何预筛会丢失大量既有正标签。训练还存在 hard-negative 刷新引起目标变化、同标签样本互为负例、`min_ndc` 不参与权重、single 标签与在线 top-3 / Recall@10/100 目标不一致等问题。它们解释了为何当时选择替换整条昂贵入口构建链，而没有继续增加 epoch/MLP。

### 旧 ACO-Max 结果的实现缺陷

现场复核 [benches/test.cpp](../benches/test.cpp)：加载 ACPG 后在约第 487–490 行释放 weight；随后 `EntryPointSearcher::load` 在约第 150–159 行才尝试取最大 weight，空数组回退到 `enterpoint`；ACO_WEIGHT 分支约第 377–379 行又优先使用 `center_max_points_[0]`。因此该 legacy 槽不能直接解释为真实 ACO 最大权重点消融。它与有效 Formal Neural / Fast 对照的身份分开；缺陷修复并重新验证前，旧 ACO-Max 不应进入有效比较。此次只记录缺陷，没有改源码或重跑。

## 2. Fast v1 的设计与固定输入

Fast 用 `QGT-Cover + closed-form GT-basin prototype + Micro-HNSW top-3` 替代上述四阶段。独立 5K QGT 查询及 exact top-100 GT 做 spherical query k-means；每簇按与中心的相似度遍历成员，从其 GT 选择尚未使用的真实 base ID。QGT-Cover 是项目内启发式名字，不是带近似保证的 set cover。

独立 30K prototype-train 查询先取各自 GT1 base 向量，把该目标按 cosine 分到 raw hub basin；每个 basin 累加单位查询及权重 1 的单位 raw-hub prior，最后归一化成“查询画像”。线上 raw query 查询画像 Micro-HNSW，映射 top-3 真实 base ID，调用原 `search_new` 搜相同 NSG。它不读取 ACO/DPC/probe labels/Neural bins，不运行 optimizer/MLP；它仍依赖 exact train-GT。结果槽 `Asym-Neural/NETG_AsymHNSW` 在 Fast artifact 中仅是沿用名称。

| 固定项 | WebVid | Yandex 正式版 | LAION |
|---|---|---|---|
| dataset key | `webvid2_5m_light_v1` | `yandex_t2i_official10M_ip_v1` | `laion10m_acsg_v1` |
| base | 2,505,000×512 | 官方 first 10,000,000×200 | 10,004,480×512 |
| 距离/预处理 | IP，源近单位，不额外归一化 | raw IP，不归一化 | base/query 显式单位化后 IP |
| QGT / prototype / validation | 5K / 30K / 10K 独立 split | learn [0,5K) / [5K,35K) / [35K,45K) | seed 20260830 去重抽取 5K / 30K / 10K |
| held-out | public 10K | public 前 10K | public 10K |
| hubs | 815 | 821 | 821 |
| NSG | R64 / L_build100 / C512 | 同左 | 同左 |

正式 Fast seeds 均为 20260828/20260829/20260830，只改变同批训练样本上的聚类初始化；每个 seed 各点 3 timing runs。Recall 方差来自三个 build seeds，重复计时不增加 Recall 独立样本数。新诊断/分层版本用后 20K 拟合的 paired Fast 是另一个契约，不能把本页 30K 结果混入新训练链。

## 3. WebVid / Yandex 正式 held-out 结果

先有 WebVid 三 seed 与 Yandex 单 seed 轻量复现，随后 2026-08-29 完成双数据集同批三 seed×3-run 汇总。早期 [aco_router_fast_entry.md](../aco_router_fast_entry.md)开头“Yandex 仅一个 seed”是阶段记录，已由其末尾更新及[正式报告](../fast_entry_benchmark_results/benchmark_summary.md)覆盖。

两数据集均 held-out 10K；WebVid Recall@1、逐 query Recall@10 的 L=64/128/200/400，Recall@100 的 L=100/128/200/400；Yandex另加 L=800。所有 K≤L，禁止把 K100/L64 作为有效点。Formal 每点 3 次，Fast 3 seeds×3 次；不同 invocation 的速度判断优先看同次 Medoid 归一化比值。

| Fast Prototype − Formal Neural | WebVid | Yandex official 10M/IP |
|---|---:|---:|
| Recall@1 差 | +0.803～+1.310 pp | −0.213～+0.003 pp |
| Recall@100 差 | +0.211～+0.320 pp | −0.020～+0.018 pp |
| R@1 对应 Medoid-normalized QPS 差 | +1.15%～+9.67% | +1.34%～+7.16% |
| R@100 对应 Medoid-normalized QPS 差 | +1.83%～+8.89% | +1.14%～+5.53% |

WebVid 在已测点体现效果与速度双提升；Yandex 的 Recall 接近旧 Formal Neural，主要优势是较简洁入口构建与小幅归一化 QPS 提升，不能说所有 Recall 点都超过 Neural，也不能将描述性“接近”写成统计等效检验。

逐 query Recall@10 的阈值固定 0.1/0.2/0.5/0.8，必须按 query ID 对齐后计算 rescued、newly-harmed 和净救回。两数据集全部已测 L×阈值相对 Medoid 净救回为正；WebVid进一步优于 Neural，Yandex总体接近。例如 L64、阈值 0.1：WebVid Medoid 失败 8.84%，Fast 4.63%±0.17%，平均 rescued/harmed=660.0/239.3；Yandex 4.99%→2.84%±0.13%，357.7/143.0。Fast 仍伤害部分查询，不能只报救回。

正式报告的 QPS 与 tail 使用独立进程；图中纯搜索 QPS 不包含事后 tail 计算。它是该批次测量证据，不自动满足后续新方案更严格的 routing/graph/total 拆分、纯 wall 匹配和全离线成本协议。

## 4. LAION：已完成 validation 和 held-out 的迁移控制

LAION 的 unit-IP 冻结图 SHA 为 `7040cd0a2b8f5d34b3e3affbbcb30ce19c947731a8a81c40ec64f0e0d99bb238`。validation 10K exact-IP GT 于 2026-08-30 完成，public held-out 10K 于 2026-08-31 完成；后者使用官方 top-500 截取并核验的 top-100。三 seed 的 held-out hubs/IDs/prototype checksum 与对应 validation artifact 一致，test 未参与构建或调参。

Recall@1 与 tail 的 L=64/128/200/400，Recall@100 为 L=100/128/200/400，每 seed×方法×L 三次计时。

| Fast − Medoid | validation | held-out |
|---|---:|---:|
| R@1 增益 | +0.687～+2.067 pp | +0.280～+1.723 pp |
| R@1 的同次归一化 QPS | +3.87%～+11.88% | +4.03%～+11.82% |
| R@100 增益 | +0.373～+0.667 pp | +0.242～+0.777 pp |
| R@100 的同次归一化 QPS | +3.57%～+9.33% | +3.68%～+9.77% |

两批全部八个 Recall 点 prototype 都超过 QGT-Raw；全部 16 个 L×tail 阈值对 Medoid 净救回为正。held-out L64 的 R@10<0.1 失败率 4.29%→2.72%，平均净救回 156.7。validation 全批约 46 分钟，held-out 约 50 分钟，单搜索进程 max RSS 约 21.6 GiB；这些是全评测批次耗时，不能当入口训练耗时。

**外推限制：LAION 与 WebVid public query 源文件相同（MD5 相同），所以这是不同 image corpus/规模的迁移证据，不能算第三个独立 query workload。** 初轮未单位化的 raw-IP/raw-L2 产物无效，以[失效说明](../benches/datasets/LAION10M_acsg_v1/INVALID_RAW_IP.md)为准。原 held-out 报告的“下一步”保留历史建议身份，不自动排队或授权继续 test 调参。

## 5. 成本结论与尚未测量部分

旧 WebVid Fast builder 冷加载记录 12.14～13.06 s，热 page cache 1.24～1.27 s；早期 Yandex 为 16.58 s。相对旧四阶段的数百倍缩短仅是 **已有 exact GT 后的阶段替换**，还受 cache 影响。LAION held-out 首 seed builder 约 19 s、后续约 1 s，validation 热 cache 小于 1 s，同样不能称完整训练。

当前 `build_wall_seconds` 不含 exact train-GT，也不含 evaluator 内构建的 Micro-HNSW。完整成本应为 `T_exact_train_GT + T_QGT + T_prototype + T_router_index`，共享 GT 只计一次；未知项保留 null+原因。完整 GT-inclusive break-even、统一新纯 wall 的强系统基线仍没有完成，不能从秒级 builder 或同 L Recall 推出所有成本口径的优势。

已知旧无效文件 `fast_entry_variants/webvid2_5m_light_v1/eval_qgt_vs_prototype_r1.json` 的 raw 槽发生 vector/ID 错配，不进入后续汇总。有效现存结果也不因新研究方向出现而删除。

## 6. 更早五数据集 NETG 评审与 README 的身份

根目录[总结.md](../总结.md)是更早的 NETG 评审记录：旧 Yandex tail 6.90%→4.16%，Deep/SIFT/Gist baseline tail 接近 0；五数据集合计 ACO 约 5482 s、DPC 6532 s、labels 10366 s、Router 206 s，总约 6.3 h。该文没有在摘要中绑定当前 official first-10M/raw-IP 的 split、图 SHA、L 与重复契约；本轮未对旧数组做同口径复核。故这些是旧报告陈述，不能覆盖本页正式 Yandex 的数值、也不能把五数据集总时间并入当前 WebVid 或 Yandex 单数据集成本。

旧[readme.md](../readme.md)保留 ACO→DPC→labels→Neural 流程、五数据集画图入口与旧 Yandex 消融索引。其 `cmake ../benches` 等构建指令不作为当前根工程构建方式；`plot_result.py` 中嵌入曲线也不自动构成当前 manifest 绑定的正式结果。历史提出的敏感性/新数据集工作是当时建议，不是本轮完成项或当前授权。

以下旧结果目录实际存在，不能因主线转向而遗漏。此补充只核对目录元数据、≤100KB的小JSON/CSV和对应脚本；未打开较大的逐query数组、bin、索引或原始query/GT，也未重算旧性能。

| 旧目录与可点击入口 | 已保存内容、数据及方法身份 | 使用限制 |
|---|---|---|
| [results/](../results/)，示例[deep/acos_nsg.json](../results/deep/acos_nsg.json)、[绘图源](../results/plot_fig.py) | `deep/glove/sift100K/sift1M`四目录，各有`nsg/mrnndescent/acos_nsg/acos_mrnndescent`小曲线，共16文件；字段是L、NDC、mean_rdrr | mean_rdrr不是本页Recall@10；这些小文件没有当前split/metric/图SHA/计时身份，NDC聚合口径也未在本次补充重新验证，不能转成当前QPS或正式Recall。`results/test.py`还有内嵌示例数据，不能取代原JSON。 |
| [multi_entry_baselines/](../multi_entry_baselines/)，示例[kmeans800](../multi_entry_baselines/deep10M_results/kmeans800.json)、[random3](../multi_entry_baselines/deep10M_results/random3.json)、[旧Yandex r100](../multi_entry_baselines/yandex_t2i_results/kmeans800_r100.json) | 旧`deep10M/sift10M/sift10M_skewed/yandex_t2i/gist1M`五数据，每个保存kmeans800/random3及其`_r100`文件，共20曲线，另有Gist smoke。生成脚本取随机3个真实点(seed42)，或从最多500K base样本(seed123)做800簇、20轮k-means(seed42)，选样本内最近真实点并去重 | kmeans800是目标簇数，去重后真实hub数可能少于800。两类JSON均沿用`Raw HNSW Routing`结果槽，方法身份须结合文件名与[runner源码](../benches/run/run_multi_entry_baselines.py)；其旧命令指定`--R 32`、3 runs、L32/64/128/200，不能冒充当前R64正式图。`_r100`是历史文件命名，精确K/生成命令仍须追原记录，不仅凭名字猜。 |
| [per_query_recall_results/](../per_query_recall_results/)，[小型summary.json](../per_query_recall_results/summary.json)；[per_query_recall_results_r10/](../per_query_recall_results_r10/) | 同一旧五数据集，各5个逐query结果；前者小summary列`NSG_Medoid/NETG_AsymHNSW/Raw_HNSW_Ablation`的均值、分位数与阈值占比。[R1脚本](../benches/run/run_per_query_recall.py)明确K1，[R10脚本](../benches/run/run_per_query_recall_r10.py)明确K10，均列L64/128/200/300/400/512/800/1024 | 旧[实验说明](../per_query_recall_experiment_README.py)将R1列为早期弃用、R10为后续报告口径；这不使R1文件消失。该说明仍含旧主机绝对路径，应按项目相对文件定位。大数组本轮仅核对存在/大小，不复算tail、aligned身份或统计；旧Yandex不能与official first10M/raw-IP混用。 |
| [summary_tables/](../summary_tables/)，[performance_summary.json](../summary_tables/performance_summary.json)、[ablation_summary.csv](../summary_tables/ablation_summary.csv)、[hbkm_vs_wdpc.csv](../summary_tables/hbkm_vs_wdpc.csv) | performance表覆盖旧deep/gist/glove/sift1M/sift10M/sift100K的standard/ACO/DPC-ACO各自最高QPS和最高Recall端点；两个CSV覆盖旧五数据，在L100/300/600汇总Medoid、ACO-Max、W-DPC、Full NETG及HBKM对照 | 各方法自己最高QPS/Recall端点不是同Recall或同成本比较；这些摘要未绑定当前正式provenance，ACO-Max仍受本页已记实现缺陷约束。不能凭旧表存在就认定当前基线已有效复验，也不能把汇总数字升级为新的实测结果。 |

## 7. 原始材料索引

- 正式双数据集：[完整表格](../fast_entry_benchmark_results/benchmark_summary.md)、[JSON 汇总](../fast_entry_benchmark_results/benchmark_summary.json)、[search CSV](../fast_entry_benchmark_results/search_metrics.csv)、[tail CSV](../fast_entry_benchmark_results/tail_metrics.csv)、[原始结果目录](../fast_entry_benchmark_results/raw/)。
- LAION：[validation 报告](../fast_entry_variants/laion10m_acsg_v1_validation_report.md)、[held-out 报告](../fast_entry_variants/laion10m_acsg_v1_heldout_report.md)、[validation JSON](../fast_entry_variants/laion10m_acsg_v1_validation_multiseed_summary.json)、[held-out JSON](../fast_entry_variants/laion10m_acsg_v1_heldout_multiseed_summary.json)。
- 输入 manifest：[WebVid](../benches/datasets/WebVid2.5M_light_v1/manifest.json)、[Yandex](../benches/datasets/YandexT2I_official10M_ip_v1/manifest.json)、[LAION](../benches/datasets/LAION10M_acsg_v1/manifest.json)；示例 [Fast seed manifest](../fast_entry_variants/webvid2_5m_light_v1_seed20260828/manifest.json)。
- 方法与复跑来源：[builder](../benches/run/build_fast_entry_variants.py)、[双数据集 runner](../benches/run/run_two_dataset_fast_benchmark.sh)、[旧审计](../aco_router_fast_entry.md)、[旧训练机器审计](../logs/webvid2_5m_light_v1/training_bottleneck_audit.json)。这些脚本此次只读，不表示应现在执行。
