# 固定路由成本下的 A+B 单入口选择

**推荐把 A+B 收敛为“Fast 初始化的低秩多区域入口路由”，以本地 v4 直接效用斜切树作为备用。暂不作方向 NO-GO，也不作实验 GO。** 两者都有明确的数学对象、可执行的离线优化和受限的在线形式；现有证据尚未证明任何一个能把 E20 的 oracle 空间变成样本外收益。

A 应理解为“查询空间怎样划分成便于选择入口的区域”，B 为“每个区域选择哪个真实入口”。联合设计可以有研究价值，不要求每个组件都从零发明。真正需要证明的是：组合后解决了此前目标、表示和部署成本之间的具体矛盾，并在强对照下产生可复现收益。以下只给方法和未来验证设计，全部新算法均未实现、未运行。

## 1. 已确定的事实与仍未解决的问题

### 1.1 本地契约

原始依据是当前 [spec](../../spec.md)、[summary](../../summary.md)、[E20 protocol](../../fast_router_diagnosis/20260908_v1/protocol.md)、[E20 正式报告](../../fast_router_diagnosis/20260908_v1/report.md)及对应源码。A/B/AB R0 和 v4/v5 是研究设计，不能与已运行的 E20 混为一谈。当前 C 分支已有单独停止结论，它没有验证 A+B，也不作为 A+B 的正证据。

| 对象 | 本轮采用的定义 | 对方法的约束 |
|---|---|---|
| 数据 | WebVid 2,505,000×512；Yandex 官方前 10M×200 | 两数据集分别训练；不把不同 ID/维度合成同一模型 |
| 距离 | 原始、未归一化 base 上的 IP | 不归一化 Yandex base，不套用 L2 度量保证 |
| 图与搜索 | 冻结 NSG R64/Lbuild100/C512；原 `search_new(mode=2)` | 不改邻边、visited、候选池、展开或回退逻辑 |
| 动作 | 从当前 H=815/821 个真实 hub 中选一个 base ID | 每次只传一个入口；不扩大到全 base，不执行额外 probe |
| 搜索工作点 | K=10，L=64/128 | L 是候选池容量，既非距离计算次数，也非严格 wall 预算 |
| Fast 对照 | 同源拟合查询构造的 paired Fast | E20 使用后20K；旧30K正式基线不能混用 |
| 路由成本 | 表示计算、索引查询、ID转换的完整在线成本 | 固定 M、维度和 ef 只是结构限制，不等于固定时间 |

Fast 的画像不是“一个 query 均值随便加 prior”。其构造为：先把训练 query 的 GT1 向量分给 cosine 最近的 raw hub；每个 hub 的单位向量 prior 加上该 basin 内所有单位 query 的**和**，最后整体归一化。prior 权重为 1。它优化的标签并非该入口在有限 L 下的 Recall。

当前在线实现使用 `InnerProductSpace` 的 `1-qᵀp`；库本身不会把输入单位化。因为旧 p 是单位向量，对固定非零 q，该排序与 cosine 排序相同。学习后的向量范数不同，继续使用 cosine 或逐向量单位化会改变新模型。

### 1.2 E20 提供了机会，但没有提供预测器

以下是 E20 已存报告的历史聚合结果，单位为 Recall@10 百分数；不是本轮新测量。其主样本是每数据集 512 条历史开发 pilot，另有训练侧辅助查询，并非全20K或新鲜审核样本。

| 数据集/L | Fast1 | exact 画像1 | 真实 GT1-basin 入口 | 全 H 最佳 single |
|---|---:|---:|---:|---:|
| WebVid/64 | 66.00 | 66.54 | 67.64 | 80.70 |
| WebVid/128 | 73.87 | 74.49 | 75.61 | 85.96 |
| Yandex/64 | 82.85 | 82.48 | 85.74 | 93.50 |
| Yandex/128 | 91.00 | 90.64 | 91.76 | 96.56 |

这些结果支持改变监督目标。即使直接获得正确的旧 basin，仍离当前 H 内的最佳入口很远；把旧分类准确率作为主指标会继续错位。exact 画像检索也未稳定改善所有工作点，所以只修 HNSW 近似不是充分方案。

E20 同时发现：全 H 相对 exact C8 最佳 single 仍有 **6.660/5.762/4.941/3.164 个百分点**空间；exact C8 内的最佳 single 又比 exact1 高约 **7.50/5.70/6.07/2.75 个百分点**。因此既有候选遗漏，也有选择错误。新方案需要允许旧 C8 外的入口被选中，而不是只换一个 C8 排序损失。

并列最优非常普遍：A0 集合大小中位数为 WebVid 50.5/61.5、Yandex 205.5/821；Yandex L128 有 266/512 条 query 的全部 H 个入口都达到 Recall=1。跨 L 的 A0 交集非空比例为 92.19%/96.09%。这支持保留整行效用和全部 ties，却不能证明同一个廉价决策函数容易学到这些交集。

简单 query 近邻迁移没有稳定正信号，原型分数与全 H 效用的平均 Spearman 仅约 0.011–0.024。这是风险证据，不是任意 query-only 模型不可学习的定理。所有 oracle 都查看了目标 query 的真实结果，既不支付选择成本，也不代表可部署收益。

### 1.3 确定与未确定的边界

已经可以确定：监督应直接指向有限 L 下的原搜索 Recall；不应强制唯一最佳 ID；单入口不需要先保留 Fast anchor；表示与入口身份应允许分离；成本必须在最终在线路径核验。

