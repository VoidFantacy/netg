# E101：原生 Faiss NSG 同图比较与优化价值

用户要求比较库与项目实现、判断哪里值得优化。本轮完成，E101于2026-09-16完成内置Faiss1.9.0同图比较：WebVid四点、十版本、120轮plain/2000000search；GT10的span+batch4组合相对当前E99四点QPS变化+13.10%至+26.56%，各GT10控制返回和NDC相同。高预算K100/L1250组合341.45QPS、Recall@100 90.6868%，当前GT10 269.80QPS；原生Faiss 230.52QPS/90.4819%。另做80000次真实batch4计数核验及496000次四集一致性回归，其它四集64配置的输出ID/距离bits/入口/逐query NDC全部与E99一致。

本轮原生基线为内置Faiss1.9.0，直接调用IndexNSG.search，借用同一storage和邻接，不重构图；它使用入口邻居加随机点填满L，与项目固定一个/GT10三个初始点不同。native不能与项目版本强求返回一致，也不能只按同L时间判断。当前NSG/GT10实际链接E99库。研究用minimal/core及span、prefetch-filter、batch4、span-batch4是独立适配，不冒称原生库；所有代码和模型原件保持。

WebVid锁定K1/L96、K100/L100、K1/L800、K100/L1250，10K原public query，CPU15/单线程/方法串行。每配置warm+3plain+count，共40点120plain/2000000search；6480组合差分普通与ASan/UBSan均通过。每个GT10控制的ID、距离bits、入口与逐query NDC同E99；原生返回与自己的public API对齐并检查合法性，GT独立严格ID评分。少NDC不必更快，而相同NDC下批量计算与邻接组织可以改变wall；收益不能全归于SIMD，也不能把空槽比例当节省时间。

主count的batch4默认scalar转发局限另以80000次真实batch4包装核验补齐，原计时不改，细节见补充协议。

高预算GT10组合从3.7064降至2.9287ms/query，Recall不变；完整HNSW为283.19QPS、Recall@100 90.3718%。span额外2505000字节辅助空间，加载阶段生成。最小适配/预取过滤等全部正负点与三轮波动保留，未按最好一轮选结论。主比较查询阶段57.619分钟，精确加载/身份核验成本见报告。

按用户之前的四集一致性范围，预锁相同组合在Yandex/Deep/SIFT/GIST完整10K/10K/10K/1K query、各四预算和NSG/hard/soft/GATE真实入口核验，计数包装真正转发Faiss batch4。另496000search/64配置，其它四集64配置的输出ID/距离bits/入口/逐query NDC全部与E99一致。完整成功与失败、距离bits/ID/NDC差异均保留；该阶段0正式QPS，不能宣称四集提速。

未训练、构图或生成GT，未打开新的held-out，没有生产替换或默认更改。修改前Git备份dba6986eb9baa645e9ad1231f9d112bb06550c5d，main/index保持。后续生产改造须结合跨集数值边界，补trace、特殊值与未知DC回退，再公平验证全部共享NSG方法；本轮不自动追加参数网格或部署。

[报告](../entry_method_exploration/20260916_faiss_nsg_comparison_v1/report.md) · [主协议](../entry_method_exploration/20260916_faiss_nsg_comparison_v1/protocol.md) · [兼容性补充](../entry_method_exploration/20260916_faiss_nsg_comparison_v1/compatibility/protocol.md) · [40点指标](../entry_method_exploration/20260916_faiss_nsg_comparison_v1/results/metrics.csv) · [控制收益](../entry_method_exploration/20260916_faiss_nsg_comparison_v1/results/paired_speedup.csv) · [兼容性分析](../entry_method_exploration/20260916_faiss_nsg_comparison_v1/compatibility/analysis.json)
