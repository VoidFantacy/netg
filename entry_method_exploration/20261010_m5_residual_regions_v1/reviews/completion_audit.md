# E174：root完成审查

PASS_ROOT_COMPLETE_FROZEN_TRIAL_REQUIREMENTS_WITH_DECLARED_SCOPE

本轮有限试验要求已实际满足；研究总体的可靠Recall–QPS双升目标未达成。保留原M5研究与GT10默认，停止本冻结一跳/seed/cap版本。另行最终交付独立复核有自己的收据，不由本文件提前宣称。

实际112点、336正式批次、4成功job；评价112/288/64，独立整数/wall/trace审计PASS。root关闭检查重核18科学源码/ELF SHA、6辅助SHA、109输入stat、1193独审来源stat、当前metrics SHA及112绘图点字段。原四root正文剥离E174块后与备份字节相同。

native总耗时7015.307499284秒，其中owned wall4069.756376932秒已包含，不重复相加。新增TRAIN=0。当前产物346823475字节，free 7316062208字节；实际peakRSS数值未单记，成功native资源guard范围保留。

原静态清单的21项在此逐项核验；原清单保持“待验”历史身份，不回改。详见[机器收据](completion_audit.json)、[实际合同检查](final_contract_checks.json)、[主比较解释检查](final_primary_interpretation_checks.json)与[独立数值审计](independent_result_audit/report.json)。

1. **PASS_WITH_DECLARED_SCOPE**：完成冻结全部112点、336正式批次；a九方法、b五方法，两集各真实K1/K100及两L；不得由a反馈取消b或换参数。

全部112真实点/336正式批次完成，72a+40b，四job完整矩阵与轮转由独审核验。

证据：[protocol.md](../protocol.md), [parameter_lock.json](../parameter_lock.json), [run_state.json](../run_state.json), [final_contract_checks.json](../reviews/final_contract_checks.json), [report.json](../reviews/independent_result_audit/report.json)。

2. **PASS_WITH_DECLARED_SCOPE**：四个独立job成功退出且无活动子进程，实际单线程CPU15、固定轮转、warmup256一次、每点三轮。

四job exit0、最多线程1、CPU15；warm256一次、三正式轮、2,351,104主query调用。当前独有native/serial进程为0。

证据：[run_state.json](../run_state.json), [native_completion_acceptance.json](../reviews/native_completion_acceptance.json), [final_contract_checks.json](../reviews/final_contract_checks.json)。

3. **PASS_WITH_DECLARED_SCOPE**：协议、job、native源码/ELF及后处理源码保持冻结身份。

实际重核18源码/ELF SHA、6辅助SHA、protocol与四job SHA全部匹配；后结果v2仅独立展示源，不覆盖冻结源。

证据：[execution_lock.json](../execution_lock.json), [auxiliary_lock.json](../auxiliary_lock.json), [parameter_lock.json](../parameter_lock.json), [final_contract_checks.json](../reviews/final_contract_checks.json), [figure_layout_v2_execution.json](../reviews/figure_layout_v2_execution.json)。

4. **PASS_WITH_DECLARED_SCOPE**：注册109项依赖/输入身份闭合，正式期前后stat稳定；原画像/labels、表、原图/metric和注册base不变。

正式前四大base/index SHA内容闭合；当前109输入stat及独审1193注册源stat均匹配。base/index不在关闭阶段重复读取。

证据：[data_preflight.json](../reviews/data_preflight.json), [data_preflight_large_sha.receipt.json](../reviews/data_preflight_large_sha.receipt.json), [execution_lock.json](../execution_lock.json), [final_contract_checks.json](../reviews/final_contract_checks.json)。

5. **PASS_WITH_DECLARED_SCOPE**：编译和原GT/M5回归资格与正式证据分开。

实际编译PASS，smoke新旧运行、16query GT/M5逐位回归及static source review保留，仅作为运行前资格。

证据：[build.json](../reviews/build.json), [smoke_execution.json](../reviews/smoke_execution.json), [preexecution_acceptance.json](../reviews/preexecution_acceptance.json), [native_source_independent_review.json](../reviews/native_source_independent_review.json)。

6. **PASS_WITH_DECLARED_SCOPE**：保留原GT主搜索和原M5完整C及合并；实现冻结seed/cap/arrival规则与回退。

原M5完整C/评分/合并与GT保持；seed/cap/arrival/fallback冻结实现与全4096独立oracle实际通过，region trace整数审计PASS。普通异常fatal范围保留。

证据：[region.hpp](../src/region.hpp), [benchmark.cpp](../src/benchmark.cpp), [m5_relationship.md](../m5_relationship.md), [report.json](../reviews/independent_result_audit/report.json), [final_contract_checks.json](../reviews/final_contract_checks.json)。

7. **PASS_WITH_DECLARED_SCOPE**：完整wall计入正常输出生命周期及全部附加query工作；正式计时不采集trace/oracle。

