# 最小证伪 gate 草案：固定主入口、真实三入口组合

2026-09-08；`DRAFT_NOT_IMPLEMENTED_NOT_RUN`。本文件是可审阅的未来设计，不是运行授权。所列新接口、脚本、命令均未实现，本轮没有执行其中任何一步。旧夜间runner/deadline/gate不复用。若另获执行任务，先把本草案、实现差异、输入身份和资源限制冻结到新的执行目录，再运行；本调研目录不改成实验输出目录。

**唯一主机制固定m=3：同一C8、同一Fast主入口a，比较21个`{a,b,c}`的真实共享beam结果。** 29个含a的一至三入口集合只用于诊断；模型没有可变m、probe、额外view、辅助图、停止/队列修订。

## 1. 数据、已有使用历史与固定样本

| 项 | 冻结草案 |
| --- | --- |
| datasets | `webvid2_5m_light_v1`，`yandex_t2i_official10M_ip_v1`；分别2,505,000×512、first10M×200 |
| search metric / graph | 原始IP；WebVid源近单位范数不再变换，Yandex不归一化；原NSG `R64/Lbuild100/C512`，base/GT/图身份绑定，不改边 |
| hubs / paired Fast | 独立QGT5K，seed20260828的815/821 raw hubs；prototype仅用router_train `[10000,30000)` 20K |
| 可复用20K模型 | `hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p1/paired_fast20k/<dataset>/manifest.json`所绑定的prototype；按manifest重新验证后只读复用，不运行旧`p0/build_paired_fast.py` |
| fit labels | 只从上述20K中固定抽2048条；全部prototype允许使用20K，此处标签采样是有界证伪，不声称2048与20K成本等同 |
| D1机制筛查 | 历史pilot `[0,10000)` 中固定512条，绝不称未使用测试集 |
| D2可预测性审计 | 同一历史pilot内另512条，与D1完全不重合；D1标签不进入模型或超参数选择 |
| 全池诊断 / anchor诊断 | D1的前128 / 前64条，预先确定，不能按失败程度挑选 |
| G3成本筛查 | 历史pilot全部10K，已包含D1/D2；这是开发复核，不是独立测试 |
| budgets | K=10；G1/G2标签L={64,128}；G3固定有限曲线，见第7节 |
| raw validation / held-out | 本最小gate全部禁止打开；方法冻结后的正式协议另立 |

确定抽样而不读取query内容：按`SHA256(UTF8(dataset + "|entry_joint_gate_v1|" + decimal_original_row_id))`升序（哈希同分按行ID）排列各合法行号。fit取前2048；pilot前512为D1、接下来512为D2。保存原文件行ID及选择算法/版本，不复制原始query/GT。索引范围均相对router_train文件，禁止误用Yandex原learn的绝对偏移。

历史访问必须如实列入manifest：旧oracle/ranker/GATE/Multi-view已使用validation做性能评测或checkpoint选择；分层夜间版本对validation仅做完整性检查；项目Fast的held-out也有既往正式评测。不能称全项目validation/held-out从未使用。本gate不消费这些原始文件或旧30K模型，旧结果只作设计背景。

## 2. G0：先锁定入口与搜索契约

新评测层调用与当前`search_new(mode=2)`同语义的plain/count路径。三个种子、visited、候选容量、终止、返回收集、原始IP、tie行为均固定。不得直接拿区域搜索的独立global-topK路径冒充原search_new；若要抽取kernel，先逐ID和NDC验证，不能趁机换搜索规则。

每个集合序列化为anchor第一、另外两个按C8原rank升序；单入口按其自身ID记录。相同集合在所有控制/plain/count中使用同序列，kernel原有真实距离tie行为保持。

