# E80：按真实hub条件化的GT10目标分组

条件目标画像已完成双数据集构造和真实查询。两集均未通过预锁门，停止本条件均值版本，不扫参数或改选旧对照。 整日21:00目标未完成。

原A按GT每个目标分别归属hub；E79却给同一query的所有hub使用全GT10均值。E80仅将分组特征改为该hub条件权重beta下的目标均值，仍按原A和query聚合子画像。目标/query/base/raw-IP/原NSG/真实H固定，线上仍一次ef10小HNSW取7slot去重三真实入口。此为信息定义改变，尚不能把目标混合作为已确认的失败原因。

| 数据 | 候选 / 对照 | 净GT10命中 | ΔRecall pp | 救回 / 新增零命中 | 两半净命中 |
|---|---|---:|---:|---|---|
| WebVid | conditional10 / baseline10 | -39 | -0.0490 | 32 / 49 | 13 / -52 |
| WebVid | conditional10 / compact10 | +20 | +0.0252 | 57 / 63 | 29 / -9 |
| WebVid | conditional10 / global10 | -28 | -0.0352 | 35 / 45 | -10 / -18 |
| WebVid | global10 / baseline10 | -11 | -0.0138 | 33 / 40 | 23 / -34 |
| WebVid | global10 / compact10 | +48 | +0.0604 | 57 / 53 | 39 / 9 |
| Yandex | conditional10 / baseline10 | -12 | -0.0151 | 28 / 25 | -86 / 74 |
| Yandex | conditional10 / compact10 | -132 | -0.1660 | 29 / 39 | -125 / -7 |
| Yandex | conditional10 / global10 | -12 | -0.0151 | 27 / 26 | -41 / 29 |
| Yandex | global10 / baseline10 | +0 | +0.0000 | 32 / 30 | -45 / 45 |
| Yandex | global10 / compact10 | -120 | -0.1509 | 31 / 42 | -84 / -36 |

条件化对P/compact要求全量正、两半非负/失败不增，对global全量及两半非负/失败不增。全门在训练/查询前锁定，global是E79冻结target原件在本批的对照身份。门失败不由同LRecall或NDC升级成效率结论。

旧收益保留与损伤迁移（相对P的逐query净命中正负部；GT成员集合增损另列）：

- WebVid：保留旧compact正命中 356/820；丢失 464、新增收益 345；避免旧损失 566、新增/放大损失 427。
- Yandex：保留旧compact正命中 183/545；丢失 362、新增收益 173；避免旧损失 253、新增/放大损失 196。

离线目标支持只用于解释输入/表示，没有把逐hub几何差异当NSG因果信用：

- WebVid：610个active父hub，534个合格双子，1883物理画像；按父mass加权目标1−cos均值 0.058481、条件有效GT目标数 3.498、对global分区无标签差异 22.17%。
- Yandex：784个active父hub，701个合格双子，2223物理画像；按父mass加权目标1−cos均值 0.100089、条件有效GT目标数 4.081、对global分区无标签差异 11.85%。

全部rank权重/A SHA、父P字节及E79全局目标digest恢复。每集固定32query×12hub条件特征独立逐rank参考、12hub独立query聚合通过；正支持零目标退化按协议记录，A=0只表示无该hub权重。全部beta/目标在RAM，逐hub流式，不持久化N×H×d大矩阵。条件化也可改变子支持、画像容量和图，不能把最终差异只归于某个中介。

实际 129536 NSG / 129280 HNSW、2离线画像分组训练、2真实build，0梯度/新GT/编译/合成ANN。离线 450.089s（含rank恢复 9.857s）、图build 0.376s、四native 110.429s。操作wall含加载/count/I/O，不能当QPS；继承GT/P成本未知。

旧P/compact/global47712条完整返回/距离bits/入口/两NDC恢复、全部plain/count及256原kernel、完整7slot/图W/labels/邻接/集合mask均通过。CPU15/实际进程与数值库1线程，方法/数据集串行，工具terminal0后分析。

失败并集 486个dataset/source-row，其中291个失败状态变化。全表保留GT10/入口/返回ID及所有方法都失败的行，图仅按源行取每集前24个变化例。

P-fit20K含旧train/monitor，aux7952及两半已观察且接受反馈计训练；cal/audit历史使用。E34最终/held-out本阶段未打开，旧E79门和seal保持。资源独立锁64MiB阶段上限、6.8GiB下限外留64MiB晚间+4MiB交接，不清理旧产物。

[协议](../entry_method_exploration/20260913_until2100_v1/stage21_hub_conditioned_targets_v1/protocol.md) · [完整配对](../entry_method_exploration/20260913_until2100_v1/stage21_hub_conditioned_targets_v1/results/paired.csv) · [质量门](../entry_method_exploration/20260913_until2100_v1/stage21_hub_conditioned_targets_v1/results/gate.json) · [条件支持](../entry_method_exploration/20260913_until2100_v1/stage21_hub_conditioned_targets_v1/results/conditional_support.csv) · [完整失败query](../entry_method_exploration/20260913_until2100_v1/stage21_hub_conditioned_targets_v1/results/failure_queries.csv) · [失败图](../entry_method_exploration/20260913_until2100_v1/stage21_hub_conditioned_targets_v1/figures/failure_queries.png) · [质量与计数图](../entry_method_exploration/20260913_until2100_v1/stage21_hub_conditioned_targets_v1/figures/conditional_modes.png) · [成本](../entry_method_exploration/20260913_until2100_v1/stage21_hub_conditioned_targets_v1/results/cost.json) · [验收](../entry_method_exploration/20260913_until2100_v1/stage21_hub_conditioned_targets_v1/reviews/verification.json)。

本阶段新增QPS点0。E73/E74 Yandex局部信号和Web损伤保留；最新独立完整性能曲线仍见[E74报告](../entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/report.md)，不能拼接本批L128点。晚间冻结后最终同批对照仍待完成。
