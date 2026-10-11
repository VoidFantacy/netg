# E176 费用账本字段草案（DRAFT，尚未填实测终值）

本文件仅定义最终交付的费用与解释字段。编写期间 formal native 在运行；未读公共返回、GT、metrics、QPS或任何比较数值，未运行数值分析。本文件不是执行收据、资格证明或完成判定。冻结的22源、原报告生成器及科学矩阵均不修改。

最终另附 `analysis/final_v1/cost_ledger_supplement.md` 和对应 JSON，引用实际原件路径、SHA、字段名、计时边界和未知项。仅在两个正式 job 结束、native completion 接受、实际评价和独审完成之后填账；数值和执行状态不得由本草案补造。

## 计时层级与入账规则

- 每项记录 `source_path / source_sha256 / field_path / actual_value / unit / timer_scope / parent_cost_id / additive / eligibility / unknown_reason`。未记录的耗时或失败的未知耗时保持 `null`；不以0补缺，不把静态接口修正写成实际执行失败。
- 采用互不重叠的最外层实际阶段计时组成“已计量本轮成本”；如果只记录了内部计时，只能列“已计量内部范围”，不能称完整生命周期总价。外层计时覆盖的内部子计时作为解释细分，`additive=false`。
- 行政 preparation、hash、编译、模型加载、layout构建、资格校验、完整 native、评价、独审、绘图和报告均分别登记。新 FIT 的900秒资格账与整个研究活动费用账范围不同。
- 三轮点级完整 Batch wall 是 online QPS 分母；整 native job wall 还包括加载、binding、warmup、full plain oracle、count audit、serialization等。点级计时已经包含在整 job 内，不再次相加；不能用整个 job 除查询数替代已保存的点级 QPS。
- setup/layout 的内计时、原生 helper/score/count统计都不能从整 wall 中直接扣除或视作某一操作的 wall 占比。

## 最终应登记的实际收据与字段

以下均为字段方案，不在此填写执行数值。

