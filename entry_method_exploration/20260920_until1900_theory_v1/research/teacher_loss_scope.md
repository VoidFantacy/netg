# 真实集合监督的损失：不能把失败统一归因于拟合能力

2026-09-20。重新逐行核对E104的train.py、analyze_labels.py、六模型training_runs以及已完成的C8缓存诊断。这里只读历史汇总/源码，无新训练、推理或搜索；不恢复旧QMLP/WFree版本。

## 原损失实际是什么

E104对固定C8的56个三入口真实搜索计算等K分数`100×hit1+hit100`，所有达到最大分数的集合构成T。模型为每个hub输出一个分数，集合分数是三个分数之和。损失是

`ell(s,T)=logsumexp_all S score(S) − logsumexp_S in T score(S) = −log P_s(T)`。

它不是对所有集合按效用softmax后拟合边际的KL，也不是逐hub多标签独立交叉熵。不能先假定错误损失，再用“结构化损失”重命名一次训练。集合真实效用标签已经存在，训练没有只依靠几何标签。

## 模式选择与总概率质量的条件界

设m=|T|且存在非最优集合。若最高概率的集合不在T，其概率至少不小于每个最优集合。因此`P(T)≤m(1−P(T))`，即`ell≥log(1+1/m)`。所以`ell<log(1+1/m)`是实际argmax属于T的充分条件；m越多，这个充分阈值越小。所有集合最优时模式总是正确，单独处理。

这说明均值loss下降不保证每条query的模式正确，但不证明该损失本质不一致：如果能把概率集中到任何一个可表示的最优集合，ell可以趋于0且模式正确。固定查询存在几何witness，不等于一个共享低秩query网络能同时实现所有query的witness，也不等于未见query上的正确性。

## 已有数值已经区分了几种问题

| 数据 | 模型 | fit CE起点→终点 | fit C8最优集合比例 |
|---|---|---:|---:|
| WebVid | QMLP | 1.5909→0.9871 | 41.99%→64.75% |
| WebVid | WFree | 1.5909→0.0322 | 41.99%→100% |
| Yandex | QMLP | 1.4328→0.8854 | 56.93%→68.31% |
| Yandex | WFree | 1.4328→0.0393 | 56.93%→100% |

WFree已经在已标注的fit动作族达到最优集合100%，不能说其失败源于该动作族内始终学不会或loss无法转换成动作。旧cal C8最优比例却只有Web45.12%、Y59.38%，Identity为43.95%/58.40%；源样本/动作族/分布迁移是后续缺口之一。WFree的cal全H质量反而高于同模型C8限制，故也不能仅凭训练外动作比例推出限制候选就能恢复收益。

QMLP在Web fit上，限制C8的真实R1/R100为79.4922%/66.9067%，全H精确则76.0742%/65.5991%；训练动作族与部署动作族确实造成损失。但限制C8后的cal相对同C8 Identity只余R1+0.1953pp/R100−0.0684pp；Y为R1−0.1953pp/R100−0.0117pp。修复动作范围也没有自动解决跨query迁移。数字都来自原缓存诊断，不是这次新实验。

当前不因此更换loss温度、anchor、rank、epoch或追加同类网络。后继若提出图条件特征，应先证明它提供了旧原始query/目标几何之外的可迁移操作结构，并保留同监督简单控制与实际动作合同，而不是只声称网络更强。

[原损失](../../20260920_query_representation_pilot_v1/src/train.py) · [原teacher构造](../../20260920_query_representation_pilot_v1/src/analyze_labels.py) · [六次训练记录](../../20260920_query_representation_pilot_v1/results/training_runs.json) · [原C8诊断](../../20260920_query_representation_pilot_v1/results/cached_support_diagnostic.json) · [完整复盘](../../../experiment_history/98_query_representation_pilot.md)。
