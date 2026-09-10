# 07｜目标区域与受保护候选池：P2/P3完整负结果

本卡归档 `hierarchical_target_search/20260907_v1` 于2026-09-07夜间至09-08 07:00的实际执行。**P0/P1通过，P2仅通过“oracle潜力与可定位预测差距”的机制门槛；P3完整运行但搜索收益NOPASS，没有有效端到端改善。** 三项失败诊断、原定23查询trace及截止报告均已完成。P4–P8未运行，不能将“交付完成”写成方法成功，也不能把历史下一步当作当前待续任务。

本卡直接核对冻结协议、阶段gate、版本state、current_findings、独立审查及[原实验总结](../实验总结.md)，不替换其原件。历史版本state为[`TIMEBOX_STOPPED_REPORT_COMPLETE_P3_NOPASS`](../hierarchical_target_search/20260907_v1/state.json)。当前工作须从[项目入口](../AGENTS.md)与[当前方案](../s-target.md)判断；本卡中的命令/路径仅是证据索引，不授权执行。

## 动机、机制与待证假设

此前入口路由可能把搜索送往正确的大区域，但统一有限候选池会淘汰通向目标的中间节点。该版本尝试同时设计覆盖全base的目标区域、query到区域质量的预测、每区门户，以及固定总容量下的区域候选保留。它没有把base分成互不连通的检索分片：原有向NSG保持原边，跨区域边一直可走，全部队列共享visited和全局top-K。

P2先用纯图64区和轻量几何画像做小规模机制证伪，比较同route下的统一、均匀区域和概率区域队列，并用目标GT区域比例提供oracle诊断。只有oracle与真实路由之间存在可定位差距，才允许一次表示/划分修订进入P3。P3加入训练GT10共现目标，在相同层次初始化和门户数下检验“目标更集中是否真正改善有限搜索”。这只是进入学习预测器前的结构性检验；P4层次预测器没有训练。

## 冻结设置与数据访问

| 项目 | 实际执行合同 |
|---|---|
| 数据 | WebVid `webvid2_5m_light_v1`，2,505,000×512；Yandex `yandex_t2i_official10M_ip_v1`，10,000,000×200 |
| 搜索图与距离 | 原冻结directed NSG、raw-IP；用于METIS初始化的去重对称辅助邻接不替代搜索图 |
| 拟合与pilot | router_train后20K `[10000,30000)`用于结构/门户/画像；前10K `[0,10000)`是已历史使用的development pilot |
| 配对Fast | 复用独立QGT5K raw hubs，只用相同后20K重建prototype；旧30K Fast不能混入配对训练链 |
| 搜索 | 全CPU、16线程，K10，L64/128；L是保留候选池容量，不是NDC或扩展次数上限 |
| P2 | 64图区域、每区2门户、激活4区；seed=2026090711，Micro-HNSW seed=100 |
| P3 | 16粗×16细=256叶，共同初始化；λ0/λ1分别两轮；每叶3门户，共768；frequency3/greedy3组成固定2×2 |
| 容量/调度 | shared池为floor(0.25L)，其余给4活跃区域，每区至少4槽，余量按概率最大余数分配；区域ID打破同分；区域内距离排序、队列间加权轮转 |
| 起点 | 新路径保留paired Fast首入口和图默认shared起点，消费全部有效门户；重复入口先取得队列所有权者保留，不误用legacy mode2最多3入口限制 |
| 重复/统计 | 每点warm-up128查询、count一次、纯wall五轮；10K query配对bootstrap10,000次，普通95%探索性区间 |

**访问口径必须区分两个阶段。** 夜间P0确实读取validation query/GT做文件头、全SHA、逐行查询指纹去重/跨split重叠、finite和GT范围/行内重复检查；validation未用于拟合、参数/模型选择或ANN性能评测，held-out文件未打开。旧P2 gate等文句中的“validation/held-out未读”不完整，以[访问补充](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p0/validation_access_scope_addendum_v1.json)为准。后来的Fast根因诊断没有打开原始validation/held-out，见[08卡](08_fast_router_diagnosis.md)，不能把两轮访问事实合并。

P2画像为按GT10区域比例加权的fit单位query之和再归一化；64区域分数softmax温度1，取top4后重新归一化以分配容量。门户是区域内fit GT10频次最高的两个真实ID，同分按ID；不足时从本区最小ID补足并记录。P3 oracle直接取目标GT10质量最高的4个叶区，它不是已实现的两层预测器。完整合同见[P2协议](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/protocol.json)及[P3协议](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/protocol.json)。

## 实际执行、验收与工程问题

