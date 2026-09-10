# 方向 B 有界机制 pilot：协议草案

> 状态：`CLOSED_UNAPPROVED_REFERENCE`。  
> 用户于2026-09-09因新颖性碰撞选择不投入该pilot并转向方向A。本草案从未获批、从未执行；这里列出的工具名均为**待实现接口合同**，不是当前可执行命令。除非用户明确重开一个重新核查和批准的新版本，否则不得据此开始实现或实验。

## 1. 目标与非目标

目标只回答：在冻结图和固定轻路由容量下，selector-aware H 外一换一交换是否比同预算的 coverage/oracle-marginal/旧 H 方案通过一次冻结的历史-development audit。该 audit 相对 `Q_fit` 是 sample-out，但不是 fresh test、独立构建或正式泛化证据。

首轮不主张：

- 新颖性已经成立；
- 同 L Recall 等于同 wall Pareto；
- H 外入口普遍必要；
- GT-frequency 是新候选算法；
- development audit 是 fresh test；
- 单构建 pilot 可以替代三构建或 held-out 10K×3。

## 2. 冻结合同

| 项目 | WebVid | Yandex |
|---|---:|---:|
| dataset key | `webvid2_5m_light_v1` | `yandex_t2i_official10M_ip_v1` |
| base | 2,505,000×512 | official first 10,000,000×200 |
| metric/normalization | raw IP；源近单位，不额外归一化 | raw IP；不归一化 |
| graph | 原 R64/Lbuild100/C512 NSG | 同左 |
| old H | 815 real IDs | 821 real IDs |
| K / L | K10；L64、L128分别建目标 | 同左 |
| kernel | 原 `ACSG::search_new(mode=2)`，单入口 | 同左 |
| Fast参照 | 最近诊断使用的 paired-fast20K manifest/prototype；禁用旧30K Fast | 同左 |
| CPU | 同时一个重进程，最多16线程，BLAS单线程 | 同左 |

base、metric、normalization、图、query split、GT、kernel 任一身份变化都使相应标签不兼容并终止本版本；不得静默重建后沿用本协议结果。R0的 `source_manifest.json` 不是execution lock；批准版须直接冻结或重新核验实际base/query/GT/graph bytes、paired-fast20K manifest/prototype以及新runner/kernel SHA，不能只绑定 `.info` 或沿用旧ledger文字。

## 3. query ledger 草案

抽样与文件读取统一使用 `router_train local_index`（0–29999），不把WebVid原始语料的source row当作数组下标。每数据集按以下顺序冻结，所有集合物理不重叠：

1. 在local index `[10000,30000)` 上按prop hash排序，取前4096为 `Q_prop`；它只生成 H 外候选，不训练 F、不作审计。
2. 从同一后20K扣除 `Q_prop`，按fit hash排序取前2048为 `Q_fit`；再按fold hash排序后连续分成四个固定512折。它只用于标签、pool/F拟合与交叉折交换。这是需用户批准的screening-pilot例外，小于`s-target.md`的后20K拟合合同；通过后仍须20K复验。
3. 在local index `[0,10000)` 中先以local-index域排除Fast根因诊断旧512行，再按audit hash排序取前1024为 `Q_audit`；只在所有pool/model/config/statistics/scorer SHA冻结后生成标签并评分一次。它是历史development audit，不称独立测试。
4. validation与held-out的query/GT canonical realpath及内容SHA同时加入拒绝表；本版本不得打开，不能靠路径别名绕过。

建议哈希键：

```text
SHA256(dataset_key + "|b_r0_v1|" + role + "|" + decimal_router_train_local_index)
```

split ledger 至少保存 `router_train_local_index`、可用时的 `source_corpus_row`、role、allocation order、fold ID、所有适用allocation hash（含prop/fit/fold/audit hash）、query/GT source SHA、所有交集计数和旧512 local-index排除清单 SHA。另建 cell-level reuse ledger：与E20全H缓存、旧sparse top32等逐项核对完整复用键；旧search-aware winner/聚合不可伪装成完整列，未匹配单元必须新测。只有 `Q_fit`/G0的完整匹配cell可实际复用；`Q_audit`与任何旧artifact的row/cell重叠只记为历史暴露，当前版本一律在execution lock后重新测，trainer与设计流程在此之前拒绝打开旧audit-row标签。共享研究成本和每方法从零成本分别报告。

## 4. 候选与完整标签

推荐默认候选：

- `E`：Q_prop 的 GT10 中出现频率最高的 64 个 H 外真实 base ID；
- `C=H∪E`：WebVid 879，Yandex 885；
- 所有 ID 唯一、范围合法；同频按真实 ID 升序；candidate manifest 在任何 utility 测量前冻结。

