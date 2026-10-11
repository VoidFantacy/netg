# 便携阅读副本

此文件派生自 [cost_ledger_supplement.md](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/cost_ledger_supplement.md)；只转换实际纳入发布的 Markdown 文件链接。实验结论、冻结原件与服务器外部路径不变。

# E176 费用补充：实际保存收据与未计量边界

此附件保留原冻结 report/metrics，补入原writer遗漏的资格外层，并明确内部 whole_elapsed_seconds 的包含关系。

| 项目 | 原件字段 | 实际秒 | 可加到已计量小计 | 父项 | 范围 |
| --- | --- | --- | --- | --- | --- |
| fit_build | [fit_build.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/fit_build.json) `elapsed_seconds` | 7.098643 | 是 | — | actual FIT build receipt interval; complete external wrapper lifecycle not inferred |
| fit_preflight | [fit_preflight.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/fit_preflight.json) `elapsed_seconds` | 0.286051 | 是 | — | prepare_fit internal administrative/source-identity timer; excludes unmeasured earlier/later orchestration |
| fit_pipeline_outer | [fit_pipeline_execution.json](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/fit_pipeline_execution.json) `elapsed_seconds` | null（未计量/未登记） | 否 | — | complete run_fit process lifecycle, if actual external process receipt exists |
| fit_budget_webvid2_5m_light_v1 | [fit_execution.webvid2_5m_light_v1.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/fit_execution.webvid2_5m_light_v1.json) `elapsed_seconds` | 469.143610 | 是 | — | perDS900 budget timer: both native/compiler full child lifecycles; excludes later manifest load/hash and administrative receipt closing |
| fit_budget_webvid2_5m_light_v1_native | [fit_execution.webvid2_5m_light_v1.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/fit_execution.webvid2_5m_light_v1.json) `stages[0].elapsed_seconds` | 435.726580 | 否 | fit_budget_webvid2_5m_light_v1 | nested complete subprocess lifecycle; included in perDS FIT timer |
| fit_budget_webvid2_5m_light_v1_compiler | [fit_execution.webvid2_5m_light_v1.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/fit_execution.webvid2_5m_light_v1.json) `stages[1].elapsed_seconds` | 33.416477 | 否 | fit_budget_webvid2_5m_light_v1 | nested complete subprocess lifecycle; included in perDS FIT timer |
| fit_budget_webvid2_5m_light_v1_compiler_internal | [compile_manifest.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/models/webvid2_5m_light_v1/compile_manifest.json) `compiler_elapsed_seconds/source_hash_seconds/label_decode_seconds/point_stages` | 33.352583 | 否 | fit_budget_webvid2_5m_light_v1_compiler | nested compiler internal timer and metadata; native_response_generation repeats prior native timer |
| fit_budget_yandex_t2i_official10M_ip_v1 | [fit_execution.yandex_t2i_official10M_ip_v1.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/fit_execution.yandex_t2i_official10M_ip_v1.json) `elapsed_seconds` | 472.986268 | 是 | — | perDS900 budget timer: both native/compiler full child lifecycles; excludes later manifest load/hash and administrative receipt closing |
| fit_budget_yandex_t2i_official10M_ip_v1_native | [fit_execution.yandex_t2i_official10M_ip_v1.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/fit_execution.yandex_t2i_official10M_ip_v1.json) `stages[0].elapsed_seconds` | 448.634244 | 否 | fit_budget_yandex_t2i_official10M_ip_v1 | nested complete subprocess lifecycle; included in perDS FIT timer |
| fit_budget_yandex_t2i_official10M_ip_v1_compiler | [fit_execution.yandex_t2i_official10M_ip_v1.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/fit_execution.yandex_t2i_official10M_ip_v1.json) `stages[1].elapsed_seconds` | 24.351196 | 否 | fit_budget_yandex_t2i_official10M_ip_v1 | nested complete subprocess lifecycle; included in perDS FIT timer |
| fit_budget_yandex_t2i_official10M_ip_v1_compiler_internal | [compile_manifest.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/models/yandex_t2i_official10M_ip_v1/compile_manifest.json) `compiler_elapsed_seconds/source_hash_seconds/label_decode_seconds/point_stages` | 24.291415 | 否 | fit_budget_yandex_t2i_official10M_ip_v1_compiler | nested compiler internal timer and metadata; native_response_generation repeats prior native timer |
| public_prepare | [data_preflight.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/data_preflight.json) `elapsed_seconds` | 0.035131 | 是 | — | prepare_formal internal source/model freeze timer; not assumed full external process lifecycle |
| public_native_build | [build.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/build.json) `elapsed_seconds` | 11.513078 | 是 | — | actual public benchmark build receipt interval |
| qualification_outer | [qualification_execution.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/qualification_execution.json) `elapsed_seconds` | 38.304731 | 是 | — | actual complete qualifier process lifecycle; frozen writer omits this outer receipt |
| qualification_inner | [native_qualification.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/native_qualification.json) `whole_elapsed_seconds` | 38.270648 | 否 | qualification_outer | inner qualifier cutoff immediately before final receipt/state serialization; non-additive |
| qualification_child_0 | [native_qualification.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/native_qualification.json) `jobs[0].elapsed_seconds` | 15.056370 | 否 | qualification_inner | complete owned serial child lifecycle; included in qualifier inner and outer |
| qualification_child_1 | [native_qualification.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/native_qualification.json) `jobs[1].elapsed_seconds` | 23.137311 | 否 | qualification_inner | complete owned serial child lifecycle; included in qualifier inner and outer |
| native_webvid2_5m_light_v1 | [run_state.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/run_state.json) `completed[0].elapsed_seconds` | 6970.796179 | 是 | — | complete owned formal native child execution/exit; includes startup/warm/oracle/count/serialization and timed batches |
| native_yandex_t2i_official10M_ip_v1 | [run_state.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/run_state.json) `completed[1].elapsed_seconds` | 7089.322895 | 是 | — | complete owned formal native child execution/exit; includes startup/warm/oracle/count/serialization and timed batches |
| evaluate_outer | [evaluation_execution.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/evaluation_execution.json) `elapsed_seconds` | 145.978025 | 是 | — | actual sequential post-native subprocess lifecycle; actual argv/source SHA identifies version |
| audit_outer | [independent_audit_execution.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/independent_audit_execution.json) `elapsed_seconds` | 81.193447 | 是 | — | actual sequential post-native subprocess lifecycle; actual argv/source SHA identifies version |
| plot_outer | [plot_curves_wrapper_execution.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/plot_curves_wrapper_execution.json) `elapsed_seconds` | 1.265668 | 是 | — | actual sequential post-native subprocess lifecycle; actual argv/source SHA identifies version |
| report_outer | [report_wrapper_execution.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/report_wrapper_execution.json) `elapsed_seconds` | 0.062433 | 是 | — | actual sequential post-native subprocess lifecycle; actual argv/source SHA identifies version |
| plot_inner | [plot_curves_execution.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/plot_curves_execution.json) `elapsed_seconds` | 1.192732 | 否 | plot_outer | internal plot timer before own receipt serialization; non-additive |
| report_inner | [report_generation.json](../../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/report_generation.json) `elapsed_seconds` | 0.040539 | 否 | report_outer | internal frozen writer timer before own receipt serialization; non-additive |
| static_review_admin_unknown | 未计量 | null（未计量/未登记） | 否 | — | unmeasured source review/lock/hash/orchestration work outside recorded timer boundaries |
| fit_postbudget_admin_unknown | 未计量 | null（未计量/未登记） | 否 | — | manifest load/hash and closing writes after perDS FIT budget cutoff, unless included by measured FIT outer |
| supplement_outer_unknown | 未计量 | null（未计量/未登记） | 否 | — | this supplement complete process lifecycle can only be supplied by later actual external execution receipt |