路由统一`M16/efConstruction200/ef10/seed20260828`，HNSW按同一插入ID顺序构建。新wrapper显式实现近到远结果顺序，核验top8包含同调用语义下的Fast top3，首入口一致；源码`max(ef,k)`只是验收依据，不替代检查。若C8非Fast3前缀，本版本先记INVALID，不静默改成并集、换ef或增候选。

必要验收：

- synthetic：1/2/3入口，重复、非法ID、空route、K>L、相同距离、padding；非法输入在评测层拒绝，不能依赖旧kernel注释所谓“越界兜底”。真实方法始终给三个唯一合法ID。
- 同实际入口的旧kernel/新plain/count返回ID、Recall和graph NDC一致；距离计数含初始化，重复种子只消费一次；无新增默认medoid/随机补点。
- 从fit内预定64条query、L64/128验收；需要增加parity动作时受第8节剩余调用预算约束。不访问D1/D2的GT做实现调参。
- GT只在结果返回后评分。真实router和search API没有GT、oracle策略ID、query→label文件、Fast已完成搜索结果或D_F输入。
- timer前完成模型/图加载及线程workspace/输出缓冲分配；timer内含归一化、短名单、8个prototype加8个raw点积、组合打分、必要reset/dedup、搜索、结果写入。GT评分/hash/trace/JSON及counter instrumentation在timer外。
- count与plain是独立运行且输出一致；batch wall只计单个方法，禁止将线程内latency均值倒推QPS，或相加不同批次router/graph时间冒充端到端。

G0失败是实现/测量无效，不能评价算法。未通过不生成新效用标签；只能在新任务授权范围及总预算内修正确性，不修改机制超参数。

## 3. G1a：把单入口的池、短名单与排序损失拆开

对D1前128条query、每个L，对当前全池H和限定扩展池X128中的每个入口独立运行同kernel。X仅作范围有限的诊断：从独立QGT5K既有GT10中排除H，以出现频次降序/ID升序取64；从剩余不同ID按`SHA256("entry_pool_v1|"+decimal_base_id)`升序取64。不足128则用全部并记录数量，不更换规则。不能用pilot/validation目标来选X，不生成新GT。

设`M(P)=max_{e∈P}R(q,{e},L)`，同Recall时最小graph NDC，再按ID。用同批单入口结果报告：

| 量 | 精确定义与限制 |
| --- | --- |
| 有限池增量 | `M(H∪X)−M(H)`；只是这128额外候选带来的oracle增量，不是原池对全base的损失，更不是同hub预算部署收益 |
| 短名单损失 | `M(H)−M(C8)`；同一H内的几何画像/近似短名单遗漏合计 |
| 排序损失 | `M(C8)−R(q,{a},L)`；单入口任务中的选错，不与Fast3直接相减解释 |
| 精确几何截断 | 额外只计算全部prototype分数得exact C8；`M(H)−M(exact C8)`非负 |
| ANN shortlist替换影响 | `M(exact C8)−M(approx C8)`可正可负，两个C8不一定包含；另报top8集合recall及anchor一致率 |

前三项逐query相加恰等于`M(H∪X)−R(q,{a},L)`，只在这个**单入口、同L**定义下成立。不能把它们加到Fast3收益上。报告均值、分位数、胜/平/负比例和paired区间；本阶段不学习pool、不重建router，也不因X获益自动推进A。

免费oracle的所有遍历成本进入离线诊断成本；任何oracle Recall–NDC图标为`selection_cost_excluded / not_deployable`，不进入部署QPS前沿。

## 4. G1b：真实组合还有没有剩余空间

对D1全部512条、两个L：

- C8中8个single。
- 包含a的29个一至三入口集合：`1+7+C(7,2)=29`。
- 合并重复的`{a}`后，每query/L共**36个不同搜索动作**。每个动作独立reset后真实联合搜索；不是single结果并集。
- D1前64条另枚举C8中所有一至三入口子集，`8+28+56=92`；前述36包含其中，额外只需56个。仅作预定anchor限制诊断，不进入模型动作空间。

