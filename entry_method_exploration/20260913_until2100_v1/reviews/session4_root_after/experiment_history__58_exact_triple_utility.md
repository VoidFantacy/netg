# 58. E69 完整画像前三的真实NSG效用

2026-09-13，第4串行会话。Yandex通过预锁的有限辅助质量接续门，WebVid未通过；当前默认未替换。该结果来自真实原NSG返回与完全相同输入的缓存，未计完整在线画像扫描，不是QPS或效用oracle。

| 数据 | 对照 | 净命中 | ΔRecall pp | 救回/新增失败 | 失败净增 | 两半净命中 |
|---|---|---:|---:|---|---:|---|
| WebVid | exact_P | -109 | -0.1371 | 32/39 | +7 | [-86, -23] |
| WebVid | baseline | +85 | +0.1069 | 46/40 | -6 | [26, 59] |
| WebVid | mode3P | +191 | +0.2402 | 36/17 | -19 | [64, 127] |
| Yandex | exact_P | +132 | +0.1660 | 36/26 | -10 | [32, 100] |
| Yandex | baseline | +97 | +0.1220 | 40/32 | -8 | [1, 96] |
| Yandex | mode3P | +48 | +0.0604 | 12/8 | -4 | [15, 33] |

WebVid精确mode比approx mode改善191命中、净减19失败，但精确P本身更强；不能把修正近似的通用收益归因于多模态。Yandex精确P反而比approx P少35命中，精确mode比二者都好，说明该固定表示在此历史aux有局部NSG效用；不存在“精确排序一律更好”的结论。两集损伤与救回同时存在，不按新失败案例训练门控。

继任只测试一个固定ef10→30干预，P/duplicate/mode均有参照；不扫更大ef/种子。WebVid作为原样迁移反证保留，不期待从此结果推出双集提升。是否可部署、是否有完整Recall–QPS收益须独立测量，原E66开发门保持失败。

输入：原router_train[2048:10000]，7952及固定3976两半，全部历史辅助/选择训练反馈。P-fit含旧train/monitor；cal/audit已有暴露。E34最终validation及held-out本阶段未使用。

38,942次新NSG=31,808 baseline plain/count回放+7,070缺口plain/count+64原kernel reference。31,808逻辑exact结果中28,102复用旧三方法、3,535唯一新key、171互alias。旧缓存碰撞15,986项逐字段bits核对；全量原baseline15,904恢复。0HNSW/构图/新GT/梯度；计数和原生操作wall不能当QPS。

原生进程37.904s，其中加载15.892s；独立编译12.842s，主评分0.929s，绘图/查表/I/O另计。CPU15，进程与数值库1线程；两个native实际terminal exit0后评分。42非法整批输入在零调用时拒绝，空输入类型/shape通过；79,520返回独立集合评分，30组GT成员增损/逐query净增损恒等。plain/count及64原wrapper ID/float bits/NDC通过。

[完整配对](../entry_method_exploration/20260913_until2100_v1/stage10_exact_triple_utility_v1/results/paired.csv) · [原值](../entry_method_exploration/20260913_until2100_v1/stage10_exact_triple_utility_v1/results/points.csv) · [全部失败转换](../entry_method_exploration/20260913_until2100_v1/stage10_exact_triple_utility_v1/results/failure_cases.csv) · [图](../entry_method_exploration/20260913_until2100_v1/stage10_exact_triple_utility_v1/figures/exact_triple_utility.png) · [成本](../entry_method_exploration/20260913_until2100_v1/stage10_exact_triple_utility_v1/results/cost.json) · [协议](../entry_method_exploration/20260913_until2100_v1/stage10_exact_triple_utility_v1/protocol.md) · [缓存身份](../entry_method_exploration/20260913_until2100_v1/stage10_exact_triple_utility_v1/reviews/cache_coverage.json) · [验收](../entry_method_exploration/20260913_until2100_v1/stage10_exact_triple_utility_v1/reviews/verification.json)。
