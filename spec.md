# ACSG 代码架构与实现契约

文档接续于2026-11-23。GT10 主搜索内核按 E211 合同。E201–E253 见4.17–4.53。本文维护当前实现、输入/输出、metric、artifact及计量合同；结论见[summary](summary.md)，下一研究问题见[s-target](s-target.md)。详细历史模块合同已[归档](experiment_history/_maintenance/20261024_current_state_cleanup_v1/archive/spec.md)，原实现没有因文档整理被删除或改写。

2026-11-19存储更新：按用户“旧数据直接清除、保留简档”授权，退役数据集及早期实验的大型数据、旧模型和原始返回已按[逐项简档](experiment_history/_maintenance/20261119_obsolete_payload_prune_v1/archive_index.md)删除。当前七数据集所需输入/图/GT/画像/B32/SQ、E200–E203冻结依赖和COCO/Flickr准备后的身份/划分数据保留。下文旧实验的完整原件/重放描述属于当时交付事实；清单内旧包当前已不可直接重放，需重新下载或生成。生产API、metric、默认及当前模型内容未变。

2026-11-10补充[论文写作约定](论文写作约定.md)：说明训练GT/在线搜索/测试评测的角色，以及当前B32按三入口完整搜索遗漏、单位query-target联合覆盖贪心造表的准确含义。本次仅核对并解释现有合同，无API、画像、候选表、计时或默认变更。

## 1. 当前主链与实现位置

```text
合法训练query/GT → QGT选择真实base入口H → GT10目标归属 → 单位query画像W
raw query → 画像Micro-HNSW → 三个真实base ID → ACSG::search_new(mode=2) → Top-K
残差研究分支：同一主返回 → 三行冻结posting去重/评分 → Top-K合并
E198已测归档分支：保留全部直接C → 前置门 → 双塔短名单/教师重排 → 0/96/384单入口辅助扩展 → Top-K合并
GT只在训练监督或搜索返回后的评测层读取
```

GT10画像为`p_h=normalize(unit(x_h)+Σ_i a_ih unit(q_i))`；a来自训练GT前10个目标与真实hub的hard/soft归属，不是在线神经网络。GT10方法名的10与评测K独立。QGT按簇中query及其GT候选选择全局唯一真实ID，不等于质心GT1或GT全局投票。

2026-11-04研究收敛：主线只保留原搜索与直接补点；当前学习选点/精排导航/门控版本停止扩展，源码、模型和已测接口完整归档。下文4.12–4.14继续描述已实现事实，不代表当前推荐或待恢复队列。仅派生绘图与报告，不修改生产调用链、API、模型或计时。

| 模块 | 当前源码/配置 | 关键边界 |
| --- | --- | --- |
| 索引/搜索 | [ACSG.cpp](ACSG/ACSG.cpp)、[ACSG.h](ACSG/ACSG.h)、[IndexACSG.cpp](ACSG/IndexACSG.cpp) | 冻结邻接、真实ID、原DistanceComputer、visited与retset |
| 基础Fast构造 | [build_fast_entry_variants.py](benches/run/build_fast_entry_variants.py) | 原GT1画像及QGT分支；不能把旧30K Fast当GT10同训练量控制 |
| GT10画像 | [E24 build_profiles.py](entry_method_exploration/20260910_gt_topk_profiles_v1/src/build_profiles.py)、[E97 L2适配](entry_method_exploration/20260915_gate_l2_r1_r100_v1/src/build_profiles.py) | GT-topK hard/soft、当前W/ID映射以manifest为准 |
| 通用评测 | [test.cpp](benches/test.cpp)、[DataLoader](benches/datasets/DataLoader.hpp) | 选择split/metric；旧命令不自动代表新实验合同 |
| E183实际计时与补全 | [benchmark.cpp](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/src/benchmark.cpp)、[residual_tools.cpp](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/src/residual_tools.cpp)、[configs](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/configs/) | 原scalar主核、真实timed包、后置精确评分合并 |
| E184离线诊断 | [analyze.py](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analyze.py)、[audit_integers.py](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/audit_integers.py) | 只读旧返回/原向量；无ANN、训练、GT生成或QPS |

旧ACO→DPC→Neural Router、区域搜索、RL、多画像及证书等版本各有自己的历史实现/未实现边界，见[历史索引](s-experiment.md)；不属于当前GT10必需调用链。

## 2. 搜索接口与不变量

`ACSG::search_new(dis, topk, I, D, visited, mode, custom_enterpoints, retset_buf)`：mode0/1/2为原随机/固定权重/自定义入口模式。主结果必须为真实base ID和实际任务距离。

- mode2最多消费输入前三个位置，再用visited去重，重复不补位。调用方验证`0≤id<N`；旧注释不能替代ID检查。
- `search_L`是候选池容量，不是距离计算预算；正式K100要求L≥100。返回retset Top-K，不以其他独立global-topK语义代换。
- HNSW内部slot和base ID必须显式映射；heap-pop与真实ID排序是不同合同，各实验保留其配置。
- 现有`SearchTrace`不是完整可恢复搜索状态，retset/visited也不是pause/resume接口。独立C状态机属于历史工具，不能写成原接口已有能力。
- 画像W为单位向量，路由实现的`1-qᵀW`对固定非零q排名与余弦等价，数值不泛称已归一化余弦。原raw query/base不因路由而额外归一化。
- 主图为带向量的原生二进制时，`.json`后缀不表示JSON。padding −1保留其未用槽意义；原有序邻接/实际kernel身份属于复现输入。

- 标准 `IndexFlat`/`IndexFlatIP` 的 raw-IP 距离由 `storage_distance_computer` 标识，mode2 默认用 SPAN4。每次展开从当前邻接行尾取有效跨度，按原顺序计算并插入，四个有效未访问邻居使用原 Faiss batch4。候选池由调用方复用或由本次查询创建。
- `set_flat_ip_batch4_enabled(false)` 对该索引选择标量回退；在启动查询线程前配置。mode0/1、trace、L2、外部距离计算器以及空入口回退使用标量。每个线程持有各自的 DistanceComputer、visited 和候选池。索引文件沿原读写合同，邻接跨度无持久化数组。

E99共享NSG预取和候选复制优化的合同见[详细卡片](experiment_history/92_nsg_search_optimization.md)。E183沿其冻结的scalar实现，不能与不同优化核的旧绝对QPS拼接。

## 3. 当前七集评测域

| 数据集/key | N × d | metric | E183 H / 测试query | 原入口次序 |
| --- | --- | --- | --- | --- |
| Deep / deep10m_l2_v1 | 10M × 96 | squared L2 | 800 / 10000 | sorted_ids |
| SIFT / sift10m_bigann_l2_v1 | 10M × 128 | squared L2 | 800 / 10000 | sorted_ids |
| GIST / gist1m_l2_v1 | 1M × 960 | squared L2 | 800 / 1000 | sorted_ids |
| WebVid / webvid2_5m_light_v1 | 2505000 × 512 | raw IP | 815 / 10000 | sorted_ids |
| Yandex / yandex_t2i_official10M_ip_v1 | first 10M × 200 | raw IP | 821 / 10000 | sorted_ids |
| COCO / coco | 118272 × 512 | raw IP | 815 / 10000 | heap_pop |
| Flickr / flickr30k | 31782 × 512 | raw IP | 815 / 5000 | heap_pop |

真实base/query/GT、图、W、ID及角色路径以[E183配置](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/configs/)和[dataset catalogue](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/reviews/dataset_catalogue.json)为准，文件名不是身份。Deep/SIFT/GIST已完成接入，旧“未接入/不属正式协议”仅是历史时点。L2不强行归一化成IP；Web源近单位范数也不等于额外归一化；Yandex保持原IP，GT须对应first-10M库。

训练/验证/测试角色不混用。E183五集残差fit可共享原画像fit前16K；COCO/Flickr残差角色独立，须分别披露。已曝光公共测试不是新盲确认。LAION是历史迁移控制：其公共query与Web来源重合，不算独立第三query workload；其原始大数据及旧产物已于2026-11-19按授权清理，保留简档、原配置与报告，重放需重新下载/构建。旧泛化SIFT10M/Yandex目录也已退役，当前SIFT仍采用E97的BigANN输入，Yandex仍采用official first10M。

## 4. 残差补全合同

E183每个hard/soft家族用合法16K query、K100/L200遗漏生成单位query–GT成员token；保留全局未截断源、hub源、token、B8→32嵌套行。正式仅B8/B32，K1/K100共享同张K100教师表是固定条件，不称各K最优。

每query取三个路由行，B32去重前最多96候选。排除主返回及重复ID后按原metric补算，和同K/L实际GT10主包合并；不启动第二次主搜索，不改visited/展开/停止。候选覆盖与最终救回分别统计，近并列/浮点损伤保留，不能事后改GT。

**补点作为答案与作为入口的实现边界：** 当前B32没有连通度/密度资格筛选，也没有把补点映射成导航代表或注入原搜索状态。低密度或低连通度不构成现有直接补点阶段的删除规则。历史[E174](experiment_history/174_m5_residual_regions.md)另用原M5 C≤24逐路由行query-best选最多3个seed，沿原图一跳、额外24/96精算，保留完整C；它不是本B32的续搜功能，也不是完整多步搜索。

[2026-10-30理论文稿](entry_method_exploration/20261030_residual_navigation_theory_v1/theory_zh.md)提出区分入/出方向、有限预算导航价值与密度代理，保留答案候选并另选真实导航代表，以及条件性的稀疏修复/主搜索便宜评分。该文稿当时为THEORY_ONLY_UNIMPLEMENTED_UNTESTED；E195现已另实现全图静态统计、独立辅助扩展和导航代表基线，见4.10。原完整状态续搜、修图和主搜索新评分仍未实现，默认保持。

[2026-11-01学习入口设计](entry_method_exploration/20261101_learned_residual_navigation_design_v1/report_zh.md)提出真实扩展收益监督、多导航代表/路由入口表、查询条件拒绝与组合选择；新算法THEORY_ONLY_UNIMPLEMENTED_UNTESTED，只有既有探针只读复算。没有新增可部署模型、搜索状态接口、生产依赖或计时路径。直接C与导航H资格分开；将来导出状态、改变队列/图或增加模型时，须分别绑定输入、离线/在线特征和完整计量，不以本设计冒称现有实现。

E176的M5OPT、M5RES12、PAIR/WIDE及E179–182其他表属于独立版本；其容量、训练源、计时核、费用和结果不能借给当前版本。完整历史接口读[旧spec归档](experiment_history/_maintenance/20261024_current_state_cleanup_v1/archive/spec.md)并沿卡片找到对应协议。

### 4.1 适配设计与实际实施范围

[E186设计](entry_method_exploration/20261027_adaptive_completion_design_v1/design_zh.md)的原件保留当时纯理论身份。其候选来源部分现已在[E187](entry_method_exploration/20261028_adaptive_completion_pilot_v1/protocol.md)实现并测量；完整统一动作接口/不补全门控/逐query选择器未实现。原search_new没有新增暂停/恢复能力。

### E187区域候选实现合同