仍未确定：原 query 中是否有足够可泛化信号；815/821 个受限区域能否表达该信号；低秩是否足够；多对一映射的收益是否超过丢失部分动作的损失；Micro-HNSW 能否可靠检索新的非单位向量；两 L 是否值得共享参数。以下推荐是针对这些不确定性的有约束选择，不是已有答案。

## 2. 最接近的论文到底做了什么

完整书目信息、原文和固定作者代码链接见 [论文清单](papers.md)。以下只保留影响选型的区别。

**GATE 是直接相关的入口学习工作。** 它用 HBKM 产生真实 hubs，抽取拓扑信息，再把 query 信息蒸馏到可检索的 hub 表示。论文 §4.2 Definition 4 按 hop 定义正样本，式(4)是对比目标；这不是固定 L 的 GT10 Recall 整行效用。检查的作者发布代码实际启用 cosine triplet loss，且正样本选择沿每个 query 的 hubs 比较；不能把论文公式和该发布脚本说成完全一致。在线 C++ 使用原 query 检索 hub embedding 并选择多个入口，未运行在线 query MLP。A+B 与其共同点是离线学习、在线检索入口表示；拟解决的差别是直接 Recall 监督、区域与真实入口解耦、单入口和可核验成本。[^1]

**Adaptive Entry Point Selection 提供几何入口和理论对照。** 论文 §3.3 先以 k-means 中心附近的真实点构造候选，再选离 query 最近的候选；§4 的 b-monotonic/B-MSNET 分析有图与距离假设。它没有联合学习有限 L 的入口效用，相关界不能直接移植为本地 raw-IP 的保证。[^2]

**Learning to Route in Similarity Graphs 已有图搜索监督、集合正样本和离线表示折叠。** 其学习对象包括每一步的图路由评分，作者训练代码对多个最短-hop 正动作使用 log-sum-exp 集合损失。`NoProjAgent`/预计算节点表示证明线性 query 变换可以搬到节点侧；但作者具体变换还处理了 bias，不能简单称所有在线运算消失。它会影响图内路由/验证评分，本轮只改入口。[^3]

**Multi-Prototype SVM 的预测公式与主方案的结构最接近。** 其式(2)就是“所有 prototype 中取最高内积，再查所属类别”，等价于每类取多条线性函数的最大值。因而多向量对应一个入口、区域并集、max-linear 都不是新发明。主要差别应落在真实搜索的逐 query 效用、多对一映射的学习、Fast 可恢复约束和固定规模的 ANN 编译，而不是给已有形式换名字。GAMM 的式(4)及增长/剪枝算法说明多超平面容量可以自适应，但无限增向量不符合本轮预算。[^4][^5]

**ProtoPool 已联合学习 prototype 和类别分配。** 它的 §3 将共享 prototype 分配到每类的 slots，采用 Gumbel-Softmax，聚合图像空间和多个 slot 的相似度。主方案则每条路由向量只映射一个真实动作，只执行全局获胜 slot；它们有共同设计思想但输出语义不同。这种关联需要引用与讨论，不构成自动 NO-GO。[^6]

**ProtoNN 联合优化投影、原型和输出标签权重，但其在线算子不同。** 式(2)/Algorithm 1 学 W、B、Z，在线按 Gaussian 相似度加权求和所有 prototype 的输出；作者 `forward` 直接执行该聚合。一般不能用一次 top1 MIPS 精确替代。对 H≈820，本轮不优先引入一个默认需要全量原型及输出聚合的网络。[^7]

**SPOT、TAO 与 COMNETS 支撑备用方案。** SPOT 式(2)/(4)优化决策遗憾；TAO §3 把节点优化化为当前左右子树的实际结果比较；COMNETS 式(2)/(3)已按逐样本吞吐损失训练成本敏感斜切树。因此“用真实效用差训练小树”有充分前例。本地 v4 是这些思想在固定 NSG 多动作效用上的设计，并非一个全新的通用树算法。SPOT 关于叶内平均成本的 Theorem 1 假定相关最优决策唯一；这里大量 ties，应直接优化叶子的离散入口，不照搬加噪声造唯一标签。[^8][^9][^10]

**其他结构提供方法零件，不必全部塞入最终模型。** Latent Structural SVM 给出潜变量补全和凸—凹交替，但修改映射、加入低秩因子后，不能继承其原始 CCCP 保证。VQ-VAE 的 codebook/commitment 项服务重构，并不保证入口效用；Switch 的 top1 MoE 负载均衡用于专家容量，不应强迫各入口等频；Hydra 将配置生成与选择结合，强调互补价值，不能把免费 portfolio oracle 当可预测策略。VIPER 的教师引导压缩有用，但不要求本轮先训一个重教师。[^11][^12][^13][^14][^15]

## 3. 统一数学问题与两个候选

冻结图为 G，真实入口集合为 E={e₁,…,e_H}。给定 q 和 L，原搜索输出前10个 ID，定义

\[
u_{i e}^{L}=|\operatorname{Search}_{G,L}(q_i,e)\cap GT_{10}(q_i)|\in\{0,\ldots,10\},
\qquad R_{ie}^{L}=u_{ie}^{L}/10.
\]

每条查询的标签是 H 维整数 hit 向量；NDC 单独保存，不加入未经论证的 `Recall−λ·NDC` 主标签。记 `R_i*=max_e R_ie`，A0ᵢ 为所有达到该值的入口。部署策略 f_L(q)∈E 的目标是最大化样本外平均 R，并满足路由成本上限。训练用样本平均替代期望，不能把该替代当作泛化结论。

