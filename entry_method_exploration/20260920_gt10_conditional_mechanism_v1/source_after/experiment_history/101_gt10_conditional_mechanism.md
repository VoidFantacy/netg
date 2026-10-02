# 101｜E106 GT10条件分解、置换与条件聚合

2026-09-20，用户活动目标“按解释机制 → 推导改进 → 实验检验 走吧”授权按证据推进。本版已完成第一轮推导、候选、冻结检验与独立分析，结论为 **STOP_GROUPMEAN_CANDIDATE**。未找到稳定改进，尚未解释GT10全部收益；原Web soft/Yandex hard默认及生产E99保持。完整结果见[报告](../entry_method_exploration/20260920_gt10_conditional_mechanism_v1/report.md)。

GT10未归一化画像精确分成：GT1分组内共享的目标/query均值项B，加组内query与GT10归属的交叉矩D。在相同硬GT1组内置换完整归属行，严格保持每hub权重多重集、质量、平方和和ESS；这是对E27非匹配tail置换的机制补充。四个固定置换只作诊断，不是四份新独立query或有效条件独立p值。Web soft辅助仍按硬GT1分组，未保留query特定的GT1软概率。

由Eπ[vπ]=B推导唯一GroupMean候选，导出normalize(B)，不扫alpha或seed。它可能减少不稳定的组内细节，也可能删掉有效信号；没有无条件MSE/Recall保证。区别于E26的两单位画像插值、E80的目标条件化多画像聚类和E95的查询二阶矩构图。

fit20K三画像族恢复与分解通过，最大误差7.07e−14。D能量为条件置换期望的Web hard6.71倍、soft8.95倍、Y hard4.91倍，说明当前fit关联有结构。两集E105各4096已曝光query/原GT100用于固定机制开发，真实K1/K100、L128，Web14/Y8方法、exact对照与原默认ANN恢复；实际361856 NSG、16448原小图ANN，0新GT/图/梯度训练/正式QPS。各配置plain/count逐位一致，全部query独立集合评分、float64距离/排名抽查通过。

原GT10−四条件置换均值的R1/R100差值为Web hard +0.1282/−0.0188pp、soft 0/+0.0294pp、Y hard −0.1770/+0.0119pp。六项描述性95%区间全跨0，各项seed方向混合；不支持细粒度对应必然提供稳定Recall收益，也不证明细节完全无用或等效。

GroupMean相对匹配exact GT10的主结果：Web soft R1 75.3906%→75.3418%（−0.0488pp），R100 65.6191%→65.5969%（−0.0222pp）；Y hard R1 90.5762%→90.8203%（+0.2441pp），R100 83.7341%→83.7405%（+0.0063pp）。四项98.75%配对区间全跨0，两集预锁门均失败。零命中分别1008→1010、4→0、386→376、24→24，正面事件与负面均保留；Web hard辅助为−0.1709/+0.0198pp，不能据此重新选族。

原默认ANN的R1/R100为Web75.3174%/65.5408%，零命中1011/5；Y90.6250%/83.7917%，零命中384/24。GroupMean仍是exact路径，与当前ANN差值分别+0.0244/+0.0562pp、+0.1953/−0.0513pp，不能把路由差异计入画像收益或称部署比较。没有新QPS；候选主族graph NDC较匹配exact原画像增加Web0.3622%/Y0.0656%，不换算wall。

事后完整输出分析显示，候选改变Web soft75.59%/Y hard59.99%的入口，K1仅98/52查询命中变化；K100额外目标命中/损失为2136/2227、1793/1767，净收益相互抵消。这是已保存输出的描述，不改冻结门。GT10相对GT1 exact在本K/L的Recall差异同样混合，不能从稳定GT10增量的前提出发讲机制；既有相对NSG的完整前沿是另一个比较对象。

闭式fit约12.24秒，编译8.21秒，搜索编排179.98秒、四子进程170.65秒，主要评分7.08秒；搜索RSS最大9.92GiB，CPU15/线程1/串行。全部原结果保留，23旧资产SHA及两NSG stat核验，模型/源/数据冻结与图表检查收尾；这些时间不是在线QPS。原始文件及两次文档快照不覆盖。

停止GroupMean及追加alpha/seed/分组网格，不进入其条件ANN/完整wall阶段，无待运行任务。下一理论问题是明确比较对象、预算、相关性代理到联合搜索轨迹的成立条件，再决定是否存在实质不同的优化；不得把条件置换不显著写成已完整解释GT10，也不恢复E104/E105旧runner。

证据：[推导](../entry_method_exploration/20260920_gt10_conditional_mechanism_v1/research.md) · [协议](../entry_method_exploration/20260920_gt10_conditional_mechanism_v1/protocol.md) · [fit分解](../entry_method_exploration/20260920_gt10_conditional_mechanism_v1/results/fit_decomposition.json) · [主门](../entry_method_exploration/20260920_gt10_conditional_mechanism_v1/reviews/decision.json) · [全部44点](../entry_method_exploration/20260920_gt10_conditional_mechanism_v1/results/metrics.csv) · [状态](../entry_method_exploration/20260920_gt10_conditional_mechanism_v1/state.json)。