- [prepare_backend.py](entry_method_exploration/20261028_adaptive_completion_pilot_v1/scripts/prepare_backend.py)：原base抽65536训练coarse1024及global PQ M16×8bit；全base稳定分区，显式centroids/codebooks/ID映射/offset/PQ codes，IP粗代表球面训练只用于辅助路由。导出raw布局，不跨Python/C++Faiss版本交换序列化。
- [pilot.cpp](entry_method_exploration/20261028_adaptive_completion_pilot_v1/src/pilot.cpp)：共用E183原主核与路由，主搜索后REG-NN/Q/R从coarse top8选2区域，完整扫PQ码，排除原R，最多96原metric精算严格合并。NN取最近；Q用5特征ridge；R用10特征，额外包含R区域/分数摘要。选区、LUT/扫描/去重/精排/合并全部计时。
- [train_selector.py](entry_method_exploration/20261028_adaptive_completion_pilot_v1/scripts/train_selector.py)：合法原16K前12K fit、后4K cal只描述，不调参；标签为原L200教师遗漏在各region的计数，标准化ridge α10，负预测裁0，ties回粗rank。冻结模型固定迁移L100/200/400。B32原16K表保留。在线不读GT。
- 正式两集真实K100；原矩阵23点/集，独立C1控制每集另3个GT10点，共52点/156轮；CPU15实际1线程、完整六数组生命周期，原timed包保存。零NDC为未插桩布局；REG扫描/精算实时计数。B32原JSON的Stats0为占位，第二实现从实际主包/冻结表重构候选数，不能当作0访问。
- [freeze.json](entry_method_exploration/20261028_adaptive_completion_pilot_v1/freeze.json)绑定源码/binary/静态库/配置/模型/小输入，原base/图沿E183身份并核当前stat；编码记录完整消费向量流SHA，不冒称原容器全量hash。保存三轮raw SHA、点/轮收据、主包合并oracle、旧程序前缀/全分区/抽样编码核验及第二实现统计。
- [analysis](entry_method_exploration/20261028_adaptive_completion_pilot_v1/analysis/)：52点（原46+6控制）、配对成员/查询救损、严格<10%尾部、源内外救回、全离散预算对照、逐query压缩CSV及矢量PDF。单独部署区域法需额外全base后端RAM；共同benchmark进程加载后端不意味着GT10生产依赖它。结果不属于默认主链。

### 4.2 E187费用边界与后续实现

E187已有完整batch wall和REG扫描/额外精算计数；平均query耗时增幅可由中位QPS比值`QPS_GT10/QPS_method−1`派生。尚无粗路由、特征/预测、PQ LUT、码扫描/堆维护、精算、合并的分段耗时；不得把计数当耗时占比。

E187区域法固定选2区域并完整扫描，没有硬码数/字节数上限、成本感知训练目标或逐query跳过补全开关。R原分数已用于合并缓存；更广的候选/距离复用需先核现有接口和生命周期，不假设search_new导出了完整搜索状态。这些方案在E187当时尚未实现，并在[接续说明](experiment_history/_maintenance/20261028_completion_cost_handoff_v1/conclusion_zh.md)登记；原E187代码、模型、返回、计时和seal不变。

### 4.3 E188实验实现与实测合同

[E188协议](entry_method_exploration/20261028_completion_cost_budget_v1/protocol.md)与[源码](entry_method_exploration/20261028_completion_cost_budget_v1/src/cost_budget.cpp)在独立目录实现分段诊断、保持返回语义的OPT-R、区域内最多128点的PQ重构向量块、512/2048/8192码硬预算，以及实际救回/费用预测选区。原base/图/metric/主核和E187封存未改；仅COCO/Deep真实K100。

块预算每区域B/2，按原metric排序块中心，跳过超出剩余预算的整块；每区域48候选，总共最多96原metric精算。BLOCK-R沿原R选择，BLOCK-C2048用前12K实际补全标签固定ridge alpha10及非负操作费用模型。校准末4K选择数据集/L配置，正式10K矩阵前冻结；无逐query二元门控或完整主搜索状态缓存。正常QPS路径不插阶段计时器；legacy分段诊断复用扫描缓冲，不是原始完整wall的严格拆解。实现/输入身份见[freeze](entry_method_exploration/20261028_completion_cost_budget_v1/freeze.json)，完成状态见[state](entry_method_exploration/20261028_completion_cost_budget_v1/state.json)。

E188完成正式100点/300轮、校准100点/300轮。原B32包含末4K校准训练标签，原六项选择保留为角色失配诊断；正式前另冻[角色修正](entry_method_exploration/20261028_completion_cost_budget_v1/calibration_role_correction.md)，自动选择排除旧B32，正式参考仍保留它。未改变模型、预算或100点矩阵。新模型实际救回标签为单区域预算1024码/48候选的合并后GT100净增量，费用模型只估区域可变工作；固定粗路由/LUT等仍计完整wall。原REG-R诊断复用扫描工作缓冲，正式原REG-R调用旧路径。全部真实包、扫码/块代表/精算计数及三轮身份见[analysis](entry_method_exploration/20261028_completion_cost_budget_v1/analysis/)。

### 4.4 E189稀疏补全路由实现

[源码](entry_method_exploration/20261028_reuse_completion_routing_v1/src/reuse.cpp)复用只改main符号名的E188局部快照及原静态库；原E188/E187源码只读，非生产主核变更。[prepare.py](entry_method_exploration/20261028_reuse_completion_routing_v1/scripts/prepare.py)用合法前12K L200教师实际遗漏，分别按已有三入口统计region/block成员出现频次，每hub保留最高8项、ties按ID；另存全base ID→block i32映射。块/PQ/图/GT10复用原件。

REUSE-REG将三hub表与R中频次最高8区域合并去重（最多32），原metric评分后取最多8，沿原REG-R ridge选最多2区；少于8时跨度取实际末位，rank仍除7，少于2不补位。后续沿E188每区1024码/48候选。REUSE-BLOCK直接合并最多32块，按原metric中心距离/块ID排序，整块访问累计≤2048码，跳过放不下的块；全局PQ96、排除R、原metric精算及严格合并。MAIN-BLOCK只用R的最高8块，实际扫码≤1024，总体上限仍2048。辅助查表/统计/去重/评分均计wall；没有在线GT或新门控/完整搜索状态缓存。

正式70点/210轮、校准64点/192轮，真实K100/两集/CPU15/T1，L100/200/400补全及20档GT10控制。旧B32只做正式参考，因校准标签重叠而不进校准矩阵；本轮不做配置选择。3轮实际包一致、全主包oracle及预算核验；trace为L200实际主包的wall外全排序重建，非另外的timed内部trace。模型与源码/输入绑定见[freeze](entry_method_exploration/20261028_reuse_completion_routing_v1/freeze.json)，未改原base/metric/kernel。新ID→block映射为N×4字节，旧后端常驻成本并未清零。

### 4.5 E190固定候选评分实现

[源码](entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/src/scoring.cpp)在只改main符号及相对include路径的E189局部快照上增加SQ8；旧科学源码/图/metric/GT10/块/PQ不改。[协议](entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/protocol.md)固定原REUSE-BLOCK的pool、原metric块中心排序、2048码及96原metric精算上限。SQ8使用原C++Faiss QT_8bit、RS_minmax arg0，全原base无query/GT训练，输出trained和按原block IDs顺序的码；运行期新增ID→码位置映射。SQ8分数取负IP，稳定短名单，再沿原精算/合并。

SQ8-96对所有扫描且不在R中的码评分；无用PQ LUT不创建。条件PQ384-SQ8则沿旧PQ取384，再SQ8取96，代码已资格核验；本轮条件未触发，未作为正式在线方法执行。选择记录见[selection](entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/selection.json)，不增加其他宽度/模型。

正式38点/114轮，primary校准26点/78轮；仅COCO/K100。实际timed包三轮一致，全量主包补全oracle，所有评分版本pool/扫描块顺序逐query一致；SQ8近似评分数与原metric精算数分别计。trace是wall外从实际主包重建，非timed内部trace。完整费用包含正常输出生命周期；共载SQ8数组的benchmark RSS不等于GT10生产依赖或单独部署增量。来源/二进制/静态库/配置身份见[freeze](entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/freeze.json)，结果/结论见[报告](entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/report_zh.md)。

### 4.6 E191七集两K综合实现

[源码](entry_method_exploration/20261028_seven_dataset_scoring_v1/src/benchmark.cpp)沿E183冻结主核/加载/路由/完整计时，支持真实K1/K100。GT10/B32控制与旧实际包一致；REUSE-PQ/SQ相同pool/扫描ID，MAIN-SQ仅真实主返回块。K1不暗取100返回。K100教师块表前12K拟合，每hub8块，跨K固定共用；B32原16K表只作正式参考。

COCO/Deep复用E188/E189块/表，其余同机制在全base建立coarse1024/global PQ/最多128点块。Yandex d200适配M20，其余M16；原metric不变。SQ8原C++Faiss QT_8bit minmax全base训练、无query/GT；码按block ID顺序。REUSE扫描≤2048、MAIN实际≤1024/K1仅一块，各最多96原metric追加精算并严格合并。计数分别保存PQ/SQ/块中心/追加精算，不是总NDC。

正式原矩阵448点/1344轮，另一次密集541点/1623轮，预热256、3轮实际包bits/SHA与全量补全oracle。每集正式结束后才分析/二实现核验/无损gzip trace，再串行下一集；不并发数值工作。实际timed原始字节经逐文件SHA往返核验后无损存入raw_packets.tar.zst；packet_archive.py支持验证和精确还原，run_archived_posthoc.py只适配读取，原科学posthoc源码保持。trace为wall外实际主包的全排序重建，gzip保留未压缩SHA。归档与分析不和正式性能并发。

模型与结果在/root/acsg-e191-storage，项目storage链接明确索引；共享benchmark RSS不等于默认依赖或单独部署增量。新五集PQ编码有完整消费向量流SHA；复用资产/大base及图沿旧来源并核stat，小输入/模型/库/二进制完整SHA见[freeze](entry_method_exploration/20261028_seven_dataset_scoring_v1/freeze.json)。补充身份见[dense freeze](entry_method_exploration/20261028_seven_dataset_scoring_v1/dense_freeze.json)。当前存储合同见[存储修订](entry_method_exploration/20261028_seven_dataset_scoring_v1/storage_format_update.md)。用户后续明确授权PDF，交付PDF/文字/CSV及图表；原冻结no_PDF属于此前交付计划；结论见[report](entry_method_exploration/20261028_seven_dataset_scoring_v1/report_zh.md)。

### 4.7 E192共享必要条件与重配对照（已完成）

[协议](entry_method_exploration/20261029_sharing_necessity_v1/protocol.md)和[集合证明](entry_method_exploration/20261029_sharing_necessity_v1/theory.md)区分固定ID源、块支持与主搜索效用。E191主核局部拷贝只新增同长度组内重配的第二张hub-block表；SHUFFLE-SQ与REUSE-SQ共用全部块/码/精算/合并，2048/96上限不改，实际访问计数另报。旧源码/输入/原seal不回写。

新表重配为固定32种PCG64 seed20261029..20261060，正式只测预定第0种，不按结果选择。三集真实K100/L200六方法与8档GT10同窗口39点/117T1轮；资格36点单轮另计。七集真实两K/L200全部旧实际包用于候选池上界和32次重配诊断，不把它当新在线QPS。当前实现/配置身份见[冻结](entry_method_exploration/20261029_sharing_necessity_v1/freeze.json)。全部39点/117轮与36资格点通过；七集14个数据/K组合×32重配，共358.4万个查询/重配实例的池覆盖另由stdlib复算。费用排除证书以整数命中数、当前实测完整QPS和同窗口GT10判断，不是未来实现的时间下界。结果见[报告](entry_method_exploration/20261029_sharing_necessity_v1/report_zh.md)。

E191 seal包含可变根文档，其原字节已在本轮source_before保存，映射见[迁移收据](entry_method_exploration/20261029_sharing_necessity_v1/reviews/E191_before.json)；当前根文档按新授权更新，旧科学产物和seal原件不改。新增产物/root/acsg-e192-storage经storage链接；无新增PQ/SQ训练或图改动。

### 4.8 E193条件残差开关（已实现并完成pilot）

