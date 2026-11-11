# ACSG 代码架构与实现契约

更新于2026-11-04。本文维护当前实现、输入/输出、metric、artifact及计量合同；结论见[summary](summary.md)，下一研究问题见[s-target](s-target.md)。详细历史模块合同已[归档](experiment_history/_maintenance/20261024_current_state_cleanup_v1/archive/spec.md)，原实现没有因文档整理被删除或改写。

## 1. 当前主链与实现位置

```text
合法训练query/GT → QGT选择真实base入口H → GT10目标归属 → 单位query画像W
raw query → 画像Micro-HNSW → 三个真实base ID → 原NSG search_new(mode=2) → Top-K
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

训练/验证/测试角色不混用。E183五集残差fit可共享原画像fit前16K；COCO/Flickr残差角色独立，须分别披露。已曝光公共测试不是新盲确认。LAION是历史迁移控制：其公共query与Web来源重合，不算独立第三query workload；本地图索引已清理，重放需重建，原数据/证据保留。

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
