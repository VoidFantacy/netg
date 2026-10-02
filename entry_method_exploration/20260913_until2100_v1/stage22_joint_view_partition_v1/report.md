# E81：query与条件GT目标联合分组

固定双视角离线训练和双数据集真实查询完成。双集预锁门失败，本等权联合分组版本停止。整日21:00目标未完成。

从E66完整query分区初始化，共享两类分配；query与E80按hub条件目标各自形成单位中心。固定等权目标J为两视角、两类加权向量和范数的总和；运行20轮，同一次迭代内两视角共同决定分配。每hub目标单调不降，任一视角出现空类或零中心整hub回退。最终仍只按原query聚合画像并保留父P，没有在线双视角或额外路由。

| 数据 | 候选 / 对照 | 净GT10命中 | ΔRecall pp | 救回 / 新增零命中 | 两半净命中 |
|---|---|---:|---:|---|---|
| WebVid | joint10 / baseline10 | -78 | -0.0981 | 44 / 52 | -28 / -50 |
| WebVid | joint10 / compact10 | -19 | -0.0239 | 32 / 29 | -12 / -7 |
| WebVid | joint10 / conditional10 | -39 | -0.0490 | 59 / 50 | -41 / 2 |
| WebVid | conditional10 / baseline10 | -39 | -0.0490 | 32 / 49 | 13 / -52 |
| WebVid | conditional10 / compact10 | +20 | +0.0252 | 57 / 63 | 29 / -9 |
| Yandex | joint10 / baseline10 | +58 | +0.0729 | 42 / 31 | -30 / 88 |
| Yandex | joint10 / compact10 | -62 | -0.0780 | 19 / 21 | -69 / 7 |
| Yandex | joint10 / conditional10 | +70 | +0.0880 | 38 / 30 | 56 / 14 |
| Yandex | conditional10 / baseline10 | -12 | -0.0151 | 28 / 25 | -86 / 74 |
| Yandex | conditional10 / compact10 | -132 | -0.1660 | 29 / 39 | -125 / -7 |

联合分组对P/compact要求全量正、两半非负/失败不增，对conditional全量及两半非负/失败不增。全门在训练/查询前锁定，conditional是E80冻结conditional原件在本批的对照身份。门失败不由同LRecall或NDC升级成效率结论。

旧收益保留与损伤迁移（相对P的逐query净命中正负部；GT成员集合增损另列）：

- WebVid：保留旧compact正命中 601/820；丢失 219、新增收益 210；避免旧损失 228、新增/放大损失 238。
- Yandex：保留旧compact正命中 396/545；丢失 149、新增收益 134；避免旧损失 120、新增/放大损失 167。

离线目标支持只用于解释输入/表示，没有把逐hub几何差异当NSG因果信用：

- WebVid：610个active父hub，487个合格双子，1789物理画像；按父mass加权目标1−cos均值 0.058481、条件有效GT目标数 3.498、对原Q分区无标签差异 5.21%。
- Yandex：784个active父hub，648个合格双子，2117物理画像；按父mass加权目标1−cos均值 0.100089、条件有效GT目标数 4.081、对原Q分区无标签差异 8.31%。

全部rank权重/A SHA、父P字节及E79全局目标digest及所有E80逐hub条件特征digest恢复。保存全部21步联合目标和初末两视角范数，固定12hub独立重算初末加权和；此检查不重放所有Lloyd迭代。每集固定32query×12hub条件特征独立逐rank参考、12hub独立query聚合通过；正支持零目标退化按协议记录，A=0只表示无该hub权重。全部beta/目标在RAM，逐hub流式，不持久化N×H×d大矩阵。联合分组也可改变子支持、画像容量和图，不能把最终差异只归于某个中介。

实际 129536 NSG / 129280 HNSW、2离线画像分组训练、2真实build，0梯度/新GT/编译/合成ANN。离线 681.920s（含rank恢复 9.880s）、图build 0.356s、四native 110.937s。操作wall含加载/count/I/O，不能当QPS；继承GT/P成本未知。

旧P/compact/conditional47712条完整返回/距离bits/入口/两NDC恢复、全部plain/count及256原kernel、完整7slot/图W/labels/邻接/集合mask均通过。CPU15/实际进程与数值库1线程，方法/数据集串行，工具terminal0后分析。

失败并集 480个dataset/source-row，其中281个失败状态变化。全表保留GT10/入口/返回ID及所有方法都失败的行，图仅按源行取每集前24个变化例。

P-fit20K含旧train/monitor，aux7952及两半已观察且接受反馈计训练；cal/audit历史使用。E34最终/held-out本阶段未打开，旧E79/E80门和seal保持。资源独立锁64MiB阶段上限、6.8GiB下限外留64MiB晚间+4MiB交接，不清理旧产物。

[协议](protocol.md) · [完整配对](results/paired.csv) · [质量门](results/gate.json) · [条件支持](results/joint_support.csv) · [完整失败query](results/failure_queries.csv) · [失败图](figures/failure_queries.png) · [质量与计数图](figures/joint_modes.png) · [成本](results/cost.json) · [验收](reviews/verification.json)。

本阶段新增QPS点0。E73/E74 Yandex局部信号和Web损伤保留；最新独立完整性能曲线仍见[E74报告](../stage15_compact_wall_v1/report.md)，不能拼接本批L128点。晚间冻结后最终同批对照仍待完成。

## 独立检查器更正与局部信号

第一次独立目标检查在F字节digest处失败，旧检查源/失败记录保留。v2恢复训练输入的目标gather、n×10 rank矩阵copy布局及逐rank A归约后，原严格F digest与独立初末范数全部通过；未放松原哈希、未改模型/训练/查询/门，0额外ANN。没有分别隔离这些检查器布局改动的贡献，不将其说成模型错误。首次检查耗时未在失败前写出，成本为未知；v2耗时另记。

- webvid2_5m_light_v1：610条21步J轨迹通过；12固定hub初末两视角独立求和最大误差2.91e-13。J总变化+22.674754，query视角-3.418522，条件目标视角+26.093276。Web最小步差约−1.8e−15在预锁1e−9浮点容差内；不是完整20轮重放。
- yandex_t2i_official10M_ip_v1：784条21步J轨迹通过；12固定hub初末两视角独立求和最大误差7.11e-15。J总变化+151.653025，query视角+3.238994，条件目标视角+148.414030。Web最小步差约−1.8e−15在预锁1e−9浮点容差内；不是完整20轮重放。

E81保留旧compact正收益Web601/820、Y396/545，E80条件目标分别仅356/820、183/545：联合分组确实更能保留原分组的已测收益。但它也少修复旧损失，不能只按保留率选型。Web相对compact丢失219旧正命中，新增210收益，避免228旧损失却新增/放大238损失，合计−19；Y对应−149+134+120−167=−62。

Yandex相对P多58命中且少11失败，相对条件目标多70命中且少8失败，属于局部修复信号。它相对compact仍少62命中、多2失败，而且对P两半并非同时非负；因此不通过原门，不启动E81 enhancement wall，也不把等权附近的权重作为隐含新搜索。Web仍对P−78命中/+8失败。联合几何目标单调上升未保证真实搜索受益；这不证明所有目标表示或所有离线学习都无效。

独立v2检查操作wall 10.458s，[更正记录](reviews/objective_checker_correction.json)和[目标核验](reviews/joint_objective_verification.json)保留。
