# 最小可证伪协议草案：真实效用斜分决策树

状态：**DRAFT_NOT_IMPLEMENTED_NOT_RUN**。2026-09-08。本文件只供研究/实现评审，不是训练、搜索、访问新 split 或安装依赖的执行授权。所有阶段任务尚未实现；不提供冒充可执行入口的伪 CLI。

主候选为一棵按真实搜索效用优化的 oblique policy tree：每个内部节点只计算 query 的一个线性投影并选择左右子树，每个叶子输出一个真实 hub ID；不同叶子允许输出同一 hub。采用 TAO 式交替更新，**不引用 policytree 的全局最优保证或 Filter Tree 的归约界来保证本适配**。重模型 T 是高容量、query-only 的可学习性参照，既不是理论上界，也不是必须被逐层模仿的部署组件。

## 1. 冻结对象、数据和资源

- 原始 IP、原 base/NSG、K=10、L∈{64,128}、原 `search_new(mode=2)` 语义不变；第一轮仅研究单入口决策。Fast1 和 Fast3 用同 paired-20K 原画像/同一 HNSW 配置，另保留既有 exact/H 单入口 oracle 作诊断。
- 第一轮每数据集复用当前 QGT5K 产生的 H=815/821 个真实 hubs。一棵树的每个叶子均可从整个 H 选 action；不把 C8、anchor 或固定三个入口作为约束。不同 L 使用独立模型，在线 L 已知，不进行搜索后预算判别。
- 标签拟合范围为 `router_train[10000,30000)` 的全部20K。前10K只作已历史使用的开发集，不能称独立新测试集。从中排除本次 Fast 诊断已用的512行，再按 `SHA256(dataset + "|utility_tree_v4|dev|" + decimal_row_id)`、行ID顺序选前2048：前1024校准、后1024审计。排除仅防本轮重复使用，不抹除前10K的历史开发属性。
- 原始 validation/held-out query/GT不打开；不新增 exact GT。既有有效训练侧 GT 与图/base身份必须重核。fit、calibration、audit 的行ID、哈希规则、重叠检查及文件SHA先冻结再生成标签。
- 对两数据集22,048行的全部H、两个L穷举单入口，标签调用数为 `(20000+2048)×2×(815+821)=72,141,056`。第一轮硬上限80,000,000次搜索，剩7,858,944次仅覆盖已列的验收/计时，不追加样本、模型家族或动作组合。
- 拟议资源：CPU16线程；同一时刻一个重数据集进程；RSS≤80GiB；标签/搜索累计wall≤4小时，全部模型训练累计wall≤8小时；建议新产物≤8GiB且/data留≥10GiB，具体值在执行协议再冻结。到限保留结果并报告未覆盖，不能用超过预算的最佳checkpoint补齐主结果。
- 本预算覆盖一次固定hub构建的可行性gate。后续三独立build与held-out正式验证需要另列全部标签/训练/计时预算，不能假称已包含于上述80m上限。

## 2. 标签、目标和在线信息边界

每个 `(query_id, hub_id, L)` 至少保留整数GT10命中 `h∈{0,…,10}`、Recall=`h/10`、graph NDC、返回GT10 hitmask；保存返回ID或可独立核查的原始分块记录。GT评分在GT-free原kernel返回之后。全H列顺序、真实base映射、metric、代码/库身份与计数定义进入manifest。

主质量目标先固定为真实 Recall，即 `U(q,h,L)=Recall@10`、`C=max_h U−U`。NDC独立报告，在叶子累计Recall完全同分时先选累计NDC较小者；再同分时保留旧action，最后按base ID定序。不可把唯一存储代表变成唯一正确训练标签。若要改为 `Recall−λ·cost`，必须先另行冻结λ、成本单位及全比较族；本草案不暗设自由调参的λ。

T和S推理只接收当前query及已知L。允许静态训练集统计/模型参数和离线预计算；禁止把当前query的GT、完整utility向量、真实轨迹、先跑Fast所得Recall/NDC或目标query oracle输入T/S。训练标签包含这些信息并不等于推理特征可以包含。teacher在审计query上也必须query-only前向，否则只能命名privileged oracle，不能通过T gate。

输入采用原raw query。若训练标准化，均值/尺度只能由fit求得，并可折入每个线性节点的权重与bias；任何不能折叠的归一化/特征提取必须出现在在线计时。

## 3. 有限模型配置与更新定义

