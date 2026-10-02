# ACSG 代码架构与实现契约

> 架构与实现事实核对至2026-09-12（E55固定候选池完整比较已验收；E37部署及原Fast/NSG kernel不变）。本文只维护已实现架构、接口、数据/metric、artifact、计量和变更依赖。当前实验结论见[summary.md](summary.md)，下一阶段目标见[s-target.md](s-target.md)，历史实验概览与复盘入口见[s-experiment.md](s-experiment.md)。未实现的研究设想不得写成现有API。

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

`choose_unique_gt_hubs`按每簇query到质心的cosine相似度排序，再逐query按GT100名次取第一个全局未使用的base ID；不是直接求质心GT1，也不是全簇GT投票。当前seed20260828使用25轮、`nredo=1`，两数据集空QGT簇均为0；不足H时实现会扫描全GT补齐，最终ID排序。随后`build_gt_basin_prototypes`独立按GT1真实向量到raw hub的cosine归属，计算`normalize(unit(hub)+Σ unit(query))`，不复用QGT簇，且是query之和加先验。相关只读核对见[四问题报告](entry_method_exploration/20260910_ood_hubs_clustering_router_research_v1/report.md)，源码行为未修改。

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

## 三入口排序 v1：固定入口、真实组合监督（2026-09-10）

独立版本[20260910_three_entry_rank_v1](entry_method_exploration/20260910_three_entry_rank_v1/protocol.md)复用原raw-IP/NSG和seed20260828的H及paired Fast20K；不改原ACSG源码、原标签或模型。[prepare_fit.py](entry_method_exploration/20260910_three_entry_rank_v1/src/prepare_fit.py)从旧隔离输入复制fit20K、cal1024、audit1024，只有fit读取旧single列来提议组合，不能用single收益替代新标签。

[label_triples.cpp](entry_method_exploration/20260910_three_entry_rank_v1/src/label_triples.cpp)接口为`config.json new_output`，每query四个context×六个第三入口；三个真实ID升序后调用原kernel，GT只在返回后评分。按query/context/option输出hits.u8、masks.u16、graph_ndc.u32和完整ids.i32；相同有序三元组缓存复用并分别记录逻辑/实际调用。组合标签的复用键还包括完整三入口集合及顺序；旧single缓存不兼容。双数据集96万逻辑标签的完整ID→GT10评分、三个入口消费及plain/count/repeat验收已通过。

[train.py](entry_method_exploration/20260910_three_entry_rank_v1/src/train.py)只读fit；W=P0+τD，τ为fit Fast top1–top8中位差。训练固定pairwise logistic，按query归一化真实联合hit差权重，锚定λ||D||²/(2H)。Full为自由H×d；Rank8为(VZ)ᵀ，以共同fit目标初始梯度的右奇异方向初始化V、Z=0。二者均float64 LBFGS，最终导出不归一化float32 W，真实ID映射不变。Full记录强凸目标梯度残差上界；rank8同一上界是相对无约束最优值的界，不是其约束最优证书。cal只选择预定λ，audit/validation不进入目标。

[evaluate.cpp](entry_method_exploration/20260910_three_entry_rank_v1/src/evaluate.cpp)支持原NSG、唯一真实ID标签的HNSW direct3及精确top3。matched Fast20K和学习模型使用相同HNSW参数/seed，并在调用原kernel前对三个真实ID升序；原Fast30K保留legacy heap顺序。所有查询配置、数值库和实际OpenMP team均要求单线程。`measure_wall=false`用于诊断，只做plain/count真实结果而不输出QPS；正式点一轮warmup、一次独立plain端到端wall，另做全量count与ID/距离bits/入口parity，GT/hash/I/O/建图均在timer外。每个方法点另16query与冻结原wrapper比较。合成五L/精确top3/三唯一入口和多线程配置拒绝验收已通过；真实50点的100000个query输出独立GT复核通过，四个路由模型在五L下序列化HNSW图及逐query入口均一致。NSG/原Fast30K的40000个query输出与E22逐位回归通过。cal诊断v1的warmup计数元数据错误由独立evaluate_v2修正，数值结果/模型选择不变，原件保留；正式validation使用v2。实测性能与范围见summary。

## 固定 H 的 GT-topK画像 v1（2026-09-10）

独立[E24版本](entry_method_exploration/20260910_gt_topk_profiles_v1/protocol.md)实现从fit exact GT闭式构建GT1/GT10×硬/软画像，不修改原Fast builder或原ACSG。原Fast链仍为第2节；该画像分支是额外的独立实现，不表示所有新画像性能通过。

- [initialize.py](entry_method_exploration/20260910_gt_topk_profiles_v1/src/initialize.py)：核验原base/图/训练query/GT hash、H真实ID与raw向量、E23 fit/cal原行及GT100列宽；不运行旧prepare_fit的single提议/训练标签路径。仅用fit GT1 cosine最高/次高间隔确定T尺度。
- [build_profiles.py](entry_method_exploration/20260910_gt_topk_profiles_v1/src/build_profiles.py)接口`recover|candidates`。先以原builder float32逐位恢复GT1硬，真实搜索恢复PASS后才允许其它候选。每GT目标对全部H作cosine硬argmax（ties升序真实ID）或stable softmax，K_gt名次等权平均，a每query总质量1；p=unit(unit(raw_hub)+sum a*unit(query))。其它加权累加float64，导出float32。K_gt与Recall@10的K分别命名；无新的归一化预处理/正式metric变更。
- 每数据集8份画像，T表在cal前锁定；fit query/GT/目标/hub不接受cal/audit/validation样本。manifest保存W/hash、K_gt/T、支持质量/ESS/熵、画像变化和成本。GT1硬保留dense归属，后续候选保留完整支持统计和float64归属矩阵digest，可按fit重算以控制存储；无梯度/搜索训练标签依赖。
- [evaluate.cpp](entry_method_exploration/20260910_gt_topk_profiles_v1/src/evaluate.cpp)复用E23 GT-free Policy与原kernel，支持原NSG、HNSW direct3、exact3；matched统一真实ID升序，原Fast30K保留legacy seed100/heap。新版本增加/proc进程线程数及冻结CPU affinity检查、启动前预计调用cap、实际调用记账、policy构建/加载时间，以及协议内L128独立route-only/graph-only warmup和wall；不得相加代替独立端到端wall。
- [jobs.py](entry_method_exploration/20260910_gt_topk_profiles_v1/src/jobs.py)逐job预留完整调用、拒绝已有输出，强制OMP/OpenBLAS/MKL1和taskset CPU15，记录actual team/process threads、RSS、时间/磁盘上限。正常调用543296、仅身份/parity修复预留8192；失败job按预留全额记账，不能通过重启规避上限。
- [run_development.py](entry_method_exploration/20260910_gt_topk_profiles_v1/src/run_development.py)只按cal HNSW hits、graph NDC和固定ties选族/T，exact和QPS不参与选择；audit只有冻结候选。两数据集cal主候选均严格胜Fast才能进入validation。[run_validation.py](entry_method_exploration/20260910_gt_topk_profiles_v1/src/run_validation.py)先验证并写入冻结文件，再核对/复制历史validation前2K，六方法五L、原值全保留。
- [analyze.py](entry_method_exploration/20260910_gt_topk_profiles_v1/src/analyze.py)独立评分所有返回ID/mask/NDC、三入口及row alignment；query bootstrap仅描述，不使用timing轮作Recall样本。[frontier.py](entry_method_exploration/20260910_gt_topk_profiles_v1/src/frontier.py)仅处理实测非支配点和明确标记的事后插值，无新搜索或模型选择。

实际GT1硬恢复逐位通过；全部116点169408输出独立评分，三条基线60000个validation输出E23逐位回归、各画像五L相同图与入口、单线程/预算/冻结身份检查均已通过。模型选择只用cal，audit/validation均有历史使用披露，held-out未读取。结果与方法判断见summary及[E24报告](entry_method_exploration/20260910_gt_topk_profiles_v1/report.md)；实现验收不升级为性能GO。


## 两固定画像的搜索前选择 v1（2026-09-10夜间）

独立[E25协议](entry_method_exploration/20260910_selective_profile_gate_v1/protocol.md)与实现不修改原Fast builder、E24画像或原ACSG kernel。A0/A1均为冻结的三个真实入口策略，选择只发生在主搜索前；以下接口不具备probe、restart或结果合并能力。

