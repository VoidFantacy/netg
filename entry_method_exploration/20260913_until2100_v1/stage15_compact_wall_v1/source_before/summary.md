# ACSG 当前结果摘要

2026-09-13，第5串行会话完成E72/E73。E73精简版在Yandex历史辅助质量门通过；WebVid仍低于P10。尚未测本候选完整QPS，不替换默认；整日21:00目标未完成，E34晚间最终反馈未使用。

E73只删除同一hub的字节完全相同画像，Web2445→1771、Y2463→2067，保留全部不同模式向量与真实H815/821。源bank能由保留slot精确恢复，故每hub完整max评分集合不变；普通重建小图改变近似遍历，仍ef10/7slot去重3入口→原NSG。

| 数据 | compact对P10 | compact对完整mode10 |
|---|---|---|
| WebVid | −59命中、失败+11、两半−16/−43 | +47、失败−2、两半+22/+25 |
| Yandex | +120命中、失败−13、两半+39/+81 | +71、失败−9、两半+53/+18 |

路由NDC相对完整mode只降低Web0.649%/Y0.098%，总NDC−0.092%/−0.165%；相对P10路由仍+3.63%/+20.22%。删除节点比例不能换算QPS。E73按预锁协议进入独立E74同批五L五轮，以实际compact为唯一新候选，保留完整mode和规定基线，不按新反馈调参。

E73新增97152 NSG/96960 HNSW/2小图，0新画像训练/GT；精简.031秒、build .348秒、编译25.432秒、四native90.132秒。48480集合/mask及47712独立标量评分、31808旧控制返回/距离/入口/两NDC、192原kernel、全部图W/label及七slot验证通过。实际CPU15/进程与数值库1线程，全部工具terminal0后分析。

E72 distinct10本版本按双集原门停止，0QPS。Y对P10 +73命中/失败−6，Web−21/失败+4；相对mode30路由NDC−25%～31%，但质量未保住，局部信号保留。E71完整65点325wall没有稳定整体前沿改善，E66/E70旧门保持。

本会话累计291456 NSG/290880 HNSW/2实际build，合成另4图/512HNSW。P-fit含旧train/monitor，cal/audit/aux均历史暴露，辅助选择计训练；E34最终与held-out今日未进入。全部旧产物、source_before与root_after封存保留。

[E73报告](entry_method_exploration/20260913_until2100_v1/stage14_compact_modes_v1/report.md) · [E72](entry_method_exploration/20260913_until2100_v1/stage13_distinct_hub_width_v1/report.md) · [下一阶段](s-target.md)。