若排除H并去重后不足64个合法ID，G0以候选源失败停止；不得从audit、validation/held-out或未登记来源补足。

这里的GT10只读取既有dataset manifest所绑定exact-GT100的前10列：WebVid为 `benches/datasets/WebVid2.5M_light_v1/gt.router_train.seed20260826.ip.ivecs`（SHA256 `1db08bf5b259a468558e6dfed19661d73bc6fe6947a3c862e526176242ace72c`），Yandex为 `benches/datasets/YandexT2I_official10M_ip_v1/gt.router_train.ip.ivecs`（SHA256 `5255cc604439ad9d2523dd7526dab85e61b40f0784fd630d5f297ef43af6bdcb`）。不生成新GT，GT generation/search calls与新增GT成本均为0。

标签必须分两个不可倒置的阶段生成：

1. candidate manifest 冻结后，先只测 `Q_fit`；所有 pool、最终模型、统计规则、配置和评分代码冻结并记录 SHA；
2. 只有上述 execution lock 完整后，才允许单独生成 `Q_audit` 标签并评分一次；audit 标签生成后不得重训、换池、改阈值或改代码。

两个阶段分别测量各自 query 上每个 `(q,e,L)` 的：

- `hitcount:uint8`；
- `hitmask:uint16`；
- `graph_ndc:uint32`；
- parity 小样本中的完整 top10 returned IDs/distances；
- query row、candidate real ID、L、K、base/metric/graph/kernel/source SHA。

真实调用数（分阶段相加，总预算不变）：

```text
WebVid fit   = 2048 * 879 * 2 = 3,600,384
WebVid audit = 1024 * 879 * 2 = 1,800,192
WebVid total = 3072 * 879 * 2 = 5,400,576
Yandex fit   = 2048 * 885 * 2 = 3,624,960
Yandex audit = 1024 * 885 * 2 = 1,812,480
Yandex total = 3072 * 885 * 2 = 5,437,440
main from-zero total = 10,838,016
8-row all-candidate count/plain/repeat parity
  = 8 * (879 + 885) * 2 * 3 = 84,672
G0 + fit/audit labels + listed parity hard cap = 11,100,000 calls
```

GT只允许在原 kernel 返回之后计算 hitmask/hitcount。计数版本的 latency/QPS 不可发布。parity 行从 `Q_fit` 固定抽取；不得为 parity 提前打开 audit。合法复用可减少实际新调用，但节省额度不得改用于扩大 C、query数、L或验收族；失败重试中已经进入原kernel的调用也计入硬上限。

## 5. 固定轻路由器 F

推荐 F 是每个 dataset/L 一棵 query-only axis-aligned utility tree：

- `max_depth=5`、`min_leaf=32`；最多32叶；
- 输入是原 raw query；在线每层一次坐标比较；
- 叶子只存一个真实 entry ID；不同叶可重复 ID；
- 不读取 GT、搜索结果、trace、query-neighbor atlas 或 Fast probe；
- 每个 pool/折均从同一固定初始化规则重新拟合。

可复现的贪心拟合草案：节点只考虑当前到达的fit行。对每个原始维度，将该节点n个值升序；第j个候选阈值（j=1…7）取0-based位置 `ceil(j*n/8)-1` 的实际float32值，重复阈值去重，左分支固定为 `x_dim<=threshold`、右分支为 `>`，违反`min_leaf`者过滤。叶动作在给定P内最大化该叶累计Recall；同分依次取累计graph NDC更低、真实ID更小者。切分最大化左右叶累计Recall之和；同分依次取左右累计graph NDC更低、维度索引更小、float32阈值数值更小者。只有相对当前未切分叶的累计Recall严格增加才切分，否则保留叶；NDC只破同Recall平局，不单独触发切分。最终导出后逐query验收Python/C++ route ID一致，并用独立reference固定这些边界、重复值与同分规则。

该树只是固定 F，不是 B 的新颖性主张；若其容量太弱导致全部方法失败，本版本仍按预注册 gate 停止，不能在看过 audit 后换模型。

## 6. pool 与交换算法

每个 L 独立产生 pool/tree；m 固定为32。

### Coverage-only

在整个 `Q_fit` 上从空集开始，按 `sum_q max_{e∈P} u_L(q,e)` 的边际增益贪心加到32，得到唯一全局P；同分按较低累计NDC、真实ID。fold只用于随后F的cross-fit，不产生四个不同的coverage pool；最终只在该P上拟合F。每个query的oracle动作固定按Recall降序、graph NDC升序、真实ID升序定序。

### Oracle-marginal/Hydra-style control

