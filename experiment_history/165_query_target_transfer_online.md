# 165 查询→真实目标迁移与同容量目标侧控制

2026-09-30完成。`STOP_QUERY_TARGET_TRANSFER_V1`；原默认与生产E99保持。主目标为完整线上Recall–QPS综合收益。

原20K训练query/GT1与E105历史4096评价向量字节分离。相似训练query的GT1作入口，可落在原H外；配投回H、同20K目标HNSW、配对置换、原三入口/原rank1五控制。四普通图在任何评价前构建冻结，真实K1/K100、原L/底图/主搜索不变，CPU15实际单线程、三轮完整wall。没有读今日151/157新源或held-out。

| 工作点 | Default3 Recall / QPS | QueryTarget1 Recall / QPS | ΔRecall pp及95%描述区间 | ΔQPS |
|---|---:|---:|---|---:|
| WebVid R1/L1000 | 90.454102% / 423.710 | 90.551758% / 416.559 | +0.097656 [-0.292969, +0.488281] | -1.6878% |
| WebVid R100/L1250 | 90.581543% / 335.485 | 90.591064% / 332.523 | +0.009521 [-0.063477, +0.083252] | -0.8828% |
| Yandex R1/L128 | 90.625000% / 2386.805 | 90.112305% / 2260.786 | -0.512695 [-1.098633, +0.097656] | -5.2799% |
| Yandex R100/L256 | 91.044434% / 1329.735 | 90.688232% / 1276.806 | -0.356201 [-0.634033, -0.082269] | -3.9804% |

四点主候选均更慢；Web质量微正但不确定，Y两点均值负、K100描述区间负。Web配对相对置换有局部信息，仍不足以超过默认和目标侧控制。目标侧Web R1为90.991211%/420.254 QPS，相对默认+0.537109pp [0.122070,0.952148]、−0.8156%QPS，50救回/28损伤，保留质量/速度取舍；未证同Recall更快或跨集稳定。

完整98304返回行独立集合评分、全40K训练GT1/hub映射、四图80K向量/结构、历史Default3/全部重复/plain/count/E99、slot/区间及额外几何诊断通过。独立实现为同一agent，非独立人员。三轮速度与历史开发bootstrap均有适用边界。QueryTarget主图NDC四点均未减少，额外路由没有被主搜索节省抵消。

新397440 NSG/397056 ANN/4小图，0新GT/画像；原生测量作业674.300秒，编译构图24.047秒。全部原件保留。停止固定迁移版本的实例数、ef、近邻数、GT数量和模型调参；局部控制收益归控制，不认领为query条件信息。

[完整报告](../entry_method_exploration/20260930_theory_until2200_v1/research/query_target_transfer_v1/report.md) · [协议](../entry_method_exploration/20260930_theory_until2200_v1/research/query_target_transfer_v1/protocol.md) · [理论](../entry_method_exploration/20260930_theory_until2200_v1/research/query_target_transfer_v1/theory.md) · [统计](../entry_method_exploration/20260930_theory_until2200_v1/research/query_target_transfer_v1/results/analysis.json) · [核验](../entry_method_exploration/20260930_theory_until2200_v1/research/query_target_transfer_v1/reviews/independent_audit.json)。
