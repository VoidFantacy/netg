# 125 TargetKNN 三点三次轻量完整计时

日期：2026-09-22。E120的用户明确授权补测，不是新学习方法或正式验收；独立版本 `entry_method_exploration/20260922_knn_three_point_timing_v1/`。状态 `COMPLETED_LIGHTWEIGHT_COMPARISON`，默认不变。

## 动机与冻结范围

E120测到了召回率均值提高，但没有测完整QPS。原信息门失败不能替代速度测量，也不能表述为已测出没有加速。用户要求简单比较三个点、每点三次，因此仅补冻结TargetKNN对默认GT10的完整成本，不重训或调参、不改变旧停止结果。

复用原两集各4096条已曝光query、四折角色与目标预算响应。Web K1 L640/800/1000、K100 L800/1120/1250；Y K1 L64/96/128、K100 L128/200/256。全部L使用原同一K选择规则。CPU15实际单线程，双方每点预热128query，再三次4096query完整wall，轮换先后、串行运行。

原生TargetKNN在计时内完成每query归一化、对应fit3072向量的float64精确余弦/top55、七动作标签均值决策、实际选中策略的精确画像或GT10小图路由、原NSG及输出写内存，不查离线动作表。四折fit矩阵离线物化，模型/索引加载和磁盘结果写出不计查询时间；无模型搜索、GT访问或标签拟合在在线路径内。底图、主搜索、入口顺序及固定L不变。

## 结果

12个匹配点的召回均值均正，完整QPS均负，而且双方三次范围在各点均不重叠。Web K1的召回提高+.2197至+.2930pp、QPS下降19.81%至26.96%；K100提高+.1077至+.1396pp、QPS下降17.58%至24.39%。Y K1提高+.1465至+.3174pp、QPS下降40.52%至54.06%；K100提高+.0784至+.1143pp、QPS下降27.88%至40.45%。完整12点和三次范围见报告，逐次QPS在metrics.csv。

90%召回处仅作相邻点之间的时间线性插值参考，不外推：Web R1/R100的默认→TargetKNN为446.1→362.5、368.5→302.9QPS（−18.75%/−17.79%）；Y为2502.0→1470.4、1427.2→1012.6QPS（−41.23%/−29.05%）。这是粗略三点插值，不是精确匹配召回实测。按已测点达到90%门槛直接选择时，四格也均更慢；Web R100虽能从默认L1250降到候选L1120达到90%，候选302.2QPS仍低于默认336.8。

结论：召回确有小幅正均值，当前完整实现速度成本更高，所测三点未形成净加速。不能据本轮外推所有kNN实现/所有入口学习，也不据三重复宣称正式显著性。默认Web soft/Y hard和生产E99不改，不追加性能调参或新模型。

## 验证与成本

全16384个query/K的近邻集合、动作和入口复现E120；所有默认输出恢复E105，11个已存在候选预算点恢复E107/E120，新增Web K1/L1000按真实GT评分。主点召回增益与前轮相同。全部三重复返回逐位一致，768次原核/链接E99 smoke通过；独立成员循环与广播成员比较分别重评分。76输入及E120 seal、冻结源码/模型身份保持，原始文件未改。

24方法点、72次完整wall、298752次NSG（计时294912、预热3072、核验768）。两集作业498.23秒，编译8.72秒；0重训/新GT/画像/图/新鲜测试载荷。OOF四模型驻留并按原query顺序切换，不是单一最终部署模型。作业wall含加载/检查，不能代替表中的查询QPS。

## 证据

- [报告与完整三次范围](../entry_method_exploration/20260922_knn_three_point_timing_v1/report.md)、[逐次QPS](../entry_method_exploration/20260922_knn_three_point_timing_v1/metrics.csv)。
- [协议](../entry_method_exploration/20260922_knn_three_point_timing_v1/protocol.md)、[配置](../entry_method_exploration/20260922_knn_three_point_timing_v1/config.locked.json)、[原生实现](../entry_method_exploration/20260922_knn_three_point_timing_v1/src/benchmark.cpp)。
- [分析](../entry_method_exploration/20260922_knn_three_point_timing_v1/analysis.json)、[作业账](../entry_method_exploration/20260922_knn_three_point_timing_v1/reviews/jobs.json)、[状态](../entry_method_exploration/20260922_knn_three_point_timing_v1/state.json)。