主比较固定三入口，全部对照都含a、候选都在C8。免费21动作oracle按**最高真实Recall**、再最小graph NDC、再ID选择；不能改成argmax U后仍宣称Recall支配。单列argmax U和NDC成本分布，但不混为主oracle。

必须真实重放的代理（均已在21动作结果中，不需再搜）：

1. Fast3与固定Fast1/2。
2. 以single的`R−0.05D/max(D_F,1)`给另外7个入口排序，保留a加前两名。
3. 从single `{a}`命中mask开始，按single命中并集的边际收益贪心加两名；tie按single NDC/ID。该策略只是GT oracle代理，union覆盖值和真实重放值分列。

G1主余量是`R(best_real_triple)−max(R(Fast3),R(single_rank_triple),R(union_proxy_triple))`，max也在每query计算，因这些动作在同一家族中所以非负。四个dataset×L点均要求平均≥**0.5pp**，10,000次按query ID配对bootstrap、4项Bonferroni校正区间下端>0；同时报告普通95%区间。它是有限家族可研究空间筛查，不能声称真实方法显著改善。

均值不足：`NOPASS_NO_MATERIAL_JOINT_HEADROOM`；均值达到而校正区间不支持：`INCONCLUSIVE`。两者均停止，不扩大C8或追加query。没有硬性equal-NDC gate；graph成本若明显上涨如实报告，后续模型/纯wall仍可能被否决。这里的质量oracle不是成本最优oracle。

无anchor92、29可变m、21固定m之间的差值单列。若空间主要来自去anchor或少选入口，解释为当前主假设不受支持；不在本版本切换动作家族。

## 5. G2：一次小模型可预测性检查

仅G0/G1均通过才生成fit2048的36动作×2L标签；D2另512也生成同36动作×2L。D2与D1不重合；D2不是新鲜测试集，但没有参与本版本oracle gate或拟合。主模型只使用fit内21个三入口动作训练，single标签提供必要对照。

目标和固定模型：

`y(q,S,L)=R(q,S,L)−R(q,F3,L)−0.05·(D_G(q,S,L)−D_G(q,F3,L))/max(D_G(q,F3,L),1)`。

`x(q,S,L)=φ(q,S,L)−φ(q,F3,L)`；无截距ridge，目标为`mean((wᵀx−y)²)+1e−3||w||²`。列缩放只用fit的RMS（小于1e−8置1），不做均值平移，确保Fast3特征严格全零。每个query/L在损失中等权；每数据集一套系数，两L共享。所有主超参数两数据集相同，不做early-stop/模型挑选。

特征表必须按以下顺序冻结，而不是运行后补到“最多48维”。记`q̂=q/max(||q||,1e−12)`，`s_e=q̂·p_e`、`t_e=q̂·h_e`、`n_e=log(1+||h_e||)`，`P_ij=cos(p_i,p_j)`、`H_ij=cos(h_i,h_j)`，`S={a,b,c}`。

| 特征块 | 明确内容 |
| --- | --- |
| 每个补入口12维f(e) | `[s_e,t_e,n_e,s_e²,t_e²,s_e*t_e,s_e*n_e,t_e*n_e,P_ae,H_ae,s_e*P_ae,t_e*H_ae]` |
| 可加12维 | `f(b)+f(c)` |
| 补入口交互8维 | `[P_bc,H_bc,s_b*s_c,t_b*t_c,s_b*t_c+s_c*t_b,P_bc*(s_b+s_c),H_bc*(t_b+t_c),(s_b−s_a)*(s_c−s_a)]` |
| L条件 | 将上述20维与其乘`log2(L/64)`的20维拼接，共40维 |

s/t在特征阶段显式重新计算，不假定复用HNSW的距离；8个prototype加8个raw点积共16次计入routing NDC和wall。P/H表只来自已冻结向量，零范数按固定epsilon处理并计数；主实验原始base与搜索query不归一化。上述特征只是明确、廉价的交互假设，没有声称SOAR理论或图可达性保证。

