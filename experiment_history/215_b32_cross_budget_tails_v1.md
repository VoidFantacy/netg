# E215 小 L 补点候选来源

2026-11-21 完成。COCO hard、WebVid soft-t1，沿用 E206 的合法身份角色划分和真实 K1/K100 训练返回。目标是在 L184 与每查询原 B32 实际精算数下，达到同一 fit-only B32 表在 L192 的召回。

第一阶段保留原 B32-L200 行前缀，另编跨档救回与持续遗漏两个加权后半表。枚举三行各三种尾部的 27 个动作，精算与严格 Top-K 真合并。64,000 状态、1,728,000 动作回放。COCO K100 事后逐查询最佳距 L192 参考差 2/3 个正确成员（dev/cal），WebVid 差 444/631。WebVid K100 校准窗的三个尾表并集用 GT 理想挑选仍差 326。0/4 个单元满足两窗的预设跨 L 参考条件。

追加诊断用完整 query 余弦从 fit 拿 16 个近邻，根据其 L184 实际遗漏投票。保留原前缀，至多替换 8 或 16 个尾部 ID，原实际精算数逐查询相同。15,906 状态、63,624 次合并。全部遗漏来源、16 个新点配额下，K100 校准窗 COCO 由 96.1770% 达到 96.4807%，L192 参考为 96.3866%；WebVid 由 72.5607% 达到 73.1924%，L192 参考为 73.2403%。WebVid 的 K1 两窗均超参考，K100 开发窗超 43 个成员、校准窗差 95 个。WebVid K100 校准窗候选池在原三尾表并集外提供 7,552 个不同的 query–GT 成员事件。

候选供应与精确合并均为离线诊断，第二阶段沿用已曝光的 dev/cal。全量预算、64,000 个旧基线 ID/距离比对、1,296＋128 独立线性与 Python 小样本核验通过。新 ANN、公共测试读取和正式 QPS 均为 0。下一评估问题是近邻候选供应怎么低成本在线实现，需把寻近邻和投票一起计入完整 wall。

[报告](../entry_method_exploration/20261121_b32_cross_budget_tails_v1/report.md) · [后半表协议](../entry_method_exploration/20261121_b32_cross_budget_tails_v1/protocol.md) · [邻近查询协议](../entry_method_exploration/20261121_b32_cross_budget_tails_v1/neighbor_source/protocol.md) · [逐窗实测](../entry_method_exploration/20261121_b32_cross_budget_tails_v1/analysis/neighbor_source.csv) · [状态](../entry_method_exploration/20261121_b32_cross_budget_tails_v1/state.json)。
