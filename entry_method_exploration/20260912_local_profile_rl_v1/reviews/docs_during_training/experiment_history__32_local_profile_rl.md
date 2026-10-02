# 32. E43 固定背景的局部画像策略优化

2026-09-12，状态`TRAINING_LOCAL_PROFILE_RL`，非最终结果。[协议](../entry_method_exploration/20260912_local_profile_rl_v1/protocol.md)、[配置](../entry_method_exploration/20260912_local_profile_rl_v1/config.locked.json)、[状态](../entry_method_exploration/20260912_local_profile_rl_v1/state.json)、[调用账](../entry_method_exploration/20260912_local_profile_rl_v1/logs/jobs.json)。用户授权有明确目标就持续推进至20:00，本阶段接续E42条件归因，已实际开始训练。

区别为H×16独立行参数，每次一行Gaussian动作、其它画像当前值固定；原P/B/H、普通HNSW和NSG保留。GT无关hub日程与uniform train128独立，两臂同seed日程相同。八独立方向LOO RL对四正负对ES，原σ.3/200步/Adam日程不扩网格；RL/ES都实际支付当前+八候选的HNSW构图与NSG，整个batch收益损伤收费。

双数据集预检已恢复全部10240原基线返回，验证单行构造/零参数字节、baseline抵消/梯度/Adam、序列化plain与原kernel；实际10816 NSG/6图。八次完整训练预计1981440 NSG/14504图，仍在执行，不能将预检或中途monitor当成方法结果。原E37–E42保护与根文档前件已保存。

完成后将独立复算全部奖励/梯度/Adam/状态、原始反馈与checkpoint，补完整正负、覆盖hub和反馈稀疏度、成本/图表与门。单纯减当前J在LOO/ES中严格抵消，不把reward改名当机制创新。H×16自由度也与E37不同，不把跨版本差异全部归因RL。当前没有新开发/QPS或默认替换结论。
