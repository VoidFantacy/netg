# E78 固定图子质量范数权重

主候选对子画像乘rho^(1/d)，rho来自原P-fit子质量占比，不再单位化；P首槽不动。统一对照乘exp(mean_child(log rho)/d)，平均log缩放相同。两者原方向、slot/真实映射、完整compact图邻接/层级/入口保持；只在新图文件安装向量字节，0构图、无新增在线计算。

| 数据 | 候选 / 对照 | 净命中 | ΔRecall pp | 救回/新增失败 | 两半净命中 | 路由/总NDC变化% |
|---|---|---:|---:|---|---|---|
| WebVid | mass10/baseline10 | -59 | -0.0742 | 44/55 | [-11, -48] | +3.69/+0.24 |
| WebVid | mass10/compact10 | +0 | +0.0000 | 2/2 | [5, -5] | +0.06/+0.05 |
| WebVid | mass10/uniform10 | +14 | +0.0176 | 3/4 | [6, 8] | +0.17/+0.04 |
| WebVid | uniform10/compact10 | -14 | -0.0176 | 5/4 | [-1, -13] | -0.11/+0.01 |
| Yandex | mass10/baseline10 | +76 | +0.0956 | 39/29 | [21, 55] | +20.19/+0.72 |
| Yandex | mass10/compact10 | -44 | -0.0553 | 1/4 | [-18, -26] | -0.02/-0.00 |
| Yandex | mass10/uniform10 | -23 | -0.0289 | 1/4 | [1, -24] | -0.14/-0.05 |
| Yandex | uniform10/compact10 | -21 | -0.0264 | 3/3 | [-19, -2] | +0.11/+0.05 |

主候选预锁门：WebVid未通过, Yandex未通过。对P/C要求全量正、两半非负/失败不增；对uniform要求全量与两半非负/失败不增。无一集通过，停止此范数权重版本，不追加其wall，不改选uniform或扫指数。 旧E73/E74 Yandex局部信号与E75/E77原停止状态保持，不升级为默认或性能GO。

旧收益保留与新损伤均按逐query净命中正负部分解，不是GT成员实际新增/丢失计数：
- WebVid：保留旧正命中797/820，丢失23，另生正命中14；避免旧损失23，新增/放大损失14，最终总损失870（旧879）。
- Yandex：保留旧正命中494/545，丢失51，另生正命中13；避免旧损失12，新增/放大损失18，最终总损失431（旧425）。

本乘法权重不是旧E10加log(rho)/d的等价变换，也不是校准概率；1/d只是固定小尺度设计。正内积分数下降、负分数向0靠近，不保证三入口/NSG单调；原底层raw-IP/NSG未改变。float32舍入会有极小方向数值差，不把它称精确位相同方向。

实际129536 NSG/129280 HNSW、0build/4向量安装/0新合成ANN/0新GT/梯度，evaluator同SHA引用、编译0。权重构造0.797s、向量安装0.124s、四native 110.869s。继承E66画像训练30.286s及早期GT成本未重测；计数操作wall不能当QPS，本阶段QPS点0。

独立64640返回集合/mask、63616逐行set评分；31808旧P/C全字段恢复、256原kernel、全部plain/count/7slot/图W/labels及非向量bytes保持通过。rho范围/统一平均log缩放、逐行标量导出bytes和P原字节验收通过；4种非法shape/NaN/rho实际零查询拒绝。19790主候选相同三入口返回行恢复。

aux7952及两半均历史暴露，选择反馈计训练；P-fit含旧train/monitor，cal/audit已观察，E34最终与held-out未打开。查询串行CPU15/实际进程及数值库1线程，两个数据集工具terminal0后分析。strict failure=GT10零命中，aligned返回/源行及全部成员得失保存。整日目标未完成。

[协议](protocol.md) · [配对](results/paired.csv) · [失败查询](results/failures.csv) · [收益保留](results/gain_retention.json) · [权重/安装](results/construction.json) · [成本](results/cost.json) · [图](figures/mass_norm.png) · [验收](reviews/verification.json)。
