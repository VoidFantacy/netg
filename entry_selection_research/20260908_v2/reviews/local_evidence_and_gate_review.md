# 本地证据与最小 gate 独立审查

审查日期：2026-09-08。范围：完整阅读 AGENTS.md → summary.md → spec.md → s-target.md、当前 direction/state/next-dialogue 指令，再只读源码和已有小型结果。没有运行 ANN、训练、构图、安装、统计实验，也没有打开原始 query/GT/base/图。本文件是本轮调研的审查记录，不是实验 gate；旧状态不改变。

## 1. 独立判断

优先证伪“固定一次 Fast top-8、保留 anchor，直接预测真实共享 beam 的三入口集合效用”。这个建议仍是研究问题，不是已经成立的新算法。候选池的搜索效用覆盖目前缺少主瓶颈证据；单入口效用蒸馏已与本地静态 ranker、search-aware centroid、residual prototype 和 cost-first atlas 大幅重合。

建议主检验固定 m=3；少选为 1/2 入口保留为诊断和固定 m 对照。否则收益可能只是改了入口数量，必须额外加入 C3/additive3 对照才能判断是否学到组合交互。三入口家族中的 anchor 是受控限制，不是已证明最佳的设计。

最强反驳：真实联合 label 修正了单入口监督与联合部署不一致，却没有自动增加在线可预测信息。若有限 beam 中的竞争主要取决于查询相关的长搜索路径，联合效用可能比单入口更难预测。一次失败后不能自然升级 MLP、在线 probe 或 Multi-view。

## 2. 真实调用链

| 事实 | 当前源码证据 | 解释边界 |
| --- | --- | --- |
| QGT 查询球面 k-means，各簇内先访问接近中心的查询，再选择其 GT 中首个未用 ID；不足时按展平 GT 补齐，最终 ID 排序 | `benches/run/build_fast_entry_variants.py:180–238` | 没有实际搜索效用评分，不是严格 set cover |
| top-1 GT 向量按 cosine 归最近 raw hub；查询单位向量和 raw-hub prior 求和再归一化 | 同文件 `:144–164`，top-1 取数 `:293` | 单画像、几何 basin 是实现事实；其是否导致搜索失败尚未证明 |
| QGT-only 覆盖无需 ACO/probe/神经训练属性 | 同文件 `:323–332` | 文件内通用函数的 `requires_aco_dpc=True` 不能覆盖该实际分支 |
| 旧 test 的 HNSW 使用 M16/efConstruction200，直接从返回最大堆弹出入口 | `benches/test.cpp:139–142,353–357` | 此处输出远到近；oracle helper 已 reverse，见 `bench_entry_oracle.cpp:173–178` |
| 新 paired Fast 显式使用 seed、M16/efConstruction200/ef10，并倒序填入 route | `benches/bench_hierarchical_eval.cpp:131–145` | 真实近到远；不得把旧端到端入口顺序说成同一契约 |
| 旧 search_new mode2 只消费前 min(n,3)，visited 去重，重复不从第4位补齐 | `ACSG/ACSG.cpp:1517–1537` | 不能将 top-m 文件长度当实际 m；包装层须先拒绝非法 ID，旧种子路径不应被假定有完整范围防护 |
| 种子按真实 base-query 距离重排，随后共享 visited 和 L 池 | `ACSG/ACSG.cpp:1565,1581–1614` | 同三个 ID 且没有真实距离 tie 时，路由反向输出本身通常不会改变种子排序；不能仅凭顺序修正声称质量收益 |
| searchKnn 先以 max(ef,k) 搜索，再截断 k | `benches/hnswlib/hnswalg.h:1273–1326`，默认 ef10 `:115` | 同索引/query、ef10 的 k3/k8 搜索池相同是源码支持的推断；需验收 prefix/anchor/count/plain，返回与打分仍有 wall 成本。旧 k32 触发 ef32 |

20K paired 重建读取 `[10000:30000)`，见 `hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p0/build_paired_fast.py:48–61`。该旧 wrapper 的 `:32–33` 有已结束 deadline，不可作为新实验命令入口。现有 paired manifest 确认 WebVid 815 hubs、802 有分配，Yandex 821/821，均 20K fit、pilot_queries_used=0；旧 30K prototype 被明确禁止作为新模型输入。只读 manifest 不等于本轮重新读取或核验原始样本。

## 3. Oracle 和负证据

