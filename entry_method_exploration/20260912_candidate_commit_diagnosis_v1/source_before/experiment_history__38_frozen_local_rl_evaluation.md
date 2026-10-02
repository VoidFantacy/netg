# 38. E49 冻结局部画像开发与性能

2026-09-12，`COMPLETE_FROZEN_LOCAL_RL_EVALUATION_NO_DUAL_FRONTIER_GAIN`，开发门`STOP_DUAL_DEVELOPMENT_GATE`。0新训练，80个质量/性能点和250轮plain wall完成。

| 数据集 | cal选定模型 | cal ΔR pp | audit ΔR pp [配对95%区间] | audit gain/loss hits | audit改善/损伤query | audit Δtotal NDC % |
|---|---|---:|---:|---:|---:|---:|
| WebVid | rl_20260921 | +0.0391 | +0.0879 [+0.0000,+0.2344] | 9/0 | 3/0 | +0.1013 |
| WebVid | es_20260921 | +0.0684 | +0.0977 [+0.0000,+0.2930] | 10/0 | 1/0 | +0.0475 |
| Yandex | rl_20260922 | +0.0781 | +0.0000 [+0.0000,+0.0000] | 0/0 | 0/0 | -0.0092 |
| Yandex | es_20260922 | +0.0391 | +0.0000 [+0.0000,+0.0000] | 0/0 | 0/0 | -0.0158 |

冻结RL的局部正值只在WebVid部分工作点保留，没有形成双集Recall–QPS改进。WebVid RL在audit L128新增9个命中、无损伤，但L256/400/800各丢4个命中；Yandex选中RL和ES在五L全部没有命中变化。WebVid RL相同Recall的三个描述插值位置为+0.436%、−1.095%、−0.743%，不构成整条曲线提高。五轮QPS小差异方向不一致，不能归为稳定性能优势。

ES的局部结果也保留：WebVid在L64/128/256各新增10命中、无损伤，L400/800相同；L128失败从11降到10。RL L128失败仍11，Yandex所选两模型五L失败与基线完全相同。WebVid的配对Recall区间下界均为0，收益query很少，不能据正均值宣称稳定泛化。E47 monitor没有显示WebVid ES正值，独立开发却有该局部信号，说明不能以某一内部统一门替代所有后续固定模型事实。

预锁可比开发门仍为STOP：两集RL cal +0.0391/+0.0781pp均未到+0.1pp，且Yandex audit为0。保持E47统一训练门原身份，E49也不替换默认。原默认WebVid GT10-soft-t1 / Yandex GT10-hard保留。

## 完整五L所选候选结果

相对当前GT10起点。全部NSG/Fast/基线原值、所有seed cal/audit及五轮范围见CSV，不仅报告以下所选模型。

| 数据集 | 模型 | L | ΔRecall pp | QPS中位数 | ΔQPS % | 失败数/1024 |
|---|---|---:|---:|---:|---:|---:|
| WebVid | RL | 64 | +0.0000 | 4162.23 | -0.003 | 32 |
| WebVid | RL | 128 | +0.0879 | 2308.59 | -0.149 | 11 |
| WebVid | RL | 256 | -0.0391 | 1233.99 | -0.685 | 6 |
| WebVid | RL | 400 | -0.0391 | 806.90 | -0.193 | 1 |
| WebVid | RL | 800 | -0.0391 | 408.50 | -0.165 | 0 |
| WebVid | ES | 64 | +0.0977 | 4171.63 | +0.223 | 31 |
| WebVid | ES | 128 | +0.0977 | 2310.03 | -0.087 | 10 |
| WebVid | ES | 256 | +0.0977 | 1241.54 | -0.077 | 5 |
| WebVid | ES | 400 | +0.0000 | 806.67 | -0.222 | 1 |
| WebVid | ES | 800 | +0.0000 | 409.08 | -0.022 | 0 |
| Yandex | RL | 64 | +0.0000 | 4132.56 | +0.013 | 38 |
| Yandex | RL | 128 | +0.0000 | 2309.85 | -0.348 | 19 |
| Yandex | RL | 256 | +0.0000 | 1262.04 | +0.153 | 11 |
| Yandex | RL | 400 | +0.0000 | 833.97 | -0.127 | 9 |
| Yandex | RL | 800 | +0.0000 | 435.00 | +0.087 | 6 |
| Yandex | ES | 64 | +0.0000 | 4131.28 | -0.018 | 38 |
| Yandex | ES | 128 | +0.0000 | 2294.75 | -1.000 | 19 |
| Yandex | ES | 256 | +0.0000 | 1269.29 | +0.729 | 11 |
| Yandex | ES | 400 | +0.0000 | 834.59 | -0.053 | 9 |
| Yandex | ES | 800 | +0.0000 | 433.72 | -0.208 | 6 |