**教师T的拟议起始家族**：每dataset/L一个 `d→512→512→H` MLP，隐藏层ReLU，H维sigmoid输出拟合各hub Recall；损失包含全H Recall回归和softmax策略的期望实测regret。它不是GT1分类器，也不把全部非唯一oracle动作视为负类。架构、回归/期望regret系数、softmax温度、优化器、学习率、batch size、最大epoch、early-stop规则、seed和checkpoint选择规则，必须在实现前作为单一配置冻结。可从固定的 `MSE + expected_regret`、AdamW、batch256、lr1e-3、weight_decay1e-4、最多200epoch/20epoch patience开始评审；这些值是建议，不是已实现或经本地验证的设置。不得审计后扩大教师家族并保留“预注册主模型”称谓。

**学生S仅四种容量**：`max_depth∈{8,10}` × `max_nnz_per_node∈{64,d}`；`min_leaf=32`。不含在线教师、query神经特征网络、HNSW shortlist或全H打分。每L一棵树。在线上限分别为8或10次节点判断、最多512/640 MAC（nnz64），或WebVid4096/5120、Yandex1600/2000 MAC（dense），另加分支、索引读取和输出；这些算术界不是延迟/QPS保证。

容量张力必须报告：20K fit和min_leaf32最多625个非空叶；depth8最多256叶，depth10最多625叶。每叶只有一个action，故模型实际可输出的不同hub不超过叶数；多叶同hub会进一步减少。整个H均参与离线叶选择，不等于模型能输出整个H。需要报告叶数、使用hub数、路径深度/nnz、每叶fit支持量，以及“所用hub子集”的事后oracle与全H oracle之差，不能隐去这一结构上限。

拟议TAO式训练过程：

```text
初始化有界树结构和有效叶action；只使用fit，不用审计标签。
重复有限轮 bottom-up passes：
  叶节点：收集当前到达该叶的fit query I；
          action ← argmax_h Σ_{q∈I} U(q,h,L)；并列依次用累计NDC、旧action、baseID定代表。
  内节点v：收集在当前祖先规则下到达v的query I_v；
          对每个q分别实际通过当前左右子树，得到a_left(q)、a_right(q)；
          Δ_q ← U(q,a_right(q),L)−U(q,a_left(q),L)；
          用sign(Δ_q)作左右标签、|Δ_q|作权重；Δ=0不强迫方向。
          拟合满足nnz/叶支持约束的线性分裂候选。
          重新计算真实整树fit效用；Recall增加才优先接受；
          Recall不变时，仅在累计NDC不增且模型复杂度不增时接受。
  记录真实目标、被拒更新、零权重比例、每节点有效样本量和稀疏度。
有限迭代后完成预定剪枝/导出；重新验收导出前后路由逐ID一致。
```

拟合加权logistic/hinge surrogate不保证真实Recall目标改善，所以最后的真实目标接受检查不可省略。每个仍可在线到达的叶子都须有至少32个fit支持样本；节点更新后核对整个受影响子树，不能只检查非空叶而留下零支持的有效叶。不合规候选拒绝，或按预先冻结的规则剪去对应分支后重新验收。模型复杂度的比较量（建议先节点数、再全树nnz的词典序）须在实现前冻结。该算法是非凸的局部交替优化；初始化、遍历顺序、最大轮数、正则化/稀疏求解与接受同分规则须冻结，不宣称全局最优。

教师不必串在树前面。主学生直接消费实测全H utility；T首先回答更大模型是否在query-only条件下有样本外信号。若以后改用T产生的软utility或节点soft target，必须另列direct-utility对照与teacher误差；父节点目标需按**当前学生左右子树的实际输出**重算，不能继续模仿旧教师子树赢家。软标签不能覆盖已有实测零regret ties并虚构区别。

## 4. 阶段任务与停止条件

**G0 输入与实现验收。** 冻结上述数据/模型/统计/资源清单；验证原kernel single-entry count/plain/repeat、GT隔离、真实ID、label块形状与hash、split和溢出；树训练逐步目标接受检查、重复leaf action、多模态合成例、零权重/空叶/不足minleaf等边界；导出后仅raw query/L输入、同模型Python/C++逐ID一致；纯计时排除GT/hash/JSON且包含全部预测/重置/主图搜索工作。验收只用合成或fit；失败先修实现，不解释为方法失败。