- [initialize.py](entry_method_exploration/20260910_selective_profile_gate_v1/src/initialize.py)绑定原资产hash与hub映射，生成fit-only hub表`[log1p ESS0, log1p ESS1, 1-cos(W0,W1)]`；导出fit8192/cal2048，audit及validation输入必须在模型冻结之后才准备。
- [gate_policy.hpp](entry_method_exploration/20260910_selective_profile_gate_v1/src/gate_policy.hpp)的`SelectivePolicy`包装冻结`Policy`；`inspect`返回13维GT-free特征与A0/A1三元组，`choose`返回完整所选路由、logit、选择bit及两路调用/特征内积计数。BaseGate只读前7维、选A1才调用新路由；DualGate每query两路。每query实际额外3/6次原IP distance重评分计入route NDC，raw query不改变原NSG metric。
- [train.py](entry_method_exploration/20260910_selective_profile_gate_v1/src/train.py)用真实配对命中差的P/N权重拟合线性logistic；fit全行标准化、clip±6、float64 Newton、截距不惩罚，三λ和五个fit阈值固定。JSON必须包含`feature_set/mean/scale/beta/bias/threshold`，预测按顺序float64求和并以`>=`选择A1。线上模型不读L或GT。
- [evaluate.cpp](entry_method_exploration/20260910_selective_profile_gate_v1/src/evaluate.cpp)支持`nsg/fast30k/fast20k/e24/base_gate/dual_gate`六种方法，单线程独立plain wall三次各自预热，全批count及前16条原wrapper在timer外。计时包含在线路由、特征、预测、排序、原kernel和预分配输出写入；GT在所有raw输出和计时结束后评分。L128的route-only/graph-only单测不相加为端到端wall。
- [jobs.py](entry_method_exploration/20260910_selective_profile_gate_v1/src/jobs.py)绑定源码/binary/config身份、CPU15、实际进程线程/RSS、进程时间、磁盘/输出和真实NSG调用上限；失败job保留完整预留。诊断point收费`2N+16`，三次wall点收费`7N+16`，L128分项额外`2N`；正常1,089,152、修复16,384、合成≤10,000。
- [verify_outputs.py](entry_method_exploration/20260910_selective_profile_gate_v1/src/verify_outputs.py)独立重评分、对照被选策略的ID/距离bits/graph NDC、复算全部路由收费和13维特征、比较C++与离线预测。[audit_report.py](entry_method_exploration/20260910_selective_profile_gate_v1/src/audit_report.py)只重建已缓存的两次真实搜索，不给反事实结果填写在线QPS。

Artifact包括逐query输入row IDs、GT100形状/来源、两路真实结果与特征、全部候选/优化轨迹、audit前冻结manifest、三次独立wall、派生门控输出与机制分析。A0/A1的W、H、metric、图、split或L身份变化会使相应配对标签/特征/模型/结果失效，必须独立重建；不得只改模型路径继续复用旧标签。只改离线分析解释不允许改冻结权重、阈值或原输出。

实现验收已通过：124点219584输出独立GT评分，四条原曲线80000个validation输出与E24逐位相同；门控选中策略/完整费用、五L决策及相应微型图一致、冻结/预算/线程/63项上游资产hash均通过。模型及方法效果见[summary](summary.md)与[E25报告](entry_method_exploration/20260910_selective_profile_gate_v1/report.md)，不由实现验收升级为性能GO。


## 单路画像收缩 v1（2026-09-10夜间）

独立[E26协议](entry_method_exploration/20260910_profile_shrinkage_v1/protocol.md)复用E24 A0/A1，不修改原builder、kernel、E25门控或其封存产物。在线接口仍为单份GT-free `Policy`，没有学习门控或在线插值。

- [build_profiles.py](entry_method_exploration/20260910_profile_shrinkage_v1/src/build_profiles.py)：同hub的既有float32端点数值作float64 `(1−α)W0+αW1`和L2归一化后导出float32，固定α0.25/0.50/0.75；0/1端点直接bit复制，混合范数finite且>1e−12，否则拒绝。保存W/hash、几何变化和构建成本，不新增fit或GT训练标签。
- [evaluate.cpp](entry_method_exploration/20260910_profile_shrinkage_v1/src/evaluate.cpp)：薄封装原单路Policy，支持NSG/Fast30K/Fast20K/E24及alpha画像；原NSG不改。matched三真实ID升序，一画像一微型图，原Fast30K legacy顺序保留。每point三次独立warm/plain总wall，全批count及16条原wrapper在timer外；L128 route/graph分项不相加为总wall，所有raw输出完成后才读取GT评分。
- [effect_stats.py](entry_method_exploration/20260910_profile_shrinkage_v1/src/effect_stats.py)：`d1=hA1−hA0, da=hα−hA0`；R按原正事件保留，Rh用`sum min(da+,d1+)/sum d1+`；A_all=`1−count(da<0)/count(d1<0)`，Ah_all=`1−sum da−/sum d1−`。总损失包含新产生/加重损伤，可为负比例；另保存原损失避免、新损失、丢失原收益、新收益的逐query恒等式，分母0为undefined。辅助unique query统计不参与选择。
- [select_alpha.py](entry_method_exploration/20260910_profile_shrinkage_v1/src/select_alpha.py)：只用新cal L64/128，先选达标者，否则以最差四项归一化比率S选最接近反证项，再依净命中/受损事件/负幅度/入口变化/小α打破ties。cal失败状态保留，不能用audit/validation更换。W/cal输入与源码先冻结，再冻结全部cal候选和主α；audit后才准备历史validation。
- [verify_outputs.py](entry_method_exploration/20260910_profile_shrinkage_v1/src/verify_outputs.py)、[check_transitions.py](entry_method_exploration/20260910_profile_shrinkage_v1/src/check_transitions.py)：独立GT评分/合法ID/三入口、plain/count和原wrapper；四条原曲线回归E25，五L入口不变。新α入口相同于某端点时，结果ID/距离bits/hits/mask/graph NDC须相同；第三套入口分组只解释，不成为新选择特征。
- [jobs.py](entry_method_exploration/20260910_profile_shrinkage_v1/src/jobs.py)：继承CPU15/实际线程1、失败完整预留、identity/RSS/时间/磁盘与调用硬限制；正常897280、修复16384、合成≤4096。仅固定新cal2048/audit1808及历史validation2000，无新fit/全H标签或held-out访问。

W、H映射、Micro-HNSW参数/seed/顺序、原NSG/kernel、query/GT、L或metric改变均须按依赖重建相应结果/选择/计时；不能复用旧命中差模拟新alpha。只读跨E25质量连接须先验证相同query/GT/A0/A1结果，QPS仍来自各自独立轮次，不跨轮拼接。

实现验收完成110点177760输出、四基线80000输出bit回归、115项上游hash、六份中间W独立标量参考及cal选择ties复核。全部8真实job完成，50正式点各三次单线程wall；数值/计量验收不构成性能GO。结果见[summary](summary.md)及[E26报告](entry_method_exploration/20260910_profile_shrinkage_v1/report.md)。

## GT10机制分析与限定补测（2026-09-11）

独立[E27目录](entry_method_exploration/20260911_gt10_mechanism_v1/report.md)提供已有证据分析及有明确缺口后的限定诊断；不修改第2节Fast、E24画像或原ACSG，不把诊断控制登记为已选择部署方法。

- [analyze_existing.py](entry_method_exploration/20260911_gt10_mechanism_v1/src/analyze_existing.py)：只读原fit、base、GT、W、三入口和搜索原输出，按E24原目标float32评分/batch4096重建四份已选画像归属，核对digest/support/W数值。GT1 manifest的`assignments_identity`对应已有dense f64，后续候选的`assignments_sha256`对应可重算权重；两种schema不能混读。输出rank→真实hub、质量转移、每hub mass/ESS/方向集中度及全部aligned query配对。
- [analyze_target_links.py](entry_method_exploration/20260911_gt10_mechanism_v1/src/analyze_target_links.py)：离线计算已有query的GT目标hub归属、实际三入口频次、GT各rank命中变化和GT1 float64数值控制；不调用ANN/NSG。几何覆盖、ESS和数值重评分不是效用标签或新部署结果。各query×L正负命中变化与rank成员新增/丢失是不同口径，只有净命中恒等式相同。
- [补测协议](entry_method_exploration/20260911_gt10_mechanism_v1/supplement/protocol.md)在新控制和搜索前冻结。[prepare_supplement.py](entry_method_exploration/20260911_gt10_mechanism_v1/src/prepare_supplement.py)固定一个20K行排列，保留0.1 GT1项并整组打乱第2–10名所属hub，按原float64加权unit-query画像规则生成一份tail_shuffle/数据集。每rank全局hub频次、每hub总质量、每query总质量保持，ESS/方向/GT1-tail重合不保持。没有新single/triple标签或梯度训练；shuffle只作原cal/audit L128 exact/HNSW机制控制。
- [独立evaluate.cpp](entry_method_exploration/20260911_gt10_mechanism_v1/supplement/src/evaluate.cpp)复制E26评测器，只放行其冻结Policy原本已有的exact3开关。原Policy、kernel、计时循环不变；WebVid旧validation2K两硬画像五L三次warm/plain，另对WebVid L64/Yandex L128两硬画像做exact诊断。诊断无QPS；plain/count/原wrapper和重复bits检查、GT后读取、CPU15/实际线程1及L128分项不相加的合同沿用。
- [run_supplement.py](entry_method_exploration/20260911_gt10_mechanism_v1/src/run_supplement.py)：9个job依赖恢复门顺序执行，配置和binary/源/上游身份冻结，拒绝已有输出，失败保留全预留。正常真实调用181376，恢复修复另限640，全硬上限182016；无合成搜索。单job1200s、总查询进程1800s、RSS40GiB、目录512MiB和free10GiB硬限制。所有新原始输出独立GT评分，恢复/重复的七字段回归E24。

结果保存旧批次与新批次独立身份；不跨批次拼接QPS，重复计时不增加Recall样本。全部source和array均记录来源，base/图的完整hash在既有分析阶段复核；补测前/过程中检查冻结身份。新exact只覆盖两个事后指定正点，不能由它推导其它validation L的后端分解；任何新query/GT、W/H、metric/graph/kernel、路由seed/顺序或L变化都使相关配对失效。更新报告/图表可复用兼容原始结果，不得借分析脚本覆盖E24–E26或自动重启补测。当前判断与执行成本见[summary](summary.md)和[历史16](experiment_history/16_gt10_mechanism.md)。


