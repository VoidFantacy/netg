# 文档重整完成审计

2026-09-08。此审计针对用户要求的文档结构与内容，不是方法实验验收。核查对象为当前工作区成品；旧结果依据原报告/配置/审查复盘，不重新运行实验。机器链接/保护检查及最终文件身份见同目录`document_checks.json`与`delivery_manifest.json`。

## 用户要求与当前证据

| 用户要求 | 当前交付与验证依据 | 判定 |
|---|---|---|
| spec是代码架构契约 | 根spec维护真实Fast调用链、模块/API、split/metric/NSG、入口/pool/visited、artifact与成本、环境及变更依赖。未实现B/A/C/D和树明确分开；完整旧spec留source_before，历史章节号不冒用新版编号。主维护者完整阅读；document_contract_review逐条检查必要合同迁移。 | PASS |
| summary是当前实验总结 | 根summary只以最近实际完成的Fast根因诊断为中心，含数据/执行、数值、当前判断、analysis/costs v2与推断限制；研究设计明确未实现、没有新方法GO，旧分支走历史索引。 | PASS |
| s-target是下一阶段目标，同spec/summary目录 | 根s-target明确先完成B/A/C各自R0，再依次有界探索B→A→C；各有机制、对照、数据/成本、实现及结果门槛、停止条件、写回流程。D暂缓，树作共同参照；未实现工具不写成可执行命令。本轮文档任务未启动探索。 | PASS |
| 新建s-experiment，检查拼写，同spec目录 | 根文件实际存在，使用正确单词experiment和用户给定的单数文件名；E01–E20提供已做内容/有限判断/详细入口，另列准备与未执行设计。 | PASS |
| 新目录保存历史详细情况，索引置于s-experiment | experiment_history含README及01–09九份实质记录；覆盖20类实验与诊断，包含动机、监督/实现、输入配置、结果、成本、版本修正、停止/未知和原件位置。详细层保留原产物路径，未搬走大型数据。 | PASS |
| 不确定须进入目录详细复盘 | AGENTS、spec、s-target、s-experiment及README均要求“概览→完整历史卡→原协议/配置/state/gate/结果/修正”；证据仍不足标为未确认，不能只据摘要/记忆判定失败或重做。 | PASS |
| 旧记录不能因精简而丢失 | 整理前AGENTS/spec/summary/s-target完整快照在source_before；旧实验目录、原实验总结/早期总结/Fast审计/README保留并在01/07及索引分流。旧版本delivery清单保留当时身份，不回写。 | PASS，保护范围见机器报告 |

## 人工复盘覆盖

- 主维护者完整阅读当前AGENTS、四主文件、README及01–09九卡，并核对专题审查和最后补充。01/02/03由未撰写它们的复核者对照正式Fast/LAION/Multi-view/GATE原报告、manifest和gate；04/05/06由另一复核者对照原报告、decision及源码。两份交叉审查分别保存为`baseline_history_review.md`、`history_cross_review.md`。
- `document_contract_review.md`检查根文档职责、未执行状态、计划顺序、07/08/09与历史访问合同；07/08作者直接完整读了对应原协议/统计/gate/成本/独立审查。它对自己卡片的检查没有包装成新的独立实验重算；主维护者再完整阅读成品。
- 01的更早结果补充仅核小型报告/源码与目录身份，明确旧数据/版本局限；没有把旧JSON存在性等同于当前正式评测有效性。覆盖的是实验家族与原始追溯入口，不宣称每个旧输出行重新验算过。
- 不联网刷新既有文献、重算原始矩阵/统计或重新证明旧实验性能。新方向是否成立由下一阶段门槛判断，当前完成只证明文档交付。

## 已解决的复核问题

1. 02明确三view复用同一QGT/prototype输入，仅改变聚类seed；避免误称独立样本。
2. 03补齐无效HBKM的stale-size balance缺陷、簇大小1–11,376、INVALID原件和有效Sinkhorn适配区别。
3. 04明确modes表来自validation10K，补train阶段结果，后20K隔离只适用于本节modes；utility residual使用前10K标签。补BTG v1–v4修订与v3/v4数值/路由SHA相同的边界。
4. 根索引E08改为“局部同L Recall提升、未证同成本/跨数据收益”，保留centroid真实正信号。E09也保留utility residual微正；finite-beam旧terminal以审计修正为准。
5. spec补充`acosp_nsg.json`实际上是内嵌base的二进制索引，不能按后缀作JSON或无界文本读取。依据已存input_source_audit，不新开大索引。09的旧delivery身份描述改为“当时主文档”，不虚称历史已包含新建s-experiment。
6. 01补充旧results、多入口基线、逐query数组和summary_tables目录入口，明确其旧数据身份与未在本轮统一复核的限制。

专题review内SHA固定各自审查当时版本；上述最后的局部补充由主维护者复核，最终身份以delivery_manifest为准，不能用早期review SHA冒充最终文件。

## 执行范围与保护边界

本轮只新增/重整文档及维护检查产物，没有安装、训练、ANN、GT生成、性能测量或源码修改，没有删除/移动原实验产物。根AGENTS的职责同步属于落实四文档契约。

存在一次已披露I/O例外：历史卡作者误将WebVid二进制`acosp_nsg.json`作为文本读取，读取字节后UTF-8解码失败；没有成功解析对象、运行搜索、修改索引或继续读取Yandex。详情保留在document_contract_review，不将本轮概括成“完全未碰图字节”。没有打开原始query/GT文件。

保护检查逐一比较整理前清单的144个既有小文件之size/SHA，包括4个关键源码与旧诊断/研究文档。该范围不等于重新hash所有大型base/graph/模型；原工作区预存dirty状态不被重置或据此当作本轮改动。链接检查只证明目标存在；历史结论仍由上述原件阅读与审查支撑。