**G1 固定模型训练和校准。** 在20K fit训练T及四种S，只在1024 calibration选择T checkpoint、学生配置和已预定训练停止点。建议两个数据集共用一种学生容量配置，以四个dataset/L校准点中最小的S−Fast1均值最大为主选择准则；同分优先更浅、再更少nnz。不得用audit挑树。训练规模、seed/初始化个数和T损失参数无开放扫描；预算到限停止。

同时预注册三个归因对照：① 从全部H选择fit累计Recall最高的单个全局hub（同分规则同叶动作）；② 全H线性 `query→R` 模型，使用相同完整效用标签与回归/期望regret目标，作为简单可学习性参照；③ 教师唯一ID模仿树，训练标签为冻结T对fit query的唯一选中hub，深度、节点nnz和min_leaf与所选S匹配，用同fit/calibration/audit。第三项故意保留硬标签的信息损失，以检验直接效用目标的作用；它是对照而非推荐目标。三项的完整训练/选择规则也须冻结，计入8小时总训练预算；直接复用全H标签，不新增搜索。教师模仿树同样须验收在线可达叶支持和导出一致性。所有对照在审计中完整描述，不能看结果后换对照家族。

**G2 一次性质量审计。** 配置/模型SHA冻结后，在1024 audit query运行T/S前向并读取其所选单入口的既有全H实测结果；此质量回放不新增搜索，也不计作在线时间。主族为 `T−Fast1` 与 `S−Fast1` ×两个dataset×两L，共8项query配对Recall比较，完整保存全部8项后解释。报告10,000次固定seed query-paired bootstrap的普通95%及Bonferroni8全族95%区间；同dataset两L共享query抽样流。另列所有baseline的Recall、NDC与tail，S−Fast3不可遗漏。

T诊断gate要求四点的T−Fast1均值均为正且全族区间下端均>0；未通过只记 `NO_SIGNAL_FOR_THIS_TEACHER_AND_DATA`，不能记理论不可学习。T和S在G1共同完成训练后分别审计，T诊断失败不否决成功S。S进入计时需四点均满足：S−Fast1≥0.5 pp、全族区间下端>0；仅在对应T均值增益为正时，另要求S均值增益至少保留该T增益的50%。后者是预定均值保留比例，不冒充另一个已有同时置信保证；可补报其描述性不确定性。T失败但S成功时应照实报告并继续通过门槛的S计时，不删除S结果或称任务不可能。

G2失败后不改depth/nnz、leafmin、teacher、label目标或审计样本再宣布原gate通过。必须区分：T不显示信号、T有信号但S容量/优化损失、树所用hub子集覆盖损失、以及低Recall大后悔样本。下一版另立设计。

**G3 完整在线成本筛查。** 只有G2通过才建立单方法独立纯wall路径；count与wall分开，warm-up、方法轮换、线程、cache与批量预分配冻结。比较Fast1、Fast3、选中S，报告router、graph、total NDC和端到端wall；不能用MAC、graph NDC或逐query latency之和代替QPS。L64/128先作质量匹配检查；若不能形成相邻工作点的同Recall/同QPS比较，须先登记有限的额外L点及比较族，不能事后自由挑交叉点。

首轮两个L各有对应的冻结policy，不将L64树在新L上运行的结果混称为“该L专门训练的树”。若后续额外L复用已冻结的某棵树，须预先声明映射和仅改变搜索L的比较意义；若按当前method为新L另训树，则需新增全H fit/calibration/audit标签及训练预算，并重新冻结相应评估族。80m中剩余验收搜索额度不自动授权新L标签生成或模型训练。

**G4 后续正式验证，另立预算。** 通过成本筛查且方法冻结后，三独立hub/model builds、tail与至少两个相邻工作点的正式比较：同Recall QPS≥+10%，或同QPS Recall≥+1 pp，并有预定校正区间支持。最后才访问held-out10K×3。三build不等于三timing轮；历史开发audit不等于held-out。强基线、公平离线成本、共享图身份、完整在线成本和重跑依赖均继承spec，不因允许重训练而降低。

## 5. 交付要求

每阶段保存完成/停止状态、实际命令与源码/库/模型/输入hash、query和hub映射、全部比较、逐query路由/Recall/NDC、有效训练样本权重与树容量、离线GT/标签/teacher/tree/导出成本及在线wall。未知历史成本记null+reason，不能记0。任何理论主张须单独列出假设与适用范围；当前允许的结论只有指定模型、指定数据和预算下的经验结果。
