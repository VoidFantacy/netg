# 01/02/03 与 s-experiment 独立交叉复核

日期：2026-09-08。复核者未撰写被审查的 01/02/03 卡片与根概览。结论：**PASS，发现的两处文档问题已按主维护者授权修复；未发现改变历史结论的数值、数据集身份或最终 gate 错误。**

## 范围与实际操作

完整阅读 `experiment_history/01_fast_and_legacy.md`、`02_multiview_and_attention.md`、`03_baselines.md` 和根目录 `s-experiment.md`。只读取本地小型 Markdown/JSON、manifest、现有源码片段和路径存在性；未打开原始 query/base/GT/图大文件，未计算新 GT，未加载模型，未安装依赖，未运行 ANN、训练或方法实验。

本轮独立对照的关键原件为：

- `fast_entry_benchmark_results/benchmark_summary.md`：双数据集正式 held-out、多 seed、QPS 与 tail 表。
- `fast_entry_variants/laion10m_acsg_v1_validation_report.md`、`laion10m_acsg_v1_heldout_report.md`：两阶段迁移结果和成本/查询来源边界。
- WebVid/Yandex 各三份 `fast_entry_variants/{dataset}_seed20260828/29/30/manifest.json`：实际输入 sources、SHA 与构建 seed。
- `target_basin_formalization/20260907_v1/gate.json`、`pilot/hnsw/report.json`：正式 E1b 参数、总成本四点与 E2–E4 状态。
- `target_basin_meta_diagnostics/v1/decision.json`：共享非零 alpha gate、双数据单独通过项。
- `gate_baseline_artifacts/webvid2_5m_frozen_r64_v2/analysis.md`：GATE 合同、训练与 12 点原表。
- 同目录 `hbkm512_seed42/INVALID.md`：旧无效 HBKM 的具体原因及禁止使用范围。
- `hierarchical_target_search/20260907_v1/dependencies/README.md`、`dependencies/manifest.json`、`state.json`：准备状态、源码版本、依赖边界与后续夜间终态。

历史数值按原件复核；本次没有重测其底层数组或刷新完整机器环境，不能把文档审查当作新性能验收。

## 核对结果

| 项目 | 独立核对内容 | 判断 |
| --- | --- | --- |
| Fast 正式 WebVid | Recall@1 +0.803～+1.310 pp、Recall@100 +0.211～+0.320 pp；同次 Medoid 归一化 QPS 差与原报告一致 | PASS |
| Fast 正式 Yandex | 使用 `yandex_t2i_official10M_ip_v1`；Recall@1 -0.213～+0.003 pp、Recall@100 -0.020～+0.018 pp；明确“接近”不是统计等效 | PASS |
| 旧 NETG 与 official 隔离 | 旧 `总结.md` 的五数据集时间、旧 Yandex tail 只作为历史陈述；未替换 official first-10M/IP 数值或并入当前单数据集成本 | PASS |
| Fast seed 与运行次数 | 三个 build seed 的 Recall 方差与每 artifact 三次 timing 分开；同一训练样本的 seed 变化没有写成独立 query task | PASS；02 另作措辞修复 |
| Fast 成本 | 旧四阶段 6501.94 s、秒级 post-GT builder、cache、未含 Micro-HNSW 与 exact-GT 的边界分开；没有将其称为全训练成本 | PASS |
| LAION | validation/held-out 两批全部范围、冻结图 SHA、821 hubs、三 seeds×三 timing、约 46/50 分钟 batch wall 与原件一致；保留共享 WebVid public query 来源限制 | PASS |
| Multi-view 最终 gate | `NO_GO_ROUTING_COST`、selected_method Fast v1、E2/E3/E4 `NOT_RUN`、heldout false 均与 gate 一致 | PASS |
| Multi-view E1b 数值 | 四点匹配 L=22/80/44/104，Recall Δ=-14.697/-4.960/-4.103/-1.463 pp 与原 JSON 一致；routing 与 total NDC 分开 | PASS |
| Multi-view 未测量项 | 原 JSON 明确 timing 未跑；卡片没有伪称 wall 实测失败，也没有把 count JSON QPS 当纯 wall 通过 | PASS |
| Confidence attention | WebVid 只通过 alpha=-0.5、Yandex 只通过 +0.5，共享交集为空；卡片没有让旧保留 alpha=0 覆盖后来 Multi-view no-go | PASS |
| GATE | CPU/raw-IP/同图适配、512 hubs、Graph2Vec、10K/10K checkpoint-selection 范围、best68/stop88、46m41.73s 和全部 12 点原表一致 | PASS |
| GATE 外推 | 训练 wall 没有冒充完整离线成本；graph NDC 没有冒充端到端 QPS；Yandex 未运行和作者 release 差异明确 | PASS |
| 依赖准备 | manifest 中 `research_experiments_run_this_preparation=false`；15 个新增系统包、原有 0 升级/删除、gp-ann MIPS 编译、LIRA CPU smoke、RoarGraph help 均作为准备证据 | PASS |
| 旧暂停与最新终态 | preparation 的 `PAUSED_BY_USER` 没有覆盖后来 `TIMEBOX_STOPPED_REPORT_COMPLETE_P3_NOPASS`；安装与后续 P2/P3 分开 | PASS |
| 环境路径 | 两个环境脚本确实位于 `hierarchical_target_search/20260907_v1/tools/`；根 `tools/env.sh` 与 `tools/roargraph-env.sh` 均不存在，卡片写全路径正确 | PASS |
| s-experiment 导航 | 已执行、准备、设计、未跑阶段分开；Fast/LAION/Multi-view/GATE 行与三张卡一致；有“进入详细卡及原件”的强制阅读规则 | PASS |

