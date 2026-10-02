# ACSG 当前结果摘要

2026-09-13第11串行会话E92–E94完成：新组合修复与冻结最终矩阵已实测，**尚未得到稳定优于现有默认的方法**，默认保持；本会话结束不等于整日21:00目标完成。

顺序均L64/128/256/400/800，Recall为百分点，失败为零GT10命中净新增。

| 最终同批2000对比 | Recall变化 pp | 失败净新增 |
|---|---|---|
| Web组合 / compact | +.095/+.270/+.080/+.085/+.030 | −3/−4/−1/−1/−1 |
| Web组合 / 匹配GT10-soft P | −.340/−.385/−.410/−.125/−.105 | −7/−1/+4/+2/+1 |
| Y compact / GT10-hard P | +.090/+.070/+.120/−.030/−.125 | +3/−2/−4/−1/+2 |

Web组合修复的局部质量收益在最终批仍存在，尚未补齐compact相对P的损失。组合/compact及Y/P五点QPS交叉范围均跨零；组合/P L128略负，其余跨零。同Recall描述性插值组合/compact +1.08/+1.34/+1.51%、Y/P +.15/+.77/+1.19%，范围均跨零；组合/P −3.53/−4.02/−2.57%，范围均负。插值非新增等Recall测量，不作GO。

E92仅将冻结补边和父画像恢复组合，Web线上仍1771画像slot/815真实入口，Y compact为2067/821，一次小HNSW7slot去重3入口+原NSG/rawIP。E92开发对compact+97命中/失败−10，但对P后半−7/失败+1，原门FAIL保持。Y恢复零更新别名不作为新方法。

E93实际核对77目录、独立评分41项/326032返回：Web无过门新方法，best_all=P、best_new=E92反证；Y两角色compact。模型/规则/ties先冻，再开E34历史validation2000；最终反馈未回流，held-out未开。P-fit含旧train/monitor，aux/cal/audit历史使用，E90前3976动作训练；所有选择反馈算训练，不称盲验证。

E94 50点250wall、700800NSG/560000HNSW，native操作994.213s与纯wall695.047s分开。8源图/40plain+40count加载，0新拟合/普通构图/GT。100000集合评分、70000原基线七字段E34回归、800原kernel/七slot/跨L身份均通过。401独立失败query、346状态变化；812query×L事件4230单元与完整五L10730单元分表，GT/入口/返回全保留。

本会话累计781760NSG/640800HNSW、1组合图安装，四native任务全部串行CPU15/实际及库1线程terminal0。继承离线训练/GT总成本缺项仍未知。全日累计6854176NSG/17820080HNSW/360普通build；旧四开发QPS批不拼本次最终曲线。

[完整报告与图](entry_method_exploration/20260913_until2100_v1/stage35_final_comparison_v1/report.md) · [全部50原点](entry_method_exploration/20260913_until2100_v1/stage35_final_comparison_v1/analysis_v1/points.csv) · [401失败query完整五L表](entry_method_exploration/20260913_until2100_v1/stage35_final_comparison_v1/supplement_v1/failed_queries_all_L.csv) · [E92局部组合](entry_method_exploration/20260913_until2100_v1/stage33_composed_repair_v1/report.md) · [下一步](s-target.md)。

第12会话报告补充完成：独立复算50,000条既有返回和15组成对成员增损/失败，全部恢复原值，0新增训练/ANN/QPS。Web L128组合对compact新增66/丢失12 GT成员，仍对P新增274/丢失351；局部修复未成为整体胜出。[简短汇报](entry_method_exploration/20260913_until2100_v1/session12_report_v1/report.md)。实际文档收尾超过20:00会话边界，整日目标保持未完成。
