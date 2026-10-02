# 164 目标预算的状态到查询相对rank表

2026-09-30完成六方法四工作点、三次完整wall及独立核验，状态`STOP_ROUTER_RANK_PARETO_V1`。默认与生产E99不变。

E121按状态输出全H中的固定真实ID；本版按状态输出当前query实际rank1/2/3或默认三入口，两类规则不包含对方。两集E118历史fit4096、原四折3072/1024，目标L为Web1000/1250、Y128/256；每格经验召回不降条件下选最快动作，默认优先。State与全局、训练状态置换、原六特征浅树同监督；所有冻结规则均测完整wall，不按质量删点。

| 数据集/工作点 | Default Recall / QPS | StatePareto Recall / QPS | ΔRecall pp及95%描述区间 | ΔQPS |
|---|---:|---:|---|---:|
| WebVid R1/L1000 | 90.722656% / 419.773 | 90.600586% / 418.127 | -0.122070 [-0.292969, +0.024414] | -0.3922% |
| WebVid R100/L1250 | 90.679443% / 339.305 | 90.649902% / 340.938 | -0.029541 [-0.067139, -0.006836] | +0.4812% |
| Yandex R1/L128 | 91.577148% / 2391.821 | 91.455078% / 2373.680 | -0.122070 [-0.415039, +0.170898] | -0.7585% |
| Yandex R100/L256 | 91.399658% / 1314.626 | 91.302002% / 1322.325 | -0.097656 [-0.197272, -0.016846] | +0.5856% |

两K1均值为负但描述区间跨零；两K100召回区间负且QPS略升，未证明相同Recall更快。State四点召回均未超过置换控制；停止本固定版本的状态/trace/阈值/深度/L/样本/seed扩展。训练经验非降不是外折无损证书，不能把oracle余量当可迁移信息。

全路由、原生核、旧rank/六特征逐位一致；全部在线规则/返回恢复。65536返回行独立集合评分、64规则/所有树分裂复算、19456历史向量恢复、整数bootstrap区间误差0。独立实现为同一agent，非独立人员。594688 NSG、610816 ANN、0新GT/画像/图，原生作业1017.597秒（含加载），查询QPS单独计。全部query历史曝光；四折模型切换不是最终单模型部署，三次wall不构成总体速度区间。

[完整报告](../entry_method_exploration/20260930_theory_until2200_v1/research/router_rank_pareto_v1/report.md) · [冻结协议](../entry_method_exploration/20260930_theory_until2200_v1/research/router_rank_pareto_v1/protocol.md) · [全部统计](../entry_method_exploration/20260930_theory_until2200_v1/research/router_rank_pareto_v1/results/analysis.json) · [独立核验](../entry_method_exploration/20260930_theory_until2200_v1/research/router_rank_pareto_v1/reviews/independent_audit.json)。
