# ACSG 当前结果摘要

2026-09-12。最近完成E40已有画像动作收益损伤归因，状态`COMPLETE_PAYOFF_ATTRIBUTION_LOCAL_OPPORTUNITY_WITH_CANCELLATION`。[报告](entry_method_exploration/20260912_profile_payoff_attribution_v1/report.md)、[历史29](experiment_history/29_profile_payoff_attribution.md)、[验收](entry_method_exploration/20260912_profile_payoff_attribution_v1/reviews/final_audit.json)。E39仍是最近新搜索，E37仍是最近训练/完整性能评测；默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。

## 当前判断

现有局部动作有非零但稀疏的改进空间；收益分散与正负抵消同时存在。32个全局扰动均帮助一部分query、损伤另一部分，单一已测配置仅保留有限逐query上界的0%–23%。这支持停止给同一全局扰动训练器加预算，先定位联动损伤；它尚未证明共享参数表示在数学上无法兼顾这些query。

| 固定点 | 有可获益query / 1024 | 九配置逐query上界 ΔR pp | 单一配置最佳 ΔR pp | 最佳配置增益−损伤（命中数） |
|---|---:|---:|---:|---:|
| WebVid / 初始化 | 35 | +0.9277 | +0.1855 | 41−22=19 |
| WebVid / 已选点 | 26 | +0.4102 | +0.0000 | 0−0=0 |
| Yandex / 初始化 | 15 | +0.6445 | +0.1465 | 36−21=15 |
| Yandex / 已选点 | 17 | +0.6641 | +0.1465 | 42−27=15 |


数值均相对各固定点确定中心。上界和最佳只针对原八扰动+中心，使用历史训练query的GT，不是部署选择或新泛化结果。可获益query仅15–35/1024；九配置只能恢复中心剩余漏检的1.70%–6.77%，局部机会有限但非零。

三个有正净收益的最佳扰动分别增加41/36/42个命中，同时损失22/21/27个；WebVid已选点八扰动全负，最佳为保持中心，最好的扰动也仅增加9却损失20。有限上界到静态最佳的差距同时包括未覆盖收益和实际损伤，不能全归为表示冲突。[完整增益损伤图](entry_method_exploration/20260912_profile_payoff_attribution_v1/figures/action_gain_loss.svg)。

同一全局动作对不同query产生正负有直接证据；但同动作/同入口交换的正负重复实例为0，5953单交换事件分成5879组，重复支持很少。同hub新增/移除的混合关联存在，但其它入口与画像也变化；相似query证据也稀疏，尚未识别共享参数化的不可兼容性。约92.76%的入口变化未改变命中，不从最终输出推断HNSW访问路径。

## 实际执行与边界

0新NSG/HNSW/构图/optimizer/GT；独立复核36864既有返回、6508入口事件、13016离线得分边界、23369分组和1161query pair。主分析实际单线程约0.746s、RSS约135.5MiB，不含编写/保护hash/绘图或阅读，不能当QPS。E37/E38/E39整目录SHA保持，根文档前件保存，无新的原validation/held-out读取/hash。

E39四点512-query方向稳定门仍全部失败；E37主RL开发门仍停止，cal/audit变化为WebVid−0.1172/−0.0391pp、Yandex−0.0195/+0.0391pp，L128 QPS约+0.069%/+0.078%。E24 GT10、E36局部正信号保留，没有新默认替换。

下一步设计为目标入口画像与其余画像的2×2隔离，以原画像行拼出静态反事实，检验损伤是否来自其它画像联动；不是再训练自由W或增加epoch。该控制尚未执行，预计8576次NSG、建议硬限10000、0optimizer，详见[s-target](s-target.md)。无排队任务。
