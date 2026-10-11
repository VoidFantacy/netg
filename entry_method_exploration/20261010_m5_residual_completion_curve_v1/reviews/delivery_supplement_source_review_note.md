# delivery_supplement.py 源码审阅说明（DRAFT；未执行）

新源：`src/delivery_supplement.py`。当前 SHA256：`6d908055aa2d1c92c834f6a0056e9f1f50269900969448923c97919d60f7b1b9`。仅对源文本做 AST.parse；没有 import/execute 本模块，没有读当前 public结果、metrics、GT、返回或计时比较。原22冻结源与已审计v2行政adapter不修改。

## 运行门与输入边界

进入保存字段之前，严格要求 `run_state.status=NATIVE_COMPLETE_PENDING_INDEPENDENT_GT_EVALUATION`、`active=None`、两dataset/public_test job exit0，以及实际独审 `reviews/independent_result_audit/report.json` 的 E176160点/480批次/800比较资格。metrics/points.csv/comparisons.csv 必须与实际独审登记的 SHA+stat4 完全相同。

原report须已生成；这是最终补充附件，实际运行应在原report stage完成后。原 `evaluate.py/write_report.py` SHA仍对原execution锁闭合，原protocol/v2行政补充锁也核绑定。所有读取均由 bounded small-source helper登记SHA/stat4并在结束复核；不打开向量、rawGT/returns/trace、模型二进制、大base/graph、距离或任何训练教师标签。只读保存JSON/CSV和必要源码/小型行政身份文件。

该新源尚未执行或被宣布科学完成。root应静审此说明对应实际源字节后，按自己的实际执行授权运行；后续实际运行收据应登记 argv、source SHA、退出码与完整外层elapsed。

## interpretation输出

- 新建 `analysis/final_v1/interpretation.csv` 和 `.json`；原 metrics/report不改，任何已有/partial补充文件均拒绝覆盖。
- 所有800原比较逐个保留、无筛选，验证560同L+240跨L，全部原字段（包括paired ratio、observed_joint_gain、all_rounds_faster、speed_ranges_separated与CI）原值保留，并对原 comparisons.csv核字段一致。
- 新字段只使用现有 point.qps_median：`ratio_of_saved_point_qps_medians`、`point_median_qps_change_pct`、`strict_joint_point_medians`、`strict_joint_both_definitions`、速度/双升两口径分歧标志及两个点的原身份。严格门为原saved Recall delta>0且新比值>1，不用epsilon，不将该事后展示口径替换原paired门。
- summary对全部/同L/跨L分别计已保存口径和交集；保全每个原比较，而非只列双升。跨L配对仅round-index描述性。没有重新算bootstrap、GT、成员质量或中间L估计。

## 费用输出与计时层级

新建 `cost_ledger_supplement.json/.md`，实际读取外层资格 `qualification_execution.json` 与四post-native process receipts；显式补充原writer遗漏，保留原report中的诚实None。原生两job采用最终state完整elapsed与sampled RSS；峰值不相加。

FIT build/preflight、每dataset实际900秒budget及native/compiler子进程、旧TRAIN债和累计账单列。新FIT不因formal no_training归零；预算取值之后manifest hash/admin closing成本保留未知。如果确有 `fit_pipeline_execution.json` 外层，必须argv明确为 run_fit.py，采用它而将两个budget计时列为内含，避免重复。不存在该外层时，budget已计量范围入小计，未计量完整run_fit生命周期仍为null。

资格inner `whole_elapsed_seconds` 与两个child、plot/report inner elapsed、native startup/layout/resident metadata均非加法；外层分别是实际qualification与plot/report process receipt。旧compiler manifest native_response_generation 回引前段native，不再次加。administrative failure若实际保存，记录原elapsed或null，未知包含关系不自动加进小计。

费用JSON记录 `known_disjoint_interval_subtotal_seconds`，明确是限定边界的已计量区间小计，`complete_activity_cost_seconds=null`；不将未知/admin/历史未计量填0，不伪造v1实际失败或其耗时。source bindings同时覆盖源、实际metrics/report、audit及读取的每份成本收据。完整supplement进程费用只能由外层未来实际收据补记，不循环冒充包含自身所有写入。

## 当前检查范围

只检查源码与AST语法，以及冻结原evaluate/write_report/run_fit/run_serial/run_analysis_v2中的字段声明。未做虚拟结果测试、没有执行新分析，不将这份DRAFT称为独立审计或实测结论。
