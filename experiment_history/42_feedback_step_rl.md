# 42. E53 RL反馈步长接受

2026-09-12，`COMPLETE_FEEDBACK_STEP_RL_LOCAL_SIGNAL`；局部门`PASS_DUAL_LOCAL_FEEDBACK_STEP_RL_SIGNAL`。

| 数据集 | seed | 选中步 | full train ΔR pp | monitor ΔR pp | 末点monitor ΔR pp | 接受次数/200 |
|---|---:|---:|---:|---:|---:|---:|
| WebVid | 21 | 40 | +0.1514 | +0.1270 | +0.0391 | 95 |
| WebVid | 22 | 80 | +0.3052 | +0.1562 | -0.0781 | 104 |
| Yandex | 21 | 200 | +0.1489 | +0.0195 | +0.0195 | 74 |
| Yandex | 22 | 140 | +0.1294 | +0.0293 | -0.0195 | 79 |

RL保留原八Gaussian候选的LOO梯度与Adam方向，候选仅估计方向；提交仅在同方向r/4、r/2、r三个真实测量点及不动之间按原J择优。r由Gaussian扰动中位范数给出，不使用GT确定半径；步长接受使用完整train4096反馈。m/v和局部计数每步推进，实际画像及缓存只有接受后改变。线上导出静态普通HNSW，仍一次路由取得三个真实入口后运行原NSG。

这检验E51指出的更新尺度问题，也保留E52直接提交候选的贪心对照身份。完整训练与监控曲线分开报告，监控参与选点；双集至少一个可行正候选的局部门并不证明四seed稳定性、独立泛化或Recall–QPS前沿收益。连续算法状态逐步分岔，不能把整个算法对比当固定状态单因子因果证据。

## 成本与独立验收

实际125577 NSG=62976固定+50536 Gaussian变化+12065确定点变化；36107264 HNSW、9612构图、800 RL梯度/接受决策、352实际接受。完整训练进程816.273s，实际单线程CPU15串行。0新cal/audit/validation/held-out查询、0新GT、0QPS点。

独立6400 Gaussian候选/2400确定点、800四分量梯度/Adam/步长选择/不动及拓扑缓存链、44完整checkpoint、8静态导出、512三路parity通过；304265集合评分，审计30.297s。原冻结源码的reserved_builds字段沿用1803，低记600/run；协议与实际每run2403不变，正确四run9612低于15000硬限，单独重记并保留原日志，详见[记账修正](../entry_method_exploration/20260912_feedback_step_rl_v1/reviews/build_reservation_accounting_note.md)。

## 接续与边界

下一阶段E54对完整学成模型做评分/邻接四格：C(P,G0)、A(W,G)、S(W,G0)、T(P,G)。固定E52/E53各双seed全部模型，train与monitor分开，仅静态干预不再训练。它补足E48仅单行小动作的机制范围；源码/协议准备中，当前尚未查询。最终模型由既有cal预选，在历史validation2000同机CPU15单线程与NSG、Fast30K、FastGT10-hard比较五L五轮QPS/Recall/零GT10命中失败率；最终结果不回流选模型。用户22:00收口，21:15前进入最终比较窗口，21:40停止新查询。

默认仍为WebVid GT10-soft-t1 / Yandex GT10-hard。最新完整曲线是E49，最终用户要求的完整基线比较仍未执行。

[协议](../entry_method_exploration/20260912_feedback_step_rl_v1/protocol.md)、[四模型](../entry_method_exploration/20260912_feedback_step_rl_v1/results/models.csv)、[44 checkpoint](../entry_method_exploration/20260912_feedback_step_rl_v1/results/checkpoints.csv)、[800步骤](../entry_method_exploration/20260912_feedback_step_rl_v1/results/steps.csv)、[成本](../entry_method_exploration/20260912_feedback_step_rl_v1/results/cost.json)、[局部门](../entry_method_exploration/20260912_feedback_step_rl_v1/results/gate.json)、[独立验收](../entry_method_exploration/20260912_feedback_step_rl_v1/reviews/training_verification.json)、[学习曲线](../entry_method_exploration/20260912_feedback_step_rl_v1/figures/feedback_step_learning.svg)。

最终冻结v2修正收尾日志写入时序，见[E53修正](../entry_method_exploration/20260912_feedback_step_rl_v1/reviews/final_freeze_repair.json)。
