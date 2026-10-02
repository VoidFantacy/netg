# 教师入口与目标对齐：本轮检验什么

E28给出了两个不同的缺口：真实C8三入口教师比原GT10有候选内命中空间，但共享模型降低集合CE后，精确top3的教师入口重合度反而下降。E29分别干预教师和损失，保持网络、训练预算和在线流程固定。方法定义见[执行前协议](protocol.md)，数据结论另见最终report。

## 教师不等于真实答案

每个query都有56个真实NSG三入口结果。T0先最大化hits，再按graph NDC等规则压成唯一集合。多数query的原GT10三入口已达到C8最高hits，此时更换教师主要由成本排序决定。把该唯一集合当成分类真值，会要求模型学会许多“同样命中、不同入口”的区别。

T1在这些query保留原GT10实际HNSW三入口，在确有额外hits空间的query沿用T0。两教师的候选Recall上界严格相同，成本上界不相同：T1主动丢掉一部分成本优化标签。它不是普遍更正确的教师，而是检验这些改道监督的价值。所有query仍等权，因而本轮没有同时更改样本权重。

单一教师还有未消除的限制：若许多不同三元组都有相同好结果，完整拟合其中一个集合并不是提升Recall的必要条件；入口重合度只衡量蒸馏，不定义检索质量。C8外集合在原标签中未知，本轮靠完整fit真实检索评价模型，不把未知效用填成零或外推缓存子集。

keep保留的是原HNSW实际返回的集合，不是原画像全H精确top3。两者可能不同，因此零残差模型也可能不完全匹配keep教师；精确打分训练既要保留原部署决策，又可能受到近似路由差异的影响。本轮同时保存精确重合与真实入口，不能用前者替代后者。

## 从完整集合CE到结构化margin

结构化大间隔学习通过对错误输出加任务损失来寻找最难的竞争输出；本轮采用其margin-rescaling形式。[1] 对本项目的加性三元素集合，下面可以直接推导，不需要把全H三元组逐个枚举。

设`F(S)=sum(z_h,h∈S)`，固定教师`T`有三个成员，定义：

`M(z,T)=max_{|S|=3}[F(S)+μ|S\T|]−F(T)`。

给每个非教师入口加μ，再取top3，就是括号内的精确最优集合。正常精确预测是`S_hat=top3(z)`。由于`F(S_hat)≥F(T)`，有：

`M(z,T)≥F(S_hat)+μ|S_hat\T|−F(T)≥μ|S_hat\T|`。

这给出可逐query检验的教师漏选上界。M=0要求所有教师分数比所有非教师至少高μ；单次目标下降仍不保证每条query或平均入口错误都下降。加上归一化参数化、锚定正则和固定优化预算后，更不能由上界推出最终NSG收益。

原集合CE的全H精确MAP同样是top3。E28的反例表明，某次CE下降可以伴随MAP变错；这只是优化轨迹上的事实，不是CE普遍不一致的证明。关于top-k分类的文献区分校准性、最优风险和有限训练轨迹，且其单类别标签假设不同于这里的三入口教师，更不同于NSG有限搜索的Recall。[2] 因此本轮不宣称hinge具有比CE更好的普遍校准理论。

## 两轴比较的解释范围

cost_ce、keep_ce、cost_margin、keep_margin四格使用相同GT10锚点和共享linear。`keep−cost`在同一损失下解释教师替换的总效果；`margin−CE`在同一教师下解释损失替换的总效果。交互是两个教师差值之差。它们都是这组固定设置下的干预，不能自动解释为等Recall加速。

两种损失虽然使用同一温度、λ和优化器，却不具有相同梯度分布或有效锚定强度。margin可能让大部分满足条件的query停止推动；CE持续分配概率质量。本轮同时报告W漂移、梯度、组内对齐与训练轨迹。若margin的变化更小，不能把保守改动带来的影响全部归因为更好的排序目标；反之，也不能把教师对齐提升当成检索质量提升。

离线共享linear仍导出静态单位W，在线原始query只对W打分并运行一次微型HNSW；没有增加query端表达能力，没有学习主图或NSG搜索过程。M只监督入口成员，不能表示任意三入口互补效用。

## 证据链和停止位置

本轮要求完整链条：原始三入口标签→教师变更组→模型精确top3→实际HNSW三入口→原NSG hits/图工作→独立端到端wall。exact诊断、fit真值和正式QPS各自标记。最终报告保留全部四格和原有基线，即使某格无改善，也不临时换seed、margin、正则或epoch。

fit/cal/audit/validation均有历史使用；margin=.1、λ100和模型容量只测一套，原图/H只有一个构建。三次wall描述计时波动，query bootstrap描述本次查询样本变化。新盲测、不同图/seed、漂移匹配控制和更广泛的优化结论都不在本轮已测证据中。

## 一手来源

1. Tsochantaridis, Joachims, Hofmann, Altun. *Large Margin Methods for Structured and Interdependent Output Variables*, JMLR 2005，§2.2.4、式8和命题2。[原文](https://www.jmlr.org/papers/volume6/tsochantaridis05a/tsochantaridis05a.pdf)。本轮采用已知结构化损失形式，没有移植论文性能数字。
2. Yang, Koyejo. *On the Consistency of Top-k Surrogate Losses*, ICML 2020，§2–4。[原文](https://proceedings.mlr.press/v119/yang20f/yang20f.pdf)。用于限定校准性与有限优化/不同标签任务的关系，不将其结论直接套到NSG。

两份原文与hash见[sources/inventory.json](sources/inventory.json)。E28本地机制、原标签与代理反例见[原报告](../20260911_gt10_shared_transform_v1/report.md)，新测量不与旧QPS混批。
