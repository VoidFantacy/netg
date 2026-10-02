# ACSG 当前结果摘要

2026-09-12，最近完成E49，`COMPLETE_FROZEN_LOCAL_RL_EVALUATION_NO_DUAL_FRONTIER_GAIN`。[报告](entry_method_exploration/20260912_frozen_local_rl_evaluation_v1/report.md)、[历史38](experiment_history/38_frozen_local_rl_evaluation.md)。

| 数据集 | cal选定模型 | cal ΔR pp | audit ΔR pp [配对95%区间] | audit gain/loss hits | audit改善/损伤query | audit Δtotal NDC % |
|---|---|---:|---:|---:|---:|---:|
| WebVid | rl_20260921 | +0.0391 | +0.0879 [+0.0000,+0.2344] | 9/0 | 3/0 | +0.1013 |
| WebVid | es_20260921 | +0.0684 | +0.0977 [+0.0000,+0.2930] | 10/0 | 1/0 | +0.0475 |
| Yandex | rl_20260922 | +0.0781 | +0.0000 [+0.0000,+0.0000] | 0/0 | 0/0 | -0.0092 |
| Yandex | es_20260922 | +0.0391 | +0.0000 [+0.0000,+0.0000] | 0/0 | 0/0 | -0.0158 |

冻结RL的局部正值只在WebVid部分工作点保留，没有形成双集Recall–QPS改进。WebVid RL在audit L128新增9个命中、无损伤，但L256/400/800各丢4个命中；Yandex选中RL和ES在五L全部没有命中变化。WebVid RL相同Recall的三个描述插值位置为+0.436%、−1.095%、−0.743%，不构成整条曲线提高。五轮QPS小差异方向不一致，不能归为稳定性能优势。

ES的局部结果也保留：WebVid在L64/128/256各新增10命中、无损伤，L400/800相同；L128失败从11降到10。RL L128失败仍11，Yandex所选两模型五L失败与基线完全相同。WebVid的配对Recall区间下界均为0，收益query很少，不能据正均值宣称稳定泛化。E47 monitor没有显示WebVid ES正值，独立开发却有该局部信号，说明不能以某一内部统一门替代所有后续固定模型事实。

预锁可比开发门仍为STOP：两集RL cal +0.0391/+0.0781pp均未到+0.1pp，且Yandex audit为0。保持E47统一训练门原身份，E49也不替换默认。原默认WebVid GT10-soft-t1 / Yandex GT10-hard保留。

实际423680 NSG、80质量/性能点、250独立wall，单线程同机串行；72960返回独立评分和完整parity验收。最近完整Recall–QPS已更新到E49，默认保持。

E48证明WebVid更多邻接响应、Yandex更多评分响应，单因素均不能双集保留收益并减半损伤。接着E50检查已见候选到确定更新的转化，0新查询。用户目标持续至22:00；最终最佳候选对NSG/Fast/FastGT的完整比较尚未执行，详见[s-target](s-target.md)。
