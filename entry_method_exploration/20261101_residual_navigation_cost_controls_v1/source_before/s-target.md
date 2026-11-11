# ACSG 后续研究问题

2026-11-01。用户授权的[E195七集详细定位](entry_method_exploration/20261101_residual_navigation_diagnosis_v1/protocol.md)已完成固定范围，无待恢复队列，默认E99 GT10保持。实际结果读[summary](summary.md)和[E195报告](entry_method_exploration/20261101_residual_navigation_diagnosis_v1/report_zh.md)。

## 根据定位保留的分支

分数据解释、有效配置与下一问题见[定位结论](entry_method_exploration/20261101_residual_navigation_diagnosis_v1/findings_zh.md)。

按数据/K/预算评价直接补全、导航增量和完整费用。具体两窗正且未被本轮已有网格覆盖的配置见[stability](entry_method_exploration/20261101_residual_navigation_diagnosis_v1/analysis/stability.csv)，属于探索候选；未通过的实际效应和成员损伤保留，不能一票否决所有后端或所有数据集。后续不自动追加当前曝光窗口调参。

1. 来源不足时先研究更便宜的新支持；固定源不含目标，池内评分不能创造该目标。区域/块可访问源外，但须看路由覆盖、短名单和完整费用。保留强B32和历史M5/SQ具体有效配置。
2. 导航研究以本轮实际新增/损失和选择费用为基础。直接C保留，真实代表/种子只承担有限动作价值；入度/出度/未访问邻居是特征或静态基线，GT相关不是可部署规则。E195已实现独立辅助多步扩展，原search_new仍无完整续搜接口；更多seed或独立命中并集不保证共享beam改善。
3. 稀疏修复和主搜索便宜评分仍是条件性提案，尚未在E195实现或验证。要先识别实际路径或评分费用障碍；改主图必须重绑教师/表/响应/计时，压缩/guard/精排均支付完整费用。RoarGraph/NGFix及旧M2/FINGER/LeanVec/RaBitQ/PAG的前作边界沿原[理论](entry_method_exploration/20261030_residual_navigation_theory_v1/theory_zh.md)保留。

## 进退与稳定性

后继按具体数据集的效应、成本和小计数保留候选，先明确需要改善的是来源、动作还是信息；不用更复杂模型代替新信息。未来新模型/图/查询角色和预算须另冻协议，正式仍为真实K1/K100、串行T1、完整wall、强GT10/B32同窗比较。当前A/B已曝光，不称盲确认。E194的两个OPT-B32条件性工程配置保留；E193原门控和E174原一跳结果保持历史身份。

本次详细验证固定矩阵与分析已收口；下一轮具体实现与确认按用户新指令，不恢复旧runner或自动扩大当前窗口。
