# E48 画像评分与HNSW邻接的四格因果控制

2026-09-12，`COMPLETE_SCORE_TOPOLOGY_FACTORIAL_MIXED_MECHANISM`，接续门`KEEP_MIXED_MECHANISM_NO_SINGLE_FACTOR_TRAINING`。原E44全部20状态/160原动作，完整train4096，无优化更新。

| 数据集 | 四格因素 | 累计gain/loss/net hits | 最佳静态净值 | 逐query上界 | 未覆盖/自身损伤差额 |
|---|---|---:|---:|---:|---:|
| WebVid | A 评分+邻接 | 198/215/-17 | 35 | 63 | 24/4 |
| WebVid | S 只评分 | 61/69/-8 | 22 | 29 | 7/0 |
| WebVid | T 只邻接 | 143/152/-9 | 29 | 39 | 5/5 |
| Yandex | A 评分+邻接 | 62/78/-16 | 26 | 26 | 0/0 |
| Yandex | S 只评分 | 49/78/-29 | 20 | 20 | 0/0 |
| Yandex | T 只邻接 | 15/16/-1 | 6 | 6 | 0/0 |

以上是各状态/动作诊断总和，不是Recall收益或一份模型。

已有动作的收益损伤不能统一归因于共享画像评分，也不能统一归因于HNSW重建。WebVid只邻接保留143 gain但带152 loss；只评分61/69，二者都有跨query冲突。Yandex只评分49/78，占主要质量响应；只邻接15/16，主要在目标hub原入口补集。固定拓扑没有清掉Yandex损伤，固定评分也没有保住其主要收益。两因素均未过预锁的双集“保留≥75%gain、loss≤50%、最佳静态净值不减”接续门，因此不直接启动单因素训练或扫幅度。

动作逐query完整响应分类更具体：WebVid80动作中32全质量空、6评分独立充分且邻接空、22邻接独立充分且评分空、1只有联合才有响应、19混合；9动作有非零交互，交互绝对命中差合计44。Yandex分别62空、8评分充分、4邻接充分、6混合；5动作非零交互，绝对差18。这里“充分”只指该动作固定背景下完整命中向量恢复，不是机制唯一归因；交互不能独占计给任何一方。

用户问的两种瓶颈都有，但数据集不同。原A的有限动作集，WebVid九个有响应状态合计oracle63、最佳静态35，差28分成未覆盖24和最佳动作自身损伤4；23/80动作同时增益和损伤，真实冲突存在，但有限方向覆盖不足更占这个差额。Yandex仅3/10状态有质量机会，而原A的oracle与最佳静态都26，存在无损动作完整取得本批观察到的收益；因此这批状态的主要证据是机会稀疏，并非必须牺牲其他query。不能由八个有限方向外推整个表示空间小，也不能把不同状态的最佳动作拼作一份可部署模型。

## 实际控制与计量

C=(Wc,Gc)、A=(Wa,Ga)逐位恢复旧端点；S=(Wa,Gc)、T=(Wc,Ga)为补测物理干预。安装器先完整验证同H/ID/层级/入口/maxlevel/合法有序邻接及容量，才修改邻接；native逐行memcmp画像bytes，状态全拓扑SHA对应冻结来源。20同拓扑no-op与8非法拓扑无副作用拒绝通过。S/T不要求是普通builder单独可生成的图，只作机制控制。

全500状态真实route4096；相同query和完整有序三入口键精确复用对应C的NSG返回，变化者全部新NSG，当次route NDC保留。实际NSG7525=2725变化query+4800三路parity，其中原C/A补测1333、S/T补测1392；旧C种子81920历史成本分账。HNSW2051200，340普通构图、320干预+20no-op安装。WebVid/Yandex进程28.588/30.432s，累计59.021s，CPU15实际单线程串行；这包含控制构造等工作，不是线上QPS。

独立集合评分2048000行，737280端点逐位复现、全部缓存键/patch身份、655360逐query交互与四条件边际、500画像/拓扑身份和100代表物理图×16query三路parity通过。0optimizer/新GT/开发/validation/held-out/QPS；源和E37–E47旧资产SHA保持。默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。

## 接续

下一问题转向E47已冻结RL候选的独立静态评测：RL在两集monitor有局部正值，保留该信号；原E47整体门因WebVid ES失败仍保持STOP，不扩训练预算。固定两arm双seed选中模型，先fit逐位恢复，再用既有隔离cal选seed、audit验证，并实测单线程五L/五轮完整Recall–QPS。当前E49尚未查询；所有选择规则/预算另冻，不用新开发结果调整画像。19:40停止新查询，20:00完成研究收口。

[协议](protocol.md)、[动作表](results/actions.csv)、[状态上界](results/contexts.csv)、[完整分析](results/analysis.json)、[接续门](results/gate.json)、[成本](results/cost.json)、[独立核验](reviews/verification.json)、[图](figures/factorial_mechanism.svg)。
