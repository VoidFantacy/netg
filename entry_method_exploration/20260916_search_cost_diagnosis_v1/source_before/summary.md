# ACSG 当前结果摘要

E97 于2026-09-16完成：WebVid/Yandex/Deep/BIGANN-SIFT/GIST，排除LAION；Recall@1/100共800点、2400次单线程端到端计时，四张总图已实际检查，冻结身份核验通过。[详细分析](entry_method_exploration/20260915_gate_l2_r1_r100_v1/analysis.md)、[完整方法与成本](entry_method_exploration/20260915_gate_l2_r1_r100_v1/report.md)、[Recall@1图](entry_method_exploration/20260915_gate_l2_r1_r100_v1/figures/recall_qps_k1.png)、[Recall@100图](entry_method_exploration/20260915_gate_l2_r1_r100_v1/figures/recall_qps_k100.png)。

本轮没有统一赢家。WebVid在90% Recall@1门槛下hard为352.5 QPS/90.73%，NSG为280.9/90.65%；K100同门槛则完整HNSW为283.0/90.3718%，soft为239.4/90.6868%。Yandex在95% Recall@1门槛下hard为1127.5/95.02%，soft为906.1/95.77%；99%门槛的反向差异只由L1250上1个query命中差触发，不作普遍优势。Deep/SIFT的hard/soft曲线非常接近；GIST的K100以完整HNSW更有竞争力，K1高召回需保留NSG/GT10。GATE正负冲突归零并重训后，仍未显示跨五集稳定优于GT10。hard继续作预先指定主线、固定soft辅助，Web软/Y硬旧默认不变。

正式阶段15.826小时，07:09结束；已记录离线阶段4.869小时。三次QPS最大/最小相对范围中位数0.441%，最大15.401%，微小速度差不作强结论。保留[Yandex输入修正](experiment_history/90a_yandex_test_prefix_fix.md)及约70分钟等待中断，等待不算计算成本；GIST下载校验缺失、Web/Y历史公开测试曝光与新SIFT来源边界均写入分析。

2026-09-15 GATE后续检查完成：按用户接受合理适配的标准，核心流程成立，模型/导出/源码和保存计时核验通过；确认沿用release的正负标签存在交集，实际triplet中占0.25%–0.40%，后继应排除交集再训练。全部子图触及1000节点上限，影响未量化。无需因论文/代码不一致推翻E96，但其结果仅对应当前受限适配，不能据此否定完整GATE。[详细审查](entry_method_exploration/20260915_gate_reproduction_audit_v1/report.md) · [记录89](experiment_history/89_gate_reproduction_audit.md)。

上述 GATE 审查阶段（E97执行前）为0新训练/ANN/图/GT/QPS，当时未启动Deep/SIFT/GIST；建议GT10-hard统一主线、soft-t1辅助，不宣称已测最优。审查发现的旧配置训练/测试同路径、SIFT实际11164866行、E96仅IP/K10等接入问题由E97独立版本处理。后续新开发与正式比较只测Recall@1、Recall@100，旧Recall@10与Web软/Y硬默认保持历史身份。

2026-09-15 E96已完成：WebVid/Yandex/LAION完整底库、各10000公开query，GATE（release10适配）、当前GT10、NSG、全量HNSW，16预算至1500；192点576次单线程wall及逐query评分、配对、身份/线程审计通过。正式阶段4.758小时，图表已检查，原始结果全部保留。[报告与图](entry_method_exploration/20260914_gate_new_ood_v1/report.md) · [完整CSV](entry_method_exploration/20260914_gate_new_ood_v1/results/metrics.csv) · [复盘88](experiment_history/88_gate_three_dataset_comparison.md)。

Web/Y上，GT10在全部16预算均有高于GATE的Recall和平均QPS；LAION高预算有取舍：L1500 GATE96.287%/145.86QPS/0.03%零命中，GT10 96.154%/148.94QPS/0.06%。全量HNSW与GT10也有前沿交叉，不能称任何方法全条件最快。Web/Y最大预算的GT10分别93.506%/192.05QPS/0.04%、99.007%/206.44QPS/0.13%。主失败定义为Recall@10=0，GT1漏失另报。默认Web软/Y硬保持，LAION本轮cal选择soft-t1；没有按public结果追加训练。

最终GATE训练639.97/751.71/1331.11秒，标签151.23/200.82/230.21秒；历史GT/NSG/继承画像成本未知，不能当零。LAION特征已含HBKM，不重复计费。旧采样错误、环境重启和存储保护恢复均已隔离记录；所有正式点在同一boot一次完成。按用户授权删除原netg.tar.gz后，LAION索引已校验恢复项目目录；原base/NSG/GT/模型不变。Web/LAION公开query同源，结论不是三套全新盲测。E95停止结论作为历史边界保留。

E95查询统计构图的四组开发门均失败，因此停止当时的固定H画像/小图增强分支；这个判断不等于全部离线入口学习或RL无解。[E95复盘](experiment_history/87_query_moment_graph_and_branch_stop.md)。E94为该旧分支的五L五轮最终矩阵，与E96的三数据集16预算比较分开保存。[E94复盘](experiment_history/83_frozen_final_comparison.md)。这些旧分支没有待恢复的实验进程；后继E97现也已完成，当前无待恢复的实验。
