# PyTorch、低秩与入口学习：论文及现有实现复核

2026-09-10。状态：`RESEARCH_COMPLETE_METHOD_UNSELECTED_UNRUN`。本轮只做论文阅读、源码检查、既有结果分析和文档更新。没有生成搜索标签、训练模型、构建ANN或运行新的评测。研究问题来自用户：“路线是对的，但现在PyTorch和梯度下降低秩矩阵合适吗？”

**结论：PyTorch适合作为训练工具；梯度学习也合理；但现有rank8、同学习率SGD、单入口soft效用和自由重映射的组合，没有依据被认定为合适的最终方法。建议先固定真实入口身份，以真实三入口搜索收益构造排序监督，用带Fast先验的完整入口矩阵建立可解释的参考，再以同目标的低秩版本作对照。离线共享MLP是有文献依据的备选。** 这是研究建议，尚未选定或实现。

## 1. 先分清四个选择

| 层次 | 本轮判断 | 理由 |
|---|---|---|
| 训练工具PyTorch | 保留 | 能计算梯度，不规定我们必须使用MLP、低秩或某种损失；旧在线程序加载的是已导出的W |
| 参数化：完整W、低秩、共享MLP | 需要比较 | 决定容量、参数共享及优化几何；当前没有证据支持固定rank8 |
| 学习目标 | 优先修正 | 实际部署要三个入口共享原搜索过程，旧训练却奖励单入口；把softmax换成soft top-k不会自动得到联合收益 |
| 优化方法 | 随目标选择 | SGD、Adam类或确定性凸优化只是求解器；更好地拟合错误目标仍可能降低Recall/QPS |

论文支持“离线学习、在线便宜”的总体结构，没有直接证明我们的低秩维数、训练损失或入口映射合适。

## 2. 现有失败能说明什么

来源为[原训练源码](../20260909_ab_experiment_v1/src/train.py)、[锁定配置](../20260909_ab_experiment_v1/config.locked.json)、[冻结模型记录](../20260909_ab_experiment_v1/exploration_5point_v1/reviews/frozen_model_profile.json)和本目录[evidence.json](evidence.json)。以下都是seed20260828、L128标签训练出的旧模型，未重跑。

| 数据集 | fit Recall：初始化→联合候选 | cal Recall：初始化→联合候选 | 候选残差范数 | 映射覆盖真实入口 |
|---|---:|---:|---:|---:|
| WebVid | 75.1765%→78.2585% | 74.9805%→74.6484% | 0.0001850 | 462/815 |
| Yandex-IP | 90.2990%→93.4285% | 89.6289%→89.2383% | 0.0001813 | 435/821 |

联合候选的W几乎未动，大部分槽位改变了真实入口映射。算法先把fit查询按hard top1槽位分组，再为每组从全H选择总命中数最高的入口；它没有对每槽样本量、选择偏差或多对一集中作约束。20K/约800≈25只是平均量，实际分配不均。**VZ的低秩约束并不约束离散映射pi，所以低秩不能替这种小样本全入口选择提供保护。**

另一方面，旧W-only训练确实更新了W，cal也有很小的正值：WebVid约+0.2441pp，Yandex约+0.0293pp。这排除了“所有连续分支都完全学不动”的说法，但不是三入口收益证据。联合候选的微小残差也不能证明rank8容量已经耗尽；其范数远低于约14的约束半径。

旧完整WebVid validation10K的L128记录提供了额外成本线索：与同构建Fast20K单入口相比，联合单入口的平均图NDC约从1667.94升至1804.99，路由NDC几乎相同；三次计时的路由wall中位数约0.0695/0.0694秒，而图搜索约4.915/5.351秒。该范围内，退化主要出现在后续搜索，并非在线执行了PyTorch。分项计时与完整wall来自独立区间，不能简单相加。这只解释这份旧WebVid完整记录，不能冒充最终双数据集五点2K的逐点分项归因。[原始记录](../20260909_ab_experiment_v1/single_thread_v1/results/validation/webvid2_5m_light_v1/seed20260828/results.json)

## 3. 低秩有没有必要

