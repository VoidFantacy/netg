# E52 直接提交已测有效候选的连续对照

2026-09-12，`COMPLETE_DIRECT_CANDIDATE_COMMIT_LOCAL_SIGNAL_SEED_INSTABILITY`，局部门`PASS_DUAL_LOCAL_COMMIT_SIGNAL`。四次连续训练和独立重放完成；0梯度更新，800决策、295实际提交。

| 数据集 | seed | 选中步 | full train ΔR pp | monitor ΔR pp | 末点monitor ΔR pp | 原E47 RL选中monitor ΔR pp | 提交次数/200 |
|---|---:|---:|---:|---:|---:|---:|---:|
| WebVid | 21 | 200 | +0.6250 | +0.3125 | +0.3125 | +0.0781 | 91 |
| WebVid | 22 | 40 | +0.2490 | +0.2051 | +0.1758 | +0.0098 | 94 |
| Yandex | 21 | 200 | +0.2515 | +0.0586 | +0.0586 | +0.0000 | 55 |
| Yandex | 22 | 140 | +0.1831 | -0.0977 | -0.1270 | +0.0781 | 55 |

连续提交已经把部分已见候选机会转成真实静态画像收益，说明E50的更新转化缺口可以实际改善。WebVid两seed选中monitor +0.3125/+0.2051pp，高于原E47 RL对应+0.0781/+0.0098pp；第一seed末点完整训练池+0.6250pp，第二seed末点+0.6543pp。但这是不同状态逐步分岔后的完整算法对照，不是固定状态因果消融，直接证据仍由E50/E51提供。

损伤和种子不稳定也真实存在：Yandex第一seed选中monitor +0.0586pp，第二seed−0.0977pp、末点−0.1270pp，而原E47 RL第二seed选中为+0.0781pp。两seed末点完整训练池均上涨（+0.2515/+0.2734pp），不能据此声称独立query稳定提升。预锁双集“至少一个可行正monitor候选”门通过，只说明候选信号存在；不是四seed稳定性、开发或性能GO。该方法是贪心局部搜索对照，不包装成RL。

## 方法与实际成本

原E47 RL P/B/scale/局部H×16、两seed/200×8/σ.3/GT无关hub和Gaussian ε保持。原J在全部合法候选（系数±2内）与不动之间择优，平分先不动再原序；原八候选即使越界也按原Gaussian真实评测，只限制提交。没有Adam/动量，checkpoint的零m/v只是存储兼容。完整train4096实际route/精确补测，当前缓存来自真正被选中的候选，每步重新build提交W验证拓扑SHA；新状态下一步重新获得真实反馈。

原step0/20/…/200 monitor1024与非零feasible checkpoint选择保持，train512从完整缓存提取。每步确定J不减与逐query提交命中差守恒通过，净命中/monitor损伤不隐藏。selected/last导出普通静态HNSW/W，线上仍一次HNSW→三个真实ID→原NSG，没有在线策略模型。

实际113950 NSG=62976冷启动/监控/parity固定调用+50974候选变化；26276864 HNSW、7212普通构图、6400候选、800决策、295提交、0梯度更新。逻辑候选26214400行与真实新增搜索分开；无额外均值route。WebVid/Yandex进程349.330/270.407s，累计619.738s约10.3分钟，实际单线程CPU15、串行，含加载/构图/写盘/验收，不是线上QPS。

## 核验与解释范围

独立6400候选W/画像公式/Gaussian/原奖励、800合法集合择优/no-op/tie/提交拓扑链、全部完整cache hash/50974变化patch、292638集合评分、44全checkpoint、8导出和512三路parity通过，22.427s，0新搜索。原E37–E51/source/native/data/GT全SHA保护；4job完整预留400000、全部成功，无失败重试。

0新cal/audit/原validation/held-out查询或训练反馈、新GT/QPS。原monitor参与checkpoint选择，不能称盲测。默认保持WebVid GT10-soft-t1 / Yandex GT10-hard；最新完整Recall–QPS仍E49，未形成双集前沿增益。

## 接续

下一阶段E53保留原RL八候选LOO梯度和Adam方向，以GT无关的候选中位半径r，在r/4、r/2、r三个真实确定点与不动之间按原J选择；Gaussian候选只估计方向，不可直接提交。m/v和局部计数每步推进，实际均值接受后真实恢复图身份与缓存。其依据来自E51放大机会和最大半径损伤的固定控制；协议在E52完整结果之前写定，源码和独立审计已准备，尚未冻结训练。

E53四run预计9612build/36107264 HNSW，NSG固定62976+实际变化、每run预留150000/总600000，0新开发反馈。用E52实测时长保守估算，须预计21:10前完成；用户最后最佳候选对NSG/Fast/FastGT的QPS/Recall/零GT10失败率比较必须在21:15前进入准备窗口，21:40停止新查询，22:00收口。当前尚未执行最终完整比较。


[协议](protocol.md)、[模型表](results/models.csv)、[44 checkpoint](results/checkpoints.csv)、[800真实步骤](results/steps.csv)、[成本](results/cost.json)、[局部门](results/gate.json)、[独立核验](reviews/training_verification.json)、[完整学习曲线](figures/commit_learning.svg)。
