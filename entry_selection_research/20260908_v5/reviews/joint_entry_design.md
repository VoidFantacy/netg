# 候选入口发现与可部署路由的联合设计：碰撞审计

2026-09-08。状态：`CONDITIONAL_RESERVE_NOT_HIGH_NOVELTY_CLAIM`。只读原论文、作者代码和本地契约；未训练、安装、运行ANN或打开原始向量/GT。原件及SHA见 `../sources/joint_entry/download_manifest.json`、`author_code_manifest.json`。10分钟有界检索不是穷尽新颖性证明。

**判断：仅“选一个小hub池，再学路由”不能作为独立高原创性方案。** 在既有H内让不同tree leaf选择hub，正是v4已经设计的动作学习；加池大小惩罚仍是其容量变体。若保留本轴，应缩为“在冻结搜索图上发现既有H外的新入口，并按照受限路由器能实现的收益决定加入/替换”，作为条件性备选。当前尚无证据证明旧H是必须更换的瓶颈，更无端到端收益。

## 近期原论文与作者实现的直接碰撞

| 工作与一手来源 | 已有机制 | 本候选必须超出的部分 |
|---|---|---|
| [GATE，2025原论文](https://arxiv.org/abs/2506.15986)，[作者搜索代码](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/tests/test_gate_search.cpp) | 先以HBKM选小hub集合，再用图结构与query监督学习入口表示，额外导航索引降低在线开销 | 不能声称首次小入口集/图感知/离线重在线轻；须把hub ID本身的选择纳入可部署收益目标，而非固定HBKM后只变embedding |
| [RoarGraph，VLDB2024原论文](https://kay21s.github.io/RoarGraph-VLDB2024.pdf)，[作者代码](https://github.com/matchyc/RoarGraph/blob/7c9ef95dcb9b1022a2e3b8dfee55409ad73c605e/src/index_bipartite.cpp) | 用训练query的NN构建query-base二部图，再投影和增强连通性，最终改变base搜索图；作者搜索从`projection_ep_`进入 | 本候选应保持原NSG逐边不变，只修改入口集合与query→ID路由；若把query-GT共现投影成边，就落回RoarGraph类构图 |
| [LIRA，WWW2025原论文](https://zheng-kai.com/paper/2025_www_zeng.pdf)，[作者代码](https://github.com/SimoneZeng/LIRA-ANN-search/tree/7beeee52d5b9a880f443876e24563713146ef581) | 从KMeans分区出发，probing模型预测含kNN的分区；同一模型指导数据复制和动态分区探测，随后构建分区内索引 | “构造与路由共同学习”“兼顾覆盖和可预测性”本身已高度重叠；需要固定单一NSG、监督真实单入口kernel结果而非kNN分区membership、没有数据复制/区域池 |
| [NGFix/RFix，2025原稿](https://arxiv.org/abs/2510.22316) | 以真实搜索和Escape Hardness定位局部问题；RFix修复到query邻域的可达性，NGFix修复邻域图结构 | 从失败轨迹找关键点并不是新点；本候选若只把RFix关键点改叫hub，原创性弱。明确不加边，新增节点是否可由轻路由稳定选择必须另证 |
| [Routing-Guided Learned PQ，2023预印本](https://arxiv.org/abs/2311.18724) | 以邻域和路由特征训练可微量化器，压缩距离计算服务图搜索 | “用实际路由信号训练紧凑表示”不是首次；其对象是PQ和搜索中评分，本轴对象是入口ID发现。未在本轮执行或核实其代码，不能据摘要推断完整实现 |

已读GATE原稿§4.1：hub为平衡簇中离centroid最近的真实点；后续才做feature distillation。因此本候选若改变真实hub ID的机制，确有相对GATE这个流程的区别，但尚不等于有可发表的新算法。保存原稿 `gate_paper.txt:456–490`。

LIRA作者代码核查：`lira_model_probing.py:5–38`含query向量和到centroid的距离两个输入支路，sigmoid输出分区概率；`lira_LIRA_smallscale.py:225–285`以kNN分区标签、BCELoss训练，并以模型输出做redundancy。它不是直接优化冻结NSG单入口Recall/NDC。作者主分支本轮冻结为 `7beeee52d5b9a880f443876e24563713146ef581`。RoarGraph冻结为 `7c9ef95dcb9b1022a2e3b8dfee55409ad73c605e`；`roargraph_index_bipartite.cpp:2311–2325`从单个`projection_ep_`初始化，但其底图本身是新投影图，不能和本地冻结NSG入口层混同。

古典算法组合早已学习按实例选择互补算法，强调特征计算成本和补足现有组合的困难实例；这也是入口池问题的抽象先例，不能把“互补且易选的portfolio”当作原创。[作者原文，IJCAI2003](https://robotics.stanford.edu/~shoham/www%20papers/portfolio-IJCAI03.pdf)。本轮近期检索未找到与下述完整受限入口发现问题完全相同的原文，但不能据“未找到”声称首次。

## 唯一保留的主候选：以受限路由收益驱动入口发现

记原图G、原kernel A固定，`u_L(q,e)`为A从真实base ID e出发所得R10，D为相应graph NDC；先分开质量与成本，不通过自由调λ掩盖退化。选择最多m个入口P以及固定轻量函数类F中的路由f：

`max_{P⊆C, |P|≤m; f∈F, range(f)⊆P} E_train u_L(q,f(q))`，同时限制实际在线推理预算，并在独立开发审计检验完整成本。

C必须允许既有H之外的真实base ID，否则只是v4的动作压缩变体。F先冻结为有界稀疏线性树或另一明确轻结构，不把“任意神经模型”留成事后改进空间。**原NSG可以完全不变**：e本来就属于base，原search_new支持自定义single entry。变化的是离线查询如何到达该ID。

具体新增的研究机制应是有界的入口列生成：

1. 在fit内把查询分为入口提议/效用测量/路由选择折，按轮交叉使用。当前route实际损失大且有足够支持的query组产生候选；候选可来自已冻结fit轨迹的被访问节点，另保留训练GT高频节点与均匀候选对照。禁止把某审计query的GT节点直接新增为该query入口。
2. 每轮只给预登记数量的新ID补测真实single utility列；候选来源是提议器，不是有效性标签。未测单元格不能当失败/零收益，也不能让surrogate估计替代主验收。
3. 固定在线结构预算，对每个候选交换在fit内重新优化相同F，以未用于该次拟合的内部折的**实际选择收益**决定接受；不能只看`max_{e∈P}u(q,e)`的免费oracle提高。内部折在多轮被用于候选交换，是训练选择信号，不是无偏的最终泛化估计。外部calibration/audit保持不参与轮内候选发明。轮数与总搜索数冻结，避免无限适应同一开发集。
4. 最后一次性冻结P和f，再做未使用audit与全成本对比。用同一个候选母集C、同m、同F、同标签预算比较coverage-only选池与路由收益选池，才能归因到联合设计。

其可证伪的学术增量是：**在原搜索图不变、标签预算和路由容量相同的条件下，按可部署路由收益发现的入口池，可能以略低oracle覆盖换取更低选择损失，最终获得更好的Recall–wall曲线。** 这是要检验的假设。列生成、双层优化、树训练各自都已有先例；有价值的贡献需要新的可计算交换准则/误差控制或可靠跨任务实证，而不是把三者串接后重新命名。

覆盖分解可精确写为（对固定C、同q/L）：

`oracle_C − u(q,f(q)) = [oracle_C − oracle_P] + [oracle_P − u(q,f(q))]`。

前项是池覆盖损失，后项是该池下实际路由损失。联合方案须改变二者的权衡；在既有H之外的C上能找到更好入口也只是候选空间诊断。若整个C的标签都没测，不能声称知道oracle_C或把缺失列当成已穷举。

## 三个立即否决的换名版本

- 以GT覆盖/最近距离或query聚类选代表，再拟合均值prototype：回到QGT-Cover/Fast或LIRA式几何标签，未优化真正搜索动作。
- 在既有H上按真实utility做greedy cover，然后v4树：可当强对照，不足以成为独立高原创性方法。`F(P)=sum_q max_{e∈P}u(q,e)`在非负固定矩阵上是标准单调次模函数；这一覆盖性质不包含受限路由器f的可预测性，不能把其greedy保证迁移到部署性能。
- 从失败轨迹统计“好节点”、按出现频率选hub：和旧ACO/DPC的使用频率思路、RFix关键点及query-GT覆盖都接近。没有严格同预算消融证明“可由路由器实现”带来的收益，就应否决其高创新主张。

## 成本和最小证伪门槛

新hub不会免费产生训练标签。每轮新增b列，在n行、两个L上全测，增加`2nb`次搜索；例如n=20K、b=64，一轮就是2.56M次/数据集，尚未计开发行、提议轨迹、旧池标签和重训。C若来自20K×GT10而达数万ID，完整矩阵会迅速超过v4的72.14M总预算。必须明确总C、每轮列数、轮数、query×entry实际测量数和缺失机制；不能从“最终m很小”反推离线便宜。

最小gate先固定一个有界C（含H外节点）与m、F：比较①原H+相同F；②从同C选择的coverage-only池+F；③联合选择池+F；④随机/频率池+F。要求同池规模时取m=|H|，或为①另设同m的旧H子池；全H另报参考，不能用池规模差异归因机制。全部训练/提议只用fit，query配对审计。若C外新增节点只提高免费oracle却不提高受限F的实际收益，直接否决本候选；若实际收益不优于②，否决“兼顾可预测性”的机制；若完整router+graph wall不改善，也不能以缩小m或降低router操作数过关。不能先看到结果再追加C、m、F或轮数。

当前label generation与router refit没有新实测时间；v4成本预算不是本候选的自动授权。拟合/提议/测列/导出/在线分别记账，并与只训练原H路由器比较额外离线成本的回收条件。

## 哪些本地产物需要重建

依据当前`spec.md:175–188,280–282,338`：只替换/增加真实hub、保持base/metric/G/kernel/split不变时，原NSG和已有有效exact train GT可复用。已测且身份完全相同的旧`(q,e,L)`单入口列可按行/ID拼接复用，新e必须实测；不能仅因hub列表变动就假称所有旧列数值失效，也不能把旧完整矩阵当作新池完整标签。

新池的raw hub ID/向量映射、几何basin标签、所有prototype或入口embedding、路由模型、路由索引、oracle覆盖参照、全部路由与下游评测需重新建立或显式映射校验。若不使用prototype，可免造该模块，不能复用旧prototype冒充新入口画像。若发生图改边、kernel/metric/base/预处理变化，则兼容旧single utility也失效，必须重做对应标签与正确性/计时验收。旧产物保留。

**最终等级：机制方向有条件价值，但目前原创性至多中等且证据不足，不建议把它包装成已确定的高原创性主荐。** 必须先排除“v4加入口池大小约束”的同义改名，再证明H外入口发现与路由可实现收益之间的增量。若另外三至四条候选有更强的结构性新问题和证据，本轴应排在其后。

## 附：原位 continue-vs-inject 的三分钟独立挑战

**条件性保留，旧 alternate chooser 的负证据仍然相关；不得把区别写成“旧标签只有 standalone Recall”。** 当前原件 `probe_reroute_results/analysis.md:7–12,41–55,70–100` 和 `benches/run/train_trace_conditioned_rerouter.py:203–235` 表明，旧方法已用 probe 与第二次搜索合并后的 Recall 和 total graph NDC 作连续效用监督，并以相对 restart merged Recall 的 gain 加权；输入已有付费 L10 trace、候选与 frontier 的向量亲和及一/二跳图关系。其 frontier+topology 版本在 WebVid top-risk 20% 两预算分别损失 3.371/1.416 pp Recall，并增加 2.668%/1.036% NDC。因此“增加状态输入、预测干预收益、学轻量树”各自都不能绕过历史失败。它没有证明任意状态下原位干预不可预测，但明确提高了此方向的证据门槛。

尚未被该旧实验直接检验的区别是：从**同一完整搜索 checkpoint**分叉，在相同剩余实际工作预算下比较原位 continue 和插入入口 e 后继续，保留 visited、候选池及其 expanded flags/cursor、结果、已有距离与任何会影响后续搜索的状态；直接监督 `Delta(q,s,e,B)=R(inject-and-continue)-R(continue)`，将 continue 作为显式动作。这样可能消除重复扩展，并使某些 e 的作用取决于“原有 frontier 将继续探索什么”，而旧 restart/merge 无此执行语义。可是保留状态也可能让 e 早已被 visited、被有限候选池立即剪掉、或只重走已搜索区域，导致可利用增益更小；减少重复工作本身不会自动产生更可预测的入口身份。最低研究门槛应依次是：no-op resume 与不暂停执行逐查询等价；固定 checkpoint/候选生成器/总预算下确有正的原位干预 oracle 空间；低成本、GT-free 的状态和候选特征能在隔离查询上预测直接增量并胜过同预算 continue、固定注入和旧 restart/merge；最后计入特征、候选路由、注入距离、去重和状态管理的完整 wall。若只有免费 oracle 改善，或必须重新全 H 选择才出现收益，应停止；不能重新扩大通用 chooser 扫参。旧 restart/merge 标签不能直接充当新 Delta 标签。此附录只评价设计，没有恢复旧停止分支或授权实现/实验。
