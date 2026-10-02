# 101｜E106 GT10条件分解、置换与条件聚合

2026-09-20，用户活动目标“按解释机制 → 推导改进 → 实验检验 走吧”授权按证据推进。本版独立执行，旧E105与GT10默认保持；当前完整机制搜索进行中，结果分析尚未完成。

GT10未归一化画像精确分成：GT1分组内共享的目标/query均值项B，加组内query与GT10归属的交叉矩D。在相同硬GT1组内置换完整归属行，严格保持每hub权重多重集、质量、平方和和ESS；这是对E27非匹配tail置换的机制补充。四个固定置换只作诊断，不是四份新独立query或有效条件独立p值。Web soft辅助仍按硬GT1分组，未保留query特定的GT1软概率。

由Eπ[vπ]=B推导唯一GroupMean候选，导出normalize(B)，不扫alpha或seed。它可能减少不稳定的组内细节，也可能删掉有效信号；没有无条件MSE/Recall保证。区别于E26的两单位画像插值、E80的目标条件化多画像聚类和E95的查询二阶矩构图。

fit20K三画像族恢复与分解已通过。组内D平方范数约为条件置换期望的5–9倍，不能直接视作噪声；是否帮助真实搜索仍待本版结果。两集E105各4096已曝光query/原GT100用于固定机制开发，真实K1/K100、L128，Web14/Y8方法、exact对照与原默认ANN恢复，plain/count一致；预定361856 NSG，0新GT/图/梯度训练，未测正式QPS。

候选仅在Web soft/Y hard两集都达到预锁exact质量门后进入另立实际ANN/独立完整wall验证；失败停止GroupMean，不追加收缩参数。主机制保留全部seed/K/正负事件，单L不作性能GO。

证据：[推导](../entry_method_exploration/20260920_gt10_conditional_mechanism_v1/research.md) · [协议](../entry_method_exploration/20260920_gt10_conditional_mechanism_v1/protocol.md) · [fit分解](../entry_method_exploration/20260920_gt10_conditional_mechanism_v1/results/fit_decomposition.json) · [状态](../entry_method_exploration/20260920_gt10_conditional_mechanism_v1/state.json)。