| 比较项 | 主方案：低秩多区域入口路由 | 备用：直接效用斜切树 |
|---|---|---|
| 查询表示/区域 | 原 query；H 条可训练内积的获胜区域 | 稀疏线性判断组成的单条树路径 |
| 入口分配 | H 个 slot 各选一个真实 hub，可多对一 | 每个叶子选一个 hub，可多叶同 hub |
| 连续参数 | 低秩残差 VZ，离线折叠成 H 个向量 | 内部节点的权重与阈值 |
| 训练 | 整行 Recall；离散映射与连续评分交替 | 整行 Recall；叶动作与分支交替 |
| 默认 L 策略 | L64/L128 分别建模，每次只调用对应模型 | L64/L128 分别建树 |
| 在线 | Micro-HNSW top1 slot → base ID | ≤10次线性判断 → base ID |
| Fast1 恢复 | 参数内含 exact Fast1；实际近似版本另保留原后端 | 有界深度树不保证包含 Fast1；仅模型级回退 |
| 主要强项 | 不增加 query 投影；与现路由结构接近，容量变化可定位 | 单路径、明确操作数上限；形状与平面竞争不同 |
| 主要风险 | 动作丢失、低秩欠拟合、塌缩、近似检索误差 | 样本不足、上层误分、叶数压缩、无法类内恢复 Fast |
| 与既有工作的关系 | 多原型/max-linear + 决策效用 + 受限编译的项目适配 | 明确延续本地 v4，不另起名称包装 |

没有把“共享 affine”“任意 MLP”“ProtoNN”“Gumbel codebook”各列成一个候选：前者适合作为主方案的限制性对照，其余尚无足以支付复杂度和在线代价的本地证据。两种结构已形成真实、可实现的选择。

## 4. 主方案：Fast 初始化的低秩多区域入口路由

### 4.1 参数、决策和表示能力

设 P₀=[p₁,…,p_M]∈ℝ^{d×M} 是 paired Fast 原型，固定 **M=H**。学习

\[
V\in\mathbb R^{d\times r},\quad Z\in\mathbb R^{r\times M},\quad V^TV=I_r,
\quad \|Z\|_F\le\rho\sqrt M,\quad \pi:\{1,\ldots,M\}\to E.
\tag{1}
\]

定义 W=P₀+VZ，列向量为 w_j。默认 **r=8、无 bias、不单位化 w_j**。ρ 是允许偏离 Fast 的锚定半径，建议首个协议考虑 ρ=0.5；这是待选的超参数起点，不是经验证的最优值。

\[
s_j(q)=q^Tw_j,
\quad j_\theta(q)=\operatorname{argmax}_{j}^{\text{固定slot次序}}s_j(q),
\quad f(q)=\pi(j_\theta(q)).
\tag{2}
\]

一个 slot 的区域是 `{q:qᵀ(w_j−w_k)≥0, ∀k}`，在精确实数模型下为多面锥。一个入口的决策区域是其所有 slot 区域的并集，可以覆盖相隔的查询方向。没有规定每个入口只有一个中心，也没有强迫区域对齐 GT1 basin。

等价写法为 `S_e(q)=max_{j:π(j)=e} qᵀw_j`；没有 slot 的入口得分为 −∞。这明确暴露一个预算交换：**M=H 且要求每个 H 入口至少分到一个 slot 时，映射必然是一一对应；要让部分入口拥有多个区域，就必须允许另一些入口暂时不被输出。** 不能同时承诺固定 H 个向量、每个入口都保留、又每个入口任意多个 prototype。

因此主方案保留的是“训练时始终允许从全 H 重选动作”，不是“每个最终模型都能输出所有 H”。重分配不等于删改原 NSG 或 hub 文件。

### 4.2 为什么不默认共享 affine 或在线非线性

旧 A+B 的共享低秩 affine 评分 `p_jᵀ(I+UVᵀ)q` 可以折叠成 `w_j=p_j+VUᵀp_j`。它要求所有残差系数来自同一个 `Uᵀp_j`；式(1)释放每个 slot 的 r 维系数 Z[:,j]，让不同区域对同一潜在方向有不同响应。在秩与半径条件兼容时，共享 affine 是该类的受限特例。

这个放宽针对“需要改变各区域边界，而非统一扭动旧画像”的可能性。它不证明 affine 一定不够，所以 affine+同一映射学习规则应作为最近的结构对照。全自由 d×H 向量作为额外容量也可研究，但本轮优先低秩，原因是可学习参数更少，且易定位欠拟合与过拟合；不是因为低秩有已知 Recall 保证。

无 bias 是一个有意选择：真实 IP 排序在正比例缩放 query 时保持不变，旧 Fast 也如此。无 bias 保持该不变性，并保持原维度。若将来加入 bias，可用 `[q;1]` 与 `[w_j;b_j]` 做 MIPS，但会改变 query 范数响应、维度和后端计算路径，必须作为单独配置验证，不能声称免费。

### 4.3 训练目标与离散更新

主目标是约束内最大化硬路由的经验 Recall：

\[
J(V,Z,\pi)=\frac1N\sum_iR_{i,\pi(j_\theta(q_i))}^{L}.
\tag{3}
\]

固定 W 后，每个 query 的 slot 确定，记 I_j={i:jθ(qᵢ)=j}。每个 slot 的最优映射可独立计算：

\[
\pi(j)\in\arg\max_{e\in E}\sum_{i\in I_j}u_{ie}^{L}.
\tag{4}
\]

这是固定分区下精确的坐标最优解，因为式(3)按 slot 可加。无需 Hungarian 匹配：没有一对一约束。也不按“某入口被多少 query 判为唯一最优”投票，而是直接求总 hit。

若多个动作总 hit 相同，优先保留原映射，其次用固定真实 ID 次序；空 slot 保留原映射。主方案不在这一步用 NDC 打破 query 的 Recall ties，避免把额外成本目标偷偷写进质量标签。输出 ID 的确定性 tie-break 只是实现规则，不把所有同效用动作变成错误标签。

