# 22 强化学习直接训练HNSW图边（E33）

2026-09-11完成，状态`HNSW_EDGE_RL_COMPLETE_WEBVID_SIGNAL_NO_DUAL_GAIN`。用户明确希望训练改变HNSW图，并授权推进小实验。本轮完成真正的图边RL闭环及真实开发评测；WebVid主图过局部门，Yandex失败，双集门停止，未开展新validation/QPS。

## 问题、机制和旧版本区别

[E32](21_direct_reward_policy.md)在固定C8内选择完整三入口，不训练HNSW边。E33固定当前默认画像、H815/821、映射和原NSG，给Micro-HNSW底层原边设置独立Bernoulli logit。真实HNSW遍历时抽样keep/remove，输出三个真实入口进入原NSG；GT在搜索返回后评分，REINFORCE用终局命中和总NDC更新边概率。不是PPO、神经网络教师或坐标变换；不会改变原NSG大图。

奖励`hits−hits_base−.1(totalNDC/totalNDC_base−1)`，每query此前奖励EMA基线、熵系数.001、Adam600步、lr.025余弦到.0025、batch128、clip1/logit±4。策略不依赖query，导出概率≥.5边的静态图后，线上只需原hnswlib，不含采样/网络或C8全H填充。方法依据及与原TRPO论文区别见[研究说明](../entry_method_exploration/20260911_hnsw_edge_rl_v1/literature/method_basis.md)。

固定出树/入树和每节点min(2,原出度)条最近边，保持强连通；节点画像、外部ID、层级、上层邻接逐位不变。首版预检过严要求原出度≥2，WebVid38个合法单边节点导致训练前停止；保留原协议/源码/binary，以v2修正结构条件，未调整奖励、seed、split或开发门。首次失败NSG/HNSW查询及optimizer均0，[修正](../entry_method_exploration/20260911_hnsw_edge_rl_v1/structural_preflight_repair.md)。

## 数据、训练与图结构

原fit20K固定排列为train16K/monitor4K，monitor本轮不参与更新，全部样本有历史使用。两集×RL seed20260911/20260912各600步，共307200条新反馈；每100步导出静态图，按最高monitor奖励选非零checkpoint。各seed另有逐节点保留边数匹配的随机控制。cal只选主seed，audit不选模型。

WebVid两个seed选step600/400，monitor ΔRecall +.0600/−.0300pp；Yandex选step300/100，为−.0675/+.0500pp。cal最终选WebVid seed20260912、Yandex seed20260911，分别删除2301/7530=30.56%、3090/9055=34.12%的底层边。正信号与负信号分开保留，训练末段采样奖励仍均低于原图，不能说已经稳定收敛到更优图。

## 开发结果与随机控制

每集cal/audit各1024query，原图、两个RL、对应两个随机图，20个L128点。主图相对原图：

| 数据集/split | ΔRecall pp | 总NDC变化 | RL−匹配随机 pp |
|---|---|---|---|
| WebVid cal | +0.3418 | −0.978% | +0.2832 |
| WebVid audit | +0.1270 | −0.985% | −0.0684 |
| Yandex cal | −0.1660 | −0.424% | +0.1465 |
| Yandex audit | −0.2734 | −0.350% | −0.3125 |

WebVid两点均满足质量/成本门，合并奖励胜对应随机，保留单集线索；但audit随机图本身+0.1953pp，不能归因全部改善于学习。Yandex两个RL seed在两个split四点皆负，主seed还未胜合并随机奖励，双集门失败。RL−随机的全部配对区间覆盖0；WebVid cal参与了seed选择，其相对原图正区间未校正选择，不是独立显著性结果。

路由NDC约降低18%–19%，NSG NDC增加约.19%–.38%，总成本仅减少不足1%；无wall，不换算QPS。依原门停止后续validation，没有只为WebVid追加性能矩阵。当前默认仍是WebVid GT10-soft-t1、Yandex GT10-hard的原HNSW，未替换索引。

## 成本、验收和边界

实际NSG500736调用、预留500992/1200000；HNSW508608查询单列；旧C8标签0。四次训练含monitor共218.20s，训练总进程255.41s含加载/基线/保存等，线程1/RSS约10.25GiB。所有开发评测CPU15、实际进程/OMP线程1、OMP/BLAS/MKL1。

all-keep/骨架/随机mask的hook与物理删边HNSW一致；原NSG/计数和完整开发plain/count通过。16种小图枚举/有限差分/基线不变性通过；独立NumPy重放2400次更新，24个非零checkpoint最大误差<2.4e−15。36份导出图的坐标/映射/层级/上层保持、底层mask/连通验证通过；479680保存输出独立GT复算，原默认完整回归E32。

原E32完整目录及实际依赖SHA保护，更早9211文件只stat身份保护；旧validation原始输入未hash/解码，新validation未评测，held-out未读/hash。只有一个原HNSW建图seed与两个RL seed、全部split重复历史使用，无正式性能GO。本轮只能评价保骨架、只删底层原边的静态策略；加边、重连、坐标偏移和在线逐跳网络均未测试。

- [完整报告](../entry_method_exploration/20260911_hnsw_edge_rl_v1/report.md)、[协议](../entry_method_exploration/20260911_hnsw_edge_rl_v1/protocol.md)、[开发门](../entry_method_exploration/20260911_hnsw_edge_rl_v1/results/development_gate.json)、[状态](../entry_method_exploration/20260911_hnsw_edge_rl_v1/state.json)、[调用账](../entry_method_exploration/20260911_hnsw_edge_rl_v1/logs/jobs.json)。
- [训练与静态图](../entry_method_exploration/20260911_hnsw_edge_rl_v1/figures/training_and_static_graphs.svg)、[开发/成本图](../entry_method_exploration/20260911_hnsw_edge_rl_v1/figures/development_and_cost.svg)、[结构图](../entry_method_exploration/20260911_hnsw_edge_rl_v1/figures/graph_structure.svg)、[Excel](../entry_method_exploration/20260911_hnsw_edge_rl_v1/chart_data.xlsx)。
- [环境](../entry_method_exploration/20260911_hnsw_edge_rl_v1/src/environment_v2.cpp)、[训练](../entry_method_exploration/20260911_hnsw_edge_rl_v1/src/train_v2.py)、[开发控制器](../entry_method_exploration/20260911_hnsw_edge_rl_v1/src/development.py)、[训练独立复核](../entry_method_exploration/20260911_hnsw_edge_rl_v1/reviews/training_independent_verification.json)、[最终验收](../entry_method_exploration/20260911_hnsw_edge_rl_v1/reviews/final_audit.json)。

预算已收口。后续先区分局部删边信号与学习相对随机的增益；若另行研究坐标位移，需要独立协议和重建HNSW/真实奖励闭环。新目标见根[s-target](../s-target.md)，不重启此冻结runner。
