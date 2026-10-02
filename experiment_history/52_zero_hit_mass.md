# E63 零命中query质量重权

2026-09-13，`COMPLETE_ZERO_MASS_FIT_SIGNAL_NO_CAL_GO`。保持原GT10成员归属，只把原P在完整20K fit的zero-hit query质量加倍，再归一总质量20000、raw-prior权重1不变；WebVid348/Yandex311条被加强。固定seed随机抽同数量query为sham，同质量分布但不保持难度/画像位移。六画像和原P归属/字节恢复先于新查询冻结。区别于E09 signed单入口残差，不宣称hardness新颖性。

真实画像fit/cal/audit ΔRecall：WebVid+0.0160/−0.0098/−0.0879 pp，Yandex+0.0600/−0.0195/+0.0293 pp。fit净+32/+120命中，失败数−3/−16；这份训练局部正值保留。cal净−1/−2命中，WebVid失败持平、Yandex+2，预锁门均失败，选择仍baseline。sham fit−0.0340/−0.0325 pp，却cal+0.1953/+0.0586 pp，说明小开发样本的方向和训练身份并不一致；sham不转为推荐或回选。

两数据集zero_mass2分别救回25/34条fit失败，同时新增22/18；原全命中变零5/12条。11个原命中组、每GT成员得失和aligned失败案例保留，极端分组受命中上下界限制，不当query收益预测证明。停止2倍版本强度或随机seed网格；可另立完整既有候选的更大历史开发复核，但旧cal失败不回写。

新增9142 NSG、133056 HNSW、6build；原生操作23.523秒含加载，不是QPS；0新GT/梯度更新/正式QPS。132288输出集合/mask/缓存键、44096原路由恢复、六物理图与384三路parity通过，六画像独立逐rank聚合通过。单native CPU15实际线程1，分析在双job工具实际exit之后运行。

P-fit含历史train/monitor，cal/audit历史及今日暴露，Fast30K曾拟合整个router_train；E34最终validation未参与输入/反馈，held-out不打开。没有新方法替换默认，整日目标未完成。

[协议](../entry_method_exploration/20260913_until2100_v1/stage4_zero_hit_mass_v1/protocol.md) · [报告和图](../entry_method_exploration/20260913_until2100_v1/stage4_zero_hit_mass_v1/report.md) · [全部指标](../entry_method_exploration/20260913_until2100_v1/stage4_zero_hit_mass_v1/results/points.csv) · [失败案例](../entry_method_exploration/20260913_until2100_v1/stage4_zero_hit_mass_v1/results/failure_cases.csv) · [选择](../entry_method_exploration/20260913_until2100_v1/stage4_zero_hit_mass_v1/results/selection.json) · [验收](../entry_method_exploration/20260913_until2100_v1/stage4_zero_hit_mass_v1/reviews/verification.json)。
