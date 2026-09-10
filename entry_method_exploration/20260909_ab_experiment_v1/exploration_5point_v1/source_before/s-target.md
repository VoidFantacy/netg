# ACSG 当前推进目标：A+B 完整实验

2026-09-09 用户已授权“完整推进实验，最后给出相较 Fast 的 QPS、Recall、查询失败率改善”。之前只读研究已交付，本次按[推荐主方案](entry_method_exploration/20260909_ab_readonly_research_v1/report.md)进入独立实现与测量。当前实验总结见[summary.md](summary.md)，实现事实见[spec.md](spec.md)，旧实验索引见[s-experiment.md](s-experiment.md)。此前理论版目标完整保存在[执行前快照](entry_method_exploration/20260909_ab_experiment_v1/source_before/s-target.md)。

## 当前优先级

用户最新纠正：当前是探索阶段，原14类方法×双L×三构建×双数据集×validation/held-out及重复分项计时过重，已停止其控制器和NSG后续队列。下方原完整范围保留历史身份，当前不自动执行；先解释已有测试矩阵，再缩为最小NSG/Fast/A+B单线程三指标比较。完整标注和12个模型复用，不重新训练。

唯一主线是rank8低秩固定槽位表示 `W=P0+VZ` 与 `pi(slot)→真实hub` 联合优化，在线离线折叠成原维度的一次Micro-HNSW路由和ID查表。自由Z与旧共享affine的 `Z=UᵀP0` 不同；没有引入bias或学习向量归一化。方法/系统贡献允许来自已有组件的有机组合，不要求正交互项或从零发明组件。所有贡献判断仍须实测。

C维持已停止 `NO_GO_UNCONDITIONAL_HEADROOM_STOP_C`，不运行C3/C4；D离线效率支线后置；v4效用树保留为研究备用，不在本协议失败时自动切换。E20 oracle只提供诊断动机，不预测本方法收益。

## 冻结范围和阶段

唯一执行依据：[protocol.md](entry_method_exploration/20260909_ab_experiment_v1/protocol.md)、[config.locked.json](entry_method_exploration/20260909_ab_experiment_v1/config.locked.json)。WebVid/Yandex，原raw-IP/冻结NSG，K10、L64/128，三独立QGT构建种子20260828/29/30。20K fit，各1024 cal/audit；cal/audit来自历史开发池，只对本次拟合隔离。冻结后分别评价完整validation10K和held-out10K。

1. 准备/正确性：核验base/graph/query/GT/hubs的manifest/hash，重建paired Fast20K；合成与双真实图plain/count/repeat、返回IDs/距离/命中评分parity通过才完整标注。该项、全标签核验及12个模型拟合均已完成；当前执行第5项的单线程评测。
2. 全H真实标签：为三种子H的并集统一计算query×真实hub×L标签，分种子取列；不扩大模型候选集。记录全部hit ties及graph NDC，薄二进制落盘，资源下限保护。
3. 训练：原exact Fast、仅W、仅mapping、联合W+mapping及一次分阶段对照；离散全H映射更新与连续软遗憾提案交替，hard fit总命中验收。校准集选择预限定checkpoint；冻结后audit不反馈优化。
4. 部署：W折叠，唯一slot label建Micro-HNSW、另表映射真实ID，验证重复动作仍保留全部槽位。direct Fast1/Fast3都重新测；保留原backend恢复Fast。
5. 完整比较：冻结候选后跑validation/held-out，所有方法统一单线程，三构建×三轮换序plain full-batch timing，count与计时独立；相对paired Fast20K、历史Fast30K及NSG固定入口报告QPS/Recall/严格R@10<0.1失败率和失败数量，以及rescued/newly_failed。2026-09-09用户纠正线程口径后停止原16线程评测，保留其历史输出；复用冻结标签/模型，正式测试全部重新以1线程执行。用户随后明确加入NSG：现有因素评测结束后按[NSG比较修订](entry_method_exploration/20260909_ab_experiment_v1/baseline_comparison_amendment.md)将NSG、两种Fast3及A+B同批重测，不能只与Fast比较后省略NSG。
6. 收口：逐点CSV/JSON/图、配对统计、模型/输入/源码hash、命令与资源账；先新增历史详细卡片和s-experiment索引，再同步summary/spec/本文件。

## 进退条件和证据边界

正确性失败立即修复原因为先，不产生可用性能结论。质量不足仍完成当前冻结候选的有界最终benchmark，向用户给出完整负结果；不会扩大rank/H/ef或更换树以追求通过。相同L、相同ef、相同NDC都不能替代端到端wall。四点Recall至少不低于Fast3、至少一处有显著提升且QPS四点无下降，才可在该有限范围内称Pareto改善；不满足就明确列出收益/损失。旧图中的40%失败率改善不能迁移为本次数字。

一次一个CPU重进程；标签生成/训练最多16线程，正式查询评测及任何其他方法基线比较固定1线程。评测期间不并发其他重任务，显式限制OpenMP/BLAS/MKL并核验结果线程数。磁盘空闲至少10GiB、可用内存至少12GiB，日志与PID可验证。保留未提交源代码、原索引和所有历史artifact；不做远程同步、清理或覆盖。