低支持区域存在过拟合风险。20K/H 平均只有约24个查询，不能再要求全部 H 个 slot 都有至少32个样本。主方案不设置这种不可满足的硬要求；要记录每个 slot 的样本数、有效动作数和重映射稳定性，并用训练侧分离的模型选择控制过拟合。强制负载均衡会改变原问题，不作为默认补丁。

### 4.4 连续更新：软目标提案，硬效用验收

硬 argmax 不可微。固定 π，使用下式产生连续参数更新提案：

\[
a_{ij}^{\tau}=\frac{\exp(s_j(q_i)/\tau)}{\sum_k\exp(s_k(q_i)/\tau)},
\quad
\ell_\tau(V,Z\mid\pi)=\frac1N\sum_i\sum_j a_{ij}^{\tau}
\bigl(R_i^*-R_{i,\pi(j)}^{L}\bigr).
\tag{5}
\]

它是带 softmax 随机选择时的期望遗憾，用来平滑硬决策；不是预测一个唯一好入口的 cross entropy，也不要求所有并列最优入口分数相等。整行 R 相同的 query 贡献恒定0、梯度0，但保留在总体质量和成本统计中。若只在当前已映射动作之间出现 tie，它们也不会被式(5)人为区分。

具体优化可用无动量的投影梯度或小批 SGD 形成一个有限步候选，然后 QR 规整 V：若 V′=QT，置 V←Q、Z←TZ，保持残差乘积不变；若 Z 超出半径则投影回球。**初始化 V 为固定 seed 的正交基、Z=0；不能两因子都置零，否则双线性残差的梯度会一起消失。**

每次连续提案必须回到全拟合集的硬式(3)核验。提高总 hit 才接受；总 hit 相同且当前温度下式(5)下降也可接受，用于穿越平台；总 hit 下降则回退或缩短步长。随后重新计算到达 slot，再用式(4)更新映射。降温前后分别记账，不把不同温度的软损失直接比较。

一个可实现的停止规则是每个温度最多20轮映射—连续交替，每轮最多5个提案 epoch、最多5次步长回退；若连续3轮没有硬 hit 改善且软目标没有改善则结束。可定义 `τ₀=max(median_i[s⁰_(1)(q_i)−s⁰_(8)(q_i)],10⁻⁶)`，其中括号下标表示旧 exact 分数降序排名、只在fit计算；预定三段温度 `{τ₀,0.3τ₀,0.1τ₀}`。步长、batch及精度也须事前固定。上述数值均是将来协议的初始工程选择，不是理论常数。

**保证边界：**式(4)和硬验收保证这条训练轨迹的拟合集 Recall 不下降；平滑梯度、低秩非凸性及有限回退不能保证找出坐标或全局最优。它也不保证校准集、审核集或最终在线 HNSW Recall 不下降。保留每轮 checkpoint，再在训练侧独立校准上选模型，不能通过反复查看审核集决定重启或继续训练。

多对一可能塌缩到少数入口；若所有 slot 都映到同一入口，式(5)甚至失去区分梯度。这是实际失败模式。保留 Fast 起点与事先限定的少量重启可以诊断，但不使用无限加 slot、强迫等频或事后扩大搜索作为自动补救。

### 4.5 完整流程伪代码

以下是设计文档中的伪代码，不是 trainer 实现。

```text
输入：冻结 E/G/kernel/L；拟合集 Qfit；未来得到的完整 hit[query, entry]；
      仅由允许的拟合数据构造的 Fast 原型 P0；预定 r、ρ、温度、步数与 seed。

保存 Fast1 原始路由后端为独立 baseline。
V ← 由 seed 决定的 d×r 正交基；Z ← 0；π(j) ← 第 j 个原 hub。
保留初始模型；训练时只使用 fit 的 query 和 hit。

对每个预定温度：
  在轮数上限内重复：
    W ← P0 + VZ。
    对全部 fit query 计算 exact 获胜 slot（固定 tie 次序）。
    对每个 slot：用完整 H 动作的总 hit 更新 π；平局保留旧 π。
    固定 π，以软期望遗憾产生一个 V/Z 更新提案。
    对提案做 QR 与半径投影；重新计算硬路由、总 hit 和软目标。
    若硬 hit 增加，或硬 hit 相同且软目标下降：接受。
    否则有限回退；全部失败就保留原参数。
    重新统计 slot 到达量、输出动作数、全 H 到输出动作集的 oracle 损失。
    保存 checkpoint；达到预定停机规则则退出。

用独立训练侧校准数据在预先限定的 checkpoints/配置与 Fast1 中选模型。
冻结模型后才做一次训练侧审核；审核结果不返回优化环。

若选择新模型：离线编译 W；为每个向量使用唯一 slot ID 建 Micro-HNSW；
               保存 slot → 真实 base ID 的映射和完整元数据。
               在未来验收中核查 exact 与近似路由的效用差及路由成本。
若选择 Fast1：调用保存的原后端。

在线：已知 L → 对应模型 → 输入原始 q → 查询一个 slot → 查表得到一个 base ID
      → 原 search_new(mode=2)，输入单元素入口列表 → 原 K10 结果。
```

这是**联合目标、交替求解**。只拟合 A 再永久冻结、最后做一次 B 作为分阶段对照保留；因为 B 改变了每个区域应服务的动作，允许 A 再调整有明确理由。但交替是否优于一遍分阶段必须实证，不先写成定论。

### 4.6 在线编译与成本

