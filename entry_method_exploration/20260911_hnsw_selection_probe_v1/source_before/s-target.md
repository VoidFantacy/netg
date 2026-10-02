# ACSG 下一阶段方向与实验接续

2026-09-11。E34冻结RL图性能补测已完成，状态`COMPLETE_FROZEN_RL_BENCHMARK`。[报告](entry_method_exploration/20260911_hnsw_rl_benchmark_v1/report.md)、[历史23](experiment_history/23_hnsw_rl_benchmark.md)。用户新增QPS/Recall/失败率请求已完成；45点225轮wall，无新训练/改选模型，无排队任务。E33开发门停止原件保留。

## 当前判断与保留信号

前一轮E33完成实际REINFORCE图边训练：当前Micro-HNSW底层删边，原画像/上层/真实ID/NSG固定。WebVid主图相对原图cal/audit +.3418/+.1270pp，路由成本降低但总NDC只约−.98%；audit未超过同出度随机图。Yandex两seed四个开发点均负，双集门停止。不能把E33结论扩大成全部图结构/坐标RL无效。

默认继续WebVid GT10-soft-t1/Yandex GT10-hard的原HNSW。GT10/E28已有局部前沿、E32同C8目标收益和E33单集删边信号分别保留；三个问题的作用位置不同，不能混称同一方法或互相代替性能证据。

本轮新增E34实测曲线：WebVid相对其直接起点，五L的Recall变化为-0.220～+0.035pp，QPS变化-0.22%～+0.04%；1/5点Recall上升，2/5点QPS上升。同Recall三个描述性插值位置的QPS变化为-0.91%～-0.29%。 Yandex-IP相对其直接起点，五L的Recall变化为-0.140～+0.010pp，QPS变化-0.04%～+0.25%；1/5点Recall上升，2/5点QPS上升。同Recall三个描述性插值位置的QPS变化为-0.63%～-0.38%。 全部失败率、同L配对及共同Recall区间估计见[数据表](entry_method_exploration/20260911_hnsw_rl_benchmark_v1/results/paired_changes.csv)。后续判断须同时保留E33开发/随机对照与E34独立wall结果，不能再把当前RL图说成完全没有性能测量。

## 优先一：确定学习相对简单删边的增量

E33已提供逐节点同出度随机控制、完整两个seed、训练轨迹和paired区间。先完整核对[控制表](entry_method_exploration/20260911_hnsw_edge_rl_v1/results/csv/rl_vs_random.csv)与[策略诊断](entry_method_exploration/20260911_hnsw_edge_rl_v1/results/csv/policy_diagnostics.csv)：WebVid audit RL−随机−.0684pp，Yandex主图audit−.3125pp；全部RL−随机区间覆盖0。多数边有数百至上千次暴露，约41%–60%保留概率仍在.45–.55，不能直接把失败解释成“没训练”或用更多epoch保证成功。

若另立复现，应锁定主图/提取阈值/奖励/样本，使用未参与选择的开发数据和多个预定匹配随机图；至少比较原图、冻结学习图、同逐节点出度随机及简单几何删边。分别检查质量、路由/NSG/总成本和跨seed稳定性。样本GT与新query来源须先核验；历史cal/audit/validation不能重新称盲测。先要求学习稳定胜简单控制，再决定是否值得完整同机单线程前沿；无增量则停止此删边表示。

## 优先二：若研究“导航坐标偏移”，建立真正闭环

本轮没有改坐标、加边或重连。坐标路线应明确仅修改入口的导航画像，原base向量、真实IP检索目标、H/映射和NSG不变；每个训练动作后重建/修复HNSW，运行真实遍历→三个入口→原NSG，再反馈收益。不能只训练一个不经过实际HNSW的代理目标，却称为图偏移RL。

最小设计宜把动作限制在低维、带半径约束的共享位移或少量局部边交换，记录构图耗时和真实反馈调用。对照应包含原图、同预算随机扰动/无学习结构搜索、E33删边，以及有相同表示的监督训练；明确与E28–E32监督画像/候选重排的实质差异。不可直接向离散HNSW构图反传；若采用策略梯度/黑盒估计，须核验估计与真实图变化，并单列方差与训练成本。

这只是尚未实施的候选方向，不能据E33的接口通过认定方法可用。下一份协议需在新实验前锁定唯一主变量、奖励单位、信赖域、候选动作、query split、标签兼容范围、优化与构建预算、模型选点和退出规则。已有C8标签不覆盖一般新图返回的全部三元组；新组合必须实际搜索，不当作零效用。

## 优先三：已有性能证据与后续复现边界

E34已按用户新增授权完成原图/冻结RL/NSG/Fast/GT10的同机单线程五L曲线与零命中失败率；这次补测不表示E33原开发门通过。先读[全部曲线](entry_method_exploration/20260911_hnsw_rl_benchmark_v1/report.md)，区分相对NSG/Fast、相对GT10-hard，以及相对RL真正起点的增量。保持完整端到端wall，不用路由NDC换算QPS。

如以后需要稳定方法结论，另锁定跨seed/独立查询的复现范围和资源预算；现有历史validation不能重新称盲测，也不能据本次曲线继续选模型或调阈值。新协议应保留学习与简单随机/几何控制、共同Recall区间、计时轮换与全部正负点。当前没有自动授权训练或held-out任务。

## 接续要求

完整读AGENTS→summary→spec→本文件→s-experiment，先进入[历史23](experiment_history/23_hnsw_rl_benchmark.md)及本轮性能原件，再进入[历史22](experiment_history/22_hnsw_edge_rl.md)及原协议/修正/模型/开发门。有效训练实现是`environment_v2.cpp/native_v2.py/train_v2.py`；第一版只是保留的结构预检停止原件。冻结产物不得覆盖重跑。

接续指令示例：先只读核对E33两seed完整训练/monitor/开发与随机控制，明确要验证学习增量、坐标变化还是结构交换，提出一个含对照、数据/GT依赖、构图和反馈成本、选点与停止规则的最小新协议。E34仅完成本次已授权性能补测；当前方向均未自动追加训练/ANN/validation；有新用户授权后在独立版本执行，不凭旧NO_GO额外制造确认流程。