| 阶段 | 实际完成 | 决策 |
|---|---|---|
| P0 | 输入SHA/形状/编号、fit/pilot/QGT/validation完整性及相互重叠核验；raw hubs与base字节、嵌入/外部base固定样本核对 | PASS，未生成新exact GT |
| P1 | 统一/区域搜索、count/plain/trace、同真实入口parity、计时和stage边界 | PASS，实现验收不是性能GO |
| P2 | 两数据集10K、6方法×2L，共24测量行/28固定对照；区域选择、容量和trace诊断 | `GO_P3_STRUCTURE_DIAGNOSTIC_ONLY` |
| P3新增P1 | 256叶、3门户、潜在14起点的消费/去重、P2兼容、单门户L32代理及模型身份 | PASS |
| P3 | 双数据集×两λ×两门户法完整8模型，48测量行/32固定对照 | `NO_GO_P3_SEARCH_TRANSFER` |
| 有界补充 | 门户暴露、目标泛化、局部尺度/代数审查及原定trace补齐 | COMPLETE，未新增性能点、参数或gate |
| P4–P8 | 层次预测、正式工作曲线、独立构建/消融/基线/tail、冻结held-out/第三数据、论文完成 | NOT_STARTED |

P1含11组合成检查、1200个kernel parity实例（含800同分）、visited epoch回绕、非法ID/空区域/重复起点/容量边界/K>L拒绝，以及两个数据集各512个真实查询的L64/128 count/plain/legacy、route和五轮结果一致性；另核对m4/6/8实际消费。ASan/UBSan针对所编译的新路径，不能称所有旧静态库已全面重编译审计。旧`ACSG.cpp/h`与旧Fast默认源码保留；新区域路径独立，CMake在原前缀后增加三个目标。新paired Fast消费正确的best-first入口顺序，不把“相同入口kernel一致”外推为旧/新端到端路由完全相同。[P1 gate](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/gates/P1.json)、[P3重新验收](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/gates/P1_P3_reacceptance.json)。

工程问题与方法失败分开：首次evaluator因PATH找不到cmake未启动，改用已有环境绝对路径后成功；WebVid前两次METIS容量检查失败，诊断保存12区各超2节点，随后补偿库内额外容差并保持原1.2硬上限，strict-v3通过。原失败manifest/标签/日志未删除，不能把INCOMPLETE分区当有效模型。还修复了同分顺序、sanitizer include和trace分析器合成问题；P3负结果是在这些验收通过后完整取得。[容量契约补充](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/partition_contract_amendment_v1.json)。

## P2关键结果：真实保护退化，oracle质量提高但成本增加

下表Recall为%，QPS是五轮整批wall QPS的算术平均，均为历史warm-cache实测；oracle使用目标标签，不能进入部署Pareto曲线。

| 数据/L | paired Fast：Recall / QPS | 真实几何+概率区域：Recall / QPS | oracle+概率区域：Recall / QPS |
|---|---:|---:|---:|
| WebVid64 | 65.657 / 32,079.8 | 59.929 / 19,573.6 | 71.354 / 21,352.3 |
| WebVid128 | 74.698 / 17,421.8 | 70.642 / 12,003.5 | 80.081 / 13,744.2 |
| Yandex64 | 82.832 / 27,390.7 | 75.652 / 16,508.9 | 86.248 / 19,062.9 |
| Yandex128 | 89.655 / 15,947.7 | 85.974 / 10,033.1 | 93.183 / 11,780.0 |

同route的概率区域池减统一池，真实路由四点Recall差为WebVid−5.431/−3.640 pp、Yandex−6.867/−3.488 pp；oracle则为+5.413/+5.252、+3.155/+3.359 pp，四个普通95%下界均正。可是oracle也增加NDC、降低QPS；全部真实P2方法在测点被paired Fast支配。以L64为例，Fast/真实概率/oracle概率总NDC分别为WebVid1046.777/1693.630/1473.662，Yandex1768.918/2864.523/2472.030。

区域选择诊断中，真实/oracle top4覆盖的GT10绝对质量为WebVid0.62539/0.94691、Yandex0.78774/0.98625；真实选区最大归一化权重均值0.254254/0.265276，oracle为0.647620/0.774598。WebVid L64有99.83%的真实概率分配恰等于均匀容量；相同容量样本的输出/计数相同。不过即使真实选区GT质量高的query也会受损，所以“只漏选区域”不是完整解释。这些证据只允许一次P3结构修订，不是端到端GO。[P2 gate](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/gates/P2.json)、[P2分析](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/analysis_v1/report.md)。

**23查询trace完整性。** 原注册ID为0–15以及157、631、2003、4093、6007、8009、9967。P2决策时仅完成前16个query，320条trace/192配对；其历史gate不覆写。后来按原名单和冻结实现补齐7条，共460 trace、276配对重放全部通过，新增140条trace与原10K count结果一致。trace显示被保留并展开的非GT祖先与救回GT相关，也存在反向伤害；它不是随机代表样本，first-discovery祖先不是必要/唯一桥的证明。同route对照同时改变保留和调度，不能宣称单独识别了保留机制的因果效应。[完成补充](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/trace_completion_addendum_v1.json)、[完整重放](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/trace_analysis_complete_v2/report.json)。