## 方法与核验

全部E47 selected模型在cal前冻结，fit各128query对train0:64和monitor4096:4160逐位恢复；cal按原平均U、较低total NDC、较小seed选择并冻结，再开启audit，未依audit换seed。两开发池各1024，source IDs与train/monitor5120及彼此不交，但历史研究已使用这些开发数据，不是项目盲测。所有模型仍raw query→一次普通HNSW→三个真实入口→原NSG。

固定五方法×两dataset×五L，原E37同SHA静态binary；CPU15实际进程/OMP/BLAS/MKL1，方法和dataset串行，每点一次warmup和五轮轮换完整plain wall。计时包括路由/映射/原NSG/预分配输出，GT/count/I/O/load/build在外；L128分项独测不代替总wall。GT在所有原始返回产生之后打开评分。失败严格GT10零命中，timing重复不是新质量样本。

实际423680 NSG，8job均完整预留并完成、无失败查询job；累计460.890s，含加载/输出/核验而非线上wall。独立72960集合评分/命中mask、1280原kernel parity、1280 fit checkpoint位恢复、4096旧基线回归、6144 audit128→curve128位恢复，全部跨L图/入口及五轮/plain/count一致。所有source/model/原E37–E48/native SHA保持。

准备阶段仅一次manifest字段兼容错误：E48冻结清单没有旧helper强制mtime字段，查询前修正为有该字段时检查；bytes/SHA始终检查，0搜索损耗，原记录保留。0新GT/训练/原validation/held-out访问，默认未替换。

## 接续与最终交付

接着执行已写明的E50原轨迹诊断：固定1600动作前状态/12800已测候选，比较包含不动的原J-best、有限hit-best和实际Adam均值，检查“有正候选而确定更新无质量响应”的比例，0新搜索。若证据支持，再做独立步长/方向反事实或连续有限候选择优提交对照；后者必须明确称贪心局部搜索，不包装成RL，也不能使用旧分岔状态的反馈。

用户已延长到22:00并追加最终比较要求：最后将冻结的最佳候选与NSG、原Fast、FastGT10-hard同批测QPS/Recall/失败率，WebVid另列GT10-soft匹配起点。Fast身份已由历史23和E34原配置核对。E49的WebVid矩阵缺hard基线，不能称已经完成最终要求；最终阶段另冻完整矩阵及模型选择规则。21:15前为最终比较留出窗口，21:40停止新查询，22:00收口。

[协议](../entry_method_exploration/20260912_frozen_local_rl_evaluation_v1/protocol.md)、[全部点](../entry_method_exploration/20260912_frozen_local_rl_evaluation_v1/results/points.csv)、[配对区间](../entry_method_exploration/20260912_frozen_local_rl_evaluation_v1/results/paired.csv)、[逐query](../entry_method_exploration/20260912_frozen_local_rl_evaluation_v1/results/query_results.csv)、[五轮计时](../entry_method_exploration/20260912_frozen_local_rl_evaluation_v1/results/timings.csv)、[描述插值](../entry_method_exploration/20260912_frozen_local_rl_evaluation_v1/results/frontier_interpolation.csv)、[原开发门](../entry_method_exploration/20260912_frozen_local_rl_evaluation_v1/results/development_gate.json)、[输出核验](../entry_method_exploration/20260912_frozen_local_rl_evaluation_v1/reviews/output_verification.json)、[合同核验](../entry_method_exploration/20260912_frozen_local_rl_evaluation_v1/reviews/contract_verification.json)、[Recall–QPS](../entry_method_exploration/20260912_frozen_local_rl_evaluation_v1/figures/recall_qps.svg)、[相对变化](../entry_method_exploration/20260912_frozen_local_rl_evaluation_v1/figures/quality_cost_changes.svg)。