## GT10共享入口变换 v1（E28，2026-09-11，已完成）

独立[entry_method_exploration/20260911_gt10_shared_transform_v1](entry_method_exploration/20260911_gt10_shared_transform_v1/protocol.md)固定E24 GT10 hard为锚点，离线导出 `W=normalize(P+f(P))`，共享线性、小MLP(d→64→d)与自由hub残差使用相同全H三元素集合似然和锚定正则。在线原始query→一份microHNSW top3→三个真实hub→原NSG，query端没有MLP。全H精确MAP为top3；HNSW仍为近似实现。新src和bin在版本目录，原kernel/build/旧资产只读。

fit20k/集从两硬画像HNSW3并集补齐C8，枚举56个完整三元组、L128原生NSG；兼容E23缓存复用前校验query/GT/H/图/L/入口顺序并核验native结果。224万逻辑标签中1971899次新标注加256次parity，268101次缓存复用；全部原始ID独立重算hits/masks已通过。教师先max hits，再min graphNDC，再原型分数和真实ID；只是C8教师。每族λ10/100、80epoch、相同fit与优化器，无验证epoch选择。12次训练完成；每族cal仅选λ，随后冻结再执行audit/validation。

正式wall只在训练完成后按CPU15、实际线程1、OMP/BLAS/MKL1顺序运行，每点三次warm/plain；计数/GT/I/O在timer外，累计预算和冻结文件见协议与reviews。历史fit/cal/audit/validation重复使用如实披露，held-out未授权访问。后续spec只同步最终接口与验收，效果写summary与历史卡。

E28实现验收：完整150点235296个query输出独立评分，原六对照120000个输出回归E24；全部三轮warm/plain/count/reference结果按bit核验，五L入口和microHNSW身份一致。独立NumPy重算12份模型前向/单位化与最终集合CE通过。实际真实NSG调用3377147、repair0、synthetic0；原上游资产和冻结选择核验见[最终验收](entry_method_exploration/20260911_gt10_shared_transform_v1/reviews/final_audit.json)。方法结果状态`SHARED_TRANSFORM_EXPLORATION_COMPLETE_NO_FORMAL_GO`，效果与不确定性见summary/[历史17](experiment_history/17_gt10_shared_transform.md)，不由实现通过升级性能GO。

## 教师与目标对齐 v1（E29，2026-09-11，已完成）

独立[E29协议](entry_method_exploration/20260911_teacher_objective_alignment_v1/protocol.md)固定E28共享linear/λ100/80epoch，2×2分别改变教师和损失。[prepare.py](entry_method_exploration/20260911_teacher_objective_alignment_v1/src/prepare.py)核验E28原始三入口标签，导出原cost教师和无额外hits时保留GT10实际HNSW3的keep教师；两教师逐query最高hits相同，新标注0。新M损失给非教师分数加μ=.1后取top3，减去完整教师分数；原C集合CE不变。只对教师漏选成员给结构化hinge上界，不将其视为NSG损失。

[train.py](entry_method_exploration/20260911_teacher_objective_alignment_v1/src/train.py)输出8份float32单位W、完整目标轨迹和每10epoch精确对齐。cost_ce在两集逐位恢复E28 linear100；全枚举/有限差分与NumPy导出/最终两损失核验通过。全部模型在开发query前冻结，无cal选择。在线raw query/一份HNSW3/原NSG不变。

[run_evaluation.py](entry_method_exploration/20260911_teacher_objective_alignment_v1/src/run_evaluation.py)使用与E28逐位相同的独立复制binary及源码，原build身份记录在bin/evaluate.provenance.json。完整fit20k、cal1024、audit1024及原validation2000：170点471200输出；110正式点各3次warm/plain，GT/count/I/O在timer外，CPU15/实际线程1与资源/调用cap逐job核验。相同模型五L入口/微型图一致，全部count/reference/repeat结果按bit核验；8条旧曲线160000输出回归E28。

[analyze.py](entry_method_exploration/20260911_teacher_objective_alignment_v1/src/analyze.py)独立GT重评分、完整fit新入口与兼容标签核对、两个因素的配对差值/交互，以及明确标记的非支配曲线插值。[gradient_diagnostics.py](entry_method_exploration/20260911_teacher_objective_alignment_v1/src/gradient_diagnostics.py)仅在全部查询后做fit梯度/几何分析，optimizer step与NSG调用均0。实际NSG调用2085120，repair0，synthetic0；本版本预算收口。全部旧资产/冻结/图表与文档验收见[final_audit](entry_method_exploration/20260911_teacher_objective_alignment_v1/reviews/final_audit.json)。方法结论见summary与[历史18](experiment_history/18_teacher_objective_alignment.md)，不由实现通过升级为性能GO。


## 等效三入口集合监督 v1（E30，2026-09-11，已完成评测）

独立[E30协议](entry_method_exploration/20260911_equivalent_teacher_sets_v1/protocol.md)复用E28完整C8三元组标签，新增可接受集合mask：最高hits且其中最低graph NDC的全部完整三元组。single仅接受原T0，multi接受全部G。两种损失均为已标注56组合上的max(F+.1×非接受指示)减max可接受F，未知组合不作为已知负例。共享linear导出静态W，在线一份microHNSW3/原NSG不变；本轮未实现任意组合交互或在线重排。

[train.py](entry_method_exploration/20260911_equivalent_teacher_sets_v1/src/train.py)输出4个共享A与W、81点优化轨迹及9次完整集合诊断；[match_drift.py](entry_method_exploration/20260911_equivalent_teacher_sets_v1/src/match_drift.py)只用fit导出，在较大位移的normalize(P+t(W−P))路径上二分，匹配较小者的均方弦长；较小者保留原字节并以alias复用，不作为独立训练。控制不匹配逐hub位移分布或保证同一A可精确生成缩放W。

[独立评测器](entry_method_exploration/20260911_equivalent_teacher_sets_v1/src/evaluate.cpp)复制E29源码，仅将timing repetition合同3改为5，原Policy/kernel/timing循环不变，独立编译并保存diff/build身份。[runner](entry_method_exploration/20260911_equivalent_teacher_sets_v1/src/run_evaluation.py)将完整fit、开发、五轮正式曲线顺序执行；query CPU15/实际线程1，GT/count/I/O在timer外，原方法输出须回归旧批次。实际180点491200个输出已独立GT评分，120正式点各五轮wall，9条旧曲线180000输出回归E29；五L同模型入口与微型图一致。全部3,177,280原NSG调用，repair/synthetic0，预算收口。择优按冻结的共同Recall参照及五轮速度条件执行，原始wall/插值/描述性最快与推荐身份分别存储。完整验收见[final_audit](entry_method_exploration/20260911_equivalent_teacher_sets_v1/reviews/final_audit.json)，方法结论见summary/[历史19](experiment_history/19_equivalent_teacher_sets.md)，不由实现通过升级为性能GO。


## 训练有效性检查 v1（E31，2026-09-11，已完成缓存验收）

独立[协议](entry_method_exploration/20260911_training_effectiveness_v1/protocol.md)与[训练实现](entry_method_exploration/20260911_training_effectiveness_v1/src/train.py)逐字保留E30数学核心、teacher masks和输入，只变Adam日程/1200步上限/fit总目标最小checkpoint规则。两集single/multi各一次，4次4800更新共302.73s，外层进程600s硬限与内层共享deadline同时控制；末点和选中点分别导出A.f64/W.f32。

[preflight](entry_method_exploration/20260911_training_effectiveness_v1/src/preflight.py)复核E30旧资产链和原4个A/W目标；原枚举/有限差分与共享归一化A累积梯度测试复用并重新运行。[analyze](entry_method_exploration/20260911_training_effectiveness_v1/src/analyze.py)独立NumPy复算4份新模型的选中/最后点，共8个目标/导出，统一float32画像对已测C8组合评分，保存query级slot/hits/NDC、条件已知效用及完整fit的未知组合上下界。G由原hits/NDC重建核验。未知组合不作为零效用标签；仅数学下界允许未知贡献为0。

[checkpoint诊断](entry_method_exploration/20260911_training_effectiveness_v1/src/diagnose_checkpoints.py)只读比较选中/最后点的浮点位移和离散入口/缓存命中敏感性，optimizer/NSG调用0，不更改选点。[缓存门](entry_method_exploration/20260911_training_effectiveness_v1/results/cache_gate.json)按预锁的双集效用/成本/未知覆盖规则失败，因而本版本没有新HNSW查询、NSG调用或QPS点；未实现或执行新的性能评测器。新增API/产物只涉及离线训练、缓存分析和PNG/SVG/CSV/XLSX报告，不改变线上Policy/kernel/metric。

训练输入和模型各有冻结manifest，全部旧资产/表格/图与文档验收见[final_audit](entry_method_exploration/20260911_training_effectiveness_v1/reviews/final_audit.json)。方法结论见summary和[历史20](experiment_history/20_training_effectiveness.md)，实现验收不升级为性能GO。本版本预算收口。


## 完整动作直接收益策略 v1（E32，2026-09-11）