全部112收据normal_output_release_before_stop true、timed_output_retained false。完整正常生命周期与附加流程计时；正式墙时4069.756376932秒。

证据：[benchmark.cpp](../src/benchmark.cpp), [native_completion_acceptance.json](../reviews/native_completion_acceptance.json), [final_contract_checks.json](../reviews/final_contract_checks.json), [points.csv](../analysis/final_v1/points.csv)。

8. **PASS_WITH_DECLARED_SCOPE**：每点保存完整4096 plain，并完成独立全量replay逐位相等及direct/region相应全量oracle。

每点全4096 plain+独立replay bit flags实际true；direct/region相应全量linear或candidate/scalar oracle flags覆盖。保存ids尺寸与真K吻合。

证据：[native_completion_acceptance.json](../reviews/native_completion_acceptance.json), [final_contract_checks.json](../reviews/final_contract_checks.json), [report.json](../reviews/independent_result_audit/report.json)。

9. **PASS_WITH_DECLARED_SCOPE**：全64区域点完整trace、容量/来源/唯一性与全量费用一致；主M5REG96共16点。

全64区域点4096×128 i32/2MiB trace schema与大小核验，独审C/ID/status/唯一性/费用PASS，其中主方法16点。score words仅native内核验。

证据：[analysis_schema.md](../analysis_schema.md), [final_contract_checks.json](../reviews/final_contract_checks.json), [report.json](../reviews/independent_result_audit/report.json)。

10. **PASS_WITH_DECLARED_SCOPE**：固定均匀256 plain/count词一致及物理调用账一致。

全部112 point count_audit_n=256、事前均匀sample plain/count bits标志true；计数账及返回词由另行独审核验，不声称full4096 NDC。

证据：[analysis_schema.md](../analysis_schema.md), [native_completion_acceptance.json](../reviews/native_completion_acceptance.json), [final_contract_checks.json](../reviews/final_contract_checks.json), [report.json](../reviews/independent_result_audit/report.json)。

11. **PASS_WITH_DECLARED_SCOPE**：所有native完成后实际生成完整评价，不以静态脚本代替运行；112 points、288 comparisons、64 mechanisms。

全部native后的评价真实exit0，112 points/288 comparisons/64 mechanisms，三CSV行数匹配，112 scored文件保留。

证据：[evaluation_execution.json](../reviews/evaluation_execution.json), [metrics.json](../analysis/final_v1/metrics.json), [points.csv](../analysis/final_v1/points.csv), [comparisons.csv](../analysis/final_v1/comparisons.csv), [mechanisms.csv](../analysis/final_v1/mechanisms.csv)。

12. **PASS_WITH_DECLARED_SCOPE**：独立整数/成员/wall/trace/费用/收据审计实际通过，并与JSON及CSV完整一致。

另行独立脚本实际exit0/PASS整数、成员、wall、trace与CSV；112/288/336/64/16。非evaluate import，非CI端点独立重生。

证据：[independent_audit_execution.json](../reviews/independent_audit_execution.json), [report.json](../reviews/independent_result_audit/report.json), [independent_points.csv](../reviews/independent_result_audit/independent_points.csv), [independent_comparisons.csv](../reviews/independent_result_audit/independent_comparisons.csv), [independent_mechanisms.csv](../reviews/independent_result_audit/independent_mechanisms.csv)。

13. **PASS_WITH_DECLARED_SCOPE**：既有角色GT、原TRAIN支持及U来源准确绑定；质量差异与机制覆盖分开。

角色GT和原TRAIN支持绑定已独审；Web/Y posting U=5433/6543、TRAIN U=684562/1581191，真实U外救回与候选分开；逐query incidence范围明示。

证据：[analysis_schema.md](../analysis_schema.md), [m5_relationship.md](../m5_relationship.md), [metrics.json](../analysis/final_v1/metrics.json), [report.json](../reviews/independent_result_audit/report.json)。

14. **PASS_WITH_DECLARED_SCOPE**：全方法实际救回/损伤以comparisons为权威；M5-only机制字段不得误用于MF/GEO。

全方法实际救/损以comparisons为权威；MF/GEO三M5-only mechanism初始化0未计算，U外damage未单列，报告无补造。

证据：[analysis_schema.md](../analysis_schema.md), [comparisons.csv](../analysis/final_v1/comparisons.csv), [report.md](../analysis/final_v1/report.md), [result_interpretation_independent.md](../reviews/result_interpretation_independent.md)。

15. **PASS_WITH_DECLARED_SCOPE**：既定paired统计与速度标签真实、范围披露准确。

描述性paired bootstrap既有seed/2000/scope经独审；QPS中位/范围与round比检查，不重新CI；crossL仅顺序round对齐。

证据：[metrics.json](../analysis/final_v1/metrics.json), [report.json](../reviews/independent_result_audit/report.json), [report.md](../analysis/final_v1/report.md)。

