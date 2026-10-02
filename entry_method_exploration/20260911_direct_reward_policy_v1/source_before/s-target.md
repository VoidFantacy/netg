# ACSG 下一阶段方向与实验接续

2026-09-11。E31训练有效性检查已完成，状态`TRAINING_EFFECTIVENESS_COMPLETE_OPTIMIZATION_IMPROVED_CACHE_GATE_FAILED`。本轮授权的有界验证结束：4次训练合计302.73s，新标签/NSG/QPS均0。[结果报告](entry_method_exploration/20260911_training_effectiveness_v1/report.md)、[缓存门](entry_method_exploration/20260911_training_effectiveness_v1/results/cache_gate.json)、[历史20](experiment_history/20_training_effectiveness.md)。

## 当前采用和研究收口

默认仍为WebVid GT10 soft、Yandex GT10 hard，以[E30同批曲线](entry_method_exploration/20260911_training_effectiveness_v1/../20260911_equivalent_teacher_sets_v1/report.md)为依据。原GT10/E28 MLP局部结果保留。

E31确认原80步有优化余地，额外优化使WebVid缓存Recall相对原multi再增0.0910pp，Yandex没有有效提升。单/多教师都未通过双集缓存门，未继续真实开发或validation。当前固定教师、共享linear、λ100的优化支线收口；没有因为剩余训练预算而追加日程、正则网格或容量。

## 下一阶段优先问题：GT10独立复现与公平比较

优先确认原方法的可复现价值。先复用现有协议和原始曲线，明确当前默认在不同Recall区间、相同线程、相同图/metric/入口数下的证据；将数值领先、局部前沿和稳定提升分开。新的实验要回答一个明确的复现问题，不能将反复使用的历史validation重新称为盲测。

下一份执行协议至少明确：比较的原方法和基线身份；固定图上不同query或独立seed中的哪一项变化；fit/选择/评估拆分；完整单线程端到端wall与Recall的记录；查询/构建/GT依赖和预算；预设共同Recall目标、重复轮次与停止条件。优先采用现有可部署画像和原kernel，训练新画像不是复现默认的先决条件。

这只是接续优先级，下一阶段的复现、基线构建、标签生成、训练或held-out测试均尚未执行。需在下一任务中确定具体实验范围与资源，不从E31或E30剩余预算自行扩大。

## 重新讨论画像学习的证据门槛

若将来提出新目标或新结构，先说明它与E28–E31已完成方案的实质区别、机制预期和最小对照。保留低成本缓存检查的原则；仅当现有教师/候选域能够覆盖所提问题时才复用标签，未知组合不可当零收益负例。任何同L Recall、缓存效用、NDC或训练目标下降都不替代同机独立端到端Recall–QPS前沿证据。

E31的负结果只覆盖当前固定教师/共享linear/λ100/seed和有界日程；没有全局最优证明。WebVid局部缓存改善值得完整保留，但不足以绕过双集推进条件或自动替换部署默认。

## 接续阅读与启动要求

完整读AGENTS→summary→spec→本文件→s-experiment，然后由[历史20](experiment_history/20_training_effectiveness.md)和[历史19](experiment_history/19_equivalent_teacher_sets.md)进入原protocol/state/gate/模型与结果。原E24–E31源码、图、H、GT、labels、模型、日志和报告保留，旧runner拒绝覆盖。

可用接续指令：先核对E31为何停止及WebVid局部正信号，再沿E30完整曲线定位当前默认的适用Recall区间；据现有证据设计最小独立复现协议，列出需要新增的query/seed/GT/构建成本和停止条件。此指令本身不启动训练、ANN或held-out。

所有正式性能继续CPU15/实际进程与OMP线程1，OMP/BLAS/MKL1，一次一个方法，不与训练或重分析并发；计数、GT评分、建图、I/O和hash在plain wall之外。