四个固定模型（不是超参数扫描）：

- **C**：40维、真实triple标签。
- **B-single**：每query/L使用C8全部8个single，f(e)及L交互共24维；其训练输入是未差分的f(e)，RMS也由这些fit single特征计算，无截距、同正则，以绝对single `R−0.05D/max(D_F,1)`作目标。训练不套用C的差分x/y；只在推断时对两个补入口分数相加、减去本模型的Fast3补入口分数以回退。相同fit/候选，不用旧10K权重。
- **B-triple-additive**：24维可加块，训练于相同真实triple标签。区分换标签和成对特征；只在D2缓存结果中评估，不追加G3曲线。
- **置换负控制**：将fit query按固定哈希整体循环移位1位，按候选rank编码的整套21动作标签向量连同两个L一起移位，训练同40维模型。一次固定置换只是检查，不作为正式随机置换p值，也不挑种子。

主部署规则：21动作都算预测分，Fast3分数固定0；只有严格正分才替换，同分优先Fast3，再按补入口ID词典序。模型输出经同一wrapper进入原kernel。真实在线绝不运行Fast来取得D_F；D_F仅用于离线标签和评分。B-single的选择分数也以自身Fast3分数为基准回退。

G2主族为`2 datasets × 2 L × 3 contrasts`：C对Fast3、B-single、B-triple-additive，共12项。每项平均Recall提升≥**0.3pp**且10,000次query-paired bootstrap的Bonferroni校正区间下端>0。按这个严格门槛失败只否决/不能确认这个40维有限家族，不证明联合收益数学上不可预测。对置换控制只作描述性检查；若效果相当，不能声称学到了query特定交互。记录预测动作、误换比例、rescued/newly_harmed、固定m收益以及target/pair支持度。

oracle余量恢复比例`(R_C−R_F3)/(R_oracle3−R_F3)`仅作描述；分母≤0写null，不拿不稳定比值作GO标准。主模型与全部对照的标签/拟合耗时和参数字节均计入，不能只报最后一次成功fit。G2不通过就停止，不增加特征、标签量、正则、网络或在线trace。

## 6. 新接口与命令草案

下列API不存在于当前方法源码；参数契约须在新执行版本实现。不能把当前`bench_entry_oracle --extra_routes`的graph-only结果当完整在线输出。

```text
route_plain(raw_query, frozen_router, entry_model, L, route_workspace)
  -> ordered_unique_base_ids[3], route_provenance
search_plain(raw_query, frozen_NSG, ids, L, search_workspace)
  -> result_ids[10], raw_distances[10]
search_count(...same arguments...)
  -> same results + graph_ndc
enumerate_actions(query_ids, allowed_train_or_pilot_slice, fixed_actions)
  -> search results; GT is joined afterward in evaluator only
measure_batch(method, raw_queries, L, threads, output_buffer)
  -> full wall_seconds; no GT argument
```

命令草案，**全部未实现、未执行**；`NEW_EXECUTION`必须是此前不存在的路径，每stage独占输出、验证上游gate。不能用本文件触发旧`run_target_basin_protocol.py`或夜间`stage_run.py`。

