# E176：残差条件补全与完整 wall 曲线

本轮实际完成 160 点、480 个计时批次、800 个事先固定比较、60 个完整候选机制记录，独立整数、原始返回、wall 与 trace 审计已通过。保持 GT10 默认，保留原 M5 研究基线。公共测试为既有已曝光 10K 单角色，不能称为新的可靠确认。

方法：NSG, GT, M5, M5OPT, M5REG96, REGOPT96, WIDE12, M5RES12。两数据集均继承原 raw-IP、K=1/100、L=200/400/800/1000/1200；串行 CPU15 单线程，每点三轮完整正常 Batch 生命周期。新 FIT 是用户授权的独立实际阶段；formal test 不训练。split 的 source/role tuple 继承历史登记，本次只核 frozen TRAIN/public 窗口 exact-byte 查询去重与源行身份，不构成对全部历史角色语义独立性的重新证明。所有数值来自 [metrics.json](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/metrics.json)，全部实测点见 [points.csv](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/points.csv)。

## 曲线与判定范围

![主方法曲线](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/figures/recall_qps_budget_curves.png)

[SVG](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/figures/recall_qps_budget_curves.svg) · [精确绘图字段CSV](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/figures/recall_qps_budget_curves.csv)

![优化与等预算补全对照](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/figures/mechanism_budget_curves.png)

[SVG](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/figures/mechanism_budget_curves.svg) · [精确绘图字段CSV](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/figures/mechanism_budget_curves.csv)

横轴 Recall，纵轴完整 wall QPS 中位数，误差线为三轮实际 [min,max]。线段只引导阅读五个实测 L；没有曲线拟合或中间 L 承诺。同 L Recall 增长仍需检查 QPS，严格同时增长才计 observed joint gain。样本 paired bootstrap 仅描述性，非语义 IID 或全比较同时显著性保证。

## 同 L：原 M5、成本优化与新增补全

| 比较 | 点数 | R 升/平/降 | ΔR pp范围 | QPS 升/平/降 | paired QPS %范围 | 救回成员 | 损伤成员 | 双升点 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M5−GT | 20 | 20/0/0 | [+0.0042, +1.9200] | 0/0/20 | [-4.4541, -0.1235] | 26379 | 0 | 0 |
| M5REG96−M5 | 20 | 17/3/0 | [+0.0000, +0.1600] | 0/0/20 | [-3.2744, -0.1361] | 4138 | 0 | 0 |
| M5OPT−M5 | 20 | 0/20/0 | [+0.0000, +0.0000] | 12/0/8 | [-0.1433, +2.6210] | 0 | 0 | 0 |
| REGOPT96−M5REG96 | 20 | 0/20/0 | [+0.0000, +0.0000] | 19/0/1 | [-0.0104, +2.6053] | 0 | 0 | 0 |
| M5RES12−M5 | 20 | 14/6/0 | [+0.0000, +0.4168] | 10/0/10 | [-0.2805, +1.9260] | 12460 | 0 | 9 |
| M5RES12−M5OPT | 20 | 14/6/0 | [+0.0000, +0.4168] | 2/0/18 | [-0.7402, +0.0321] | 12460 | 0 | 0 |
| M5RES12−M5REG96 | 20 | 5/3/12 | [-0.0500, +0.3051] | 20/0/0 | [+0.0018, +3.9788] | 11533 | 3211 | 5 |
| M5RES12−WIDE12 | 20 | 1/5/14 | [-0.1000, +0.0005] | 15/0/5 | [-0.0682, +0.2946] | 7532 | 8887 | 0 |
| WIDE12−M5OPT | 20 | 15/5/0 | [+0.0000, +0.4454] | 0/0/20 | [-0.7227, -0.0013] | 13815 | 0 | 0 |

缓存优化的效果以 M5OPT/M5、REGOPT96/M5REG96 同一轮返回 ID/score word 的严格身份为前件。新 residual 表的增量同时对原 M5 和同成本基础 M5OPT 报告，不能把缓存节约全算为补全监督的质量贡献。WIDE12 与 M5RES12 在线额外上限都为12，实际到达 X 个数可能不同；PAIR/WIDE 离线条件键数、键目标对数、模型字节与resident字节未强制匹配，差异不能全部归因于 winner 条件化。

四个 dataset/K 分组的主方法同 L 对照：

