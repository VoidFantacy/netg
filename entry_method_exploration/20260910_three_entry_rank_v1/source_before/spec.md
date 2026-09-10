# ACSG 代码架构与实现契约

> 架构与实现事实核对至2026-09-09（A+B模块已实现，用户指定五点单线程探索已验收完成）。本文只维护已实现架构、接口、数据/metric、artifact、计量和变更依赖。当前实验结论见[summary.md](summary.md)，下一阶段目标见[s-target.md](s-target.md)，历史实验概览与复盘入口见[s-experiment.md](s-experiment.md)。未实现的研究设想不得写成现有API。

## 1. 文档职责与事实优先级

四个主文件都位于项目根目录`/data/netg/ACSG/`：

| 文件 | 负责的唯一主问题 |
|---|---|
| `spec.md` | 代码怎样组织、接口/输入/输出/评测必须满足什么合同 |
| `summary.md` | 当前最近实验做了什么、得到了什么、结论到哪里为止 |
| `s-target.md` | 下一阶段先评估什么、探索哪些方向、如何进入/退出每个阶段 |
| `s-experiment.md` | 过去做过哪些实验、状态与一句话结论、到哪里详细复盘 |
| `experiment_history/` | 按实验家族保存详细复盘、版本修正和原始证据索引 |

事实优先级为当前源码/配置/manifest/实测产物，高于说明文档或旧记忆。遇到历史实验不确定、结论冲突或疑似重复路线时，必须由`s-experiment.md`进入对应详细卡片，再读卡片指向的协议、配置、gate、结果和修正记录；证据仍不足则明确标为未确认，不能只据概览或旧摘要推断。

未提交代码、旧日志/索引/模型/结果不得重置、清理或覆盖；新执行输出使用独立版本。旧报告中的spec章节号属于当时文档，完整版本保存在[本次整理前快照](experiment_history/_maintenance/20260908_document_reorganization/source_before/spec.md)，不能把旧编号套入本文件。

## 2. 已实现主链：Fast

```text
正式数据manifest + 冻结NSG
  ├─ 独立QGT 5K + exact GT100 → spherical k-means → 唯一真实base hub IDs
  └─ 独立prototype-train + GT1 → GT目标与raw hub的cosine归属
       → unit query累加 + unit raw-hub prior(weight=1) → normalize prototype
在线 raw query → prototype Micro-HNSW → real base IDs → search_new(mode=2) → top-K
评测层在搜索返回后读取GT并计算Recall
```

代码：[builder](benches/run/build_fast_entry_variants.py)、[EntryPointSearcher与评测入口](benches/test.cpp)、[索引包装](ACSG/IndexACSG.cpp)、[原搜索实现](ACSG/ACSG.cpp)。QGT是项目内Query Ground-Truth术语，QGT-Cover是启发式而非严格set cover；prototype是入口的query画像，不是节点原向量。

Fast的QGT-only分支不依赖ACO/DPC、逐hub probe标签、optimizer或Neural Router。通用`build_gt_basin_prototypes`内部元数据默认含`requires_aco_dpc=True`，QGT-only分支会覆盖为False；应读最终manifest及实际调用分支。`Asym-Neural/NETG_AsymHNSW`结果槽也可能承载闭式prototype，不能据名字判断在线有MLP。

历史正式Fast使用30K prototype-train；最近诊断及后续拟议对照使用router_train后20K重建的paired Fast。两者必须分别标记，不能把旧30K模型接入20K拟合链。训练时对query/GT目标/hub作的normalize不等于在线额外归一化：现有Fast将raw query送入Micro-HNSW，主搜索仍使用数据manifest规定的原IP。当前Micro-HNSW使用`InnerProductDistance=1-q^Tp`，库不自动归一化；因现有prototype为单位向量，对固定非零query的排序与cosine等价，但数值本身不能泛称L2或已归一化cosine距离。

## 3. 模块与入口

