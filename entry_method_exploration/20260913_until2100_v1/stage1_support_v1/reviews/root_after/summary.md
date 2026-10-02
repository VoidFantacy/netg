# ACSG 当前结果摘要

2026-09-13，今日独立campaign首阶段E60已完成并验收。固定E53每集40状态及原三个确定动作，在历史cal1024检查辅助支持、audit1024记录迁移；双集均0/40，未过各10/40门，约束全部选择不动。停止相同局部动作的连续预算扩张。

WebVid120动作中辅助命中全空108、迁移全空93；9个辅助净正动作全部不满足原train-J不降（7个损失训练命中，2个命中不变但成本/漂移J略负）。Yandex辅助全空114/120、迁移120/120，无辅助净正动作。不能把WebVid0/40说成完全没有辅助正值，也不能据有限动作声称全画像空间不可兼容。

原J规则在这些固定状态的迁移增益/损伤命中合计WebVid8/5、Yandex0/0；约束全为0/0，是不动造成，不能称成功风险控制或连续模型提升。实际17830新NSG、660640 HNSW、322构图，双集原生阶段含加载63.127s；659488输出集合评分、完整缓存/画像/拓扑/576三路parity通过。CPU15实际单线程，0新GT/optimizer/正式QPS。

数据角色已逐行核验：P-fit20K含旧train4096和monitor1024全部行；cal、audit均历史使用，Fast30K还曾拟合全部router_train。辅助用于动作决定即计选择训练信息，旧audit本轮再用后仍不是盲集。E34最终validation输入和响应未进入本阶段。

默认仍WebVid GT10-soft、Yandex GT10-hard。昨日E53/E56的离线局部信号保留，E57最终45点225轮未稳健超过匹配GT10；新训练收益不得写成最终方法进步。今天后续方向与最后一小时正式QPS–Recall/零命中失败率窗口见[s-target.md](s-target.md)，整日目标未完成。

[E60报告与图](entry_method_exploration/20260913_until2100_v1/stage1_support_v1/report.md)、[数据暴露审计](entry_method_exploration/20260913_until2100_v1/stage1_support_v1/reviews/data_exposure_audit.json)、[历史49](experiment_history/49_fixed_action_support.md)、[昨日封存报告](entry_method_exploration/20260912_until2000_v1/closeout/final_report.md)。
