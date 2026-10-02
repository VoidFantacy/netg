# ACSG 当前结果摘要

2026-09-12，最近完成E47，`COMPLETE_FULL_FEEDBACK_PROFILE_RL_LOCAL_RL_SIGNAL_AGGREGATE_GATE_STOP`。[报告](entry_method_exploration/20260912_full_feedback_profile_rl_v1/report.md)、[历史36](experiment_history/36_full_feedback_profile_rl.md)、[审计](entry_method_exploration/20260912_full_feedback_profile_rl_v1/reviews/training_verification.json)。用户20:00持续研究目标继续，默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。

| 数据集 | 方法/seed | 选中步 | train512 ΔR pp | full train ΔR pp | monitor ΔR pp | 末点monitor ΔR pp | 原E43选中monitor ΔR pp |
|---|---|---:|---:|---:|---:|---:|---:|
| WebVid | RL/21 | 100 | +0.0195 | +0.0513 | +0.0781 | +0.0781 | +0.0098 |
| WebVid | RL/22 | 80 | +0.1953 | +0.0391 | +0.0098 | -0.1660 | -0.0098 |
| WebVid | ES/21 | 40 | +0.0781 | +0.0220 | +0.0000 | -0.0195 | +0.0781 |
| WebVid | ES/22 | 20 | +0.0000 | +0.0098 | +0.0000 | -0.0781 | +0.0000 |
| Yandex | RL/21 | 100 | -0.0195 | +0.0073 | +0.0000 | +0.0000 | +0.0000 |
| Yandex | RL/22 | 200 | +0.0000 | +0.0171 | +0.0781 | +0.0781 | +0.0000 |
| Yandex | ES/21 | 120 | +0.0000 | +0.0098 | +0.0000 | +0.0000 | +0.0000 |
| Yandex | ES/22 | 200 | +0.0000 | +0.0073 | +0.0586 | +0.0586 | -0.0195 |

完整反馈显著增加了可见质量响应，但仍未形成所有数据集/估计器都稳定增益的结果。WebVid每200步有133–145步见候选命中变化，Yandex74–85步；原E43为13–18/3–7步。两轮训练的状态会分岔，这一频次对比不再是固定状态采样消融；E44已有固定状态的漏反馈证据。

实际确定均值响应仍稀疏：WebVid每200次更新仅12–20次改变全池命中，Yandex仅1–3次。八模型末点完整训练池均为净正值，但WebVid RL第二seed后期monitor退到−0.1660pp，ES两seed选中monitor均0，说明训练机会与新query收益没有稳定转化。不能把非零reward或看见更多候选收益直接当作泛化成功。

RL的局部正值必须单独保留：WebVid选中两seed monitor +0.0781/+0.0098pp，Yandex为0/+0.0781pp；RL这个arm在两集均有正候选。原预锁门要求每个数据集的RL和ES都至少一个seed正增量，因WebVid ES失败而未过，按协议停止本完整反馈版本的预算扩展。这个统一门的失败不能抹掉RL双集信号，也不能反过来改写为统一门通过。Yandex ES第二seed +0.0586pp同样保留；尚无独立开发或Recall–QPS证据。

实际228832 NSG、59107328 HNSW、14424普通构图、1600更新，累计训练进程1260.983s。精确复用保持完整反馈，0新GT/开发/QPS；完整重放586208集合评分、12800候选W、88 checkpoint、16导出与1024parity通过，E37–E46保护。当前最近完整Recall–QPS仍E37。

接着执行E48评分/邻接2×2，直接回答原有动作的跨query收益损伤来自共享评分方向还是普通HNSW重建的干扰：固定E44全部20状态/八方向，补齐(Wa,Gc)/(Wc,Ga)，真实路由全池并精确补测变化query，不增加训练epoch或幅度。源码和协议已准备，当前尚未编译或查询。

之后另立“冻结RL候选能否保留双集增量”的独立对照问题，考虑用既有隔离cal/audit和原单线程静态评测器验证完整Recall–QPS。它不复活E47的统一训练门、不重训或按新结果改模型；所有候选/选择规则/预算在查询前另冻，当前无新cal/audit。用户要求大胆假设、小心证明，因此继续验证已有具体信号，不把自设统一门变成放弃所有局部结果的理由。 详细接续见[s-target](s-target.md)。