| 层/用途 | 代码或工具 | 实现边界 |
|---|---|---|
| 数据与配置 | [DataLoader](benches/datasets/DataLoader.hpp)、[settings](benches/datasets/settings.json)及各dataset manifest | manifest绑定split、metric、base和GT；文件名不能代替身份 |
| 索引/原搜索 | [IndexACSG](ACSG/IndexACSG.h)、[ACSG接口](ACSG/ACSG.h)、[ACSG实现](ACSG/ACSG.cpp) | 存储/距离、冻结邻接、visited、候选pool和入口消费 |
| Fast构建 | [build_fast_entry_variants.py](benches/run/build_fast_entry_variants.py) | QGT-only与其他历史变体按manifest分支区分 |
| 路由与通用评测 | [test.cpp](benches/test.cpp)、[per-query评测](benches/bench_per_query_recall.cpp) | 搜索器load/reset、真实ID映射、split/计时实际实现须验收 |
| oracle/trace诊断 | [bench_entry_oracle.cpp](benches/bench_entry_oracle.cpp) | GT只在诊断层；oracle不是部署路由 |
| Three-view评测 | [bench_target_basin_eval.cpp](benches/bench_target_basin_eval.cpp)及对应protocol runner | 历史组件保留；接口分离不代表旧wall边界全部合格 |
| 区域搜索组件 | [RegionalSearch.h](ACSG/RegionalSearch.h)、[test_regional_search.cpp](benches/test_regional_search.cpp) | 已实现独立队列语义，不能替代原kernel假称parity |
| 区域评测/门户 | [P2](benches/bench_hierarchical_eval.cpp)、[P3](benches/bench_hierarchical_eval_p3.cpp)、[portals](benches/bench_hierarchical_portals.cpp) | 历史实现与实验状态分开，详见历史07 |
| Fast根因诊断工具 | [诊断src说明](fast_router_diagnosis/20260908_v1/src/README.md) | 独立版本调用原kernel，工具验收不等于新方法 |
| C stage1 独立状态机/诊断 | [state_machine.hpp](entry_method_exploration/20260909_c_stage1_v1/src/state_machine.hpp)、[C2 runner](entry_method_exploration/20260909_c_stage1_v1/src/c2.cpp) | 仅独立mode2状态机；C1验收通过，C2为有限动作oracle，不含learner或正式QPS |

旧NETG链`NSG→ACO→DPC→probe labels→Router`仅作历史复现，详见[历史01](experiment_history/01_fast_and_legacy.md)。v4效用树、历史A/B独立R0及D稀疏标注仍未实现。新的A+B实验已独立实现自由低秩`W=P0+VZ`、slot→entry映射、联合trainer和micro-index，见本文件末节；它不是旧共享affine设计的原样实现。C R0本身保留设计未运行身份；新[C stage1](entry_method_exploration/20260909_c_stage1_v1/protocol.md)已独立实现状态机，不能将其验收写为已部署C策略。

## 4. 正式数据集契约

| 数据集 | WebVid-2.5M | Yandex official 10M/IP | LAION-10M/IP |
| --- | --- | --- | --- |
| key | `webvid2_5m_light_v1` | `yandex_t2i_official10M_ip_v1` | `laion10m_acsg_v1` |
| artifact version | `roargraph-webvid2.5m-ip-v1` | `yandex-t2i-official-first10m-ip-v1` | `roargraph-laion10m-unit-ip-acsg-v1` |
| base | 2,505,000 × 512 | first 10,000,000 × 200 | 10,004,480 × 512 |
| metric | inner product | inner product | inner product |
| normalization | source 近单位范数，不额外归一化 | none | base/query 逐行 L2-unit |
| QGT / prototype / validation | 5K / 30K / 10K | learn `[0,5K)` / `[5K,35K)` / `[35K,45K)` | seed 20260830 去重抽取 5K / 30K / 10K |
| held-out | public 10K | public 前 10K | public 10K |
| manifest | `benches/datasets/WebVid2.5M_light_v1/manifest.json` | `benches/datasets/YandexT2I_official10M_ip_v1/manifest.json` | `benches/datasets/LAION10M_acsg_v1/manifest.json` |

补充边界：

- WebVid、Yandex 四个 split 的六组两两 overlap 均为 0；Yandex GT 必须对应 first-10M base 的 exact IP top-100。
- LAION held-out GT 来自 DiskANN truthset top-100 IDs，并以 unit-normalized exact IP 抽样复核；未带 `.unit`／`.unit_ip` 的首轮 raw artifact 已失效，见 `INVALID_RAW_IP.md`。
- LAION 与 WebVid public-query 源文件 MD5 相同，因此 LAION 只能算不同 base corpus/scale 的迁移控制，不是独立第三 query workload。
- `sift10M`、`sift10M_skewed`、`deep10M`、`gist1M` 和旧 `yandex_t2i` 不属于当前正式协议。