独立版本[entry_method_exploration/20260911_direct_reward_policy_v1](entry_method_exploration/20260911_direct_reward_policy_v1/protocol.md)固定E28 C8/56组合标签及E31共享linear。新[train.py](entry_method_exploration/20260911_direct_reward_policy_v1/src/train.py)支持teacher hinge和精确策略期望Recall regret，两组从A=0、λ100/τ.05、同1200步日程；β只用初始化fit数据梯度范数计算一次并冻结。每步记录期望与贪心Recall/NDC；在二者成本均≤各自初始化+1%的点中选本组fit总目标最低最早点，导出A.f64/W.f32与末点原件。独立NumPy复核β、全部选中/末点目标和模型；teacher逐位恢复E31。

新[Policy](entry_method_exploration/20260911_direct_reward_policy_v1/src/benchmark_with_nsg.cpp)的family=c8接受`c8_anchor`及两个固定`c8_policies`：先复用原HNSW direct3并集和原GT10全H float32得分填满8，再以unit query/float32 W的float64分数枚举56完整动作，按真实ID映射后调用原NSG。候选/slot/真实三入口与冻结fit计算全量一致，plain/count共享已序列化小图。route NDC包含两HNSW距离、H次填充得分和8次模型得分；graph/total分别记录。新Decision保存8候选local ID和动作slot，GT仅在全部原始搜索后读取评分。

[evaluate.cpp](entry_method_exploration/20260911_direct_reward_policy_v1/src/evaluate.cpp)保留原kernel和direct3路径，支持无wall的完整plain/count/原kernel16条验收；条件wall接口实现一次完整warmup+5轮轮换独立wall，包含完整C8生成/打分/组合选择/映射/NSG/output，排除GT/count/hash/I/O/build。该wall接口已编译，本轮因开发门失败未产生QPS测量。实际fit/cal/audit21点已完成，配置与实际CPU15/单线程均核验。

有效控制器为[run_deployment_v2.py](entry_method_exploration/20260911_direct_reward_policy_v1/src/run_deployment_v2.py)及[deployment_common_v2.py](entry_method_exploration/20260911_direct_reward_policy_v1/src/deployment_common_v2.py)：启动前校验所有画像/映射文件、拒绝已有输出，分离缓存/路由/fit/开发/条件validation门并记录调用账。初始默认W路径漏`t1`的零查询失败原件保留；修正只恢复E30已有默认身份，释放预留的特例与证据见[配置修正](entry_method_exploration/20260911_direct_reward_policy_v1/configuration_repair.md)。其它失败仍按完整预留计费。输入/模型/候选改变须重新核对标签复用键；不得把本C8策略收益直接外推为全H或单路HNSW选点收益。实验结论由summary与[历史21](experiment_history/21_direct_reward_policy.md)维护。

E32访问审计分别记录字节hash读取、数组解码、训练/选点和查询评测使用；旧保护链包含12个历史validation query/GT/row_ids文件，其SHA256读取已发生，但未进入本轮训练/新评测。原笼统`validation_access=false`不能解释为所有I/O均未发生；当前范围见[访问说明](entry_method_exploration/20260911_direct_reward_policy_v1/access_scope_clarification.md)及[记录](entry_method_exploration/20260911_direct_reward_policy_v1/reviews/access_scope.json)。held-out不进入该保护扫描。


## HNSW底层边强化学习 v1（E33，2026-09-11）

独立[协议](entry_method_exploration/20260911_hnsw_edge_rl_v1/protocol.md)固定当前默认画像、H/真实ID、原NSG/IP，只改变Micro-HNSW底层已有有向边。初始结构预检的≥2出度要求被[修正](entry_method_exploration/20260911_hnsw_edge_rl_v1/structural_preflight_repair.md)为min(2,原出度)，原件保留。有效实现为[environment_v2.cpp](entry_method_exploration/20260911_hnsw_edge_rl_v1/src/environment_v2.cpp)、[native_v2.py](entry_method_exploration/20260911_hnsw_edge_rl_v1/src/native_v2.py)、[train_v2.py](entry_method_exploration/20260911_hnsw_edge_rl_v1/src/train_v2.py)，不修改主hnswlib或ACSG源码。

- `Environment`序列化原M16/efConstruction200/efSearch10/seed20260828小图，按原邻接顺序给底层边编号；保护原入口BFS出树/入树及最近原边。原图必须强连通，导出不得增边或变更画像/ID/上层。
- 训练编译独立hnswlib副本，`searchBaseLayerST`仅在未visited目标上调用keep/remove hook；删除不标visited、不计算距离。保存每episode实际暴露edge/action/offset、三入口、NSG返回ID/距离/route与graph NDC。概率策略只依赖边ID，GT由Python在真实输出返回后评分，不进入遍历。
- C接口`e33_run`提供采样或固定mask轨迹；`e33_static`加载物理删边图并关闭hook，供真实monitor；`e33_export`导出静态HNSW。`e33_parity`核对hook与物理图的入口/计数及原NSG IDs/float bits/NDC。原/新原始API不具备坐标RL或新增边动作。
- REINFORCE训练独立边logit，每query历史奖励EMA基线和熵正则；train16K/monitor4K只来自原fit20K，4×600步。实际完整轨迹、logit/optimizer/query-baseline checkpoint、静态图和逐节点出度匹配随机图均冻结。独立NumPy重放2400更新和36图结构校验已通过。
- [Policy](entry_method_exploration/20260911_hnsw_edge_rl_v1/src/benchmark_with_nsg.cpp)新增`graph_file`：加载外部静态HNSW并验证每内部节点的画像bytes/外部ID与W/mapping相同，plain/count从同一序列化图加载。正式[评测器](entry_method_exploration/20260911_hnsw_edge_rl_v1/src/evaluate.cpp)编译原hnswlib，不含训练hook；原NSG、GT后评分、CPU15/线程1和完整wall合同保持。
- [开发控制器](entry_method_exploration/20260911_hnsw_edge_rl_v1/src/development.py)冻结全部模型后运行cal5方法/集、按cal奖励选seed后冻结、再audit全部模型；20点20480输出已独立评分/原默认回归、plain/count/reference通过。条件五L×5轮wall接口已实现，但本轮双集门失败，未执行validation/QPS。

图边、画像、H/映射、构图参数、split或NSG/L/K/metric改变均需重建相关环境/轨迹/选点和评测。旧C8/独立入口标签不能当新图三入口完整反馈；本轮新增307200真实训练反馈，C8缓存复用0。旧资产保护区分当前E32/实际依赖SHA与更早链stat；旧validation仅stat核对，未hash/解码，held-out未读/hash。结果由[summary](summary.md)和[历史22](experiment_history/22_hnsw_edge_rl.md)维护，接口通过不升级为性能GO。


## 冻结HNSW-RL图性能补测（E34，2026-09-11）

独立[协议](entry_method_exploration/20260911_hnsw_rl_benchmark_v1/protocol.md)承接用户新增QPS/Recall/失败率授权，E33原开发门和零QPS状态保留。[prepare.py](entry_method_exploration/20260911_hnsw_rl_benchmark_v1/src/prepare.py)逐字复制E33无hook评测binary、冻结E33已选图和已有基线小图、核对历史validation2000输入及模型身份；没有新画像/图训练或按validation选模型。

[run.py](entry_method_exploration/20260911_hnsw_rl_benchmark_v1/src/run.py)配置NSG/Fast30K/GT10-hard/RL，WebVid另GT10-soft起点，五L合计45点。正式wall接口此前未执行，本轮已完成225次：一次完整warmup后五轮按数据集/repeat/L轮换的独立plain整批wall；完整路由/映射/原NSG/输出在timer内，GT/count/hash/I/O/load在外。CPU15、实际进程及OMP/BLAS/MKL1，方法与数据集串行，失败完整预留不释放。接口调用量为每点(5+2)N+16；总630720，修复0。

[analyze.py](entry_method_exploration/20260911_hnsw_rl_benchmark_v1/src/analyze.py)独立复核90000输出的GT10 hits/mask/失败率、两项NDC和QPS=2000/wall；NSG/Fast/GT10共70000旧输出ID/距离bits/入口/hits/mask/NDC逐位回归E30。相同方法五L序列化图及入口保持，五轮/plain/count/reference一致。失败严格hits=0，配对挽救−新增失败=原失败−RL失败；query bootstrap区间与五轮QPS范围分开。

该版本新增实测原值/配对CSV、共同Recall区间内明确标注的非支配曲线log-QPS插值、PNG/SVG/PDF和Excel，不改变原Policy/kernel/metric或默认模型。历史validation已有反复使用，held-out未读/hash。图/模型/query/GT/NSG/计时或L变化需重新评测；不能跨旧轮次拼接QPS。结果见[summary](summary.md)/[历史23](experiment_history/23_hnsw_rl_benchmark.md)，完整验收见[final_audit](entry_method_exploration/20260911_hnsw_rl_benchmark_v1/reviews/final_audit.json)。


## 当前GT10 HNSW访问与选点诊断（E35，2026-09-11）

[协议](entry_method_exploration/20260911_hnsw_selection_probe_v1/protocol.md)冻结双集E20前128个训练pilot、当前原GT10 HNSW/H/画像/真实ID/NSG，L128/K10。有效[prepare_v2.py](entry_method_exploration/20260911_hnsw_selection_probe_v1/src/prepare_v2.py)核对原train query/GT文件源行与SHA、当前20K fit不重叠、H映射与NSG身份，切出旧全H单入口ID/hits/mask/NDC；首版prepare因pilot不在fit而0查询停止，原件保留。旧16线程标签只作质量证据。

