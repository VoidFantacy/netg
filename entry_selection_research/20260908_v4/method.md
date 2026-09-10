# 拟议方法契约：真实搜索效用斜切树

`DRAFT_NOT_IMPLEMENTED_NOT_RUN`。这是适配设计；没有现成训练CLI或部署artifact。研究理由见[report.md](report.md)，实验边界见[minimum_gate.md](minimum_gate.md)。

## 数据与目标

固定数据集、原始IP、NSG、base ID和H个现有hubs。K=10，L分别为64、128，先为两个L各训练一棵树；不把L叫作相同距离计算预算。单入口动作是hub对应的真实base ID，原 `search_new(mode=2)` 消费一个入口。

对训练行i和入口h记录 `R[i,h,L]=hits/10`、`D[i,h,L]=graph_NDC`、返回ID和GT10命中mask。GT及搜索轨迹只生成训练/评估标签，部署输入只有已有query向量。每行的全部同Recall入口保留，`R*=max_h R`仅用于离线regret。

主目标为 `J(T)=sum_i (R*[i]−R[i,T(q_i)])`。R*对树参数是常数。**主门槛优化Recall，不先调任意Recall/NDC混合系数。** 若两个叶动作的总Recall相同，则选择总NDC更小者，再同分时保留旧动作，最后按base ID定序。分支更新若总Recall相同，仅在总NDC不增且模型复杂度不增时接受；这只是经验目标的次序，不保证测试集或每条查询都不退化。graph NDC仍不是完整在线wall。

## 高容量参照

query-only非线性模型 `q→512→512→H`、ReLU隐藏层、sigmoid收益输出，对每个L独立拟合；其作用是检验这种输入/样本规模下是否有可学的样本外规律。拟议损失是所有入口的均方收益误差，加上softmax预测收益所诱导的实测期望regret；具体优化器、归一化、温度/权重、轮数与种子须在开跑前配置冻结，范围见gate。不能在看审计集后追加容量或训练轮数。

该模型没有输入当前query的GT、真实结果或轨迹；不能把privileged teacher的成功代替此项。它也不是oracle、Bayes上界或所有模型的能力上界。重模型训练和审计必须记录自己的收益预测误差、选择regret及成本。

## 学生树与初始化

每个内部节点存 `(feature_indices, weights, bias, left, right)`，判断 `wᵀq≥b`，每个叶子存一个hub/base ID。允许不同叶子存同一ID。深度拟议取8/10，节点最多64个非零坐标或全维，最少拟合叶样本32；最大叶数受深度及样本约束共同限制。20K/32最多625个非空合规叶，所以可能无法输出全部815/821个hub；这是显式容量限制，不把全H监督说成全H输出覆盖。

拟议初始化用拟合query的固定种子随机投影按中位数递归切分，不能看开发审计标签；不足最少叶样本时停止。所有在线仍可到达的叶子都必须有至少32条拟合支持，不能留下零训练支持的“合法空叶”。叶子立即以完整实测效用向量选动作。重模型不决定唯一叶标签，也不引入在线调用。后续若使用教师引导初始化或软效用填补缺失标签，必须另立消融与误差契约，不在首轮隐含加入。

## TAO式效用训练

原TAO是分类树训练框架，本节是对逐行行动效用的推导。仅有已测完整标签时执行以下离线过程：

```text
initialize bounded tree using fit queries only
repeat at most frozen number of sweeps:
    recompute which fit rows reach every node under CURRENT tree
    for every nonempty leaf:
        choose h from ALL H maximizing sum of measured R[i,h] in this leaf
        tie-break by sum D, then old action, then base ID
    visit internal depth levels from bottom to root:
        recompute rows reaching the current level
        for each reached row i and node n:
            a = output of CURRENT left child subtree on q_i
            b = output of CURRENT right child subtree on q_i
            delta_i = R[i,a] - R[i,b]
            target_i = left if delta_i > 0, otherwise right
            weight_i = abs(delta_i); zero weight means no forced choice
        propose a bounded linear separator using weighted logistic/hinge surrogate
        enforce node sparsity and descendant minimum-leaf constraint
        evaluate the proposal on actual tree outputs and full measured R/D
        accept only if the lexicographic empirical objective does not worsen
    stop on frozen convergence criterion; log all checked objectives and retain predeclared checkpoints
select permitted configuration/checkpoint on calibration split; freeze before audit
```

只处理实际到达节点的训练行；用于计算两个孩子最终输出时，离线可以遍历两边，但在线始终只走被分支选择的一边。不得在训练父节点时使用“左/右全部叶的免费最佳入口”，也不能把旧教师子树输出当作当前学生输出。父节点改变后，到达所有后代的行集合必须重算；更新会破坏最少叶样本约束时拒绝该候选，不能仅检查当前两孩子行数。

固定其余树时，选左/右造成的Recall差正好为delta，所以代价差加权二分类与该节点的真实选择损失相差一个常数。logistic/hinge只是求分隔面的代理；降低其损失不保证降低树的实测regret，因此显式进行整树/受影响行验收。有限迭代、初始化、稀疏近似均可能导致局部停滞，没有全局/泛化保证。

每叶选择可重复，使同一hub的选择域是多个叶区域的并集；单个线性叶路径仍是半空间的交。这与“每hub唯一leaf”的线性Filter Tree不同，也不能声称有限叶数能逼近任意复杂效用。

## 部署与成本

在C++中按节点索引走一条路径，输出叶ID对应的真实base ID，调用一次原搜索。模型载入时检查维度、节点合法性、无环、深度上限、非零数量、叶hub映射及图/输入SHA；不能调用GT评分、在线probe、query近邻Atlas、教师或Fast候选生成器。若未来要回退Fast，回退判断与两套路由开销必须重新建契约、实测，首轮没有隐藏回退。

深度10下，64非零上限为640 MAC，全维上限为WebVid5120/Yandex2000 MAC。满二叉深度10有1023个内部节点；单精度全维权重约2.00/0.78 MiB，另有阈值、节点索引和叶ID。稀疏权重还需支付坐标索引存储及gather，不能仅按权重字节估缓存。实际剪枝后的节点数、活跃叶数、不同hub数、每路径MAC和p95/p99深度均须报告。

在线计时包含query预处理、模型推理、入口ID读取/初始化和原NSG搜索；GT、hash、JSON、统计与instrumentation排除到独立pass。共同上游query编码的边界显式声明。单线程延迟、部署线程数吞吐、p95/p99与cache条件分开，不从操作数或NDC推算QPS。

离线分别记录原GT/QGT/NSG的复用身份与未知历史成本、新搜索标签、重模型拟合、树拟合、模型导出和索引/载入成本。完整标签不是免费基础设施；图、hub、metric、base或split变动会按spec触发失效/重建。

## 必须区分的四个差距

1. 全H oracle与重模型：样本外预测差距，不是简单的压缩误差。
2. 重模型与树：两种模型的实际质量差；树直接优化实测效用，不强称为纯蒸馏损失。
3. 全H oracle与树实际可输出hub集合内oracle：有限叶子/动作分配的覆盖差距。
4. 树输出集合内oracle与树：分支预测差距，包含不可由当前结构/训练捕捉的变化。

各oracle对当前query查看标签，仅作离线分析。树的输出集合只能从已冻结模型读出，不能用审计标签挑选入口后再算该集合覆盖。所有差距分别在同一查询、同一L、同一动作数上计算，随后才检验完整Recall–QPS。