16. **PASS_WITH_DECLARED_SCOPE**：新TRAIN/fit/teacher/表/画像/图构建增量0，历史债保持，实际工程/查询成本完整披露。

本轮新增TRAIN/教师/模型/图构建0，旧TRAIN超额不重置；native及各postprocess实际费、失败build缺时长、人工总费未全记录均披露。

证据：[protocol.md](../protocol.md), [run_state.json](../run_state.json), [postprocessing_costs.json](../reviews/postprocessing_costs.json), [evaluation_execution.json](../reviews/evaluation_execution.json), [independent_audit_execution.json](../reviews/independent_audit_execution.json), [report_render_execution.json](../reviews/report_render_execution.json), [figure_layout_v2_execution.json](../reviews/figure_layout_v2_execution.json), [report.md](../analysis/final_v1/report.md)。

17. **PASS_WITH_DECLARED_SCOPE**：实际生成报告和两role四panel图，填入所有点及主same-L/cross-L、pilot强控、机制救/损和费用；SVG/PNG实际视觉检查。

最终报告保留全部112表及same/crossL/controls/机制/费用；v2两role SVG+PNG均实际生成。root实际view两PNG，112绘图坐标/范围与预计算点逐字段相等；原图/首版报告字节保全。

证据：[report.md](../analysis/final_v1/report.md), [figure_layout_v2_execution.json](../reviews/figure_layout_v2_execution.json), [figures_visual_review.json](../reviews/figures_visual_review.json), [final_contract_checks.json](../reviews/final_contract_checks.json), [report.renderer_v1.md](../source_before/closing_documents/report.renderer_v1.md)。

18. **PASS_WITH_DECLARED_SCOPE**：报告“已独审”绑定实际选用metrics文件，而非旧/其他评价。

实际metrics SHA和stat4重核与独审1193绑定内的当前绝对路径登记一致，renderer身份guard通过，最终手工补充未改metrics。

证据：[report.json](../reviews/independent_result_audit/report.json), [report_render_execution.json](../reviews/report_render_execution.json), [final_contract_checks.json](../reviews/final_contract_checks.json)。

19. **PASS_WITH_DECLARED_SCOPE**：给出有限保留/停止决定、默认保持；不强造双升、不根据反馈扩网格。

主40比较/20两role组保存字段复核：原协议及附加报告门均0。16sameL原M5参考14增2平/全部速度负；bWebK1正a负且原M5已具优势。停止仅冻版，默认GT10/原M5研究保留。

证据：[protocol.md](../protocol.md), [final_primary_interpretation_checks.json](../reviews/final_primary_interpretation_checks.json), [result_interpretation_independent.md](../reviews/result_interpretation_independent.md), [report.md](../analysis/final_v1/report.md), [state.json](../state.json)。

20. **PASS_WITH_DECLARED_SCOPE**：同步四root文档、E174历史及campaign README，使状态/合同/结果入口一致。

四root当前块、README、history174、state已同步；root职责分开，当前E174终态优先；旧native run_state保留阶段标签并明确最终评价另证。

证据：[README.md](../README.md), [state.json](../state.json), [report.md](../analysis/final_v1/report.md), [summary.md](/data/netg/ACSG/summary.md), [spec.md](/data/netg/ACSG/spec.md), [s-target.md](/data/netg/ACSG/s-target.md), [s-experiment.md](/data/netg/ACSG/s-experiment.md), [174_m5_residual_regions.md](/data/netg/ACSG/experiment_history/174_m5_residual_regions.md)。

21. **PASS_WITH_DECLARED_SCOPE**：保全科学锁、旧M5/GT10/原图数据、原E172/E173及其他历史记录；交付后停止本冻结范围。

所有注册原GT/M5/图依赖保持；四root剥离E174后与pre-E174备份字节相等，RUNNING阶段及首版报告字节另备份。关闭修改仅新E174与当前四块，不重开旧队列。未宣称全旧历史目录独立全量SHA基线。

证据：[final_contract_checks.json](../reviews/final_contract_checks.json), [manifest.json](../source_before/root_documents/manifest.json), [root_backup_manifest.json](../source_before/closing_documents/root_backup_manifest.json), [campaign_status_backup_manifest.json](../source_before/closing_documents/campaign_status_backup_manifest.json), [execution_lock.json](../execution_lock.json)。

边界：全部native后才读取角色GT质量，但行政监控曾看到部分a/Yandex速度，事件已记录；timed packet未存，计数NDC为256均匀sample，完整plain/replay/trace为4096。随机CI端点未由整数独审重生；角色字节排除不建立语义IID，U外是query incidence，MF/GEO的M5-only机制0表示未算。原native callback_symbol=UNRESOLVED、具体peakRSS缺记录范围保留；没有全旧历史目录的pre-task SHA基线。
