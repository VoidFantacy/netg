# P2 trace 机制解释独立复核

复核时间：2026-09-07T16:50:20.578751+00:00。只读取既有 report、count/timing 分析及原始 trace；没有启动 ANN 搜索、模型训练或新的实验。

结论：在两个数据集都确认了“非 GT 中间节点在区域队列中得到扩展，继而成为新增 GT 的实际首次发现祖先；同入口统一队列曾在扩展前淘汰或拒绝该节点”的具体证据。此处 GT 指每条查询的精确前 10 个目标。证据支持候选保留方式确实改变可探索路径，而不是仅改变最终 GT 结果收集器。不过，oracle 也会丢失原本找到的 GT，且区域队列伴随更多节点扩展与距离计算。它支持继续做有限诊断，不能证明可部署的效率改善，也不能单独通过 P2 gate。

## 覆盖和样本边界

既有分析独立重放 320 条 trace，形成 192 对同 route（入口、共享种子、区域与权重一致）的比较。实际仅查询 ID 0–15；预选但未观察的 ID 为 157、631、2003、4093、6007、8009、9967。12 个数据集 × L × 比较单元都有上述 16 条配对，但全部预注册查询矩阵应为 276 对，当前并不完整。以下统计仅描述这个预选子集，不作总体推断。

下表比较 oracle_unified → oracle_probability。扩展和未扩展淘汰都是 16 条查询的合计；Recall 差用百分点（pp）。

| 数据集 | L | Recall 差 pp | 获得 / 损失 GT | 有非 GT 救回路径证据的查询 | 扩展数 | 未扩展淘汰数 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| WebVid | 64 | +11.875 | 24 / 5 | 8 / 16 | 1167 → 1385 | 2660 → 3361 |
| WebVid | 128 | +4.375 | 14 / 7 | 4 / 16 | 2178 → 2381 | 4696 → 5671 |
| Yandex | 64 | +3.750 | 9 / 3 | 2 / 16 | 1084 → 1345 | 3163 → 4591 |
| Yandex | 128 | +0.625 | 1 / 0 | 1 / 16 | 2103 → 2332 | 4688 → 6832 |

四组均增加扩展和未扩展淘汰总数，因此“区域保护减少了全局候选排斥”不是受支持的表述。准确说法是：它改变了哪些候选得到扩展，救回某些路径的同时也失去另一些路径。

## 可复查例子

以下为事后选取的说明性例子：按数据集，先取 L 较小者，再取 query ID 最小、Recall 净提高且含非 GT 救回证据的查询；反向例子用同样排序选净下降且含非 GT 受损证据者。这一可复现规则不把例子选择伪装成事前注册，也不以它估计发生率。所有事件位置采用原始 events 数组的 0 起始索引。

### WebVid q1，L=64：救回

同入口 oracle_unified → oracle_probability：Recall 0.9 → 1.0；获得 GT [639265]，损失 GT []。图距离计算 NDC 958 → 1314；扩展数 67 → 87；未扩展淘汰数 138 → 243。

- [oracle_unified 原始 trace](webvid_eval/trace.json.parts/trace_L64_oracle_unified_q1.json)，SHA256 `a01399c1830deb962cfead46fa8c45ee8d83cfc068b18064d81bbd1ae50b3b01`。
- [oracle_probability 原始 trace](webvid_eval/trace.json.parts/trace_L64_oracle_probability_q1.json)，SHA256 `4d4fed4f579a2d6f88db09bbb9079c448d5fa100992d5ef3f35a52d7e00ce216`。

GT 639265 在 oracle_probability 的首次发现链：

`2240578 → 2314825 → 1273252 → 1083485 → 217514 → 2426846 → 1357219 → 1048768 → 1462506 → 10681 → 639265`

- 非 GT 节点 2240578（区域 29）在 oracle_probability 事件 75 扩展；在 oracle_unified 事件 189 被节点 1270775 从队列 0 淘汰，此前未扩展。
- 非 GT 节点 1083485（区域 29）在 oracle_probability 事件 619 扩展；在 oracle_unified 事件 654 被节点 1801483 从队列 0 淘汰，此前未扩展。
- 非 GT 节点 1048768（区域 28）在 oracle_probability 事件 1459 扩展；在 oracle_unified 事件 1651 被节点 738134 从队列 0 淘汰，此前未扩展。

### WebVid q12，L=64：反向损失

同入口 oracle_unified → oracle_probability：Recall 0.6 → 0.5；获得 GT []，损失 GT [260773]。图距离计算 NDC 1427 → 1561；扩展数 68 → 81；未扩展淘汰数 213 → 242。