```bash
# DRAFT ONLY: 新执行任务中实现后先检查 --help；不是当前可运行命令。
python3 NEW_EXECUTION/tools/entry_joint_gate.py --help
python3 NEW_EXECUTION/tools/entry_joint_gate.py --protocol NEW_EXECUTION/protocol.json --stage g0_contract --output NEW_EXECUTION/g0
python3 NEW_EXECUTION/tools/entry_joint_gate.py --protocol NEW_EXECUTION/protocol.json --stage g1_decompose --split pilot_d1 --output NEW_EXECUTION/g1
python3 NEW_EXECUTION/tools/entry_joint_gate.py --protocol NEW_EXECUTION/protocol.json --stage g2_fit_audit --fit-split fit2048 --audit-split pilot_d2 --output NEW_EXECUTION/g2
python3 NEW_EXECUTION/tools/entry_joint_gate.py --protocol NEW_EXECUTION/protocol.json --stage g3_count --split pilot10k --output NEW_EXECUTION/g3_count
python3 NEW_EXECUTION/tools/entry_joint_gate.py --protocol NEW_EXECUTION/protocol.json --stage g3_wall --split pilot10k --output NEW_EXECUTION/g3_wall
python3 NEW_EXECUTION/tools/entry_joint_gate.py --protocol NEW_EXECUTION/protocol.json --stage report --output NEW_EXECUTION/report
```

runner必须拒绝raw validation/held-out、重叠输出、G1/G2 gate缺失或失败、未绑定源码/图/模型、未知method/L、追加point和累计资源超限。report只消费已保存产物；不能隐式补搜。现有代码的`--help`本轮没有调用，因为并未复用可运行实验命令。

## 7. G3：只测固定的完整成本曲线

仅G2通过进入。CPU16线程、每次一个数据集一个进程；模型与原始图常驻内存。主要3方法`Fast3 / B-single / C`各L={48,64,96,128}，12点；另`Fast1 / Fast2`各L={64,128}，4点；共**16点/数据集**。L48/96的模型使用预定L特征，不追加训练标签；预算迁移可能失败，照实报告。

同一16点每点1次独立count、5次整批plain wall，10K历史pilot。QPS点估计固定为`10000/mean(五轮wall_seconds)`，bootstrap也使用同一估计器，不能改成五个QPS的平均。每点固定一次512-query warm-up；方法顺序按协议哈希排列形成五轮交错顺序，同一round绑定对应Fast锚点。每个plain invocation只计一个方法、整批归一化到输出写入；GT评分在外。不得把五轮当五个Recall样本。routing-only wall可另做有界诊断，但不相加替代端到端wall，额外调用计入资源余量。

主成本匹配：Fast3的L64/L128为两个预定锚点。C只有四个实测L。C/Fast的QPS比点估计及其下述同时区间必须全部落在`[1.00,1.03]`，才算可行；在可行C点中取最高Recall，tie按更高QPS、再较小L。称“最多3%差异的近似QPS匹配”，不是严格等时间。没有可行点则INCONCLUSIVE，禁止插值、补点或改容差。

C选点后，从B-single四个实测点选出`QPS_C/QPS_B`点估计及同时区间也全部在`[1.00,1.03]`的对照，再取其中最高Recall；无B匹配则交互部署增量INCONCLUSIVE，不另换一个有利C点。这样B在容差内可使用至少与C一样多的时间，不能用明显更快而Recall不足的B来证明交互收益。

为避免先在四个L中选优、再仅给四个区间造成选择偏差，**先对全部固定候选比较建立同时区间，再选点**。统计向量固定为：16个C-L对Fast-anchor的Recall差、16个对应log(QPS比)，以及32个C-L对B-L的Recall差、32个对应log(QPS比)，共96项（均含两数据集）。相同C/B比较不因两个Fast锚点重复计数。

所有G1/G2/G3的bootstrap各用独立PCG64种子202609081/202609082/202609083，10,000重复；两数据集分开抽query但同dataset的method/L共享query重采样。分位采用排序后位置`(B−1)p`的相邻点线性插值；标准差用ddof=1，执行manifest锁定numpy版本。G3用10,000次配对bootstrap：query ID共同重采样Recall，五个配对timing rounds共同重采样batch wall，保持method/L的round关联。对96维bootstrap误差按各自bootstrap标准差标准化，取每次最大绝对误差的95%分位作为共同临界值，形成max-standardized同时区间；log-QPS区间再指数变换。标准差为0且所有重采样误差为0则该项取点区间，否则标数值INVALID。保存全部原始对比、尺度和临界值。这是有限重复下的bootstrap近似，不宣称有限样本精确覆盖；小样本/计时不稳定即INCONCLUSIVE，不用选择后的朴素CI作GO。