`qᵀ(P₀+VZ)[:,j] = qᵀp_j + (Vᵀq)ᵀZ[:,j]`。把左式的 W 离线存下来，在线无需显式算 Vᵀq，也无需访问 V/Z。返回的永远是 π(j) 对应的真实 base ID，w_j 自身不必是 base 向量。

**索引的外部 label 必须是唯一 slot ID。** 多个 slot 可能映射到同一个 base ID；若把 base ID 直接当 HNSW label，重复 label 会触发已有元素的更新，破坏固定 M 的语义。该要求与已有一向量一入口的加载方式不同，属于未来实现必须明确的接口变化。

| 量 | WebVid | Yandex | 解释 |
|---|---:|---:|---|
| 在线向量矩阵 float32 | 815×512，约1.59 MiB | 821×200，约0.63 MiB | 不含 HNSW 图、分配器、映射和元数据 |
| r=8 的学习因子参数数 | 8×(512+815)=10,616 | 8×(200+821)=8,168 | 不计固定 P₀、整数映射；在线可只保留 W |
| exact 全扫描的乘加项 | 417,280/query | 164,200/query | 只作为参考，不是默认在线扫描 |
| HNSW 距离乘加项 | 约 v(q)×512 | 约 v(q)×200 | v(q)由实际访问决定，不由 ef 唯一决定 |

建议未来首次索引对照沿用 E20 所记录的 M16/efConstruction200/ef10 及构建顺序/seed，查询 k=1；若基线调用语义不同，先建立同口径 Fast1。新的向量几何可能改变图连通、层访问、缓存行为与 v(q)。同 M/d/ef 不能推出“和 Fast 一样快”，更不能引用 E20 包含装载和计数的进程时间估算新方法 QPS。

MIPS 可直接表达式(2)；Micro-HNSW 是其中一个近似后端，没有本地 raw-IP 检索误差保证。应报告 actual route 选择的真实 Recall，而非只报告它恢复 exact top1 的比例，因为不同入口可以同效用，近似偏离有时也可能提高 Recall。

离线也需要完整记账。20K fit 时每个L的H维uint8 hit矩阵约16.3/16.4 MB；令Q按行存query，训练可缓存 `QP₀` 对应的N×M旧分数，float32约65.2/65.7 MB，避免每步重算全部原维度点积。连续提案用该缓存加 `Q·V·Z`，每次评分约 `O(Ndr+NrM)`；映射更新约 `O(NH)`。这些是算术/存储量，不包括优化器、批处理、标签生成和索引构建的实测开销。后续若选择实现，保持本地CPU-only要求；不因引用神经网络论文引入GPU依赖。

### 4.7 恢复 Fast 的准确含义

令 Z=0、π(j)=e_j，式(2)精确恢复旧原型的 **exact Fast1** 分数与动作，前提是 tie 次序也相同。因此该精确模型类包含同口径 Fast1。

实际旧 Fast 用 HNSW；即使向量相同，重建图、用 slot label 代替 base label、换 SIMD 路径、top8 前缀改成直接 top1，都可能影响实现行为。应保留旧后端作为 `baseline` 配置来恢复实际 Fast1，不能只凭代数等式承诺逐字节一致。

还需划清一个不可兼得的要求：**单入口函数不能完整包含原 Fast3 的三入口联合搜索行为。** E20 的 Fast1 是其 top8 检索结果的第一项，原 bench 有直接 top3 调用。新协议应定义一个可复现的同入口数 Fast1，同时将 Fast3 保留为端到端性能参照。若“恢复原 Fast”必须指完整 Fast3 流水线，需要在最终模型级允许选择旧三入口流水线，这会超出严格“每个 query 只一个入口”的新模型定义，须由方法选择明确。

### 4.8 L64/L128 和最可能的失败

默认每个 L 单独学习 V、Z、π。L 在调用前已知，选择一个模型不会引入 query probe；在线每 query 仍只有一次路由，代价主要是保存两份模型，而不是做两次推理。理由是先把“单个 L 能否学到效用”与“跨 L 压缩是否成功”分开定位。

下一层对照可共享 W，只保留 π₆₄、π₁₂₈ 两张表，优化两 L 等权目标；还可以完全共享 W/π。E20 的 A0 交集比例给共享提供动机，但不足以跳过分 L 对照。任何共享结果都应逐 L 报告，平均收益不能掩盖一个 L 的明显损害。

最可能失败在四处：原 query 对 finite-L 效用的信号弱；低秩与固定 M 丢掉必要区域；映射把少样本噪声当成稳定专长；精确路由有收益但 HNSW 的误差或成本吃掉收益。任何一种都应有对应证伪指标，不能统一解释为“模型不够大”。

## 5. 备用方案：直接效用斜切树

### 5.1 完整模型与目标

直接沿用 [本地 v4 方法](../../entry_selection_research/20260908_v4/method.md) 的主干。树 T 的内部节点 n 用 `a_nᵀq−t_n≥0` 选择左右孩子；叶 ℓ 保存真实入口 e_ℓ。最多深度 D=10，每节点最多 s=64 个非零特征；初始可用 D=8。输出 `f_T(q)=e_{leaf_T(q)}`。允许多个叶子保存同一入口。

\[
\max_{T,a,t,e}\frac1N\sum_i R_{i,f_T(q_i)}^{L},
\quad \mathrm{depth}(T)\le D,\quad\|a_n\|_0\le s,
\quad |I_\ell|\ge n_{\min}\ \text{对有效训练叶}.
\tag{6}
\]

预定 n_min=32 沿用 v4 作为起点。20K 拟合查询下最多625个满足此约束的有效叶，不能承诺输出全部815/821个入口。树的资源限制和样本量共同限制了动作覆盖。

### 5.2 具体优化与 ties

