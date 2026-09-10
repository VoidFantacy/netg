# 08｜Fast入口选择根因诊断：全H真实效用、组合与局部迁移

2026-09-08实际实验，版本[`fast_router_diagnosis/20260908_v1`](../fast_router_diagnosis/20260908_v1)。最终状态[`COMPLETE_FAST_ROUTER_DIAGNOSIS`](../fast_router_diagnosis/20260908_v1/state.json)。**已检查的输入/画像/搜索执行未发现错误；Fast几何代理与有限搜索效用不一致，ANN近似不是主要缺口。简单query近邻迁移没有稳定优势，不能推论一般不可学习。** 固定anchor、固定3入口和C8充分覆盖三个预设因此撤下；没有训练新selector，也没有新方法GO或端到端QPS收益。

本卡直接读[冻结协议](../fast_router_diagnosis/20260908_v1/protocol.md)、state、正式analysis/v2、costs_v2和输入/执行/统计/最终审查，交叉核对[原报告](../fast_router_diagnosis/20260908_v1/report.md)。仅归档既有证据，不重新访问原始query/GT、运行ANN或重新统计。当前行动以[项目入口](../AGENTS.md)及[当前方案](../s-target.md)为准。

## 为什么做，以及“最好入口”的精确定义

此前免费入口oracle明显高于Fast，但差距混有旧30K画像、validation和入口数量变化，不能直接归因于路由。v2曾拟议固定Fast rank0、从C8补到3入口；本轮经用户明确授权实际诊断，先检验这些前提，不自动训练v2组合模型、不恢复区域/Multi-view等旧分支。

对固定query、现有H个真实hub、原kernel、指定L和Recall@10，记`R*(q)=max_h R(q,h)`，A0保留所有同分最高入口；A1允许少一个GT10命中，即每query少0.1 Recall，并非很小的误差门槛。H-single、Fast C8 single、exact C8 single、C8 pair/triple各有不同动作集合，不能互相当全局上界。oracle事后查看目标标签，选择免费，不是可部署路由，也不是全base或全H组合最优。

## 冻结数据、公式、动作与统计

| 项目 | 实际值与限制 |
|---|---|
| 数据/图/距离 | WebVid-2.5M与Yandex official10M，原raw-IP、原冻结NSG；原query直接用于HNSW、exact画像评分和NSG |
| hubs | 独立QGT5K已有真实hubs，WebVid815/Yandex821；不重选hub或生成新exactGT |
| paired画像 | router_train后20K `[10000,30000)`；同夜间paired Fast20K构建，不能混算旧30K结果 |
| 主pilot | 前10K历史开发池按协议SHA排序取512条/数据集，不是新鲜测试集 |
| 密度控制 | 主pilot前128条各取后20K的cosine最近query；只按query选源，不看效用标签；另取排除最近源后的128条固定SHA随机源 |
| 总行数 | 最近源去重后WebVid767、Yandex768；前512行为pilot，其余为fit辅助行 |
| routing | M16/efConstruction200/ef10，主seed20260828，保存旧seed100对照；无HNSW扫参 |
| 原搜索 | `ACSG::search_new(mode=2)`，K10、L64/128；本轮所有动作均1–3个真实入口，按所给顺序消费；L是pool容量而非固定NDC |
| 枚举 | 每行×全H single；pilot另跑实际Fast C8全部28 pair/56 triple及Fast/exact1/2/3、seed100固定对照，91个命名列 |
| 资源 | 单重子进程、16 OpenMP线程、BLAS1线程；≤300万搜索、RSS80GiB、新产物2GiB、磁盘余量10GiB、真实搜索总wall≤4h |
| 统计 | 八种预注册对比×两数据集×两L=32项；七类用512配对query，最近−随机用128；bootstrap10,000次、PCG64 seed20260908 |

**画像公式经过最终审查纠正。** 先用GT1向量与单位raw hub的cosine得到basin；对该hub的单位query**求和**，加单位raw-hub prior（权重1），再整体归一化。不是先平均query再加同权prior。单位化仅用于几何basin、邻近query和画像复算；不把base/raw-IP搜索改成cosine。这个监督没有直接询问从该入口在当前L能召回多少GT10。

本轮原始validation/held-out文件均未打开，GT仅复用训练侧；与[07夜间P0读取validation作完整性检查](07_hierarchical_p2_p3.md)不同。512 pilot曾有历史开发使用，排除其中部分也不能把剩余前10K称新鲜测试集。

普通CI取0.025/0.975分位，Bonferroni32取0.05/(2×32)及补数；同数据集的512行主族共享跨L重采样索引，128行族另组。是固定图/画像/fit语料与历史pilot条件下的percentile-bootstrap近似，不是严格有限样本保证或跨build不确定性；10,000抽样下全族极尾端点约仅8个尾部重复支撑，近0端点不应当决定性证据。全部32项见[正式统计表](../fast_router_diagnosis/20260908_v1/analysis/v2/analysis.md)，不得只报告有利点。