另在各bootstrap重复内按点估计重新匹配/选点，记录C/Fast及C/B联合匹配成功率，需≥99.5%；无匹配重复保留为UNMATCHED，不删除或用于条件均值冒充主结果。该稳定性诊断不替代上述固定96项同时区间，也不再把缺失比较写成伪造Recall。整批wall重采样没有假装知道重采样query组合的逐query纯wall，相关限制须报告。

四个dataset×anchor都必须满足：C对Fast3平均Recall≥**+0.5pp**，对已匹配B-single≥**+0.3pp**，两项对应同时区间下端均>0。另若任何已测Fast1/2或B-single点在点估计上同时Recall≥C、QPS≥C（至少一项严格），保守地不推进；这条否决规则不声称统计学支配。固定m控制只覆盖已测点；G3没有测B-triple-additive的wall，故不能宣称胜过全部可加方法。正式阶段必须补齐两种可加模型及Fast1/2/3的完整曲线。

通过仅为`PILOT_COST_SIGNAL`，不叫正式性能GO。NDC解释工作量，不作替代wall的hard gate；汇报routing/graph/total及选择开销。G2同L胜可加模型不能替代本节同成本增量检查。

## 8. 搜索次数、时间与存储的硬边界

下表按X128、H815/821计算上界；缓存同query/L/route的结果必须匹配完整模型/输入身份，不能只按短文件名复用。

| 工作 | 完整搜索调用数（双数据集合计） |
| --- | ---: |
| G1a：128query×(H+128)×2L | 484,352 |
| G1b：D1 512×36×2L×2datasets | 73,728 |
| anchor诊断：64×额外56×2L×2datasets | 14,336 |
| G2 fit：2048×36×2L×2datasets | 294,912 |
| G2独立D2：512×36×2L×2datasets | 73,728 |
| G3：16点×10K×2datasets×(1count+5wall) | 1,920,000 |
| 小计（允许缓存后实际数更少） | **2,861,056** |
| parity/plain复核、warm-up、尾延迟等共用余量 | **138,944** |
| 总硬上限 | **3,000,000** |

G3一次512-query warm-up全部点共16,384调用，从余量扣除。没有把独立count漏算，也不把proxy的缓存查表计为新搜索。可在余量内给64fit样本做count/plain、512固定pilot做1-thread p50/p95/p99；后者是开发诊断，不能替代正式tail统计。任何额外一次kernel调用均登记，超过总量停止，不靠多进程绕过。

仅一个重数据集进程；最多16 CPU线程，不启用GPU，不混RoarGraph的MKL/OpenMP环境。新产物≤8GiB，`/data`始终保留≥10GiB，RSS上限80GiB；不复制base/GT/图、不清缓存、不删除旧文件。总研究执行wall上限4小时（包含数据加载/标签/拟合/计时/分析），G0+G1累计上限2小时。上限是停止条件，不是完成耗时预测；首次重阶段观察约一分钟，依真实吞吐报告ETA，预计超限则停止为INCONCLUSIVE。断点只续同协议尚未完成的固定工作，不加比较点。

## 9. Artifact schema与成本台账

建议紧凑数组+JSON元数据，禁止pickle；已有numpy可用，不为格式安装依赖。每个结果必须按原query ID对齐，不能用排序后的Recall数组算paired收益。