[源码](entry_method_exploration/20261029_adaptive_completion_gate_v1/src/benchmark.cpp)通过重命名main嵌入原E191实现，原文件不改；GT10/B32/REUSE-SQ直接复用旧调用，条件分支在真实原NSG主搜索之后执行同一SQ complete，原32块/2048码/96精算和metric不改。新Gate支持off/on、标准化ridge双头和深度3 CART双头；gain/cost得分与冻结阈值比较。特征仅来自原query范数、route profile摘要及当前主返回D摘要，ROUTE5项/POST12项；未新增独立预查询probe或读取GT的可部署特征。

开发取原合法16K残差角色相对[12000,14000)拟合、[14000,16000)校准，新块表前12K不重训。旧GT10监督可能用过16K，旧B32包含末4K标签所以只作正式参考。拟合2特征族×2模型×7阈值，校准保留>=90%正收益后最小估计费用，允许全开/全关回退；实际模型见[冻结](entry_method_exploration/20261029_adaptive_completion_gate_v1/formal_freeze.json)。推断预算0.5us仅为校准估计，实际QPS计真实调用。

真实三集两K、2048固定query、12个GT10 L与L200五个辅助方法，共102点/306轮；资格36点、开发12点另计。完整timer覆盖Batch生命周期、路由/主搜索、特征/模型/开关、条件complete和六数组复制。GATE-ORACLE预载GT导出的正收益mask，实际付开关与条件执行费用，严格诊断、不可部署。GATE-OFF用于观察条件核费用，不以微计时简单相加替代wall。另保存三次逐query complete微计时，仅动作费用选择用。

实际四数组、enabled.u8、access.u64、三轮wall/hash在storage保留；native全query全排序SQ oracle，Python核Recall/损伤/门分支/推断/访问量/hash，L200三旧方法与E191同query字节对齐。封存、数据角色和原E192根文档迁移映射均独立，不改旧seal；默认未改，结论见summary，完整证据见[报告](entry_method_exploration/20261029_adaptive_completion_gate_v1/report_zh.md)。

已有补全实现继续保留各自身份：M5三hub至多24个固定ID候选、B32单位query-target表、REUSE-SQ/MAIN-SQ块源均见各原合同。E193只对冻结REUSE-SQ新增条件调用，并未替换或穷尽这些后端。历史有效配置与原始费用见[证据目录](experiment_history/_maintenance/20261029_residual_positive_evidence_sync_v1/conclusion_zh.md)，属于结果索引，不新增实现或默认依赖。

### 4.9 E194等价省费实现（固定矩阵已完成）

[独立源码](entry_method_exploration/20261030_residual_optimization_stability_v1/src/benchmark.cpp)重命名main嵌入原E191实现。原B32、SQ、GT10调用保留；OPT-B32用固定512槽哈希表保留三行/候选次序，原metric全部评分后严格合并，K1简化单元素堆；异常主返回回原apply。OPT-SQ保留pool/块中心评分顺序、2048码/96精算及合并，仅连续存储分数再nth_element与Less(distance,arrival)排序。未改生产核、原模型或实现新门。

每集两窗口各2048query；COCO确认源为未分配身份组，WebVid新抽源query与已登记角色逐向量去重。确认GT由全原base/raw-IP IndexFlatIP生成，固定8条float64分块核查。大产物/root/acsg-e194-storage经storage链接。旧base/图继承来源并核stat，小资产完整SHA。query期CPU15/T1、三轮完整Batch生命周期；B32计数wall外重建，SQ计数计入wall，均非总NDC。实际包/三轮hash、全排序及scalar oracle、候选次序/std-lib核验见reviews，已完成256点/768T1及20资格点，全部原生/stdlib核验通过；具体性能与保留配置见本轮report和analysis/stability.csv。

### 4.10 E195详细定位与独立辅助导航（已实现并完成）

[独立源码](entry_method_exploration/20261101_residual_navigation_diagnosis_v1/src/benchmark.cpp)嵌入只重命名main的E194快照，GT10/B32/SQ调用沿旧原实现；新六种动作在原主搜索后保留全部B32 C及原metric分数，再选择最多3个seed并沿原图一跳或独立有界多步扩展。DIST96/384用逐路由行query-best，NOVEL96/384在距离前12个C中按相对主visited和已选邻接的新覆盖贪婪选择，REP384使用全图真实h→C入邻居的静态度数代表。代表评分计入384，C评分另计；物理辅助访问≤64×额外精算预算。原visited只读、辅助seen/队列独立；已选seed可主动展开，后续main visited及全部C/已评分节点跳过精算和新入队，未选C不自动展开。该限制见implementation_boundary.md，不代表所有状态共享/续搜策略。不恢复原beam，不改主图或生产核。

Meta按唯一非自环有效边计算入度/出度，保留N×4/N×2数组及C→代表映射；这些全N数组用于离线/诊断，REP在线只需映射，GT10/B32不新增依赖。共同benchmark加载SQ/度数不等于默认部署RAM。局部replay.inc由原search_on_graph_new复制，仅加评分/展开/拒绝ID记录，七集两窗两K三L全42864条调用与原主包ID/距离字节核对；不是完整可恢复状态API。

正式1260点/3780T1，资格140、旧二进制控制56（42对应包），两曝光公共窗口各512、GIST500。正常完整Batch生命周期、路由/主搜/C评分/选择/扩展/合并/六数组复制销毁计wall。所有三轮输出/工作一致；504个辅助点的257184条query候选事件由原生线性oracle和Python全排序核最终ID/距离字节。单seed384探针及GT相关仅wall外诊断，不是线上规则或联合beam证明。冻结、来源/预算、计数语义见[协议](entry_method_exploration/20261101_residual_navigation_diagnosis_v1/protocol.md)与[formal_freeze](entry_method_exploration/20261101_residual_navigation_diagnosis_v1/formal_freeze.json)；旧科学文件、PDF和seal不改。仍未实现原状态续搜、修图、新主搜索评分或新门。

### 4.11 E196费用邻近控制（已完成）

[源码](entry_method_exploration/20261101_residual_navigation_cost_controls_v1/src/benchmark.cpp)只嵌入重命名main的E195快照，新runner改变固定评测点表和三轮顺序，不改任何导航、图、metric、GT或模型。51个既定配置/102窗口点与GT10/OPT-B32控制共837点/2511完整T1。控制L由E195完整费用曲线的预先插值±2及原L+1提出；OPTB32旧L100绝对时间差只作预算估计，实际Recall/QPS重新测量。旧QPS不混拼。

全部新OPT-B32预算沿原Posting合并，原生全query线性oracle验证；原窗口包全query SHA对齐，三轮六数组/工作相同。NumPy全排序再核52008条候选事件，NumPy和stdlib整数/hash/完整wall复算全部837点；输入继承E195 identity，旧meta只读。timer沿E195完整生命周期，CPU15实际T1。两曝光窗口、有限L与单图限制保留；当前结果是对照收紧，不新增生产依赖/状态续搜/修图/评分器或新门。

固定配置/预算/二进制身份见[协议](entry_method_exploration/20261101_residual_navigation_cost_controls_v1/protocol.md)、[选择](entry_method_exploration/20261101_residual_navigation_cost_controls_v1/selection_freeze.json)、[freeze](entry_method_exploration/20261101_residual_navigation_cost_controls_v1/formal_freeze.json)。大输出/data/acsg-e196-storage经storage链接；E195科学原件与seal不变，根文档由source_before桥接。

### 4.12 E197瓶颈分离与恢复合同（已实现并完成）

[协议](entry_method_exploration/20261101_residual_bottleneck_separation_v1/protocol.md)、[源码](entry_method_exploration/20261101_residual_bottleneck_separation_v1/src/benchmark.cpp)在独立目录复用只重命名main的E195快照。Q8-B32从旧合法16K教师token筛前8K，按嵌套greedy8/16/32编译；后8K固定2048入口fit/1024 cal，精确向量去重、COCO/Flickr身份组核验另存。旧16K B32保持强控制；GT10画像历史监督重叠披露。Q8模型向FULL、L200向L100/400为固定迁移。

ORACLE-C1/S1读取GT导出的入口mask，是不可部署诊断，GT选择费用不作为在线识别成本，不参与默认/部署比较。正常学习选择只用可部署特征，独立决策核验移除teacher mask。

真实K1/K100、L200、单seed384产生3485197标签。已实现24维ridge及104维固定128轮HGB（原坐标签名投影、前4有效有向出槽摘要等，非训练GNN），28候选拟合/14选定模型。MODEL1全C预测净增量选1入口；MODEL-GATE在评分后按合法cal阈值选0/1入口，完整C直接答案始终保留。DIST1/FULL为同池、同384单入口控制。已实现的门不能省掉已完成的全C评分。

CBRIDGE放开未选C中间点；SHARED用minimal_cached_search保存真实主评分及展开ID，允许已主评分未展开中间点并过滤其他已展开点，仍是独立辅助队列。SHARED-CAPTURE只付捕获并返回直接答案；AUX384-FAST使用同候选计划/适配层且包与原AUX逐字节一致。提前入口只用画像/残差表预评分，最多3槽，替换初始化集合；原GT10路由ID与实际early seed分别保存，不是时机单变量实验。生产search_new仍无完整pause/resume，未修图或改主搜索评分。

正式9434点/28302完整T1，CPU15实际线程1、库线程1、单方法串行。计wall包含正常Batch创建、路由/主搜/评分、特征与预测、状态保存、扩展/合并、六数组复制与销毁；加载、GT、写盘、hash/oracle在外。原/新完整native三轮返回/工作一致；原timed包按1原持久、11原三轮SHA恢复、2新GIST保留身份。四个保存数组加两组零NDC数组和形状构成包SHA；零NDC不是零距离计算，额外work不是总NDC。

恢复实现[recover_packets](entry_method_exploration/20261101_residual_bottleneck_separation_v1/src/recover_packets.cpp)只调用冻结搜索/Runner，必须逐点匹配原日志每轮六数组SHA才复用原wall；恢复时长不作query QPS。60点/416原持久payload资格字节一致。恢复窗work/seed/witness重放，不声称各自丢失原文件SHA已还原。GIST旧中断仅留时长下界，完整进程费未知；新A/B完整重测。285冻结文件和大资产stat、模型参数均不改。

[checkpoint_storage](entry_method_exploration/20261101_residual_bottleneck_separation_v1/scripts/checkpoint_storage.py)在native结束后无损归档raw/witness payload，长窗zstd重编码核整个tar SHA；逐点JSON入带member SHA的metadata tar，完整summary/config/environment仍可读。原gzip包装字节不声明保留。每窗复制/核对持久副本再进入下一窗。最终/root/acsg-e197-storage为真实持久目录，部分packet在/data持久卷，以稳定文件链接访问；原日志亦按字节不变的链接保留，无RAM依赖。[存储例外](entry_method_exploration/20261101_residual_bottleneck_separation_v1/storage_amendment_20261102.md)仅改内部预算，不改冻结协议字节。raw读取仍用原archive.load_packets，逐点JSON可按metadata manifest重建。

验证完成：1344初始捕获/原核调用、6074996缓存评分词、8064辅助线性合并；精简捕获再核并保持952旧运行包。正式分析核9434包、2768568候选witness、5403128GT探针，728旧包字节一致；逐候选native/NumPy模型选择及门分支、stdlib独立整数/hash/wall核验全部通过。独审是同执行者不同实现，不重跑所有图标签或独立bootstrap。恢复动作证据身份随前段注明。具体结果和默认决定只读summary；E197收口时后继强表示/前置拒绝尚未实现，随后E198的具体实现另见4.13。

### 4.13 E198条件残差动作策略（已实现并验证）

[协议](entry_method_exploration/20261102_conditional_residual_policy_v1/protocol.md)、[源码](entry_method_exploration/20261102_conditional_residual_policy_v1/src/benchmark.cpp)及[策略](entry_method_exploration/20261102_conditional_residual_policy_v1/src/policy.inc)在独立目录嵌入只重命名main、改绝对include的E197快照；原主核/图/metric不变。新DIST96/384为全C最近的单seed，与E195同名逐路由多seed语义不同；不能按同名混拼。完整C直接答案始终保留，辅助后端visited/seen/队列沿E195独立有界扩展，新增精算上限96/384、邻接槽上限64×预算，不恢复主beam。

