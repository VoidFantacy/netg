# 稀疏目标ID为什么不能靠记住训练答案解决

2026-09-20。对已完成source_support统计的事后理论解释，不重新读取query/GT、不训练或搜索。采用经典Good–Turing思想作为IID参考模型，不宣称当前源分区和字节去重采样已经满足该模型。

## 基本恒等式

设真实GT1 ID为离散随机变量Y，其固定分布为p_j。n个IID query产生n个Y；N_j是ID j的次数，N_1^(count)是只出现一次的不同ID数。训练样本未覆盖的下一次目标概率为随机缺失质量

`M_n = Σ_j p_j 1{N_j=0}`。

经典Good–Turing统计量为`N_1^(count)/n`。直接展开二项概率，有

`E M_n = Σ_j p_j(1−p_j)^n`，

`E[N_1^(count)/n] = Σ_j p_j(1−p_j)^(n−1) = E M_(n−1)`。

因此该统计量对E M_n的期望偏差非负，且

`0 ≤ E[N_1^(count)/n − M_n] = Σ_j p_j²(1−p_j)^(n−1) ≤ (1/n)(1−1/n)^(n−1) ≤ 1/n`。

最后一步把一个p_j移入求和权重，再取`p(1−p)^(n−1)`在[0,1]的最大值。这里控制的是**期望偏差**，不是单个样本的绝对误差或置信区间。

若一个预测器只能输出训练中出现过的精确目标ID，它的条件命中率最多为1−M_n。但GT10/NSG通过图搜索能够返回未见过的ID，不受这个lookup-only限制；图邻接也可能把已见节点连接到未见目标。不能拿缺失质量当GT10、GraphH或所有图学习方法的Recall上界。

## 与已经观察到的统计对照

| 数据/目标来源 | 原n | 单例ID/n：IID参考缺失质量 | 后续来源 | 实际GT1未在原GT1集合出现 |
|---|---:|---:|---|---:|
| Web QGT | 5000 | 84.8800% | fit20K | 84.9500% |
| Web QGT | 5000 | 84.8800% | development4096 | 85.0098% |
| Web fit | 20000 | 67.4300% | development4096 | 68.2373% |
| Yandex QGT | 5000 | 99.3400% | fit20K | 99.1650% |
| Yandex QGT | 5000 | 99.3400% | development4096 | 99.0234% |
| Yandex fit | 20000 | 96.8750% | development4096 | 96.7773% |

数量级相符，提示目标ID稀疏并不是仅凭“开发源行较远”才能解释的现象：相同问题也出现在QGT到另一训练分区。由于这些数值已被观察、来源规则不同且去重后不必IID，这不是前瞻预测验证，不足以证明没有分布变化，也不应给出未经校准的置信度。

这为GT10的共享粒度提供了有用解释：它把具体目标映射到几何区域，积累相关query方向，然后让原图继续查找实际目标；它不是把每个目标ID单独记为分类答案。E112的首行证书与E113的具体节点比较对都很局部，当前支持不足；这说明应检查共享粒度，而不是看到图信息就立即增加网络参数。它仍未证明GT10区域标签能够正确排序有限beam效用。

## 来源与范围

Good–Turing及缺失质量浓缩的一手讨论见[McAllester与Ortiz，JMLR 2003，§1](https://www.jmlr.org/papers/volume4/mcallester03a/mcallester03a.pdf)。非IID轨迹下经典估计可能有偏，见[Pananjady等，JMLR 2024](https://jmlr.org/papers/volume25/24-0511/24-0511.pdf)的摘要与引言；本页不移植其Markov估计器或完整定理。上述期望恒等式为基础概率的直接推导，不声称新理论。

原项目统计：[目标支持](source_support_v1/target_support.csv)、[来源重合](source_support_v1/source_target_overlap.csv)、[数据角色与边界](source_support_v1/report.md)。GT1 ID与训练目标数10是不同概念；本页没有新增K10评测。