## 5. 冻结底图

三个正式数据集均使用 `R=64, L_build=100, C=512`：

| 数据集 | NSG |
| --- | --- |
| WebVid | `indices/webvid2_5m_light_v1_index/acosp_nsg.json` |
| Yandex | `indices/yandex_t2i_official10M_ip_v1_index/acosp_nsg.json` |
| LAION | `indices/laion10m_acsg_v1_index/acosp_nsg.json` |

同目录 `.info` 必须匹配 dataset version、metric 和参数。不得把 RoarGraph 的 `L_pjpq=500` 当成重建 NSG `L_build=500` 的依据。WebVid 固定宽度图中的 `-1` 是未用 padding，不是坏边；导出 variable-degree 图时只过滤 padding。所有方法比较必须绑定相同图 checksum。

这里的`acosp_nsg.json`实际是内嵌base向量的原生二进制索引，扩展名不代表JSON。核对元信息优先读`.info`和已有manifest；需要解析时使用对应索引加载实现，不能按后缀调用`json.load`或无界`read_text`。

## 6. 搜索接口与行为不变量

原接口为`ACSG::search_new(dis, topk, I, D, visited, mode, custom_enterpoints, retset_buf)`；query通过DistanceComputer绑定，输出为真实base ID及距离。`mode=0/1/2`分别为随机、固定权重、自定义入口。`search_new_traced`调用相同搜索主体；可选`trace_gt`仅用于监督诊断，不能影响在线决策。

- 原mode2代码常量`limit_heuristic=3`，只考虑输入前三个位置，再用visited去重；传入更多不等于消费更多。所有自定义ID应由调用方验证`0≤id<ntotal`，不能相信旧注释所称的越界自动兜底。
- 初始种子在计算raw query–base距离后排序；同三唯一ID且无distance tie时，反转HNSW堆输出顺序不自动构成行为差异。任何顺序/去重/入口数变更都需结果与实际消费验收。
- `search_L`是候选pool容量；实现分配`max(search_L,topk)`，但正式协议仍要求`L≥K`。L不是NDC预算，不保证逐query Recall随L单调。
- 原kernel返回retset中的top-K，不得以RegionalSearch的独立global-topK替换。复用外部retset时需按其要求重置workspace/visited；并发状态、query计数/seed及fallback必须纳入可复现身份。
- HNSW返回maxheap；路由器必须明确heap→排序→真实ID的映射，不能混用local index与base ID。实际ef/k/距离函数以调用代码和manifest为准。

区域组件另有共享/区域pool、全局visited与独立top-K、按概率分配容量和加权轮转；历史协议保存其完整定义：[详细07](experiment_history/07_hierarchical_p2_p3.md)。其成功实现不表示方法收益成立。

原 `search_new` 仍不能从 `SearchTrace` 或 `retset_buf` 恢复搜索：`SearchTrace`只是聚合诊断且显式不含 routing state；外部 retset 每次仍被 resize 并重置；`num_ids`、游标`k`、`updated_pos`和stagnation均为调用内局部量。`VisitedTable`只标记“已经算过距离”，而仍留在pool的`Neighbor.flag`才标记待扩展；被pool淘汰后，现结构不能区分已扩展与已评分未扩展。`search_L`还是共享成员，不是每个分支冻结的state字段。

纯入口层变更保持base、原图、metric与后续kernel；若新方向改变候选调度、强制扩展、预算截断或暂停恢复，即成为独立搜索过程版本，须新增版本化state-machine而不是覆盖原`search_new`。该state至少要保存有序retset及flag、有效长度、调度游标、彼此独立的visited/expanded、L/K/入口身份和graph-NDC；若cap可在邻接扫描中耗尽，还要保存当前扩展节点、neighbor offset及updated position。必须先验收pause/clone/no-op/resume的返回ID、距离、NDC和扩展顺序等价，再谈方法质量；count/plain/纯wall继续分离。原API没有这些能力；独立C实现与验收入口见下一小节。

### 6.1 C stage1 v1 独立API与语义

实现位于 `entry_method_exploration/20260909_c_stage1_v1/src/`，命名空间 `cstage1`，不修改、替换或向原 `search_new` 加callback。当前仅支持原mode2入口语义，C阶段冻结K10/L64、128；非法初始ID由新API拒绝，原kernel对越界ID仍无安全保证，不运行原kernel的非法输入来假称parity。