从 `coverage_C` 的 forward-greedy pool 开始，最多做四轮穷举的一换一 oracle hill-climb：对所有 `(e,d)∈(C\P)×P` 计算 fit 上的 ideal `oracle_P` 变化，每轮只接受 oracle objective 严格提高最大的一个 pair，同分按真实 ID，首次无提高即停。pool 冻结后从头拟合同一 F；候选产生和保留全程不看 routed utility。这样它与一次 forward greedy 的 `coverage_C` 有明确差别，又与 joint 使用相同 m 和最多四次替换；它只是 Hydra 式结构控制，不声称逐位复现 Hydra/SATzilla。

### Selector-aware joint

以 coverage pool 开始，最多四轮：

1. 在整个 `Q_fit` 上，按加入e后ideal `oracle_P` 的累计Recall增益降序、真实ID升序，产生一个全局 `A_top4⊂C\P`；
2. 在整个 `Q_fit` 上用当前full-fit F，按 `(route_support_count(d), oracle_P-oracle_{P\{d}}, real_ID(d))` 三元组字典序升序，产生一个全局 `D_top4⊂P`；第二项只破支持数平局且越小越先移除；
3. 对同一个全局笛卡尔积 `A_top4×D_top4` 的16个一换一 pair，分别做四次“其余三折从头拟合同一 F、留出一折评分”；
4. 每个 pair 拼接四个留出折的2048个逐 query routed Recall 差；每折都减去同样由其余三折拟合的当前池基线 `f_{P,-k}`，不得减 full-fit F。按预登记的 fit 接受统计量与真实 ID 同分规则唯一排序；
5. 先过滤同时满足mean/LCB门槛的pair，再按 `(OOF mean gain降序, OOF lower bound降序, add real ID升序, remove real ID升序)` 唯一选第一名；一次只接受该pair，更新同一个全局P，并在全部`Q_fit`上重拟合当前F；
6. 无合格交换立即停止，最多接受4次；最终 P 确定后再在全部 `Q_fit` 上从头拟合并冻结最终 F。

候选 F 的硬上限为 `4 rounds × 16 pairs × 4 folds = 256` 次拟合，另计初始四个fold-baseline、预先列出的其他baseline、每轮 full-fit 与 final refit；上一轮获胜pair的fold预测可作为下一轮当前池基线缓存。它们共同受第8节拟合 wall/RSS 上限约束。

推荐的待批准 fit 门槛为：10,000次固定seed query-paired bootstrap，OOF mean gain至少`+0.05 pp`且普通单侧90% lower bound `>0`。这是使用全fit预筛pair后的 cross-fitted post-selection training score；lower bound只是自适应训练稳定性启发式，不作无偏推断，也不因重复使用fit而包装成显著性结论。audit规则见G2；两者均须用户确认后写入 protocol lock，不得事后选择。

### Old-H与描述性控制

- `oldH_joint_m`：令 `C:=H`，以 `coverage_H` 初始化，使用与 `joint_C` 完全相同的fold、F、fit门槛和最多四轮交换；禁止读取E列。
- `frequency_m`：按冻结 `Q_prop` 的GT10频率在C内取前32个动作，再拟合同一F。
- `random_m`：三个预登记seed在C内无放回取32个动作，分别拟合同一F并逐seed报告。
- `full_H_F`：允许同一axis-aligned F从完整H选择叶动作，仅作较大候选池参考；它不是尚未实现的v4 TAO/斜切效用树，也不用于固定m机制归因。

## 7. 质量 gate 草案

### G0：实现/身份

必须全部通过：`Q_prop/Q_fit/Q_audit` 三组query local-index两两交集均为0且 `Q_audit∩old512=0`；validation/held-out拒绝；audit role在execution lock前拒绝；candidate base-ID范围/唯一性；single-entry实际消费；count/plain/repeat返回一致；GT后置；分块恢复与exclusive output；所有SHA/shape；树边界、同分、空叶与导出一致性。G0失败是实现失败，不解释方法。

### G1：候选与分解

完整报告 `oracle_C-oracle_H`、`oracle_C-oracle_P`、`oracle_P-routed`、H 外候选成为严格最优/并列最优/被实际路由的比例，以及 rescued/newly-harmed。`oracle_C` 不提高不能单独否决，因为 H 外动作可能与 H 同 utility 但更易选择；oracle 提高也不能让 B 通过。

### G2：机制主 gate

主比较为 `joint_C-coverage_C`、`joint_C-oracle_marginal_C`、`joint_C-oldH_joint_m`，四个 dataset×L 点全部保存，共12项主族。推荐的待批准最低条件：