## 实际执行与输入/结果验收

四个串行job均退出0：WebVid parity 43,392次、main1,336,510次；Yandex parity43,680次、main1,347,188次，共**2,770,770**搜索，其中87,072次验收。原输入/库/二进制保持身份，新增runner/输入副本/输出隔离在本版本；四任务无重叠，没有新路由模型拟合。

两数据集base/图/训练输入全SHA、hub真实base字节与ID、同20K画像完整复算均通过，prototype逐字节一致。原builder辅助元数据`requires_aco_dpc=true`没有导致本轮读ACO/DPC；旧源码注释“前1/3或前5个”与实际常量3不一致，以真实执行为准，有效输入未进入随机fallback。

专用parity用local rows `[512,520)`的8条辅助fit query，分别检查14,464/14,560配置：全H singleton和89个多入口列、count/plain返回ID/距离、count repeat NDC及route前缀均一致。不是在全部512 pilot重跑parity；main目录的parity状态NOT_RUN是控制器依赖专用parity已PASS后的设计，非漏验收。count包装还核对首次距离求值按顺序触达全部供给入口，确认有效1/2/3入口合同；不证明任意kernel里顺序无关。

独立执行审计核对全部exact排序是合法H排列、同分按真实ID，approx距离等于同ID exact距离；重建全部512 pilot动作列与padding，验证28/56组合完整、hitmask低10bit/popcount、single与缓存重复列一致。确定性抽样重新评分返回ID，跨边界覆盖allH与pilot列；另每数据集236个top10按小范围raw-IP读数核对，无float64逆序。部分结果检查是独立重评分，不是新独立搜索样本。GT不进入`Work::run`，评分在搜索之后。

审计当时33个执行冻结文件、14个build文件与94个保护旧文件大小/SHA全部一致。runner SHA `968796a903bd562a2b4231a1b92a90bb35528f5dc932de37c1361f7f9f8c9c28`，独立二进制SHA `c2948518b715aa66d28cede1aec126fef197b513dc555d0f42ff6e14d826287f`；它们是本轮原记录身份，不声称今天又重新hash了所有大图/base。[输入审计](../fast_router_diagnosis/20260908_v1/reviews/input_source_audit.md)、[输入准备审查](../fast_router_diagnosis/20260908_v1/reviews/protocol_input_preparation_review.md)、[执行审计](../fast_router_diagnosis/20260908_v1/reviews/independent_execution_audit.md)。

## 六个问题的实测答案

### 1. 是实现错误或HNSW近似吗

检查范围内未发现错位/执行缺陷，不等于全算法无缺陷证明。Approx/exact top1一致率WebVid93.36%、Yandex96.88%；更换成相同距离函数的exact画像检索后：

| 数据/L | exact3−Fast3 (pp) | Bonferroni32 95%CI (pp) |
|---|---:|---|
| WebVid64 | +0.352 | [−0.590,+1.328] |
| WebVid128 | +0.625 | [+0.020,+1.687] |
| Yandex64 | −0.449 | [−1.484,0.000] |
| Yandex128 | −0.312 | [−1.328,+0.078] |

改善小且方向不一致，不能解释exact1之后5.9–14.2 pp缺口。WebVid128的近0正下界保留但不能推成跨数据稳定GO；exact分数更准确也可能使搜索Recall下降。CI含0不证明两者等效，seed100对照未推翻当前解释。

### 2. 真实GT1 basin标签能代表好入口吗

下表全部是相同single动作数，Recall为%；GT1 basin由该目标query GT1提供，属于离线oracle。

| 数据/L | Fast1 | exact1 | GT1 basin入口 | 全H最佳single |
|---|---:|---:|---:|---:|
| WebVid64 | 66.00 | 66.54 | 67.64 | 80.70 |
| WebVid128 | 73.87 | 74.49 | 75.61 | 85.96 |
| Yandex64 | 82.85 | 82.48 | 85.74 | 93.50 |
| Yandex128 | 91.00 | 90.64 | 91.76 | 96.56 |

即使给出正确几何basin，仍差13.07/10.35 pp和7.75/4.80 pp。因此只把现有basin分类准确不能保证找到真正好入口。Fast1恢复basin率20.12%/30.27%，不能直接解释为搜索准确率。严格分解`R*−R(Fast1)=[R*−R(basin)]+[R(basin)−R(Fast1)]`的后项可负，不是两个非负分类错误，也不能转成因果占比。

每query全H画像分数与single Recall的Spearman均值约0.011–0.024（去除常数效用行，ties平均秩），说明全局排序代理弱；仍不否认其短名单筛选价值。单均值、多模态、prior、训练密度尚未分别做因果干预，不能将全部缺口归因于某一项。

