# E47 局部画像完整反馈RL/ES

2026-09-12，`COMPLETE_FULL_FEEDBACK_PROFILE_RL_LOCAL_RL_SIGNAL_AGGREGATE_GATE_STOP`，统一门`STOP_FULL_FEEDBACK_BUDGET_EXPANSION`。八次真实训练完成，RL双集局部信号保留，统一稳定性门停止扩展预算。

| 数据集 | 方法/seed | 选中步 | train512 ΔR pp | full train ΔR pp | monitor ΔR pp | 末点monitor ΔR pp | 原E43选中monitor ΔR pp |
|---|---|---:|---:|---:|---:|---:|---:|
| WebVid | RL/21 | 100 | +0.0195 | +0.0513 | +0.0781 | +0.0781 | +0.0098 |
| WebVid | RL/22 | 80 | +0.1953 | +0.0391 | +0.0098 | -0.1660 | -0.0098 |
| WebVid | ES/21 | 40 | +0.0781 | +0.0220 | +0.0000 | -0.0195 | +0.0781 |
| WebVid | ES/22 | 20 | +0.0000 | +0.0098 | +0.0000 | -0.0781 | +0.0000 |
| Yandex | RL/21 | 100 | -0.0195 | +0.0073 | +0.0000 | +0.0000 | +0.0000 |
| Yandex | RL/22 | 200 | +0.0000 | +0.0171 | +0.0781 | +0.0781 | +0.0000 |
| Yandex | ES/21 | 120 | +0.0000 | +0.0098 | +0.0000 | +0.0000 | +0.0000 |
| Yandex | ES/22 | 200 | +0.0000 | +0.0073 | +0.0586 | +0.0586 | -0.0195 |

完整反馈显著增加了可见质量响应，但仍未形成所有数据集/估计器都稳定增益的结果。WebVid每200步有133–145步见候选命中变化，Yandex74–85步；原E43为13–18/3–7步。两轮训练的状态会分岔，这一频次对比不再是固定状态采样消融；E44已有固定状态的漏反馈证据。

实际确定均值响应仍稀疏：WebVid每200次更新仅12–20次改变全池命中，Yandex仅1–3次。八模型末点完整训练池均为净正值，但WebVid RL第二seed后期monitor退到−0.1660pp，ES两seed选中monitor均0，说明训练机会与新query收益没有稳定转化。不能把非零reward或看见更多候选收益直接当作泛化成功。

RL的局部正值必须单独保留：WebVid选中两seed monitor +0.0781/+0.0098pp，Yandex为0/+0.0781pp；RL这个arm在两集均有正候选。原预锁门要求每个数据集的RL和ES都至少一个seed正增量，因WebVid ES失败而未过，按协议停止本完整反馈版本的预算扩展。这个统一门的失败不能抹掉RL双集信号，也不能反过来改写为统一门通过。Yandex ES第二seed +0.0586pp同样保留；尚无独立开发或Recall–QPS证据。

## 方法与真实成本

原E43 P/B/H/单行H×16参数、两arm双seed/σ.3/200步/Adam/GT无关hub与ε日程保持；只把奖励query覆盖改为完整4096。候选以及每次确定均值更新都真实build/route4096、仅三入口变化补测原NSG，其他完整返回按同query/原NSG/L/K/metric键复用。全部route NDC更新，当前缓存随均值更新替换；80次缓存换父/no-op/回退及效用恒等预检通过。

冷启动每run实际run4096；monitor1024每20步实际查询，train512从当时完整缓存提取。完整checkpoint保存全W/系数/动量/计数以及train4096+monitor1024返回；选中非零checkpoint规则与E43相同，selected/last输出静态W与普通HNSW。线上仍一次HNSW→三个真实入口→原NSG，没有在线策略模型。

实际228832 NSG=125952固定冷启动/monitor/parity+101961候选补测+919均值补测；HNSW59107328、普通构图14424、optimizer1600。候选逻辑反馈52428800行、均值逻辑6553600行，与真实新增搜索分开。完整预留800000，未释放失败预算；本阶段无失败job。两query进程710.011/550.973s，累计1260.983s（约21.0分钟），CPU15实际进程/OMP/BLAS/MKL1、串行；含加载/路由/构图/评分/写盘/验收，不是线上QPS，也不是与E43的独立重复速度对照。

## 独立核验

重放12800候选与1600确定均值的完整缓存、路由entries/cache hash及所有变化patch，独立集合评分586208返回（含102880新patch、32768冷启动和450560 checkpoint行），核验12800候选W身份、1600四分量梯度/Adam、88全量checkpoint、16导出和1024条三路parity。均值逐step命中变化累加逐query等于最终完整训练池差，源/输入/原E37–E46与native/NSG SHA保持；核验45.448s，无新搜索。

所有新结果都来自历史train/monitor，monitor选择checkpoint，不是盲测/泛化结论。0新GT/cal/audit/validation/held-out/QPS，默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。E43原ES正值和E44分层失败不覆盖。

## 接续

接着执行E48评分/邻接2×2，直接回答原有动作的跨query收益损伤来自共享评分方向还是普通HNSW重建的干扰：固定E44全部20状态/八方向，补齐(Wa,Gc)/(Wc,Ga)，真实路由全池并精确补测变化query，不增加训练epoch或幅度。源码和协议已准备，当前尚未编译或查询。

之后另立“冻结RL候选能否保留双集增量”的独立对照问题，考虑用既有隔离cal/audit和原单线程静态评测器验证完整Recall–QPS。它不复活E47的统一训练门、不重训或按新结果改模型；所有候选/选择规则/预算在查询前另冻，当前无新cal/audit。用户要求大胆假设、小心证明，因此继续验证已有具体信号，不把自设统一门变成放弃所有局部结果的理由。

[协议](protocol.md)、[模型表](results/models.csv)、[完整质量](results/quality.csv)、[反馈](results/feedback.csv)、[逐步](results/steps.csv)、[原门](results/method_gate.json)、[成本](results/cost.json)、[独立审计](reviews/training_verification.json)、[图](figures/full_feedback_learning.svg)。
