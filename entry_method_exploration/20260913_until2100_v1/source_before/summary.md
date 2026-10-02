# ACSG 当前结果摘要

2026-09-12，今晚离线RL、动作诊断和最终基线比较已完成。主结论：局部动作有收益，旧更新步幅的转化问题已经得到真实控制支持；修正后仍以稀疏支持和少量关键损伤为主，尚未获得超过匹配GT10起点的稳定Recall–QPS增量。

E58完整12条轨迹、2400步、908个接受动作：monitor命中完全不变占WebVid73.5%–88.9%、Yandex90.0%–96.6%；E53两seed累计monitor收益/损伤分别80/84和8/8。WebVid有同一步跨query增损并存，Yandex该监控样本未观察到；不能把这些结果概括为共享表示不可调和的硬冲突。

E59固定19模型cal池只有WebVid11/1024、Yandex7/1024个query可获益，逐query免费选优的有限上界为+0.293/+0.117 pp，仅填补约1.2%的起点漏检。cal最佳单模型与该上界的差额主要为未覆盖，而非自身损伤。该上界仅覆盖已测模型，不是全画像/图空间上界。

本轮学习对象是815/821入口画像节点的Micro-HNSW，底层NSG固定。E53是离线联合画像/拓扑RL，E56是离线学习构图坐标C、以固定P评分的G(C)；在线均普通HNSW取3入口后原NSG，无RL策略推理。纯构图双seed加入后，19候选cal仍选中WebVid E52 seed21拓扑部署、Yandex E53 seed22联合RL；E52本身是贪心对照。默认继续WebVid GT10-soft、Yandex GT10-hard。

以下L128代表点：历史validation2000/集，实际单线程，五轮纯端到端wall；失败为GT10零命中。完整五L的新候选Recall均未超过匹配起点，QPS差异处于五轮波动内。Fast/FastGT对NSG原有收益不能归给新RL。

| 数据集 | 方法 | Recall@10 % | QPS五轮中位数 | 五轮QPS范围 | 零命中失败率 % |
|---|---|---:|---:|---:|---:|
| WebVid | NSG | 70.940 | 2121.37 | 2105.02–2124.23 | 5.15 |
| WebVid | Fast（GT1、30K） | 73.990 | 2299.65 | 2281.28–2306.25 | 2.70 |
| WebVid | FastGT10-hard | 74.175 | 2315.05 | 2304.59–2322.65 | 2.45 |
| WebVid | GT10-soft匹配起点 | 74.190 | 2320.38 | 2305.80–2323.76 | 2.55 |
| WebVid | cal选中新候选 | 74.145 | 2321.73 | 2302.17–2323.99 | 2.45 |
| Yandex | NSG | 88.660 | 2068.63 | 2063.97–2072.18 | 2.95 |
| Yandex | Fast（GT1、30K） | 89.830 | 2283.00 | 2278.40–2286.82 | 1.85 |
| Yandex | FastGT10-hard | 90.055 | 2281.23 | 2271.87–2284.64 | 1.60 |
| Yandex | cal选中新候选 | 89.980 | 2282.81 | 2282.03–2288.40 | 1.70 |

[完整收口报告](entry_method_exploration/20260912_until2000_v1/closeout/final_report.md)、[最终五L/225轮](entry_method_exploration/20260912_expanded_final_comparison_v1/report.md)、[动作诊断](entry_method_exploration/20260912_accepted_action_conflicts_v1/report.md)、[19模型迁移](entry_method_exploration/20260912_frozen_pool_transfer_v1/report.md)。

monitor曾参与初始P拟合和选点；cal已用于模型选择；历史validation非项目盲测。全部局部正信号、负结果、独立集合评分/图身份/计时和数据范围核验保留。下一轮设计未运行，见[s-target.md](s-target.md)。
