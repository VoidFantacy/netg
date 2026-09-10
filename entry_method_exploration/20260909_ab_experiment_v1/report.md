# A+B最终实验结果入口

**用户指定的五点单线程探索已完成：当前候选没有显示出相对Fast的整体改进。**

完整NSG/Fast/A+B的Recall@10、QPS、失败数量/率以及逐点相对变化见[最终报告](exploration_5point_v1/report.md)。

两个数据集各2000条validation，L64/128/256/400/800，一个seed、一个固定入口模型，每点一次预热和一次端到端计时。五L逐query入口完全相同。

原三seed/双split/多消融完整矩阵已按用户要求取消，其未完成部分不计作最终证据；所有原产物保留。详细执行和修正见[E22复盘](../../experiment_history/11_ab_fixed_slot_exploration.md)。