- [oracle_unified 原始 trace](webvid_eval/trace.json.parts/trace_L64_oracle_unified_q12.json)，SHA256 `47a873e6e4f062d4edb980b8ac2824f8b63ef5e816fba50d1f9464eca20bb826`。
- [oracle_probability 原始 trace](webvid_eval/trace.json.parts/trace_L64_oracle_probability_q12.json)，SHA256 `af7294332faabd4964476ea5a88b209812c49d963cec03dfdf7f1cee8b675682`。

GT 260773 在 oracle_unified 的首次发现链：

`637368 → 729443 → 752315 → 316561 → 260773`

- 非 GT 节点 729443（区域 39）在 oracle_unified 事件 60 扩展；在 oracle_probability 事件 703 被节点 2170496 从队列 0 淘汰，此前未扩展。
- 非 GT 节点 752315（区域 28）在 oracle_unified 事件 101 扩展；在 oracle_probability 事件 3048 被队列 1 拒绝。

### Yandex q4，L=64：救回

同入口 oracle_unified → oracle_probability：Recall 0.7 → 0.8；获得 GT [138328, 1453890]，损失 GT [3845869]。图距离计算 NDC 2640 → 3008；扩展数 70 → 81；未扩展淘汰数 233 → 288。

- [oracle_unified 原始 trace](yandex_eval/trace.json.parts/trace_L64_oracle_unified_q4.json)，SHA256 `798dd95d874a717c25540f8f2f021908b9313bfa3092759e3a3c5ed0df47e274`。
- [oracle_probability 原始 trace](yandex_eval/trace.json.parts/trace_L64_oracle_probability_q4.json)，SHA256 `b70839bbb688748ceb1ec10c4632a9e27c184a64ea0b100c784263805dea9295`。

GT 138328 在 oracle_probability 的首次发现链：

`5889839 → 7728837 → 5398566 → 4840171 → 6389396 → 6680956 → 138328`

- 非 GT 节点 7728837（区域 18）在 oracle_probability 事件 95 扩展；在 oracle_unified 事件 468 被节点 5980762 从队列 0 淘汰，此前未扩展。
- 非 GT 节点 5398566（区域 61）在 oracle_probability 事件 199 扩展；在 oracle_unified 事件 1546 被节点 1646495 从队列 0 淘汰，此前未扩展。
- 非 GT 节点 6389396（区域 20）在 oracle_probability 事件 1617 扩展；在 oracle_unified 事件 5578 被队列 0 拒绝。

GT 1453890 在 oracle_probability 的首次发现链：

`5889839 → 7728837 → 5398566 → 4840171 → 5795539 → 3973369 → 4136634 → 1453890`

- 非 GT 节点 7728837（区域 18）在 oracle_probability 事件 95 扩展；在 oracle_unified 事件 468 被节点 5980762 从队列 0 淘汰，此前未扩展。
- 非 GT 节点 5398566（区域 61）在 oracle_probability 事件 199 扩展；在 oracle_unified 事件 1546 被节点 1646495 从队列 0 淘汰，此前未扩展。
- 非 GT 节点 5795539（区域 63）在 oracle_probability 事件 3086 扩展；在 oracle_unified 事件 3046 被队列 0 拒绝。

此查询同时损失 GT 3845869，已经说明救回不是逐目标单调改善。统一队列找到该 GT 的链中，非 GT 节点 4640674 和 9207050 在区域队列均于扩展前被队列 1 淘汰；完整链和事件状态见 report.json 对应 harmed_target_discovery_paths。

### Yandex q13，L=64：反向损失

同入口 oracle_unified → oracle_probability：Recall 1.0 → 0.9；获得 GT []，损失 GT [8500333]。图距离计算 NDC 1456 → 2199；扩展数 71 → 91；未扩展淘汰数 219 → 325。

- [oracle_unified 原始 trace](yandex_eval/trace.json.parts/trace_L64_oracle_unified_q13.json)，SHA256 `2d832719aa8635e8631b40ca84b37165788a614ecca25f1b8a87a75ee42a18c3`。
- [oracle_probability 原始 trace](yandex_eval/trace.json.parts/trace_L64_oracle_probability_q13.json)，SHA256 `57165e8a06095d3bc48a46c46ae6b4c68625933e91880bcfa0426132ef96566d`。

GT 8500333 在 oracle_unified 的首次发现链：

