# 方向 A：有界 systems/empirical 表示诊断协议草案

> 状态：`UNAPPROVED_OPTIONAL_REFERENCE`。  
> 只有用户明确选择 `REOPEN_A_AS_BOUNDED_SYSTEMS_EMPIRICAL_DIAGNOSTIC` 后，才可据此建立新的批准版本。本草案未获批准、未执行；下文工具名均为待实现职责，不是当前可执行命令。

## 1. 目标与定位

本草案只检验：在 H、raw-IP base、冻结 NSG、原 single-entry kernel 和总 facet 数不变时，有限-L全H真实效用驱动的非均匀多面表示，能否在隔离的历史-development audit 上优于同 M 的普通多原型与通用增删基线，并在支付微索引和图搜索完整 wall 后保留收益。

即使全部通过，也不声称：

- 首次提出每类多个 hyperplane、latent structured hinge、prototype add/prune 或 flat multi-vector MIPS；
- 同 L Recall 等于同 wall Pareto；
- 训练表 regret 上界是未知 query 的 Recall 保证；
- 一次固定图/固定构建的 development audit 等于 fresh test；
- exact facet scan 的质量等于 approximate micro-index 的质量或成本。

若用户仍以强算法 novelty 为硬要求，本草案不应执行，直接关闭 A 并进入 C 的 R0。

## 2. 授权边界

“接受 systems/empirical 定位”只允许另建版本、补齐协议锁并实施 G0 与 G1/G2 的有界质量诊断；它不自动授权 G3 wall、validation、held-out 或正式三构建。

新版本启动前还须由用户确认：

1. 唯一 adaptive 算法及 `2H/4H`、每hub上限、优化器、正则、seed、epoch、重分配批量和最多四轮；
2. 比较族、bootstrap和实质阈值；
3. 标签4小时、训练8小时、20GiB RSS、1GiB artifact与72,227,776次from-zero调用硬上限；
4. 只在parity保存完整top10 IDs，还是把artifact上限提高到5GiB；
5. v4 utility tree 在首轮并列还是 exact 表示通过后补齐；
6. G2通过后是否另批 G3，以及微索引参数网格和允许的exact→approx损失。

这些选择未锁定前，不写代码、不生成新标签，也不打开 calibration/audit utility。

## 3. 冻结搜索合同

| 项目 | WebVid | Yandex |
|---|---:|---:|
| dataset key | `webvid2_5m_light_v1` | `yandex_t2i_official10M_ip_v1` |
| base | 2,505,000×512 | official first 10,000,000×200 |
| metric | raw inner product；不为 A 改搜索归一化 | raw inner product；不归一化 |
| graph | 原 R64/Lbuild100/C512 NSG | 同左 |
| H | 815个真实base ID | 821个真实base ID |
| K / L | K10；L64与L128分别建模 | 同左 |
| kernel | 原 `ACSG::search_new(mode=2)`，单入口 | 同左 |
| 资源并发 | CPU-only；同一时刻一个重数据集进程；最多16线程；BLAS单线程 | 同左 |

A 固定 H，不发现、替换或重排 hub 集合；否则与 B 混杂并终止本版本。base、metric、normalization、graph、H、query split、GT、kernel 或 tie 定义任一变化都会使相关标签身份不兼容。R0 的 `source_manifest.json` 只是证据快照；执行锁必须直接重验实际 base/query/GT/graph bytes、hub IDs、原库、新 runner、trainer、scorer 和 evaluator，不能只绑定 `.info`。

facet 分数固定为：

```text
s_h(q)   = max_j (q^T w_hj + b_hj)
h_hat(q) = hub(argmax_{h,j} ([q;1]^T [w_hj;b_hj]))
```

exact tie 固定按 `(score降序, real_hub_id升序, facet_ordinal升序)`。任何训练标准化只用 fit 统计并精确折入导出仿射权重；facet 不作独立 cosine 归一化。每个 query 最终只映射一个真实 hub，原 kernel 只消费该 single entry。

## 4. Query ledger 与访问隔离

统一使用 `router_train local_index`，不混用 WebVid source-corpus row：