| 成本项 | 原件与字段 | 最终入账与范围 |
| --- | --- | --- |
| FIT 编译 | `reviews/fit_build.json`: `elapsed_seconds`, `argv`, `exit_code`, `log`, source/binary SHA | 使用真实编译收据；如果另有包含它的完整外层计时，内项只解释而不重复加。 |
| FIT 预检/准备 | `reviews/fit_preflight.json`: `elapsed_seconds`, `stage`, source identity/stat与split说明 | `prepare_fit.py` 内部计时截止收据生成附近，不能自动称 Python 全生命周期；真正外层若未计量，保留该缺口。该阶段在新增 FIT 900秒 pipeline 外。 |
| Web/Y 两次新增 FIT | `reviews/fit_execution.{dataset}.json`: `elapsed_seconds`, `cap_seconds`, `stages`, `model_eligible`, `full_process_lifecycle_included`；`fit_state.json.completed` 是这些收据的登记副本 | 每数据集收据只计一次；状态副本不另计。包含 native/compiler 子进程完整生命周期及计时区间内的阶段切换，但 budget `elapsed_seconds` 在最终 manifest读取/hash及行政收据写入之前取值，后者不是0成本。 |
| FIT native 子计时 | 每数据集 FIT 收据 `stages[0].elapsed_seconds/argv/exit_code/log`；`fit_results/{dataset}/complete.json` 的 `elapsed_seconds`, `loading_and_binding_seconds`, `route_seconds`, `main_seconds`, `original_m5_seconds`, `oracle_seconds`, `serialization_seconds` | 父层为该数据集 FIT budget wall；子项不重复加。原生内部计时又内含于 native subprocess wall，不能再加到 pipeline总额。 |
| Compiler 子计时 | 每数据集 FIT 收据 `stages[1].elapsed_seconds`；`models/{dataset}/compile_manifest.json`: `compiler_elapsed_seconds`, `native_response_generation_elapsed_seconds`, `source_hash_seconds`, `label_decode_seconds`, `point_stages`, `models.*.*.seconds_including_model_serialization_hash`, `compiler_max_seconds_remainder` | 记录准确嵌套。`native_response_generation_elapsed_seconds` 是先前 native费用的回引；`compiler_max_seconds_remainder` 是剩余上限，不是实际花费。内部 compiler timer 不替代完整子进程 wall。 |
| 两集 FIT 新增总量 | `run_state.json.training_increment_seconds`；`fit_state.json.completed[*].elapsed_seconds` | 前者是两数据集 budget计时的登记总量，不是在两条FIT费用之外第三条成本。最终核值闭合；不在运行期间计算。 |
| 历史 TRAIN 债 | 每数据集 FIT 收据 `historical_TRAIN_seconds`, `cumulative_TRAIN_with_this_increment_seconds`, `historical_cost_reset`；冻结原模型/旧训练manifest的原账 | 将历史已付/已曝光监督成本作为继承债单列，不能因本轮 `test_no_training` 或新的900秒许可归零。旧缺失或未计量标签、构图、原模型成本保持“继承未计量”，不重新运行或估为0。新旧窗口的 source/role tuple继承历史，本次exact-byte TRAIN/public去重不重证全部历史语义独立性。 |
| 公共数据准备/模型冻结 | `reviews/data_preflight.json.elapsed_seconds`（`prepare_formal.py`），`reviews/preexecution_acceptance.json` 的实际计时字段（若有） | 原公共10K源和既有GT继承，当前byte identity/模型SHA准备费用单列；内计时不是Python完整生命周期。静态/行政收据无计时则保未知。 |
| Formal native 编译 | `reviews/build.json`: `elapsed_seconds`, `argv`, `exit_code`, `source_sha256`, `binary_sha256` | 与FIT编译是不同编译动作，分别登记；不把已保存前轮构建时间充作新同步成本。 |
| 资格完整外层 | `reviews/qualification_execution.json`: `elapsed_seconds`, `argv`, `exit_code`, `log`, qualifier/source binding（以实际schema为准） | 这是完整 qualifier进程生命周期的成本入口。原冻结 writer的 `receipt_names` 漏此文件，最终 supplement必须补列，保持原writer字节不改。 |
| 资格内部整段 | `reviews/native_qualification.json.whole_elapsed_seconds`, `cost_scope`, `source_identity`, `jobs`, `comparisons`；`qualification_state.json` 为状态副本 | 内计时截至最终资格收据/state序列化之前，包含元数据/hash、job生成、两串行子进程及prefix校验等；不是外层完整脚本 wall，`additive=false`。状态副本不另计。 |
| 两个资格子进程 | `native_qualification.json.jobs[*].elapsed_seconds/exit_code/argv/log/peak_rss_bytes_observed/max_threads_observed/native_calls` | 包含已退出和清理的完整 child生命周期；内含于资格整段以及外层，不再次加。资格16查询前缀不能作为10K性能、Recall或新确认。 |
| 两个 formal native 整 job | 最终 `run_state.json.completed[*].elapsed_seconds`, `exit_code`, `argv`, `max_threads_observed`, `peak_rss_bytes_observed`, `rss_scope` | 两个实际T1 child完整执行/退出的 job耗时分别入账。RSS按约0.25秒 `/proc` 样本记录，不声称精确峰值；两集峰RSS不相加成“峰内存”。全部正式结束之前不填写本项。 |
| Native加载/layout/resident解释 | 每job `native_environment.json.startup_seconds`, `optimized_layouts[*].startup_seconds/startup_graph_reads/startup_trimmed_slots/resident_bytes`, `completion_tables[*].rows/resident_bytes`, `complete_distinct_posting_resident_bytes`, `complete_posting_completion_layout_resident_bytes` | 全部内含于native job，不加到其wall。原posting共享、模型/布局resident语义按保存字段保留，不能把resident字节当artifact磁盘字节。无wall因果归因；扫描计数不等于其耗时占比。 |
| Evaluation完整进程 | `reviews/evaluation_execution.json.elapsed_seconds/argv/source_sha256/exit_code/log` | 使用实际外层process计时。读已有冻结结果/GT不生成新教师，其计算成本仍登记。 |
| Independent audit完整进程 | `reviews/independent_audit_execution.json.elapsed_seconds/argv/source_sha256/exit_code/log` | `argv`/SHA须指向实际行政schema v2；原v1缺重复sidecar是静态发现，不冒充v1已执行失败，也不伪造失败耗时。v2补充锁独立保存。 |
| Plot完整进程 | `reviews/plot_curves_wrapper_execution.json.elapsed_seconds/argv/source_sha256/exit_code/log` | 采用实际外层；`reviews/plot_curves_execution.json.elapsed_seconds` 是内计时，截止自身收据写入前，`additive=false`。主图与机制图同一stage不能各算一次整个stage。 |
| Report完整进程 | `reviews/report_wrapper_execution.json.elapsed_seconds/argv/source_sha256/exit_code/log` | 最后由外层落账。`reviews/report_generation.json.elapsed_seconds` 为原冻结writer内计时，无法在它自己生成的report正文中声称自身最终外层总耗时；只在后置supplement补列。 |
| 行政修正/独立复核/交付补充 | 原静态source/schema review和实际后续supplement执行收据（若有） | 审阅或写文档未被实际计时则未知；PASS字符串不是费用记录。不得把静态脚本准备或漏接口修正伪造成native/GT失败或新实验。 |

