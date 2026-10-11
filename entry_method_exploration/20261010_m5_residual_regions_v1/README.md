# E174：沿 M5 候选扩展局部区域

2026-10-10：**预锁试验已完成，停止本冻结一跳/seed/预算版本。原 M5 继续保留研究，生产默认仍为 GT10。** 112点、336个完整计时批次、4个串行job均完成且exit 0；评价覆盖112点/288比较/64机制行，独立整数、wall与trace审计PASS。没有比较达到原协议的较强主双升门，也没有比较达到附加QPS范围分离的更严格报告门，二者计数均为0。

主M5REG96相对原M5同L的16点，14点Recall提高、2点持平；三轮配对QPS变化的中位数全部为负，范围−0.700263%至−0.131740%。这是增量质量/速度取舍。WebVid K1确认b的L800区域版相对L1000 GT有观测双升，但pilot a对应Recall差为负；b的原M5 L800本来已对GT L1000双升，因此整个跨档速度优势不能归给区域扩展。

先读[最终报告](analysis/final_v1/report.md)，再看全量离散点的展示改版：[pilot PNG](analysis/final_v1/figures_v2/pilot.png)、[confirm PNG](analysis/final_v1/figures_v2/confirm.png)（对应[pilot SVG](analysis/final_v1/figures_v2/pilot.svg)、[confirm SVG](analysis/final_v1/figures_v2/confirm.svg)）。v2仅改边距和标签，112个点的Recall、QPS中位数/三轮范围、颜色及大小L形状保持；[首版图](analysis/final_v1/figures/pilot.svg)与[首版renderer报告字节快照](source_before/closing_documents/report.renderer_v1.md)完整保留。当前报告由root仅作展示文档追加及图链接修订，metrics/CSV/raw未改，冻结renderer源码未改。

本轮保留原GT10画像路由、原NSG主搜索、rawIP度量，以及原M5的完整C≤24、fresh scalar重评分和严格TopK合并；新增从同份C每行选query-best seed，至多3个去重不补位，沿原NSG一跳生成额外评分X≤24/96。它没有重训或改图。跨模态任务信息来自**原20K训练query的实际漏GT1/GT100监督**；seed选择、visited过滤和一跳扩展是通用操作。表外ID或表外实际救回都不能直接证明跨模态泛化。

- [与原 M5 的关系](m5_relationship.md)、[代价与收益解释](theory_interpretation.md)、[分析字段范围](analysis_schema.md)
- [冻结协议](protocol.md)、[参数锁](parameter_lock.json)、[执行锁](execution_lock.json)、[辅助来源锁](auxiliary_lock.json)
- [正式native完成核验](reviews/native_completion_acceptance.json)、[实际运行记录](run_state.json)、[评价执行收据](reviews/evaluation_execution.json)
- [独立整数/wall/trace审计](reviews/independent_result_audit/report.json)、[独审实际执行收据](reviews/independent_audit_execution.json)、[独立比较CSV](reviews/independent_result_audit/independent_comparisons.csv)
- [数据身份](reviews/data_preflight.json)、[原GT/M5小样本逐位回归及运行前核验](reviews/preexecution_acceptance.json)、[原生源码独审](reviews/native_source_independent_review.json)
- [完成要求](reviews/completion_requirements.md)、[收尾完成核验](reviews/completion_audit.md)（[JSON](reviews/completion_audit.json)）、[最终交付独审](reviews/final_delivery_independent_review.md)（[JSON](reviews/final_delivery_independent_review.json)）；收尾项状态以各自收据为准，不能由结果审计PASS代替。
- [详细历史记录](../../experiment_history/174_m5_residual_regions.md)、[此前E173结果](../../research_snapshots/20261009_nsg_gt_m5/README.md)

实测范围为两集×K1/K100×各两档L：WebVid L800/1000、Yandex L1000/1200。pilot a每集4096query、九方法，共72点；confirm b每集4096query、固定五方法，共40点。每点三轮T1/CPU15完整wall，实际最多观察到1线程；确认集未按pilot结果取消或改参数。FIRST、额外24以及MF/GEO的direct配对仅pilot有，不能写成confirm复现了这些专门控制。

本轮实际native总耗时7015.307499284秒，其中336批正式wall为4069.756秒，已包含在native总费用中，不能重复相加。评价19.267431196秒、独审28.088101554秒、冻结报告/首版绘图1.730014449秒、展示v2绘图1.531206854秒，分别见[后处理费用](reviews/postprocessing_costs.json)、[报告执行收据](reviews/report_render_execution.json)、[v2执行收据](reviews/figure_layout_v2_execution.json)。输入hash、成功编译和smoke费用见最终报告及历史记录；首次失败build耗时未保存，不能填0，也不能把已记录阶段小计称为完整项目总成本。新增TRAIN/教师/模型或图构建为0，旧TRAIN超额债与旧队列边界保持。

证据限制必须随结论保留：全4096 plain/replay、direct/region独立oracle与完整ID/status trace通过；NDC与plain/count词核验只覆盖事前固定均匀256query。timed各轮返回已释放，不能声称逐轮timed bits已离线核验；整数独审不重新计算原图/visited/scalar，描述性bootstrap区间端点也未被独立重生。MFREG/GEOREG的`new_rescues...`机制字段初始化0表示未计算，控制实际救回/损伤取comparisons或独审CSV；U外数量是逐query出现次数，非全局distinct ID。

另已记录[监控中部分速度意外可见事件](reviews/monitoring_visibility_incident.json)：只涉及confirm_a Yandex部分timing字段，没有解码GT/返回或评价Recall，没有改变参数/协议/模型/分析源，全部预锁job继续。四job的native环境中`router.binding.callback_symbol=UNRESOLVED`，回调符号名未解析；共享对象、image offset、二进制身份及评分词oracle有绑定，不能写成符号已识别。资源guard通过，但未单独保存实际peakRSS数值。角色来源/字节排除不证明全项目未曝光或语义IID；本轮结论只覆盖实际两K/两L。

RUNNING时点的本入口与历史记录已原样保存在[source_before/closing_documents](source_before/closing_documents/campaign_status_backup_manifest.json)。旧E173、旧科学源码/锁/raw完整保留；不根据a/b反馈追加调参、不恢复旧队列、不切换默认。
