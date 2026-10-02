# E66 单个小索引的多画像开发结果

固定真实H，每hub保留原P和两份加权GT10 query模态；三slot一真实hub。一次HNSW取7slot，按距离/slot序去重为3真实入口，再执行原NSG。duplicate3P为同容量重复P控制；两模式的随机分组作用未隔离。所有新模型及门均在查询前冻结。

| 数据集 | 合格双模态 / H | fit净命中 | aux净命中 | aux两半 | aux失败净增 | aux相对duplicate净命中 | 开发门 |
|---|---:|---:|---:|---|---:|---:|---|
| webvid2_5m_light_v1 | 478/815 | -496 | -106 | [-38, -68] | +13 | +130 | FAIL |
| yandex_t2i_official10M_ip_v1 | 623/821 | +164 | +49 | [-14, 63] | -4 | +182 | FAIL |

此门是开发质量/成本信号，未测完整wall，不能由同L Recall或NDC宣称性能改进。两个集合均历史暴露，aux7952全部属于辅助选型训练反馈；fit包含旧train/monitor，基础Fast30K和旧E10亦使用这些源行。E34最终validation及held-out未进入本阶段。

| 数据集 / 集合 / 比较 | ΔRecall pp | 成员找回 / 丢失 | 失败救回 / 新增 | 入口变化数 | 总NDC变化 |
|---|---:|---:|---:|---:|---:|
| webvid2_5m_light_v1 / fit / duplicate3P−baseline | -0.4520 | 1604 / 2508 | 67 / 152 | 7277 | +0.832% |
| webvid2_5m_light_v1 / fit / mode3P−baseline | -0.2480 | 2653 / 3149 | 102 / 137 | 14932 | +0.349% |
| webvid2_5m_light_v1 / fit / mode3P−duplicate3P | +0.2040 | 3597 / 3189 | 179 / 129 | 15385 | -0.479% |
| webvid2_5m_light_v1 / aux / duplicate3P−baseline | -0.2968 | 734 / 970 | 35 / 65 | 2874 | +0.528% |
| webvid2_5m_light_v1 / aux / mode3P−baseline | -0.1333 | 1081 / 1187 | 44 / 57 | 5897 | +0.288% |
| webvid2_5m_light_v1 / aux / mode3P−duplicate3P | +0.1635 | 1362 / 1232 | 78 / 61 | 6122 | -0.240% |
| yandex_t2i_official10M_ip_v1 / fit / duplicate3P−baseline | -0.1150 | 740 / 970 | 40 / 60 | 5011 | +0.495% |
| yandex_t2i_official10M_ip_v1 / fit / mode3P−baseline | +0.0820 | 1611 / 1447 | 97 / 86 | 13428 | +0.728% |
| yandex_t2i_official10M_ip_v1 / fit / mode3P−duplicate3P | +0.1970 | 1900 / 1506 | 119 / 88 | 14071 | +0.232% |
| yandex_t2i_official10M_ip_v1 / aux / duplicate3P−baseline | -0.1673 | 367 / 500 | 24 / 32 | 1971 | +0.425% |
| yandex_t2i_official10M_ip_v1 / aux / mode3P−baseline | +0.0616 | 716 / 667 | 42 / 38 | 5404 | +0.891% |
| yandex_t2i_official10M_ip_v1 / aux / mode3P−duplicate3P | +0.2289 | 909 / 727 | 55 / 43 | 5616 | +0.463% |

成员找回/丢失按GT10 mask集合计算；逐query净命中正部/负部另存paired表，两者净值相同但不混用。失败严格hits=0；原命中0..10的分组受上下界限制，不作为在线可预测收益。全部失败转换按源namespace行号及三入口保存。

实际新增 337248 NSG、336960 HNSW；4个新3H小图构建，2个baseline源图加载、12个后续物理图加载及18次count重载。合成另1小图/15 HNSW/0NSG。画像训练时间 30.286s，原生进程操作时间 250.863s（含加载/计数/I/O，不是QPS）。无新GT/梯度更新。

独立集合评分 167712 条开发返回，55904 条baseline恢复；另768预检返回及288原kernelparity。所有7slot去重、图坐标/label/邻接、plain/count bits和CPU15实际单线程通过。父/子质量与ESS、raw prior守恒及7个固定父hub/集的20轮独立重放通过。

[开发图](figures/development.png) · [全部指标](results/points.csv) · [配对](results/paired.csv) · [失败query](results/failure_cases.csv) · [11组原命中分析](results/cohorts.csv) · [冻结门](results/selection.json) · [协议](protocol.md) · [验收](reviews/verification.json)

本阶段完成不代表整日21:00目标完成；需要后续完整开发wall与晚间冻结后的最终同批对照。无开发门时停止该容量/阈值/seed版本，保留局部正负，不扫模式数找阳性。