- `Engine::initialize`：保存raw query副本、query ID、L/K、初始入口与base/graph/metric/kernel身份；只消费入口前三位置，visited去重后不足不补到3，无入口时保留原固定seed fallback。
- `Engine::resume`：到指定完成扩展数checkpoint、自然终止或graph-NDC cap。`State::set_additional_cap`保存prefix NDC及绝对limit，`remove_cap`仅供无cap parity；实际查询每L只有一个checkpoint。
- `State`：全部L+1 retset槽的ID/float distance/pending、num_ids、cursor、updated_pos、当前row/node/neighbor offset、独立visited/expanded、query/入口/身份、NDC与remaining、started/completed扩展计数及最多16个历史扩展ID。visited/expanded是必要membership，不把全部suffix trace交给线上决策。
- `State`按值深clone；`to_json/from_json`持久化有序pool、canonical membership及完整partial-row状态。每分支独立DistanceComputer，resume显式绑定state中的query；冻结base/graph只读共享。状态的L不读取共享`search_L`。
- `Engine::inject(e,force=false)`支付candidate距离，按原pool bound自然插入并rewind；`force=true`对同一候选尝试插入后，不论是否留在pool，均清除其pending并独立记expanded、启动强制row；其后由`resume`实际扫描邻接行一次，再保留/rewind原cursor。每分支最多一个动作；已visited、非法槽与自然终态映射continue/no-op。
- cap在下一次合法未visited距离计算前截断；未评分节点不标visited，保存当前row/offset/updated_pos。cap恰耗尽后仍可跳过visited/padding并自然结束；started expansion与completed row不能混用。返回原retset topK，不使用独立global-topK。

L+1 scratch、初始化按distance-only排序、full-pool的`dist>=worst`拒绝、row内固定cursor与整row后的rewind均保持原规则。原kernel没有输出完整扩展顺序，C1用冻结源码机械提取且仅增observer的[reference](entry_method_exploration/20260909_c_stage1_v1/src/native_reference.hpp)，先对真实原kernel验ID/float bits/NDC/扩展数，再逐序验证state-machine；另有独立合成边界测试。证据：[C1 gate](entry_method_exploration/20260909_c_stage1_v1/results/c1_gate.json)、[独立kernel审阅](entry_method_exploration/20260909_c_stage1_v1/reviews/kernel_final_review.md)。

C2 [配置锁](entry_method_exploration/20260909_c_stage1_v1/config.locked.json)固定paired Fast3 direct top3、单独top7的后四槽去重不补位、checkpoint完成扩展33/65、单全局额外B=1856。最多9分支为continue＋四个natural＋四个force。每条训练query均保留完整prefix state、原始topK/距离、逐分支实际NDC/终止和plain wall；无资格分支明确alias同一continue结果及其计时，alias复制成本单列。候选真实距离计入B，路由两次调用成本另计。各物理branch的count/trace与独立plain完整state一致；GT在两数据集全部raw分支完成后由[独立评分脚本](entry_method_exploration/20260909_c_stage1_v1/src/score_c2.py)打开，不能进入搜索动作。

clone、JSON序列化/恢复、状态初始化、prefix/suffix wall单列；初始化包含前三入口距离，resume包含图搜索，不能把它们称纯bookkeeping overhead。C2没有完整独立整批方法QPS；同cap不保证实际NDC或wall相等。C标签复用键还必须包含起始策略、query、完整prefix state、checkpoint、B、候选生成器及具体动作语义；静态single `u_L`、旧probe/restart标签不兼容。

## 7. Artifact 与 provenance

单 seed Fast 目录：

```text
fast_entry_variants/<dataset>_seed<seed>/
  manifest.json
  qgt_cover_hubs.bin
  qgt_cover_hub_ids.bin
  qgt_gt_basin_prototype_hubs.bin
  eval_r1_3run.json
  eval_r100_3run.json
  per_query_r10.json
```

正式 Fast seeds 为 `20260828/20260829/20260830`；hub budget 为 WebVid 815、Yandex/LAION 821。manifest schema v2 至少记录 dataset/artifact version、split、metric、normalization、query/GT/base/graph path 与 checksum、seed、hub budget、参数、输出 checksum、代码版本、CPU/线程和时间。

