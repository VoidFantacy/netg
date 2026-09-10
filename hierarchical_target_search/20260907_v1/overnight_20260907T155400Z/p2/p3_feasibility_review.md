# P3 最小可行实现与预注册审查

状态：**设计审查；未实现、未启动 P3**。本文件只依据 `s-target.md`、本轮 `protocol.json`、当前 P2 源码及已存在的分区资源记录编写。没有读取 fit 查询/GT、base 向量或冻结图内容。P2 gate 仍由主任务结合结果与预选 trace 决定；本审查不替代该 gate，也不自动授权 P3/P4。

最小可行方案是：共用一个完整的 **16 粗区域×16 细区域**图结构初始化，分别以 λ=0/1 对 **256 叶区域的既定 J** 做两轮确定性节点移动，同时保持粗、细两层全局容量上限；每个结构各建固定 **3 门户/叶**的 frequency 与 greedy 两个版本，构成 2×2。四个模型都只做 train-only oracle 的统一池/概率区域池比较，暂不训练 P4 层次预测器。固定门户数为768，既满足2–4范围，又低于 WebVid815/Yandex821预算，避免把更多门户的收益误判为更好的选点。

## 1. 已确认的现有实现及直接缺口

| 项目 | 当前已确认事实 | P3 最小新增内容 |
|---|---|---|
| 图读取 | `p2/partition_graph.cpp` 以 O_RDONLY、只映射原 NSG 邻接；原向量不复制，非对齐 int32 用 memcpy | 复用解析/保护；增加原 directed 入邻接索引以计算正确移动增量 |
| METIS | i64、graph-only 对称去重 CSR、固定 seed/ncuts1/niter10；验证 coverage/非空/严格容量 | 16-way 粗分区及16个 induced coarse 子图的16-way 分区；按原节点顺序构建局部编号 |
| balance 修正 | 现有 helper 补偿 METIS 内部额外0.0000499，最终用整数 floor 检查1.2 | 将 helper 的目标改为显式参数；不能把写死1.2直接套在所有子图 |
| cut 记录 | 同时记录 symmetrized-undirected edgecut 和 original-directed nonself cut | 优化目标明确用后者；两个数继续分别报告 |
| 区域/门户模型 | P2 只支持64区域、每区2门户、查询画像、fit20K | 新 schema 明确256叶、16父区域、3门户、λ、初始化/移动/候选/查询子集 provenance |
| evaluator | `region_limit=64`、Model 强拒其他区域/门户数量、64-score/2-portal loops、64维 oracle mass | 显式 P3 schema 分支、256维 oracle mass、3-portal循环；保持旧 P2 schema 不变 |
| search kernel | `RegionalSearch.h` 接受 region_count 参数，labels 为 uint16，最多4 active；每个 route entry数组18槽，default shared seed另列 | 固定3门户×4叶+Fast anchor+default最多14个去重前种子，现有数组容量足够；仍需实际消费验证 |

不能从旧64分区任意合并/拆分后声称完成新的16×16 graph-only初始化；两个 λ 分支必须绑定完全相同的完整初始 labels checksum。P2 artifact 和可执行文件的历史版本保持可识别，不覆盖已有证据。

## 2. 建议冻结的初始化及容量契约

**主任务提出的初始化留量是可辩护且更简单的选择：粗分区初始化上限1.1，最终粗/细两层上限仍为1.2。** 1.1只用于给子分区留可行性空间，不是在线容量参数；必须在任何 P3 数据执行前写入协议，且两个 λ 分支共用该初始化。相比新增一次可能提高 J 的容量修复，这减少了一段独立、难以归因的算法。若初始化不满足其注册约束，保留失败产物并按正确性/可行性问题处理，不事后放松标准或挑 seed。

步骤如下：