## P3机制、主对照和否决

目标为`J=C/M+λ·S/(9Q)`：C是原有向有效非自边跨叶槽数，M是全部有效非自边槽数，保留方向和重复槽；S是fit每query“GT10跨叶区数−1”之和，Q=20,000。λ0/λ1共享16×16初始化，每轮按base ID递增、即时更新，候选包括邻接叶，λ1另加同fit GT10共现叶；仅接受精确整数`9Q·ΔC+λM·ΔS<0`的可行移动。粗/细容量均受全局平均1.2倍上限，源叶至少3节点，每个分支两轮。每轮全量复算C/S与容量，禁止事后改λ、seed或轮数。

每叶最多8个fit频次候选，对含本叶GT10的fit query按固定SHA取最多128条。以原图K10/L32单入口搜索测该叶GT10命中mask，greedy选3门户最大化新增命中并集；frequency3取同候选列表前三。mask缓存共享，不为greedy三步重跑ANN；无fit支持时记录频次fallback。该代理不是最终多门户共享池的真实联合收益。

fit平均跨叶数λ0→λ1：WebVid4.33285→2.60275，Yandex3.00925→1.96480，结构子条件通过；预注册主对照始终为**oracle_probability下λ1_greedy3−λ0_greedy3**：

| 数据/L | λ0 Recall% | λ1 Recall% | 差(pp) | 普通95%配对CI(pp) |
|---|---:|---:|---:|---|
| WebVid64 | 74.140 | 73.274 | −0.866 | [−1.083, −0.647] |
| WebVid128 | 82.119 | 81.329 | −0.790 | [−0.960, −0.621] |
| Yandex64 | 87.994 | 87.899 | −0.095 | [−0.207, +0.016] |
| Yandex128 | 93.990 | 93.973 | −0.017 | [−0.080, +0.048] |

四格均没有正下界；WebVid两点明确退化，Yandex没有改善证据而非等效证明。因此P3于北京时间02:00:52完整判定NOPASS，并非07:00截止打断。8个greedy−frequency门户对照CI全部含0；16个同route区域保护对照虽加Recall，却同时加NDC/降QPS，不能救回主gate。λ0是预定消融，不能事后升格胜出主方法。[P3 gate](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/gates/P3.json)、[P3完整分析](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/analysis_v1/report.md)、[独立gate复核](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/gate_independent_review_v1.json)。

两个字段解释保留：Fast的部分expanded/rejected/evicted是未测量占位，不能当0；P3 bootstrap嵌套status残留初始值，但全部32个10,000-draw文件、完成标记与CI已独立核对，原件不覆写。[计数语义](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/measurement_semantics_addendum_v1.json)、[分析完成补充](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/analysis_completion_addendum_v1.json)。

## 三项失败诊断与局部尺度结论

**门户确实改变实际route。** 8格×10K的实际入口集合全部变化，排除“greedy门户没进入搜索”。返回top10集合仍有68.34%–93.36%相同，但不能推出访问轨迹相同、门户必然冗余或连接因果。没有完全相同route样本，所以相同route不变性检查为空，不能当新增实值验收。WebVid λ1有6条query的正权重区域没有fit支持，代理值记未定义而非补0。[门户暴露](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/portal_exposure_diagnosis_v1/analysis.json)。

**集中度不等于命中。** pilot跨叶数λ0→λ1：WebVid4.3194→4.0209，Yandex3.0181→3.0193；所选4区域承载的GT10比例M4分别+1.808/−0.004 pp。搜索可跨区域，所以M4不是Recall上界。seen是目标base ID出现在fit GT10，不是query重复；pilot seen目标槽占比57.258%/10.163%。WebVid−0.866/−0.790 pp由seen贡献−0.870/−0.753、unseen贡献+0.004/−0.037组成，排除“全是unseen导致”的解释。40对照、440支持分组和命中重算复核通过；这些分组无新增CI。[目标泛化](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/target_generalization_diagnosis_v1/diagnosis.json)。

**λ1局部候选排序实质先ΔS、后ΔC。** d(u)按原有向有效非自入/出边槽之和计，重复边保留。实际冻结输入如下：

| 数据 | M | M/(9Q) | fit-seen独立目标数 | seen最大d | 满足d·9Q<M |
|---|---:|---:|---:|---:|---:|
| WebVid | 49,611,457 | 275.619206 | 118,811 | 168 | 100% |
| Yandex | 294,844,794 | 1638.026633 | 188,913 | 162 | 100% |

