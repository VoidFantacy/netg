# 真实搜索效用到低成本在线策略：文献与作者代码审计

2026-09-08。状态：**研究设计，未实现、未训练、未运行 ANN**。本审计比较三种可实际部署的学生结构，并检查教师是否需要进入推荐方法。结论是：首选直接优化逐 query×hub 实测收益的稀疏斜分策略树；教师只作高容量 query-only 参照。低秩双塔和多原型仅作后备设计，不加入首轮模型扫描。完整执行边界见 [minimum_gate.md](../minimum_gate.md)，精确方法契约见 [method.md](../method.md)。

## 1. 推荐依据与新颖性边界

真正需要解决的是：如何把允许离线大量搜索的入口选择函数，表示成上线仅走一条短路径的策略。现有全H搜索标签不是唯一最佳hub的分类标签；同一query可以有多个同Recall动作，错选不同动作的后果也不同。因此，主要训练对象应是实测行动收益矩阵，而非GT1类别或教师唯一argmax ID。不同叶可输出同一hub，使一个hub拥有多个相隔的query区域；这在结构上超出每hub单向量线性打分的凸选择域，但有限深度和叶数仍严格限制表达能力。后两句是本任务下的几何推导，不是论文性能结论。

“离线重、在线轻”“从搜索结果学习”“成本敏感树”“子树损失差加权”都不是可直接申报的新发明。新方法若成立，其可检验增量只能是：固定原NSG搜索，按真实Recall效用学习入口策略，在完整上线成本下超越Fast，并证明改进来源于效用监督/决策结构，而不是新增动作覆盖、隐藏query网络或训练数据优势。文献不保证这一结果。

## 2. 路线A：效用策略树；TAO优先，VIPER作对照

### 原文与源码事实