1. 对同一冻结图的无向并集 CSR 做16-way METIS，固定 seed=`2026090711`、ncuts=1、niter=10、numbering=0；粗初始化硬上限 `floor(1.1*N/16)`，使用已有 dependency-epsilon 补偿方式。
2. 对每个粗区域依次构造其诱导无向子图，按原 base ID 升序建立 local-to-global；每次只保留一个子图。局部 METIS 仍16-way，局部 seed 的派生规则预注册（建议全部使用同一固定 seed；不可根据结果换 seed）。
3. 细区域使用**全局**上限 `F=floor(1.2*N/256)`。对节点数为 `n_c` 的粗区域，子分区实际允许的均衡因子应由 `16*F/n_c` 推导，再做向下浮点/内部 epsilon 补偿及最终整数验证。不能直接用局部1.2：若粗区域为全局均值1.2倍，再给其孩子局部1.2，会允许全局细区域1.44倍。
4. 在粗初始化最大1.1倍均值处，子分区仍有约 `1.2/1.1−1=9.09%` 的局部余量；这避免让最重 coarse 的子分区被迫几乎完全等分。仍须验证 `n_c <=16*F`，不能只凭浮点推导假定可行。
5. 建议 METIS 输出 ID 按每区域最小 base ID 规范化一次；细区域全局 ID=`16*coarse+local_leaf`。规范化后保存共同初始化，开始 refinement 后不在轮中重编号。每叶至少3个节点，保证固定3个真实不同门户可定义。

最终硬上限为：

| 数据集 | N | 粗容量 floor(1.2N/16) | 叶容量 floor(1.2N/256) |
|---|---:|---:|---:|
| WebVid | 2,505,000 | 187,875 | 11,742 |
| Yandex | 10,000,000 | 750,000 | 46,875 |

注意 WebVid `16*11,742=187,872` 比单独粗 floor 少3个节点，这是实在的整数可行性边界。共同初始化的1.1留量避开此边界；后续细、粗容量同时检查，16叶各自合法也会自然限制该 coarse 的可用总节点数。每次移动既不扩容也不使用临时超容量。

## 3. J 的含义与精确移动增量

建议按主任务最新选择冻结：

`Π` 指256个叶区域，粗标签始终为 `leaf_id//16`。优化

`J_leaf = C_directed / M_directed + λ * sum_q(distinct_leaf_regions(GT10(q))−1)/(9*Q)`，

其中 Q=20,000 fit 查询；M 是原 frozen directed NSG 中所有有效、非 self 的**存储边槽数**，去除 padding/self-loop，保留方向，互反边计两次。若原图存在重复存储边，也按固定槽定义计数并报告；不能在 refinement 中悄悄去重。无向去重 CSR 只服务于 METIS 初始化，不作为 J 的替代。

粗层 cut、GT distinct、大小分布均单列报告，但**不加入 J 的加权和**。这是最小的明确解释；若后续要同时优化粗/细目标，须另行预注册相对权重与轮次，而不能在当前 λ=1 中暗含新目标。

对节点 u 从叶 A 移到叶 B：

- `ΔC = out_to_A + in_from_A − out_to_B − in_from_B`，self 边已排除。必须同时计入 incoming/outgoing；一对互反边给两份贡献。无向并集的单位度数不能重建此增量。
- 令 `c[q,r]` 为 query q 的 GT10 在叶 r 的数量。对于 GT10 包含 u 的每个 fit query，`Δdistinct = 1[c[q,B]==0] − 1[c[q,A]==1]`；对不包含 u 的 query 增量为0。GT10必须先验证ID唯一，才能使用此单节点公式。
- λ=1 时，以整数比较 `ΔC*(9Q) + ΔS*M <0` 决定严格下降；λ=0只检查 `ΔC<0`。当前规模可用 int64，但实现须明确溢出检查。避免浮点阈值改变“严格降低 J”的判断。

