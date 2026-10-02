# 123 决策一致性与置信排序缓存审查

日期：2026-09-22。独立版本 `entry_method_exploration/20260922_decision_alignment_audit_v1/`。不新增性能实验号。状态 `STOP_CALIBRATION_ONLY_REUSE`；完成用户授权的理论/目标审查及先诊断后条件训练流程，默认与 E119 原件保持。

## 动机与理论

E119 六种评分配置的双集 query-out 净效用都为负。不能继续仅换评分器，也不能简单归因为没有信息。本轮区分：损失是否与决策一致，动作排序是否好于全 H 平均，分数能否判断相对 GT10 的切换收益，L128 目标能否代表实际高召回区间。

对原 Rank objective 构造二动作反例：同一可观测 context，U=+1 概率 .1、U=-.01 概率 .9，期望收益 +.091；逐 query gap 归一化连同 .1 MSE 的最优分数 -0.2131393372，错误回退。原 torch 函数与独立标量公式/导数一致。是一般一致性缺口，不是执行错误或对全部负结果的归因；MSE/GBDT/TabM 不受这一特有反例解释。SPO+ 前作的分布条件不能直接假定成立。

匹配召回的局部时间变化为 ΔT+c−(T'/R')ΔR，须局部平滑且导数为正。E103 90% 区间为 Web R1 L640–800、R100 L1120–1250，Y R1 L96–128、R100 L200–256；局部斜率 .0659/.0847/.0888/.1080。L128 不是统一目标区域，lambda=.1 也不是已证实的主要错误。

## 输入、冻结与实际执行

原 E119 两集各4096条历史开发 query、四折、真实K1/K100/L128、全H815/821加原动态GT10；六配置全部外折预测及完整效用/召回/搜索时间标签只读。主搜索、原模型、画像、图、真实入口映射均不变。

协议披露先前已见的总体结果和选择偏差。新五等分诊断前冻结统计定义与准入门；先提名旧总体最接近默认的 GBDT，明示事后提名及曝光身份。每折/K最高非默认候选按分数及真实ID确定，分数按源行打破 ties 分五组；最高组816/4096。全部六配置报告，但不得事后换获准候选。

仅当 GBDT 双集最高组平均 U>0、最高组减其余组的95%描述性区间下界>0、至少3/4折差值正且每K召回损失不超.1pp，才做一次原monitor256上的isotonic校准。冻结原模型/候选，不把混合OOF再切分作元训练以免跨折泄漏；不得调阈值或改模型。

## 结果与判断

GBDT所选入口真实效用平均分位 Web69.76%/Y75.12%，高于全H行均值，有有限动作排序信号；不证明 query-entry 交互因果。最高分组等K U×100 为 Web−1.1171（95%区间−2.0566至−.1729）、Y−.9064（−1.6464至−.1768）。两集最高组减其它组区间跨0，Y仅2/4折差值正，各K质量门亦失败。

六配置最高组均值全部为负。Web两个Rank有最高组相对其余组的正差值区间，Y个别中间组有正均值，完整保留但不选新规则。结论是本轮预先限定的校准-only准入不通过；不能外推任意更窄子集/非单调校准/高预算方法都没有收益。

未触发校准训练、base模型重训、新搜索或完整性能阶段。没有新的Recall/QPS改善；E119停止不变，Web soft/Y hard及生产E99保持。下一问题应先落到实际目标预算的信息和结构条件，不自动发起全H新标签或换loss续跑。

## 成本与验证

主分析41.04秒，两次独立实现审计共25.84秒（12.73+13.11），0新NSG/ANN/GT/构图/QPS/训练。98,304个query/K动作、480分箱、原已保存收益、三种同分/回退边界核验通过；补充四处原始wall斜率和400组合成遗憾不等式。76消费输入及冻结分析SHA匹配。仅同会话独立数值实现，不是独立人员审查；没有本轮原生搜索parity或新完整图hash。

bootstrap5000次，按query在折内重采样、两K配对，历史曝光/训练折重叠/多模型报告限制明确。U时间是原搜索-only，不含路由/评分，U×100不能当Recall百分点或QPS。旧seal不更新；根文档修改前快照留新版本。

## 原始证据

- [报告与后续顺序](../entry_method_exploration/20260922_decision_alignment_audit_v1/report.md)、[理论及论文](../entry_method_exploration/20260922_decision_alignment_audit_v1/theory.md)。
- [冻结协议](../entry_method_exploration/20260922_decision_alignment_audit_v1/protocol.md)、[全量结果](../entry_method_exploration/20260922_decision_alignment_audit_v1/analysis/results.json)。
- [分析源码](../entry_method_exploration/20260922_decision_alignment_audit_v1/src/analyze.py)、[独立复核](../entry_method_exploration/20260922_decision_alignment_audit_v1/src/audit.py)、[审计结果](../entry_method_exploration/20260922_decision_alignment_audit_v1/reviews/independent_audit.json)。
- [输入身份](../entry_method_exploration/20260922_decision_alignment_audit_v1/reviews/before.json)、[源前快照](../entry_method_exploration/20260922_decision_alignment_audit_v1/source_before/)、[状态](../entry_method_exploration/20260922_decision_alignment_audit_v1/state.json)。
