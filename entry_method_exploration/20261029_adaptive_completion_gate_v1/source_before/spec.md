# ACSG 代码架构与实现契约

更新于2026-10-29。本文维护当前实现、输入/输出、metric、artifact及计量合同；结论见[summary](summary.md)，下一研究问题见[s-target](s-target.md)。详细历史模块合同已[归档](experiment_history/_maintenance/20261024_current_state_cleanup_v1/archive/spec.md)，原实现没有因文档整理被删除或改写。

## 1. 当前主链与实现位置

```text
合法训练query/GT → QGT选择真实base入口H → GT10目标归属 → 单位query画像W
raw query → 画像Micro-HNSW → 三个真实base ID → 原NSG search_new(mode=2) → Top-K
残差研究分支：同一主返回 → 三行冻结posting去重/评分 → Top-K合并
GT只在训练监督或搜索返回后的评测层读取
```

GT10画像为`p_h=normalize(unit(x_h)+Σ_i a_ih unit(q_i))`；a来自训练GT前10个目标与真实hub的hard/soft归属，不是在线神经网络。GT10方法名的10与评测K独立。QGT按簇中query及其GT候选选择全局唯一真实ID，不等于质心GT1或GT全局投票。

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

[本轮详细PDF](entry_method_exploration/20261028_seven_dataset_scoring_v1/E191_七数据集_K1_K100_综合测试报告.pdf)（用户后续明确授权）。

新块表末4K不参与本轮拟合或配置选择；旧GT10画像与旧B32仍继承各自合法历史监督，不能说末4K从未参与系统监督。