### 3. C8内还是C8外损失

| 数据/L | Fast C8最佳single(%) | exact C8最佳single(%) | 全H−exact C8(pp) |
|---|---:|---:|---:|
| WebVid64 | 73.44 | 74.04 | 6.66 |
| WebVid128 | 79.59 | 80.20 | 5.76 |
| Yandex64 | 88.55 | 88.55 | 4.94 |
| Yandex128 | 93.42 | 93.40 | 3.16 |

四项全族CI均正；Fast C8包含任一A0的query比例WebVid49.02%/56.05%、Yandex64.06%/76.17%。所以短名单内选错和短名单外漏失并存，完美C8重排也不足以取回全H机会。exact32/64的免费覆盖更好，但无部署成本证据；全base入口未测，亦未证明重选hub池必要。

### 4. 固定anchor或三入口安全吗

| 数据/L | Fast3(%) | C8最佳single(%) | C8最佳triple(%) | 含anchor最佳triple(%) |
|---|---:|---:|---:|---:|
| WebVid64 | 65.80 | 73.44 | 72.50 | 69.39 |
| WebVid128 | 73.83 | 79.59 | 79.02 | 76.50 |
| Yandex64 | 83.40 | 88.55 | 87.91 | 85.25 |
| Yandex128 | 90.76 | 93.42 | 93.13 | 92.29 |

强制rank0 anchor损失3.105/2.520 pp和2.656/0.840 pp，四项全族CI严格正。最佳triple均值比C8最佳single差0.29–0.94 pp；WebVid仅4/512、2/512 query的triple更好，Yandex两点0/512，相等分别486/491及490/506。后者是描述性补充，不在32主族；足以撤掉默认固定3的前提，不能证明single部署最优，因oracle/同L都不等于同成本。

### 5. 独立single命中并集能替代联合搜索吗

每query对56个triple平均，真实联合搜索比独立single命中并集少WebVid0.741/0.533个GT10、Yandex0.433/0.227个；本样本没有并集之外新命中。按独立并集挑triple再真实跑，WebVid仅66.29%/74.08%，低于真实triple oracle72.50%/79.02%。共享pool/visited/展开顺序改变探索，不能相加独立搜索标签充当实际组合监督；并集包含实际输出只是本样本现象，不是任意图/query定理，独立搜索成本也不同。

### 6. 最优入口“不可预测”成立吗

A0中位规模WebVid50.5/61.5，Yandex205.5/821。Yandex128有266/512=51.95% query全部hub Recall=1；也有全部同分但未满Recall的query。均匀随机hub落入A0/A1的概率不等于期望Recall或任意GT命中率。任意唯一标签准确率会混淆巨大ties平台。

跨L的A0有共同入口的query占92.19%/96.09%；按源L最高Recall、最低源NDC、真实ID确定一个代表后迁往另一L，平均regret1.25–4.55 pp。唯一代表变化也可来自ties内NDC次序变化，不表示完全没有跨L稳定好入口。

128条近邻控制中，最近源平均cosine0.750/0.697，随机源0.424/0.166，确实更近；但将源A0中按源NDC/ID选的代表直接迁给目标：

| 数据/L | 最近fit−随机fit(pp) | Bonferroni32 95%CI(pp) |
|---|---:|---|
| WebVid64 | +1.562 | [−6.187,+8.672] |
| WebVid128 | +3.594 | [−1.983,+10.093] |
| Yandex64 | −1.016 | [−6.983,+3.921] |
| Yandex128 | −0.547 | [−6.499,+5.015] |

四项均跨0。改成源A0全部入口在目标上的平均收益，最近源仍未胜随机源；在目标上挑源A0最佳则再使用目标标签，仍是oracle。最近query对的GT10平均交集仅0.969/0.250；GT交集与相似度分层只用于描述，不能当线上已知特征或新的独立检验。结论仅是当前query几何、20K密度、当前图/H/L下局部迁移弱，不是信息论下界、NP-hard、不可约误差估计或所有模型/新表示无效。

## 正式分析与成本版本纠正

**正式数值只用analysis/v2。** v1的nearest−random NDC存在uint32减法问题，exact C8 oracle NDC不完整；v2转为有符号差并补齐。全部Recall、32主对比与图保持一致，没有重跑搜索或改参数。A1用有符号int16处理最高命中为0的情况；source代表绝不查看target NDC/效用，target-best单列oracle。[独立统计复核](../fast_router_diagnosis/20260908_v1/reviews/independent_analysis_review.md)。