- 20,000次固定seed query-paired bootstrap，同时保存普通95%与Bonferroni-12全族95%区间；同一数据集的两个L及三个比较共享重采样行；
- 三项比较各自的四点非加权mean routed Recall至少`+0.10 pp`；
- 对每个数据集、每项主比较，至少一个L的全族区间下界`>0`；
- 任一主族点的mean不得低于`-0.10 pp`；
- 对每个数据集，至少存在一个L同时满足 `P_{dataset,L}∩E≠∅` 且audit上实际路由到E的query比例≥1%；H外机制归因由已定义的 `joint-oldH_joint_m` 主比较承担，不另造事后“消融”；
- 收益不依赖更大 m、更深 F、额外标签或使用 audit 再选择。

`frequency_m`、三个逐seed `random_m`、`full_H_F`、可由paired-fast20K route ID查本版single矩阵得到的Fast1及全部分解必须同表报告；random逐seed及其预先定义的等权seed均值均保存。Fast3是真实三入口联合搜索，不能把三列single hit相加伪造，故不在G2生成或报告，留待另行授权的G3真实运行。上述描述性控制不混入12项主族，也不作为未定量的事后veto；若出现反常结果，只能降低机制解释并触发后续独立审查，不能改变已冻结的G2 PASS/NO_GO。上述统计family、置信水平与最小实质差仍须用户确认；若任一冻结gate失败，状态为 `NO_GO_THIS_B_CONFIGURATION`，不在同一audit上扩C/m/F/轮数。

### G3：完整成本（条件执行）

只有G2通过才另立一份经用户审定的纯wall协议，然后才实现／运行 evaluator；本R0和11.1M质量pilot的批准不自动授权G3。该协议至少须在运行前冻结：仍只使用本版1024条 `Q_audit` 的timing row顺序、从 `Q_fit` 取且不计时的128条warmup、每点五次独立full-batch wall、跨方法／L轮换顺序、cache与线程状态、paired-fast20K Fast1/Fast3及coverage/oracle-marginal/joint/强基线列表、调用数与累计wall上限、paired Recall和wall统计、相邻点Recall–QPS PASS/NO_GO。计时包含路由、入口映射/初始化和图搜索，排除GT/hash/JSON/count；routing、graph、total wall/NDC分列。G3不占用也不借用11.1M标签/parity上限的177,312余量。包括G3在内，本pilot都不得访问validation/held-out；只有方法冻结、三独立构建及开发门槛通过后，才另立正式阶段申请使用held-out。

## 8. 资源与停止上限

- G0+fit/audit标签+所列parity：全版本累计最多11.1M次原kernel调用、累计30分钟搜索进程wall；不是每job各30分钟，恢复/失败调用照计；首个重任务观察约一分钟后按实测吞吐更新ETA；
- 单重进程，16线程；RSS≤16GiB；
- 新版本全部产物≤1GiB，且 `/data` 始终保留≥10GiB；
- 全部树/pool拟合累计elapsed wall≤1小时、RSS≤8GiB；另记录累计`cpu_seconds`，不把多线程CPU time混叫wall；
- 任一上限触发即保存已完成块与状态并停止，不扩大预算；
- 长任务使用独立日志/结果和持久进程身份，不从旧 state 猜测重启。

上述6–8分钟纯搜索是由旧诊断吞吐线性外推，不是本方法实测时间或QPS结论。

## 9. 待实现接口与 artifact schema

接口名只描述职责：

1. `prepare_b_candidates`：显式 source manifest/row IDs；输出 split ledger、C/E IDs、频率/去重记录、拒绝路径与SHA；
2. `bench_single_utility`：原 single kernel、任意固定C、分块、调用硬限、exclusive output、completion marker；按 role 分离输出，且没有完整 execution lock 时拒绝 audit role；
3. `fit_b_joint`：只读 fit 标签；保存每折、每轮、每个被评估交换和接受理由；
4. `score_b_audit`：要求 pool/model/config lock SHA，单次读取 audit 标签并输出 aligned 比较；
5. 条件性的 `bench_b_pure_wall`：仅G2通过后实现。

建议目录：

```text
entry_method_exploration/<approved_version>/
  protocol.json
  config.json
  state.json
  inputs/{source_manifest,split_ledger,candidates}/
  labels/fit/<dataset>/L{64,128}/{blocks,complete.json}
  labels/audit/<dataset>/L{64,128}/{blocks,complete.json}
  models/<dataset>/L{64,128}/{folds,final}/
  audit/{aligned_results,bootstrap,report}/
  logs/
  reviews/
```

所有未测值写 `null + reason`。只有 `complete.json` 和 state 的终态共同证明阶段完成；文件存在或进程曾启动不够。
