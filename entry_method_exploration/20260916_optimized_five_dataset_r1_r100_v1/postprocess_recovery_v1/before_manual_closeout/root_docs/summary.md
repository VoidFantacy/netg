# ACSG 当前结果摘要

E103于2026-09-17T08:18:23.251697+08:00完成统一优化后五集完整重测：800配置、2400轮单线程plain、32800000次真实搜索；NSG/hard/soft/GATE同一span+batch4，HNSW同轮重新计时。全部返回/入口/逐query NDC对齐E97，Recall独立重算。90/95/99%门槛中25个组合至少一方法达到，GT10均值最快22个、进入三轮范围重叠组24个；范围重叠不是显著性判断。图和分析已自动生成，人工图像检查待完成。无训练/新图/GT/默认变更。 [报告与新图](entry_method_exploration/20260916_optimized_five_dataset_r1_r100_v1/report.md) · [复盘96](experiment_history/96_optimized_five_dataset_retest.md)。

E102于2026-09-16完成统一优化公平比较：NSG、GT10-hard/soft、GATE均使用相同span+batch4，WebVid四预算各新旧内核及同轮HNSW共36配置108plain。NSG自身四点平均QPS变化+18.58%至+27.28%；K100/L1250从252.11变为320.90QPS，Recall@100保持90.4456%。同内核soft为324.95QPS/90.6868%，GATE为319.69QPS/90.6317%；HNSW为271.54QPS/90.3718%。 同内核低预算K1/L96和K100/L100，GT10-soft相对NSG分别增加4.73/1.64pp Recall与11.68%/11.28%平均QPS；高预算速度差缩小，结合三轮范围判断，不支持“GT10无效”或“全面第一”。 其它四集64配置的ID/距离bits/入口/逐query NDC全部一致，合计2296000次真实搜索。公共内核加速与入口方法收益分开报告，四点不能代表完整前沿或其它四集新QPS；生产/默认仍E99，修改前备份8afd61cd。[报告与图](entry_method_exploration/20260916_shared_span_batch4_v1/report.md) · [复盘95](experiment_history/95_shared_span_batch4_comparison.md)。

E101于2026-09-16完成内置Faiss1.9.0同图比较：WebVid四点、十版本、120轮plain/2000000search；GT10的span+batch4组合相对当前E99四点QPS变化+13.10%至+26.56%，各GT10控制返回和NDC相同。高预算K100/L1250组合341.45QPS、Recall@100 90.6868%，当前GT10 269.80QPS；原生Faiss 230.52QPS/90.4819%。另做80000次真实batch4计数核验及496000次四集一致性回归，其它四集64配置的输出ID/距离bits/入口/逐query NDC全部与E99一致。 [报告与图](entry_method_exploration/20260916_faiss_nsg_comparison_v1/report.md) · [复盘94](experiment_history/94_faiss_nsg_comparison.md)。 本轮是独立研究候选，生产源码/默认仍E99、Web软/Y硬；没有重训或新构图，不声称完整前沿或四集新QPS。修改前备份`dba6986e`。

E100于2026-09-16完成E99优化后的剩余成本诊断：WebVid K100/L1250、GT10-soft/完整HNSW共80000次诊断search，输出和逐query NDC与E99一致；没有新正式QPS或生产改动。NSG每query检查80398个邻接槽，71.82%为空槽，检查量约HNSW的3.095倍；新采样距离区域63.94%、图循环/visited/预取附近26.98%，路由仅0.50%。全图空槽均为连续尾部，支持保序span优化研究，但尚未测其收益。项目已用Faiss建图/存储/距离组件，在线是项目多入口改造；历史“NSG”是共享内核的单入口控制，尚缺原生Faiss搜索对照。[报告与两张诊断图](entry_method_exploration/20260916_residual_cost_research_v1/report.md) · [复盘93](experiment_history/93_residual_search_cost_research.md)。默认和E99正式结果保持；研究前E99已备份到`7d09367e`，诊断调度5.185分钟，无训练/新构图。

E99于2026-09-16完成共享NSG实现优化：WebVid四个预算、四种NSG入口方法的新旧对照，QPS变化+10.51%至+13.53%；五集100个组合的返回ID/距离bits/入口和逐query NDC均与E97一致。WebVid K100/L1250优化后soft为268.9 QPS、Recall@100 90.6868%；同轮完整HNSW为282.5 QPS、90.3718%。 [报告](entry_method_exploration/20260916_nsg_search_optimization_v1/report.md) · [Recall–QPS图](entry_method_exploration/20260916_nsg_search_optimization_v1/figures/webvid_recall_qps.png) · [复盘92](experiment_history/92_nsg_search_optimization.md)。 生产源码已优化、独立优化库已验证，原构建库保持；入口模型默认不变。其他四集仅一致性回归，无新QPS结论。本轮2,296,000次真实查询、108轮单线程plain，无训练/新构图；修改前6115个文件已Git备份到`2739b09a`。

E98于2026-09-16完成WebVid GT10-soft实现诊断：路由仅0.47% wall；距离及访存等待约77.3% CPU样本。固定输出与逐query NDC后，预取、有效候选池、组合相对匹配基线分别提升7.81%/0.95%/13.15% QPS（候选池单独变化在波动范围内）；组合253.2 QPS，原HNSW参考267.4。550000次search/36轮plain，无训练或新构图；仅K100/L1250的局部优化证据，主源码和默认不变。 [诊断报告](entry_method_exploration/20260916_search_cost_diagnosis_v1/report.md) · [诊断图](entry_method_exploration/20260916_search_cost_diagnosis_v1/figures/cost_diagnosis.png)。单独候选池控制不构成稳定加速结论；后续正式采用应公平重测所有共享NSG内核的方法。