## 发现并完成的两处修复

### R1：02 的三 view 训练样本表述有歧义，已修复

原句“各 view 用独立 QGT 5K 与旧 prototype-train 30K”可能被读成三个 view 分别重新抽样。对 WebVid/Yandex 各三个 seed manifest 的整个 `sources` 字典进行小文本比较，两个数据集均为 `all_sources_equal=True`。

现改为“三个 view 复用同一份 QGT 5K 与同一份旧 prototype-train 30K，仅改变聚类 seed；QGT 与 prototype-train 彼此独立，不是三个 view 各自重新抽样”。这与 01 的三 seed scope 及 02 的“一个 ensemble instance”一致，避免产生新的独立性主张。

仅修改 02 第一节对应段落，没有修改原 manifest 或历史路由产物。

### R2：03 没有解释概览提及的无效 HBKM 版本，已补齐

`s-experiment.md` E17 写“无效 HBKM 版本另存”，但原 03 卡片只介绍有效 Sinkhorn v2。读取既有 `hbkm512_seed42/INVALID.md` 后，新增一段具体说明并链接原件：旧 stale-size batched penalty 虽输出 512 hubs，簇大小为 1～11,376，未遵循 Algorithm 2 动态 balance state，因此禁止用于 GATE 结果或论文表。

明确旧目录保留、有效 `hbkm512_sinkhorn_seed42_v2` 不与其混算；Sinkhorn 是项目适配，修复后也不能写成作者算法逐位复现。仅补 03 对应机制段，没有改旧 INVALID 文件或结果。

## 最终检查与文件身份

对三个历史卡和概览全部 Markdown 相对链接执行本地存在性检查，**失效链接为 0**。以下 SHA256 为本轮修复完成时的小文本文件快照，供后续维护判断是否仍为已审版本；不是对其引用的大数据重新计算的哈希。

| 文件 | SHA256 |
| --- | --- |
| `experiment_history/01_fast_and_legacy.md` | `f9bf71bbd7fd301f9dd6133795b4458d3315999b80de7cf8d24dec89f582ce59` |
| `experiment_history/02_multiview_and_attention.md` | `33ac602d79b8d9ec4b187a1ede18f48c9b89d9916314f00afe64d318d08dfe38` |
| `experiment_history/03_baselines.md` | `eb5f291b246849ee1c7fcb0ff13ecff7b2cb1ac00b7858862a295b24c720d201` |
| `s-experiment.md` | `9c490b9e415bfb6a649da16ff1dd8a41b95fcc3bc144d87fbbaf372dd38cb8f9` |

该检查范围内没有待处理的阻断项。01 和根概览未被本复核者修改；02/03 仅包含上述两处授权文档修复。没有新增研究结论、性能 GO 或继续实验授权。