| 证据 | 已观察到的结果 | 不支持的结论 |
| --- | --- | --- |
| WebVid 旧 validation 1K、815 candidates、K10/L64 | `oracle_entry_diagnostics/webvid_validation_1k_current_hubs_v1/results.json:6057–6079`：Fast top3 R=.6523、graph NDC=923.564；single oracle R=.8024、913.376；union-greedy3 重放 R=.7617、907.98 | 不证明新20K paired、双数据集、完整路由成本下存在同样提升；3 timing runs 不是3000独立查询 |
| Oracle 实现 | `benches/bench_entry_oracle.cpp:769–778` 每入口单独搜索，Recall 同分取较低 NDC；`:779–796` 按独立 hit masks 的并集增量贪心选三，再真实重放 | 没有真实联合 pair/triple 穷举；不是联合最优上界 |
| Oracle 计时 | `bench_entry_oracle.cpp:139–147` timer 仅包 search_new | 未支付选择/路由及部分重置成本，不是部署 QPS |
| 静态 ranker | `sparse_utility_ranker_results/analysis.md:5–16,20–39`：10K fit/10K validation，top32，单入口 R10/NDC L64/128，三 seed diagonal listwise；WebVid 同L +.197～.329 pp但NDC+.47～1.03%；Yandex近NDC L62比Fast64 R−.158～−.402 pp且NDC+.46～.89% | pairwise 替 listwise、top8 替 top32、低秩替对角均不独立构成新颖性 |
| Ranker 的监督部署差异 | `train_sparse_utility_ranker.py:133–138` 平均两 L 的单入口 R−.05·relative NDC；`:173–177` listwise；`:205–206` 部署取前三 | 单入口监督与联合部署不一致是事实；它是不是失败原因尚未证明 |
| Probe chooser | `probe_reroute_results/analysis.md:7–16,20–27,43–52`：真付L10 probe有增量检测信号，但frontier chooser风险20%下WebVid R−3.412/−1.426 pp、NDC+2.593/+0.969% | 不能说 trace 没有信息，也不能重启已失败在线 probe 家族 |
| 拓扑 chooser | 同文 `:70–95`：风险20%下topology R−3.577/−1.381 pp，frontier+topology −3.371/−1.416 pp，都多付NDC；Yandex按规则未跑 | 单纯增加“图感知”特征不是未测新机制 |
| Cost-first atlas | `finite_beam_reachability_diagnostics/v2_distillation/decision.json:10–15` 四点utility CI跨零；源码 `run_cost_constrained_reachability_distillation.py:15–20,86–112` 为1600 fit/400 audit、64近邻历史查询、至少4次entry观察、均值±SE成本约束、top8，无在线probe | 历史近邻效用、保守下界和蒸馏也已有具体失败控制，不只是从未实现的建议 |
| Multi-view | `target_basin_formalization/20260907_v1/report.md:3–13`：等total-NDC R10差WebVid−14.697/−4.960 pp，Yandex−4.103/−1.463 pp，E2–E4未跑 | 不能恢复多路扫描或称已有完整成本改善 |
| Multi-view 精度与成本 | `pilot/hnsw/report.json:117,124,339,346` 后两view exact top8 set Recall .9873125/.9883375/.9971875/.997575；WebVid routing122.2987→642.3368（`:213,222`）、Yandex116.112→549.3762（`:435,444`） | 失败不能简单归因为近邻检索完全失真；其质量代价由剩余搜索预算缩减主导 |

旧 NETG 真实搜索监督可直接核对 `benches/bench_generate_labels.cpp:187–207`：top1 GT、逐hub probe、成功后取最小 NDC；`:212–226` 是失败时几何 fallback 和 min_cost=-1。因此“学习入口”“真实搜索监督”“reachability”都不能单独声称新颖。

## 4. 对最小 gate 草案的审查

### 4.1 已发现且已反馈的硬问题

1. 原 G3 五方法×双数据集×六L×10K×五轮 wall，单计时已300万search，违反全流程300万上限。修订为每数据集 C/additive/Fast3×L48/64/96/128，以及 Fast1/Fast2×L64/128，共16点；双数据集各一次count＋五轮timing为1,920,000次search。这个窄pilot不能声称覆盖 Fast1/2 的完整frontier，也不能替代最终强基线。
2. 两个代理必须同 anchor、固定 m3。否则 unrestricted single-utility top3/union-greedy 可能不在21个anchor triple家族中，联合oracle与代理不是同一决策空间。未受限对照可以额外列示，但不能代替主机制控制。

### 4.2 唯一搜索次数核算

以下是保守上限，重合缓存可以减少实际调用，但不得少报真实执行：

| 阶段 | 核算 | 两数据集合计 |
| --- | --- | ---: |
| pilot128，全池加128固定扩展候选、两L、全单入口 | 128×2×[(815+128)+(821+128)] | 484,352 |
| pilot512，C8的8single与29个anchor的1–3集合，去掉重复anchor singleton | 512×36×2×2 | 73,728 |
| 内含pilot64检查全92个1–3子集，复用已有36动作 | 64×(92−36)×2×2 | 14,336 |
| fit2048，同36动作、两L | 2048×36×2×2 | 294,912 |
| 修订后的G3 | 16×2×10,000×(1+5) | 1,920,000 |
| 合计 | 未计正确性、额外重放、暖机 | 2,787,328 |

剩余212,672次不能被当作自动追加参数/样本的授权。建议 G2 使用与 G1 不重合的预定 pilot512，新增73,728次标签，总计2,861,056次，仍可为正确性、暖机及有界异常复查留下138,944次。若使用同pilot512，须明确这是开发筛查，G1筛查和后续G2不是两次独立确认。

### 4.3 在实现前必须冻结的细节

