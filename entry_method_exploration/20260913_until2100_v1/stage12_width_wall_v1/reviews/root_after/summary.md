# ACSG 当前结果摘要

2026-09-13，第4串行会话完成E69–E71并进入安全交接。本次多画像加宽没有形成稳定整体QPS–Recall改善，原默认保持；局部质量正信号与严重损伤同时保留。整日21:00目标未完成，E34晚间最终validation尚待冻结对照。

E71同批65点、325轮完整单线程wall包含原NSG、Fast30K、GT10-hard、Web匹配soft/P10及P30/mode10/mode30。相对匹配P10，按L64/128/256/400/800：

| 数据 | mode30 ΔRecall pp | QPS中位变化% | 零命中净新增 |
|---|---|---|---|
| WebVid | +.3174/+.0977/+.1611/+.3369/+.1416 | −4.82/−3.42/−1.41/−1.78/−.84 | −7/+1/−2/−3/−2 |
| Yandex | +.4004/+.1123/+.0098/−.0342/+.0635 | −3.76/−2.39/−1.05/−1.13/−.32 | −8/−3/0/0/+1 |

Web相对mode10五L质量正、QPS中位均负；相对P30的L128质量负且多3失败。Y相对mode10四L Recall负且L256/800各多1失败。相对P10的五轮QPS交叉范围Web2点/Y3点全负，其余跨0；这不是置信区间。共同Recall的描述性log-QPS插值Web两负一正、Y三个全负，不能写成实测同Recall提速或最终泛化收益。

严格零GT10命中转换共84个不同源query、149跨L事件、420完整五L格，全量CSV及五类图已保存。Web3524全五L从0变7，Y2769从全0变8/9/10/10/10；Web2618从3/5/5/5/5变0/0/0/0/5，Y3645从全10变全0。救回/新增、GT成员得失、逐query净命中正负部不混用。

E69固定历史aux7952/L128，精确mode相对精确P：Web净−109命中/失败+7、两半−86/−23；Y净+132/失败−10、两半+32/+100。相对approx P为Web+85、Y+97。精确P本身Web改善194而Y损失35，完整画像排序不保证NSG效用。38942新NSG，31808逻辑精确结果中28102旧复用、3535唯一补缺、171别名；0HNSW/构图/QPS。

E70固定图ef10/30控制：Web mode30对P10净+6但失败+5、对P30净−100，未过门；Y对P10+77/失败−7、对P30+89/失败−7，固定两半均非负，过有限辅助质量接续门。route NDC相对P10 Web+87.32%/Y+111.69%，total+5.26%/+3.93%；194304 NSG/193920 HNSW/0构图。这些门与E66原门保持，E71历史开发2048不回写原门。

E71新增932880 NSG/788480 HNSW/0新构图训练GT，原生两job1324.923秒，325轮纯wall合计930.101秒；55 plain加55 count源图加载，0图副本。133120集合/mask、全plain/count、1040原kernel、55源图、325wall顺序和旧返回回归通过；两job实际CPU15/线程1，terminal exit0后分析。完整路由+原NSG+输出在wall内，GT/count/hash/build/load在外，分项wall未另测有明确null原因。

本会话合计1166126新NSG/982400 HNSW、0新构图/训练/GT；今日累计165个历史开发性能点、825轮wall，E65/E67/E71不同批不能拼曲线。P-fit包含旧train/monitor，cal/audit/aux均历史暴露，辅助选择反馈计训练；本轮2048是已观察aux子集。E34最终validation及held-out今日仍未使用。

[E71完整报告](entry_method_exploration/20260913_until2100_v1/stage12_width_wall_v1/report.md) · [判断](entry_method_exploration/20260913_until2100_v1/stage12_width_wall_v1/assessment.md) · [E70](entry_method_exploration/20260913_until2100_v1/stage11_width_control_v1/report.md) · [E69](entry_method_exploration/20260913_until2100_v1/stage10_exact_triple_utility_v1/report.md) · [下一阶段](s-target.md)。
