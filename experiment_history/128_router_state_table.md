# 128 E121 原路由上层状态表

2026-09-22，用户授权实际改进并研究至22:00。独立版本`20260922_until2200_improvement_v1/stages/e121_router_state_table_v1`，状态`STOP_ROUTER_STATE_TABLE_V1`，总体目标继续。

原GT10上层下降结束节点z提供最多52个离散状态；只观察z，不改变图/画像或主NSG。动作扩至全H单入口加默认，区别于E117原top3四动作，也不运行E118/E119的在线全H评分。先核原/观察版heap ID/距离bits、NDC及历史三入口，16384次路由全部一致。

E118 fit4096历史曝光query，四折3072拟合/1024外折。按状态平均真实Recall差或成本代理u选动作；同监督全局固定和保状态计数的置换控制，所有规则/角色先冻结。每K独立，不根据结果调阈值/状态/模型。u使用旧graph-only时间，不是完整QPS。

StateCost ΔR1/R100：Web−1.0742/−0.3154pp，Y−0.3418/−0.2839pp；等K U×100为−1.1668/−1.1385，98.75%描述区间均负。StateRecall也负。真实状态优于打乱Cost（两集+0.5192/+0.5358 U×100，合并区间正），但低于默认/全局固定，主信息门失败。训练U正而外折负，多数状态四折选择动作不一致；状态相关性不足以保证部署净收益。

0新NSG/GT/图/QPS/网络梯度训练；有96份条件表/全局均值拟合、16份默认无拟合评估。原记录112是全部方法×折×K评估数，非112份学习表。拟合/统计6.16秒、独立逐项核验186.63秒；114688动作值、402消费文件身份审查通过。同会话独立实现，不是独立人员审查。

停止本上层状态表，不扩特征/格子/模型续调，也不因未过门追加新测试或目标预算全H标签。Web soft/Y hard、生产E99保持；后续先寻找实质不同的结构依据，不将本结果泛化为所有入口信息无效。

[报告](../entry_method_exploration/20260922_until2200_improvement_v1/stages/e121_router_state_table_v1/report.md) · [协议](../entry_method_exploration/20260922_until2200_improvement_v1/stages/e121_router_state_table_v1/protocol.md) · [理论](../entry_method_exploration/20260922_until2200_improvement_v1/stages/e121_router_state_table_v1/theory.md) · [门](../entry_method_exploration/20260922_until2200_improvement_v1/stages/e121_router_state_table_v1/results/gate.json) · [审计](../entry_method_exploration/20260922_until2200_improvement_v1/stages/e121_router_state_table_v1/reviews/independent_numeric_audit.json)
