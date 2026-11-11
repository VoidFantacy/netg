# ACSG 代码架构与实现契约

更新于2026-10-24。本文维护当前实现、输入/输出、metric、artifact及计量合同；结论见[summary](summary.md)，下一研究问题见[s-target](s-target.md)。详细历史模块合同已[归档](experiment_history/_maintenance/20261024_current_state_cleanup_v1/archive/spec.md)，原实现没有因文档整理被删除或改写。

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