1. `Q_fit=[10000,30000)`，每数据集完整20K。按冻结 SHA key 分成四个内部fold；这些fold用于 proposal/acceptance 轮换和全部训练，不作外部推断。
2. 在前10K中以 local-index 域排除 Fast 根因诊断旧512行；对余下行按冻结 `cal` hash 取1024为 `Q_cal`。
3. 再排除 `Q_cal`，按独立 `audit` hash 取1024为 `Q_audit`。audit只在模型、scorer、配置、统计及所有代码SHA锁定后生成/打开标签并评分一次。
4. validation 与 held-out 的 query/GT canonical realpath 和内容SHA加入拒绝表；本版本不得通过软链接或路径别名打开。

建议哈希键仅作待批准默认：

```text
SHA256(dataset_key + "|a_systems_diag_v1|" + role + "|" + decimal_router_train_local_index)
```

ledger至少记录 `router_train_local_index`、可用时的source row、role、fold、所有allocation hash、query/GT来源SHA、旧512排除清单SHA、集合交集计数与拒绝路径。两个开发集合都有历史暴露，只能称calibration/audit，不称fresh held-out；本版主Fast对照使用paired-Fast20K，旧实验中的formal30K/target-basin基础Fast只保留为历史身份，不能混入主比较。

trainer进程只能读取 fit role；calibration只选择一次全局预算/配置，不回写候选算法；audit目录在 execution lock 前必须不存在或由 scorer拒绝。主Fast1/Fast3对照固定为manifest所列QGT-Cover hub IDs与`paired_fast20k` prototype（后20K fit身份），其路径和SHA进入execution lock。历史旧30K Fast只作明确标注的旧参照，不进入本版主比较或替代paired-Fast20K。audit评分后不得重训、换阈值、改索引网格或再建第二个audit。

## 5. 全 H 标签、复用和验收

待实现的 slim label runner 必须显式接收 role、row-list、hub-list、L、K和输入身份，逐chunk调用原 `search_new(mode=2)`。可复用旧诊断中的 single-entry adapter、入口消费审计、aligned count/mask/NDC schema和分块完成思想，但不能直接把旧 binary 当新 runner：它强制生成旧 prototype/组合产物、拒绝已有输出目录，且不支持按role安全恢复。

每个 `(query_id, real_hub_id, L)` 保存：

- `hitcount:uint8`；
- `GT10 hitmask:uint16`；
- `graph_ndc:uint32`；
- query row、真实hub ID、L/K及全部输入/代码身份；
- 仅在确定性 parity 行保存完整 top10 returned IDs/distances。

GT只在 native search 返回后计算mask/count。主损失使用整数Recall regret并保留全部exact ties；NDC不进入主label，只用于报告或预注册的同Recall tie-break。count版本的wall/QPS不可发布。

先用每数据集8条fit parity行检查全H、两个L的 `count/plain/repeat` 返回ID、距离、mask、count、NDC与入口顺序；共 `8×3×2×(815+821)=78,528` 次。通过后才生成fit标签。cal标签在fit模型族实现冻结后生成；audit标签最后生成。

现有全H诊断中的255条WebVid、256条Yandex辅助fit行，理论上最多对应：

```text
255*815*2 + 256*821*2 = 836,002 cells
```

只有完整匹配 `(query ID, real hub ID, L, K, base, metric, graph, kernel, label schema)` 且确属 `Q_fit` 的cell可由复用ledger引用。旧512 pilot及任何audit cell一律不复用；不能按数组位置盲拼。复用节省同时报告为共享研究成本和每方法从零成本，不能用于增加query、面数或轮数。

## 6. 模型族与参考 adaptive 算法

每个数据集、每个L独立训练，但一个全局配置必须用于四个 dataset×L 点。所有模型共享 raw query、全H标签、fit/cal/audit row和总面数M。

### 6.1 必须同场的模型

1. `one_facet_regret`：一面/hub，tie-aware regret loss；
2. `equal_mprot_regret_M`：每hub固定2或4面、同一latent regret目标；
3. `equal_mprot_hardid_M`：相同面数和优化预算，按预先固定的最优hub代表做普通hard-ID margin/CE消融，同时保留ties统计；
4. `geometric_mprot_M`：在hub为exact-good的fit query内作固定seed几何聚类，同M，随后用同一训练预算；
5. `gamm_clone_prune_M`：按AMM/GAMM作者机制公平适配clone+prune，不读取A专用rescue/harm接受量；
6. `adaptive_lvq_add_remove_M`：按adaptive-LVQ在跨类全局prototype硬上限B下增添有益prototype、删除有害/少用prototype的机制公平适配；
7. `sparse_mprot_fusion_M`：实现Sparse Multi-Prototype式fusion/group稀疏控制，并以同M导出；
8. `finite_L_regret_allocate_M`：下面的系统适配候选；
9. Fast1、真实Fast3及v4 utility tree按获批范围并列。Fast1/Fast3使用锁定的paired-Fast20K身份；Fast3必须真实运行，不能把三列single hitmask并集冒充联合搜索。