| artifact | 必要字段 |
| --- | --- |
| `protocol.json` | version/status=DRAFT或FROZEN、scope、datasets、allowed_ranges、sample_algorithm、all_method_L_points、seeds、G0–G3 gates、bootstrap/matching、budgets、implementation_review |
| `manifest.json` | dataset/artifact/metric/normalization；base/graph/query/GT及router/model的路径+SHA；train/pilot使用范围及历史使用；source/binary/compiler版本、CPU/threads/cache；禁止输入列表 |
| `sample_ids.json` | 原始行ID；fit与pilot互斥、D1/D2互斥，pool128/anchor64为D1嵌套子集校验；SHA，不含原始query/GT |
| `actions.json` | family、candidate_local→base ID映射、anchor、requested/consumed IDs顺序、m、去重、tie、L、is_oracle、GT_use_role |
| `labels.*` | query_id/L/action_id、真实returned IDs、Recall10、graph NDC、single hitmask（仅GT事后诊断）、F3参照；输入/kernel SHA、valid/completion，在线禁止读取 |
| `model.*` | 明确40/24维feature顺序、RMS、coefficients、regularization、fit IDs SHA、target公式、fallback、L条件；不保存可在线查GT的映射 |
| `audit_predictions.*` | D2每query预测分、选择动作、actual consumed IDs、真实收益/误换、各控制；标明开发性质 |
| `count.*` | aligned result IDs、routing/graph/total NDC、dot/MAC/lookup数量；`qps=null`、独立plain parity |
| `timing.*` | method/L/round/order、batch_n、threads、warm-up、wall seconds、QPS、result hash、timing exclusions、plain状态；非纯timer标INVALID |
| `costs.json` | exactGT、QGT、prototype、router-index、pair-table、每类labels、所有model-fit、IO/analysis、公共NSG；wall/CPU/RSS/bytes、复用项null+reason、研究成本与部署增量成本分开 |
| `gate_g*.json` | 比较族、means/普通与校正CI、匹配率/无匹配处理、status/reason、证据SHA、未运行阶段及触发条件 |
| `state.json` | stage、completed/not_run、active_job身份/日志/ETA、累计kernel_calls/wall/bytes、停止原因、next_action；不修改旧state |

`T_offline=exactGT+QGT+prototype+router-index+labels+pair-table+fit`；公共图构建另列，整系统成本加回。冷/热cache与复用exactGT分开；历史GT耗时未知就null，不能写0。只有同Recall实际每query摊销wall节省δt>0时才计算`break_even_queries=额外离线秒/δt`，注明它是固定线程吞吐摊销而非单query延迟；δt≤0或成本未知则不可计算。

## 10. 通过与停止之后

| 结果 | 确定动作 |
| --- | --- |
| G0 INVALID | 先解决可比性；不作方法结论、不继续效用标签 |
| G1空间不足或空间主要来自另一个动作家族 | 停止当前C8/anchor/m3组合；报告池/短名单/anchor定位，不自动启动A/B |
| G2不可预测或只有可加模型同样好 | 停止40维组合假设；不加模型/特征/trace/view |
| G3成本不支持 | NOPASS，或无匹配/测量不足为INCONCLUSIVE；不补L/阈值 |
| 任一资源上限触发 | INCONCLUSIVE_RESOURCE_LIMIT，保留部分产物及NOT_RUN标记 |
| G3通过 | 只提交下一份正式协议，不借旧夜间授权自动执行validation/held-out |

正式协议的必需后续不能省略：同20K的三独立build seeds；Fast1/2/3的完整曲线、相同C8的B-single和B-triple-additive完整成本对照及受约束GATE/PSP候选对照；原方法与CPU/raw-IP/20K适配的差别单列，适配未完成时不能宣称强基线已过。另列优化充分的完整系统（如PyANNS、RoarGraph）及其不同图/硬件成本，不能用论文QPS当本地结果。两数据集至少两个相邻工作点同Recall QPS≥+10%或同QPS Recall@10≥+1pp、校正区间支持，尾部/退化分析与完整离线成本齐备，冻结后held-out 10K×3才可确认结论。历史pilot、已用validation和held-out的既往使用全部披露，不用新测试结果回调方法。