E97 于2026-09-16完成：WebVid/Yandex/Deep/BIGANN-SIFT/GIST，排除LAION；Recall@1/100共800点、2400次单线程端到端计时，四张总图已实际检查，冻结身份核验通过。[详细分析](entry_method_exploration/20260915_gate_l2_r1_r100_v1/analysis.md)、[完整方法与成本](entry_method_exploration/20260915_gate_l2_r1_r100_v1/report.md)、[Recall@1图](entry_method_exploration/20260915_gate_l2_r1_r100_v1/figures/recall_qps_k1.png)、[Recall@100图](entry_method_exploration/20260915_gate_l2_r1_r100_v1/figures/recall_qps_k100.png)。

本轮没有统一赢家。WebVid在90% Recall@1门槛下hard为352.5 QPS/90.73%，NSG为280.9/90.65%；K100同门槛则完整HNSW为283.0/90.3718%，soft为239.4/90.6868%。Yandex在95% Recall@1门槛下hard为1127.5/95.02%，soft为906.1/95.77%；99%门槛的反向差异只由L1250上1个query命中差触发，不作普遍优势。Deep/SIFT的hard/soft曲线非常接近；GIST的K100以完整HNSW更有竞争力，K1高召回需保留NSG/GT10。GATE正负冲突归零并重训后，仍未显示跨五集稳定优于GT10。hard继续作预先指定主线、固定soft辅助，Web软/Y硬旧默认不变。

正式阶段15.826小时，07:09结束；已记录离线阶段4.869小时。三次QPS最大/最小相对范围中位数0.441%，最大15.401%，微小速度差不作强结论。保留[Yandex输入修正](experiment_history/90a_yandex_test_prefix_fix.md)及约70分钟等待中断，等待不算计算成本；GIST下载校验缺失、Web/Y历史公开测试曝光与新SIFT来源边界均写入分析。

2026-09-15 GATE后续检查完成：按用户接受合理适配的标准，核心流程成立，模型/导出/源码和保存计时核验通过；确认沿用release的正负标签存在交集，实际triplet中占0.25%–0.40%，后继应排除交集再训练。全部子图触及1000节点上限，影响未量化。无需因论文/代码不一致推翻E96，但其结果仅对应当前受限适配，不能据此否定完整GATE。[详细审查](entry_method_exploration/20260915_gate_reproduction_audit_v1/report.md) · [记录89](experiment_history/89_gate_reproduction_audit.md)。

上述 GATE 审查阶段（E97执行前）为0新训练/ANN/图/GT/QPS，当时未启动Deep/SIFT/GIST；建议GT10-hard统一主线、soft-t1辅助，不宣称已测最优。审查发现的旧配置训练/测试同路径、SIFT实际11164866行、E96仅IP/K10等接入问题由E97独立版本处理。后续新开发与正式比较只测Recall@1、Recall@100，旧Recall@10与Web软/Y硬默认保持历史身份。

2026-09-15 E96已完成：WebVid/Yandex/LAION完整底库、各10000公开query，GATE（release10适配）、当前GT10、NSG、全量HNSW，16预算至1500；192点576次单线程wall及逐query评分、配对、身份/线程审计通过。正式阶段4.758小时，图表已检查，原始结果全部保留。[报告与图](entry_method_exploration/20260914_gate_new_ood_v1/report.md) · [完整CSV](entry_method_exploration/20260914_gate_new_ood_v1/results/metrics.csv) · [复盘88](experiment_history/88_gate_three_dataset_comparison.md)。

Web/Y上，GT10在全部16预算均有高于GATE的Recall和平均QPS；LAION高预算有取舍：L1500 GATE96.287%/145.86QPS/0.03%零命中，GT10 96.154%/148.94QPS/0.06%。全量HNSW与GT10也有前沿交叉，不能称任何方法全条件最快。Web/Y最大预算的GT10分别93.506%/192.05QPS/0.04%、99.007%/206.44QPS/0.13%。主失败定义为Recall@10=0，GT1漏失另报。默认Web软/Y硬保持，LAION本轮cal选择soft-t1；没有按public结果追加训练。

最终GATE训练639.97/751.71/1331.11秒，标签151.23/200.82/230.21秒；历史GT/NSG/继承画像成本未知，不能当零。LAION特征已含HBKM，不重复计费。旧采样错误、环境重启和存储保护恢复均已隔离记录；所有正式点在同一boot一次完成。按用户授权删除原netg.tar.gz后，LAION索引已校验恢复项目目录；原base/NSG/GT/模型不变。Web/LAION公开query同源，结论不是三套全新盲测。E95停止结论作为历史边界保留。

E95查询统计构图的四组开发门均失败，因此停止当时的固定H画像/小图增强分支；这个判断不等于全部离线入口学习或RL无解。[E95复盘](experiment_history/87_query_moment_graph_and_branch_stop.md)。E94为该旧分支的五L五轮最终矩阵，与E96的三数据集16预算比较分开保存。[E94复盘](experiment_history/83_frozen_final_comparison.md)。这些旧分支没有待恢复的实验进程；后继E97现也已完成，当前无待恢复的实验。