| 数据集 | K | 比较 | R 升/平/降 | ΔR pp | QPS 升/平/降 | QPS % | 救回 | 损伤 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WebVid2.5M | 1 | M5RES12−M5 | 4/1/0 | [+0.0000, +0.1100] | 0/0/5 | [-0.2805, -0.0504] | 18 | 0 |
| WebVid2.5M | 1 | M5RES12−M5OPT | 4/1/0 | [+0.0000, +0.1100] | 0/0/5 | [-0.1757, -0.0341] | 18 | 0 |
| WebVid2.5M | 1 | M5RES12−GT | 5/0/0 | [+0.9700, +2.0300] | 0/0/5 | [-1.4782, -0.3691] | 682 | 0 |
| WebVid2.5M | 1 | M5RES12−WIDE12 | 0/0/5 | [-0.1000, -0.0100] | 4/0/1 | [-0.0235, +0.2946] | 7 | 28 |
| WebVid2.5M | 100 | M5RES12−M5 | 5/0/0 | [+0.1543, +0.4168] | 5/0/0 | [+0.3769, +1.9260] | 12169 | 0 |
| WebVid2.5M | 100 | M5RES12−M5OPT | 5/0/0 | [+0.1543, +0.4168] | 0/0/5 | [-0.7402, -0.1728] | 12169 | 0 |
| WebVid2.5M | 100 | M5RES12−GT | 5/0/0 | [+0.5677, +1.0476] | 0/0/5 | [-2.6736, -0.4674] | 37303 | 0 |
| WebVid2.5M | 100 | M5RES12−WIDE12 | 0/0/5 | [-0.0286, -0.0232] | 4/0/1 | [-0.0102, +0.0711] | 7356 | 8644 |
| YandexT2I | 1 | M5RES12−M5 | 0/5/0 | [+0.0000, +0.0000] | 1/0/4 | [-0.0747, +0.0126] | 0 | 0 |
| YandexT2I | 1 | M5RES12−M5OPT | 0/5/0 | [+0.0000, +0.0000] | 2/0/3 | [-0.0822, +0.0321] | 0 | 0 |
| YandexT2I | 1 | M5RES12−GT | 5/0/0 | [+0.0100, +0.0900] | 0/0/5 | [-0.8048, -0.1992] | 17 | 0 |
| YandexT2I | 1 | M5RES12−WIDE12 | 0/5/0 | [+0.0000, +0.0000] | 5/0/0 | [+0.0114, +0.0687] | 0 | 0 |
| YandexT2I | 100 | M5RES12−M5 | 5/0/0 | [+0.0022, +0.0120] | 4/0/1 | [-0.0977, +0.5268] | 273 | 0 |
| YandexT2I | 100 | M5RES12−M5OPT | 5/0/0 | [+0.0022, +0.0120] | 0/0/5 | [-0.5995, -0.1272] | 273 | 0 |
| YandexT2I | 100 | M5RES12−GT | 5/0/0 | [+0.0064, +0.0374] | 1/0/4 | [-2.0780, +0.1767] | 837 | 0 |
| YandexT2I | 100 | M5RES12−WIDE12 | 1/0/4 | [-0.0018, +0.0005] | 2/0/3 | [-0.0682, +0.1784] | 169 | 215 |

## 跨 L：逐个原始工作点的实际双升

预锁跨 L 比较 240 个，实际 observed joint gain 12 个。所有都是较小预算候选方法对较大预算 GT；以下保留两端真实方法和预算身份，不插值。