若作者基线不能在多label ties与cost matrix上逐位移植，执行锁必须事前冻结最小适配、列出不对齐项并同时保留原hard-label版本；不能因适配困难删除通用增删对照。

### 6.2 `finite_L_regret_allocate_M` 参考轮廓

1. 以 `equal_mprot_regret_M` 初始化，每hub至少一面。
2. 四个fit fold按预登记轮换；某轮只在proposal folds计算候选，在未参与proposal的acceptance fold评分，fold角色按轮号固定。
3. proposal上逐面做suppress-one回放，得到移除该面造成的真实mean-regret增加和route support；同时对 `h∈G_i` 且当前route有正regret的行，按当前regret累计hub未满足mass。
4. 每轮批量固定为 `ceil(0.05M)`，但不超过可删除面数。按 `(removal harm升序, support升序, hub ID升序, facet ordinal升序)` 选择删除槽，且每hub保留至少一面；按 `(unmet mass降序, hub ID升序)` 分配同数槽，并受执行锁中的每hub cap约束。
5. 新面由目标hub冲突行的regret加权query方向作确定性初始化；bias、gauge和零样本回退在执行锁中唯一化。随后用相同epoch/优化器重拟合全部面，不给候选额外训练预算。
6. 在acceptance fold比较整批加入前后真实route；只有预注册mean-regret降低、rescued/newly-harmed约束和最坏点同时通过才接受。失败立即停止，不缩批、不换seed、不改变目标。最多四轮。

该轮廓刻意有界，但仍是通用多原型增删的ANN适配，不声称新算法。fit内部fold因反复参与选择不是无偏test；唯一主推断来自最终一次audit。

## 7. Calibration、audit与推荐统计合同

下面数值是**待用户批准的推荐默认**，不是当前有效gate。

### G1：calibration

仅比较M=`2H/4H`及执行锁中的有限固定配置。对每个控制模型c和四个dataset×L点p，先计算`Delta(c,p)=mean_regret(c,p)-mean_regret(candidate,p)`，正值表示candidate更好；配置分数固定为所有`(c,p)`上的最小Delta，并最大化该分数。这里的c分列为equal-quota regret、geometric、GAMM、adaptive-LVQ与Sparse Multi-Prototype控制，绝不按query拼接一个oracle-best控制。分数同分依次选择2H、较少已接受轮数、较小seed。calibration不得按数据集/L分别选模型，也不得生成新算法变体。

### G2：exact representation audit

主比较建议固定为adaptive exact scan相对：

1. equal-quota regret maxout；
2. geometric multi-prototype；
3. GAMM-style clone-prune；
4. adaptive-LVQ-style add-remove；
5. Sparse Multi-Prototype-style fusion/sparsity。

五项×两数据集×两L形成20项主族。对1024 paired queries做20,000次固定seed bootstrap，同时保存普通95%与Bonferroni-20全族95%区间。推荐最低条件：

- 每项比较的四点非加权mean Recall增益至少 `+0.10 pp`；
- 每个数据集、每项比较至少一个L的全族下界 `>0`；
- 任一主族点mean不得低于 `-0.10 pp`；
- 相对one-facet与Fast1四点mean均为正，且没有点低于 `-0.10 pp`；
- adaptive容量确实非均匀，所有模型满足同M/bytes/训练预算；
- 完整报告mean regret、Recall、rescued、newly harmed、ties、facet support、每hub面数、稀有hub与全部失败点。

hard-ID、random/frequency/conflict-mass allocation、Fast3与v4树按预注册身份报告；是否进入主族必须在audit标签生成前决定。任一主门失败即`NO_GO_THIS_A_SYSTEMS_CONFIGURATION`：不追加M、轮数、网络、query encoder或第二个audit。G2通过仍只是exact表示通过，不是部署GO。

