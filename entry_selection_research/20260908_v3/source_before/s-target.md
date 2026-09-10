# ACSG 当前研究任务：依据Fast诊断重审入口选择目标

> 2026-09-08。`COMPLETE_FAST_ROUTER_DIAGNOSIS`。用户授权的实际诊断、统计与报告已完成；当前无待续实验进程。先解决真实搜索效用的表示与低成本可预测性，撤下固定anchor、固定三入口和C8充分覆盖的预设。

## 当前证据

本文件统一记录“现在做什么、下一步是什么”；实现与复现契约见[spec.md](spec.md)第18节，研究结论见[summary.md](summary.md)。

- [根因报告](fast_router_diagnosis/20260908_v1/report.md)：六个诊断问题、数值、理论边界与决策。
- [32项完整统计](fast_router_diagnosis/20260908_v1/analysis/v2/analysis.md)、[机器可读结果](fast_router_diagnosis/20260908_v1/analysis/v2/analysis.json)、[执行台账](fast_router_diagnosis/20260908_v1/state.json)。
- [冻结协议](fast_router_diagnosis/20260908_v1/protocol.md)、[复现说明](fast_router_diagnosis/20260908_v1/README.md)、[独立执行审计](fast_router_diagnosis/20260908_v1/reviews/independent_execution_audit.md)、[独立统计复核](fast_router_diagnosis/20260908_v1/reviews/independent_analysis_review.md)。

两数据集同20K paired Fast、原NSG/raw-IP，各512历史pilot，全H单入口及C8全部pair/triple、最近fit/随机fit控制，共2,770,770次搜索。输入、画像逐字节复算、真实执行与独立分析均通过。仅新版本内增加诊断工具/副本/结果，方法源码和历史产物保护；原始validation/held-out未访问。

| 诊断问题 | 实际发现 | 当前判断 |
|---|---|---|
| 是否实现错了 | 图/base/ID/画像一致，count/plain/repeat及真实入口消费通过 | 检查项内没有发现实现错误，不能扩大成整个算法无缺陷证明 |
| HNSW近似是主因吗 | exact3相对Fast3变化WebVid+0.35/+0.63 pp，Yandex−0.45/−0.31 pp | 效果小、方向不一致，不先扫HNSW补主要缺口 |
| 几何标签代表好入口吗 | 即使直接知道GT1 basin，全H最佳single仍高4.80–13.07 pp | 当前监督代理不等于真实搜索效用；单均值、多模态、prior等尚未分别干预 |
| C8够用吗 | 全H最佳single仍比exact C8最佳single高3.16–6.66 pp | 短名单内外均有损失，不能默认完美C8重排足以解决 |
| 固定anchor/三入口合理吗 | anchor限制损失0.84–3.11 pp；四点C8最佳single平均均略高于最佳triple | 撤下两个默认限制；oracle未证明single部署最优 |
| 理论上不可学习吗 | 四个最近fit−随机fit主区间均跨0；跨L A0仍有92.19%/96.09%相交 | 当前简单近邻信号不稳定，既无普遍不可学习证明，也无廉价可预测性GO |

所有表中差值限定当前H、给定L、Recall@10和动作家族。同L不等于同NDC/同wall；oracle使用目标标签、免费选择。32项区间来自历史pilot配对bootstrap近似，不能代替三独立构建或正式held-out。

## 下一步的研究顺序

**先确定廉价在线信息怎样预测真实搜索效用，再决定入口组合。** Fast基线继续保留；“换模型名/加MLP/换loss”不自动形成新机制，旧single utility ranker已经用过真实Recall/NDC监督。

1. 以单入口作为最小诊断动作，保留`(query, entry, L)`条件和全部同Recall入口。明确拟议表示比GT1 basin/单均值多了什么可部署信号、为何有望超过旧ranker。
2. 若形成可检验的新机制，另冻结训练/开发分离与有限标签预算。画像及训练只用后20K，不能拿本轮pilot搜索标签回灌训练再测同一pilot；比较Fast、当前几何代理和新表示，同时检查短名单内外损失。
3. 先看样本外真实Recall/NDC信号，再测候选检索、打分、选择、搜索的完整wall。不得把oracle上限或图NDC节省当作端到端收益。无可靠信号就停止该机制，不靠扩大模型或追加扫参掩盖。
4. 只有单入口/候选匹配证据指向组合必要性，再建立入口数与联合标签契约；不预先固定anchor，也不从此次结果直接认定single最优。

这里没有已实现、可直接继续运行的新训练命令，也没有新方法GO。当前授权的诊断已完整结束；此研究顺序保留为下一方法设计的依据。

## 保留边界

原`entry_selection_research/20260908_v2`的[调研报告](entry_selection_research/20260908_v2/report.md)、[推荐](entry_selection_research/20260908_v2/recommendation.md)和[最小gate草案](entry_selection_research/20260908_v2/minimum_gate.md)保留历史交付身份。其固定anchor/三入口与40维联合选择器均不是当前默认主线，未训练；原计划见[本轮前快照](fast_router_diagnosis/20260908_v1/source_before/s-target.md)。

旧R0–R2、分层P3 NOPASS、Multi-view成本NO-GO和夜间state/gate/CLOSED不恢复。候选/base/预处理/metric/图/GT/split变化时按spec联动重建相应下游，保留旧产物。新方法仍须双数据集、强基线、三独立构建、尾部、两相邻工作点与完整成本验证，方法冻结后才使用held-out10K×3。诊断完成不等于长期方法目标完成。