两个分支从共同初始化复制 labels；各执行**恰好两轮**原 base ID 升序扫描。每个节点的候选目的叶由其 incoming/outgoing 邻居所处叶及（仅 λ=1）同一 fit GT10 超边中的其他叶组成，去重后按叶 ID 排序。选择合法且增量最小的严格改进移动，增量相同按目的叶 ID 破同分；立刻更新 labels、叶/粗计数与受影响 query 的计数，再处理下一个节点。目的叶可跨 coarse，但此时必须同时检查目标 coarse 的最终1.2容量。源叶至少保留3个节点。

λ=0 的移动路径无需读取 GT incidence，即为同一 refinement 实现的纯图对照；其 GT distinct 仅在独立事后结构诊断中计算。不在 λ=0 中额外使用 GT 选候选、换遍历顺序或挑初始化。λ=0 不保证最终 labels 与纯 METIS bitwise 一样，因为两轮 cut-descent 可能继续降低 cut；需要保证的是同初始化、同容量、同移动/破同分规则下，λ=0与独立 graph-only reference 的输出完全一致。

每轮后独立重扫原 directed edges 和 fit GT10，核验增量累计与完整重算的 C/S/J 完全一致、两层容量及全覆盖成立。无 GT 的 base 节点也必须被分区并参加规定的扫描，不能只对训练目标子集构建区域。

## 4. 两个结构×两个门户规则的最小设计

固定每叶3门户、总768，是比“frequency2对greedy2–4”更清楚的归因设计。建议四个 artifact：

| 结构 | 门户 | 回答的问题 |
|---|---|---|
| λ0 | frequency3 | 同层次、同 refinement 的纯图结构基线 |
| λ1 | frequency3 | 固定频率门户规则时，GT 共现结构变化是否传递到搜索 |
| λ0 | greedy3 | 固定 λ0 结构时，离线覆盖选点相对频率选点的作用 |
| λ1 | greedy3 | 固定 λ1 结构时，同样门户规则改变的作用及与结构的交互 |

只做“同一个门户规则的 λ0/1”也能回答该规则条件下的结构效应；它不足以单独验收 P3 的门户选择贡献。既然当前 P3 同时包含结构与搜索代理选门户，2×2是成本仍小、解释更完整的最低充分设计。不得只报告四格中最好一格，或把结构/门户一起改变的差值写成单一因素因果。

候选与查询规则建议冻结为：

- 每叶最多8个候选：按 fit20K GT10 中该叶真实 base ID 的出现次数降序、ID升序破同分，取top8。不足8时是否补足必须固定；最简单是以该叶最小未选 base ID 补至 `min(8,叶大小)`，并标记 fallback。Frequency3直接取前三；两个门户方法使用同一候选集合。
- 每叶拟合查询来自 fit20K 中 `GT10∩该叶` 非空的 query。最多128，按固定 seed/hash 对 `(dataset, original_fit_query_id, leaf_id)` 排序选择；不要优先挑 pilot表现好、portal收益高或距离方便的查询。两个门户方法在同一结构上共享这组查询。
- 每个 `(leaf,candidate,fit-query)` 恰好执行一次无路由的**单候选入口**统一池搜索，原 directed NSG、原 raw-IP query、K10/L32。这里不额外加 Fast anchor/default seed，否则会混淆候选入口自身的离线代理。代理的种子定义是需显式预注册的选择，不是对在线语义的更改。
- 将每次结果转换成10-bit目标覆盖 mask：`returned10∩GT10(q)∩该叶`。Greedy3每步选能增加这些 masks 的总并集覆盖最多的候选，增量为整数 hit 数，tie按候选 base ID。每叶恰好选3个不同候选；即使后续增量为0，也用确定性tie规则完成固定预算并记录零增量。不需要再跑ANN来评估第二/第三轮 greedy。
- 该叶没有合格fit query时，不能编造代理收益：greedy3明确退化为frequency/fallback前三并记录无训练证据。这个fallback与查询筛选规则要在执行前冻结。