[probe.cpp](entry_method_exploration/20260911_hnsw_selection_probe_v1/src/probe.cpp)用SpaceInterface距离回调旁路记录实际被评分内部ID，不改hnswlib搜索/metric。`observed_ip`调用原InnerProductSpace函数；k1/k3/k8逐query与plain/count堆元素值及NDC一致，现有Policy三入口一致。被评分包含上/底层并保留重复事件，不能直接称扩展；ef10下k1/3/8的底层预算均为max(ef,k)=10，最终裁剪k不改变这次搜索预算。堆距离检查为浮点值相等，没有单独memcmp两份距离字节。

输出exact全H同原生距离排序、ann8/ef40/efH、评分mask/events/NDC；每query原NSG执行ANN3/exact3/ef40_3和当前ANN8全部56组三入口，真实ID升序共享beam，C++不读GT。另16query×3固定单入口/集回归旧缓存。新NSG15200、HNSW3072，无新训练/GT/validation/held-out/QPS；CPU15，进程与OMP/BLAS/MKL单线程。

[analyze.py](entry_method_exploration/20260911_hnsw_selection_probe_v1/src/analyze.py)复算209408旧单入口及15104新联合返回、mask、96个native回归，解析HNSW有向底层强连通/可达/度/最短跳，按全部并列最佳单入口A0分解访问与最终选择，并输出真正C8三入口oracle。当前C8是单张GT10 top8，不能复用E28/E32两路并集C8标签；若query、H、NSG、metric、L、entry顺序变更，相关标签必须重新验证/生成。

[CSV/JSON](entry_method_exploration/20260911_hnsw_selection_probe_v1/results/diagnosis.json)、[图](entry_method_exploration/20260911_hnsw_selection_probe_v1/figures/selection_diagnosis.svg)及[验收](entry_method_exploration/20260911_hnsw_selection_probe_v1/reviews/final_audit.json)只支持机制诊断。all56联合费用、单/三入口oracle及几何exact分开；NDC/进程时间不是QPS。后续设计不属于此已实现API，见s-target。

## 查询相关三入口换点策略（E36，2026-09-11）

[协议](entry_method_exploration/20260911_query_swap_policy_v1/protocol.md)固定当前原GT10 H/画像/HNSW与NSG/raw IP，以一次HNSW top8作为候选，原top3为初态。56个rank字典序三元素集合、16动作（停止/15单点交换）、最多3步；真实入口按ID升序执行原NSG L128/K10。未修改原Fast/NSG kernel或全局图/候选库。

[common.py](entry_method_exploration/20260911_query_swap_policy_v1/src/common.py)定义状态图/预算，prepare保存源行/SHA与固定16维query投影、画像投影/pair cosine，fit1792行统计标准化76维特征。每集合特征含三候选rank/query-profile cosine/相对top1差/投影交互、画像pair cosine和query投影；先f32量化，再f64标准化/clip和1521参数MLP。F=rank先验+MLP，16后继softmax形成策略，greedy 1e−9同分优先停止，最多3步。query ID/GT/NSG结果不进入模型特征，随机控制单独使用源row hash。

[runner.cpp](entry_method_exploration/20260911_query_swap_policy_v1/src/runner.cpp)生成每query完整56真实联合返回/距离/入口/NDC；C++不读GT，Python独立评分U=命中增量−0.1×总NDC相对变化。reward为相邻U差、γ1、stop吸收。[model.py](entry_method_exploration/20260911_query_swap_policy_v1/src/model.py)/[train.py](entry_method_exploration/20260911_query_swap_policy_v1/src/train.py)实现REINFORCE加历史query-state EMA基线和同一三步策略完整期望DP控制；相同表示/seed初始化/batch/日程，两臂双seed各3000更新，缓存真实反馈不产生新NSG。checkpoint按monitor U与graph NDC门选，cal按U/NDC/seed选主模型并冻结后运行audit。

[runner_v2.cpp](entry_method_exploration/20260911_query_swap_policy_v1/src/runner_v2.cpp)是部署前增加pool距离导出/parity的独立版本；原label runner不覆盖。[deploy.py](entry_method_exploration/20260911_query_swap_policy_v1/src/deploy.py)执行fit回归、cal/audit六方法、原/主RL/主Exact的单L128五轮plain wall。计时含HNSW、query投影、全部56特征/MLP、最多三次交换、映射、原NSG及输出；GT/count/load/hash/IO在外，CPU15/实际线程1。矩阵/特征运算不记NDC，须以全wall表示费用，单L不能替代完整前沿。

[preflight](entry_method_exploration/20260911_query_swap_policy_v1/reviews/preflight.json)验收完整路径DP/策略梯度/有限差分和标签；[训练核验](entry_method_exploration/20260911_query_swap_policy_v1/reviews/training_verification.json)独立恢复全部checkpoint前向、轨迹reward/return/EMA；[部署核验](entry_method_exploration/20260911_query_swap_policy_v1/reviews/deployment_verification.json)验证原生/NumPy特征分数/动作及缓存/原kernel/wall一致。结果由[analyze_v2.py](entry_method_exploration/20260911_query_swap_policy_v1/src/analyze_v2.py)汇出CSV/JSON配对区间，首版JSON布尔错误保留并记录，0额外查询训练。[最终验收](entry_method_exploration/20260911_query_swap_policy_v1/reviews/final_audit.json)冻结源/模型/返回/图表/工作簿和文档。

输入各2048 fit（1792 train/256 monitor）、cal/audit各512，行互斥但历史使用，画像来自历史fit，非盲测；没有新validation/held-out。E28/E32两路union C8标签不兼容本轮单路top8。若query/H/画像/HNSW/NSG/metric/L/真实入口次序变化，需核验/重生成受影响标签；标准化或投影/模型变化须重导出模型并验证原生动作。当前结果与未来方案分别见summary/s-target，不能把后续图交换或等价加速写成已实现API。

## 离线画像策略优化与普通HNSW重建（E37，2026-09-12）

[独立协议](entry_method_exploration/20260912_offline_profile_rl_v1/protocol.md)将学习放在离线静态画像构造阶段。固定当前GT10画像P、H815/821、真实ID映射、原base/raw-IP/NSG；只用train4096单位query二阶矩生成B(d×16)。[common.py](entry_method_exploration/20260912_offline_profile_rl_v1/src/common.py)实现W=normalize(P+0.25(PB)(tanh(X)/4)Bᵀ)，float64计算、float32导出；X=0直接复制P字节。输出画像会改变普通HNSW重建后的邻接，但没有独立边操作或在线策略模型。

[environment.cpp](entry_method_exploration/20260912_offline_profile_rl_v1/src/environment.cpp)提供create/build/run/save/verify/data/stat C接口，[native.py](entry_method_exploration/20260912_offline_profile_rl_v1/src/native.py)绑定。每个候选画像从零以原M16/efConstruction200/seed20260828/原ID插入顺序建普通HNSW，efSearch10、direct top3，三个真实ID升序进入原NSG L128/K10。C++不读取GT，返回完整ID/距离/入口/route与graph NDC；Python后评分真实命中及零命中事件。每次构图保存W SHA和入口、层级、全部有序邻接的拓扑SHA。接口拒绝非有限/非单位画像、非法query行与非协议L，原项目hnswlib和大图不修改。

[train.py](entry_method_exploration/20260912_offline_profile_rl_v1/src/train.py)是one-step Gaussian参数策略：每个动作采样整份静态画像系数，同一份图服务batch128。奖励为命中增量减0.1倍逐query总NDC相对变化、0.1倍零命中事件变化及画像均方漂移。RL使用8个独立扰动的score-function/leave-one-out估计；ES对照使用4对正负扰动。两者同高斯平滑黑箱目标、表示和调用预算，不将其称作两个不同模型族；没有多步PPO、固定C8重排或旧三元组标签代理。

两集各RL/ES双seed，200更新/次，σ0.3、Adam、cosine步长、梯度范数与参数均值限制均由[锁定配置](entry_method_exploration/20260912_offline_profile_rl_v1/config.locked.json)及协议定义。step0和20..200存完整确定性train512/monitor1024结果；非零checkpoint按monitor U及graph NDC门选择，选中/末点分别输出mu.f64、W.f32、graph.hnsw和identity.json。全部动作/扰动/batch/奖励/返回/optimizer轨迹保存，12800份重复大画像由冻结系数与B重建，原始H/NSG仍为冻结依赖。

[部署控制器](entry_method_exploration/20260912_offline_profile_rl_v1/src/deploy.py)在全部模型冻结并通过独立训练复算后才准备历史cal1024；按cal U/总NDC/seed冻结选择，再准备audit1024。实际部署直接使用与E34逐字一致的无hook[评测binary](entry_method_exploration/20260912_offline_profile_rl_v1/bin/evaluate)。在线仅raw query→普通HNSW top3→ID升序→原NSG，无query投影/MLP/组合枚举，GT只在全部原始搜索后打开。选中模型与训练checkpoint在fit128完整字节一致；plain/count/原kernel和五L相同入口/图均独立核验。

当前GT10、RL、ES、Fast30K、NSG在两集历史audit1024上各L64/128/256/400/800，共50点。每点一次完整warmup和5次轮换plain整批wall，CPU15、进程/OMP/BLAS/MKL1线程、无同时训练或重分析。timer包含完整路由、映射、NSG和输出，GT/count/hash/build/load/IO在外。L128的route-only/graph-only单独测量，不相加充当完整wall。Fast30K是原训练量/seed的历史基线，非本轮同训练量消融。

