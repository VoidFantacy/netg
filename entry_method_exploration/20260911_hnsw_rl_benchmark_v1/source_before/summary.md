# ACSG 当前实验总结

2026-09-11。最近完成E33，状态`HNSW_EDGE_RL_COMPLETE_WEBVID_SIGNAL_NO_DUAL_GAIN`。[完整报告](entry_method_exploration/20260911_hnsw_edge_rl_v1/report.md)、[历史22](experiment_history/22_hnsw_edge_rl.md)、[状态](entry_method_exploration/20260911_hnsw_edge_rl_v1/state.json)。

## 当前结论

本轮已实现用户希望的“训练改变HNSW图、再直接遍历”之边结构版本：REINFORCE在真实HNSW→NSG轨迹上学习底层边的保留概率，最后导出静态图。WebVid有局部收益，Yandex两seed四个开发点均下降；学习相对匹配随机删边的稳定优势未建立。双集开发门失败，未开展新validation/QPS。

当前默认仍为WebVid GT10-soft-t1/Yandex GT10-hard的原HNSW。原GT10/E28局部前沿及E32同C8直接收益信号保留；E33只评价此次保骨架删边，不否定全部RL、重连或坐标训练。

## 实际训练与图变化

固定H815/821、默认画像、真实映射、HNSW M16/efConstruction200/efSearch10/seed20260828和原NSG/raw-IP。非保护边独立Bernoulli logit；终局奖励为真实命中差减.1倍相对总NDC变化，每query历史奖励EMA基线、熵正则和Adam600步。4次×600更新、batch128，共307200条新反馈，没有复用C8标签。

原fit20K分train16K/monitor4K，每100步导出静态图选checkpoint；全部样本有历史使用。两个seed的monitor ΔRecall为WebVid+.060/−.030pp、Yandex−.0675/+.050pp，未稳定改善。cal再选主seed后冻结，audit不选模型。

主图WebVid删2301/7530条边，Yandex删3090/9055条边；保留强连通骨架。全部36份checkpoint/selected/随机图已核对，坐标、映射、层级和上层邻接不变。线上只需加载静态图，无策略网络或C8全H扫描。[图结构](entry_method_exploration/20260911_hnsw_edge_rl_v1/figures/graph_structure.svg)。

## 开发与控制

每split1024query，下表为cal选主图；完整两个seed和逐节点同出度随机控制均见报告。

| 数据集/split | RL−原图 ΔRecall pp | 总NDC变化 | RL−随机 ΔRecall pp |
|---|---|---|---|
| WebVid cal | +0.3418 | −0.978% | +0.2832 |
| WebVid audit | +0.1270 | −0.985% | −0.0684 |
| Yandex cal | −0.1660 | −0.424% | +0.1465 |
| Yandex audit | −0.2734 | −0.350% | −0.3125 |

WebVid主图过局部质量/成本门，合并奖励胜随机，保留信号；但audit随机删边+0.1953pp，高于学习图+.1270pp。Yandex门失败，未追加WebVid单集性能矩阵。RL相对随机的全部区间覆盖0；WebVid cal参与seed选择，正区间不能作为独立显著性结论。[开发门](entry_method_exploration/20260911_hnsw_edge_rl_v1/results/development_gate.json)、[开发/成本图](entry_method_exploration/20260911_hnsw_edge_rl_v1/figures/development_and_cost.svg)。

路由NDC约减少18%–19%，NSG NDC增加.19%–.38%，总节省不到1%；没有wall，不能换算QPS。当前结果没有稳定默认替换或端到端性能GO。

## 成本、验收与修正

实际NSG500736、预留500992/1200000，HNSW508608查询单列；20开发点、479680保存输出独立GT复算。训练含固定monitor218.20s，训练总进程255.41s包含加载/基线/保存，线程1；开发CPU15、进程/OMP/BLAS/MKL1。NumPy独立重放全部2400次更新，最大checkpoint误差<2.4e−15；hook/物理删边、原NSG、plain/count与旧默认回归通过。

首版结构预检在任何query/优化前因38个合法单边节点停止，v2将保留最近边数修正为min(2,原出度)，全部原件保留，奖励/收益门不变。[修正](entry_method_exploration/20260911_hnsw_edge_rl_v1/structural_preflight_repair.md)。旧E32和实际依赖SHA保护；更早9211文件仅stat保护，未把它称新SHA验证。旧validation原始输入未hash/解码，held-out未读/hash。

[报告](entry_method_exploration/20260911_hnsw_edge_rl_v1/report.md)、[Excel](entry_method_exploration/20260911_hnsw_edge_rl_v1/chart_data.xlsx)、[最终验收](entry_method_exploration/20260911_hnsw_edge_rl_v1/reviews/final_audit.json)齐备；下一阶段见[s-target](s-target.md)。本轮预算收口，没有排队的训练/ANN任务。
