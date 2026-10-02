# ACSG 下一阶段方向与实验接续

2026-09-11。E29教师与目标对齐已完成并收口，状态`TEACHER_OBJECTIVE_ALIGNMENT_COMPLETE_NO_STABLE_DUAL_GAIN`。本轮未建立优于原GT10的稳定双数据Recall–QPS优势。 当前建议继续保留WebVid已冻结GT10 soft、Yandex GT10 hard；本轮四格均没有足够证据支持替换。 原用户授权的训练、真实Recall–QPS曲线、分析和验收均完成；以下建议未执行，不自动借用本轮剩余额度。

## 1. 首先评估多个等效好集合的监督

E29将“换教师”与“换损失”分开，margin对教师入口的拟合与真实检索效果不总同步。下一步可先只读当前C8完整标签，研究最高命中层级内多个集合的等效程度和成本分布，避免强迫学唯一入口身份。候选外效用未知，不能将其默认为负例或用C8内评价外推全H。完整fit真实检索、因子差值与梯度证据见[报告](entry_method_exploration/20260911_teacher_objective_alignment_v1/report.md)。

若启动新的训练，应先锁定集合等效定义、成本取舍和唯一教师控制；保持同H/原NSG/实际三入口，通过新独立协议报告fit与开发真实命中，不凭目标下降扩网络。该方向当前只有建议，没有实施新的多集合损失。

## 2. 漂移匹配控制优先于扩大模型

同λ没有匹配CE/margin的实际变换幅度。可设计仅由fit导出向量确定缩放系数的CE残差对照，以匹配margin漂移，再做独立真实查询比较；这能检查收益是否主要来自更保守的改动。几何投影结果已经单列，但未执行该反事实QPS控制。新画像和新查询必须有独立预算，不能从旧输出模拟速度。

## 3. 优化精度与迁移边界

当前为固定80轮、一个种子、共享linear，无收敛证书。若继续同目标，应先明确优化充分性的可检验标准和固定停止规则，再研究开发段是否跟随；不要把更多epoch或更大MLP自动等同于方法改进。若完整fit真实效用没有进展，不扩大模型/held-out；若仅fit有收益，先定位可迁移监督。

## 4. 资产、数据与重新启动约束

- E29实际NSG调用2,085,120，训练8，新标注0，repair0，预算收口；不转用修复余量。
- E24–E29原图/H/源码/标签/模型/日志与结果保留。架构/API见[spec](spec.md)，历史见[s-experiment](s-experiment.md)。
- fit/cal/audit/validation均有历史使用；held-out未读取/hash。本轮结果不是新盲测或论文充分性结论。
- 只有新的独立同机端到端Recall–QPS支持性能判断，教师空间、精确入口排名、梯度和NDC都不是其替代品。
- 接续先读AGENTS、summary、spec、本文件、历史18和原协议/结果，再建立独立版本。旧runner拒绝覆盖，不能换名重启已收口网格。

本轮完整产物：[报告](entry_method_exploration/20260911_teacher_objective_alignment_v1/report.md)、[因素曲线](entry_method_exploration/20260911_teacher_objective_alignment_v1/figures/factor_effects.svg)、[Excel](entry_method_exploration/20260911_teacher_objective_alignment_v1/chart_data.xlsx)、[验收](entry_method_exploration/20260911_teacher_objective_alignment_v1/reviews/final_audit.json)。