COCO/WebVid每集四状态分别生成全C两预算真实净命中/救损/工作标签。Q8银行来自原前8K，后8K合法选定角色沿E197；2048学生fit、512epoch/λ开发兼门fit、512独立阈值/费用cal。原画像监督交叠及开发角色共享披露。每状态/预算HGB128轮/15叶/lr.08/L2=10；学生query25→64→两32头，node34→64→32，另23便宜候选线性特征，结合教师/真实收益回归与query内正收益排序，24epoch由开发收益选定。node32表示离线导出，线上query只编码一次。未训练GNN。

FAST在全C廉价选1；CASCADE每预算保留最近1＋学生前5（去重≤6），再用匹配教师重排；ADAPT选最大预测收益减λ×预算/384的正值，否则无动作。λ只选固定开发列表。POLICY先在12维便宜query/route/C/主返回摘要上运行深度3门，再决定是否付投影/学生/重排费用；门拒绝返回Q8直接答案。门仍付C精算，不能视作跳过全部补点。GT仅离线标签/评测读取，TEACHER384是部署可用预测器，非GT oracle。

共享query投影/范数/距离跨度等只计算一次。OLD-CACHED384与原MODEL1全query返回字节等价，强控制仍调用原GT10/OPT-B32/Q8-B32/SQ实现。完整matrix1,480点/4,440批次，CPU15实际T1、库线程1、单方法串行；计wall包括正常Batch创建、主搜、C、模型/门/扩展/合并、六数组复制销毁。加载/GT/持久化/hash/核验在外。工作邻接计数只覆盖辅助展开，不含主搜索和教师特征扫描，额外精算非总NDC，包内零NDC只是占位。

独立决策审计使用analyze_v2.py，将树比较输入提升float64以保持原生double阈值语义；首版NumPy隐式降精度导致的失败日志与原冻结源码保留，正式模型/返回/wall不改。首轮保存实际返回，另外两轮SHA、work、seed/budget/gate决策相同。native线性oracle、NumPy全排序、独立Python逐query预测/短名单/预算/门决策、stdlib整数/hash/wall/强前沿与旧兼容包核验通过；同执行者不同实现。标签源由labels_frozen.cpp精确桥接构建SHA，后续实现不回写它。新raw/work/决策/witness/特征witness按payload无损压缩并往返核验，持久storage为真目录，无RAM证据依赖；gzip包装字节不声明保留。源/模型/配置/角色/小输入SHA及继承大资产stat见[formal freeze](entry_method_exploration/20261102_conditional_residual_policy_v1/formal_freeze.json)，结果、费用与边界只读summary/report。旧科学文件、seal、PDF不改，根文档由source_before桥接。

### 4.14 E199门时机、F/N语义与精排成本（已实现并验证）

[协议](entry_method_exploration/20261104_gate_timing_cost_v1/protocol.md)、[benchmark](entry_method_exploration/20261104_gate_timing_cost_v1/src/benchmark.cpp)及[kernel](entry_method_exploration/20261104_gate_timing_cost_v1/src/kernel.inc)在独立目录嵌入只重命名main/绝对include的E198快照。四多模态集原raw-IP/base/图/router不变。COCO/WebVid复用冻结E198 L200模型，Flickr/Yandex按相同方案新建匹配K1/K100模型；Q8银行和3072角色沿E197，2048学生fit、512开发兼门fit、512独立cal，原画像交叠和开发共享披露。

STATIC按状态cal正增量选全开/全关。PRE22在路由后主搜前预测；POST28再用主Top-K摘要，在C精算前预测；N-CPOST12使用已评分C摘要。门为深度3/min_leaf32树，fit512，阈值只由独立cal按75%/90%正增量保留选择。PRE-LATE使用同PRE模型/阈值只改执行位置，返回、动作、工作量完全一致。主搜索始终完整，无主循环内动态早停或pause/resume。

F门off返回主结果、on调用相同Q8＋CASCADE384；N门off返回完整Q8直接答案、on追加同CASCADE384。固定单seed384、物理辅助邻接≤64×384。FAST384、最近DIST384、全C TEACHER384及完整B32/SQ强控制均同期测量；候选bank/后端/预算一致。原模型与主核未改。

736正式点/2208完整T1，CPU15实际线程1与库线程1；正常路径通过模板关闭所有阶段时钟，完整Batch创建、全部处理、六数组复制销毁计wall。另行profile记录route/main/gate-features/gate-predict/C/student-shortlist/rerank-features/rerank-predict/expansion/merge及query总量，逐条与normal包/工作/决策核对。profile batch缺少正式六数组复制销毁并含阶段时钟，边界不同；分段和、P50/P95和profile差额都是诊断，不替换正式QPS。基线GT10/OPT-B32/Q8分段采用返回等价逐query适配路径，分配/调度不同于原优化batch，不是严格拆解；门normal/profile沿同一模板查询逻辑。门特征可能复用，阶段迁移不是同额新开销。

辅助work保留原8字段；decisions.i32每query7字段为action-enabled/seed-ID/cap/rerank-rows/rerank-neighbor-slots/gate-position/gate-enabled。profile.f64每query11字段顺序见environment.stage_names。ALWAYS的selection witness保存22+28+12门输入及全C104维特征，用于Python独立门/学生/教师决策；其他自定义点保存main+events线性合并witness。实际首轮四数组加两组零NDC和形状形成包SHA，三轮返回/work/决策一致；零NDC非无计算。

全开/全关、同门移位、normal/profile、旧动作包资格通过；正式native线性merge、NumPy全排序/树double阈值与学生推断、门分支、stdlib整数/hash/wall/前沿和旧兼容包核验通过。独审为同执行者不同实现。raw/work/决策/profile/witness按payload无损归档并往返核验，证据持久化，无RAM依赖；gzip容器字节不声明保留。模型/源/配置/角色/小输入SHA及继承大资产stat见[冻结](entry_method_exploration/20261104_gate_timing_cost_v1/formal_freeze.json)。详细PDF已实际渲染核查，旧科学文件/seal/PDF保持，根文档由source_before桥接。

### 4.15 E199图解整理与停止决定（无新实验）

[图解报告](reports/20261104_residual_pruning_graphs_v2/README.md)只读取E199冻结的points/frontier/aggregate/stage/rerank表。按同dataset/K/L/方法合并A/B命中数与每query完整耗时，粗线为描述合并、浅线为逐窗控制、灰点保留复杂分支逐窗原值；16K/8K表明确区分，SQ保留条件对照身份，不把所有旧残差版本判负。没有重测QPS、重训、调阈值或删除旧科学资产。

交付5页PDF、PNG/SVG、派生CSV及实际PDF渲染。来源SHA前后保持；修改前六根入口文档由source_before桥接E199交付时的after SHA，旧delivery manifest与16页PDF原件不回写。研究停止属于优先级变更，已实现历史接口不因退出主线而抹除。

2026-11-05[当前方法说明](reports/20261105_current_method_summary_v1/README.md)仅依据现有spec、E183造表源码和E194直接补点源码编写，交付3页PDF与流程图。范围为GT10接口与B32直接补点；不把已归档双塔分支写入当前调用链。PDF示例采用人为数值、非新测试。没有新增API、模型、生产依赖或计时路径，旧报告和封存字节不改。

随后按新授权交付[8页方法/收益/尾部/局限综合版的图形修订](reports/20261105_method_benefits_limits_v3/README.md)：原3页直接嵌入且逐页文本一致；后五页为E199两条固定主线K1/K100曲线、E183严格低召回三阶段统计、E183同L200完整成本和限定范围的研究局限。用户要求移除A/B浅线后，每方法只绘制一条合并实线；208个合并曲线点与8行成本CSV和前版逐字一致，仍来自原两批各512条曝光查询。COCO七L/21个原GT/实际ID包重新按集合交集复核，并与旧NPZ逐条相等；尾图标明新增1条发生于GT10阶段，B32未新增也未救回。不同来源/窗口分别标注，不合并绝对QPS；无新API、ANN、GT、训练、计时或默认变更。原v2综合版、无PDF尾部分析目录和旧PDF/manifest均保持原件，六根入口另存修改前字节并桥接v2交付。

### 4.16 E200四方法评测适配（完整矩阵与核验已完成）

[独立目录](entry_method_exploration/20261110_multimodal_four_method_retest_v1/protocol.md)复制E183 runner，四方法共用原scalar主核；直接残差使用复制的E194 fast_plan/fast_apply，GT10路由与完整16K/B32原表保持。GATE分支沿E97单位query、slot映射与heap-pop，主搜仍用raw query。WebVid GT10固定soft-t1，其余hard；真实K1/K100各20档L，共640点/1280批次/1120万查询。只计两遍，主QPS是两个N/wall的算术平均，另存平均wall和合并QPS。完整六数组生命周期计wall，实际CPU15/T1，加载/GT/写出/hash/oracle/压缩在外；未插桩NDC零值不代表没有距离计算。

四集64个资格点通过：48点NSG/GT10/B32与E183实际包逐字一致，16点GATE与独立旧E97评测器一致。正式640点两轮bits/SHA相同、全部残差与同K/L实际GT10主包的独立合并oracle通过。首轮四payload加两个零计数数组与形状构成packet SHA；2560个payload无损gzip并往返核验后才移除新冗余原始副本。全部101项冻结文件在正式前后完整SHA核验。

COCO/Flickr GATE补建沿E97标签/拓扑/训练流程，合法residual前10K训练、随后1024 monitor，与测试向量及身份组分离，但与旧B32监督共享。原GT10监督规模也不同，非等监督量消融。512真实hub、WL2/Doc2Vec10epoch、修正正负标签、原塔；线上只用导出W及小图。COCO选epoch22，Flickr选epoch7，patience20终止。Flickr因主机重启从epoch7完整模型/优化器/RNG接续epoch8，最终选定W与重启前最佳W逐字一致；全部正式计时在恢复之后。未知中断费用与已记录下界分列。Web/Yandex模型复用。

[主分析](entry_method_exploration/20261110_multimodal_four_method_retest_v1/scripts/analyze.py)从原GT和实际timed包重算640点、480配对、96门槛和有限网格覆盖；[stdlib独立实现](entry_method_exploration/20261110_multimodal_four_method_retest_v1/scripts/audit.py)另核全部整数、wall/平均、SHA和2560个archive payload。实际PNG审阅及SVG每条20标记核对完成，独审为同执行者不同实现。报告派生记录4个正确成员替换事件但无逐查询命中数下降，不改GT或返回；详细结果只读summary/report。

新产物预算6GiB、root可用f_bfree下限6GiB，不改文件系统保留比例。旧科学资产、seal和模型不改；当前根文档的原字节按source_before及reviews/root_before_final桥接。无新增生产API、图修改、残差门/导航、PDF或默认替换。当前交付见[README](entry_method_exploration/20261110_multimodal_four_method_retest_v1/README.md)与[state](entry_method_exploration/20261110_multimodal_four_method_retest_v1/state.json)。

### 4.17 E201 查询条件化在线残差实现（2026-11-13）

[原设计](entry_method_exploration/20261113_query_conditioned_residual_design_v1/design_zh.md)保留当时纯理论身份；用户后续授权在独立[E201目录](entry_method_exploration/20261113_query_conditioned_residual_v1/README.md)实施两集首版。原生产B32/search_new接口、图、metric和默认保持。

