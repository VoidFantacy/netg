# E112：首行覆盖入口设计的理论信息门

2026-09-20。**STOP_ONE_HOP_H_DESIGN_INFORMATION_GATE**：WebVid通过预锁信息门，Yandex三个条件全部失败，按跨数据集协议停止本版H设计，不训练画像或执行真实搜索。Web GT10-soft-t1、Yandex GT10-hard及生产E99保持；这不是新部署Recall/QPS结果。

## 推导与唯一干预

单入口h首先完整展开闭出邻域D(h)={h}∪N_out(h)。在L≥K、GT与搜索距离及并列语义一致的条件下，D(h)中的GT_K成员会保留到最终返回。因此c_K=|GT_K∩D(h)|/K是条件下界。指定GT1 ID另需严格第一名或一致并列规则；这里用原DC检查GT1/GT2，非严格query只将K1证书置0，全部query及原GT/Recall保留。GT100外部排名/浮点一致性仍是前提，未新增GT101验证。

用等K分数c=(c_1+c_100)/2定义F(H)=平均_q max_h c(q,h)。它是标准单调次模目标；精确最大边际贪心有1−1/e近似保证。这个保证只约束QGT训练目标，不保证开发覆盖、真实搜索或可部署路由。候选遍历全部真实base节点，在与原QGT-Cover相同的QGT5K、相同H815/821、同一底层NSG下选择GraphH。OriginalH与同QGT的GT1频率FrequencyH是固定控制。

[完整推导及前作](research.md) · [冻结协议](protocol.md) · [配置](config.locked.json)。E111固定旧H的排名核心证书已停止；本版改变H、只用首行邻居，没有扩大m/路径网格。H在本runner读取开发载荷前冻结；开发4096/集此前已曝光，不是新盲测或held-out。

## 实际覆盖及门槛

数值均为百分数，F是知道GT后在H中选择的条件覆盖。GT1_any与GT100_max分别取各自最优入口，二者均值不必等于同一入口的F。

| 数据 | H选择 | QGT F | 开发F | 开发GT1存在覆盖 | 开发GT100最大覆盖 |
|---|---|---:|---:|---:|---:|
| WebVid | OriginalH | 13.9348 | 6.4498 | 11.0107 | 1.9756 |
| WebVid | GraphH | 25.1048 | 10.5004 | 18.2373 | 2.9724 |
| WebVid | FrequencyH | 16.0748 | 8.2351 | 14.4775 | 2.1440 |
| Yandex | OriginalH | 9.4188 | 0.6600 | 0.8545 | 0.4656 |
| Yandex | GraphH | 17.6002 | 0.8004 | 1.0498 | 0.5540 |
| Yandex | FrequencyH | 9.3660 | 0.6176 | 0.7812 | 0.4558 |

| 数据 | 开发配对对比 | F变化pp | 98.75% bootstrap区间 |
|---|---|---:|---:|
| WebVid | GraphH − OriginalH | +4.0505 | [+3.3158, +4.8103] |
| WebVid | GraphH − FrequencyH | +2.2653 | [+1.5763, +2.9736] |
| Yandex | GraphH − OriginalH | +0.1404 | [-0.0996, +0.3916] |
| Yandex | GraphH − FrequencyH | +0.1829 | [-0.0570, +0.4351] |

Web GraphH在默认L128的1011条K1失败query中有96条条件可恢复，占全4096条的2.3438pp；旧H51条、频率H75条。Yandex默认384条失败中GraphH与旧H均0条，频率H1条。这里假定免费知道何时保留默认、何时改用证书入口，属于特权条件恢复量，不是执行过的Recall增益。

预锁门要求两集F相对旧H≥2pp、四个对比区间下界均>0、对默认失败的条件恢复量≥1pp。Web全过，Y全不过，因此整体停止。不能依据Web局部信号改为单数据集继续，或降低Y门槛。

## 这次解释了什么

GraphH的训练收益主要来自真实出边，不能简单归因于把热门GT1放进H：Web的开发非自节点GT1覆盖16.5771%，自节点2.4658%；Y相应1.0010%与0.0488%。GraphH与旧H重叠仅38/815、20/821，QGT至少两个query提供GT1证书，但每hub中位数只有2条。Y训练F17.6002%下降到开发0.8004%，连很保守的实际目标覆盖也难延续。

这支持“精确目标ID的首行覆盖在当前Y数据/样本/容量下信息不足”，不证明整个图无可迁移结构，也不证明所有H选择失败。稀疏支持、选择偏差、目标分布变化可能共同作用；本阶段未分离各自因果份额。GT10仍可通过多行搜索获得很高Recall，不能把小的局部下界误作真实效用上界。后继回到数据分布、有限beam动作稳定性和学习目标的理论审查，不扩本版H/m/跳数/seed/预测器。

## 核验、成本与修正

全部稀疏行顺序/范围及整数分数组合核验；1636步贪心前缀回放和全局边际上界检查；独立预定64条query/角色/集×所有H，共628224组成员核验。QGT稀疏/稠密分数逐元素相等。0新NSG、ANN、GT、底层图、路由图或梯度/画像训练；有新图派生标签和离线H优化。四个标签进程含加载合计49.734秒，编译8.679秒，最大RSS10.169GiB；不当作QPS。

分析两次因NumPy布尔值JSON序列化失败；初次修正遗漏另一条件，第二次补齐。原源码、日志、四张CSV与两次修正记录均保留；第三版仅转为Python bool，全部CSV SHA相同，门槛/样本/数值未改。首次读取新质量结果发生在最终分析完成后，失败时只查看traceback与源码。最终独立分析耗时4.446秒；失败分析日志时间单列，不隐去。图已目视检查。

[覆盖表](results/certificate_coverage.csv) · [配对区间](results/paired_information.csv) · [条件恢复](results/conditional_rescue.csv) · [支持量](results/selected_H_support.csv) · [门](results/gate.json) · [图](figures/conditional_coverage.png) · [数值核验](reviews/numeric_verification.json) · [执行成本](reviews/jobs.json) · [第一次分析失败](reviews/analysis_serialization_failure/review.json) · [第二次分析失败](reviews/analysis_serialization_failure_v2/review.json) · [完成审计](reviews/completion_audit.json)。
