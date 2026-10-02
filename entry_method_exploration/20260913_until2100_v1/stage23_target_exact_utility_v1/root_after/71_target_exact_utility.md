# E82 新目标画像完整排名的真实效用

三种冻结bank、两数据集完整诊断完成。后续轻量近似候选：无；六组原诊断门均未通过。原E79–E81门不变，整日21:00目标未完成。

| 数据 | 完整排名 | 相对精确P 命中/失败变化 | 相对compact | 相对自身近似 | 门 |
|---|---|---|---|---|---|
| WebVid | target10 | +3 / +2 | +256 / -22 | +208 / -18 | FAIL |
| WebVid | conditional10 | -22 / +7 | +231 / -17 | +211 / -23 | FAIL |
| WebVid | joint10 | -118 / +4 | +135 / -20 | +154 / -17 | FAIL |
| Yandex | target10 | +66 / -6 | -89 / +9 | +31 / -2 | FAIL |
| Yandex | conditional10 | +51 / -10 | -104 / +5 | +28 / -5 | FAIL |
| Yandex | joint10 | +110 / -12 | -45 / +3 | +17 / +1 | FAIL |

精确画像前三不是NSG效用oracle，也没有测完整在线扫描wall。上述是同L真实效用诊断，不能称QPS、前沿或最终改善。每bank对精确P和compact全量命中须正、两半非负、zero失败不增、graphNDC<=1.01，相对自身approx全量非负；全部门先冻结。完整两半、GT成员得失、逐query净命中正负、旧收益保留/丢失和新损伤均在CSV。

新增7,762次NSG，其中原P256行plain/count=512、3,593唯一缺口plain/count=7,186、原kernel64。47,712逻辑exact结果中43,800旧复用、319互alias；源缓存碰撞60,831逐字段一致。0HNSW/构图/新训练/GT/编译。双集native 21.140s，其中load 16.467s；排名准备 5.181s，主评分1.612s；绘图/文档另计，继承GT/P/旧训练成本未知。这些操作wall不是QPS。

全部159,040集合/mask独立评分、47,712复用来源与三入口逐行核验、256原P回放及64原kernel/全缺口plain-count通过。三个bank各两行完整标量排名检查，完整bank max聚合和源namespace/rows核验。所有ANN CPU15、实际进程及数值库1线程串行，工具实际terminal0后评分。

失败并集517条dataset/source-row，343条状态变化；全GT10/各方法三入口与返回ID保存，图仅展示每集前24变化例，全方法零命中行保留。

数据为历史router_train[2048:10000]辅助7952及固定两半，选择反馈计训练。P-fit20K含旧train/monitor，cal/audit历史使用；E34最终和held-out未打开。保留全部旧产物和seal，无新默认替换。

[前瞻协议](../entry_method_exploration/20260913_until2100_v1/stage23_target_exact_utility_v1/protocol.md) · [原值](../entry_method_exploration/20260913_until2100_v1/stage23_target_exact_utility_v1/results/points.csv) · [完整配对](../entry_method_exploration/20260913_until2100_v1/stage23_target_exact_utility_v1/results/paired.csv) · [收益保留](../entry_method_exploration/20260913_until2100_v1/stage23_target_exact_utility_v1/results/gain_retention.csv) · [质量门](../entry_method_exploration/20260913_until2100_v1/stage23_target_exact_utility_v1/results/gate.json) · [完整失败查询](../entry_method_exploration/20260913_until2100_v1/stage23_target_exact_utility_v1/results/failure_queries.csv) · [效用图](../entry_method_exploration/20260913_until2100_v1/stage23_target_exact_utility_v1/figures/exact_utility_v2.png) · [失败图](../entry_method_exploration/20260913_until2100_v1/stage23_target_exact_utility_v1/figures/failure_queries_v2.png) · [成本](../entry_method_exploration/20260913_until2100_v1/stage23_target_exact_utility_v1/results/cost.json) · [验收](../entry_method_exploration/20260913_until2100_v1/stage23_target_exact_utility_v1/reviews/verification.json)

数值边界：近tie仍保留完整分母。Web全局/条件/联合近tie20/21/19条，其exact−approx净命中0/0/−1；其余远离tie条目+208/+211/+155。Y近tie8/5/8条净0，远离tie+31/+28/+17。float64完整排名未宣称与原SIMD逐位等价，不能把全部差额纯归遍历。[完整精度分组](../entry_method_exploration/20260913_until2100_v1/stage23_target_exact_utility_v1/results/precision_groups.csv)。初版正柱标签留白不足，原图保留，报告链接为v2，仅修绘图范围。
