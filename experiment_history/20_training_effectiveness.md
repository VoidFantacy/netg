# 20 有界训练有效性检查（E31）

2026-09-11完成，状态`TRAINING_EFFECTIVENESS_COMPLETE_OPTIMIZATION_IMPROVED_CACHE_GATE_FAILED`。用户同意一次CPU训练合计10分钟内的优化检查；同一模型、教师、正则和数据固定，若缓存实际收益不达标则停止。结果是优化目标进一步下降，WebVid局部收益增大，Yandex没有有效提升，预设双集缓存门失败。

## 疑点、控制和实现

[E30](19_equivalent_teacher_sets.md)使用Adam.003/80步最后点，初始目标大幅上冲，末段仍下降；这不足以认定bug，也未排除优化余地。E31逐字复制set_loss、triple_scores、归一化共享A、加载与诊断核心，复用最高hits且最低graph NDC的并列G和唯一T0。模型W=normalize(P+AP)、λ100、τ.05、margin.1、A=0、CPU8/float64/fullfit20k/seed20260911不变。

只采用一套预锁优化日程：前20步3e-5→3e-4，至200步保持，之后余弦衰减至1200步3e-6。checkpoint只由fit总目标最低决定，保留最后点作只读敏感性诊断。两集single/multi共4次，从初始化重新训练；不改变老师、模型容量或正则，不按缓存效用挑有利迭代。90个枚举/有限差分及共享A梯度测试通过，旧4个模型独立恢复，新4个选中/最后点共8份NumPy目标与导出核验通过。

## 实际优化和效用

| 数据集 | 教师 | 原80步总目标 | 新选中总目标 | 变化 | 选中步 | 末100步最佳目标再降 |
|---|---|---|---|---|---|---|
| WebVid2.5M | single | 0.533651 | 0.516364 | -3.239% | 1200 | 0.001263% |
| WebVid2.5M | multi | 0.526664 | 0.508577 | -3.434% | 1200 | 0.001306% |
| Yandex10M IP | single | 0.930740 | 0.928057 | -0.288% | 1199 | 0.000043% |
| Yandex10M IP | multi | 0.925134 | 0.922398 | -0.296% | 1197 | 0.000026% |

末段变化小不等于全局收敛，单/多教师目标绝对值不能直接排名。Yandex单教师1199/1200目标仅差约1e-8，离散C8选择仍改变109个query，缓存Recall差0.0100pp；只读检查不更改选点规则。新方案没有出现原第1步的大幅上冲。

| 数据集 | 画像 | 缓存Recall@10 | 相对锚点pp | 相对原同教师pp | 图NDC变化 |
|---|---|---|---|---|---|
| WebVid2.5M | single | 75.3820% | +0.1945 | +0.0940 | -0.1426% |
| WebVid2.5M | multi | 75.3990% | +0.2115 | +0.0910 | -0.1407% |
| Yandex10M IP | single | 90.1775% | -0.0040 | -0.0055 | -0.0241% |
| Yandex10M IP | multi | 90.1775% | -0.0040 | -0.0025 | -0.0288% |

表中统一float32画像，在已测56个C8完整三元组中选最大分数，再查原真实L128/K10标签。基准为同C8域anchor选择，不是原实际HNSW入口。WebVid multi相对原80步增加0.0910pp（fit配对bootstrap95%区间+0.0455至+0.1340），来自净增182个命中，其中headroom组171；Yandex为−0.0025pp（−0.0185至+0.0110），无有效提升，不是稳定退化证据。

## 阶段门与边界

协议要求同一种cell双集缓存Recall≥anchor+0.20pp、胜原同cell、graph NDC≤+1%，全H已知覆盖≥99.5%且新下界−anchor上界≥+0.20pp。WebVid multi在C8有+0.2115pp，但全H有14个未知query，保守净界+0.1610pp；Yandex全部精确top3已知，依然−0.0040pp。即使忽略WebVid保守界，Yandex也会使双集门失败。状态`STOP_CACHE_UTILITY_GATE`，未进入新fit/cal/audit实际HNSW→NSG或validation/QPS。

已测query上的缓存标签不是新端到端性能；未知组合只是上下界计算，不作为零效用标签。全部query有历史使用，一个H/图/seed/固定λ；无全局最优证书、独立盲测或held-out读取/hash。该结论收口当前固定教师/共享linear/λ100优化支线，不反推所有共享画像不可能有效，也不抹掉GT10既有正信号。

## 成本、结论与证据

4次训练4800更新，训练阶段302.73秒，低于600秒合计上限。新标签0、复用224万逻辑标签；新HNSW查询/原NSG调用/新QPS点均0。E30及原保护链9098个旧文件保持身份，根文档前版本另存source_before。默认保留WebVid GT10 soft/Yandex GT10 hard，依据E30既有完整同批曲线。

后续优先明确原GT10的独立复现与公平基线问题、输入身份和预算；本轮不自动追加训练或held-out。当前下一步见[s-target](../s-target.md)。

- [完整报告](../entry_method_exploration/20260911_training_effectiveness_v1/report.md)、[预锁协议](../entry_method_exploration/20260911_training_effectiveness_v1/protocol.md)、[缓存门](../entry_method_exploration/20260911_training_effectiveness_v1/results/cache_gate.json)、[状态](../entry_method_exploration/20260911_training_effectiveness_v1/state.json)。
- [优化与效用图](../entry_method_exploration/20260911_training_effectiveness_v1/figures/optimization_and_utility.svg)、[缓存收益图](../entry_method_exploration/20260911_training_effectiveness_v1/figures/cache_utility.svg)、[Excel](../entry_method_exploration/20260911_training_effectiveness_v1/chart_data.xlsx)。
- [模型恢复/梯度检查](../entry_method_exploration/20260911_training_effectiveness_v1/reviews/preflight.json)、[独立模型与缓存核验](../entry_method_exploration/20260911_training_effectiveness_v1/reviews/model_and_cache_verification.json)、[停机敏感性](../entry_method_exploration/20260911_training_effectiveness_v1/reviews/checkpoint_diagnostics.json)、[最终验收](../entry_method_exploration/20260911_training_effectiveness_v1/reviews/final_audit.json)。
