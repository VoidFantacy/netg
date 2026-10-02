# ACSG 当前结果摘要

2026-09-22晚间。**原默认保持；ApproxTarget10保留为低成本候选，不再因一个区间未过而直接停止探索。** Web默认GT10-soft-t1，Yandex默认GT10-hard，生产主搜索E99。

## 最新实际测试

用户要求的E125冻结模型Web单组复测已于21:21前完成核验。4096条新源query、K1/L1000、CPU15实际1线程、三次完整wall：

| 方法 | Recall@1 | 命中 | 完整QPS |
|---|---:|---:|---:|
| GT10-soft-t1 | 90.795898% | 3719/4096 | 419.559 |
| ApproxTarget10 | 90.649414% | 3713/4096 | 419.121 |

候选救回6/损伤12，差−0.146484pp，95%配对bootstrap描述区间[−0.341797,+0.048828]；QPS−0.104439%，三轮范围重叠。旧批同点为−0.097656pp、3救回/7损伤；两批均小幅为负，不能说无损或线上更快，但仍可评估费用与质量取舍。新批与登记split、旧E105整个20K窗口及原画像拟合输入字节互斥，源顺序窗口不是全源随机/语义独立。全返回、原E99、线程/身份、精确GT和区间独立复核通过。[记录138](experiment_history/138_e125_web_fresh_check_and_policy.md) · [复测报告](entry_method_exploration/20260922_until2200_improvement_v1/stages/e125_web_fresh_check_v1/report.md)。

## 近似监督的价值与成本口径

原E125两集12点、三次完整wall中，所有召回均值损失不超过0.10pp，QPS差−0.2161%至+0.0893%；只有Web主点旧98.75%非劣下界没有过预定−0.25pp。原STOP门/结果保留。现在按用户修订策略，将探索与默认替换分开，状态为**RETAIN_LOW_COST_CANDIDATE**。单点区间未过不一票否决；保留实际损失及不确定性，不把放宽探索资格写成统计通过。[策略](entry_method_exploration/20260922_until2200_improvement_v1/research_decision_policy.md)。

20K画像近似目标完整作业Web64.591秒、Y28.040秒；对应exact20K搜索312.862/1417.293秒。近似单线程、exact受8个CPU限制，阶段/资源不同，不称同资源加速比。QGT5K精确监督仍保留。GT-inclusive当前默认核心构建合计403.997/1780.232秒，其中exact GT占97.94%/99.43%；不含公共底图、嵌入/下载/历史选型。[成本135](experiment_history/135_gt10_gt_inclusive_build_cost.md) · [原试验137](experiment_history/137_approximate_target_profile_cost_pilot.md)。

补充费用范围：Web继承的soft温度源于原20K精确GT1，Y-hard无该依赖。当前是固定既有H/参数下的近似标签费用改进，尚非新数据集从零构建验证；新复测有效性不变。[依赖与纠偏方向](experiment_history/139_approximate_supervision_scope.md)。

## 本轮机制结论

GT10的优势有具体证据：真实GT选H、十目标形成较稳定且保留语义对应的query方向、静态画像和廉价小图推理。固定20K两半下，Web GT1/hard10/soft10的画像夹角中位24.5°/12.1°/8.5°，Y GT1/hard10为27.2°/16.5°；去共同方向后仍保持，真实对应跨半亲和胜置换。闭式亲和最优与稳定性不等于Recall最优。[记录134](experiment_history/134_gt10_profile_direction_stability.md)。

E123真实目标区域服务策略有正值；E124预测更准仍未形成净收益，原因需要区分代理偏差与学生预测误差，不能仅归为模型弱。目标预算固定256-query全H诊断仍有余量，Web/Y K100 single+默认oracle为+1.586/+2.641pp，但只是历史query事后上限，不是可部署收益。[记录133](experiment_history/133_privileged_surrogate_decision_geometry.md) · [记录136](experiment_history/136_target_budget_fullH_opportunity.md)。

只读训练缓存已补核算：随机残差校正要在合力归一化的向量总和MSE上优于直接近似，Web/Y解析临界m约3269/8517，占20K的16.34%/42.58%。残差方差虽小，直接近似偏差也已部分抵消，少量补标不必更好。没有据此训练模型或选择m；这不是Recall门或否定混合监督，只用于评估投入。 [记录140](experiment_history/140_approximate_target_residual_variance.md)。

已有入口/返回的补充只读对齐显示：新Web1150/4096条换三入口集合，只有21条最终K1返回ID改变；当前预算下路由改变不等于搜索增益，不说明轨迹相同或全H无余量。[记录138](experiment_history/138_e125_web_fresh_check_and_policy.md)。

## 完整性能证据的位置

E103仍是最新完整五数据集重测，E118是最近宽预算候选比较；今晚E125是双集三预算及Web单点补测，不冒充五集新前沿。E103最快已测R90达标点上，Web K1/K100 QPS520.79/340.46（对NSG+24.99%/+0.79%），Y为2406.16/1241.64（+9.63%/+6.96%）；实际Recall分别90.7500%/90.6868%、91.0500%/90.9805%，方法L/Recall并非完全一致，非同Recall显著性结论。GIST收益基本持平，不能称所有数据全面占优。

当前无默认替换、无未完成性能作业或追加到通过的实验队列；余下交付审查不产生新性能数据。下一步见[s-target.md](s-target.md)。本轮[总报告](entry_method_exploration/20260922_until2200_improvement_v1/report.md) · [PDF](entry_method_exploration/20260922_until2200_improvement_v1/GT10理论与性能改进研究.pdf) · [理论](entry_method_exploration/20260922_until2200_improvement_v1/theory.md) · [改进方向](entry_method_exploration/20260922_until2200_improvement_v1/directions.md)。此前流水摘要已完整保存在[原文快照](entry_method_exploration/20260922_until2200_improvement_v1/reviews/root_docs_before_closeout/summary.md)，历史事实由[s-experiment.md](s-experiment.md)与详细卡片索引维护。