[train.py](entry_method_exploration/20261113_query_conditioned_residual_v1/scripts/train.py)只用原base建平衡树（叶≤32）；每节点8维稀疏几何投影，学习修正另8维，实际最多16个查询坐标；这是原理论8维总上限的首版偏离。合法16K查询按身份组划分fit/dev/cal，使用真实K1/K100、L100/200/400遗漏学习稀疏ridge(alpha10)几何logit残差；每节点至少32个不同fit查询才训练，否则几何回退。Q用8维查询+K/L，QR再含主返回top8子树分布、结果分数/画像分数摘要；无全查询在线编码或强教师蒸馏。每层beam1/2/3、≤64节点、≤32/64/96候选，按原metric精算并严格合并；不续搜原图。

[benchmark.cpp](entry_method_exploration/20261113_query_conditioned_residual_v1/src/benchmark.cpp)复用E200原scalar主核/B32等价实现和E191 REUSE-SQ后端，同进程同输入完整生命周期计时、CPU15实际T1、每点两遍QPS算术平均。Q/QR/几何及GT10/B32/SQ同期比较，真实timed包保存、两轮bits/SHA及主包补点oracle；Python独立路由资格已通过。正式172点/344批次已完成且独立数值核验通过，结果读[state](entry_method_exploration/20261113_query_conditioned_residual_v1/state.json)。模型/代码/输入身份见[冻结](entry_method_exploration/20261113_query_conditioned_residual_v1/freeze.json)。未实现自动动作选择、主beam恢复或完整设计的强教师；不以节点/候选计数替代耗时。5%–10%仅原设计开发假设，本轮不作硬限制。 中断后用原二进制保留完整点、整组重测WebVid K1/L400，12个中断批次另档不进入主表；目录桥接和分阶段计量见[恢复协议](entry_method_exploration/20261113_query_conditioned_residual_v1/reviews/resume_plan.json)。88个适用GT10/B32包与E200 SHA一致；额外树数组（含Q/QR）2.50/70.11MiB。

同日独立[方法诊断](entry_method_exploration/20261113_query_conditioned_residual_diagnosis_v1/README.md)只读旧模型/向量/主返回：C++节点路由增加逐层历史记录，无图/ANN调用，36个原生10K叶trace全量一致；Python集合/Counter另核候选支持和三叶上界。固定完整512维单位q cosine top16 fit查询、温度0.05加权遗漏叶票选三叶，只在原dev/cal算覆盖，另有普通GT与全局遗漏先验对照；不是线上原metric变更、强教师、完整合并或QPS。角色、原输入152项SHA、144支持行/2232深度行/120探针行和数值修正日志独立保存。该诊断版本的后继设计不属于其当时API；当前共享教师/表示压缩/路径训练实现另见4.18，未引入生产默认。

### 4.18 E202共享表示残差（已实现，四集正式测量完成）

[独立工作区](entry_method_exploration/20261117_shared_residual_value_v1/README.md)在E201目录上增加共享节点编码、128维教师与32/64维学生，四集544点/1088两遍CPU15/T1正式测量完成。该模块未替换原search_new和生产默认。452项正式源/模型/运行依赖冻结；身份、训练和数值资格见[协议](entry_method_exploration/20261117_shared_residual_value_v1/protocol.md)、[冻结](entry_method_exploration/20261117_shared_residual_value_v1/formal_freeze.json)及[方法说明](entry_method_exploration/20261117_shared_residual_value_v1/analysis/method_and_limits.md)。

节点特征为原base子树完整均值/std及规模、深度、范数摘要，离线经共享编码器导出逐节点数组。教师完整query+四个摘要、K独立头；学生一次query投影加状态调制。只保留D0、末首差、logL、query范数，没有旧QR3的局部R占比、画像距离及显式几何先验。层内绝对价值评分，最多64内部展开/128子评分，beam1/2/3叶对应至多32/64/96个原metric精算，排除R/重复ID后稳定合并。无新导航、主图恢复、自动门或B32联合。

原生标签用原DistanceComputer精算叶并实际合并得到净命中；已知叶负值下限-1，内部节点取已知叶最大正收益，未精算全部无GT困难叶。fit/dev/cal按身份隔离，dev以六状态三叶真实净增量/支持上界宏平均选checkpoint。每4epoch刷新beam困难节点，首次从epoch5使用；四集最终S32均选epoch3/4，未直接经历该阶段。q-only和普通GT控制的监督/容量/轨迹差异另见方法说明，不能当单一因素因果消融。

正常完整timer包括旧六数组和全部方法统一8字段trace的分配/复制/销毁及所有查询流程；加载、GT、压缩、保存、oracle在外。实际线程1，QPS为两个N/wall算术平均。资格43,008模型路由/49,152排序合并/6,144旧主包通过，正式1,680,000次排序合并、544点Recall与1088计时、380救损配对、有限前沿及archive SHA由不同实现复核。校验边界见[交付收据](entry_method_exploration/20261117_shared_residual_value_v1/reviews/delivery_validation.json)。

临时评估路径和离线固定层起点缓存两项修正保留原件；缓存前后49,152采样节点/RNG及六轮训练前缀完全一致。COCO/WebVid复用旧目录和主返回，Flickr/Yandex同机制新建；大产物主存储/root/acsg-e202-storage，两个离线TQ128数组以SHA及逻辑链接放在/data/acsg-e202-secondary。/dev/shm仅为可重建缓存。模型组件字节与所有方法共加载RSS分列，不称单模型部署RSS。费用、默认判断读[summary](summary.md)，后继只读[s-target](s-target.md)。

### 4.19 E203 查询残差双原型（已实现，两集正式比较完成）

独立实现目录：[E203](entry_method_exploration/20261117_residual_query_prototypes_v1/protocol.md)。保留 E201 树、QR3 的每个分支概率和累计 logprob。在候选子节点加共享的 K1/K100 两头、18 特征线性校正；校正不累计到下一层的 QR3 prior，零权重可恢复旧 QR3。STATE 只用前12特征（prior、深度、D0/gap、profile min/gap、L、局部 R 占比、完整 q 投影与 base 中心相似度/兄弟差），PROTO/HARD 再用6项残差查询原型/事件计数特征。

query 用 fit-only 归一化 query 的二阶矩特征向量作无中心 PCA 512→32 投影，投影后归一化；base 中心只用 base。原型每节点最多64条 fit 查询的确定性 bottom-hash 样本、5轮双中心聚类；事件计数按 fit 单叶真实正净收益累加。训练按身份哈希两折，只访问另一折原型；dev/cal/test 使用全 fit 原型。三版本各8epochs，HARD从第一轮使用真实当前三束竞争节点，dev在epoch0/2/4/6/8经原生三叶精确合并选择，cal仅报告。

实现见[src/prototype_core.hpp](entry_method_exploration/20261117_residual_query_prototypes_v1/src/prototype_core.hpp)、[train.py](entry_method_exploration/20261117_residual_query_prototypes_v1/scripts/train.py)。full-q top16近邻 teacher 只在dev/cal验证真实合并，不蒸馏、不上线，也未加入状态条件的相似度。树未重排。线上仍原主搜索→投影/分支校正→三叶→去重排除主返回→原 metric精确评分/稳定合并；≤64展开/128子节点分数/96补点全部计入完整wall。

两集 COCO/WebVid，强控制 GT10/B32 两K密集L，SQ/QR3/E202 S32和3个新版本在L100/200/400；236点/472批，每点两遍CPU15/T1。root/data分盘保存、gzip无损压缩；shm仅重建缓存。资格、冻结、原始返回、timing、独立审计和历史原件各自保留。两集236点/472批已完成，默认E99保持；正式结果见[报告](entry_method_exploration/20261117_residual_query_prototypes_v1/report.md)。全零权重头直接复用旧QR3、trace rank记0，资格专用ZERO仍走完整Core验证。

### 4.20 E204 固定 B32 表上的逐查询预算分配

[原生 runner](entry_method_exploration/20261119_residual_budget_allocation_v1/src/benchmark.cpp)复用 E200 的图、GT10、原始精算及完整 B32 快速路径和 E203 的 REUSE-SQ。原 B32 三行内按已有序列选前缀。以画像距近到远、ID 打平确定三个配额对应关系，汇合时仍沿原入口顺序。十个动作每路8–32，步长8，总表位48。候选排除原主返回，全局去重，按原metric严格合并。B8/完整 B32 为24/96表位控制，实际精算另记。

[拟合](entry_method_exploration/20261119_residual_budget_allocation_v1/scripts/fit.py)只访问原合法角色 fit，按数据集和K固定正则的多输出线性 ridge 学相对均分的实际净命中，使用画像及主返回共11个特征。特征中的表内重合计数及在线推断计入完整 wall。原B32完整16K监督差异保留。标签从原合法训练主包与相同DistanceComputer重放全排序导出。正式 native 不装入测试GT与训练标签。两集正式COCO/WebVid，144点、288个完整CPU15单线程批次，288万查询，真实K1/K100，每点两遍。计原六数组及统一两列 trace 生命周期，保存首批实际包和第二轮SHA，正式后独立排序与 stdlib 重算。结果及收益边界读[报告](entry_method_exploration/20261119_residual_budget_allocation_v1/report.md)和[冻结](entry_method_exploration/20261119_residual_budget_allocation_v1/formal_freeze.json)。

### 4.21 E205 公共前缀分数（离线诊断）

[实现](entry_method_exploration/20261120_residual_prefix_signal_v1/src/replay.cpp)重用 E204 原 action、metric 和真实训练主包。B32-FIT 按身份只取 fit K100/L200 的真实遗漏，
用原 e183 编译器构建 8→16→32 嵌套表。完整16K B32 另作角色交叠兼容诊断。每路前8项排除主返回并共享精确分数，
新增可评分个数、优于原主第K名的数量及最佳分数差九维。按数据集和 K 用 fit 拟合 E204 同样的 ridge，目标为实际 Top-K
净命中。真实 K1/K100、L100/200/400 各保留全动作收益及精算记录。原十一维和同条件全部标签与 E204 逐字节一致；
独立 stdlib 核 witness 的精确分数派生和稳定排序。公共测试未用于本阶段。四个 L100 单元均未达到[预锁继续条件](entry_method_exploration/20261120_residual_prefix_signal_v1/protocol.md)，
当前没有该选择器的正式计时路径或生产 API。详情见[报告](entry_method_exploration/20261120_residual_prefix_signal_v1/report.md)。

### 4.22 E206 较小预算监督的固定 B32 表

[实现](entry_method_exploration/20261120_residual_budget_matched_table_v1/src/study.cpp)重用原 GT10 K1/K100 主搜索、原 B32 exact 合并及 E191 REUSE-SQ。读取 L184/L192 实际训练主返回与冻结 L200 主包。编译器在 [common.inc](entry_method_exploration/20261120_residual_budget_matched_table_v1/src/common.inc) 接受真实教师 L，其他原始单位事件、并列规则及嵌套8→16→32编译合同一致。两张表只使用同 fit K100，均为 M5POST1 同布局。冻结的 L200 对照与 E205 的 8/16/32表逐字节一致。

训练及回放不读取公共测试。缺口按全局源、三路未截断、三路截断和最终输出分别记录。每个数据集/K 的 L184 提交条件固定。通过的 WebVid K100 用原公共10K查询，从原 GT10、完整 B32、两个 fit 表及 REUSE-SQ 运行完整批次，计六数组生命周期。CPU15/T1、32点/64批，返回包首轮存档并与第二轮逐字节核验，原生独立合并后另核数学统计。公共 GT 仅正式计时完成后评价。生产路径与发布配置采用既有合同，结论见 [E206报告](entry_method_exploration/20261120_residual_budget_matched_table_v1/report.md)。

### 4.23 E207 原 B32 补点分段测量

