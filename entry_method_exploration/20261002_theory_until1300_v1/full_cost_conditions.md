# 输出保真访问优化的完整成本条件

2026-10-02理论研究。以下恒等式与条件证明没有运行新的路由、主图搜索、GT或计时。历史时间只提供成本缺口量级，不构成未来实现的速度预测。相关访问前作、浮点条件和实际源码见[原论文笔记](access_literature.md)，当前有限搜索理论见[搜索响应笔记](search_effect_theory.md)。

## 1. 两类目标必须分开

若更换入口、精排范围或路由队列顺序，即便所选目标的raw-IP变大，也必须重新取得固定主搜索的返回与完整wall。当前没有从入口分数到Recall单调改善的保证。

若只复用同query中重复的原生距离值，并能恢复每一次参与决策的原值bits，则可以保持原路由、入口和搜索输出。这种优化不增加信息、不学习新排序，只减少算术。它有机会把已经观察到的局部质量信号从慢的一侧移动到快的一侧，但速度是否足够仍是未知量。Yandex与K100旧质量负点也会被完整继承。

## 2. 匹配优化后的盈亏恒等式

固定同一query集合、图/画像/metric/核/K/L与完整计时口径，令

\[
T_B=\text{Default3平均完整耗时},\quad
T_A=\text{TargetBank平均完整耗时},\quad D=T_A-T_B.
\]

对同一通用memo机制，分别定义净完整耗时节省

\[
S_A=T_A-T_A^{memo},\qquad S_B=T_B-T_B^{memo}.
\]

净节省已经包括lookup、store、query stamp/reset、映射、分支和缓存压力，允许为负。则

\[
T_A^{memo}-T_B^{memo}=D-(S_A-S_B).
\]

因此目标库比同样获得优化的默认更快，当且仅当

\[
\boxed{S_A-S_B>D.}
\]

只证明TargetBank本身变快不够；Default3也可能从上层/底层重复访问的memo获益。两边要共享同一种优化机会，不能拿新TargetBank对旧未优化默认认领方法收益。

**还须保留原默认控制。**因为S_B允许负，胜过DefaultMemo也可能仍输原Default3。四控制中的默认基线应取

\[
T_B^{best}=\min(T_B,T_B^{memo})=T_B-\max(S_B,0).
\]

目标库memo比两种默认都快的条件为

\[
\boxed{S_A>D+\max(S_B,0).}
\]

这不允许用一个变慢的共享memo默认降低门槛。默认原版与memo版输出相同，比较的是固定控制版本的速度；不按query挑计时结果。

若预声明最低QPS相对增益g>0，要求QPS_A_memo/QPS_B_memo≥1+g，则相应条件是

\[
S_A-S_B\ge D+\frac{g}{1+g}T_B^{memo}.
\]

g必须在新的结果前冻结；这里没有据旧结果挑一个易过门槛。重复计时/配对不确定性决定是否可靠，上式只给均值关系。

若最低增益相对更快默认，正确的最终门是

\[
S_A\ge D+\max(S_B,0)+\frac{g}{1+g}T_B^{best}.
\]

前面的匹配memo式仍是准确的两版本比较恒等式，但不能单独充当性能GO。

若加入已由源码确定的UpperHandoff简单控制，令默认净节省为S_H，并把原版的净节省0一并列入，则最佳默认是`T_B−max(0,S_B,S_H)`；目标memo需`S_A>D+max(0,S_B,S_H)`，最低g门也相应使用该最佳默认时间。一般固定控制集合J的门为`S_A>D+max_j S_Bj`，其中包含原版j=0。所有版本在反馈前冻结并同批完整重测，不能按query或轮次选最短值。UpperHandoff接口和原base分支前件见[局部复用审查](memo_interface_note.md)。这拓展了已有恒等式，没有测量新的S_H。

## 3. 已有完整wall缺口

E166各方法都真实付原路由、映射、固定NSG及输出费用；QPS来自完整轮次。下表引原配对完整wall之差除以4096，见[旧结果](../20260930_theory_until2200_v1/research/target_bank_frozen_curve_v1/results/analysis.json)与[核算JSON](bucket_feasibility.json)。

E166实际运行共享span+batch4研究核并回归原E99输出；此处时钟来自该研究配置，不是生产E99现场时钟。若以后选择原生产核作成本试验，各臂必须共同重测，不能搬用此D。