## 新增 FIT 资格与完整费用边界

用户授权的新增 FIT cap为每数据集900秒：使用旧合法20K TRAIN窗口、K=1/100与五档L，生成原M5实际最终返回和逐route C winner，监督为旧GT_K减去原M5最终返回，再编译pair/route残差表。cap计时定义继承冻结 `run_fit.py`，不能把授权cap当实际已花时间；两数据集都完整且eligible才可进入formal。

每次 FIT budget timer覆盖完整 native/compiler subprocess生命周期；其最后取值之后的manifest读取/hash和行政写收据、FIT准备/编译、资格、formal query均需在研究活动账明确另列或未知。若实际还存在计量更完整的FIT pipeline外层收据，采用该外层并将两900秒资格计时标为内含子项，不重复求和。

`no_training=true` 是formal test的操作约束，不意味着整个E176没有新增拟合。不以先前TRAIN超cap消灭旧债，也不把这次追加许可重写为原训练预算一贯合规。

## 冻结 writer的已知费用省略如何交付

原 `write_report.py.elapsed()` 只识别 `elapsed_seconds / actual_elapsed_seconds / total_elapsed_seconds`，不识别 `whole_elapsed_seconds`；它会把 `native_qualification.json` 的内计时显示为 `None`。原receipt列表也漏 `qualification_execution.json`。

最终保留原report、原writer、其来源SHA及这处诚实省略；另以supplement逐字段补入资格外层和内层，并说明两者包含关系。不能重写原source让旧report看似从一开始完整计费。报告自身外层费用也需后置补充；未知行政或历史成本仍未知。补充本身若另有实际计时，应注明截止点而不循环声称已包含自身所有后续写入。

## 全800个冻结比较的QPS定义与最终解释

该段是后续保存字段解释方案，现在不读取或计算任何比较。

令工作点A/B的三轮已保存QPS分别为 `a_r/b_r`。

- 预锁比较的主速度量是 `paired_ratio = median_r(a_r / b_r)`；saved `paired_qps_change_pct` 与 `observed_joint_gain` 沿用此定义。
- 曲线各点展示 `median_r(a_r)`；两点视觉速度比是 `point_median_ratio = median_r(a_r) / median_r(b_r)`。一般不恒等于 `paired_ratio`，不能互相替代。
- 最终在独审已通过的 `metrics.json` 上，对全部800预锁比较（560同L、240小L对大GT）逐个登记：两原工作点身份、saved paired ratio、保存point medians之比、两种速度符号、严格joint标志及是否相反。所有比较均列，不依据测试结果筛选。这个补充是确定性保存字段解释，不新跑ANN、GT、distance、bootstrap，不改原saved主指标或门。
- 若两种速度判定不一致，明确说明“预锁paired三轮比”与“曲线上点中位数”的不同；不将任一另一种事后口径用于把原未过门比较改写为过门。最终joint描述注明具体速度定义。
- 同L的round配对是相同KL内顺序方法的同轮；跨L只按round index描述性配对，非同时执行、非随机匹配。三轮min/max、`all_rounds_faster`、`speed_ranges_separated` 可按保存字段并列，不声称它们等价或提供同时显著性保证。

## 执行与保全约束

本草案只新增说明文件。后续填账不改源、不改原metrics/raw/manifest/locks，不重跑GT/CI/距离/实验，不读取大base或query向量。源码或行政修正产生的新receipt须绑定真实SHA及scope；实际failed/null也保留。最终展示已计量费用、继承债、未知费用和范围缺口，不能将不完整账宣称为无遗漏总成本。