**正式成本只用costs_v2。** `stage=route`是HNSW构建/路由之前的开始事件。4.183603446/11.03554108秒只是到路由开始前的输入/索引加载累计时间，不是路由联合耗时。HNSW与route没有可用联合或单独结束计时，三字段均null+reason，不能填0或倒推免费路由。costs_v1的误读原件保留；修正没有改变Recall或进程总wall。[成本v2](../fast_router_diagnosis/20260908_v1/results/costs_v2.json)、[最终报告复核](../fast_router_diagnosis/20260908_v1/reviews/final_report_review.md)。

| 诊断成本 | WebVid | Yandex |
|---|---:|---:|
| prepared_v2输入核验/画像复算/选择/I/O wall(s) | 8.12098 | 12.65181 |
| 其中prototype复算(s) | 0.161877 | 0.059019 |
| L64全H instrumented wall(s) | 16.45625 | 16.15499 |
| L128全H instrumented wall(s) | 30.13806 | 28.47178 |
| L64 pilot组合instrumented wall(s) | 0.92658 | 0.83204 |
| L128 pilot组合instrumented wall(s) | 1.88645 | 1.65047 |

四子进程wall合计150.556614515秒，控制器跨度150.676378459秒；峰值观测RSS10,746,122,240 bytes=10.008106 GiB。prepared_v1另21.12030秒保留，正式analysis/v2约3.07302秒，v1约3.08秒；编写、审查、文档时间不混入这些程序秒数。输入hash先预热文件，无cold-cache控制；这些instrumented秒数含加载/计数/评分/I/O的相应阶段，不能换算部署QPS或完整训练时长。原exactGT、QGT hubs和NSG构建历史时间未核实，均null。当前预算/ETA不能从这些小pilot时间无条件外推。

控制器300万次检查在每job结束后发生，固定形状事前界和本次总数都符合预算；不是任意大job内实时强制调用上限。历史controller还有固定日志名限制，复现必须为结果、日志和准备输入另建版本，不能仅换一个输出flag覆盖原证据。[复现说明](../fast_router_diagnosis/20260908_v1/README.md)。

## 结论、不可恢复范围与精确证据索引

这一诊断定位到“几何标签/评分与真实有限搜索效用错位”和“候选内外损失并存”，没有证明新效用策略可泛化。存在图路径、hub近GT1与有限L找回GT10是不同条件；raw-IP不能直接套度量空间图保证，路径依赖也不意味着随机标签。[理论和定义审查](../fast_router_diagnosis/20260908_v1/reviews/theory_and_diagnostic_definitions.md)。

后续研究可以讨论新的真实效用表示，但必须区别于旧static utility ranker并另冻结协议。不能把C8组合器换名后自动训练、重新强制anchor/三入口、扩HNSW参数、恢复局部近邻记忆，或用此oracle为probe-reroute/区域法解禁。固定H有空间并不证明必须发现H外入口；单入口是最小证伪动作，不是部署最优定理。质量信号成立后仍需完整路由+图wall、双数据集、强基线、相邻点、三独立构建、tail及方法冻结后的held-out10K×3。

| 要核查什么 | 原始证据 |
|---|---|
| 预注册样本/动作/统计/预算 | [protocol.md](../fast_router_diagnosis/20260908_v1/protocol.md) |
| 最终状态/无待续模型 | [state.json](../fast_router_diagnosis/20260908_v1/state.json) |
| 准备行ID、input SHA、样本选择 | [prepared_v2目录](../fast_router_diagnosis/20260908_v1/inputs/prepared_v2)的每数据集runner_config/sample_manifest |
| 完整执行与停止 | [jobs.json](../fast_router_diagnosis/20260908_v1/results/run_v1/jobs.json)、[completion.json](../fast_router_diagnosis/20260908_v1/results/run_v1/completion.json)、[最终保护资源](../fast_router_diagnosis/20260908_v1/reviews/final_integrity_resources_v1.json) |
| 32统计族、ties/coverage/组合/迁移分层 | [analysis/v2/analysis.md](../fast_router_diagnosis/20260908_v1/analysis/v2/analysis.md)、[analysis.json](../fast_router_diagnosis/20260908_v1/analysis/v2/analysis.json) |
| 逐query及来源映射 | [per_query.csv](../fast_router_diagnosis/20260908_v1/analysis/v2/per_query.csv)、[neighbor_transfer.csv](../fast_router_diagnosis/20260908_v1/analysis/v2/neighbor_transfer.csv) |
| 原返回ID/命中/计数矩阵 | [run_v1/main](../fast_router_diagnosis/20260908_v1/results/run_v1/main)，按数据集/L分目录，必须与prepared_v2和记录SHA绑定 |
| 成本缺失和修正 | [costs_v2.json](../fast_router_diagnosis/20260908_v1/results/costs_v2.json)；v1仅保留历史身份 |

原报告和state中的“下一研究”是诊断完成时的历史建议，随后已有v4/v5设计调研，当前优先级由主文档决定。所有原矩阵、失败解释、修正前版本和日志保留；本卡新增不会触发任何数据重跑。
