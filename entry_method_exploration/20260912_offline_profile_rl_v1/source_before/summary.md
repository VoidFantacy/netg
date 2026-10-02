# ACSG 当前结果摘要

2026-09-11。最近完成E36 query相关三入口换点学习，状态`COMPLETE_QUERY_SWAP_POLICY`。[报告](entry_method_exploration/20260911_query_swap_policy_v1/report.md)、[历史25](experiment_history/25_query_swap_policy.md)、[验收](entry_method_exploration/20260911_query_swap_policy_v1/reviews/final_audit.json)。用户确认实际推进，已完成8次×3000更新、真实联合搜索反馈与在线部署。

## 当前结果

| 数据 | 所选RL cal ΔRecall | audit ΔRecall | audit ΔQPS |
|---|---|---|---|
| WebVid | -0.1758 pp | -0.4688 pp | -9.32% |
| Yandex-IP | +0.7227 pp | +0.3906 pp | -8.30% |

一次当前GT10 HNSW top8，从原top3开始，学习至多3步单点换入/换出或停止；对照原top3、同动作域随机策略、同表示/同三步策略的Exact期望梯度，各训练臂双seed。表为cal选定并在audit前冻结的RL seed18，相对原top3。WebVid采用GT10-soft-t1，Yandex采用GT10-hard。

Yandex保留局部正信号，RL相对Exact在cal/audit仅+0.019531/+0.117188pp，配对区间跨0；尚无RL稳定增量证据。WebVid所选RL cal/audit下降，两集联合开发门`STOP_DUAL_DEVELOPMENT_GATE`。总NDC增加不足1%仍伴随8%～9% QPS下降，当前56集合特征/MLP费用进入了wall。单L128、每集历史audit512、五轮单线程成本诊断不能代替完整Recall–QPS前沿，默认未换。[质量与成本图](entry_method_exploration/20260911_query_swap_policy_v1/figures/development_quality_and_cost.svg)、[Excel](entry_method_exploration/20260911_query_swap_policy_v1/results/query_swap_policy.xlsx)。

## 训练、核验和范围

每集fit2048（1792 train/256 monitor）、cal/audit各512，行互斥但历史使用，原画像也来自历史fit，非盲测。新生成每query全部56个真实NSG三入口联合标签，奖励为命中增量减总NDC惩罚的相邻差；RL缓存反馈复用不当新查询。train收益上升未持续传至monitor，不据此追加epoch。

新NSG280352/300000、HNSW62464；8次共24000更新、RL768000条轨迹，训练进程125.42s。229376标签、全部248checkpoint、轨迹reward/return/EMA与38个原生部署点验收；当前GT10基线4096条与E33原结果一致。查询串行且实测线程1，最高RSS约9.937GiB。无新validation/held-out、GT生成、多L或改图。

部署runner v2只增加pool距离导出以完成独立特征核验；分析v1的布尔JSON类型错误在v2修复，0新训练/查询，原件保留。旧源/图/标签/模型/结果保护，四根文档与历史同步。

## 与前序和后续的关系

[E35](experiment_history/24_hnsw_selection_diagnosis.md)的“强连通、好点已评分却未保留、当前C8真实组合oracle有空间”仍是动机，不把oracle空间写成E36实际收益。[E34](experiment_history/23_hnsw_rl_benchmark.md)已表明旧删边RL相对原GT10无稳定增量，本次没有重启该算法；E24/E28等局部信号分开保留。

下一步先用已有标签定位WebVid泛化和收益损伤，再降低当前集合评分成本；Yandex信号需要独立质量和完整成本证据。图交换为后续补充覆盖路线，尚未实施。详细方法/控制/成本/停止条件见[s-target](s-target.md)。本轮无排队任务。