[诊断 runner](entry_method_exploration/20261120_b32_stage_cost_v1/src/profile.cpp)直接复用 E206 的 normal GT10/B32。同 K/L 的分段副本沿原查表去重、原额外距离核和严格原合并，分别记原始ns。独立无计时诊断提取保留池第 K 名之后的有效候选，排除暂存槽，记录精确距离逐比特重合和门槛。正常和分段计时各自计入完整六数组生命周期。额外计数不计入正常路径。仅公共前3072条，CPU15单线程，真实K1/K100，报告[结果](entry_method_exploration/20261120_b32_stage_cost_v1/report.md)。公共GT在全部测量完毕后用于复算。生产调用沿既有合同。

### 4.24 E208 B32 等价候选预取及合并快路径

[实现](entry_method_exploration/20261120_b32_equivalent_speed_v1/src/benchmark.cpp)沿原 E206 未插桩 GT10/B32作控制。PF4 在已去重候选中提前4个预取同一 Flat 存储，余下精算沿原标量计算。SKIP 仅真实K100，全部精算并核严格原门槛后决定是否构建合并堆。通过门槛的分支沿原完整排序规则，异常输入用原回退。BOTH 合用。四集各3072条固定，真实K1/K100，L100/200/400，96点/192完整两遍T1，所有新版本返回与原 B32 字节相等。生产路径沿既有合同。见[实测](entry_method_exploration/20261120_b32_equivalent_speed_v1/report.md)。

### 4.25 E209 WebVid 当前链路的 SPAN4 适配与补点复测

[实现](entry_method_exploration/20261120_webvid_b32_span_confirmation_v1/src/benchmark.cpp)重接 E102 研究内核 search<true,false,true> 到 E208 Router／原标量控制与完整B32。原图内每节点预计算一个末有效邻接位置字节，原存储 DistanceComputer 用四路精算，保留候选、预取和插入次序。原 B32 与 E208 PF4/BOTH 在 E194确认窗复测；SPAN4 在确认及公共窗配套比较纯主搜索及原B32。范围固定 WebVid、本协议两K七预算。完整包返参、独立归并、真实batch4调用与计时合同核验见[结果](entry_method_exploration/20261120_webvid_b32_span_confirmation_v1/report.md)。生产入口沿E99合同。

### 4.26 E210 四集当前图的 SPAN4 等价复测

[适配](entry_method_exploration/20261120_span4_four_dataset_retest_v1/src/benchmark.cpp)沿 E209 span+batch4，E208 四集原图和同一GT10画像、raw-IP、完整B32。两条路径分别计普通主搜索与附带原B32。真实K1/K100各7档L，公开前3072固定，原/新方法224点与448次两遍完整单线程。阶段计数不带入正常时钟，GT在正式结束后分析；冻结资产、实际返回、历史前缀、配对工作量、附加span开销和图见[报告](entry_method_exploration/20261120_span4_four_dataset_retest_v1/report.md)。生产路径按E99合同。

### 4.27 E211 GT10 正式入口与默认替换

[生产实现](ACSG/ACSG.cpp)的 SPAN4 在同一 `search_new(mode=2)` 下和标量做 A/B。E210 原输入、真实K1/K100各7档L，四集224点448个完整CPU15单线程批次。112个新旧配对返回逐字节相同，112/112个配对通过逐点速度筛选。纯GT10完整QPS变化+13.74%至+28.35%，GT10+B32变化+13.16%至+27.94%。 完整候选池与 visited 逐条配对，独立 B32 合并与历史 E210 实际包交叉验证。发布版和正式 A/B 版源码差异为默认值。四集原生 batch4、三集 L2 标量及共享索引并发通过断言。参见[E211 报告](entry_method_exploration/20261120_span4_production_default_v1/report.md)与[发布构建产物](entry_method_exploration/20261120_span4_production_default_v1/release/)。

### 4.28 E212 四集 NSG 与三条 GT10 链路

[评测入口](entry_method_exploration/20261120_gt10_nsg_b32_four_way_v1/src/benchmark.cpp)链接 E211 发布静态库。NSG 固定使用原图入口及 SPAN4，新 GT10 使用原三入口及 SPAN4。新旧补点版共用原完整 B32，旧版显式关闭 SPAN4。四集真实 K1/K100 各7 L，每点两遍 CPU15/T1，完整 wall。保存各点首轮返回包、两轮时间、输入与发布库冻结，计时结束后评估。对比见[E212 四集对比](entry_method_exploration/20261120_gt10_nsg_b32_four_way_v1/report.md)。

### 4.29 E213 四集 GT10+B32、NSG 与 GATE

[评测入口](entry_method_exploration/20261121_span4_gt10_b32_nsg_gate_v1/src/benchmark.cpp)链接 E211 发布静态库并复用 E206 批处理。NSG 用同图的固定单入口，GT10+B32 用 E212 的路由和完整表，GATE 用 E200 冻结的 512 hub、W 和小 HNSW。GATE 路由按单位 query、真实 ID 映射和 heap-pop 次序执行，原 query 随三入口传给 `search_new(mode=2)`。主比较各臂启用 SPAN4，另有 GATE 标量臂。独立链接的探针在四集 K1/K100/L200 验证实际 Faiss batch4 调用。正式程序用无探针构建，每点两遍 CPU15/T1 完整 wall，保存首轮返回，计时后核对 GT 和历史包。见[预锁协议](entry_method_exploration/20261121_span4_gt10_b32_nsg_gate_v1/protocol.md)和[封存](entry_method_exploration/20261121_span4_gt10_b32_nsg_gate_v1/seal.json)。

### 4.30 E214 B32 候选四路精算

[实验入口](entry_method_exploration/20261121_b32_batch4_scoring_v1/src/benchmark.cpp)链接 E211 发布静态库，主图统一采用 SPAN4。四路版复用 E206 查表去重，按原候选次序每四个用 `DistanceComputer::distances_batch_4` 计算 raw-IP 距离，余项逐个精算，沿原严格门槛与合并。标准 Flat raw-IP、固定原表，实验工作区复用原候选数组并用四个临时分数。正式 168 点、336 批。每配置先对首 256 条校验候选精算位元及结果。L200 补点重放复用正式纯 GT10 包，移出正式 wall。见[合同](entry_method_exploration/20261121_b32_batch4_scoring_v1/protocol.md)及[封存](entry_method_exploration/20261121_b32_batch4_scoring_v1/seal.json)。

### 4.31 E215 小 L 补点候选的离线回放

[尾部回放](entry_method_exploration/20261121_b32_cross_budget_tails_v1/src/study.cpp)绑定 E206 同一 fit/dev/cal 及真实 K1/K100 的 L184、L192 原包。保留每行原表最多 16 个前缀，以 fit K100/L184 真实遗漏编两套加权尾部，三路 27 动作逐查询实际计分数受原 B32 限制。[近邻回放](entry_method_exploration/20261121_b32_cross_budget_tails_v1/neighbor_source/protocol.md)从完整单位 query 离线取 16 个 fit 邻居，按遗漏 ID 倒数名次投票；保留各路公共前缀，固定最多替换 8/16 个原表尾部候选，回放实际原 raw-IP 且计分数逐查询相同。E211 发布库提供 DistanceComputer。候选上限和逐查询最优动作读取 GT，结果只属于离线。64,000＋15,906 个状态，正式 QPS 点为 0。见[报告](entry_method_exploration/20261121_b32_cross_budget_tails_v1/report.md)和[封存](entry_method_exploration/20261121_b32_cross_budget_tails_v1/seal.json)。

### 4.32 E216 在线相近查询的直接补点

[索引准备](entry_method_exploration/20261121_neighbor_residual_online_v1/scripts/prepare.py)使用独立 fit 查询、其 K100/L184 真实遗漏和 64 维非中心 PCA。VOTE 用 ef32 小 HNSW 取 32、原空间重排取 16、实时对遗漏 ID 投票。CACHE 用 ef16 取 4、重排取 1、取该 fit 查询预编表。两者保留各路 fit-B32 前缀，去重并排除主返回及固定表候选，最多替换 16 个尾部 ID，实际精算数逐查询相同。[在线实现](entry_method_exploration/20261121_neighbor_residual_online_v1/src/residual.hpp)共用原四路 raw-IP 精算和严格 Top-K 合并。主图用 E211 发布库。完整计时 160 点、320 批，另有同查询窗局部加密 59 点、118 批。两阶段分别计量，正式壁钟包含在线邻居查找、重排、投票和查表。[主协议](entry_method_exploration/20261121_neighbor_residual_online_v1/protocol.md) · [加密协议](entry_method_exploration/20261121_neighbor_residual_online_v1/confirmation.md) · [封存](entry_method_exploration/20261121_neighbor_residual_online_v1/seal.json)。

### 4.33 E217 GT10 入口桶的补点候选回放

[模型构建](entry_method_exploration/20261121_gt10_bucket_residual_v1/scripts/experiment.py)依据 E206 K100/L184 的 fit 三路入口建立桶，每桶贪心最远点选择实际 fit 代表。每入口取前 4/8 个，合并去重，定长全维点积选一个，读 E216 预编表。按原前缀、尾部至多 16 替换、逐查询相同实际精算数、四路精算与严格合并执行。COCO/WebVid 真 K1/K100 训练角色 [回放](entry_method_exploration/20261121_gt10_bucket_residual_v1/src/benchmark.cpp) 和 [整桶动作枚举](entry_method_exploration/20261121_gt10_bucket_residual_v1/src/oracle.cpp) 分离，后者使用训练 GT 确定上限。[协议](entry_method_exploration/20261121_gt10_bucket_residual_v1/protocol.md)及[报告](entry_method_exploration/20261121_gt10_bucket_residual_v1/report.md)记录正式阶段的资格与结果。

### 4.34 E218 入口桶净命中选择和双表上限

[建模](entry_method_exploration/20261121_bucket_gain_selection_v1/scripts/prepare.py)按 fit 身份三折重建 K100/L200 固定 B32、K100/L184 预编遗漏表、BKT8 代表和 16D 摘要。留出 fold [逐动作标签](entry_method_exploration/20261121_bucket_gain_selection_v1/src/replay.cpp)用实际同预算四路精算与 Top-K 净救回，固定线性回归分别使用余弦/入口、主返回重合、候选摘要。最终回放用冻结全 fit 目录。预测非正走同池 B32。WebVid K100 离线同预算枚举每表至多 8 个、扣除已有 ID 的双表动作，使用 memoized exact 与原生 batch4 抽样核对，单表上限核对 E217。计量和范围见[协议](entry_method_exploration/20261121_bucket_gain_selection_v1/protocol.md)。

### 4.35 E219 漏点 ID 粗排与 B32 尾部保留

[编码](entry_method_exploration/20261121_bucket_id_reranking_v1/scripts/prepare.py)以原向量逐行对称 int8 仅编码 E217 缓存和 fit-B32 ID。[实现](entry_method_exploration/20261121_bucket_id_reranking_v1/src/rerank.hpp)三路桶查前2/4代表、每表最多16个新 ID，排除主返回和原固定候选。对新点与原非前缀尾部跑 512D VNNI 内积，替换粗分较低的原尾部最多16个。原始列表实际精算数不变，使用 E216 原距离四路精算、严格 Top-K。EXACT2/4 为仅回放的同池原 IP 诊断。正式第二公共窗、配置和独立复核见[协议](entry_method_exploration/20261121_bucket_id_reranking_v1/protocol.md)与[报告](entry_method_exploration/20261121_bucket_id_reranking_v1/report.md)。

### 4.36 E220 Q8 等价优化

[热路径](entry_method_exploration/20261121_q8_equivalent_speed_v1/src/rerank.hpp)固定 E219 候选生成和评分，分别验证错误消息在失败分支才构造、在两列排序上 `nth_element` 后按原规则仅排前至多16名，以及合并版。[运行器](entry_method_exploration/20261121_q8_equivalent_speed_v1/src/benchmark.cpp)独立分段、验证浮点精算及正式全路径。WebVid K100 扩表为两/四表真实 Top-K 结果离线组合，开发窗拟合并锁定阈值。见[协议](entry_method_exploration/20261121_q8_equivalent_speed_v1/protocol.md)。