[独立审计](entry_method_exploration/20260912_offline_profile_rl_v1/src/audit_training.py)复算全部GT交集、奖励、12800动作画像hash、1600次更新和88checkpoint；[分析](entry_method_exploration/20260912_offline_profile_rl_v1/src/analyze.py)从原始输出重算质量/NDC/五轮QPS、配对结果和共同区间插值，并导出CSV、Excel和PNG/SVG/PDF。[最终验收](entry_method_exploration/20260912_offline_profile_rl_v1/reviews/final_audit.json)验证旧资产保护、真实调用、线程、所有图表/工作簿/文档链接，结果及证据限制由[summary](summary.md)/[历史26](experiment_history/26_offline_profile_rl.md)维护。

本轮train4096、monitor1024、cal1024、audit1024源行互斥，但原画像及数据都有历史使用，非全管线盲测；没有读取/hash新的validation/held-out原始输入。改变P/B/参数化/图参数/H或插入映射需重建受影响画像/小图/反馈；query、GT、NSG、metric、L/K、入口次序变化需重新核验或生成反馈。模型冻结、开发门与历史audit曲线不构成默认替换或独立正式性能GO。

## 既有静态画像训练反馈诊断（E38，2026-09-12）

[独立协议](entry_method_exploration/20260912_offline_profile_diagnosis_v1/protocol.md)及[analyze.py](entry_method_exploration/20260912_offline_profile_diagnosis_v1/src/analyze.py)只读取E37已有numpy/JSON/CSV，不导入native/evaluate/train、不执行HNSW或NSG、不构图或更新参数。GT评分从E37的已隔离fit输入与实际返回重算；动作-query未观测项不补零。输出按dataset/arm/seed/step与原source row ID对齐，记录实际暴露次数。

RL逐query条件梯度矩阵为(ε−mean ε)ᵀU/(7σ)，ES为ε正方向ᵀ(U+−U−)/(8σ)，与原8候选估计器等价；四个reward项分别分解并对原梯度回归。固定μ/方向下16次query二分仅估计query批次稳定性；有限总体修正方差与去噪信号估计不包含方向采样噪声。少数query贡献按逐query梯度范数和定义，不等于参数或检索收益占比。

随机/确定对比仅允许checkpoint s与step s+1的mu_before逐字相同，且query属于该中心已测train512；每query先平均八动作。80匹配组的1188条记录包含重复query，bootstrap按checkpoint块作描述区间，不作为独立因果验证。全部中心与选中/末点只作原结果分析，不回选cal/audit模型。

[summarize.py](entry_method_exploration/20260912_offline_profile_diagnosis_v1/src/summarize.py)导出分组、暴露校正、逐步/逐queryCSV、JSON及PNG/SVG/PDF；[verify.py](entry_method_exploration/20260912_offline_profile_diagnosis_v1/src/verify.py)以集合交集/逐项梯度公式复核32个分层step及全部精确匹配。E37整目录SHA保持，根文档变更前件在独立source_before。修改诊断公式或分组只重做派生分析，不能覆盖旧原始反馈/模型或自动产生新查询；E38原固定大批次提案保持其历史未执行身份；继任E39已单独实施，见下节。当前解释见[summary](summary.md)/[历史27](experiment_history/27_offline_profile_diagnosis.md)。


## 固定参数与动作的批次诊断（E39，2026-09-12）

[协议](entry_method_exploration/20260912_fixed_profile_batch_diagnosis_v1/protocol.md)与[control.py](entry_method_exploration/20260912_fixed_profile_batch_diagnosis_v1/src/control.py)复用E37已编译environment.so及native wrapper，不修改原kernel。prepare按冻结cal选定两μ/集与原八扰动逐字恢复W及拓扑身份，从排除两个原批次后的E37 train4096中无标签抽1024行，另存train前缀query/GT/源行；搜索配置num_queries4096、CPU15、threads1、native_call_cap19296。完整预留每dataset19296，失败不释放、不自动重试；总硬限40000，拒绝已有job及输出。

每图build/save→16历史query三路verify→1024正常run，36图实际38592次NSG/38016次HNSW/36build，全部参数固定，0optimizer。verify的count输出同时与旧轨迹或checkpoint逐字比较ID/float distance/入口/route与graph NDC；全部W与物理图、aligned原始输出及source row IDs保存。GT仅由后处理读取，不进入C++搜索。

[analyze.py](entry_method_exploration/20260912_fixed_profile_batch_diagnosis_v1/src/analyze.py)用M=(ε−mean ε)ᵀ/(7σ)构造逐query梯度，单列固定画像漂移正则；主比较预锁前后512，辅助128/256/512的互斥组对及1024单估计。有限总体N使用实际合格3843/3844；互补重组不是独立重复，条件query方差不含方向采样噪声。稳定规则在查询前锁定，不选择新μ/动作部署，不产生QPS。

[verify.py](entry_method_exploration/20260912_fixed_profile_batch_diagnosis_v1/src/verify.py)独立集合评分全部36864返回，以逐动作LOO公式和二阶矩恒等式核验4096逐query梯度、428组方差及1092互斥组对。原verify语法修正/图轴调整见[记录](entry_method_exploration/20260912_fixed_profile_batch_diagnosis_v1/analysis_repair.md)，0额外搜索。前后保护E37/E38目录SHA，原根文档快照位于source_before。改变分析仅重做派生结果；若μ/ε/query/W/图/metric/kernel/L改变，必须新建版本并重新建立真实反馈身份。结果见[summary](summary.md)/[历史28](experiment_history/28_fixed_profile_batch_diagnosis.md)。


## 既有画像动作收益与入口归因（E40，2026-09-12）

[协议](entry_method_exploration/20260912_profile_payoff_attribution_v1/protocol.md)及独立[analyze.py](entry_method_exploration/20260912_profile_payoff_attribution_v1/src/analyze.py)不导入上游native/train/runner，仅用E39已有36配置W、完整返回、原训练query/GT与E37同源基线。每点原八动作+中心，aligned Δhits以当前确定中心为参照；原U/NDC分母仍用E37anchor。逐query有限O与静态最佳B满足O−B=(O−G_best)+L_best，best ties先中心后原动作序号；该事后统计不导出新模型。

输出actions/queries/entry_events/transition_groups/query_pairs/query_neighbors CSV、aligned NPZ和JSON。入口事件保留完整三元组/新增/移除/source row，单/多交换分开，重复参与hub不拆成独立收益。已存W与unit query的float64得分边界仅为离线几何诊断，不模拟HNSW路径或声称SIMD逐位parity。query-query dense cosine/最近5只是已有向量分析，不调用ANN；有收益子集邻居明确GT条件化。

[独立核验](entry_method_exploration/20260912_profile_payoff_attribution_v1/src/verify.py)以集合交集、逐query循环/精确恒等式和标量内积重算36864返回、36动作、6508事件、13016边界、23369分组/1161pair；[邻居复核](entry_method_exploration/20260912_profile_payoff_attribution_v1/src/verify_neighbors.py)检查10240关系与pair资格。所有新搜索/构图/optimizer/GT为0，E37/E38/E39整目录SHA保持，根文档前件独立保存。派生分析变更只重做缓存统计；E40原目标hub/其余画像2×2提案保持当时未执行身份，继任E41已实现，见下节。结论见[summary](summary.md)/[历史29](experiment_history/29_profile_payoff_attribution.md)。


## 目标画像/其余画像2×2反事实控制（E41，2026-09-12）

[协议](entry_method_exploration/20260912_profile_factorial_v1/protocol.md)及[prepare.py](entry_method_exploration/20260912_profile_factorial_v1/src/prepare.py)直接冻结E40原案例与E39行名单，构造C/F/S/R四格：每行只复制中心或原扰动W字节，S只改目标行、R只改其余行。画像H/真实ID/顺序不变，S/R作为独立干预，不声称原共享参数可达。保存四格W和行级身份，无optimizer/插值/新采样。

[run.py](entry_method_exploration/20260912_profile_factorial_v1/src/run.py)复用E37原native二进制，CPU15/线程1，每集完整预留及native cap4288、全局硬限10000、失败不释放/不自动重试、拒绝覆盖。每格普通build/save→run1024→前16query三路verify；C/F全部返回及W/拓扑/物理小图SHA恢复E39，S/R是真实新搜索。实际双集8576 NSG/8448 HNSW/8build、0optimizer，完整raw返回与parity输出保存。

[analyze.py](entry_method_exploration/20260912_profile_factorial_v1/src/analyze.py)输出以C为参照的全池G/L/net、零命中事件、NDC、原anchor分母U/漂移奖励，以及逐query target/rest主效应和I=F−S−R+C；冻结案例局部条件与全池结果分开，不按新结果择优或部署。[verify.py](entry_method_exploration/20260912_profile_factorial_v1/src/verify.py)独立验证8192集合评分、4096旧输出回归、128parity行、八W构造和2048交互。E37–E40目录及原native/NSG依赖前后SHA保持，根文档前件保留；GT只在返回后评分，无新原validation/held-out访问。改变目标行、幅度、query或kernel须新版本/真实反馈，不能复用未测S/R标签。当前结论见[summary](summary.md)/[历史30](experiment_history/30_profile_factorial.md)。


## 被移除画像责任与两块条件信用（E42，2026-09-12）