先用固定 seed 的平衡线性划分初始化满足支持约束的树；不先用任意唯一 oracle ID 生长分类树。固定分支时，每叶按全部到达查询、全部 H 动作的总 hit 选入口，与式(4)相同。Recall 总 hit 平局时可沿用 v4 的总 graph NDC、旧入口、真实 ID 次序作为次级规则；NDC 不改变主 Recall 最优集合，也不据此承诺总 wall 更低。

固定节点 n 以下的两棵子树，令 e_left(qᵢ)、e_right(qᵢ) 是查询分别进入它们后**实际返回的两个叶动作**。对到达 n 的样本计算

\[
\delta_i=R_{i,e_{right}(q_i)}^{L}-R_{i,e_{left}(q_i)}^{L}.
\tag{7}
\]

δᵢ>0 标记应向右，δᵢ<0 应向左，权重为 |δᵢ|；δᵢ=0 是该节点当前的无差别样本。用带稀疏约束的加权 logistic/hinge 产生分支更新，对拟合集原始总 hit 验收；投影到最多 s 个非零权重之后再次验收。不能用“左子树包含入口的 oracle 最大值”代替实际输出，否则学到的是免费选择器。

逐层自底向上交替更新叶与分支；上层改变后重算到达集合，检查其所有后代的 n_min，而不只检查两个直接孩子。若违反限制或硬效用下降则回退；对达到上限、无改进或无可接受更新的情况停止。固定 seed、轮数和模型选择数据，避免树结构被审核集反复调整。使用 TAO 作者代码时仍需适配逐 query 多动作效用与严格验收；不能默认该通用发布版已经实现本地契约。

### 5.3 在线成本、Fast 恢复与差异

在线原 q 沿单条路径走到叶，查出一个 ID 后进入原 NSG。最多 D×s=640 个乘加项及分支/稀疏索引读取；如果用 dense 节点，D=10 时为 WebVid5120/Yandex2000个乘加项。操作数小不等于 wall 已胜出，分支、gather、树规模和缓存均要计入。

它不需要 Micro-HNSW/MIPS；强行把整棵树编译成一次普通 MIPS 通常不会保持相同大小和代价。D=10/s=64 的树也没有证明能精确表达 H 条 Fast 分数的所有竞争区域，恢复 Fast 只能通过模型级保存并选择原 Fast1，不能声称树参数内含原基线。

L64/L128 默认两棵独立树。共享分支、叶上两张 L 条件动作表是可选对照；δ 必须使用对应 L 的效用，质量 ties 不生成唯一 query 类别。

该方法与本地 v4 **是同一方法家族**。相对 TAO/COMNETS，项目差别在原 NSG 的 H 维、离散且大量并列的真实搜索效用，以及严格在线单入口边界；相对 SPOT，使用斜切路径和实际子树动作比较。贡献只能来自这种适配、问题分析与性能证据，不来自把树的叶动作重新命名。

最可能失败是：上层小偏差把查询送入没有合适动作的子树；有效叶数不足；稀疏原特征无法表达有用分界；小样本叶过拟合。不能以“重教师也失败”为必要前置 NO-GO；树与教师是不同函数类，若将来加入教师，只把它当独立诊断。

## 6. 为什么推荐主方案，以及贡献怎样成立

优先主方案的理由有三点。它在精确函数类中直接包含 Fast1，便于逐项定位变化；离线折叠后保留原维度和 H 个向量，不预付 query 网络成本；与旧共享 affine 相比，只释放各 slot 的低维残差系数，并允许动作重映射，结构增量清楚。树则提供真正不同的区域表示与成本形态，适合在平面竞争失败或 HNSW 成本不合适时作为备用。

主方案有望针对 E20 的三处缺口：式(3)把监督从旧 basin 改成原 kernel Recall；完整 H 动作的式(4)允许旧 C8 以外的入口被接入；多 slot 同入口把互不相邻的有效区域分开表示。它不增加 q 中的信息，不改变图的可达性，也不能补出当前 H 外的入口。如果主要缺口来自无法用原 q 预测的微观搜索路径，A+B 可能仍失败。

与本地历史相比，“真实效用”“soft label”“离线重、在线轻”本身均不足以构成区别。旧 E07 已有 Fast32 上的 Recall/NDC soft-listwise ranker；E09 已有有符号效用残差；旧 NETG 已有离线 hub 网络及原 query 在线检索。主方案需要明确证明全 H 直接决策、可学习多对一映射、可调区域与固定规模编译共同带来了什么，不能用新术语抹掉这些前例。对应源码与审计入口见 [本地证据](local_evidence.md)。

可辩护的研究贡献可分三层：

1. **问题层：**在固定图、有限候选池容量下，把入口视为具有整行收益的动作，分析区域容量、动作覆盖与近似路由的不同损失。
2. **方法层：**将多原型/max-linear、直接决策效用、区域—动作交替和 Fast 锚定结合，在固定路由向量预算下进行多区域资源分配。
3. **系统层：**将学习参数折叠为可检索向量，以唯一 slot ID 连接真实入口，并证明端到端 Recall–QPS 改善来自这条实际部署路径。

组件已有并不否定这三层组合贡献；不需要另造一个通用优化器或宣称“首次”。但若新系统只等同已有一组件的结果，应该缩小贡献表述或直接采用更简单组件。交互项为正是有趣证据，**不是组合贡献成立的必要条件**。

建议四格对照 `J00=Fast1`、`J10=只学W且π固定`、`J01=只学π且W=P₀`、`J11=联合`，并报告 `J11−J10−J01+J00`。若 J11 超过 Fast，却不超过最强单组件，应保留有效结果、检查复杂性是否值得；不能因此机械宣布整个入口方向 NO-GO。论文级主张仍需相对最接近图 ANN 和本地方法的公平比较。

