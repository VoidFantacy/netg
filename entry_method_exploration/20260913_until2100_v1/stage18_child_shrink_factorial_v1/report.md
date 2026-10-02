# E77 子画像固定半收缩与评分/构图四格

每个子画像改为unit(P+U)，原P首槽逐字保持，alpha固定一半、原物理槽/映射/ef10不变。C为E73 compact；A为新评分Ws普通重建Gs；S仅换评分、T仅换构图。只有A是本阶段预指定新方法，S/T用于解释，不按反馈改选。

| 数据 | 候选 / 对照 | 净命中 | ΔRecall pp | 救回/新增失败 | 两半净命中 | 路由/总NDC变化% |
|---|---|---:|---:|---|---|---|
| WebVid | shrink10/baseline10 | -1 | -0.0013 | 41/52 | [39, -40] | -1.74/-0.03 |
| WebVid | shrink10/compact10 | +58 | +0.0729 | 38/38 | [55, 3] | -5.18/-0.23 |
| WebVid | score10/baseline10 | -51 | -0.0641 | 38/47 | [-21, -30] | +2.22/+0.19 |
| WebVid | score10/compact10 | +8 | +0.0101 | 27/25 | [-5, 13] | -1.36/-0.01 |
| WebVid | topology10/baseline10 | +2 | +0.0025 | 43/48 | [19, -17] | +2.15/+0.17 |
| WebVid | topology10/compact10 | +61 | +0.0767 | 29/23 | [35, 26] | -1.43/-0.02 |
| Yandex | shrink10/baseline10 | +40 | +0.0503 | 33/26 | [10, 30] | +12.74/+0.54 |
| Yandex | shrink10/compact10 | -80 | -0.1006 | 22/28 | [-29, -51] | -6.22/-0.18 |
| Yandex | score10/baseline10 | -9 | -0.0113 | 32/25 | [-45, 36] | +21.22/+0.82 |
| Yandex | score10/compact10 | -129 | -0.1622 | 21/27 | [-84, -45] | +0.83/+0.09 |
| Yandex | topology10/baseline10 | +118 | +0.1484 | 43/31 | [34, 84] | +14.26/+0.63 |
| Yandex | topology10/compact10 | -2 | -0.0025 | 9/10 | [-5, 3] | -4.96/-0.09 |

A预锁接续门：WebVid未通过, Yandex未通过；要求对P和C全量净命中正、固定两半非负、零命中不增。无一集通过，停止A本版本，不追加其wall，不改选S/T或扫alpha/seed。 旧E73/E74 Yandex局部信号、E75失败和E76关联边界均保留，尚不替换默认。

WebVid：评分主效应Σ(S−C)=+8，构图主效应Σ(T−C)=+61，交互Σ(A−S−T+C)=-11，合计A−C=+58；276条query有非零命中交互。效应以完整图配置为干预，不拆成单画像/单边因果信用。
Yandex：评分主效应Σ(S−C)=-129，构图主效应Σ(T−C)=-2，交互Σ(A−S−T+C)=+51，合计A−C=-80；95条query有非零命中交互。效应以完整图配置为干预，不拆成单画像/单边因果信用。

E76不支持低ESS普遍导致损伤，因此本轮不按低ESS删模式。收缩作用于GT10同hub子方向且保留原P，与旧E26 GT1/GT10单画像插值不同；收缩本身不是创新，E26十点九个Recall损伤保留。球面拉回父P不保证分数或三入口单调，评分与图作用必须看真实结果。

实际161920 NSG/161600 HNSW，2普通小图build、4向量安装，0新合成ANN/梯度/GT。同SHA evaluator和builder复用，编译0；两图build 0.345s，四native总128.902s。画像构造用时见construction.json；向量安装独立耗时未记录为null，不能记零。继承E66画像训练30.286s与早期GT成本未重测。此阶段计数操作wall不是QPS，新增QPS点0。

独立80800返回集合/mask、79520逐行set评分，31808旧P/C完整字节恢复、320原kernel、全部plain/count/7slot距离与真实映射通过。四格层级/入口相同，交叉图每个非向量字节保持源图；画像float64构造/逐行标量参考、P逐字保持和全部图布局W/label/邻接均验收。14448相同三入口行结果保持。逐query交互及GT成员净值恒等式通过。

所有query源router_train[2048:10000]历史aux7952与固定3976两半，选择反馈计训练。fit含旧train/monitor、cal/audit已暴露；E34最终与held-out未打开。CPU15/实际进程与数值库1线程、方法和数据集串行，双集工具terminal0后评分；strict failure=GT10零命中。全部旧字节/新版本保留，整日21:00目标未完成。

[协议](protocol.md) · [全部配对](results/paired.csv) · [原值](results/points.csv) · [失败查询](results/failures.csv) · [四格交互](results/interactions.json) · [构造](results/construction.json) · [成本](results/cost.json) · [图](figures/shrink_factorial.png) · [验收](reviews/verification.json)。