[LoRA（ICLR 2022）](https://arxiv.org/abs/2106.09685)研究的是大模型微调：冻结预训练权重，以低秩增量节省训练参数，并可在部署前合并权重。其语言模型结果不能证明Fast入口画像的正确修正必然位于8维子空间。

我们的矩阵很小。按当前构建实际H和维度计算：

| 数据集 | 完整W参数量H×d | rank8因子参数量8(H+d) | 完整float32 W大小 |
|---|---:|---:|---:|
| WebVid：815×512 | 417,280 | 10,616 | 1.592 MiB |
| Yandex-IP：821×200 | 164,200 | 8,168 | 0.626 MiB |

完整W不意味着完整搜索全H：训练后同样把H个d维向量写入Micro-HNSW。旧低秩实现也已经折叠成这种稠密W。因此**在当前部署方式下，rank8没有独占的在线存储或矩阵乘法优势**。学到的向量几何仍可能改变HNSW访问量，所以不能据同尺寸声称实际QPS相同。

低秩仍有价值：它强制入口共享少量修正方向，可以减少数据需求。但它也会限制每个入口可学的修正，而且因子乘积使优化非凸。完整W容量更大，也更可能过拟合；推荐它首先是为了建立容易诊断的参考，不是认定它最终泛化最好。

## 4. 当前梯度下降的具体问题

采用列向量记法，W=P0+VZ，V为d×r、Z为r×H。旧代码V随机正交、Z=0，两个因子使用相同学习率的无动量SGD，逐epoch进行QR及半径投影，每个提案还要通过hard fit命中数不下降的验收。

设G为损失对完整W的梯度。初始化时：

\[
\nabla_V\mathcal L=GZ^T=0,\qquad \nabla_Z\mathcal L=V^TG.
\]

因此没有“两因子全零导致完全无梯度”的错误；但在第一次未触及半径约束的SGD更新中，完整权重仅沿\(-\eta VV^TG\)改变。梯度裁剪会缩放步长，不改变这个初始子空间限制。此推导来自当前代码，不是性能实验。

[LoRA+（ICML 2024）](https://proceedings.mlr.press/v235/hayou24a.html)在大宽度网络下指出两因子相同学习率会阻碍有效特征学习，提出不同学习率；[LoRA-Pro（ICLR 2025）](https://arxiv.org/html/2407.18242v3)分析因子更新对应的完整权重更新与全参数梯度的差异。它们支持检查优化几何，但我们的QR、裁剪和离散验收不同，不能照搬论文学习率比例并承诺有效。

更直接的问题是旧损失。记映射后单入口收益为u_j，softmax概率为p_j，单query损失为\(u_{max}-\sum_jp_ju_j\)，则

\[
\frac{\partial\mathcal L}{\partial s_j}=\frac{p_j}{\tau}\left(\sum_kp_ku_k-u_j\right).
\]

即使全H中还有更好的入口，只要pi当前保留的动作收益全部相同，梯度仍为零；常数oracle基线不会把已被pi删除的动作重新带回来。另一个风险是hard fit单调验收可能拒绝需要暂时调整排序才能获得后续收益的轨迹。这两点是机制分析，尚未被单独消融量化。

所以，不能把“改成AdamW”当成主要修复。若使用Fast锚定，正则项应明确作用于W−P0；默认对W做weight decay是向零收缩，与向Fast先验收缩不同。

## 5. MLP可以放在哪里

[GATE（KDD 2025）](https://arxiv.org/html/2506.15986v1)融合hub语义/拓扑信息学习入口表示，再在这些表示上构建导航索引。核对的作者代码在线使用原始query检索top3；MLP参与离线生成表示。[Learning to Route in Similarity Graphs（ICML 2019）](https://proceedings.mlr.press/v97/baranchuk19a/baranchuk19a.pdf)也学习可预计算的节点表示，但它改变图内路由，与我们只改入口的范围不同。

可借鉴的备选是共享hub编码器：

\[
w_e=p^0_e+f_\psi(x_e),\qquad s(q,e)=q^Tw_e.
\]

x_e可以是已有入口画像，拓扑特征是否值得增加需另论。所有hub共用同一个小MLP；离线算出W后，在线仍只查HNSW。它让训练参数跨入口共享，有机会缓解稀疏入口的数据不足，但共享是否有用取决于特征和真实效用是否相关。

这里必须区分：**hub端离线MLP对固定H最终仍生成一个矩阵W，并没有让原始query上的评分变成非线性。** 它改变的是参数共享与优化方式；自由完整W已包含这些固定向量的表达能力。若要真正学非线性query边界，需要query端MLP或更丰富的评分函数，一般不能精确折叠回原始query的固定线性内积，查询成本也会变化。

另外，[OP-LoRA（CVPR 2026 Workshop）](https://openaccess.thecvf.com/content/CVPR2026W/ECV/papers/Teterwak_OP-LoRA_The_Blessing_of_Dimensionality_with_Overparameterized_Low-Rank_Adaptation_CVPRW_2026_paper.pdf)用MLP生成低秩因子、训练后丢弃MLP，强调相同rank下改变优化路径。这是相邻任务的补充证据，不是图入口学习的直接验证；应准确保留Workshop身份。

GATE的hop/对比监督、LRSG的路由监督也都不能直接替代我们的固定预算GT10联合搜索收益。作者发布代码和论文还有实现口径差异，见[papers.md](papers.md)。

## 6. 优先建议：固定真实入口，学习三入口条件下的排序

先令每个向量对应一个固定、互异的真实hub。在线top3就得到三个不同入口，不再让自由多对一pi用每槽少量样本从800个动作中挑赢家。训练保持Fast先验：W=P0+Δ，惩罚\(\|\Delta\|_F^2\)。训练样本不足的入口因此更有理由留在先验附近，但这不是泛化保证。

监督要回答具体问题：**另外两个入口相同的情况下，第三个位置用a还是b，让原NSG搜索更好？** 定义

\[
\delta(q,T,a,b)=U_L(q,T\cup\{a\})-U_L(q,T\cup\{b\}),
\]

其中T含两个不同入口，a、b在T之外；U是原共享搜索kernel实测的Recall@10。T是离线比较的条件，不是强制在线保留的两个固定anchor。应覆盖有限的不同T，不能恢复E20已经撤下的固定anchor或固定C8普遍限制。

借鉴[RankNet（ICML 2005）](https://www.microsoft.com/en-us/research/wp-content/uploads/2005/08/icml_ranking.pdf)的成对logistic排序形式，可构造

\[
\mathcal L(W)=\frac1N\sum_q\sum_{(T,a,b)\in\mathcal P_q}
\alpha_{qTab}\log\!\left(1+\exp\left[-\operatorname{sign}(\delta)q^T(w_a-w_b)\right]\right)
+\lambda\|W-P0\|_F^2,
\]

\(\alpha\ge0\)由收益差产生，并在每个query内部归一化，避免多采样query获得更多权重。零收益差不强迫唯一赢家；无有效偏好的query仍保留在完整评测分母。收益差权重与三入口条件设计是本报告提案，不能归为RankNet论文已经验证的内容。

**固定训练pair、权重、映射且不对W做非线性归一化时，该目标对完整W是凸的；λ>0时为强凸。** 因为每个score差是W的线性函数，softplus与二次锚定项均凸。可用确定性梯度/拟牛顿方法求解，并检查目标与梯度范数；这提供清楚的优化诊断。换成VZ或MLP后不再有这个凸性。自适应换pair会改变阶段目标，不能引用固定目标的收敛结论覆盖全过程。

这一方案仍只是联合收益的排序代理：同一a/b在不同T下可能偏好反转，一个不输入T的单项评分无法同时表达全部互补关系；较低排序损失也不保证最终top3的真实Recall或QPS更好。必须保留完整top3输出后的真实联合验证。

旧单入口标签可帮助提出少量值得比较的候选，不能把三个single的分数相加、取max或独立GT并集伪装成真实三入口标签。无需枚举\(\binom H3\)，但真实组合的采样范围、调用上限和split需在后续协议明确；本轮没有授权或执行该步骤。

对之前“再增加一对一B”的建议也应收窄：若W完全自由、候选H固定，双射pi在精确评分的函数类上可被W的列置换吸收，不增加可表达的query→入口规则。Fast锚定、低秩等约束会影响这个等价性；HNSW近似过程也需另查。因此B不是必需组件，应等A的三入口参考建立后再判断是否有独立价值。

## 7. 三条候选及推进顺序

| 候选 | 用什么学习 | 在线形式 | 当前建议 |
|---|---|---|---|
| Fast锚定完整W＋真实三入口条件排序 | 固定pair凸优化；同目标rank8作为控制 | raw query→HNSW→3真实入口→原NSG | 首选诊断参考；容量小且优化问题清楚 |
| 共享hub端MLP＋同一收益监督 | 共享参数的梯度学习 | 离线导出W，在线流程相同 | 若完整W拟合提升但泛化差，再考虑参数共享；不用“加深模型”代替证据 |
| 随机三入口策略＋真实联合奖励 | 无放回采样、策略梯度 | 可仍部署确定性top3，但需检查训练部署差异 | 更直接但奖励方差和搜索标签成本较高，暂不首选 |

第三条可由[Gumbel-Top-k（ICML 2019）](https://proceedings.mlr.press/v97/kool19a/kool19a.pdf)实现无放回抽样，再用[REINFORCE（1992）](https://link.springer.com/content/pdf/10.1007/BF00992696.pdf)的score-function梯度学习不可微奖励。它优化的是随机策略的期望收益，不保证确定性top3同步改善；Gumbel抽样本身不是NSG的反向传播。

[SOFT top-k（NeurIPS 2020）](https://papers.nips.cc/paper_files/paper/2020/file/ec24a54d62ce57ba93a531b460fa8d18-Paper.pdf)解决选择算子的平滑可微化；[Differentiable Perturbed Optimizers（NeurIPS 2020）](https://arxiv.org/html/2002.08676v2)研究线性目标优化器的扰动与梯度。它们都不自动提供黑盒NSG Recall对入口向量的导数，因此不应只因存在“可微top-k”就将其定为主方法。

下一次最小辨别实验应先匹配Fast3与新方法的入口数量、训练输入、H、图、metric、线程和计时条件。在相同标签与锚定强度下比较完整W和rank8，区分目标、容量和因子优化；低秩失败而完整W成功仍需结合梯度/容量证据，不能只凭两个结果认定rank不足。不要一次展开所有MLP、优化器与rank组合。

训练/校准选择保持隔离，Fast画像本身也必须遵守对应split。一个数据集只冻结一份模型用于L64/128/256/400/800；标签来源L与查询时L分开说明，不为每个L自动重训练。后续仍优先用户指定的小validation、单构建、必要方法范围；本轮不恢复被取消的大矩阵。

诊断要能区分：fit不提升（信号/代理/优化待查）、fit提升但cal下降（泛化）、精确排序有效而HNSW损失大（部署检索）、Recall提升但图搜索变贵（成本）。NDC用于定位，最终结论仍取同机单线程完整Recall–QPS曲线，不能把单L Recall或更低训练损失称为整体改进。

## 8. 交付与边界

- 论文阅读范围、作者代码身份及迁移限制：[papers.md](papers.md)。本轮为定向方法复核，不宣称系统穷尽全部文献。
- 本地事实、参数量与旧计时抽取：[evidence.json](evidence.json)、[build_evidence.py](build_evidence.py)。脚本只读既有小型结果/配置，不调用搜索或训练。
- 下载/缓存身份：[sources/manifest.json](sources/manifest.json)、[sources/addendum.json](sources/addendum.json)、[sources/extraction.json](sources/extraction.json)。PDF抽取有字形告警，公式以论文PDF/HTML核对；REINFORCE网页PDF可读，但本地下载失败，未伪造缓存。
- 修改前文档及源码身份：[local_source_manifest.json](local_source_manifest.json)、[source_before/summary.md](source_before/summary.md)。最终检查见[audit.json](audit.json)。

原实验结论保持`EXPLORATORY_NO_OVERALL_FAST_GAIN`。本轮修正的是方法解释和研究建议，没有新的性能结论；不把候选写进已实现架构合同。
