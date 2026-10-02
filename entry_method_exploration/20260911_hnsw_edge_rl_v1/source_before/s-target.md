# ACSG 下一阶段方向与实验接续

2026-09-11。E32已完成并停在开发门，状态`DIRECT_REWARD_POLICY_COMPLETE_FIT_GAIN_MIXED_DEVELOPMENT_STOP`。[报告](entry_method_exploration/20260911_direct_reward_policy_v1/report.md)、[历史21](experiment_history/21_direct_reward_policy.md)、[开发门](entry_method_exploration/20260911_direct_reward_policy_v1/results/development_gate.json)。当前授权的小规模直接收益试验已收口，没有排队的训练/ANN/validation任务。

## 当前采用与保留信号

默认仍为WebVid GT10-soft-t1/Yandex GT10-hard，以[E30同批曲线](entry_method_exploration/20260911_equivalent_teacher_sets_v1/report.md)为依据。原GT10/E28局部正信号保留，E31固定teacher/共享linear/λ100的优化支线继续关闭。

E32更换为完整动作的真实期望Recall，同C8 fit相对teacher+0.9155/+0.3050pp，cal/audit相对teacher四点均正；对当前默认则三正一负、幅度小。不能把新目标简单等同于旧teacher重训，也不能说训练之外完全没有信号。WebVid cal少2命中而未过预设门，总路由成本同时增加：完整audit总NDC约+54%/+32%。尚无QPS或稳定替换证据。

## 优先一：直接收益的泛化与候选成本

先用现有原始结果完成问题定义，不直接扩成PPO/大模型。关键问题分开：目标是否改善同候选的真实动作选择；该改善能否在独立评估保留；同一候选生成能否用足够低的在线代价实现。

下一份小协议应先锁定一项主要变化及对照。泛化方向可考虑fit标签内部固定交叉拟合，或预先确定的位移/容量控制，至少保留原teacher、原anchor和直接收益对照；不能根据现有cal/audit选有利折或超参。已有20K×56标签只支持原query、C8、完整三入口、L128/K10及同kernel身份；可复用的部分无需新NSG标签，但新增模型及额外训练必须单列预算与停止规则。

候选成本方向先区分两路HNSW、全H填充、学习打分和NSG成本。若改为更便宜的候选域，必须显式列出旧标签覆盖率与新增组合标注需求；缺失标签不作0，不把新域的训练与旧C8部署收益混用。最终完整wall必须包含候选生成和全部在线处理，graph NDC持平不能作为总成本通过。

进入后续真实评测的条件应在运行前锁定：同域对照有实际收益，模型/候选/核验通过；在明确独立的开发数据上胜默认且成本可接受；随后同机单线程完整Recall–QPS曲线。若成本或开发门失败，保留信号后停止，不用剩余预算扩网格。阶段产物仍为协议、冻结身份、模型、aligned结果、gate、图/CSV/Excel和成本账。

## 优先二：GT10独立复现与公平比较

原GT10的独立复现与强基线问题仍未完成。E32只比较默认画像及teacher/直接收益C8，不代表所有NSG/Fast/其它方法的完整比较。复现方案需要明确固定图上变化的是query、build seed或其它因素；已有历史validation不能重新称盲测。先核对现有基线与输入身份、GT成本、Recall区间，再定义最小新矩阵。

新方案至少预锁共同Recall目标、完整端到端wall、单线程与CPU、重复轮次、构建/查询/GT依赖和硬cap；只以独立同机前沿证据认定性能收益。不得由E32缓存或同L Recall替代。

## 优先三：多步强化学习只在问题确有顺序决策时考虑

当前56动作已知收益，精确期望目标足够检验目标对齐，无需采样PPO。若未来研究搜索过程中的多步动作，须先说明状态、允许动作、真实转移、成本奖励和非RL对照，以及与已停止C状态干预的实质差异；不能重命名恢复旧runner。当前单步C8信号不授权图重连、无限标签采样或新多步训练。

## 接续要求与未执行边界

完整阅读AGENTS→summary→spec→本文件→s-experiment，再由[历史21](experiment_history/21_direct_reward_policy.md)进入原协议、部署清单、全部gate、模型和原始结果，必要时追溯[E31](experiment_history/20_training_effectiveness.md)/[E30](experiment_history/19_equivalent_teacher_sets.md)。保留原版本；本轮修正控制器为`*_v2.py`，旧失败配置不覆盖。

可用接续指令：核对E32的四个开发点、teacher与直接收益的位移差和完整路由账；在固定一个问题后，提出带对照、数据依赖、标签/训练/查询成本与停止规则的最小协议。上述三个方向的下一阶段均未执行；不从本轮剩余预算自动启动训练、ANN、validation或held-out。

正式性能继续CPU15、进程/OMP线程1、OMP/BLAS/MKL1，一次一个方法，不与训练、编译或重分析并发。所有收益解释须区分fit信号、开发信号、原始实测前沿和插值分析。