| 数据集 | K | 候选 | 原始参照 | ΔR pp | paired QPS % | 救回 | 损伤 | 贡献归属 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WebVid2.5M | 1 | M5 L800 | GT L1000 | +0.2800 | +23.9210 | 102 | 74 | 原M5此预算已双升 |
| WebVid2.5M | 1 | M5OPT L800 | GT L1000 | +0.2800 | +23.9194 | 102 | 74 | 原M5此预算已双升 |
| WebVid2.5M | 1 | M5REG96 L800 | GT L1000 | +0.3000 | +23.6328 | 104 | 74 | 原M5此预算已双升 |
| WebVid2.5M | 1 | REGOPT96 L800 | GT L1000 | +0.3000 | +23.6917 | 104 | 74 | 原M5此预算已双升 |
| WebVid2.5M | 1 | WIDE12 L800 | GT L1000 | +0.3000 | +23.7856 | 104 | 74 | 原M5此预算已双升 |
| WebVid2.5M | 1 | M5RES12 L800 | GT L1000 | +0.2900 | +23.8198 | 103 | 74 | 原M5此预算已双升 |
| WebVid2.5M | 1 | M5 L1000 | GT L1200 | +0.3500 | +19.0769 | 97 | 62 | 原M5此预算已双升 |
| WebVid2.5M | 1 | M5OPT L1000 | GT L1200 | +0.3500 | +19.1081 | 97 | 62 | 原M5此预算已双升 |
| WebVid2.5M | 1 | M5REG96 L1000 | GT L1200 | +0.3700 | +18.9343 | 99 | 62 | 原M5此预算已双升 |
| WebVid2.5M | 1 | REGOPT96 L1000 | GT L1200 | +0.3700 | +18.9300 | 99 | 62 | 原M5此预算已双升 |
| WebVid2.5M | 1 | WIDE12 L1000 | GT L1200 | +0.3800 | +19.0919 | 99 | 61 | 原M5此预算已双升 |
| WebVid2.5M | 1 | M5RES12 L1000 | GT L1200 | +0.3600 | +19.1083 | 97 | 61 | 原M5此预算已双升 |

完整全部比较（含非双升、损伤与描述性区间）：[comparisons.csv](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/comparisons.csv)。新增双升分类只表示当前公开工作点的观察，不表示新 held-out confirmation 或默认替换。

## 候选机制与 U 外真实救回、损伤

| 方法 | 数据集 | K | C均值 | X均值 | 救回vsM5 | 损伤vsM5 | M5U外救 | M5U外损 | 旧TRAINU外救 | 旧TRAINU外损 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M5REG96 | WebVid2.5M | 1 | 23.8171 | 11.9011 | 30 | 0 | 19 | 0 | 0 | 0 |
| M5REG96 | WebVid2.5M | 100 | 23.5319 | 12.6878 | 3499 | 0 | 2645 | 0 | 100 | 0 |
| M5REG96 | YandexT2I | 1 | 23.9906 | 61.3383 | 4 | 0 | 4 | 0 | 2 | 0 |
| M5REG96 | YandexT2I | 100 | 23.9174 | 62.2268 | 605 | 0 | 591 | 0 | 206 | 0 |
| WIDE12 | WebVid2.5M | 1 | 23.8171 | 3.6194 | 39 | 0 | 24 | 0 | 0 | 0 |
| WIDE12 | WebVid2.5M | 100 | 23.5319 | 11.5656 | 13457 | 0 | 9086 | 0 | 0 | 0 |
| WIDE12 | YandexT2I | 1 | 23.9906 | 0.0506 | 0 | 0 | 0 | 0 | 0 | 0 |
| WIDE12 | YandexT2I | 100 | 23.9174 | 11.9634 | 319 | 0 | 304 | 0 | 0 | 0 |
| M5RES12 | WebVid2.5M | 1 | 23.8171 | 1.4505 | 18 | 0 | 11 | 0 | 0 | 0 |
| M5RES12 | WebVid2.5M | 100 | 23.5319 | 11.3503 | 12169 | 0 | 8642 | 0 | 0 | 0 |
| M5RES12 | YandexT2I | 1 | 23.9906 | 0.0112 | 0 | 0 | 0 | 0 | 0 | 0 |
| M5RES12 | YandexT2I | 100 | 23.9174 | 10.5032 | 273 | 0 | 271 | 0 | 0 | 0 |

逐 K/L 机制见 [mechanisms.csv](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/mechanisms.csv)，完整已保存 trace 的独立成员诊断见 [independent_mechanisms.csv](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/independent_result_audit/independent_mechanisms.csv)。U 外损伤直接由 (原M5返回−实际返回)∩GT_K 无条件累加，未假定为0。

pair 表按 (route,原C逐行winner) 条件，route 表按 route；同一 winner 可重复出现在多个路由行。每行最多4目标、三行合计最多12；去原R/全部C/已出现X，pair miss 空，不回退 route。训练残差是 GT_K−原 M5_final_K，使用合法冻结 TRAIN，条件键要求至少两个 distinct TRAIN query 支持；表由实际残差目标的整数联合覆盖编译。旧 REG 扩展普通图邻接，与此目标支持机制不同。表质量观察只能支持本轮实际冻结模型，不能声称泛化定理。

