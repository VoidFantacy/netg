# E32：完整三入口的直接收益策略优化

2026-09-11，用户“好的，推进一下试试吧”授权前述小规模直接收益实验。独立版本；不改原NSG图/H/GT/旧模型。此协议在初始梯度测量和新训练之前冻结。

## 问题与两组对照

E31优化原教师目标没有产生双集有效收益。本轮改变训练目标，检验是否存在目标错配：固定每query的C8和全部56个完整三入口动作，原multi教师hinge versus 真实Recall期望目标。后者属于全信息上下文策略优化，一次选择动作，没有状态转移；不称为已验证的多步RL/PPO，不重启旧C状态干预。

fit20K/数据集，复用E28原raw-IP NSG L128/K10完整组合标签。H、GT10-hard P、原query和真实ID、C8、56动作顺序、模型W=normalize(P+P A^T)、A=0、τ=.05、锚定λ100完全固定。C8由GT1-hard和GT10-hard两个固定HNSW direct3的并集，再以原GT10-hard全H精确分数填满8；ties按真实ID，原propose.cpp为身份权威。模型给每个动作分数F=sum(q_unit W/τ)，π=softmax(F)。

- teacher：原E31 multi loss，max(F+.1*notG)-max_G F；G为最高hits中最低graph NDC的全部并列集合。
- reward：β mean_q sum_a π(a|q)*(max_b hits(q,b)-hits(q,a))/10。减去每query最优收益只改目标常数，梯度等于负期望Recall梯度。完整枚举，无采样梯度方差。
- 两者加100 mean_H ||W-P||²。不改模型容量，不按数据结果加温度/正则/seed网格。
- β为每数据集初始化A=0处teacher数据项梯度范数除以未缩放reward数据项梯度范数；仅用fit计算一次并冻结。若分母非有限或≤1e-12则停止该实验。该匹配只对齐初始梯度尺度，不声称两个目标全程正则强度等价。

## 成本约束与固定训练

从零训练teacher/reward×两集，共4次1200步，顺序WebVid teacher/reward再Yandex teacher/reward，CPU8、float64、fullfit累积、batch1024、seed20260911。Adam前20步3e-5→3e-4，至200步保持，余弦到1200步3e-6；同E31。训练子进程总wall硬上限600s，内循环提前3s收尾，磁盘余量≥10GiB、RSS<40GiB；超时不重启或补跑。

每步记录数据项/锚定/总目标、梯度、期望与贪心Recall及graph NDC。checkpoint仅在下述可行点中选择本组fit总目标最低者，严格相等时最早：期望graph NDC≤初始化期望的1.01倍，同时贪心graph NDC≤初始化贪心的1.01倍。成本是checkpoint可行域约束，不伪称加入可微NDC惩罚；不可行点保留。记录最终点和选中点，导出float32 W及float64 A。以独立NumPy复核所有选中/末点目标、成本、模型和标签；teacher与E31 multi逐位回归，若因可行域改变选点明确披露。

## 缓存门与条件后续

最终门只使用导出的float32 W在同C8中选出的完整三元组及旧真实标签。两个数据集都须：reward比原C8 anchor Recall至少+0.20pp，比本轮teacher至少+0.05pp；贪心graph NDC≤原C8 anchor的1.01倍，期望NDC≤原anchor期望的1.01倍；全部输入/模型/动作/梯度验收通过，4次1200步完成。阈值预锁；bootstrap仅描述，不能改变门。

不同于E31部署全H exact/HNSW的未知组合界，本轮部署契约明确也是同一C8策略，不用未知全H组合决定本轮门。这是方法域改变，候选代价并非免费。若任一数据集失败，停止新增ANN与QPS，保留单集信号和期望-贪心差异，完成图表/Excel/报告/文档，不扩模型或RL算法。

若缓存通过：先实现并验收GT-free在线C8生成、模型打分/56组合argmax/映射/原NSG，完整C8和选择parity；计时包含两HNSW路由、全H填充、模型打分及组合选择。固定比较GT10-hard direct3、本轮teacher C8、本轮reward C8、当前默认（WebVid GT10-soft/Yandex GT10-hard，重合基线可合并）。先fit20K及cal/audit各1024的L128 count诊断，要求reward在两集cal与audit都胜teacher及默认、图NDC≤默认+1%；否则停止。通过后才使用历史validation前2K，L64/128/256/400/800，同机CPU15单线程，每点2000 warmup+5轮独立plain wall，另进程count/GT评分。全部新NSG调用cap800000、失败及修复计入；阶段wall cap90分钟，单次只能一个方法，无并发训练/分析；不读/hash held-out。实际QPS仅来自全开销独立批量wall；不得由缓存、分项相加或NDC估算。此条件后续仍需独立运行清单在启动前冻结，不能据观察扩大矩阵。

## 输出与解释范围

保护E31及其旧保护链的全部文件身份，根文档另存source_before。新版本保存协议、输入引用/身份、梯度尺度与数学验收、4次全轨迹/模型、aligned选择/收益/NDC、缓存gate、图PNG/SVG、CSV/Excel、报告、原命令日志与最终验收。cal/audit/validation不会进入本轮训练或尺度选择，缓存门失败时也不读取它们。

所有fit查询有历史使用；一个H/seed/λ和固定温度、加性评分的有界实验。训练期望收益不是贪心收益，贪心缓存收益不是在线QPS；结果只评价本轮策略目标与表示，不外推所有强化学习可行性或图结构优化。
