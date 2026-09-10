# ACSG 当前状态与接续边界

2026-09-10，用户指定的A+B五点探索已完成，随后完成梯度/低秩/MLP论文与源码复核。最新实际结论见[summary.md](summary.md)，完整过程见[E22复盘](experiment_history/11_ab_fixed_slot_exploration.md)，实现合同见[spec.md](spec.md)。

## 当前判断

`EXPLORATORY_NO_OVERALL_FAST_GAIN`：相对Fast，小L质量退化、高L仅有少量Recall正值，十个点的实测QPS均较低；相对NSG质量改善但多数点更慢。当前结果不支持把该冻结候选替换Fast，也不足以进入原大规模正式矩阵。全部正值和负值都保留，不外推一般入口学习不可能。

## 已完成的用户范围

[最终协议](entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/protocol.md)：两个数据集各validation2000，seed20260828，NSG/Fast30K direct3/A+B三方法；L64/128/256/400/800；全部单线程，各一次完整预热和一次端到端计时。Recall@10、QPS、失败数量/率及相对两基线的挽救/新增失败完整输出。

同一数据集五L固定同一份W/mapping。训练标签曾在L128下产生，模型本身只输入query；五L逐query入口完全一致。当前比较没有为每个L重训练或换模型。

## 接下来如何继续

实验执行已收口，不自动恢复旧14方法×3seed×双评估集矩阵、NSG补测队列或追加计时。用户随后要求复核PyTorch、低秩梯度下降和相关论文；[研究报告](entry_method_exploration/20260910_optimizer_research_v1/report.md)已完成，状态`RESEARCH_COMPLETE_METHOD_UNSELECTED_UNRUN`。没有新增标签、训练、ANN构建或评测。

研究建议：保留离线学习/在线轻量路线，先固定真实入口身份，使新方法与Fast都选择三个互异入口；用原kernel实测三入口条件收益构造排序监督，以Fast锚定完整W建立可诊断参考，rank8在同目标下作控制。固定pair时完整W的排序目标可保持凸性，但它仍是实际top3收益的代理，完整W也有过拟合风险。共享hub端MLP是参数共享备选，可离线导出相同形状W；自由B映射不再被视为必需组件。具体算法、组合标签预算和优化配置尚未选定，待用户选择后才另定执行协议。

后续验证需区分目标不匹配、优化/容量、fit到cal泛化、精确排序到HNSW损失和图搜索成本。旧single标签只可帮助提议组合，不能直接当三入口联合标签；不自动枚举全部组合或恢复固定anchor/C8限制。训练及Fast画像遵守同一split隔离；一份模型用于全部五L，最终仍由同机单线程完整Recall–QPS表现判断。

今后的探索比较仍优先单seed、小validation集、少量必要方法与用户指定预算点；只有出现明确正信号且用户决定推进后，再另定正式复核范围。所有方法和基线查询测试始终单线程，OpenMP/BLAS/MKL显式限制1，并检查实际线程。训练/标签生成可以多线程，但不得与查询计时并行或把其wall称作查询QPS。

C继续保持`NO_GO_UNCONDITIONAL_HEADROOM_STOP_C`，不运行C3/C4或A+B×C联动；D和效用树不自动切换。原只读研究、独立R0、完整训练协议、大矩阵/线程/范围修正均保留历史身份。旧源代码、图、标签、模型和所有结果不清理、不覆盖、不远程同步。