## 实际费用、资源与身份

| 阶段收据 | 实际状态 | exit | 实际 elapsed 秒 | 来源 |
| --- | --- | --- | --- | --- |
| reviews/build.json | PASS_E176_NATIVE_BUILD | 0 | 11.513078 | [receipt](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/build.json) |
| reviews/fit_build.json | PASS_BUILD_FIT | 0 | 7.098643 | [receipt](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/fit_build.json) |
| reviews/fit_preflight.json | PASS_TRAIN_IDENTITY_ALIGNMENT_AND_DISJOINT_PUBLIC_WINDOWS | — | 0.286051 | [receipt](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/fit_preflight.json) |
| reviews/data_preflight.json | PASS_E176_ALL_MODELS_FROZEN_AND_PUBLIC_SOURCE_IDENTITY | — | 0.035131 | [receipt](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/data_preflight.json) |
| reviews/native_qualification.json | PASS_E176_N16_ORACLES_AND_FROZEN_ORIGINAL_WORD_REGRESSION | — | 未计量/None | [receipt](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/native_qualification.json) |
| reviews/evaluation_execution.json | PASS_E176_EVALUATE_PROCESS | 0 | 145.978025 | [receipt](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/evaluation_execution.json) |
| reviews/independent_audit_execution.json | PASS_E176_INDEPENDENT_AUDIT_SCHEMA_V2_PROCESS | 0 | 81.193447 | [receipt](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/independent_audit_execution.json) |
| reviews/plot_curves_wrapper_execution.json | PASS_E176_PLOT_CURVES_V2_PROCESS | 0 | 1.265668 | [receipt](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/plot_curves_wrapper_execution.json) |
| reviews/plot_curves_execution.json | PASS_E176_PRECOMPUTED_DYNAMIC_BUDGET_CURVES | — | 1.192732 | [receipt](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/plot_curves_execution.json) |
| reviews/fit_execution.webvid2_5m_light_v1.json | PASS_ADDITIONAL_FIT_COMPLETE_WITHIN_900S | — | 469.143610 | [receipt](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/fit_execution.webvid2_5m_light_v1.json) |
| reviews/fit_execution.yandex_t2i_official10M_ip_v1.json | PASS_ADDITIONAL_FIT_COMPLETE_WITHIN_900S | — | 472.986268 | [receipt](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/fit_execution.yandex_t2i_official10M_ip_v1.json) |

native 单线程阶段：

每数据集实际新增 FIT wholewall 与历史债：

| 数据集 | 历史TRAIN秒 | 本次增量秒 | 本次cap秒 | 累计TRAIN秒 | native subprocess秒 | compiler subprocess秒 |
| --- | --- | --- | --- | --- | --- | --- |
| WebVid2.5M | 21724.972836 | 469.143610 | 900 | 22194.116446 | 435.726580 | 33.416477 |
| YandexT2I | 15589.205720 | 472.986268 | 900 | 16062.191988 | 448.634244 | 24.351196 |

| 数据集 | role | 整job wall秒 | exit | 观测线程 | sampled峰RSS bytes |
| --- | --- | --- | --- | --- | --- |
| WebVid2.5M | public_test | 6970.796179 | 0 | 1 | 9328279552 |
| YandexT2I | public_test | 7089.322895 | 0 | 1 | 17751719936 |

run_state.training_increment_seconds = 942.1298777130032；与 formal test no_training 分开。whole FIT budget费用含 native/compiler 子进程的完整生命周期，不包含其后收尾 manifest hash 与行政收据写入；该边界按实际阶段收据保留。没有记录 elapsed 的失败项保留 None，不当0。建表、compiler、预检、smoke、native、评价、独审、绘图按各实际阶段列账；wrapper 与 inner 图 receipt 是同一阶段包含关系，不重复相加。旧 TRAIN、原模型和既有构图费用是历史债；本轮完整 new FIT 与 startup layout/setup 成本不能归为零或隐藏。

实际模型容量（直接保存的 compiler 字段；在线12上限不等于离线容量相等）：

