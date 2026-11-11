# 2026-10-24：结论同步、当前文档整理与文件清理

用户要求“把结论同步一下吧，顺便清理过时的结论和文件”。本次仅做文档与文件维护，不新增实验编号，不运行训练、ANN、GT、构图或性能测试，不修改默认。

## 当前应读哪里

[项目入口](../../../LOCAL_CODEX_START.md) → [summary](../../../summary.md) → [spec](../../../spec.md) → [s-target](../../../s-target.md) → [s-experiment](../../../s-experiment.md)。最新研究仍是E184离线诊断，最新正式性能仍是E183；GT10默认与E99共享NSG实现保持。

本次同步的中心结论是：空间结构与主搜失败有关，静态残差收益另受遗漏目标重现、路由和容量保留约束。Deep/SIFT源外主导、GIST路由/保留损失明显；七集相关与粗分层不是因果证明，不能据此把补全统一设为默认。

## 文档整理

- 四根文档从486947 bytes、2315行整理为一份各司其职的现行视图，不再堆叠互相矛盾的“CURRENT/最新”章节。精确前后大小见[document_changes.json](document_changes.json)。
- README不再以E173及ACO→DPC→Neural Router充当当前主线；LOCAL_CODEX_START不再同时提供多个过期阅读顺序。旧Deep/SIFT/GIST“尚未接入”和旧运行/截止安排移出当前文档，七集数据/metric合同按E183实际配置维护。
- `实验总结.md`、`总结.md`、`研究方向.md`、`advisor_progress_report.md`、`recent_ten_days_report_20260911.local.md`、`finite_beam_reachability_goal.md`、`aco_router_fast_entry.md`、`command.md`的全文归档，原路径改为短跳转。旧引用仍能找到历史原稿。
- [全部186份详细历史卡片](../../README.md)继续使用原文件名与字节，包含90a补充勘误；未将卡片编号误当正文E编号。旧s-target的2026-10-03交接锚点保留兼容入口。
- AGENTS补充“单一当前视图”和按引用核查清理的维护规则，原四文档职责与用户研究约束保持。

## 历史归档与原字节

清理前16份文档原字节位于[source_before](source_before/)，SHA与大小见[before_manifest.json](before_manifest.json)。这些原件保留原工作区相对链接的语义。

便于直接查阅的副本位于[archive](archive/)；增加历史时点说明并修订Markdown链接，旧命令与“当前/待执行”保留原文，均不作为今天的运行队列。可读副本只是文档归档，不新增实验结果。

| 旧文档 | 历史可读全文 |
| --- | --- |
| 当前摘要旧全文 | [summary](archive/summary.md) |
| 完整旧模块契约 | [spec](archive/spec.md) |
| 旧目标/预算/截止安排 | [s-target](archive/s-target.md) |
| 旧实验长索引 | [s-experiment](archive/s-experiment.md) |
| 旧交接提示词 | [LOCAL_CODEX_START](archive/LOCAL_CODEX_START.md) |
| 旧NETG介绍/命令 | [readme](archive/readme.md) |
| 原协作约定 | [AGENTS](archive/AGENTS.md) |

E184交付时的`delivery_validation.json`及`finalize.py`对应当时的根文档布局。本次整理不回写该历史验收；当时根文档的完整字节已经由本维护快照承接，不能在新根布局直接重跑旧suffix门后把合法整理误判成科学结果损坏。

## 实际清理文件

只在项目研究脚本和benches/run范围内核查缓存，不触碰解释器环境、build依赖或模型资产。文件被Git跟踪、basename在源代码/文档/metadata文本中有引用、无可重建源码或非普通独立文件时均保留。

- 删除194份确认无上述引用、可由保留源码重建的`.pyc`缓存。
- 保留502份有引用或封存意义的候选缓存；某些旧manifest确实登记了`.pyc`，没有按缓存名统一删除。
- 删除1份Finder `.DS_Store`元数据，以及E184首失败尝试的空输出目录；首失败日志和所有科学文件保留。
- 删除文件共4264554 bytes（约4.07MiB）；不是大型资产清理，也不把整理后文档压缩量当磁盘净释放量。

逐项路径/大小/SHA、扫描范围及原因见[cleanup_plan.json](cleanup_plan.json)、[引用证据](cache_reference_evidence.json)与[实际清理收据](cleanup_receipt.json)。原向量、GT、图、模型、实际返回、计时、失败日志、论文PDF、Git发布快照和依赖环境均未删除。

## 核验

本次核对所有新当前文档的本地链接、旧锚点、186卡片覆盖、E183/E184关键原件和详细卡片的236份保护身份、原字节快照、缓存删除/保留清单以及归档链接相对原稿没有新增缺失。结果写入[validation.json](validation.json)，完整维护文件身份在[manifest.json](manifest.json)。

旧报告本来存在的断链单列，不凭空声称全部历史依赖已恢复；本次只要求不新增历史断链且当前入口完整。没有Git提交或发布，没有新实验、默认变化或后续运行队列。