现有 manifest 的 base 字段只是路径，新正式批次必须补 base 与图 checksum。seed 位于 `variants.qgt_cover.seed`；不同 seed 只改变相同训练样本上的 k-means 初始化，不是 query bootstrap。builder 会写入已有目录，外层 runner 必须预先拒绝冲突。

`build_wall_seconds` 只计已有 exact GT 后的 builder，不含 exact GT 和 evaluator 内构建的 Micro-HNSW。完整离线成本必须分项：

```text
T_offline_single = T_exact_train_GT + T_QGT + T_prototype + T_router_index
T_offline_ensemble = T_exact_train_GT + sum_views(T_QGT + T_prototype + T_router_index)
```

三 view 共用 train GT 时只计一次；缺失阶段写 `null + reason`。不得把 post-GT 秒级时间称为完整训练。

已知无效 artifact：`fast_entry_variants/webvid2_5m_light_v1/eval_qgt_vs_prototype_r1.json` 的 raw task 曾发生 vector/ID 错配；LAION 首轮 raw-IP/raw-L2 也已失效。两者禁止进入新汇总。

## 8. 在线搜索与评测

`benches/test.cpp` 的 `--query_split drl_test|validation` 显式选择 split，默认 `drl_test`；结果必须记录实际 split。`--test_scope comparison` 只运行 Medoid、Raw 和 prototype comparison slots。IP 数据的 Raw routing 使用 IP。

Recall@K 为返回 top-K 与 exact top-K 的集合交集数除以 K；必须 `search_L >= K`，因此 Recall@100 首点为 `L=100`，禁止 `K=100/L=64`。

正式 Fast 及所有方法基线比较统一单线程（2026-09-09用户明确要求）：评测配置`threads=1`，OpenMP/BLAS/MKL线程均限制为1，启动和结果验收均检查线程数。held-out 10K；Formal 每点 3 timing runs；Fast 3 build seeds × 每 seed 3 timing runs；Recall 方差来自 build seeds，QPS 方差来自 timing runs 与 seeds；跨 invocation QPS 优先使用同次 Medoid 归一化；tail 阈值固定 `0.1/0.2/0.5/0.8`。

逐 query 数据必须按 query ID 保存未排序 aligned 数组。CDF/分位数可排序，但 rescued、newly_harmed、still_failed 和 paired bootstrap 只能使用 aligned 数据；timing runs 不是独立 Recall 样本。

计时／计数契约：

- 分别记录 routing、graph、total 的 NDC 与 latency，`total_ndc = routing_ndc + graph_ndc`；
- QPS 用单线程、单方法独立整批 wall；同机不并发运行训练、标签生成或其他性能测试，不由逐query latency均值或多线程吞吐换算；
- tail、GT 评分、hash 和 JSON 写盘不进入计时；
- 若计数 instrumentation 有开销，以结果一致的独立计数进程提供 NDC；
- 固定 warm-up、轮换方法顺序，并记录线程、CPU 和 cache condition。

离线训练、标签生成、构建允许多线程并单独记成本；它们的线程配置不能传递给正式查询测试。已有16线程测量只保留历史身份，正式主表须用所有方法重新测得的单线程结果。

旧评测器是否满足此计时合同必须逐版本审查，不能仅据接口名判断。`bench_target_basin_eval`曾存在GT评分/工作区创建落在timer内的问题；纯wall已验收路径与旧问题范围见[正式化复盘](experiment_history/02_multiview_and_attention.md)、[区域搜索复盘](experiment_history/07_hierarchical_p2_p3.md)。计数文件的QPS不可发布。

## 9. 构建与环境

本项目方法运行合同为CPU-only。2026-09-08现场核对16个逻辑CPU、约123GiB RAM、swap为0，主解释器`.venv_cpu/bin/python`存在；当前CMake cache为Ninja，GPU/Python Faiss/BUILD_TESTING开关均为OFF。工作区为`/data/netg/ACSG`。

```bash
source .venv_cpu/bin/activate
cmake -S . -B build -G Ninja \
  -DFAISS_ENABLE_GPU=OFF \
  -DFAISS_ENABLE_PYTHON=OFF \
  -DBUILD_TESTING=OFF
cmake --build build -j 16
```

必须配置根工程，不使用 `SSG/build`。复用旧命令前先运行目标程序的 `--help`；大文件只写入 `/data`。