TAO在固定树结构中交替优化节点；固定两个孩子子树后，节点训练由两边实际预测的损失差构造二分类问题。它不是逐层只向下生长的普通贪心树，也没有这里所需的全局最优保证。2018论文给出可分离节点集合与约化问题，随后用代理方法求线性/稀疏分裂；其结果不能直接推成ACSG保证。[TAO 2018原文](https://faculty.ucmerced.edu/mcarreira-perpinan/papers/neurips18.pdf)、[作者页面](https://faculty.ucmerced.edu/mcarreira-perpinan/research/TAO.html)

作者2026-07-22发布代码进一步确认：`tao.py:294–345,395–449`按当前左右子树实际输出计算loss差、绝对值权重，并可用`strict_update`拒绝真实损失变坏的更新。**默认`strict_update=False`，不能原样调用后宣称经验效用单调。** 分类叶在`models/leaf.py`聚合类别分布，不要求全树一类只出现一次。源码已有一般loss接口及分类/回归driver，但没有现成的本项目全H收益叶更新、ID/图标签合同和部署验收。[作者发布入口](https://faculty.ucmerced.edu/mcarreira-perpinan/research/TAO.html)、[本地源码](../sources/policy_compilation/TAO_author_release/tao-python-current/tao.py)

policytree更直接地接收样本×动作reward矩阵，其树叶选择动作，原则上契合当前监督形式。不过作者实现明确定位很浅的深度2/3精确搜索，搜索复杂度使其不能被当作20K×512维、深度8/10的可运行全局求解器。本任务采用其“最大化叶行动收益”的决策定义，不借用其精确求解保证。[JOSS论文](https://joss.theoj.org/papers/10.21105/joss.02232)、[固定版本R接口](https://github.com/grf-labs/policytree/blob/b543f0fa35dcb4cbe97e28d102b20523e2fcedaf/r-package/policytree/R/policy_tree.R)

VIPER把强化学习专家压缩成可验证决策树。作者`rl.py`以专家Q值跨度作重要性采样，树端仍拟合专家动作ID；`dt.py`调用常规分类树。它说明关键状态不必均匀模仿，但直接移植会把当前大量Recall ties压成一个教师代表，不能保持完整行动成本。作者训练还包含策略轨迹与DAgger数据收集；静态外生query没有这种状态分布反馈，故不照搬rollout循环。[VIPER论文入口](https://papers.neurips.cc/paper_files/paper/2018/hash/e6d8545daa42d5ced125a4bf747b3688-Abstract.html)、[固定版本重要性采样](https://github.com/obastani/viper/blob/54fc4ae803322a08cb87fbbe65171a15ef001c7c/python/viper/core/rl.py)、[分类树实现](https://github.com/obastani/viper/blob/54fc4ae803322a08cb87fbbe65171a15ef001c7c/python/viper/core/dt.py)

### 本地适配及其严格边界

使用`R[i,h,L]`整张实测Recall矩阵。叶子选择使到达该叶训练行的累计R最大的hub；同分按累计NDC、旧action、base ID。内部节点对每条到达行实际运行当前左右学生子树，得到`aL,aR`，再以`sign(R[i,aR]−R[i,aL])`作方向，绝对差作权重。零差不强迫区分；不能拿左右叶集合的免费oracle最佳值替代真实子树输出。

这是固定左右子树时的代数归约：两边成本分别为`cL,cR`，实际选择成本等于`min(cL,cR)+abs(cL−cR)×错误侧指示量`。训练加权logistic/hinge分隔面只是代理；真实树输出必须重新计算。只有Recall增加，或同Recall且累计NDC、复杂度均不增，才接受；每个在线可达叶必须仍有至少32个fit样本。上述约束是适配合同，未被实现或实测。

不同叶可重复输出同一hub是选择此路线的原因之一。相比线性分支、每动作唯一叶的Filter Tree，它允许一个动作选择域为多个叶区域之并。没有必要为此部署教师神经网络。但20K样本、min_leaf32意味着最多625个有支持叶；depth8最多256叶，实际可输出hub数不超过叶数，不能把全H监督说成全H可输出。[Filter Tree的独立定理审计](independent_literature_review.md)

部署只沿树走8/10次分支；每节点最多64个非零坐标时为512/640 MAC上界，dense则WebVid4096/5120、Yandex1600/2000。分支、索引gather、缓存和模型载入另计。训练可能局部停滞，重要样本可能分配不到叶，稀疏求解可能失败；这些都是待测风险，运算量上界不等于QPS收益。

## 3. 路线B：重交互教师到低秩单点积学生

TCT-ColBERT由较昂贵的多向量交互教师指导单向量dense retrieval学生，以分布蒸馏保留排序信息。作者代码`train/model_fn.py`显示学生query/document平均池化及点积，与教师匹配损失；原学生仍运行BERT query编码，不能据该论文宣称本项目在线没有query网络。[论文](https://arxiv.org/pdf/2010.11386)、[固定版本作者实现](https://github.com/castorini/tct_colbert/blob/4ce5843bde8d38d9005fab62e8a18fa939c12f73/train/model_fn.py)

本地适配可令既有query向量经`z=f(q)∈R^r`，离线保存H个hub向量`v_h`，上线选`argmax_h zᵀv_h`。标签和教师目标仍应来自真实效用矩阵，可用全H回归与实测期望regret；不得只拟合GT1。重交互模型只出现在离线，不意味着任意query依赖的非线性交互都能精确吸收到hub参数。

若`f(q)=Aq`，则`(Aq)ᵀv_h=qᵀ(Aᵀv_h)`：整个学生仍是原query的线性hub打分，改变了标签/低秩约束，没有增加非线性query表达能力。若加入`d→32→16`非线性网络，则确实增加在线计算。低秩学生在任意有限query集合上的打分矩阵秩至多r；它可能无法压缩教师的复杂效用关系。这些是该适配的代数边界。

全H显式打分、r16时，线性投影加hub点积的MAC为`16(d+H)`：WebVid21,232、Yandex16,336；r32翻倍。`d→32→16`网络加全H点积为29,936/20,048 MAC，另计激活与argmax。预建低维ANN可改变计算量但引入候选误差及索引成本，不在本轮授权范围，也不能未测就据此获准。考虑既有线性入口路径和本地失败，这条路线应作为简单线性对照后的条件后备，不作为首选。

## 4. 路线C：多原型的非线性学生

ProtoNN学习低维投影、少量原型及其输出权重，以核相似度组合输出。论文目标是有限存储下的高效分类；作者实现明确计算投影、到原型距离、高斯核以及输出矩阵乘法，不是默认的教师蒸馏算法。不能把原论文的小类别任务存储或速度数字移用于815/821个hub。[ProtoNN论文](https://proceedings.mlr.press/v70/gupta17a.html)、[论文PDF](https://proceedings.mlr.press/v70/gupta17a/gupta17a.pdf)、[固定版本作者前向](https://github.com/microsoft/EdgeML/blob/81025fce8ba28707eabe72e11bf3987a8d745608/pytorch/edgeml_pytorch/graph/protoNN.py)

本地适配为`z=Wq`，`phi_j=exp(−gamma²||z−b_j||²)`，`score=Z phi`，其中`Z∈R^(H×m)`。以真实收益矩阵监督所有输出，可拟合多区域的非线性选择面；可加教师软效用但需要直接效用对照。它不局限于每hub一个原query内积原型，不过H×m输出混合成本不可藏掉。

r16、m32时，忽略可预计算常数后的主要MAC为`dr+mr+Hm`：WebVid34,784、Yandex29,984，另有32次指数等开销。若每原型仅保留4个非零hub权重，则32原型的非零输出支持至多128个hub；其余同为零的动作至多贡献由冻结tie规则选定的代表，不能宣称仍具完整H的非平凡动作覆盖。扩大m增加多模态容量，也直接增加在线成本。

因此仅当高容量模型显示稳定样本外信号、树压缩失败且有证据指向平滑非线性而非标签噪声时再评审。当前不同时启动树、双塔、ProtoNN大扫描。EdgeML的Bonsai也是2017年的低成本非线性树模型，但路径节点保存多类预测参数会带来H因子；它与本次“叶直接输出一个hub”的成本合同不同，也不要与后来同名图方法混同。[EdgeML作者仓库](https://github.com/microsoft/EdgeML/tree/81025fce8ba28707eabe72e11bf3987a8d745608)

## 5. 为什么教师不是必须的中间层

QDagger研究强化学习中使用前任教师加速后续学生，并在继续环境学习中调整教师约束。当前任务的query是外生样本，一次选择入口后调用冻结搜索；既没有需要学生探索生成的MDP状态，也没有可以直接复用的TD目标。引入QDagger的完整训练循环会增加问题而未说明新增信息，故不推荐。[QDagger原论文](https://proceedings.neurips.cc/paper_files/paper/2022/file/ba1c5356d9164bb64c446a4b690226b0-Paper-Conference.pdf)、[作者代码固定版本](https://github.com/google-research/reincarnating_rl/tree/e9df46e9a20bff1ad4df097258b454c72688c196)

首轮教师T只接收query和已知L，拟议为`d→512→512→H`非线性收益模型；训练用全H标签，其审计输出也必须query-only。它回答“在当前标签、样本和较大模型下是否有可预测收益”，不能回答理论上可不可学习。真实全H oracle才可查看当前query完整标签，是行动集合内的经验上界；T不能被叫作oracle或上界。T不通过诊断也不能否决达到自身门槛的树S。

若实测标签已完整，S可以直接优化它们。教师唯一ID模仿树仅作匹配容量对照；若S没有优于此对照，就缺少“保留收益差和ties带来作用”的证据。全H线性收益模型、全H最佳常量hub也需要保留，分别排除简单线性信号和仅选择更好全局起点的解释。所有额外训练计入首轮8小时上限，不增加搜索标签调用。

## 6. 来源身份与阅读范围

作者源码快照位于[sources/policy_compilation](../sources/policy_compilation)，记录固定commit、URL、字节数和SHA；[download_manifest.json](../sources/policy_compilation/download_manifest.json)保存逐文件身份。只下载、解包阅读文本，未安装依赖或运行作者算法。TAO当前作者包README未给本审查可确认的独立许可条款，因此本次据其核查算法行为，不据此作可直接复制发布代码的授权判断。

本次重点阅读TAO论文第3节与当前作者训练/叶源码、policytree输入与求解接口、TCT论文方法与训练前向、ProtoNN公式与前向/损失实现；VIPER以论文入口摘要和作者核心树/采样实现为主，QDagger以原文机制和作者agent入口为辅助筛除。没有将这些范围虚称为所有论文逐页通读，也未复现任何论文实验。主报告的Filter Tree、GATE、LRSG另有[独立审计](independent_literature_review.md)与[图入口文献审查](graph_entry_literature.md)。

来源能够支持结构、监督与复杂度边界；本地效果只能由后续预注册gate支持。本轮没有生成新性能、运行时或可发表性结论。