[协议](entry_method_exploration/20260912_removed_profile_factorial_v1/protocol.md)与[prepare.py](entry_method_exploration/20260912_removed_profile_factorial_v1/src/prepare.py)以E40原负例C/F真实入口差集的唯一被移除hub为目标，冻结WebVid1627796/slot543、Yandex8309868/slot686及E39原1024行。C/F/S/R逐行复制字节合同同E41；S/R作为独立干预，不保证原共享X参数可达。保护E37–E41与实际native/NSG依赖，根文档变更前件另存。

[run.py](entry_method_exploration/20260912_removed_profile_factorial_v1/src/run.py)复制E41已验收查询流程，仍导入原E37 native，无新增kernel/API。每集完整预留4288、硬限10000、CPU15/实际线程1，四图正常1024+前16三路parity；实际8576 NSG/8448 HNSW/8构图。C/F全量回归E39及E41，完整raw/W/序列化图保存。

[analyze.py](entry_method_exploration/20260912_removed_profile_factorial_v1/src/analyze.py)新增固定负例目标单独损伤S−C、完整背景下F−R与分别的充分/必要条件，全池G/L/零命中/NDC/U/原漂移保留。[credit.py](entry_method_exploration/20260912_removed_profile_factorial_v1/src/credit.py)保存逐query hits/U/J两个条件边际、交互及两个背景平均信用，逐条满足两块信用和=F−C；平均数仅是明确均分交互的记账约定，不是新训练奖励执行器。

[verify.py](entry_method_exploration/20260912_removed_profile_factorial_v1/src/verify.py)独立评分8192返回、回归4096旧输出、128parity、八W及2048交互；[verify_attribution.py](entry_method_exploration/20260912_removed_profile_factorial_v1/src/verify_attribution.py)进一步核验案例真实入口/充分必要条件、全部损伤/零命中/三NDC、4096 E41回归和2048三种信用口径。改变目标行、背景、query、参数/图/metric/kernel须新身份与真实反馈；只有派生分析变化可复用当前raw。没有新增训练/GT/QPS或原validation/held-out访问。

后续状态条件局部ΔJ仅为[设计](entry_method_exploration/20260912_removed_profile_factorial_v1/reward_decision.md)，不能登记为已实现策略API。实际结果见[summary](summary.md)/[历史31](experiment_history/31_removed_profile_factorial.md)。


## 局部画像策略优化（E43，完整训练与核验已完成）

[协议](entry_method_exploration/20260912_local_profile_rl_v1/protocol.md)固定E37原P/B/H和train4096/monitor1024，以H×16独立行系数构造W_h=normalize(P_h+0.0625||P_h B||tanh(z_h)Bᵀ)，零行参数直接复制P。每次只改所选hub的一行，其余画像逐位保持当前值；这与E37共享256系数全图动作有实质区别，表示自由度也变化。

[prepare.py](entry_method_exploration/20260912_local_profile_rl_v1/src/prepare.py)从train旧基线三入口多重集合GT无关抽hub，与均匀batch128使用独立RNG，冻结两臂同seed的相同日程。[train.py](entry_method_exploration/20260912_local_profile_rl_v1/src/train.py)每步真实当前128+八候选128，普通HNSW重建→原NSG反馈，原J配对差奖励、单行LOO-RL/成对ES与局部计数Adam。原σ.3、两seed、200步、步长/成本/失败/漂移权重固定；候选不在原共享X像内。

每20步确定W评估train512/monitor1024，保存全W/系数/动量/计数/完整返回；非零monitor U与graph NDC门选择checkpoint。选中/末点保存W和物理图，64query三路parity。预检逐集5120原结果逐位恢复、32条重建重复、单行构造/梯度基线抵消/原kernel通过；全部训练已完成并通过独立复算：1600更新、12,800候选W身份、88 checkpoint、16导出与完整返回均核验。

原native.so/NSG无修改，查询CPU15/实际线程1，串行；两预检+八训练预计1992256 NSG/14510构图，硬限2200000/15000，失败完整预留，19:35训练截止。本阶段不读新的cal/audit/validation/held-out、不新建GT或运行QPS。状态和效果分别由summary/历史32维护。

[独立审计](entry_method_exploration/20260912_local_profile_rl_v1/src/audit_training.py)按保存的行字节重放整份W，以独立公式核验局部画像、GT集合评分、ΔJ、四分量/LOO/ES与局部Adam、日程/选点。额外条件query噪声分析只用原反馈，不更新模型或门。[汇总](entry_method_exploration/20260912_local_profile_rl_v1/src/summarize.py)输出完整质量、反馈、预锁monitor门及图表。全部1992256 NSG/14510图/1600更新已完成，0新GT或本阶段开发/QPS；具体效果见summary。


## 固定局部动作完整训练池诊断（E44，已验收）

[协议](entry_method_exploration/20260912_local_sampling_diagnosis_v1/protocol.md)固定E43两集RL第一seed step20/40/…/200动作前状态与原八候选。[prepare.py](entry_method_exploration/20260912_local_sampling_diagnosis_v1/src/prepare.py)用完整checkpoint和next_row字节恢复C，冻结目标hub/方向和原anchor三入口的GT无关近组。每context只保存C完整W，候选由原行字节恢复且核对原W hash。

[run.py](entry_method_exploration/20260912_local_sampling_diagnosis_v1/src/run.py)复用原E37 native，全部9图各run原train4096，保存完整raw与拓扑，须逐位恢复E43原128返回/距离bits/三入口/两NDC。每集step20与200的18图另存物理图并做16query三路parity。两集串行CPU15/实际线程1，预计739008 NSG/738432 HNSW/180图，0optimizer；每集完整预留369504，硬限760000，19:40查询截止。保护E37–E43及native依赖，根文档前件已保存；9GiB新余量和256MiB产物预算在查询前另锁，不修改E43合同。

全池参考只用于固定状态、固定方向下的条件采样方差及收益损伤诊断；uniform128与近组min(64,N1)/补集补足128均按总体权重估计。有限总体trace方差、命中与U分量以及原批次估计误差由离线后处理计算，不含方向噪声，不作为模型或QPS结果。查询/分析验收状态由summary维护。

E44 [analyze.py](entry_method_exploration/20260912_local_sampling_diagnosis_v1/src/analyze.py)保存逐query四梯度分量、条件均值/方差、全/原batch响应、近/补集G/L和有限动作oracle差分；漂移不计query噪声。[verify.py](entry_method_exploration/20260912_local_sampling_diagnosis_v1/src/verify.py)独立集合评分737280结果，以逐动作LOO与逐维标量方差核对20梯度/640方差坐标，另验23040旧返回与576条物理图parity。180图与739008次NSG已完成，0optimizer；query/方向/背景/分层规则变化需新版本，不能沿用本条件方差结论。继任确定单步控制已在E45实现，见下节；E44历史方案身份保留。


## 同状态确定均值单步完整反馈控制（E45，已验收）

[协议](entry_method_exploration/20260912_mean_update_control_v1/protocol.md)固定E44原20状态、原八ε和E43局部表示/Adam参数。[prepare.py](entry_method_exploration/20260912_mean_update_control_v1/src/prepare.py)逐行恢复μ/m/v/count，原batch梯度生成原next_row需逐位相同，再只用E44全4096条件梯度替换g生成一行。20个新反事实步互不传递，原回放20、连续训练0；输入/两行参数/画像/W来源hash全部冻结。

[run.py](entry_method_exploration/20260912_mean_update_control_v1/src/run.py)仍复用E37原native，C run16恢复E44，其完整4096缓存明确复用；batch/full各完整run4096，全部60图保存物理图/拓扑并16query三路parity。实际167040 NSG/166080 HNSW/60图，CPU15实际1线程。没有新增线上Policy或NSG复用API。

[独立核验](entry_method_exploration/20260912_mean_update_control_v1/src/verify.py)完成245760完整集合评分（含81920当前复用）、320旧输出恢复、960条parity与40次逐坐标Adam/画像构造及图身份。[分析](entry_method_exploration/20260912_mean_update_control_v1/src/analyze.py)同时保存相对C和full−batch的全池G/L/U/J/NDC及位移；跨context累加只作诊断。继任route-only/精确三入口反馈复用已在E46实现，见下节。状态和效果由summary/历史34维护。


## 完整三入口精确反馈复用（E46，已验收）

[cache_environment.cpp](entry_method_exploration/20260912_exact_feedback_cache_v1/src/cache_environment.cpp)包含原E37 environment，新增e46_route真实全池HNSW与e46_search显式三入口原NSG。后者批次先验证query行、升序唯一合法H成员再搜索；route-only仍计HNSW及route NDC，原kernel/build/run/verify保持。有效Python接口[native_cached_v2.py](entry_method_exploration/20260912_exact_feedback_cache_v1/src/native_cached_v2.py)对零长度原生输出返回类型正确空数组。

[run_v2.py](entry_method_exploration/20260912_exact_feedback_cache_v1/src/run_v2.py)对E44固定C+八候选实际route4096，完整三入口不变者仅复用C的IDs/距离bits/graph NDC，变化者调用原NSG；当前route NDC永不复用。query/图/metric/L/K/kernel和完整入口身份均为标签键。全部重构后才打开旧候选raw验收，保存全raw/变化patch/拓扑/费用，36代表物理图三路parity。

