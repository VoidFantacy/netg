# E36：针对query逐步换入/换出三入口

2026-09-11，独立版本`20260911_query_swap_policy_v1`。用户在E35最小诊断后明确确认推进实际查询相关换点学习，已完成训练/部署/预算收口。状态`COMPLETE_QUERY_SWAP_POLICY`，开发判断`STOP_DUAL_DEVELOPMENT_GATE`。详见[原报告](../entry_method_exploration/20260911_query_swap_policy_v1/report.md)、[协议](../entry_method_exploration/20260911_query_swap_policy_v1/protocol.md)、[验收](../entry_method_exploration/20260911_query_swap_policy_v1/reviews/final_audit.json)。

## 动机与实质差异

E35发现已评分好点没有保留，exact画像top3增量小而真实C8三入口oracle仍有空间。本轮固定原HNSW/H/画像/NSG，使用一次GT10 top8，从原三入口开始，按query学习最多三步换点或停止；没有改图或更换全局聚类点。56完整集合、16动作/态，query投影/画像交互等76维特征和1521参数非加性集合势函数。E28/E32曾用共享画像/真实收益，本次增加明确状态/动作/停止及同一三步策略精确梯度控制，候选由旧两路union改为当前单路top8，因此生成新标签。

奖励来自原NSG raw IP/L128/K10三个真实ID升序共享beam的实际命中及总NDC，使用相邻集合U差、γ1。RL是REINFORCE加历史query-state EMA baseline，训练时复用完整真实标签缓存；Exact是同策略完整期望梯度，线上都只使用query和候选特征，不读GT。stop不保证真实收益不降。

## 样本、选点与实际执行

两集各2048 fit（1792 train/256 monitor）、cal/audit各512，源行与SHA核验、四部分行不重叠，但都历史使用且画像为历史fit构建，非盲测。两臂双seed共8次固定3000更新；monitor按U和NDC门选checkpoint，cal选seed再冻结audit，两集主RL/Exact均seed18。全部另seed、末点、训练和开发正负保留。

新NSG280352/上限300000（完整56标签229376，其余回归/部署/wall），HNSW62464。RL768000条缓存反馈轨迹单列，不当新查询；训练进程125.42s，24000更新。查询串行CPU15/实际线程1，最高RSS约9.937GiB。无新GT、validation/held-out、多L前沿、图交换，剩余预算不扩展。

## 结果和成本

| 数据 | 所选RL cal ΔRecall | audit ΔRecall | audit ΔQPS |
|---|---|---|---|
| WebVid | -0.1758 pp | -0.4688 pp | -9.32% |
| Yandex-IP | +0.7227 pp | +0.3906 pp | -8.30% |

Yandex RL18 audit Recall88.652344%，原top3 88.261719%；失败率从1.757813%降至1.562500%。WebVid RL18为74.609375%对75.078125%，失败率1.5625%对1.171875%。Yandex RL相对Exact18仅cal +0.019531pp/audit +0.117188pp；audit对原与Exact的配对95%区间均跨0，不能归因RL稳定优势。WebVid两臂都未通过开发，不能看到audit后改选另seed。

单L128成本诊断无论开发正负都按协议完成：原/所选RL/所选Exact，audit512，warmup+五轮轮换独立plain整批wall。计时含全部56特征/MLP/换点/NSG，GT/count/load/IO在外。RL总NDC仅增加WebVid0.388%、Yandex0.283%，QPS却下降9.32%/8.30%，表明NDC未覆盖选择器的主要非距离费用。不能用单L判断完整Recall–QPS前沿。

两集平均U均胜随机，Yandex通过预定开发点门，WebVid未过，因此双集开发停止、默认不换；保留Yandex查询相关组合选择的局部信号，不外推所有RL失败。训练后期train改善未稳定传至monitor，应先定位泛化/推理开销而非盲增epoch。

## 验收、修正和证据

229376真实标签、完整路径DP与期望策略梯度有限差分验收；全部248checkpoint前向/贪心、768000轨迹reward/return/EMA独立核验，38原生部署点动作和真实入口一致，512 fit部署与缓存完整返回一致、4096基线与旧E33同GT10结果一致。原生count/plain和原kernel回归、wall/audit返回及全部图表/工作簿/CSV验收见原报告。

runner v2仅在部署前增加pool距离导出与parity，原label runner保留；分析v1的NumPy布尔序列化错误由v2类型转换修复，原脚本/派生输出保留，0新增查询训练。所有旧源/图/标签/模型/历史保护；该卡是实际结果，E35当时未训练的原协议不回写为已执行。[图](../entry_method_exploration/20260911_query_swap_policy_v1/figures/development_quality_and_cost.svg)、[工作簿](../entry_method_exploration/20260911_query_swap_policy_v1/results/query_swap_policy.xlsx)、[完整点](../entry_method_exploration/20260911_query_swap_policy_v1/results/points.csv)、[当前接续](../s-target.md)。