已计量互不重复区间小计：15287.986158 秒。该小计包含明确边界的内部与外层计时，完整活动总价保持 null；没有把未知当0。

每数据集继承 TRAIN 债、新增 FIT budget实际值和累计账：

```json
[
  {
    "dataset": "webvid2_5m_light_v1",
    "historical_TRAIN_seconds": 21724.972836322,
    "actual_additional_FIT_budget_seconds": 469.14360973600196,
    "additional_cap_seconds": 900,
    "cumulative_TRAIN_with_this_increment_seconds": 22194.116446058,
    "historical_cost_reset": false,
    "unmeasured_old_teacher_graph_model_cost_seconds": null,
    "scope": "old recorded TRAIN debt retained; missing historical labels/construction/model costs not reconstructed or set to zero"
  },
  {
    "dataset": "yandex_t2i_official10M_ip_v1",
    "historical_TRAIN_seconds": 15589.205719895,
    "actual_additional_FIT_budget_seconds": 472.98626797700126,
    "additional_cap_seconds": 900,
    "cumulative_TRAIN_with_this_increment_seconds": 16062.191987872002,
    "historical_cost_reset": false,
    "unmeasured_old_teacher_graph_model_cost_seconds": null,
    "scope": "old recorded TRAIN debt retained; missing historical labels/construction/model costs not reconstructed or set to zero"
  }
]
```

formal native RSS是约0.25秒采样峰值，不能称精确峰值或把两集峰值相加：

```json
[
  {
    "dataset": "webvid2_5m_light_v1",
    "peak_rss_bytes_observed": 9328279552,
    "rss_scope": "sampled /proc VmRSS at ~0.25s; not exact peak",
    "max_threads_observed": 1,
    "scope": "sampled /proc VmRSS, not exact peak; perDS peaks are not summed"
  },
  {
    "dataset": "yandex_t2i_official10M_ip_v1",
    "peak_rss_bytes_observed": 17751719936,
    "rss_scope": "sampled /proc VmRSS at ~0.25s; not exact peak",
    "max_threads_observed": 1,
    "scope": "sampled /proc VmRSS, not exact peak; perDS peaks are not summed"
  }
]
```

原writer不认识 native_qualification.whole_elapsed_seconds，原表的None保留；本附件单列正确字段。qualification_execution外层包含内部资格与两个child，不重复加；900秒FIT范围不包含其后的manifest哈希和行政收据写入，未知边界保留。

本附件只读已保存小型元数据。原metrics、report、冻结source和locks未改；没有ANN、向量/rawGT/返回读取、拟合、distance、GT生成或bootstrap。输入与本source的SHA绑定见同名JSON。
