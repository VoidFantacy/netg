# ACSG 当前结果摘要

2026-09-12，最近完成E52，`COMPLETE_DIRECT_CANDIDATE_COMMIT_LOCAL_SIGNAL_SEED_INSTABILITY`。[报告](entry_method_exploration/20260912_direct_candidate_commit_v1/report.md)、[历史41](experiment_history/41_direct_candidate_commit.md)。

| 数据集 | seed | 选中步 | full train ΔR pp | monitor ΔR pp | 末点monitor ΔR pp | 原E47 RL选中monitor ΔR pp | 提交次数/200 |
|---|---:|---:|---:|---:|---:|---:|---:|
| WebVid | 21 | 200 | +0.6250 | +0.3125 | +0.3125 | +0.0781 | 91 |
| WebVid | 22 | 40 | +0.2490 | +0.2051 | +0.1758 | +0.0098 | 94 |
| Yandex | 21 | 200 | +0.2515 | +0.0586 | +0.0586 | +0.0000 | 55 |
| Yandex | 22 | 140 | +0.1831 | -0.0977 | -0.1270 | +0.0781 | 55 |

连续提交已经把部分已见候选机会转成真实静态画像收益，说明E50的更新转化缺口可以实际改善。WebVid两seed选中monitor +0.3125/+0.2051pp，高于原E47 RL对应+0.0781/+0.0098pp；第一seed末点完整训练池+0.6250pp，第二seed末点+0.6543pp。但这是不同状态逐步分岔后的完整算法对照，不是固定状态因果消融，直接证据仍由E50/E51提供。

损伤和种子不稳定也真实存在：Yandex第一seed选中monitor +0.0586pp，第二seed−0.0977pp、末点−0.1270pp，而原E47 RL第二seed选中为+0.0781pp。两seed末点完整训练池均上涨（+0.2515/+0.2734pp），不能据此声称独立query稳定提升。预锁双集“至少一个可行正monitor候选”门通过，只说明候选信号存在；不是四seed稳定性、开发或性能GO。该方法是贪心局部搜索对照，不包装成RL。

实际113950 NSG/26276864 HNSW/7212build/800决策295提交，约10.3分钟；6400候选/800提交/44checkpoint/8导出/292638集合评分独立审计通过。0新开发/QPS；最新完整曲线仍E49，默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。

E53保留RL方向并按真实J接受预定步长，协议/源码已准备、尚未冻结训练。用户目标持续至22:00并最终比较最佳候选与NSG/Fast/FastGT三指标，最终完整比较尚未执行，详见[s-target](s-target.md)。