## 7. 未来最小证伪设计：仅设计，当前不执行

### 7.1 先冻结选择与数据角色

方法选择后，先写新协议，明确 Fast1 调用语义、成本上限、L 策略、候选/图/GT 身份以及拟合、校准、审核 query 的历史使用记录。第一批只使用经授权的训练侧数据；本轮不访问 validation/held-out。

原前10K 已被多次探索使用，排除 E20 的512条并不自动得到“未见审核集”。还要核对 E07/E13/E15/E21 等已用查询。若内部从后20K划出校准/审核，不能继续用包含它们 GT1 的20K Fast 画像，却声称严格拟合隔离；应为新协议在拟合集上重建 paired Fast，并明确它与 E20 的20K baseline 不同。图和 E 仍冻结。若无法从训练侧得到符合声明的样本，就降低“未见”声明或另行确定数据来源，不能偷偷使用 held-out。

### 7.2 三个连续但独立的门槛

| 阶段 | 仅在未来获准后执行的最小工作 | 要证伪的假设 | 失败时的解释 |
|---|---|---|---|
| S0 定义/一致性 | 零残差、identity映射、真实ID与slot映射、ties、单入口消费的有限验收 | 实现确实对应数学模型，基线比较公平 | 实现或协议失败，先修正，不能报告方法结果 |
| S1 质量筛查 | 双数据集先 L64；完整 H 的单入口效用；四格对照；exact 选入口；独立训练侧审核 | 当前样本量和容量下存在可预测效用，联合有必要 | 无正信号则不进入部署；不能外推任意模型不可学 |
| S2 工作点/部署 | 同一冻结设计补 L128；新向量 Micro-HNSW；独立全批 wall；与 Fast1/Fast3 比较 | 收益跨工作点且实际路由满足成本预算 | 明确区分 L 不迁移、近似损失、路由超预算、图开销增加 |

主方案通过 S1 才有理由支付 S2。若 S1 显示近似无关的表示失败，可由方法选择决定是否验证备用树，不把备用自动排队。最终正式结论仍需本地契约要求的强基线、独立构建、尾部和方法冻结后的正式评价；这不是本轮或这份最小筛查的授权。

一个预算可理解的**示例**是每数据集8,192 fit、1,024 calibration、2,048 training-side audit；只能在使用记录允许时采用。单 L 全 H 标签为 `(8192+1024+2048)×(815+821)=18,427,904` 次逻辑搜索；两 L 为36,855,808。每个 slot 平均约10条 fit，负结果可能受样本量限制；它足以筛查明显失败，不是证明完整20K方法无效的样本复杂度保证。

若最终采用完整20K/数据集、两L，fit-only 算术为65,440,000次；每数据集再加总计2,048条非fit查询，变为72,141,056次。它们都是离线标签调用数，不是运行安排或时间估计。已有标签能否复用，要由 query、图、动作、kernel、L 与 split 身份决定；审核标签不能回流训练。

### 7.3 最小输出与归因

未来标签至少保存 `dataset, query_id, split_role, L, entry_id, hit_count_uint8, graph_ndc` 及输入身份；模型保存 `P0_hash,r,rho,seed,W,slot_to_base_id,fit/calibration IDs,checkpoint rule`。完整 H 矩阵不能压成 unique winner。计时用单独无计数路径，不在 timed region 做 GT评分、hash、JSON 或标签读取。

质量输出包括总体 Recall差、逐 query gain/harm、A0/饱和分层、slot支持量、有效动作集 P=range(π) 的大小、映射变化、跨L差异。P 的覆盖损失与 exact/近似选择损失分开：

\[
R_i^{*,H}-R_i^{\mathrm{approx}}
=\underbrace{R_i^{*,H}-R_i^{*,P}}_{动作覆盖损失\ge0}
+\underbrace{R_i^{*,P}-R_i^{\mathrm{exact}}}_{表示与选择损失\ge0}
+\underbrace{R_i^{\mathrm{exact}}-R_i^{\mathrm{approx}}}_{近似影响，可正可负}.
\tag{8}
\]

树用前两项即可。式(8)是同 query、同动作集合下的代数分解；不把第三项强行当作非负错误率。若动作覆盖损失大而 selector 很准，说明多区域资源分配付出了过高的丢动作代价；若覆盖好但 exact 选择差，瓶颈是表示、优化或泛化；若 exact 好、approx 差，则先定位索引表达。

最小质量筛查建议预先设置实际意义阈值，例如双数据集 L64 各至少 +0.5pp、配对区间支持正收益，再考察 L128。+0.5pp 是建议的研究投入门槛，非来自论文的定理，也不能因 Yandex L128 饱和就事后改阈值。四点与多个对照的区间应按预定比较族处理。区间跨0归为证据不足；明确劣于基线才是该配置的反证。

成本默认按当前任务的“固定路由成本”解释：预先规定同硬件/线程/批量下的 route wall 预算及测量容差，而非把 ef 当预算；报告 route、graph、total NDC 和独立全批 wall。测量时轮换方法次序并分离构建与查询。即使 route 满足预算，同 L 图搜索也可能更贵；只有端到端 Recall–QPS 前沿改善才能支持性能主张。没有测量前不给微秒、QPS或训练耗时预测。

### 7.4 明确的停止条件

出现数据角色不清、原搜索语义不一致、Fast恢复验收不通过时，停止该轮协议。若 exact 样本外无可用收益，不通过提高 ef 掩盖；若精确收益主要来自丢失大量动作后的偶然样本优势，先按审核结果否定该配置；若固定成本下近似路由或总 wall 吃掉收益，拒绝部署结论。

