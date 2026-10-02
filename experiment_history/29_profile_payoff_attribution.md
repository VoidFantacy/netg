# 29. E40 已有画像动作的收益、损伤与入口归因

2026-09-12，状态`COMPLETE_PAYOFF_ATTRIBUTION_LOCAL_OPPORTUNITY_WITH_CANCELLATION`。[报告](../entry_method_exploration/20260912_profile_payoff_attribution_v1/report.md)、[协议](../entry_method_exploration/20260912_profile_payoff_attribution_v1/protocol.md)、[验收](../entry_method_exploration/20260912_profile_payoff_attribution_v1/reviews/final_audit.json)。用户要求继续分析E39已有动作，区分局部空间和不同query冲突；本次没有新搜索/构图/训练。

## 输入、定义与结论

四个E39固定参数点各八扰动+中心、相同1024训练query，原H/画像/ID/NSG/raw-IP/L128不变。仅从原输出集合评分和画像字节重算，主要参照各自中心。G为正Δhits之和、L为负Δhits绝对值，O为九已测配置逐query最大增益、B为最佳单一静态配置净增益；O−B=(O−G_best)+L_best。原GT10只用于奖励分母/旧返回回归，不混作各点中心。

现有局部动作有非零但稀疏的改进空间；收益分散与正负抵消同时存在。32个全局扰动均帮助一部分query、损伤另一部分，单一已测配置仅保留有限逐query上界的0%–23%。这支持停止给同一全局扰动训练器加预算，先定位联动损伤；它尚未证明共享参数表示在数学上无法兼顾这些query。

| 固定点 | 有可获益query / 1024 | 九配置逐query上界 ΔR pp | 单一配置最佳 ΔR pp | 最佳配置增益−损伤（命中数） |
|---|---:|---:|---:|---:|
| WebVid / 初始化 | 35 | +0.9277 | +0.1855 | 41−22=19 |
| WebVid / 已选点 | 26 | +0.4102 | +0.0000 | 0−0=0 |
| Yandex / 初始化 | 15 | +0.6445 | +0.1465 | 36−21=15 |
| Yandex / 已选点 | 17 | +0.6641 | +0.1465 | 42−27=15 |


逐query上界非全画像空间上界、非部署/泛化结果；只覆盖中心剩余漏检1.70%–6.77%。单一最佳动作未覆盖的收益和实际损伤分别为54/22、42/0、30/21、26/27个命中。WebVid已选最佳为中心，其余八动作全负，最好也增加9损失20，不能由中心loss0推断没有扰动损伤。

## 机制与限制

32扰动全部有正负query；跨query抵消有直接证据，但同query正负俱有仅0/1/0/0。6508次入口变化约92.76%未改命中。单交换5953事件/5879组，完整转移6502组，均未观察到相同动作+相同交换的正负重复；大多数只有单条query，不支持证明硬冲突或证明没有冲突。同动作新增某hub有4/12/3/0个混合组，移除有10/6/2/0个；其它入口同时变化，需[隔离案例](../entry_method_exploration/20260912_profile_payoff_attribution_v1/cases.md)反事实，不能分配单hub因果标签。

全1024池最近5中双方可获益的pair仅13/7/5/4，其中5/4/3/1没有共同改善动作；在有收益子集最近5的比例更高但GT条件化。相似性是有限样本内cosine，不等同语义类。单交换81.51%跨几何边界、90.95%动作下新增分数更高；不含HNSW访问trace，不能把余项当ANN错误。

## 执行、保护与接续

主分析CPU8/实际线程1约0.746s、RSS约135.5MiB；独立集合评分36864条，13016得分边界、23369分组、1161pair及最近query关系复核通过。所有新NSG/HNSW/构图/optimizer/GT均0；旧E37/E38/E39保护SHA与根文档前件保留，无新的原validation/held-out访问。E39标签取得的38592次真实NSG成本不能省略，诊断时间不是QPS。

下一步唯一优先为同一固定动作的目标hub/其它hub 2×2隔离：中心、全扰动、仅目标行、仅其余行，真实重建普通HNSW并全1024计入损伤；约8576次NSG/硬限10000是未执行建议。它区分局部画像与其余画像联动，仍不隔离评分与拓扑，也不升级free-W训练。旧自由表示/目标路线的[复核](../entry_method_exploration/20260912_profile_payoff_attribution_v1/historical_review.md)保留；新控制尚无构图/搜索或任务排队，默认/E37开发门保持。详见[s-target](../s-target.md)。

[完整动作](../entry_method_exploration/20260912_profile_payoff_attribution_v1/results/actions.csv)、[逐query](../entry_method_exploration/20260912_profile_payoff_attribution_v1/results/queries.csv)、[入口事件](../entry_method_exploration/20260912_profile_payoff_attribution_v1/results/entry_events.csv)、[有限上界图](../entry_method_exploration/20260912_profile_payoff_attribution_v1/figures/payoff_gap.svg)。