[analyze_verify_v3.py](entry_method_exploration/20260912_exact_feedback_cache_v1/src/analyze_verify_v3.py)完成737280集合评分/五字段bits/复用身份、20奖励/梯度、180拓扑及576条parity核验。实际3061 NSG、742528 HNSW、181图含首失败0/4096/1（由trace控制流重建）；失败预留保留，两个v2 job后总预留8000≤10000。初始C种子81920历史调用单列，候选新增1333不能声称全流程99.8%加速。两个修正与原件保留，0optimizer/新GT/QPS；E47连续全池训练已完成并验收，见下节。


## 局部画像完整训练池反馈（E47，已验收）

[协议](entry_method_exploration/20260912_full_feedback_profile_rl_v1/protocol.md)与[train.py](entry_method_exploration/20260912_full_feedback_profile_rl_v1/src/train.py)保持E43原局部参数化/两臂双seed/200步/σ/Adam/hub日程，用完整4096真实反馈替换batch128。候选及每步确定均值都真实build/route4096，仅三入口变化新增原NSG，其余完整结果按同query/原NSG身份复用，route NDC每次更新。每run冷启动4096真实查询，monitor1024每20步实际查询，train512由当时完整反馈提取；非零monitor选点规则保持。

使用E46已验二进制和空增量安全封装，保存candidate/mean变化patch、完整route NDC及entries/cache hash、ε/参数/奖励/Adam、完整5120行checkpoint、selected/last物理图三路parity。原缓存每次均值更新后替换，80次缓存换父/no-op/回退和完整效用恒等预检通过。每run完整预留100000 NSG，8run硬限800000；HNSW预计59107328/硬限60000000，构图14424/硬限15000，CPU15实际1线程串行。八次训练已完成，效果/审计状态由summary维护，无新开发/GT/QPS。

E47 [audit_training.py](entry_method_exploration/20260912_full_feedback_profile_rl_v1/src/audit_training.py)独立重放12800候选/1600均值缓存，586208集合评分、全部路由hash/复用键、四梯度分量/Adam/候选画像/88 checkpoint/16导出及1024parity通过；逐query更新命中差与最终状态守恒。实际228832 NSG/59107328 HNSW/14424build/1600更新，逻辑反馈与真实新增调用分账。[summarize.py](entry_method_exploration/20260912_full_feedback_profile_rl_v1/src/summarize.py)保持原统一门及逐arm结果，停止预算扩展不自动否认RL局部正值；后继评分/拓扑installer和冻结模型评测已在E48/E49完成。

## 画像评分/邻接四格（E48，已实现并验收）

[factorial_environment.cpp](entry_method_exploration/20260912_score_topology_factorial_v1/src/factorial_environment.cpp)包含已验E46精确反馈wrapper与原E37环境，增加`e48_install`两阶段拓扑验证/安装、`e48_installations`计数及`e48_verify_vectors`实际图画像全bytes校验。H/ID/层级/入口/maxlevel不变，完整有序邻接独立可换；预检失败不得部分写图。S=(Wa,Gc)/T=(Wc,Ga)只作因果控制，不能冒充普通builder输出。

[run.py](entry_method_exploration/20260912_score_topology_factorial_v1/src/run.py)固定E44所有状态/动作，真实全池route和合法三入口缓存；`raw.npz/topology.npz/patch.npz/identity.json`保留每状态，首末context物理图及三路parity。500状态/340build/340安装，7525 NSG/2051200 HNSW；独立[verify.py](entry_method_exploration/20260912_score_topology_factorial_v1/src/verify.py)全2048000集合评分、737280端点位恢复、655360交互及1600三路parity通过。原NSG/metric/GT/线上路由不变，结果由summary维护。冻结模型E49评测已完成并验收。

E49 [deploy.py](entry_method_exploration/20260912_frozen_local_rl_evaluation_v1/src/deploy.py)复用E37同SHA静态无计数评测二进制，固定E47全部selected模型，fit比较原checkpoint的train0:64/monitor4096:4160。cal只选seed并冻结再audit，原五L五轮和线程计时合同保持；独立[协议](entry_method_exploration/20260912_frozen_local_rl_evaluation_v1/protocol.md)锁423680 NSG/500000硬限，查询截止21:40。结果由summary维护，未形成双集前沿增益，不替换默认。

E49 [analyze.py](entry_method_exploration/20260912_frozen_local_rl_evaluation_v1/src/analyze.py)独立72960集合hits/mask及失败评分、全部NDC/wall核验，4096旧基线回归与6144 audit→curve返回位一致；[verify_contract.py](entry_method_exploration/20260912_frozen_local_rl_evaluation_v1/src/verify_contract.py)验收8串行job/423680 NSG、1280原kernel parity、250wall、cal选择冻结和split隔离。0新训练；E49历史性能证据保留，最新固定池比较为E55。E50轨迹诊断已验收，用户要求的NSG/Fast/FastGT矩阵已由E55测量。

E50 [analyze_verify.py](entry_method_exploration/20260912_candidate_commit_diagnosis_v1/src/analyze_verify.py)只读E47原12800候选/1600均值稀疏patch及完整route NDC，重建缓存并恢复原J。C+八候选的J-best与净命中/J排序hit-best只作独立单步反事实，含不动，不能传播旧状态输出。14400cache hash/135648独立集合评分和有限oracle分解通过，0新搜索/优化；1600step CSV和原来源保持完整追踪。E51步长方向控制及E52连续提交均已完成验收。

E51 [run.py](entry_method_exploration/20260912_update_direction_radius_v1/src/run.py)复用E46同SHA cache native二进制，重建E47 C/M并位恢复，再真实构建/路由五种固定系数方向半径画像。半径为原候选扰动范数中位数、clip±2，缓存只按同query/完整三入口键复用；实际均值不传播到控制下一状态。本阶段协议的“不读取monitor”等范围指不新增这些split的查询/评分，复用的原5120输入文件和checkpoint物理上含历史monitor记录，只有train4096作为本轮响应。

E51 [analyze_verify.py](entry_method_exploration/20260912_update_direction_radius_v1/src/analyze_verify.py)独立恢复200系数半径/方向与画像公式，1310720集合评分、327680 C/M端点位恢复及56物理图/896三路parity通过；实际3416 NSG/1148672 HNSW/280build。有限状态方向放大为因果控制，不是连续学习。E52直接提交控制已完成并验收；RL反馈步长接受已由E53实现并验收。

E52 [train.py](entry_method_exploration/20260912_direct_candidate_commit_v1/src/train.py)独立实现合法Gaussian候选+不动的原J择优提交，平分优先不动，固定σ/8候选/200步/两seed。实际提交缓存来自已测候选，重新普通build核验拓扑身份；下一状态全部新route并按合法键补测。0梯度/Adam更新，decision steps与accepted submissions分开；checkpoint保留零m/v仅兼容旧存储schema，不调用原梯度更新。src/输入/协议与四训练均已完成，结果由summary维护。

E52 [audit_training.py](entry_method_exploration/20260912_direct_candidate_commit_v1/src/audit_training.py)独立重放6400 Gaussian候选/800提交选择与全缓存、原J/合法mask/no-op/tie/拓扑状态链，292638集合评分、44完整checkpoint/8导出及512parity通过；实际113950 NSG/26276864 HNSW/7212build，295提交，0梯度更新。E53 RL方向+真实反馈步长接受四训练及独立重放已完成。

E53 [train.py](entry_method_exploration/20260912_feedback_step_rl_v1/src/train.py)原8独立LOO Gaussian梯度/Adam临时方向保持，额外真实评测r/4、r/2、r三个确定点，只在三点+不动中按原J接受；Gaussian候选不可直接提交。m/v与计数每步推进，提交W普通build恢复对应拓扑身份，缓存从真正选择点更新，下一状态全新route/合法键补测。新预算9612build/36107264 HNSW、NSG每run150000总600000；四训练完整结果与独立核验由E53报告维护。

E53 [独立重放](entry_method_exploration/20260912_feedback_step_rl_v1/src/audit_training.py)覆盖800 RL梯度/Adam和2400确定步长，以及提交图/缓存状态链。每run2403构图、9026816 HNSW，NSG固定15744+真实变化；原reserved_builds旧字段的独立修正见[重记](entry_method_exploration/20260912_feedback_step_rl_v1/reviews/build_reservation_reconciled.json)，实际成本以原生计数为准。

E54 [完整模型run](entry_method_exploration/20260912_learned_model_factorial_v1/src/run.py)复用E48原生拓扑安装器，在所有学成W/G端点构造A/S/T实际物理图并对完整train4096+monitor1024查询；全部26图导出/64行三路parity、完整向量和图身份检查，C/A旧结果五字段逐位恢复。新增接口无线上策略或kernel改变；静态干预图必须加载冻结graph，不能按评分W重新普通构建来代替。

E55 [deploy.py](entry_method_exploration/20260912_final_method_comparison_v1/src/deploy.py)固定17候选/集，128条独立checkpoint恢复、cal原U/低NDC/固定序选择后冻结最终矩阵；E34历史validation2000独立同机单线程五L五轮，FastGT显式GT10-hard，WebVid另匹配soft起点。原同SHA无策略评测二进制、GT全部raw后评分、full plain/count及原kernelparity保持；[analyze.py](entry_method_exploration/20260912_final_method_comparison_v1/src/analyze.py)独立129168集合评分与113点/225wall/710144 NSG核验。局部row IDs需绑定router_train/validation源命名空间，复制SHA及向量零重叠共同验收。
