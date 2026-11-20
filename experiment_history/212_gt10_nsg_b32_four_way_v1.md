# E212 四集 NSG 和三条 GT10 链路同期对照

E212 四个真实数据集各3072条，真实 K1/K100 各7个 L。224点448批。同表的新 GT10+B32 相对旧 GT10+B32 56组返回逐字相同，完整 QPS 变化 +13.43% 至 +27.54%。固定同 L 补点平均 Recall 增加 52/56 点，完整 QPS 降低 56/56 点。

原图上的固定单入口 NSG 使用同一 SPAN4，与新 GT10 的三入口画像比较。新旧 GT10+B32 共用各集对应 B32 表，旧主搜索显式选择标量。所有方法使用 E211 发布二进制对应库和同一计时边界。公开3,072条的真实 K1/K100 各7个 L，每点两遍、完整 wall。168 个包与 E211 相同，52 个 NSG 返回前缀与 E200 相同，GT 评分及独立审计见原件。

[报告](../entry_method_exploration/20261120_gt10_nsg_b32_four_way_v1/report.md) · [协议](../entry_method_exploration/20261120_gt10_nsg_b32_four_way_v1/protocol.md) · [状态](../entry_method_exploration/20261120_gt10_nsg_b32_four_way_v1/state.json) · [E211](211_span4_production_default_v1.md)