这些失败可支持某个 r、M、样本规模或结构的 NO-GO；不能仅凭它们证明原 query 的所有表示都不可学习。反过来，有 oracle 空间也不能成为反复扩大训练、模型或预算的理由。

## 8. 方法选择时需要明确的事项

| 选择 | 建议 | 改选的影响 |
|---|---|---|
| 主方法 | 低秩多区域入口路由；v4树备用 | 选树则优先单路径资源界，放弃类内Fast恢复保证 |
| Fast恢复口径 | 同入口数 Fast1；Fast3另作性能参照 | 若要求完整Fast3回退，应允许模型级选择旧三入口流水线 |
| L共享 | 首轮两个L分别建模 | 共享W+两张π表可减少模型存储，但引入迁移变量 |
| 参数起点 | r=8、无bias、固定M=H；ρ候选起点0.5 | 更大秩/自由W增加离线容量与过拟合风险；bias改变在线维度 |
| 成本和投入门槛 | 固定route wall预算；预先定有意义Recall差与样本预算 | 放宽路由预算将变成另一项端到端权衡研究，需要明示 |

当前已完成的是理论收敛、文献定位和可证伪设计。**没有足够证据对 A+B 作方向 NO-GO，也没有足够证据承诺它优于 Fast。建议选择主方案进入下一次协议讨论；本轮至此停止，等待方法选择。**

## 参考文献

下列编号对应正文；作者实现、固定版本及具体核查范围见 [papers.md](papers.md)。

[^1]: Ruan et al. *Empowering Graph-based Approximate Nearest Neighbor Search with Adaptive Awareness Capabilities*. 2025. [论文 v1](https://arxiv.org/pdf/2506.15986v1)，§4.1–4.2、Definition 4、式(4)；[作者代码](https://github.com/jacksondca/gate/tree/229f18dadb791ddede22597e44d5ceb028b104ba)。
[^2]: Oguri and Matsui. *Theoretical and Empirical Analysis of Adaptive Entry Point Selection for Graph-based Approximate Nearest Neighbor Search*. 2024. [论文](https://arxiv.org/abs/2402.04713)，§3.3–4。
[^3]: Baranchuk et al. *Learning to Route in Similarity Graphs*. ICML 2019. [论文](https://proceedings.mlr.press/v97/baranchuk19a/baranchuk19a.pdf)，§3及作者训练实现。
[^4]: Aiolli and Sperduti. *Multiclass Classification with Multi-Prototype Support Vector Machines*. JMLR 6, 2005. [论文](https://www.jmlr.org/papers/volume6/aiolli05a/aiolli05a.pdf)，式(2)、§3–4。
[^5]: Djuric, Wang and Vucetic. *Growing Adaptive Multi-hyperplane Machines*. ICML 2020. [论文](https://proceedings.mlr.press/v119/djuric20a/djuric20a.pdf)，式(4)–(7)、增长方法。
[^6]: Rymarczyk et al. *Interpretable Image Classification with Differentiable Prototypes Assignment*. ECCV 2022. [论文](https://www.ecva.net/papers/eccv_2022/papers_ECCV/papers/136720346.pdf)，§3，PDF第4–8页。
[^7]: Gupta et al. *ProtoNN: Compressed and Accurate kNN for Resource-scarce Devices*. ICML 2017. [论文](https://proceedings.mlr.press/v70/gupta17a/gupta17a.pdf)，式(2)、Algorithm 1。
[^8]: Elmachtoub, Liang and McNellis. *Decision Trees for Decision-Making under the Predict-then-Optimize Framework*. ICML 2020. [论文](https://proceedings.mlr.press/v119/elmachtoub20a/elmachtoub20a.pdf)，式(2)/(4)、Theorem 1、§4。
[^9]: Carreira-Perpiñán and Tavallali. *Alternating Optimization of Decision Trees, with Application to Learning Sparse Oblique Trees*. NeurIPS 2018. [论文](https://faculty.ucmerced.edu/mcarreira-perpinan/papers/neurips18.pdf)，§3。
[^10]: Shanmuga Sundaram et al. *COMNETS: COst-sensitive learning for throughput optimization in Multi-radio IoT NETworkS*. ETFA 2025. [作者最终论文](https://jothiprasanna7.github.io/homepage/pub/COMNETS-ETFA25.pdf)，§IV、式(2)/(3)。
[^11]: Yu and Joachims. *Learning Structural SVMs with Latent Variables*. ICML 2009. [论文](https://icml.cc/2009/papers/420.pdf)，§3–4、Algorithm 1。
[^12]: van den Oord, Vinyals and Kavukcuoglu. *Neural Discrete Representation Learning*. NeurIPS 2017. [论文](https://arxiv.org/abs/1711.00937)，式(1)–(3)。
[^13]: Fedus, Zoph and Shazeer. *Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity*. JMLR 23, 2022. [论文](https://www.jmlr.org/papers/volume23/21-0998/21-0998.pdf)，§2.2、式(3)–(6)。
[^14]: Xu, Hoos and Leyton-Brown. *Hydra: Automatically Configuring Algorithms for Portfolio-Based Selection*. AAAI 2010. [论文](https://ojs.aaai.org/index.php/AAAI/article/download/7565/7426)，PDF第3页算法。
[^15]: Bastani, Pu and Solar-Lezama. *Verifiable Reinforcement Learning via Policy Extraction*. NeurIPS 2018. [作者会议页面](https://proceedings.neurips.cc/paper_files/paper/2018/hash/e6d8545daa42d5ced125a4bf747b3688-Abstract.html)。
