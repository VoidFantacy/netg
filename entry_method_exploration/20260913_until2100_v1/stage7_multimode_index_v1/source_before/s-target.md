# ACSG 下一阶段目标与接续

2026-09-13，第二串行会话完成E63零命中质量、E64扩大历史开发复核、E65开发五L五轮wall。双集没有新候选过完整开发门，WebVid局部曲线正信号保留；整日21:00目标仍未完成。当前会话最迟11:14:29安全交接，由监督者串行开启后续会话，禁止并行CLI/子代理。

1. 优先备选为**单个3H多画像小索引**：固定原真实H与三入口，保留原P并增加两份离线query模态，取7个slot去重为三个真实ID。必须回查history04/旧E10，建立当前GT10归属、低支持退化、先验/模式质量、slot映射及去重新协议；同容量3H重复P控制区分表示与拓扑变化。画像节点2445/2463与真实入口815/821分账。它尚未实现/运行，单画像瓶颈也未证实；不得复用旧k3重复映射接口或同时扫2H/3H。详细有界方法、成本/门和来源见[next design](entry_method_exploration/20260913_until2100_v1/next_stage_design_session2.md)。
2. 停止E61 lambda、E63倍数、当前端点seed和同类局部动作扩大。E63的fit正值与开发迁移不足分开；E64 WebT净+38且两半正，但失败+2；E65局部曲线正值仍伴随损伤。保留全部失败案例，尤其Yandex3846五L全命中→零命中；不要用事后案例直接训练在线规则或把总损伤归给单因素。后续可提出实质不同表示/反馈机制，但先锁输入、控制与预算。
3. **20:00停新训练、20:40停新增查询、21:00完整交付**。E65是已用于选择的历史开发2048，晚间仍需在E34历史validation2000上固定best_all和今日真实best_new后的完整同批对照；最终反馈不回流训练/换候选，held-out不自动打开。即使无改进，也需展示实际新候选与原NSG/Fast30K/FastGT10-hard及WebVid匹配soft的QPS–Recall、QPS–零命中失败率、按L三指标和失败救回/新增，不能只复用本批或昨天曲线。

所有ANN/正式比较CPU15、threads1、OMP/OpenBLAS/MKL/NumExpr/BLIS1，单个被测方法与训练/评分串行；固定预热和轮换，完整在线路由+原NSG+输出的独立整批wall，多次重复。GT/count/hash/JSON/build/load在外，aligned返回集合评分。以同机完整前沿判断，不以NDC、同LRecall或单次QPS给GO。

原base/raw-IP/NSG/GT固定；新实验独立目录/manifest，root source_before和历史封存保持。现场free至少7GiB，单后续阶段建议≤128MiB，保留晚间性能输出空间，不删除旧产物。P-fit20K、旧train/monitor/cal/audit及辅助7952均有历史暴露；前10K已被Fast30K/E10使用，任何辅助动作/模型选择反馈均计训练。

[campaign状态](entry_method_exploration/20260913_until2100_v1/state.json) · [安全交接和下一命令](entry_method_exploration/20260913_until2100_v1/handoff.md) · [候选身份及别名](entry_method_exploration/20260913_until2100_v1/candidate_inventory_v2.json) · [已完成E65](entry_method_exploration/20260913_until2100_v1/stage6_development_wall_v1/report.md)。旧[next design](entry_method_exploration/20260913_until2100_v1/next_stage_design.md)与2H首稿保留历史身份，不覆盖当前未运行3H设计。