### 4.37 E221 Q8 粗分保守上界

[证书准备](entry_method_exploration/20261121_q8_certified_pruning_v1/scripts/prepare.py)对 E219 原 ID、向量与 int8 码计算 `||x||` 和量化残差范数向上值。[运行](entry_method_exploration/20261121_q8_certified_pruning_v1/src/rerank.hpp)沿 E220 作整套候选交换，只对留下且有粗分的候选按实际 q 编码误差考虑原 IP 的 FP32 舍入余量。上界严格低于原主返回第 K 名才不读取原向量，原 B32 前缀直接精算。余下候选保持原顺序，四路精算与严格合并沿旧代码。两个 K100 场景及 WebVid K1 分开冻结与计时；全部查询输出和回放拒绝见证见[报告](entry_method_exploration/20261121_q8_certified_pruning_v1/report.md)。

### 4.38 E222 B32 组内联合短尾表

[实验实现](entry_method_exploration/20261122_joint_residual_tail_v1/src/benchmark.cpp)复用 E217 三入口代表目录、E206 身份角色和 L184 的 K100 实际返回。fit 归组排除同身份代表，候选为组内 fit 遗漏并集。按原生 raw-IP 精算和最终 Top-K 净正确成员贪心构建 8/16 位嵌套表，在线只读选中的单表。保留 B32-fit 的每行前 16 位公共候选，实际新增候选与移出非公共尾部一一配对，逐查询保持实际精算预算，按原距离合并。模型文件为每代表一行的 offset/ID 数组。COCO、WebVid 冻结为真实 K100 同期单线程测量，公共 GT 仅用于计时后评分。见[协议](entry_method_exploration/20261122_joint_residual_tail_v1/protocol.md)和[封存](entry_method_exploration/20261122_joint_residual_tail_v1/seal.json)。

### 4.39 E223 单组全池逐查询残差交换

[实验代码](entry_method_exploration/20261122_group_residual_rerank_v1/src/benchmark.cpp)从 E222 fit 归组及实际 L184 遗漏重建每代表的完整候选池，线上复用代表选择。排除主返回和已有 B32-fit ID，按分数最多交换 16 个非前缀尾部，保留最终实际精算数。两集 FULL-IP 用原生完整内积额外给新点和可换旧点评分，费用单列。COCO P32/P64 采用 E216 冻结的非中心 PCA 方向，预计算原向量的 FP32 投影，查询每条投影一次。粗分决定交换，原生 raw-IP 决定最终 Top-K。WebVid 的全池全精度结果仅来自留出回放。COCO 准入、分流和完整计时见[协议](entry_method_exploration/20261122_group_residual_rerank_v1/protocol.md)及[封存](entry_method_exploration/20261122_group_residual_rerank_v1/seal.json)。

### 4.40 E224 B32/P64 查询分流

[实现](entry_method_exploration/20261122_p64_residual_gate_v1/src/benchmark.cpp)复用 E223 的主索引、原版 B32、P64 及原生 raw-IP 精算和 Top-K 合并。GT10 主返回后，从画像分数和前后段原返回分数抽取 11 维信号，固定线性模型与浅树按 L 使用校准阈值。门关闭完成原版 B32，门打开完成原版 P64；代表查找与向量投影只在 P64 分支执行。模型由 E223 第二公共窗按身份拆 fit/cal，正式第三公共窗 3,072 条此前未用于此门标签或阈值，属于历史曾用的公共数据。输出逐查询与独立复算的门选择和两条实际分支核对。见[协议](entry_method_exploration/20261122_p64_residual_gate_v1/protocol.md)与[封存](entry_method_exploration/20261122_p64_residual_gate_v1/seal.json)。

### 4.41 E225 P64 候选探针

[实现](entry_method_exploration/20261122_p64_candidate_probe_v1/src/benchmark.cpp)复用 E223 的候选组和 64 维代码。每组最多八个探针 ID，优先保留 E222 短表前四个，余量按完整组排序的位置补足。跳过主返回与 P64 原 fit-B32 已有 ID。查询投影和探针粗分提供七个新特征，和 E224 的 11 维主搜特征拟合净收益。启用后按 ID 顺序复用已算粗分及查询投影，使用原 P64 交换和精算；关闭走完整 B32。训练、校准和正式窗身份隔离，B32/P64 回放与在线分支逐条位级核对。见[协议](entry_method_exploration/20261122_p64_candidate_probe_v1/protocol.md)和[封存](entry_method_exploration/20261122_p64_candidate_probe_v1/seal.json)。

### 4.42 E226 B32/B64 双塔直接补点

[独立研究实现](entry_method_exploration/20261122_b32_b64_two_tower_v1/src/benchmark.cpp)复用 E183 原版 B32 表、E211 SPAN4 与对应 GT10 路由。B64 编译按原 K100/L200 漏点 token 的联合未覆盖贪心续填到每行至多 64，保留每行有序 B32 前缀。三入口行取并集，去重并排除主返回。两池的查询塔和候选塔分别为无偏置 512→32 线性映射，候选码离线存储。在线将查询投影一次，对对应池作 32 维内积短排，正式精算至多 48 个候选，按原生 raw-IP 与严格 Top-K 规则合并。PCA 使用同拟合查询和同精算预算。角色、原生回放、正式 K100 计时和审计见[协议](entry_method_exploration/20261122_b32_b64_two_tower_v1/protocol.md)。生产搜索合同仍按 E99/E211。

### 4.43 E227 B32 截止分双塔

[独立研究实现](entry_method_exploration/20261122_b32_cutoff_two_tower_v1/src/benchmark.cpp)沿用真实 GT10、SPAN4 和原版三行 B32。双塔独立作 512→16 线性映射，候选离线编码，表内 posting 预绑定短码槽。查询用转置 FP32 权重做在线 SIMD 投影。以真实原内积作回归目标，对原版 B32 实际补回的真值成员加罚。以主返回第 100 名原生内积分数减校准余量为选择阈值，一趟保留超过阈值的候选，按原顺序四路精算、严格 Top-K 合并。筛剩小于 16 个会恢复整池。第二公共窗训练与复核，第三公共窗真 K100 正式测量。见[协议](entry_method_exploration/20261122_b32_cutoff_two_tower_v1/protocol.md)及[封存](entry_method_exploration/20261122_b32_cutoff_two_tower_v1/seal.json)。

### 4.44 E228 全精算 B64 异窗复测

[复测实现](entry_method_exploration/20261122_b64_full_confirmation_v1/src/benchmark.cpp)冻结 E226 发布 SPAN4、两集路由、原版 B32 和 B64 扩表。B64 三路行去重、排除主图返回，在原顺序使用四路 native raw-IP 与严格 Top-K。原版 B32 使用原路径。由冻结物理行清单绑定官方 GT100。COCO 按源组身份审核，WebVid 按精确查询向量及官方角色审核。每集 20 个 L，独立原生标量核验，同档两遍完整 wall。见[协议](entry_method_exploration/20261122_b64_full_confirmation_v1/protocol.md)及[封存](entry_method_exploration/20261122_b64_full_confirmation_v1/seal.json)。

### 4.45 E229 四集真 K1/K100 全精算 B64

[正式比较](entry_method_exploration/20261122_b64_formal_four_dataset_v1/src/benchmark.cpp)冻结 E213 的发布 SPAN4、四集主图、GT10 路由与原 B32。COCO/WebVid 复用 E226 B64，Flickr30k/Yandex 从原 E183 K100/L200 token 按同一 E226 联合未覆盖贪心续填到 64，逐行保持有序 B32 前缀。查询合并三路候选 ID、去重、排除真实主返回，按原序对所有剩余候选执行 raw-IP 四路精算及严格 Top-K。K1/K100 各自独立调用主搜索，分别记录 1/100 个返回。源组或精确向量隔离、冻结物理行绑定、正式网格与完整计时见[协议](entry_method_exploration/20261122_b64_formal_four_dataset_v1/protocol.md)和[封存](entry_method_exploration/20261122_b64_formal_four_dataset_v1/seal.json)。

### 4.46 E230 WebVid B64 入口配额

[复测实现](entry_method_exploration/20261123_b64_entry_budget_v1/src/benchmark.cpp)冻结 E229 WebVid 的 GT10 soft-t1、SPAN4、主图库、B32 和原 B64 表。新版真 K1 按三行各 56 项截取，新版真 K100 复用三路路由画像距离给最远入口 40 项，另两路各 64 项。画像距离相同时，原路由次序最后的入口拿 40 项。原三路迭代次序及原 B32 前缀保留，去重并排除主返回后做原生 raw-IP 全精算与严格 Top-K 合并。K100 内部有均匀 B56 的同原始配额对照。确认窗源身份按向量字节与 E229 和冻结 fit 分离。完整测量见[协议](entry_method_exploration/20261123_b64_entry_budget_v1/protocol.md)和[封存](entry_method_exploration/20261123_b64_entry_budget_v1/seal.json)。

### 4.47 E231–E239 WebVid B64 配额与精算复用（完成部分）

E231 把最远路上限扩成 40/48/52/56/60 并保留近两路原各 64。确认和开发使用原公共查询的独立物理行。E232 的最远入口特化表使用 E183 冻结真实训练遗漏扣除近路供给，重排与允许换入其它训练 ID 的两种尾表均保留有序 B32 前缀。E234/E236 在线用 GT10 画像和原主结果分数选择第三路 40/64，E236 允许六档，实际冻结模型只用 40/64。真实完整包、查询分工和离线校准依赖分别记录于原协议与封存。E238 在相同 B32/B64 有序行上用一个主结果分数选择三路嵌套配额，按真实精算量分别冻结匹配 Far40 与 Far52 的离线策略。E239 用缓存诊断主 L 分配，生产没有实现入口预选 L。

E233 只读已经完成的 SPAN4 visited，适用于同一查询、同一原生 raw-IP 核、原主搜索返回之后。visited 对应的非入选 Top-K 候选无需原 metric 重算，剩余候选在原行次序一次去重精算。保留仅改散列查插和同档原全精算对照。资格检查逐个核被跳过距离以及原生 Top-K 等价。实验实现保存在独立目录。

协议及实现见[E231](entry_method_exploration/20261123_b64_far_depth_sweep_v1/protocol.md)、[E232](entry_method_exploration/20261123_b64_role_conditioned_tail_v1/protocol.md)、[E233](entry_method_exploration/20261123_b64_visited_skip_v1/protocol.md)、[E234](entry_method_exploration/20261123_b64_tail_gate_v1/protocol.md)、[E236](entry_method_exploration/20261123_b64_tail_ladder_v1/protocol.md)和[E239](entry_method_exploration/20261123_b64_route_budget_v1/protocol.md)。

### 4.48 E243 WebVid B64 扩训练与多预算遗漏监督

冻结 E183 的 16,000 条及 8,192 条额外 WebVid 原 exact raw-IP 训练。查询精确字节排除原完整拟合、公共 test10K 与 seed validation10K。发布 SPAN4 训练端实际运行四档 L，给真实 K100 生成主返回。More64 只用 L200。Mixed64 用 L176/192/208 的 query–L–target 遗漏事件，沿 E226 原生联合贪心编译器从原有序 B32 各行延长到 64。在线版按 GT10 原三路顺序取候选，去重和排除真实主返回，沿原 raw-IP 四路精算并严格 Top-K 合并。Mixed52 仅截同 Mixed64 最远路到 52。分工、训练身份、边界验证及实际计时见[源码](entry_method_exploration/20261123_b64_multibudget_training_v1/src/benchmark.cpp)、[协议](entry_method_exploration/20261123_b64_multibudget_training_v1/protocol.md)、[封存](entry_method_exploration/20261123_b64_multibudget_training_v1/seal.json)。

