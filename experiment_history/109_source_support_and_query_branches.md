# 109｜目标支持与query内部搜索分支

2026-09-20，E112停止后的解释性审查，不是E113新方法试验。三组开放数据QGT5K/画像fit20K/曝光开发4096，已有GT100。Y QGT有4983个唯一GT1，开发GT1仅0.9766%在QGT GT1中出现、16.1133%在QGT GT100中出现；训练组之间也稀疏（0.835%/17.135%），不足以将失败主要归因于源分布漂移。Web重合相应14.9902%/72.1680%。24576个闭邻域并集成员与E112原标签一致，全部输入重新核验，0.900秒，0新搜索/训练/GT/图；仅读取开放载荷与来源metadata。

GraphH的Y开发43条GT1证书，按QGT GT1/仅GT2–100/未见GT100分解为22/10/11；大多数开发query的GT1未在QGT100出现。该分解不选子集报Recall。原GT10通过目标几何归属让不同ID共享query支持，ESS中位Web132.28/Y60.08；不是同预算优越性或因果证明。

补充基础界：首行闭邻域≤65，使等K证书≤82.5%，低于Y默认L128等K实测约87.2083%；该下界自身不足以证明完全替换默认。标准经验次模近似与总体/路由/实际搜索残差分开，未把训练保证当作泛化或性能保证。

重新核对E104真实集合损失为−log最优集合总概率，非效用softmax边际KL。WFree在两集fit C8已达100%最优集合，而cal仅45.12%/59.38%；增加拟合能力、限制动作支持均不能单独解释或修复全部失败。原模型与停止门保持。

另4次冻结kernel合成调用验证：同强连通图、同唯一GT1、同hop距离，query在GT1区域内微变可反转两入口效用。toy不是NSG构图产物，不能推断真实数据频率或不可学习性。它引出对实际搜索比较边界的重复支持研究，尚无新特征模型或性能候选。默认Web soft/Y hard、生产E99保持，整体目标仍持续至19:00。

[支持报告](../entry_method_exploration/20260920_until1900_theory_v1/research/source_support_v1/report.md) · [经验保证边界](../entry_method_exploration/20260920_until1900_theory_v1/research/empirical_guarantee_and_search_gap.md) · [损失审查](../entry_method_exploration/20260920_until1900_theory_v1/research/teacher_loss_scope.md) · [合成分支反例](../entry_method_exploration/20260920_until1900_theory_v1/research/query_branch_stability_v1/report.md)。