两数据集各200,000个fit目标出现次数也全部满足，λ0/λ1终态标签不同的52,305/72,107节点均满足。全库WebVid仅17个例外且均unseen，Yandex全库满足。对固定节点、同一当前标签、候选与可行性，两个目的叶之间的割边变化差最多d(u)，不是2d(u)；整数ΔS不同至少差1，因此严格界使较小ΔS总优先，ΔS相同才按ΔC。unseen对所有候选ΔS=0，包括17个高阶例外。与stay零改善同分时保持原标签；严格改善移动同分才选较小叶ID。图仍影响候选和同ΔS选择，容量、源叶最小规模、更新顺序仍有效；不是全局字典序最优，不能把λ0/λ1不同轨迹当同状态反事实，也不单独解释Recall下降。该代数补充复核62汇总组及4,374个两候选比较、1,944个候选子集选择；没有新ANN。[尺度诊断](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/objective_local_scale_diagnosis_v1/diagnosis.json)、[纯代数补充](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/objective_lexicographic_addendum_v1.md)、[独立解释](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/objective_local_scale_interpretation_review_v1.json)。

三项诊断均先冻结范围再运行，不调参、不改gate。当前证据没有找到“目标更集中却丢seen命中”的唯一因果解释。

## 计时、离线成本、资源与停止

纯wall计时前分配工作区/结果缓冲，计时内包括query处理、真实路由、visited重置、去重、队列调度、搜索、结果写入；GT评分、hash、trace、JSON在计时外，count/trace独立执行并核对IDs。五轮整批计时不是独立Recall样本；routing-only另作16线程批测，不能当单query延迟。跨模型按固定顺序测量，未取得配对wall显著性；没有1线程p50/p95/p99或三独立build结果。[完整72测量行/60对照](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/measurement_tables_v1.md)。

| 已有图/GT后的离线程序wall | WebVid(s) | Yandex(s) |
|---|---:|---:|
| P2严格64区分区 | 27.7803 | 171.6399 |
| P2区域模型 | 0.2293 | 0.1814 |
| paired Fast20K prototype | 0.1831 | 0.0659 |
| P3层次分区（共同初始化+两λ分支） | 40.0332 | 262.2502 |
| P3 λ0门户程序 | 9.3434 | 17.1438 |
| P3 λ1门户程序 | 8.4327 | 16.5417 |

P3分区数不是单个部署模型成本；门户程序包含图加载/probe/评分/写出等，不含上游候选/fit抽取和exactGT/分区。frequency/greedy共享probe缓存不可重复计算；线程CPU秒不与wall相加。P2汇总partition=null是未嵌入manifest，strict-v3分区确实完成。完整从零成本仍须含exactGT、QGT、原NSG、分区、门户、路由；复用历史耗时未知为null，不能称“完整训练几秒”或据此给break-even。[分项成本](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/measurement_tables_v1_costs.csv)。

54项注册任务中34个已启动重任务的记录区间无重叠；最大子进程rusage RSS35.624901 GiB，最高轮询RSS35.560837 GiB；最终RUN逻辑大小3.335661 GiB、/data余量16.665653 GiB。它们是当时记录和快照，不是当前机器状态或全夜所有短命令的严格最大值。7个保护源码、CMake原前缀/三个新增目标及settings通过；无主动删除、reset/clean或推送。历史原件保留。

北京时间00:01:04首个注册审计开始，02:46:07最后诊断结束，03:02:48提前关闭新实验入口；07:00:00.312与07:01:24最终进程核验均无活跃任务，watchdog退出，没有跨截止任务或被截止中断的实验。其间等待不是训练。截止后只整理证据和写报告。[CLOSED](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/control/CLOSED.json)、[最终进程核验](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/control/final_process_verification_v1.json)、[保护与资源](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/final_protection_resources_v1.md)。

## 不得通过改名恢复的范围与复现索引

该版本只支持“实现合同通过、oracle保护有同L质量空间、训练集中度未传递到预定搜索收益”。不支持已获Recall–QPS改善、图不可达、所有区域法无效、一般不可学习或单一因果解释。修订计数为1不意味着还欠一次自由调参：当前gate明确不授权第二次表示修订、P4、λ/seed/L扫参、辅助图或held-out。

把同一目标改称目标一致区域、可达性分区、受保护frontier或新门户，不解除旧NOPASS。未来若有新机制，只能新协议、新输出、重审对应实现/统计/成本；旧报告末尾“下一次唯一行动”保留历史时点身份，之后已被入口选择研究接替。

精确复现参数、源码/二进制身份与原日志在[注册jobs](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/control/jobs)各JSON的`command`数组，P2/P3 runner在各阶段目录；不要向已关闭control输出。完整证据及SHA来源见[机器证据索引](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/report_evidence_index_v1.json)、[current_findings](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/current_findings.md)、[原实验总结独立复核](../hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/final_report_independent_review_v1.md)。本卡未重新计算原始矩阵、读原始query/GT或执行任何方法实验。