历史比较工具位于`hierarchical_target_search/20260907_v1/tools/`，不是项目根的`tools/`：[通用局部环境](hierarchical_target_search/20260907_v1/tools/env.sh)、[RoarGraph局部环境](hierarchical_target_search/20260907_v1/tools/roargraph-env.sh)。主方法继续使用`.venv_cpu`；比较依赖与MKL/OpenMP局部环境隔离，不能把RoarGraph环境混入正常ACSG构建/计时。完整依赖版本与已完成smoke见[历史03](experiment_history/03_baselines.md)。该段所述2026-09-08比较依赖核查没有重新构建或安装；2026-09-09的C在独立版本bin中实际编译，链接既有CPU静态库，未改主build或安装依赖。

## 10. 重跑依赖

| 变化 | 可复用 | 必须重跑 |
| --- | --- | --- |
| base、metric、normalization、图参数/后端 | 原始下载与兼容 checksum | GT（语义受影响时）、NSG、Fast、全部评测 |
| QGT/prototype split 或 train GT | 兼容 base 与 NSG | hubs/prototypes、全部评测 |
| hub budget、clustering、prototype 公式 | base、GT、NSG | builder、全部评测 |
| top-m、router backend/参数 | base、GT、NSG、兼容 prototype | 路由与下游评测 |
| search_L、top_k、计时口径 | 上游 artifact | 对应评测 |
| 只改兼容的汇总/绘图 | 原始 JSON/CSV | 汇总/绘图 |

任何不兼容的 base、预处理、metric、图、split 或 GT 变化都会使下游 artifact 失效；不得靠文件名相似继续复用。

效用标签的复用键还必须包含`query身份、real entry ID、L、K、base/metric/graph/kernel身份`。仅改变hub列表时，身份相同的旧single列可映射复用，新entry补测；旧全H不再是新池的完整矩阵。新ID映射、画像/embedding、路由模型/索引、覆盖参照及下游评测需重新生成或显式校验。图/kernel/metric改变会使对应旧效用失效；独立single标签不能充当原位干预标签。训练分区改变可保留缓存真值，但不能复用旧分区统计区间或淘汰结论。

## 11. 记录、复盘与同步规则

任何实验都要有独立版本目录、协议/配置、state/gate、实际命令与日志、代码/输入身份、原始aligned结果及计时边界。未测量写`null + reason`；未执行、实现通过、质量通过、完整性能通过分别记录，不以依赖smoke、模型训练loss或oracle替代方法验收。

每次实验完成或停止：先保存原产物与修正版本，再更新`experiment_history/`详细卡片和`s-experiment.md`索引；随后以`summary.md`更新当前结论，以`s-target.md`更新下一阶段。只有架构、API、数据、artifact、计量或复用合同改变才修改本文的相应条款，避免再次累积实验流水账。发现实现和文档冲突时先报告并用当前证据修正。

历史目录保存详细复盘与原证据入口，不搬走/覆盖原始大型模型、向量、图或结果。原`实验总结.md`、`总结.md`、`aco_router_fast_entry.md`和`readme.md`保留历史身份，由`s-experiment.md`分流；旧README或旧报告中的下一步/命令不覆盖当前合同。


## A+B experiment v1：独立准备与标签接口（2026-09-09）

新增版本 [entry_method_exploration/20260909_ab_experiment_v1](entry_method_exploration/20260909_ab_experiment_v1/protocol.md) 使用 [prepare.py](entry_method_exploration/20260909_ab_experiment_v1/src/prepare.py) 验证原数据和三 QGT hub/prototype manifest，按原 builder 重建 paired Fast20K。fit 20K、cal1024、audit1024 的 raw query、GT、row IDs独立落盘；不由该脚本读取validation/held-out。各自H的并集只用于共享相同真实入口的标签计算，每个模型仍受各自H约束。

[labels.cpp](entry_method_exploration/20260909_ab_experiment_v1/src/labels.cpp) 复用该目录冻结的E20原kernel wrapper源码，并链接核验过的现有静态库，不修改原ACSG。模式 `labels config.json new_output [--parity-only]`；标签严格GT-free搜索后评分，按query×union_hub顺序输出hitcount.u8、hitmask.u16和ndc.u32，K10/L64或128，原raw-IP/NSG/mode2。少量完整返回IDs用于评分重放，逐块输出progress；该计数过程wall不是QPS。