## 8. G3：条件性的部署与纯 wall

G3必须在G2 PASS后另行授权。先比较同一导出权重的：

1. exhaustive all-facet score；
2. flat exact inner-product top1；
3. approximate micro-index top1，再映回hub。

微索引必须使用真正的`d+1` inner-product语义。插入顺序、seed、M、efConstruction、有限efSearch网格及唯一选择规则都在G2 audit前预注册；但网格的实际执行和选择只允许在G2通过并另获G3授权之后发生，且只使用已冻结的cal行。推荐要求approximate相对exact的Recall损失不超过exact adaptive对最强同M基线audit收益的25%，且不能改变最终模型或重新打开cal选择新面。

只有近似质量通过，才实现端到端 evaluator。做五轮独立full-batch timing rounds，跨方法/L轮换顺序并冻结warmup、cache和线程状态；这五轮是同一批query的计时重复，不是五个独立Recall样本或独立build。计时包括query拼接/预处理、facet路由、映射、入口初始化、visited/reset、原图搜索和必要结果写入，排除GT/hash/JSON/count。routing-only、graph、total wall和NDC分列。Fast1、真实Fast3、exact/approx facet、同M强基线和按批准范围的v4树使用同一row顺序。

同L质量、MAC、micro-index recall或graph NDC均不能替代完整Recall–QPS。开发G3通过后，正式三构建与held-out仍需独立协议和授权。

## 9. 成本与硬停止

完整逻辑标签调用：

```text
fit         = 20,000 * 2 * (815+821) = 65,440,000
cal+audit   =  2,048 * 2 * (815+821) =  6,701,056
labels total                            72,141,056
parity                                      78,528
cal+audit Fast3                              8,192
listed quality-stage from-zero total    72,227,776
```

参考硬上限（均待批准）：

- 搜索/标签累计wall≤4小时，所有失败与恢复调用计入72,227,776上限；首任务约一分钟后才用本版吞吐估ETA；
- 包含equal/geometric/hard-ID、分列的GAMM、adaptive-LVQ、Sparse Multi-Prototype及候选在内，全部模型拟合累计elapsed wall≤8小时，同时记录CPU seconds；超限即停止而不是删基线；
- 单重进程、最多16线程、RSS≤20GiB；
- 默认新artifact≤1GiB，始终保留`/data`≥10GiB；若全cell保存top10 IDs则改为≤5GiB并重新核算；
- G3不占用质量阶段剩余额度，必须另批调用、wall与artifact上限；
- 任一上限触发即保存完整chunk/state并停止，不扩大样本、M、轮数或重跑audit。

72.14M标签的旧E20吞吐线性外推约为数量级参考，不是本版实测ETA，也不是可发布QPS。依赖安装/编译不算方法实验；本方向不需要MUVERA、RoarGraph或新训练环境，不能让外部MKL/OpenMP设置污染正常计时。

## 10. 待实现职责与 artifact schema

接口名仅描述职责：

1. `prepare_a_split_ledger`：显式manifest、row ledger、拒绝路径、复用cell账本和SHA；
2. `bench_a_single_utility`：role隔离、原single kernel、任意row/hub chunk、调用硬限、恢复及exclusive completion；
3. `fit_a_facets`：只读fit标签，导出每模型/fold/round/seed的facet、映射、优化与接受账本；
4. `score_a_exact`：C++/Python双实现exact scorer、全部tie与rescue/harm对齐；
5. `score_a_audit`：要求完整lock SHA，只读一次audit并输出主族统计；
6. 条件性 `build_a_micro_ip` 与 `bench_a_pure_wall`：仅G2 PASS且另获授权后实现。

建议批准版目录：

```text
entry_method_exploration/<approved_version>/
  protocol.json
  config.json
  state.json
  inputs/{source_manifest,split_ledger,reuse_ledger,execution_lock}/
  labels/{fit,cal,audit}/<dataset>/L{64,128}/{blocks,complete.json}
  models/<dataset>/L{64,128}/{folds,cal_selected,final}/
  audit/{aligned_results,bootstrap,report}/
  index/<dataset>/L{64,128}/
  wall/
  logs/
  reviews/
```

所有未测量值必须写`null + reason`。文件存在或进程曾启动不等于阶段完成；每个role的`complete.json`、state终态、调用账本和独立审查必须共同一致。