- **模型主动作空间：** 推荐C只选21个anchor triples；29集合只用来解释基数效应。若仍部署可变m，须单列同m3的C/additive主检验，不能用少选入口的收益支持组合交互。
- **Oracle目标：** 区分最大Recall、最大U、受成本约束的oracle。`argmax U`不保证Recall高于`argmax Recall`的代理；G1的+.5pp究竟比较何种固定选择必须写明，并同时保留R/NDC向量。NDC surrogate 不等于wall。
- **G2门槛：** “恢复oracle余量≥20%”须说明余量定义、分母正值条件和区间；建议把它列为描述性次指标，主门槛仍是相对Fast和additive的配对差。分母很小或区间跨0时不能算稳定比例。
- **线性模型契约：** 明确共享是每数据集跨L共享参数，还是两个数据集合并拟合；明确全部特征、fit标准化和ridge损失的N归一化/正则系数，不能只写≤48特征而留待扫选。建议用`phi(q,S,L)−phi(q,Fast3,L)`且无截距，保证Fast3预测delta严格为0；同分优先Fast3，其后按固定ID规则。
- **GT-free约束：** 标签中的D_F可来自离线Fast搜索，在线打分不能先搜索Fast来取得它。不得把实际Recall、真实graph NDC或pilot GT派生量放进特征。raw-IP与query归一化表征的区别需要在接口和manifest中分别记录。
- **负控制：** 按query块打乱整个动作标签向量，并保持同query两L配对；不要逐动作打乱来假装有独立样本。一个固定置换只是反泄漏诊断，不是正式置换p值检验。
- **统计单位：** bootstrap以query为单位，保留该query的全部动作/预算配对；36个动作、2个L、5个timing round都不是额外独立Recall样本。预定比较族至少需包含双数据集×两L×两个代理/模型对照。CI未过门槛可以停止本次筛查，但只能称NO_GO本配置或INCONCLUSIVE，不能声称数学不可预测。
- **缓存公平性：** G2候选选择若全在已有动作家族可直接查保存结果；这只是离线选择验证。G3真实路由不可读取这些query-ID动作表。count和plain必须真实在线生成同route/结果，oracle成本单列。
- **扩展池含义：** 新128 ID必须在pilot搜索/GT结果不可见时按确定规则生成；不够128时拒绝或按预定规则收窄。该扩展池的single gap仅是这个有限候选扩展的证据，不能视为所有base入口或所有池构造方法上界。
- **总资源与阶段超时：** 4小时是硬上限，不是已有吞吐支持的ETA；到时不完记INCONCLUSIVE/预算停止。≤8GiB artifact、≥10GiB磁盘余量、仅一个重数据集进程。每次实际search（含warmup/count/plain/重放）都入账；原始base/图不复制，重复timing轮保留聚合值及必要身份，避免把每轮完整trace写入JSON。

## 5. 审查结论

修订后的预算算术可以成立，且真实联合标签与旧单入口效用方案存在可辨认的监督/部署区别。当前仍无联合收益、可预测性或完整wall增益证据；推荐只意味着优先检验这个差别。主动作空间、oracle目标、特征及统计族须在未来执行协议冻结后才能实施，本次不运行。外部GATE等强基线、三独立构建、双数据集至少两个相邻工作点的最终1pp/10%门槛和方法冻结后的held-out仍是后续正式结论所必需。

## 6. 最终草案交叉检查补充

已只读检查本轮 `minimum_gate.md` 和 `recommendation.md`。主m3、独立D2、Recall oracle与utility oracle分开、无截距差分特征加fit RMS缩放、恢复比例降为描述性指标，均已纳入。40维表的12维可加块＋8维补入口交互及其L条件项数目正确；B-single的单入口标签与B-triple-additive的真实三入口标签控制可以区分换标签和补入口交互。G2的双数据集×两L×三个对照=12项，调用数2,861,056＋138,944余量=3,000,000，算术正确。

该次交叉检查另外反馈以下执行契约问题，是否修订以主草案最新文本为准：

1. G3无匹配bootstrap置−1时，四项Bonferroni双侧CI下分位是0.00625；无匹配超过约0.625%会把下端压至−1附近。因此95%的匹配率前置门槛不能代表实际可通过要求，应明示更严格的CI条件，或改为一致的匹配率门槛。若增添主对照并扩大比较族，还须相应重算。
2. G3对B-single/固定m的“同样好且C无增量则不推进”需要确定数值及统计规则。G2同L对照不能证明同成本的交互贡献。可在现有测量结果上加入C对B-single的配对匹配检验，不新增搜索；Fast1/2实测点若直接Pareto支配候选点，也应明确停止规则。
3. 最终40维表没有rank特征，推荐文字的“分数/排名差”应与表一致。s_e若重新计算qhat·p_e还需8个prototype点积；若只计8个raw点积，应明确复用HNSW返回分数及其float转换语义，不进行额外exact rerank。
4. 真实动作必须有确定的入口顺序，例如anchor先、补入口按C8 rank；不能只写无序集合而忽略旧kernel真实距离tie时的顺序行为。

上述均为草案可直接修订的问题；审查没有运行模型或实验，不能提供40维特征有效性或最终性能结论。
