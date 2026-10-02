# E75 精简画像保留原随机层级

2026-09-13，第6串行会话。唯一改变是精简时按原slot消耗随机流，保留原节点层级；画像、紧凑插入顺序、种子、ef10与7slot去重3真实入口均固定。Web1771/Y2067画像，真实H815/821、原NSG/raw-IP保持。

| 数据 | 新图对照 | 净命中 | ΔRecall pp | 救回/新增失败 | 两半净命中 | 路由/总NDC变化% |
|---|---|---:|---:|---|---|---|
| WebVid | baseline10 | -118 | -0.1484 | 40/53 | [-49, -69] | +3.12/+0.16 |
| WebVid | compact10 | -59 | -0.0742 | 8/10 | [-33, -26] | -0.49/-0.04 |
| Yandex | baseline10 | +98 | +0.1232 | 42/32 | [24, 74] | +19.41/+0.79 |
| Yandex | compact10 | -22 | -0.0277 | 5/8 | [-15, -7] | -0.68/+0.07 |

预锁接续门：WebVid未通过, Yandex未通过。要求同时胜P与compact、两半非负且零命中失败不增。无一集通过，停止本层级控制，不新增其完整wall或扫seed/ef。 原E73/E74局部信号及全部旧门保持，不替换默认，不由NDC/同LRecall宣称性能改善。

WebVid：普通精简使207个保留节点层级改变；本图全部1771个层级恢复原full对应slot。原入口slot 166，普通compact入口对应原slot 222，新图入口对应原slot 166。层级保留连同入口身份改变，是本次构图干预；它不保留原full邻接或保证改善检索。
Yandex：普通精简使235个保留节点层级改变；本图全部2067个层级恢复原full对应slot。原入口slot 166，普通compact入口对应原slot 204，新图入口对应原slot 166。层级保留连同入口身份改变，是本次构图干预；它不保留原full邻接或保证改善检索。

实际97152 NSG/96960 HNSW/2真实小图；合成另4图/512 HNSW。成功编译5.527s、构图0.312s、四native总91.830s；无新画像训练/GT/梯度，继承E66画像训练30.286s及早期GT成本未重测、不记零。计数操作wall不是QPS，正式QPS为0。首次编译priority_queue比较错误及源码/日志保留，0构图/查询后修复，不影响冻结模型或预算。

独立48480集合/mask、47712逐行set评分、31808旧控制全字段恢复、全部plain/count及192原kernel通过。19586相同三入口返回/距离bits/graphNDC恢复；全部七slot距离/映射/去重和图W/labels/邻接、原随机流与保留层级均核验。合成实际覆盖零/正层、最高入口删除、非同一内外label、ties、重复返回及5种非法keep拒绝。

输入为历史aux7952和固定3976两半，选择反馈计训练；P-fit含旧train/monitor，cal/audit/aux均历史暴露。本轮未新增fit/cal/audit查询，E34最终与held-out未进入。CPU15/实际进程和数值库1线程、方法与数据集串行，两个数据集原生工具terminal0后评分；失败严格GT10零命中，成员集合得失与query净命中正负部分列。整日目标未完成。

[协议](protocol.md) · [配对](results/paired.csv) · [原值](results/points.csv) · [失败查询](results/failures.csv) · [层级身份](results/levels.json) · [成本](results/cost.json) · [图](figures/preserved_levels.png) · [验收](reviews/verification.json)。
