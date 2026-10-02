# E63 零命中query质量重权

固定2倍质量的真实/随机query对照已完成；开发门结果：webvid2_5m_light_v1=baseline, yandex_t2i_official10M_ip_v1=baseline。这只是历史开发集判断，无正式QPS，原默认不替换。

保持原GT10 hard/soft成员归属，原P的348/311条零命中fit query质量加倍，总质量归一回20000、raw prior保持1。另以固定seed随机选同数量query作sham。没有调强度或选择随机seed，sham不参与推荐。在线仍一份普通Micro-HNSW top3→三个真实入口→原NSG，H815/821、raw-IP、base、GT、大图均未改。

E09是top32单入口signed advantage/hardness残差，本轮是完整GT10正权聚合，机制不同但不作新颖性声称。E09 WebVid微弱正值保留。P-fit包含旧train/monitor，cal/audit均历史与今日暴露；Fast30K也使用全router_train。不称盲测，E34最终validation未参与训练/选型。

| 数据集 | 分组 | zero ΔRecall pp | 增益/损伤hits | 零命中数 | 救回/新增失败 | sham ΔRecall pp |
|---|---|---:|---:|---:|---:|---:|
| WebVid | fit | +0.0160 | 385/353 | 348→345 | 25/22 | -0.0340 |
| WebVid | cal | -0.0098 | 14/15 | 22→22 | 1/1 | +0.1953 |
| WebVid | audit | -0.0879 | 21/30 | 11→11 | 1/1 | -0.0195 |
| Yandex | fit | +0.0600 | 339/219 | 311→295 | 34/18 | -0.0325 |
| Yandex | cal | -0.0195 | 14/16 | 16→18 | 0/2 | +0.0586 |
| Yandex | audit | +0.0293 | 12/9 | 19→19 | 1/1 | -0.0391 |

cal只按净命中>0、零命中数不增、mean totalNDC≤+1%选择，先冻结selection再汇总audit；audit不回选。失败严格是返回top10与exact GT10交集为空。完整11组GT成员周转与逐query净值分开，极端原命中组的单向变化受上下界影响，不是可预测收益证明。

新增9,142 NSG、133,056 HNSW、6小图；原生操作23.523秒含加载，画像assignment/聚合7.061秒、独立画像验收15.699秒，身份核验与准备另计。44096历史基线返回生成成本不当零。0新GT/梯度更新/正式QPS，缓存比例和NDC均不能换算性能。

原A0 SHA与P bytes恢复，六画像独立逐rank聚合、40000 zero-hit身份/随机集合重放、总质量/先验恒等通过。132288返回集合/mask、六物理图全字节、44096原路由恢复与384三路parity通过。全部native在CPU15实际线程1串行退出，分析在两job完成后执行。

[协议](protocol.md) · [指标](results/points.csv) · [选择](results/selection.json) · [11组](results/cohorts.csv) · [失败案例](results/failure_cases.csv) · [成本](results/cost.json) · [验收](reviews/verification.json) · [画像验收](reviews/profile_verification.json) · [图](figures/development_metrics.svg)