| 数据集 | K | L | family | eligible keys | populated keys | key-target pairs | bytes | resident bytes | support≥queries |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WebVid2.5M | 1 | 200 | pair | 4922 | 1089 | 1916 | 30492 | 30588 | 2 |
| WebVid2.5M | 1 | 200 | route | 769 | 536 | 1507 | 15008 | 15104 | 2 |
| WebVid2.5M | 1 | 400 | pair | 4922 | 604 | 963 | 16912 | 17008 | 2 |
| WebVid2.5M | 1 | 400 | route | 769 | 341 | 744 | 9548 | 9644 | 2 |
| WebVid2.5M | 1 | 800 | pair | 4920 | 116 | 251 | 3248 | 3344 | 2 |
| WebVid2.5M | 1 | 800 | route | 769 | 48 | 137 | 1344 | 1440 | 2 |
| WebVid2.5M | 1 | 1000 | pair | 4899 | 102 | 221 | 2856 | 2952 | 2 |
| WebVid2.5M | 1 | 1000 | route | 769 | 44 | 126 | 1232 | 1328 | 2 |
| WebVid2.5M | 1 | 1200 | pair | 4881 | 93 | 206 | 2604 | 2700 | 2 |
| WebVid2.5M | 1 | 1200 | route | 769 | 43 | 121 | 1204 | 1300 | 2 |
| WebVid2.5M | 100 | 200 | pair | 4938 | 4938 | 19738 | 138264 | 138360 | 2 |
| WebVid2.5M | 100 | 200 | route | 769 | 769 | 3076 | 21532 | 21628 | 2 |
| WebVid2.5M | 100 | 400 | pair | 4944 | 4938 | 19715 | 138264 | 138360 | 2 |
| WebVid2.5M | 100 | 400 | route | 769 | 769 | 3076 | 21532 | 21628 | 2 |
| WebVid2.5M | 100 | 800 | pair | 4952 | 4934 | 19614 | 138152 | 138248 | 2 |
| WebVid2.5M | 100 | 800 | route | 769 | 767 | 3065 | 21476 | 21572 | 2 |
| WebVid2.5M | 100 | 1000 | pair | 4929 | 4900 | 19426 | 137200 | 137296 | 2 |
| WebVid2.5M | 100 | 1000 | route | 769 | 765 | 3056 | 21420 | 21516 | 2 |
| WebVid2.5M | 100 | 1200 | pair | 4908 | 4868 | 19230 | 136304 | 136400 | 2 |
| WebVid2.5M | 100 | 1200 | route | 769 | 765 | 3056 | 21420 | 21516 | 2 |
| YandexT2I | 1 | 200 | pair | 5440 | 12 | 14 | 336 | 432 | 2 |
| YandexT2I | 1 | 200 | route | 821 | 9 | 14 | 252 | 348 | 2 |
| YandexT2I | 1 | 400 | pair | 5429 | 7 | 7 | 196 | 292 | 2 |
| YandexT2I | 1 | 400 | route | 821 | 7 | 7 | 196 | 292 | 2 |
| YandexT2I | 1 | 800 | pair | 5395 | 5 | 5 | 140 | 236 | 2 |
| YandexT2I | 1 | 800 | route | 821 | 5 | 5 | 140 | 236 | 2 |
| YandexT2I | 1 | 1000 | pair | 5390 | 4 | 4 | 112 | 208 | 2 |
| YandexT2I | 1 | 1000 | route | 821 | 4 | 4 | 112 | 208 | 2 |
| YandexT2I | 1 | 1200 | pair | 5386 | 3 | 3 | 84 | 180 | 2 |
| YandexT2I | 1 | 1200 | route | 821 | 3 | 3 | 84 | 180 | 2 |
| YandexT2I | 100 | 200 | pair | 5460 | 5448 | 21661 | 152544 | 152640 | 2 |
| YandexT2I | 100 | 200 | route | 821 | 820 | 3280 | 22960 | 23056 | 2 |
| YandexT2I | 100 | 400 | pair | 5376 | 5260 | 20260 | 147280 | 147376 | 2 |
| YandexT2I | 100 | 400 | route | 821 | 820 | 3279 | 22960 | 23056 | 2 |
| YandexT2I | 100 | 800 | pair | 5286 | 4708 | 16832 | 131824 | 131920 | 2 |
| YandexT2I | 100 | 800 | route | 821 | 820 | 3274 | 22960 | 23056 | 2 |
| YandexT2I | 100 | 1000 | pair | 5281 | 4423 | 15296 | 123844 | 123940 | 2 |
| YandexT2I | 100 | 1000 | route | 821 | 818 | 3264 | 22904 | 23000 | 2 |
| YandexT2I | 100 | 1200 | pair | 5273 | 4150 | 13904 | 116200 | 116296 | 2 |
| YandexT2I | 100 | 1200 | route | 821 | 816 | 3245 | 22848 | 22944 | 2 |

