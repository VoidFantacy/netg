# ACSG 当前结果摘要

2026-09-12。最近完成E38既有反馈诊断，状态`COMPLETE_OFFLINE_PROFILE_DIAGNOSIS_NO_NEW_SEARCH`。[报告](entry_method_exploration/20260912_offline_profile_diagnosis_v1/report.md)、[历史27](experiment_history/27_offline_profile_diagnosis.md)、[验收](entry_method_exploration/20260912_offline_profile_diagnosis_v1/reviews/final_audit.json)。最近训练与性能评测仍为[E37](entry_method_exploration/20260912_offline_profile_rl_v1/report.md)，原模型、开发门和默认均未改变。

## 诊断结论

当前最直接的瓶颈是：真实命中反馈集中在少数查询，batch128给出的更新方向不稳定。两臂同样出现这一现象。它支持优先检查查询批次噪声，但尚不能证明增大batch就一定能学出更好的画像，也不能排除当前共享表示下的真实可改进方向本来就很弱。

RL每步能区分八动作命中质量的query中位数仅WebVid 9/128、Yandex 3/128；相同扰动下两半query梯度的余弦中位数为0.0078/0.0041，约半数步为负。命中梯度远大于成本/漂移项，总梯度与命中梯度余弦约0.999，不支持“惩罚压住学习”作为主要解释。

随机动作转确定均值有局部差距，但严格匹配仅覆盖80组、1188条重复query记录，每run只有126/128个独立query身份；区间包含0，部分差值受单条记录影响很大。共享画像表达不足仍未被单独验证。下一步建议固定μ与扰动，仅检验更多查询是否能稳定方向，暂不追加epoch、改表示或启动新训练。

| 主RL诊断项（合并双seed） | WebVid | Yandex-IP |
|---|---:|---:|
| 每步能区分8动作命中的query中位数 | 9/128 | 3/128 |
| 动作-query事件中入口变化 | 27.55% | 20.00% |
| 动作-query事件中命中变化 | 2.69% | 0.94% |
| 两半query梯度余弦中位数 | 0.0078 | 0.0041 |
| 最大单query占逐query命中梯度范数和的中位数 | 30.75% | 57.71% |

这些是实际重复观测的诊断，不能当独立query总体质量。暴露校正后最集中约1%的query仍占RL逐query梯度范数和约37%–40%/66%–68%，不是占最终参数或收益的比例。参数无撞边、B/PB无秩塌缩；表示是否足够尚未因果验证。[诊断图](entry_method_exploration/20260912_offline_profile_diagnosis_v1/figures/gradient_diagnosis.svg)、[完整逐步统计](entry_method_exploration/20260912_offline_profile_diagnosis_v1/results/steps.csv)。

## 实际执行与保留边界

重算E37的1,773,568条已有返回、12800奖励、1600梯度分解与88确定中心；独立集合评分复核32768个动作返回、32步条件方差/半批方向，以及全部1188条相同μ和query匹配。分析实际单线程约8.454s，峰值约168MiB；此时间不含人工阅读/编写/绘图，也不是训练成本或QPS。0新NSG/HNSW/构图/训练/GT，无新validation/held-out原始输入读取/hash。E37全部2721文件SHA保护，文档前件独立保存。

E37主RL的cal/audit Recall变化仍为WebVid−0.1172/−0.0391pp、Yandex−0.0195/+0.0391pp，L128 QPS约+0.069%/+0.078%，双集开发门停止。离线画像→普通HNSW的部署形式已实现，未取得稳定跨数据集前沿优势。E24原GT10及E36 Yandex各自局部正信号保留。

下一步为固定μ/扰动、改变query批量的最小诊断，建议正常36864次NSG、0optimizer更新，尚未执行；若方向可稳定，再设计预算匹配的训练修订，详见[s-target](s-target.md)。无排队任务，默认未换。
