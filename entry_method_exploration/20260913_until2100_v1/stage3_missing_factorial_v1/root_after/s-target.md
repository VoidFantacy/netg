# ACSG 下一阶段目标与接续

2026-09-13，今天21:00前持续改进现有方法，并完成冻结候选的同机单线程QPS–Recall/失败查询图表。首个独立会话完成E60支持检查、E61遗漏成员画像、E62评分/拓扑四格，均无开发门新赢家；整日目标未完成。

1. 停止同类局部行随机动作扩大、E61 lambda/seed扫描及只移除评分或拓扑的扩展。E61 fit自身净负，E62双因素均有灾难性损伤责任；先读34条关键案例和完整11命中组，保留原零命中群救回及WebVid T微弱fit信号，但不由事后极端组推断可预测收益。
2. 下一优先备选是保持原GT10成员归属，直接增加冻结基线零命中query的训练质量，区别于E61只改部分命中query的成员权重；必须回查E09的hardness/signed residual原实现，保持总训练质量与raw-prior一致，并加入同数量随机query身份控制。建议固定一个2倍质量对照，不做强度网格。它目前仅为[有界设计](entry_method_exploration/20260913_until2100_v1/next_stage_design.md)，尚未实现/运行，可依据新增证据前瞻调整。必须分别核验fit净值、cal净收益/失败约束和query成员损伤，不能把训练收益叫方法进步。
3. 后续每阶段继续独立版本、输入身份、严格串行native与state/handoff。当前会话10:15前退出且无遗留native，监督者负责串行新会话切换。至少预留最后一小时：建议20:00停止新训练、20:40停止新增查询、21:00交付。最终独立协议分别冻结best_all（允许原方法）及best_new（今天实际新方法中按开发规则选，仅供诊断展示）；即使无候选过门，也要与NSG/Fast/FastGT10及WebVid匹配soft起点同批实测，不只复用昨日曲线或baseline对自身。

最终E34历史validation2000只用于冻结后的最终比较，不反馈训练/选择。所有方法CPU15、threads=1及OMP/OpenBLAS/MKL/NUMEXPR/BLIS=1；每次一个被测方法，停止训练/标签/评分并发；整批纯端到端wall、多次重复，GT评分/计数/序列化不入timer，aligned逐query保留。五L五轮沿现有合同；Recall、严格GT10零命中失败率与QPS独立呈现，评估Pareto，不用NDC换算QPS。

原base/raw-IP/NSG/GT、H815/821冻结；Micro-HNSW仅入口画像。构建/安装/路由/NSG/缓存成本分账。/data初始7.984GiB，继续现场核对且至少7GiB余量，输出压缩，不删除历史。旧cal/audit/monitor均有历史暴露；下一版本用已有开发数据也须如实记录角色。

[campaign状态](entry_method_exploration/20260913_until2100_v1/state.json)、[接续命令与边界](entry_method_exploration/20260913_until2100_v1/handoff.md)、[E62证据](entry_method_exploration/20260913_until2100_v1/stage3_missing_factorial_v1/report.md)。昨天[next design](entry_method_exploration/20260912_until2000_v1/closeout/next_experiment_design.md)保持历史未运行提案身份，本日独立协议和实测不回写昨日封存。