集合迷失定义沿用 `benches/run/plot_final_paper.py`：严格R@10<0.1等价hits=0，hits=1不失败。新增[train.py](entry_method_exploration/20260909_ab_experiment_v1/src/train.py)实现rank8的W=P0+VZ、全H多对一mapping、软遗憾提案/hard fit接受、QR与半径限制、校准选checkpoint。fit接受与保存W使用同一fold函数。标签中audit区域不进入训练张量。已通过ties/空槽/单调性/QR/fold以及已知最优映射的合成验收，双数据集全部12个模型已完成训练并冻结。

新增[benchmark.cpp](entry_method_exploration/20260909_ab_experiment_v1/src/benchmark.cpp)以唯一slot label保存全部学习向量，另表返回真实ID；Fast real-ID backend保留。plain/count从同一序列化Micro-HNSW图加载，逐query核对路由和原kernel返回；正式wall边界包含路由/映射/search/output，排除GT/计数/hash/JSON和建图。route-only与graph-only另测。Fast30K恢复原seed100与heap弹出顺序，matched Fast20K采用与学习模型相同seed。

正式单线程入口[benchmark_single_thread.cpp](entry_method_exploration/20260909_ab_experiment_v1/src/benchmark_single_thread.cpp)复用同一benchmark函数，启动前要求显式`threads=1`及OpenMP/OpenBLAS/MKL环境值1，禁止动态扩线程，并记录实际OpenMP team为1的`thread_contract.json`。[run_single_thread_eval.py](entry_method_exploration/20260909_ab_experiment_v1/src/run_single_thread_eval.py)复用已冻结模型和数据，仅生成1线程评测配置；[analyze_single_thread.py](entry_method_exploration/20260909_ab_experiment_v1/src/analyze_single_thread.py)只读取`single_thread_v1/results/`，逐批检查结果线程数、原配置及实际线程记录，拒绝混入16线程结果。原16线程记录保留但不进入正式性能主表。具体优先级见[单线程修订](entry_method_exploration/20260909_ab_experiment_v1/evaluation_single_thread_amendment.md)。

用户另要求加入NSG基线：[benchmark_with_nsg.cpp](entry_method_exploration/20260909_ab_experiment_v1/src/benchmark_with_nsg.cpp)新增固定`index.acsg.enterpoint`的Policy，无Micro-HNSW、route NDC为0，搜索仍调用原kernel，定义与项目`NSG_Medoid`一致。原[排队控制器](entry_method_exploration/20260909_ab_experiment_v1/src/run_baseline_comparison_after_single.py)计划完整同批补测，后被用户缩减探索范围而取消，未执行。其NSG Policy由下述quick入口复用并在真实五点中验收，不启动旧队列。所有方法分别报告Recall@10、QPS、失败数量/率及两种基线的配对挽救/新增失败。来源与计时关系见[NSG比较修订](entry_method_exploration/20260909_ab_experiment_v1/baseline_comparison_amendment.md)。

用户缩减为探索阶段后，上述大矩阵及队列停止。当前[quick.cpp](entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/src/quick.cpp)复用相同Policy、NSG固定入口与原kernel，放行L64/128/256/400/800并预留801槽retset。每点只执行一次2000query warmup和一次独立plain端到端wall；16条query的count/独立原kernel比较与GT评分全部在timer外，未采集全批NDC，不以0伪造NDC。启动前和实际OpenMP team均要求1线程。五点固定同一份入口模型，并检查每条query所选入口不随L改变；L只用于后续搜索。源/配置/输出位于[exploration_5point_v1](entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/protocol.md)，合成和真实两数据集五L验收均已完成：30个方法点、60000个query输出独立GT评分通过，三方法逐query入口跨五L一致。完整结果身份和范围见summary，单次wall不构成稳定性或显著性证明。

[prepare_eval.py](entry_method_exploration/20260909_ab_experiment_v1/src/prepare_eval.py)要求12个dataset/seed/L的模型全部冻结才读取evaluation；原[run_models_eval.py](entry_method_exploration/20260909_ab_experiment_v1/src/run_models_eval.py)已完成训练和部分旧16线程评测，此后单线程大矩阵和NSG队列也已取消，最终由五点quick入口完成用户指定探索。完整执行状态以state与各complete/results.json为准。实现澄清见[execution_clarifications.md](entry_method_exploration/20260909_ab_experiment_v1/execution_clarifications.md)，推进目标见[s-target.md](s-target.md)。
