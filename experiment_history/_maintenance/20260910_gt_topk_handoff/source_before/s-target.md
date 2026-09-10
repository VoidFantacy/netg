# ACSG 当前状态与接续边界

2026-09-10。用户授权的E23三入口排序探索已完成；实测结果见[summary.md](summary.md)，实现见[spec.md](spec.md)，详细证据见[E23复盘](experiment_history/12_three_entry_rank_exploration.md)。

## 当前判断

`EXPLORATORY_SMALL_RECALL_SIGNAL_NO_CLEAR_QPS_GAIN`：相比matched Fast20K三入口，有小幅Recall增益；完整W没有一致胜过rank8，QPS未形成明确整体优势。特别是Yandex，rank8五L Recall都高于Full，也都高于matched Fast20K，但多数点QPS基本持平或略低。该版本已完成并收口，不将它作为已验证的Fast替代品。

## 已完成的授权范围

[协议](entry_method_exploration/20260910_three_entry_rank_v1/protocol.md)：双数据集fit20K、cal1024、audit1024；96万逻辑真实三入口标签、88万实际标注调用；Full/rank8各三λ、共12个候选；按cal选择后冻结；validation各2K、单构建、NSG/Fast30K3/Fast20K3/Full3/Rank8-3、五L、单线程、每点一次warmup/独立plain wall和timer外完整NDC/输出核对。50点及100000个query输出验收完成，held-out未打开。

一份模型适用于全部五L。训练标签在L128下产生，模型本身不输入L；所有方法每query入口跨L一致。cal选中Full/rank8在WebVid均λ10、Yandex均λ0.1，validation没有参与重新选择。

## 四问题调研完成，后续方法尚未选定

用户随后要求调研GT入口是否需连通性、OOD聚类、rank8最优性及HNSW拉伸。已完成[报告](entry_method_exploration/20260910_ood_hubs_clustering_router_research_v1/report.md)与[14项一手阅读记录](entry_method_exploration/20260910_ood_hubs_clustering_router_research_v1/papers.md)，状态`RESEARCH_COMPLETE_METHOD_UNSELECTED_UNRUN`。仅复核源码和旧结果，没有聚类、标注、训练、ANN构建或新评测。

研究建议依次为：①保留现有H，定义GT-topK软画像，先隔离GT1归属遗漏；②以真实有限L搜索作用组织分组/在小候选集挑入口，处理三入口互补，为较重备选；③固定W，以`p′=Ap,q′=A⁻ᵀq`保分数并重建Micro-HNSW，单独研究导航效率。当前H已有免费oracle空间，不必先替换全部入口。vMF/最小支持层次聚类是分组备选实现；rank4/8/16/32与Full只是目标稳定后的容量比较草案，不自动启动。

后续方法需明确与旧centroid/BTG/rerouter/E23的区别。度数和GT-topK几何都不是有限beam效用保证；成对拉伸只作用于画像图，若改NSG主图则另立图身份并更新下游标签依赖。具体参数、样本、预算和进退门由选定方案的新协议确定；本次调研不是新实验GO。已有E23 validation已被查看，不能重新称全新盲测；正式比较仍取包含路由全部成本的单线程端到端Recall–QPS。

## E23仍需保留的问题与边界

当前实验已把三个问题分开：完整W固定目标能够充分优化；低秩虽目标较高却在Yandex最终搜索更好；真实联合收益到静态top3分数的代理仍有差距。下一步优先检查联合收益目标与最终top3选择的对应关系，以及训练/部署的泛化差异。已观察到同一query、同一a/b的偏好随context反转，但未证明这是全部差距的原因。

保留Full作优化参考、rank8作正则化对照。共享hub端MLP会改变参数共享和优化，但对固定H仍导出固定W，不能自动消除这些条件偏好冲突；query端MLP或策略梯度也尚无本轮实证。任何后续选择需说明针对哪项已观测问题、与E23的实质区别及小型验证范围，再建立新协议；本轮不自动增加MLP、rank、λ、seed、标签或计时。

今后比较继续优先单构建、小validation与必要对照；正式查询始终单线程，显式OMP/OpenBLAS/MKL=1并核验实际线程，一次只运行一个被测方法。最终结论取完整Recall–QPS，NDC、训练损失或少量同L Recall仅作诊断。完整从零离线成本还需包含当前候选提议依赖的旧single标签，不能只报88万新增联合调用。

旧E22大矩阵、额外基线队列均不恢复。C继续`NO_GO_UNCONDITIONAL_HEADROOM_STOP_C`，不做C3/C4或联动；D和效用树不自动切换。原数据、源码、图、标签、模型、日志和结果不清理或覆盖。
