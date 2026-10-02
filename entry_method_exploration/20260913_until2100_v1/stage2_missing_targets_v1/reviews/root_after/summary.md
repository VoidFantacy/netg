# ACSG 当前结果摘要

2026-09-13，E60固定动作支持和E61全fit遗漏目标画像均完成验收。当前仍没有可替换WebVid GT10-soft、Yandex GT10-hard的证据；今日整日目标未完成，未新增正式QPS。

E61由完整P-fit20K的原基线遗漏GT10成员重构画像，固定lambda0.5、每query总质量1，并加同query同遗漏数的随机目标对照。原A0/P字节恢复后六模型冻结，原NSG/H/IP/GT不变。missing的fit/cal/audit ΔRecall分别WebVid−0.1020/−0.3906/+0.0195 pp，Yandex−0.0260/−0.1465/+0.0684 pp。cal两集各净增3条GT10零命中，预锁选择均保留原P；audit小正值不回改选择。

作用已扩大到全部815/821画像，fit三入口变化8284/5602条，但fit自身净负，不能只归为迁移问题。原全命中群分别14/20条变为零命中，贡献140/200个损失；原零命中群也确有45/32条救回。m=0/10时该query自己归属未变，仍受共享画像/图影响。当前分组不能直接断言评分或邻接责任。

E60双集原J+辅助支持门0/40，约束全不动，停止同类局部动作扩大。WebVid9辅助正动作均train-J负；Yandex无辅助正动作。这是有限动作条件交集为空，不是整个画像空间不可能改善。

E61新增28484 NSG/133056 HNSW/6构图，原生含加载34.190s；132288集合评分、44096基线路由恢复、384三路parity及六画像独立聚合通过。两个阶段合计46314新NSG，均CPU15实际单线程串行、无新GT/梯度更新。

P-fit含旧train/monitor全部行，cal/audit已历史使用且今天再用，Fast30K曾拟合全router_train；均不称盲集。E34最终validation未进入本日训练或选择。昨日E53/E56局部信号、E57无稳定最终增量的结论及封存保留。下一步及晚间正式QPS–Recall/失败率窗口见[s-target](s-target.md)。

[E61完整报告](entry_method_exploration/20260913_until2100_v1/stage2_missing_targets_v1/report.md)、[E60报告](entry_method_exploration/20260913_until2100_v1/stage1_support_v1/report.md)、[历史50](experiment_history/50_missing_target_profiles.md)、[昨日最终报告](entry_method_exploration/20260912_until2000_v1/closeout/final_report.md)。
