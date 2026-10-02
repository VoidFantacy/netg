# ACSG 第7串行研究会话汇报

E79–E81三组固定改进均完成两数据集构造和真实ANN，判定以各自预锁门为准。本会话结束，整日21:00目标未完成；E34晚间最终对照仍待执行。

| 实验 / 数据 | 对原P净命中 / 失败变化 | 对compact净命中 / 失败变化 | 原门 |
|---|---:|---:|---|
| E79 / WebVid | -11 / +7 | +48 / -4 | FAIL |
| E79 / Yandex | +0 / -2 | -120 / +11 | FAIL |
| E80 / WebVid | -39 / +17 | +20 / +6 | FAIL |
| E80 / Yandex | -12 / -3 | -132 / +10 | FAIL |
| E81 / WebVid | -78 / +8 | -19 / -3 | FAIL |
| E81 / Yandex | +58 / -11 | -62 / +2 | FAIL |

E79将父hub内分组特征由query换成全GT10目标均值；E80用原GT逐rank归属权重，形成该hub条件目标；E81恢复原query分区，再以query与条件目标的等权双视角目标更新。同一真实hub始终保留父P，最后子画像聚合原query、使用原rawhub先验。变更均在离线，小HNSW仍只覆盖815/821个真实入口，NSG/base/GT/rawIP未变。

几何目标提高、训练集分区改变或NDC变化均不等于NSG效用。目标方向也影响子支持、画像容量和图，当前比较不是单一中介因果识别。各版旧收益保留、丢失、新收益/损伤与GT成员集合增损均在分阶段报告；E73/E74 Yandex局部正信号保持，不能被三个新版本的失败抹去。

本会话新增QPS点 **0**，没有新的完整性能改进证据。最新完整开发曲线见[E74 QPS–Recall、QPS–失败率与按L三指标](../stage15_compact_wall_v1/report.md)，这是其独立历史批次，不能与本会话L128质量点拼成一条曲线。晚间最终必须冻结候选后同批比较原NSG/Fast/GT10匹配起点/实际新方法。

实际新增388,608 NSG / 387,840 HNSW / 8真实build / 8离线画像训练；另2套E66原Q分区复现。离线总操作wall 1220.262s，构图 1.485s，native 331.417s。0新增GT/梯度/编译。继承GT/P成本未知，操作wall包括加载/count/I/O，不是QPS。

五主方法失败并集 **503** 个dataset/source-row，**319** 条失败状态变化；Web/Y全方法失败分别93/91条。失败严格为零GT10集合命中。已独立评分79520条返回，跨批共有P/compact 63616行全字段复现；此处仅缓存质量诊断。全表含GT10、各方法入口/返回ID，图按源行展示每集前24变化例，不挑好例。

[完整失败查询](failure_queries.csv) · [失败图](failure_queries.png) · [E80标签留白修正版](conditional_modes_v2.png)。E80原图、原源码和原封条保持，修正版仅改变y轴留白。

P-fit20K包含旧train/monitor，aux7952及两半为已观察且用于训练决策的辅助反馈，cal/audit历史使用。E34历史validation2000与held-out本会话未打开。后继会话不得将这些开发反馈包装为未见数据。所有ANN CPU15、实际进程/库1线程串行，native工具实际退出后才分析。

[E79完整报告](../stage20_target_space_modes_v1/report.md) · [协议](../stage20_target_space_modes_v1/protocol.md) · [成本](../stage20_target_space_modes_v1/results/cost.json) · [封存](../stage20_target_space_modes_v1/reviews/final_artifact_freeze.json)
[E80完整报告](../stage21_hub_conditioned_targets_v1/report.md) · [协议](../stage21_hub_conditioned_targets_v1/protocol.md) · [成本](../stage21_hub_conditioned_targets_v1/results/cost.json) · [封存](../stage21_hub_conditioned_targets_v1/reviews/final_artifact_freeze.json)
[E81完整报告](../stage22_joint_view_partition_v1/report.md) · [协议](../stage22_joint_view_partition_v1/protocol.md) · [成本](../stage22_joint_view_partition_v1/results/cost.json) · [封存](../stage22_joint_view_partition_v1/reviews/final_artifact_freeze.json)

E81局部信号单独保留：Yandex相对P+58命中/失败−11，相对E80+70/−8，但相对compact−62/+2，对P两半-30/+88。联合分组保留compact正收益Web601/820、Y396/545，高于E80的356/820、183/545；同时减少了旧损失修复，净结果仍未过门。联合目标J提升不等于检索效用。Web仍对P−78/+8。

E81独立目标检查首版因重建布局/归约路径未匹配而在F哈希处失败，原件保留；v2在原严格digest和独立数值容差下通过，无模型/ANN重跑。首次检查耗时未恢复；v2和分析耗时见阶段验收，绘图/文档耗时未单独计量。[检查器更正](../stage22_joint_view_partition_v1/reviews/objective_checker_correction.json)。
