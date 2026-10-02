# E85 路由前query向量选择：缓存可行性

双集固定接受门失败，停止此query方向线性规则，不扩大正则、阈值或划分。没有新在线实现或性能结果。

| 数据 / 分段 | 对P净命中 / 失败变化 | 对compact净命中 / 失败变化 | 原正收益保留 | 原损失避免 |
|---|---:|---:|---:|---:|
| WebVid / train | +283 / -15 | +299 / -23 | 83.92% | 83.60% |
| WebVid / accept | -35 / +3 | +8 / +0 | 57.68% | 40.00% |
| Yandex / train | +215 / -19 | +176 / -14 | 92.31% | 80.16% |
| Yandex / accept | +24 / -3 | -57 / +5 | 57.92% | 29.21% |

训练仅router_train[2048:6024]，接受后半[6024:10000]没有进入本版拟合。全部7952行和旧cal/audit均历史暴露，接受结果不是全项目新鲜独立测试。E25历史汇总结果用于机制复盘，E34最终原始query/GT与held-out未读。

特征仅unit query，以缓存真实compact−P的GT10命中差为标签，固定岭系数1/d、含零差、无失败额外权重、预测>=0选compact；前半label固定置换作同成本控制。不同于E25先路由后提7/13特征，本版拟议在路由前作norm/dot并只执行被选路由，但这一在线模块尚未实现或计时。4模型在后半输出评分之前同时冻结，没有模型/阈值/seed选择或再拟合。

训练非零监督仅Web341/3976、Y129/3976条。训练改善不能证明接受迁移，完整比例与两个固定1988子块均保留。Y主规则在接受段还不及置换控制，不能据少数正点解释为有效选择机制；两集原正收益保留均未过75%。

实际4次岭回归拟合，训练阶段 0.076242s，接受分析与独立增广最小二乘/逐query标量核验 7.620s。0新增NSG/HNSW/build/GT/编译/QPS。63,616缓存行独立集合/mask核验，31,808派生行完整选择单一原策略返回，不混合入口。缓存被选routeNDC不含norm/dot成本，不能作为总在线成本；继承标签/画像成本未知。

失败严格GT10零命中，完整并集410条，其中接受段210条，含全部GT10/两原策略及两缓存规则的三入口和返回ID。图展示每集最早24条状态变化接受query，不挑有利例。

[前瞻协议](protocol.md) · [训练源码](src/train.py) · [模型冻结](reviews/before_accept_freeze.json) · [接受门](results/gate.json) · [完整配对](results/paired.csv) · [保留/避免](results/retention.csv) · [完整失败查询](results/failure_queries.csv) · [接受图](figures/acceptance.png) · [失败图](figures/failure_queries.png) · [验收](reviews/verification.json) · [成本](results/cost.json)
