# E73 同hub完全重复画像精简

2026-09-13，第5串行会话。仅精简原mode bank同hub字节完全相同的重复槽，保留所有不同向量和原序；Web2445→1771、Y2463→2067，真实H815/821和原P保留。普通原seed/M16/efConstruction200重建两张小图，ef10、7slot去重前三真实hub、原NSG/raw-IP不变。

| 数据 | compact 对照 | 净命中 | ΔRecall pp | 救回/新增失败 | 两半净命中 | 路由/总NDC变化% |
|---|---|---:|---:|---|---|---|
| WebVid | baseline10 | -59 | -0.0742 | 44/55 | [-16, -43] | +3.63/+0.20 |
| WebVid | mode10 | +47 | +0.0591 | 13/11 | [22, 25] | -0.65/-0.09 |
| Yandex | baseline10 | +120 | +0.1509 | 41/28 | [39, 81] | +20.22/+0.72 |
| Yandex | mode10 | +71 | +0.0893 | 15/6 | [53, 18] | -0.10/-0.16 |

开发质量标记：WebVid未通过, Yandex通过。原E66/E70/E72门保持，不自动替换默认。按前瞻协议，E74将固定这个唯一compact候选并进行完整同批wall，检验真实费用及质量；即使质量未过，也诚实保留成本反证，不调参或改门。

原full bank按old_to_compact全部还原W与真实hub字节，因此对任意query每hub完整max画像分数集合不变。duplicate3P压缩后的字节集合等于原P，P控制引用原物理图；不声称duplicate的近似图等价。新compact近似拓扑及入口仍会变化，削减节点数量不等于已知QPS节省。

完整mode前三一致率（full → compact）：
- WebVid: 77.73% → 80.97%。
- Yandex: 86.38% → 89.76%。

实际97152 NSG/96960 HNSW/2小图构建，0新聚类/画像训练/GT/梯度；精简0.031s、小图build 0.348s、编译25.432s、四native进程90.132s。12 plain和12 count图加载；图/路由分项wall未单独计时为null，本阶段无QPS。继承E66画像训练及GT成本不是零。

48480集合/mask和47712独立标量集合评分、31808旧控制返回/入口/距离bits/两NDC恢复、全部plain/count与192原kernel通过；七slot完整距离/映射/去重、序列化W/label和source row核验通过。40940相同三入口结果恢复E69。1/2/3槽有效和空/4槽/负ID/H不匹配拒绝在构图前测试。

输入为历史aux7952及固定3976两半，选择反馈计训练；P-fit包含旧train/monitor，cal/audit/aux均历史暴露。E34最终与held-out未读取。CPU15实际进程与数值库1线程，双集原生terminal0后独立分析。strict failure=GT10零命中；GT成员得失、query净命中正负部、救回/新增分账，全量aligned返回与失败源行保留。

[配对](../entry_method_exploration/20260913_until2100_v1/stage14_compact_modes_v1/results/paired.csv) · [原值](../entry_method_exploration/20260913_until2100_v1/stage14_compact_modes_v1/results/points.csv) · [失败查询](../entry_method_exploration/20260913_until2100_v1/stage14_compact_modes_v1/results/failures.csv) · [成本](../entry_method_exploration/20260913_until2100_v1/stage14_compact_modes_v1/results/cost.json) · [图](../entry_method_exploration/20260913_until2100_v1/stage14_compact_modes_v1/figures/compact_control.png) · [协议](../entry_method_exploration/20260913_until2100_v1/stage14_compact_modes_v1/protocol.md) · [验收](../entry_method_exploration/20260913_until2100_v1/stage14_compact_modes_v1/reviews/verification.json)。