`7056446 → 6767015 → 1573674 → 9078193 → 8740824 → 3635644 → 9795880 → 8159898 → 3044952 → 4776700 → 9598536 → 2641315 → 8500333`

- 非 GT 节点 7056446（区域 43）在 oracle_unified 事件 20 扩展；在 oracle_probability 事件 1223 被节点 755223 从队列 3 淘汰，此前未扩展。
- 非 GT 节点 9078193（区域 43）在 oracle_unified 事件 275 扩展；在 oracle_probability 事件 1954 被节点 1219788 从队列 3 淘汰，此前未扩展。
- 非 GT 节点 2641315（区域 42）在 oracle_unified 事件 2415 扩展；在 oracle_probability 事件 2684 被节点 3412882 从队列 1 淘汰，此前未扩展。

## 与完整 10K pilot 的关系

以下数值直接读取既有 analysis_v1/analysis.json，用于约束机制解读；不是由 16 条 trace 外推。每项是同 route、固定 L 下 probability 区域队列减去相应 unified 队列的 Recall 差。置信区间是逐项探索性 paired-query bootstrap 95% 区间，未做多重比较校正。

| 数据集 | L | 真实几何路由差 pp | oracle 路由差 pp（95% 区间） | oracle QPS 配对比均值 | oracle 图 NDC 增量 |
| --- | ---: | ---: | --- | ---: | ---: |
| WebVid | 64 | -5.431 | +5.413 [+5.010, +5.826] | 0.696 | +409.030 |
| WebVid | 128 | -3.640 | +5.252 [+4.917, +5.596] | 0.809 | +417.110 |
| Yandex | 64 | -6.867 | +3.155 [+2.771, +3.540] | 0.715 | +703.125 |
| Yandex | 128 | -3.488 | +3.359 [+3.045, +3.677] | 0.787 | +779.413 |

预选 trace 的 WebVid L64 真实几何路由子集提高 3.125 pp，而完整 10K pilot 下降 5.431 pp；这是小样本不能替代总体结果的直接例子。完整 pilot 中 oracle Recall 提高，也同时降低 QPS、增加 NDC；因此不能把该改善写成已取得有效性能提升。真实几何路由的区域保护在两个数据集和两个 L 均损害 Recall。

## 可以和不可以写入 gate 的结论

- 已验证：在固定入口集合下，区域容量分配与加权队列调度这一联合干预确实改变了扩展路径；存在被统一队列拒绝或提前淘汰的非 GT 祖先，随后在区域搜索中扩展并导向新增 GT。最终结果采用全局 top K，因而“某候选被搜索队列拒绝”等同于“该候选不能入结果”的解释不成立。
- 已验证：正向与反向路径证据同时存在，oracle 也不逐查询、逐目标单调改善。结构/路由质量影响候选保护的价值，完整 pilot 提供了 oracle 潜力与真实几何预测失败之间的差距。
- 尚未证明：例中节点是唯一或必要桥梁。trace 记录的是实际首次发现森林，不是所有可达路径；另一种展开顺序可能经其他路径找到同一目标。
- 尚未证明：同 NDC 或同 wall time 的机制净收益。固定 L 只约束保留容量，未使实际扩展数、距离计算数或运行时间相等；容量分配和调度顺序在当前干预中也不能独立识别。
- 尚未证明：更好的预测器或 P3 训练一定修复真实路由失效。此为下一阶段应证伪的假设，需要 root 的预测诊断和预先冻结的小门槛。

复核建议：把 trace 证据记为机制诊断得到支持；若完整 P2 其余合同和预测诊断满足要求，可由主控记录“允许进入有限 P3 诊断”的研究决策。不要由本报告单独自动判定 GO，不要通过 P5/P6/P7，也不要宣称已有可部署的性能提升。

## 证据绑定

- [trace report.json](trace_analysis_v1/report.json)，SHA256 `af4490cfe36829aa5c3ea7a7b0e39f5e3a6d0ed927e16fb2165da563548f43e2`。
- [完整 10K pilot 分析](analysis_v1/analysis.json)，SHA256 `e73a8d8c16a5bebb2404596b63d621b1780b1aab0f9eb29efce5281edfc04c1f`。
- [trace 分析器独立终核](trace_analysis_review_final.json)。
- 本次说明性例子共直接核对 5 条 GT 首次发现链，覆盖 8 个原始 trace 文件；逐边核对 parent、父节点已扩展、GT/非 GT 标记、配对淘汰/拒绝事件及结果差。原始 trace 的 SHA256 均与 report.json 一致。
