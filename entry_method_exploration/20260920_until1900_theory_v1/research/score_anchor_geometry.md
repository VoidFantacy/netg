# WFree的score anchor控制了什么

2026-09-20。核对E104当前源码：WFree自由导出静态W，训练以原P的全H分数作二次锚定，lambda=10；不归一化每行W。本文不更改正则/数据/模型，也不重启该停止版本。

令单位fit query组成Q∈R^(n×d)，Delta=W−P，C_fit=QᵀQ/n。代码中的平均分数漂移恰为

`D_fit = ||Q Deltaᵀ||_F²/(nH) = tr(Delta C_fit Deltaᵀ)/H`。

它控制fit query的分数变化，不等于逐行参数的欧氏距离。若C_fit正定，令每行`v_h=C_fit^(1/2) delta_h`，正则成为普通欧氏二次项；方差较小的query方向允许更大的参数位移。由此不能直接认定正则错误，因为部署同分布时分数变化正是相关控制对象。

对另一组query的C_new，若`C_new≼k C_fit`，则任何Delta都有`D_new≤k D_fit`。C_fit正定时最小此类k是`lambda_max(C_fit^(-1/2) C_new C_fit^(-1/2))`。这是有限矩阵的代数上界，不是总体分布漂移的显著性检验。小校准集和高维协方差估计本身也会使最坏方向比值较大；应同时检查实际已学Delta的D_new/D_fit，不能只报最大的广义特征值。

另一个明确的支持限制来自C8集合损失。hub h只有在query的候选C8内时才出现于该query的教师数据项；若56动作全部最优，该query的数据项恒为0。因此每hub数据梯度属于其有效候选query向量的张成空间，秩至多为`min(d,n_h)`。这是可能提供监督的维度上界，不能把n_h当作独立有效样本量，也不假定每个出现都产生非零梯度。

若自由W到达可微一阶驻点，`C_fit delta_h`属于上述监督张成空间，因为锚定梯度为`(2lambda/H) C_fit delta_h`。当C_fit正定时可写成一个带C_fit逆变换的表示定理。它没有声称实际40轮Adam已经到驻点；也不表明n_h<d就必定过拟合，因为全Q锚定仍约束所有行。

后继只核对旧WFree的实际分数漂移、全体hub支持与协方差界；如果实际新query漂移没有放大，就不能把最坏方向理论直接当作已证失败原因。不会据此追加lambda/白化/归一化/新数据训练，也不会因为某个模型名字更复杂就跳过真实搜索迁移问题。

[原训练源码](../../20260920_query_representation_pilot_v1/src/train.py) · [冻结配置](../../20260920_query_representation_pilot_v1/config.locked.json) · [损失范围](teacher_loss_scope.md)。