**真实上限：** `256×8×128=262,144` 次候选单入口搜索/结构；两个 λ 共524,288次/数据集，双数据集最多1,048,576次。Frequency3本身不增加 ANN probe；greedy1/2/3使用同一批缓存 masks，不将该数字乘3。每结构 mask 缓存至多524,288字节（uint16）；加NDC等小数组仍很小，无需写出百万份 JSON或全部结果 IDs。

这些单入口 L32 结果只是离线选门户代理，不证明在线4区域、共享 visited/候选池条件下仍最优。完整成本分别记录实际 query-pair数、实际graph NDC/MAC、graph加载、候选构建、probe、greedy选择与写盘时间；旧 exactGT 成本未知则继续 null+原因，不把复用GT后的局部耗时称完整训练。

## 5. P3 搜索对照及 evaluator 的重新验收

P3先用四格模型分别运行 **oracle_unified / oracle_probability**，pilot的预定 L64/128、K10、激活4叶。最多4叶也天然涉及至多4粗区域，但这不是 P4 的层次推断算法。Oracle按真实 GT10 叶占比选择区域，仅作为 train-only 结构/门户诊断；不加入部署 Pareto，也不据它发布性能改善结论。

每格 unified/probability必须消费完全相同的 route，包括同一 paired Fast20K anchor、default shared seed、选中叶和门户；实际去重后入口数可能少于14，需要逐query记录并验证。四格总门户数768相同并不保证所有query的去重后种子数恒相同，不能漏报这个选点带来的差异。

需要重新进行的 P1验收：

1. 新 model schema 明确 `coarse_count=16, leaf_count=256, parent=leaf//16, portals_per_leaf=3`；oracle-only schema不应被当作已实现 P4 模型。若保留几何路由代码，也不能以它代替未训练的层次概率模型。
2. 去除 evaluator 的64维数组、64-score/64-MAC常数、2-portal loops及固定shape假设；仅P3分支接受256/3。`max_active=4`和当前18个entry槽可以保留，但必须实测至多14个种子全部被消费、合法ID/重复/空槽处理正确。
3. 256区域oracle mass及top4 tie规则、64旧P2回归、新 old/new CountDC与kernel计数、plain/count完整 route/result IDs、trace重放、shared seed ownership、跨 coarse/leaf 边均重新测试。
4. 新离线单候选proxy API无GT参数；评分/bitmask在搜索返回后完成。加测单入口K10/L32与已验收统一池的IDs/NDC parity。
5. 预分配、纯wall、AB/BA五轮、输出parts、参数/上游gate、pilot/heldout边界继续有效。对两数据集固定pilot小样本做真实回归后，才将P3数值视作有效。
6. `analyze_p2.py` 与 `analyze_traces.py` 的64/2/方法矩阵假设不能直接冒充P3验收：新增版本化矩阵/schema支持并保留P2历史规则。P3对比族在执行前固定，不能读取结果后挑格子或改工作点。

独立 λ0 graph-only reference parity、移动增量完整重算测试必须包括单向边、互反边、重复存储边、self/padding、GT源区域最后一个目标被移走、首次进入目标区域、跨 coarse移动、两层容量临界点，以及两轮 determinism。只通过编译或 METIS self-test 不代表这些新增语义合格。

## 6. 内存、时间与任务控制

下面是**已有 P2 测量**，只作为同机规模锚点，不是 P3 ETA：

| 数据集 | P2 valid directed nonself slots | P2 symmetric CSR原分配容量 | P2 METIS时间 | P2 command elapsed | P2峰值RSS |
|---|---:|---:|---:|---:|---:|
| WebVid | 49,611,457 | 793,783,312 bytes | 25.485 s | 28.118 s | 6,134,212 KiB |
| Yandex | 294,844,794 | 4,717,516,704 bytes | 155.563 s | 172.764 s | 35,699,900 KiB |

