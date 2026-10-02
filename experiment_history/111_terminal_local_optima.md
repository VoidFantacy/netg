# 111｜E114搜索终点的局部最优性质

2026-09-20。**TERMINAL_LOCAL_OPTIMA_VERIFIED**。先从当前kernel的池维护/完整展开/游标终止推导：固定得分下，返回topK的出邻居不存在可严格改善topK得分的外部节点；K1返回点是局部最优。该性质依赖完整展开，无附加提前停止；不是当前NSG全局单调图的证明。

仅复用E107两集全部4096条曝光query、8方法、真实K1/L128返回。按query去重5059/4516个终点，扫描60877/129232条出邻接；全部非同向量边得分差由保守float64误差界确认为正，0违反。预定32query共818条边独立fsum一致，16原R1/失败点完全恢复。Web保留同向量不同GT1 ID的原评分。

八方法在Web79.6875%、Y90.6006%的query落到同一ID；默认失败中532/1011、202/384八方法都落到同一错误终点。默认相对固定单入口恢复/损伤query为278/103、144/78，对应旧R1净+4.2725/+1.6113pp。八种有限策略的特权联合可额外恢复269/133条，非部署、非全H上界。相同K1终点不推断K100/路径/NDC/wall相同。

0新NSG/ANN/GT/图/训练/QPS；分析4.843秒、外层4.971秒，RSS5.288GiB。初始内积计数字段重复计了缓存GT引用，单独核算说明更正，原源码/JSON保留且无重跑。首版图例重叠已保存并修为v2，数据不变。默认Web soft/Y hard、生产E99保持；整体任务继续至19:00。

[完整报告](../entry_method_exploration/20260920_until1900_theory_v1/stages/e114_terminal_peaks/report.md) · [理论](../entry_method_exploration/20260920_until1900_theory_v1/stages/e114_terminal_peaks/research.md) · [全部方法对](../entry_method_exploration/20260920_until1900_theory_v1/stages/e114_terminal_peaks/results/pairs.csv) · [计数澄清](../entry_method_exploration/20260920_until1900_theory_v1/stages/e114_terminal_peaks/reviews/distance_count_clarification.json)。