### 4.49 E237/E244/E245/E246/E247 新尾表验证与迁移

E237/E244 在 WebVid seed validation exact raw-IP GT 的两个 3,072 条身份窗以精确向量字节排除完整旧训练、E243 扩训及公共测试，两个窗口互斥。E237 直接用冻结 More64/Mixed64，另保留 E234 分流和原 B32/老 B64。E244 对原 B64、Budget40 和 Mixed64 各测原流程与同一个访问复用分支，所有对应 Top-K 逐字等价。读取训练 GT 的时机与测试计时分离。

E245 在 COCO GT10 hard、同实际图和 exact raw-IP 上，用 16,000 条原真实拟合和 4,096 条按源组及精确向量隔离的额外数据重编；E229 3,072 原确认源组固定。编译及线上合同同 E243。E246 WebVid 真 K1 直接冻结 E243 表，训练仍为 K100，在线真实 K1 单独调用和合并，评分读取准确 GT 的首名。E247 沿 E243 同样本和四档原生缓存输出，用同 E226 编译器构造 L176/192/200/208 四个单档与多档对照。细节见[E237](entry_method_exploration/20261123_b64_external_validation_v1/protocol.md)、[E244](entry_method_exploration/20261123_b64_equal_fastpath_v1/protocol.md)、[E245](entry_method_exploration/20261123_coco_b64_multibudget_training_v1/protocol.md)、[E246](entry_method_exploration/20261123_webvid_k1_b64_trained_table_v1/protocol.md)、[E247](entry_method_exploration/20261123_b64_teacher_depth_ablation_v1/protocol.md)。

### 4.50 E242/E248/E249/E250 整数 L、同样本编表及近阈值复测

E242 与 E249 冻结旧策略与模型，仅在原确认窗和原在线真 K 值下细化主搜索 L。E248 复用 E245 同一批实际 COCO 主包，按 E247 的四单档对照方案重编三张新单档表。E250 冻结 E248 的强单档和多档，重测 97% 附近完整时间。均检查历史交叠配置的同查询原生 ID、距离、入口和画像字段。详见[E242](entry_method_exploration/20261123_b64_dense_target_v1/protocol.md)、[E248](entry_method_exploration/20261123_coco_b64_teacher_depth_ablation_v1/protocol.md)、[E249](entry_method_exploration/20261123_webvid_k1_b64_dense84_v1/protocol.md)、[E250](entry_method_exploration/20261123_coco_b64_target_retest_v1/protocol.md)。本轮实验状态由[完成收据](entry_method_exploration/20261123_b64_until1300/closeout.json)记录。

### 4.51 E251 四集三方法同期复测

E251 独立 runner 链接 E211 发布 SPAN4，冻结 E229 四集图、底库、GT10、原 B32、老 B64 与公开评测身份。直接读 E243/E245 封存表，另用 Flickr30k 原 profile 排重 4,096 个源组和 Yandex 排重官方 router_train 8,192 条扩训。原 E183 补点训练、实际 K100 三档漏点及原生 E226 联合覆盖续填至 64。三种方法的在线合并合同见[源码](entry_method_exploration/20261123_b64_four_dataset_retest_v1/src/benchmark.cpp)。真 K1/K100 完整计时、两次重复与逐字段历史校验见[协议](entry_method_exploration/20261123_b64_four_dataset_retest_v1/protocol.md)及[封存](entry_method_exploration/20261123_b64_four_dataset_retest_v1/seal.json)。

### 4.52 E252 经典 L2 的 Mixed64 迁移

[独立 runner](entry_method_exploration/20261123_b64_classical_retest_v1/src/benchmark.cpp)在 Deep10M、BIGANN-SIFT10M、GIST1M 冻结的 E183 底库与 NSG 图上统一走 E211 发布库的 L2 标量主搜索，B32 用 E206 原标量精算，Mixed64 用同一距离计算器精算三路去重后的候选，排除主返回成员。E197 的路由家族与原 JOINT32 不变，各增补 8,192 条有 E97 原平方 L2 标签的 learn 查询，采 L176/192/208 真实 K100 遗漏，由 E226 编译器延长前缀。真 K1/K100 两遍及公开 GT 不进入计时的合同见[协议](entry_method_exploration/20261123_b64_classical_retest_v1/protocol.md)、[输入锁](entry_method_exploration/20261123_b64_classical_retest_v1/inputs.json)和[封存](entry_method_exploration/20261123_b64_classical_retest_v1/seal.json)。

### 4.53 E253 经典 L2 的三方法同期比较

E253 [runner](entry_method_exploration/20261123_gt10_b32_mixed64_classical_v1/src/benchmark.cpp)冻结 E252 的底库、图、路由、评测身份、L 网格和两个补点表。纯 GT10 返回实际标量主搜索 Top-K，B32 与 Mixed64 使用原 E252 在线路径。三方法共用计量与 CPU15 单线程，每点两次正式批次。正式返回经 E252 逐字段对照，随后使用原冻结公开 GT 统一计分。[协议](entry_method_exploration/20261123_gt10_b32_mixed64_classical_v1/protocol.md) · [封存](entry_method_exploration/20261123_gt10_b32_mixed64_classical_v1/seal.json)。

## 5. 指标、计时与证据

- 新评测仅真实K=1/K=100。Recall@K为GT_K与返回Top-K集合交集除以K；K1必须实际返回首名命中GT1。旧Recall@10不改名复用。
- 当前用户所指K100查询失败严格为Recall@100<10%，即与GT100交集0–9个，恰好10个排除；失败率分母为同集/方法/L全部query，必须逐L报告。原低召回中命中数增加与升至≥10%分别计为“有所改善”与“脱离低召回”，零分母记无定义。未满100/少于90、完整恢复、成员救损是另外的辅助指标，不能替代本失败率。
- 正式性能统一单方法串行、实际threads=1，OMP/BLAS/MKL/NUMEXPR=1；CPU/亲和性和实际线程进收据。离线多线程另记，不能换算QPS。
- QPS用独立完整batch wall；E183包含正常Batch创建、初始化、路由、主搜、补点、统一六向量复制及正常销毁。加载、GT评分、hash、写盘、oracle和预热在wall外单列。
- E183首轮保存真实timed ID/距离/入口/画像分数，另两轮bits/SHA一致；POST与同K/L实际GT10主包的独立标量/线性合并oracle通过。零NDC布局不是0次距离，`counts_collected=false`。
- 三轮计时不是三份独立质量样本。曲线保留真实L、重复Recall分支；插值只作描述，不外推。独审范围以收据为准，不自动延伸到全部GT、bootstrap或因果。
- E183独审复算645点、1935轮、540救损、360覆盖、2088分层、360级联、3600频次及全部TRAIN源；未独立重算bootstrap、折线和全部实际greedy序列。

## 6. E184诊断artifact

`analysis/query_metrics.csv`和各集NPZ按原query行对齐；含K1/K100 mask、频次和几何，另有覆盖链、四分位、秩相关、原遗漏数分层以及全部已有B32预算敏感性表。

几何按原squared L2/负IP float64重评分原GT100目标；每集PCG64 seed20261024抽8192个base，保存ID/样本向量SHA。背景z为`(背景距离均值−GT100距离)/背景标准差`，不是论文原始relative contrast；有效秩`tr(C)^2/tr(C^2)`来自中心化样本协方差，不是流形内在维数。每集8query直接验证距离矩。整库SHA继承E183，本次只核stat；小输入SHA前后核对。

`audit_integers.py`用stdlib set/Counter复核56K整数，不导入主analyzer/NumPy；`finalize.py`另核9项秩相关/14项条件差值。它们由同一执行者完成，不称独立人员审查。E184交付时的根文档身份和旧验收原件保留；后续文档整理另有[维护收据](experiment_history/_maintenance/20261024_current_state_cleanup_v1/README.md)，不在新布局回跑旧根文档suffix门。

[五页低于10%全L修正版PDF](reports/20261024_failure_rescue_residual_lt10_v2/README.md)从E183原GT及实际raw/ids.i32逐条复算147个K100点；固定原家族与B32，输出逐L失败、成对改善/脱离/新增、全命中分布、低召回query行、跨L逐query转移与完整QPS引用。`per_query_hits.npz`按原query行对齐；恰好10命中单列。第二份stdlib set/array实现核验全部点和98组配对，属于同执行者不同实现；输入SHA前后核对。输出矢量PDF、PNG/SVG、实际PDF渲染及交付收据。旧六页版未满100口径保留原件；未重测性能或改原实验manifest。

[2026-11-05低召回三阶段记账](reports/20261105_low_recall_stage_attribution_v1/README.md)只读上述NPZ/原147点与98配对，生成49组三阶段、392种状态计数、低召回query索引和两阶段完整指标引用。分别统计NSG→GT10与GT10→B32的救出/新增/净变化，再将B32救出分为原NSG遗留及GT10新增来源；不同阶段分母分别保留。另用stdlib原GT/实际timed ID包重新复算全部147点及新分解，原163项输入SHA保持。四多模态为主，七集旧结果附录；只生成文字/CSV/PNG/SVG，不做PDF或新增搜索/GT/训练/计时，不修改API、metric、主核或旧封存。几何迷失仅为用户指定低召回标签，不作成因判定；同L记账不代表等费用获胜。

## 6.1 E185流形相关几何探查

[entry_method_exploration/20261024_manifold_residual_probe_v1/](entry_method_exploration/20261024_manifold_residual_probe_v1/report_zh.md)只读旧角色/GT/主返回。每集PCG64 seed20261025取512条：GT20/50/100目标向量中心化Gram谱计算局部participation ratio；该量不是流形维数。对合法16K训练query的最近query，L2原平方欧氏，IP单位query余弦仅诊断，不改原raw-IP。配对随机/入口重合数匹配对照；单例层保留自身并报告。另对56K旧几何按命中段与残差频次四分位描述分层。输出逐query CSV/NPZ、Gram/SVD检查、二实现核验、图表与PDF。GT特征均事后，未实现线上门控或新准入规则；旧metric/计时合同不变。

## 7. 构建、来源与重跑依赖

工作区`/data/netg/ACSG`，解释器`.venv_cpu/bin/python`；C++17/本地Faiss CPU依赖。先核当前CMake cache、静态库、对象、源码补丁、编译参数和目标帮助，再配置构建。历史命令/绝对路径不等于可移植运行包，文档清理不触发构建或实验。

| 改变项 | 必须重新绑定或生成的下游 |
| --- | --- |
| base / metric / normalization / 图或kernel | 相应GT、图、模型、响应、计数、计时；具体依赖按是否兼容判定 |
| 训练角色 / GT / H / 画像公式 | hub/画像/小图及其下游响应、表和评测 |
| router图 / 参数 / ID映射 / 次序 | 入口、主返回、依赖其遗漏的表和评测 |
| K / L / 合并或计时边界 | 对应真实搜索结果、费用和比较 |
| 仅兼容汇总、绘图、说明 | 复用原科学数组，只重做派生产物 |

新版本保存协议、源码/配置/输入/模型身份、aligned实际返回、费用和状态；旧失败/修正/封存不回写。source-only、工具验收、质量通过、性能通过和默认替换是不同事实。未测成本写null及原因，嵌套费用不相加；历史冷启动/训练债不清零，旧预算不是新额度。

[E191详细PDF](entry_method_exploration/20261028_seven_dataset_scoring_v1/E191_七数据集_K1_K100_综合测试报告.pdf)（用户后续明确授权）。

E191当时新块表末4K不参与其拟合或配置选择；E193现另将其划分为独立门拟合/校准角色；旧GT10画像与旧B32仍继承各自合法历史监督，不能说末4K从未参与系统监督。