证据：`p2/{webvid,yandex}_partition_strict_v3/manifest.json` 与 `control/jobs/p2_partition_{webvid,yandex}_strict_v3.json`。P3的16+16×16分区、1.1初始化约束、两轮refinement和portal probes均未计入这些数字，不能简单乘17或直接复用该耗时。

可采用以下内存布局：

- 原outgoing邻接继续只读mmap；incoming CSR存int32 source IDs+uint64 offsets。按当前有效边数估计，额外 incoming arrays约 WebVid218.5MB、Yandex1.26GB（十进制），远小于重新复制base/整图。若选择weighted-union等价实现，必须验证权重恢复了所有原方向与重复槽；不建议为了省少量内存直接使用无权symunion。
- METIS初始化保留现有i64无向CSR，一次处理一个coarse induced子图，不保存16套子图副本，不让两个 λ 分支同时跑。局部ID映射用int32，容量允许时复用全局lookup缓冲。
- 节点labels uint16仅约5.01MB/20MB。GT10只有200K incidences；`query×256` uint8目标计数约5.12MB，node→query倒排可用40MB以内的dense offsets加不足1MB索引，也可用排序稀疏目标表。不能建 `N×256` 数组。
- 两个分支顺序处理，并将 portal probe阶段与METIS阶段分开，释放不再需要的大CSR。搜索阶段只加载一个数据集的冻结索引和预分配CPU workspace。
- 每轮保存紧凑 labels/checksum、C/S/J及accepted/rejected计数、固定少量移动例子和下次cursor。没有必要把每次候选移动写成长JSON；那会轻易超过本轮8GiB artifact预算。中断的半轮保持INCOMPLETE及可重建状态。

理论计算量约为每分支两次节点扫描及其 incoming/outgoing边扫描；候选目的叶最多256，GT incidences总计200K。用按区域直方图累积 graph degree和GT presence可避免每候选重复遍历所有邻边/查询。每轮独立目标重算另扫描一次原边和200K GT entries。METIS内部仍是单线程；读/写CSR预处理和独立portal probes可使用最多16CPU线程，但研究重任务只能一个数据集进程。

P3运行前应先保守预留至少60GiB可用RAM（这是工程预留建议，不是实测P3峰值）；保留≥10GiB磁盘并核验本版本artifact余量。实际ETA应在首个coarse/child任务和第一批固定128-query probes后根据日志估算。若剩余时间不足以完成对应任务单元，不启动跨截止任务；不能为了赶时间删掉 λ0或某个portal格子后宣称完整归因。METIS长调用仍需外层taskctl超时/独立进程组控制，内部checkpoint不能打断其C调用。

## 7. 执行前唯一需要冻结的清单

主任务目前偏好的选择已在本文具体化，但**本文不是执行协议的替代品**。P2 gate通过后，先把以下字段写成新的P3 protocol/amendment，再实现和跑数据：

- 同一完整16×16初始化；coarse init1.1、最终coarse/leaf全局1.2、fine ub推导与严格floor；METIS seeds及label规范化。
- `J`仅指叶分区，graph term为原directed validnonself存储边；粗层指标只诊断；λ0/1、两轮、候选目的地、节点顺序、整数严格下降和tie规则。
- 两层容量同时检查、每叶至少3节点、跨coarse moves允许；共同初始化artifact与两分支独占输出。
- 固定3门户、候选top8及补足规则、每叶≤128的fit-query确定性选择、单入口proxy、目标region GT10 mask、greedy3和无fit-query fallback。
- 2×2四模型、每模型oracle统一池/概率池、预定L64/128和同route检查；P3仍不允许据oracle发布部署收益或开启heldout。
- 新源码/模型 schema及P1重新验收、资源/截止控制、全部实际成本与失败产物的保存。

下一唯一最高优先动作仍是**完成并解释 P2 gate**。若未通过或只支持一次受限表示修订，应按该结论行动，而不是因为本文件已经准备就自动开始完整 P3。
