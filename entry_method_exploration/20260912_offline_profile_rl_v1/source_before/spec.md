# ACSG 代码架构与实现契约

> 架构与实现事实核对至2026-09-11（E36 query相关三入口换点训练/部署已验收；原Fast/NSG kernel不变）。本文只维护已实现架构、接口、数据/metric、artifact、计量和变更依赖。当前实验结论见[summary.md](summary.md)，下一阶段目标见[s-target.md](s-target.md)，历史实验概览与复盘入口见[s-experiment.md](s-experiment.md)。未实现的研究设想不得写成现有API。

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
