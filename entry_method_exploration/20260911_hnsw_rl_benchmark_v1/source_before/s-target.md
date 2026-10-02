# ACSG 下一阶段方向与实验接续

2026-09-11。E33已完成，状态`HNSW_EDGE_RL_COMPLETE_WEBVID_SIGNAL_NO_DUAL_GAIN`。[报告](entry_method_exploration/20260911_hnsw_edge_rl_v1/report.md)、[历史22](experiment_history/22_hnsw_edge_rl.md)、[开发门](entry_method_exploration/20260911_hnsw_edge_rl_v1/results/development_gate.json)。用户授权的本次HNSW图训练小实验已收口，无排队训练/ANN/validation任务。

## 当前判断与保留信号

本轮是实际REINFORCE图边训练：当前Micro-HNSW底层删边，原画像/上层/真实ID/NSG固定。WebVid主图相对原图cal/audit +.3418/+.1270pp，路由成本降低但总NDC只约−.98%；audit未超过同出度随机图。Yandex两seed四个开发点均负，双集门停止。不能把此轮结论扩大成全部图结构/坐标RL无效。

默认继续WebVid GT10-soft-t1/Yandex GT10-hard的原HNSW。GT10/E28已有局部前沿、E32同C8目标收益和E33单集删边信号分别保留；三个问题的作用位置不同，不能混称同一方法或互相代替性能证据。

## 优先一：确定学习相对简单删边的增量

E33已提供逐节点同出度随机控制、完整两个seed、训练轨迹和paired区间。先完整核对[控制表](entry_method_exploration/20260911_hnsw_edge_rl_v1/results/csv/rl_vs_random.csv)与[策略诊断](entry_method_exploration/20260911_hnsw_edge_rl_v1/results/csv/policy_diagnostics.csv)：WebVid audit RL−随机−.0684pp，Yandex主图audit−.3125pp；全部RL−随机区间覆盖0。多数边有数百至上千次暴露，约41%–60%保留概率仍在.45–.55，不能直接把失败解释成“没训练”或用更多epoch保证成功。

若另立复现，应锁定主图/提取阈值/奖励/样本，使用未参与选择的开发数据和多个预定匹配随机图；至少比较原图、冻结学习图、同逐节点出度随机及简单几何删边。分别检查质量、路由/NSG/总成本和跨seed稳定性。样本GT与新query来源须先核验；历史cal/audit/validation不能重新称盲测。先要求学习稳定胜简单控制，再决定是否值得完整同机单线程前沿；无增量则停止此删边表示。

## 优先二：若研究“导航坐标偏移”，建立真正闭环

本轮没有改坐标、加边或重连。坐标路线应明确仅修改入口的导航画像，原base向量、真实IP检索目标、H/映射和NSG不变；每个训练动作后重建/修复HNSW，运行真实遍历→三个入口→原NSG，再反馈收益。不能只训练一个不经过实际HNSW的代理目标，却称为图偏移RL。

最小设计宜把动作限制在低维、带半径约束的共享位移或少量局部边交换，记录构图耗时和真实反馈调用。对照应包含原图、同预算随机扰动/无学习结构搜索、E33删边，以及有相同表示的监督训练；明确与E28–E32监督画像/候选重排的实质差异。不可直接向离散HNSW构图反传；若采用策略梯度/黑盒估计，须核验估计与真实图变化，并单列方差与训练成本。

这只是尚未实施的候选方向，不能据E33的接口通过认定方法可用。下一份协议需在新实验前锁定唯一主变量、奖励单位、信赖域、候选动作、query split、标签兼容范围、优化与构建预算、模型选点和退出规则。已有C8标签不覆盖一般新图返回的全部三元组；新组合必须实际搜索，不当作零效用。

## 优先三：收益通过后的单线程性能验证

路由只占当前总计算的一小部分：E33主图路由约−18%至−19%，NSG约+.19%至+.38%，总NDC不足−1%。因此任何新方法须明确改善最终入口质量还是减少路由工作；正式结论依赖完整端到端wall，不能只以删边数、路由NDC或同L Recall认定性能GO。

质量/成本和控制门通过后，才能按新协议执行相同CPU15、进程/OMP/BLAS/MKL1、一次一个方法、无训练并发的Recall–QPS曲线。预锁L、完整warmup/轮换重复、共同Recall区间、输入/图/模型身份、调用/时间/内存/磁盘cap；记录GT-inclusive离线成本的已知与缺项。held-out不属于本轮访问范围。

## 接续要求

完整读AGENTS→summary→spec→本文件→s-experiment，再进入[历史22](experiment_history/22_hnsw_edge_rl.md)及原协议/修正/模型/开发门。有效训练实现是`environment_v2.cpp/native_v2.py/train_v2.py`；第一版只是保留的结构预检停止原件。冻结产物不得覆盖重跑。

接续指令示例：先只读核对E33两seed完整训练/monitor/开发与随机控制，明确要验证学习增量、坐标变化还是结构交换，提出一个含对照、数据/GT依赖、构图和反馈成本、选点与停止规则的最小新协议。当前方向均未自动追加训练/ANN/validation；有新用户授权后在独立版本执行，不凭旧NO_GO额外制造确认流程。
