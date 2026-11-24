# E227 B32 截止分双塔

E226 的双塔 B32 固定精算 48 个候选，减少精算与保留真实补回成员存在取舍。按用户要求本轮只用原版 B32 候选池。用查询和候选两个 16 维编码回归 raw-IP，对低估原版 B32 实际补回的真值成员加罚。在线以主返回第 100 名分数减去校准安全余量为门槛，筛掉低分，一趟过滤，筛剩不足 16 时恢复整池。转置投影，预绑定 posting 码槽，保持原始候选顺序和精算规则。

COCO、WebVid 真 K100，第三公共窗各 3,072 条。COCO 核源身份，WebVid 拟合排除一条与正式窗字节相同的记录。四档校准原生回放共 16 点、16,352 条全排序核验。正式 11 个 L、44 点、88 批完整单线程。计时和评分阶段隔离，两遍数据包位级一致，COCO 原版返回与封存 E224 第三窗匹配 11/11 组。历史窗暴露和两遍速度重复按原协议披露。

同窗校准 L184 内，原固定 48 个的双塔对原版 B32 的损失为 43 / 204 个正确成员，动态版损失为 27 / 26 个，同时平均精算数上升到约 56 / 74。正式同 L 下，COCO / WebVid 平均少精算 30.60 / 19.60 个，召回差为 −0.0280 至 −0.0234 / −0.0348 至 −0.0335 个百分点。完整 QPS 差中位数 +0.04% / +0.23%。十个重叠点中，各有三个比 B32 折线更快。分段审计显示约 1.5 μs/query 筛选开销，精算分段可能受标量核验预热。现有结果支持继续以原版 GT10+B32 为补点基线。

[报告与图](../entry_method_exploration/20261122_b32_cutoff_two_tower_v1/report.md) · [协议](../entry_method_exploration/20261122_b32_cutoff_two_tower_v1/protocol.md) · [源码](../entry_method_exploration/20261122_b32_cutoff_two_tower_v1/src/benchmark.cpp) · [逐点](../entry_method_exploration/20261122_b32_cutoff_two_tower_v1/analysis/points.csv) · [封存](../entry_method_exploration/20261122_b32_cutoff_two_tower_v1/seal.json) · [前置快照](../entry_method_exploration/20261122_b32_cutoff_two_tower_v1/source_before/)
