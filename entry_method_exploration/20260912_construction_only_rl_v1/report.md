# E56 RL只优化离线构图，查询画像评分固定

2026-09-12，`COMPLETE_CONSTRUCTION_ONLY_RL_LOCAL_SIGNAL`；局部门`PASS_DUAL_LOCAL_CONSTRUCTION_RL_SIGNAL`。

纯构图RL存在局部正信号，但没有显示优于联合画像与拓扑RL的稳定选中点优势。WebVid两个seed选中monitor分别+0.1465/+0.1074 pp，末点仍+0.1270/+0.1074 pp；相比E53末点的+0.0391/−0.0781 pp，后段退化较小，但训练收益也更小。Yandex选中monitor仅+0.0195/+0.0098 pp，对应净增加2/1个GT命中，seed22末点转为−0.0098 pp，不能把它描述为稳定泛化。

四条训练轨迹全量4096反馈均向上，但monitor并不同步。它支持“改变离线HNSW构图确实能产生有效动作”，尚不证明这是主要瓶颈，也不证明单独训练拓扑就解决跨查询损伤。E54固定终点拆分和本次从头纯构图训练的路径不同，不能用前者的拓扑效果替代本次训练结果。两个种子全部进入E57既定19候选池，由原cal规则选型，最终指标不反向选点。


| 数据集 | seed | 选中步 | full train ΔR pp | monitor ΔR pp | 末点monitor ΔR pp | E53 joint选中monitor ΔR pp | 接受/200 |
|---|---:|---:|---:|---:|---:|---:|---:|
| WebVid | 21 | 100 | +0.2197 | +0.1465 | +0.1270 | +0.1270 | 72 |
| WebVid | 22 | 180 | +0.3418 | +0.1074 | +0.1074 | +0.1562 | 72 |
| Yandex | 21 | 200 | +0.0781 | +0.0195 | +0.0195 | +0.0195 | 57 |
| Yandex | 22 | 140 | +0.0732 | +0.0098 | -0.0098 | +0.0293 | 60 |


## 实际方法与序列化身份

离线局部坐标C沿用E53的H×16参数/同Gaussian与hub日程、LOO RL梯度/Adam方向及r/4、r/2、r真实反馈接受；训练评价始终是固定原画像P上的实际G(C)。普通build(C)取完整邻接，再build(P)并安装G(C)，逐次全向量字节检查后才查询。原漂移公式作为离线构图坐标正则保留；不是直接逐边参数化，也不是E33仅删原底边。与E53有相同候选/梯度预算，额外物理构图与安装成本单列，不能称等wall训练。

selected/last的W.f32恒P，construction_W.f32仅离线，graph.hnsw是真实P/G(C)。checkpoint W字段是构图坐标，不能用于线上评分。8图独立原生字节解析验证6544画像行、真实ID/节点层级与完整多层拓扑SHA；每次逻辑构图全物理P检查共9612次。线上仍一个普通HNSW top3再原NSG，无RL策略或隐藏C评分。

## 成本与核验

实际85204 NSG=62976固定+18013Gaussian变化+4215确定点变化；36107264 HNSW、9612逻辑构图、19224物理构图/9612安装，800梯度/接受决策、261真实接受。完整进程1346.102s，CPU15实际单线程、每seed独立native、两集串行；加载和实际所有物理构图均记账。0新cal/audit/validation/held-out训练反馈、0新GT/本阶段QPS。

独立6400Gaussian/2400确定点、800四分量梯度/Adam/步长选择/拓扑缓存状态链、44完整checkpoint、8导出/512三路parity通过；263892集合评分，审计30.063s。每run完整预留150000 NSG/4806物理构图，总19224<25000；原native每实例7500守卫不变，实际成本未因重建实例省略。

## 设计时序与启动修正

算法和超参文件写成时间早于E55 WebVid最终结果生成；封存时该结果已可用但尚未读取，首次严格“生成前封存”检查失败如实留档。之后资源预测守卫仅依据E53旧dataset耗时比修正，未使用E55最终质量；此与方法算法改变区分。E56首入口预测完成超出21:10目标约16秒，在native创建前退出，NSG/HNSW/build/update均0；有效train_v2仅将预测目标调为21:12，21:15实际训练硬停仍保持，原代码/config/log保留。没有查询失败后重试或修改种子。

历史monitor参与选点且P拟合曾用它，不能称盲测；训练局部门不是独立泛化/性能GO，不撤销E53或E55负结果，默认尚未替换。

E57按训练前协议将E55原17候选加本次两个seed全部selected，19模型/集；同fit128恢复、cal1024原U/低NDC/固定序选型后冻结。仅当某集改选新模型时，对该集全部NSG/Fast/FastGT及候选重新同批五L五轮；若身份不变，整组复用E55已验计时，不重复或混批。新调用88768+受影响组完整矩阵，最大719488；保留历史validation非盲测身份，21:40停止新查询、22:00收口。

[协议](protocol.md)、[有效训练](src/train_v2.py)、[模型表](results/models.csv)、[800步骤](results/steps.csv)、[成本](results/cost.json)、[独立重放](reviews/training_verification.json)、[设计时序](reviews/design_before_result_inspection.json)、[资源预测修正](reviews/design_guard_revision.json)、[启动窗口修正](launch_window_revision.md)、[学习曲线](figures/construction_learning.svg)。