| 数据 / K/L | D，μs/query | 旧TargetBank ΔRecall，pp |
|---|---:|---:|
| Web K1/L800 | 36.126 | +0.659180 |
| Web K1/L1000 | 23.282 | +0.537109 |
| Web K1/L1250 | 30.529 | +0.390625 |
| Web K100/L1250 | 14.369 | −0.005127 |
| Y K1/L128 | 14.992 | 0 |
| Y K100/L256 | 15.259 | −0.159424 |

历史Web K1/L1000目标库需比默认多获得约23.3μs/query的净节省才能跨过旧均值成本缺口。实际未来应在同一新调用里重新测原版和memo版；CPU/cache状态及时序变化使旧D不能充当未来严格阈值。不得将独立计时的路由和主图相加作正式QPS，也不得用旧NDC乘一次dot微基准代替完整wall。

输出保真memo只能影响路由执行。即便做到极限，它也不能额外减少原主图的访问。E165/E166保存总NDC与最终slot，没有本提案所需的完整重复请求trace或分项耗时，所以目前缺少实际重复率、净memo收益与足够成本空间，不能给性能GO。E35另有旧128-query画像trace，历史审查只读复算表明约8.3%/8.5%物理slot重复；这支持默认也应取得同优化控制，但不能外推当前query/目标库重复率或完整wall收益。

## 4. 操作数模型只能说明必要信息

令某条query的原逻辑距离请求数为R，不同有效cache key数为C。在简化常数成本模型下，memo净节省约为

\[
(R-C)c_{dot}-Rc_{lookup}-Cc_{store}-c_{stamp/reset}.
\]

真实过程还包含间接寻址、载入和缓存相互作用。静态Web库21.055%、Y库1.645%的重复slot比例不等于(R−C)/R：query访问不均匀，重复点会影响图结构，同slot跨层重复与跨slot同target重复也是不同来源。不能据静态比例估算节省或断言不值得。

公平控制应至少含Default3原版/memo与TargetBank原版/memo，并比较更快的默认控制。若需解释重复target本身的贡献，可冻结TargetBank物理slot memo控制：原版→slot memo隔离跨层同slot重算；slot memo→real-target memo隔离不同slot同字节目标复用。控制仍保留所有物理节点/顺序，不能删点重构图。

## 5. 输出保真命题与边界

对固定query和不可变向量bank，假定native评分函数/参数/dimension/kernel/FP环境固定，且每个有效key对应相同向量bytes，评分与调用次数/slot身份无关。首次访问调用原函数并保存其完整distance bits，以后同key返回这些bits。按路由事件归纳，每次比较的输入、heap/visited转移、下一个距离请求均与原版一致，因此最终物理slot、路由分数和映射真实入口相同；固定后续主搜索恢复原响应。

该命题不要求近似HNSW选到全库argmax，也不把slot合并成图节点。tie由原图/堆原规则处理，缓存不引入新tie规则。缓存query epoch须覆盖一次完整上层+底层调用并在下个query失效；wrap/reset成本和行为须预先固定。profile向量、raw-target向量、raw-base向量或不同评分kernel是不同命名空间，不能因base ID相同就共用距离。

特别是scalar与batch4浮点归约可能不同，数学IP相等不能证明原值bits相等。本提案只在同一HNSW原评分回调内复用，不跨到NSG或另一个函数。形式证明是条件保真；未来仍需对实际native路径进行slot/距离/入口/返回/主图NDC/逻辑请求逐位核验。

## 6. 对可靠综合目标的影响

若共享优化后Web R1同预算确有完整QPS提升，同时严格恢复原TargetBank质量，可以在新来源确认其旧局部Recall信号；这是一条明确的性能假设。旧query已用于选方向，不能再作为独立确认。工作负载范围应在确认前声明，不能试完后只保留通过的数据集或K。

若速度改善但Y/K100仍质量退化，不能宣称全范围可靠改进。按已知dataset/K静态选择方法可以成为另一个事前声明的服务合同，但它不是事后掩盖负点的替换结论，本轮未提出或执行该混合部署。memo本身有作者实现前作，适合作为访问成本控制，不足以单独形成论文新贡献。

当前状态：`HOLD_MEMO_MISSING_NATIVE_TRACE_AND_MATCHED_FULL_WALL`。最小下一步是一次冻结的原生保真/成本检验，仍需后续实验授权；当前不编译或接入距离缓存、不补trace、不调ef/L/样本、不启动性能运行。
