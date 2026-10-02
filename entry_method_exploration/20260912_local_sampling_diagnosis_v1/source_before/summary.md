# ACSG 当前结果摘要

2026-09-12，最近完成E43局部画像RL/ES，`COMPLETE_LOCAL_PROFILE_RL_STOP_MONITOR_GATE`，门`STOP_THIS_PARAMETERIZATION_BUDGET_EXPANSION`。[报告](entry_method_exploration/20260912_local_profile_rl_v1/report.md)、[历史32](experiment_history/32_local_profile_rl.md)、[验收](entry_method_exploration/20260912_local_profile_rl_v1/reviews/final_audit.json)。用户20:00持续研究目标尚在推进，阶段完成不等于总目标结束。默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。

## 当前结果

局部画像训练完整完成，但未形成双数据集稳定的质量增量。WebVid选中RL两seed monitor为+0.0098/−0.0098pp，ES为+0.0781/0pp；Yandex RL均0，ES为0/−0.0195pp。WebVid ES的局部正值保留，不能写成RL额外优势。Yandex未过预锁monitor门，因此本版本停止扩展预算，不进入新开发或QPS。

| 数据集 | 方法/seed | 选中步 | train ΔR pp | monitor ΔR pp | 末点monitor ΔR pp | monitor U |
|---|---|---:|---:|---:|---:|---:|
| WebVid | RL/21 | 140 | +0.0000 | +0.0098 | +0.0098 | +0.000812 |
| WebVid | RL/22 | 140 | +0.0000 | -0.0098 | -0.0195 | -0.001086 |
| WebVid | ES/21 | 180 | +0.0781 | +0.0781 | +0.0781 | +0.007866 |
| WebVid | ES/22 | 20 | +0.0000 | +0.0000 | -0.1465 | -0.000011 |
| Yandex | RL/21 | 200 | +0.0000 | +0.0000 | +0.0000 | +0.000047 |
| Yandex | RL/22 | 80 | +0.0000 | +0.0000 | +0.0000 | +0.000017 |
| Yandex | ES/21 | 60 | +0.0000 | +0.0000 | +0.0000 | +0.000013 |
| Yandex | ES/22 | 200 | -0.0195 | -0.0195 | -0.0195 | -0.001923 |


反馈仍然稀疏：WebVid每200步只有13–18步出现任一候选命中变化，Yandex仅3–7步；每次更新覆盖168–173个不同hub，每个活跃hub更新中位数为1。平均确定均值画像位移约0.0035–0.0037，而采样候选约0.060–0.064。这同时提示查询抽样、每hub学习暴露与采样/确定差异，尚不能单独定因。单行责任已可追踪，但绝大多数更新并未观察到命中反馈；不能仅凭非零总reward声称学到了检索收益。

| 数据集 | 方法/seed | 有命中变化的步/200 | 有命中变化候选/1600 | 更新hub数 | 每活跃hub更新中位数/最大 |
|---|---|---:|---:|---:|---:|
| WebVid | RL/21 | 13 | 40 | 169 | 1.0/6 |
| WebVid | RL/22 | 18 | 46 | 168 | 1.0/3 |
| WebVid | ES/21 | 14 | 39 | 169 | 1.0/6 |
| WebVid | ES/22 | 15 | 51 | 168 | 1.0/3 |
| Yandex | RL/21 | 3 | 11 | 171 | 1.0/3 |
| Yandex | RL/22 | 4 | 9 | 173 | 1.0/4 |
| Yandex | ES/21 | 5 | 15 | 171 | 1.0/3 |
| Yandex | ES/22 | 7 | 13 | 173 | 1.0/4 |


所有值来自历史train/monitor，checkpoint由monitor选择；局部正值不构成泛化、独立性能或RL额外价值。具体G/L/零命中/NDC见[全质量](entry_method_exploration/20260912_local_profile_rl_v1/results/quality.csv)。

## 执行与边界

实际1,992,256次NSG（预留1,993,440/硬限2,200,000）、1,991,104次HNSW、14,510次普通构图，1600次更新。两个训练进程累计1691.212s，含加载/构图/反馈/写盘/验收；预检另计。峰值RSS约5.459/9.956GiB。CPU15、实际进程/OMP/BLAS/MKL1线程、方法及数据集串行。不是QPS。

双集预检恢复10240原基线输出，零参数/单行构造、共同baseline抵消、梯度/Adam和plain/原kernel通过。训练独立集合评分1,978,368个返回，核验12,800候选W hash、1600奖励/梯度/四分量/Adam更新、88完整checkpoint、16选中/末点模型及1024query三路parity。候选行用独立逐坐标公式核验，完整W由记录行字节重放，未调用ANN重训。原E37–E42/实际native/NSG依赖与query前冻结保持，根文档前件独立保存。无新GT和原validation/held-out读取/hash；保护旧隔离开发产物的字节读取不混为新开发。

共同当前J在LOO/ES梯度中抵消；本阶段实质改变为一次只改一行及H×16独立参数，不能将跨E37差异全部归因奖励。E42目标必要/充分与背景交互、E41 WebVid42091单改+4无损局部信号保留。当前无新cal/audit/validation/held-out/QPS；最近完整性能评测仍为E37。

下一明确目标为固定E43原状态/八方向的完整train4096条件参照，比较uniform128与GT无关、正确加权的分层128采样方差及正负反馈覆盖。先做该诊断，不重训或调σ/epoch；双集条件方差明确改善才考虑唯一采样修订。该后继控制尚未执行，当前20:00总目标继续。 详细接续见[s-target](s-target.md)。