优化布局初始化登记：

```json
[
  {
    "dataset": "webvid2_5m_light_v1",
    "new_FIT_and_compiler_actual_fields": {
      "compiler_elapsed_seconds": 33.352583152998704,
      "native_response_generation_elapsed_seconds": 435.615852128,
      "compiler_max_seconds_remainder": 464.27326340500076,
      "source_hash_seconds": 0.10998169400045299,
      "label_decode_seconds": 0.010803268000017852
    },
    "manifest": "/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/models/webvid2_5m_light_v1/compile_manifest.json"
  },
  {
    "dataset": "webvid2_5m_light_v1",
    "startup_fields": {
      "complete_distinct_posting_resident_bytes": 59771,
      "complete_posting_completion_layout_resident_bytes": 967935,
      "startup_seconds": 5.105338978
    },
    "optimized_layouts": [
      {
        "method": "REGOPT96",
        "resident_bytes": 26232,
        "startup_graph_reads": 369718,
        "startup_seconds": 0.001652441,
        "startup_trimmed_slots": 363484
      }
    ]
  },
  {
    "dataset": "yandex_t2i_official10M_ip_v1",
    "new_FIT_and_compiler_actual_fields": {
      "compiler_elapsed_seconds": 24.291415198000323,
      "native_response_generation_elapsed_seconds": 448.403293138,
      "compiler_max_seconds_remainder": 451.3653483630005,
      "source_hash_seconds": 0.09182000299915671,
      "label_decode_seconds": 0.011536410998814972
    },
    "manifest": "/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/models/yandex_t2i_official10M_ip_v1/compile_manifest.json"
  },
  {
    "dataset": "yandex_t2i_official10M_ip_v1",
    "startup_fields": {
      "complete_distinct_posting_resident_bytes": 60041,
      "complete_posting_completion_layout_resident_bytes": 876361,
      "startup_seconds": 12.592677017
    },
    "optimized_layouts": [
      {
        "method": "REGOPT96",
        "resident_bytes": 26424,
        "startup_graph_reads": 253990,
        "startup_seconds": 0.001706549,
        "startup_trimmed_slots": 247422
      }
    ]
  }
]
```

资源冻结上限：产物累计1536MiB、最小free1GiB、RSS64GiB、每formal dataset job10800秒；实际占用与采样边界以冻结 [protocol.md](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/protocol.md) 与 [run_state.json](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/run_state.json) 原始资源收据为准；所有产物保留，不用删除失败数据使费用或磁盘账变小。报告生成耗时由独立 wrapper 后续落账，本报告生成时不伪造自身最终 elapsed。

## 限界与停止/保留

全量保存的 normal untimed plain 已在同一 pass 完成独立 fresh scalar/linear oracle 与 GT main packet word 校验；本轮没有第二次整批 native replay。OPT 分支另外与相应原方法的完整 packet word 身份核对，缓存 R 在 untimed qualifier 检查 n×K words。固定256 count 查询的 post/region计数不能写为全10K NDC；完整 oldREG trace 与两种 completion trace 分开，REGOPT 不另存 trace，依其完整原方法输出身份与 native oracle 限界。三轮 timed packet 不保存，不能声称逐 query timed bit parity。

仍保留默认 GT10、原 M5 与同步计时对照。结果仅是当前公开已曝光两数据集、单一10K角色、五档L、冻结模型上的实际信号；没有新 confirmation、没有多模态几何因果证明、没有跨数据集或未测预算推广保证。未过严格 Recall/QPS 双升的点记为取舍；即使通过公开点 observed joint gain，也不自动替换生产默认。

独审来源：[independent audit](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/independent_result_audit/report.json)；科学点/比较/候选整数来自其绑定 metrics SHA `9e9d34ca9a4e388ed9f0fb352710f079f78a5128a63189e2cd5bce7e684b7baf`。图与报告只呈现这些保存字段，无新 ANN、fit、distance、GT 或 bootstrap。
