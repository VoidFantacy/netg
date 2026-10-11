# E174：M5 残差候选作为区域入口

2026-10-10，**实测与结果审计已完成；停止本冻结一跳/seed/预算版本，保留原M5研究与GT10默认。** 本轮不是丢弃M5：原M5完整C、重评分与合并被保留，新增区域候选来源在已预锁的有限范围内真实执行并评价；结果为质量/费用取舍，没有主候选比较达到原协议的较强局部双升门或更严格报告门，计数均为0。

目录入口：[20261010_m5_residual_regions_v1](../entry_method_exploration/20261010_m5_residual_regions_v1/README.md)。权威结果为[最终报告](../entry_method_exploration/20261010_m5_residual_regions_v1/analysis/final_v1/report.md)、[metrics](../entry_method_exploration/20261010_m5_residual_regions_v1/analysis/final_v1/metrics.json)及[独立整数/wall/trace审计](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/independent_result_audit/report.json)。本文不重复112点长表，全部点、288项配对比较、64项机制行由这些产物保留。

## 动机、保留部分与新增机制

原M5以原discovery/FIT0 20K跨模态训练query的实际漏GT1/GT100监督，编译每路由行最多8个目标的冻结posting；GT1遗漏权重100，GT100遗漏成员额外权重1，联合覆盖整数greedy产物由K1/K100共用。它使用原GT10与旧Lminus下的实际主搜索返回定义训练残差，不是本轮a/b上新拟合的漏召回表。本轮针对其固定ID支持有限的问题，让这些已有残差候选成为原NSG局部区域的种子。

保留原画像路由、原NSG主搜索、原query/rawIP、原M5全部C≤24的fresh scalar重评分与严格TopK合并。区域阶段仅在完整M5阶段成功后进行：从同一份已付分数C按每路由行选query-best且不在原GT返回R中的seed，至多3个、按路由顺序去重、不补位；原邻接槽按seed0-slot0、seed1-slot0、seed2-slot0等轮转。跳过padding/非法ID、main visited已见、全部C及本次X重复，额外评分X≤24/96；X的arrival优先级晚于R/C，最终仍用rawIP严格合并。

R/C非有限时保原GT返回；X非有限时保完整原direct返回（主方法为原M5）及已付费用。成功job内这些分支与cap/seed规则由原生oracle及trace核验；未触发域不据此宣称全域数值证明。它是一跳候选生成，未暂停/恢复主搜索、重开三入口或改主图；visited“已见”不等于已展开，不同路由行不证明不同basin。保留完整C支持不自动保证最终K返回是原M5的ID超集，须核实际成员损伤。

跨模态任务信息来自原漏召回监督；query-best选择、一跳、过滤、去重与合并本身是通用图操作。MF使用同份漏召回监督的逐行频率选择，检验联合覆盖的区别；GEO使用原full-base几何表，但继承共同的已学习GT10画像路由，不能称全流程无监督。详细来源与对照命题见[原M5关系](../entry_method_exploration/20261010_m5_residual_regions_v1/m5_relationship.md)、[代价/质量差额推导](../entry_method_exploration/20261010_m5_residual_regions_v1/theory_interpretation.md)。

## 冻结范围与实际执行

[protocol](../entry_method_exploration/20261010_m5_residual_regions_v1/protocol.md)、[parameter lock](../entry_method_exploration/20261010_m5_residual_regions_v1/parameter_lock.json)、[execution lock](../entry_method_exploration/20261010_m5_residual_regions_v1/execution_lock.json)、[auxiliary lock](../entry_method_exploration/20261010_m5_residual_regions_v1/auxiliary_lock.json)均保留原字节。实际两集WebVid/Yandex、K1/K100分别真实搜索；WebVid L800/1000、Yandex L1000/1200。confirm_a每集全部4096query，九方法GT/M5/M5REG24/M5REG96/M5FIRST96/MFDIRECT/MFREG96/GEODIRECT/GEOREG96，共72点；confirm_b每集全部4096query，固定GT/M5/M5REG96/MFREG96/GEOREG96，共40点。主候选唯一M5REG96；两集两K共享策略，没有按a反馈取消b、更换模型/预算或扩大网格。

全部**112点、336个正式计时批次、4个串行job完成且exit 0**，每点三轮完整T1/CPU15 wall，按KL ordinal与round轮转方法；实际进程最多观察到1线程。完整wall支付输出分配/初始化/释放、路由/NSG/合法域guard、查表、R/C重评分、seed选择、邻接读取/过滤/去重、X评分及合并。加载/hash/写盘/GT评价/oracle外置；固定额外dot cap不是同wall。终态见[native完成核验](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/native_completion_acceptance.json)与[运行记录](../entry_method_exploration/20261010_m5_residual_regions_v1/run_state.json)。run_state保存native阶段状态；后续评价/审计完成由各执行收据另证，不把其旧phase标签当作质量仍未运行。

109项注册输入身份通过；四个大base/index的本次完整SHA匹配原值，设备号迁卷差异由内容闭合。源码/二进制与辅助来源冻结绑定通过。编译和两集72个新smoke点通过，GT/M5的112个小样本原始文件与E173原二进制逐位一致（16query/点）。这些是运行前资格，不能代替正式质量/速度证据，见[preflight](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/data_preflight.json)、[preexecution acceptance](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/preexecution_acceptance.json)。

全部native完成后才解码角色GT并评价。评价实际PASS **112点/288比较/64机制行**；独立脚本不导入evaluate，复核整数成员、配对救回/损伤、三轮wall/顺序/矩阵、ID/status trace与来源身份，实际PASS **112/288/64**，含主方法完整trace **16点**。见[评价执行](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/evaluation_execution.json)、[独审执行](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/independent_audit_execution.json)与[独立比较明细](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/independent_result_audit/independent_comparisons.csv)。

## 实际结果与停止理由

M5REG96相对原M5同L共16点，**14点Recall增、2点平，全部三轮配对QPS变化中位数为负（−0.700263%至−0.131740%）**；实际真成员损伤在这些比较中为0。WebVid K1的增量为pilot +0.122pp、confirm +0.171pp；Yandex K1的pilot +0.049pp在confirm变为0。K100有少量真实成员增益，完整同L费用仍增加，不能由新增候选或NDC推断双升。相对默认GT与相对原M5的增量分别报告，不能把原M5救回计作区域新贡献。

跨L唯一主候选观测双升是confirm b WebVid K1：REG96 L800对GT L1000，Recall +0.830pp、配对QPS中位 +23.46%；对应pilot a Recall为−0.073pp，未在两角色复现。且b原M5 L800对GT L1000本就有+0.659pp、+23.94%的观测双升；区域贡献仅为同L相对M5新增7个真成员、+0.171pp，伴随−0.43%的配对QPS中位变化。不能把整个跨L速度优势归因于扩展。其他dataset/K的已测跨档比较没有主方法观测双升；不从这两档L插值或外推。

冻结协议较强局部门要求同一具体比较两角色都正、confirm描述性Recall CI下界>0、三轮都更快。冻结report在此基础上附加confirm最慢轮仍快于参考最快轮的范围分离条件；**范围分离不是protocol原文**。主比较通过原门与更严格报告门的计数均为0。未满足门的正结果保留为观察，一升一降记取舍；默认替换资格没有成立。FIRST/REG24、MF与GEO的direct配对只在pilot存在，不能称confirm重复了这些专门控制；相同cap不保证实际C/X数量、邻接读取或wall相同，控制差异也不自动证明跨模态独有性。

机制与最终收益分开。例如confirm b WebVid K1/L800实际救回7个成员，其中5个在原M5 posting并集外、0个在原TRAIN GT100并集外；Yandex K1/L1000产生235476次原M5并集外X，却没有相对原M5的实际救回。后者计数为逐query出现次数，非235476个全局distinct ID。存在表外目标与救回只证明跨过该有限ID支持，不证明语义迁移、modality gap已被缩小或跨模态泛化。

本轮按原停止边界**封存并停止此冻结一跳/seed/预算版本**，不从a/b响应追加调参；原M5研究继续保留，GT10默认不变，不恢复E172或其他旧队列。此前[E173结论](../research_snapshots/20261009_nsg_gt_m5/README.md)仍有独立历史身份，不能被本轮同L负速度或跨档未复现覆盖掉。

## 实际费用与旧训练债

以下值取实际执行收据，单位秒。没有重新运行或用query数推算成本。

| 阶段 | 实际秒 | 收据与费用范围 |
| --- | --- | --- |
| 四个大输入串行SHA | 160.342116562 | [large SHA](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/data_preflight_large_sha.receipt.json)，性能期前base/index全文件核验 |
| 其余身份预检小文件SHA | 0.118902602 | [preflight](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/data_preflight.json)，不是全部人工/source审查耗时 |
| 成功编译 | 8.586150746 | [build](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/build.json)，工程费用，非TRAIN |
| 四个新/旧smoke job | 11.022585930 / 6.763566107 / 20.036995096 / 14.525307201 | [smoke](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/smoke_execution.json)，顺序为Web新/旧、Y新/旧；非正式QPS |
| 四个正式native job合计 | 7015.307499284 | [run_state](../entry_method_exploration/20261010_m5_residual_regions_v1/run_state.json)，含加载/身份核验/预热/正式wall/plain/replay/oracle/count/写盘/进程等待 |
| 其中336批正式wall | 4069.756 | [points](../entry_method_exploration/20261010_m5_residual_regions_v1/analysis/final_v1/points.csv)，已含在native总费用中，不再相加 |
| 评价 | 19.267431196 | [evaluation](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/evaluation_execution.json)，既有GT整数评分、bootstrap及输出写盘，收据写盘外置 |
| 独立结果审计 | 28.088101554 | [audit execution](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/independent_audit_execution.json)，完整审计子进程与报告/CSV写盘，外层收据写盘除外 |
| 冻结报告与首版图 | 1.730014449 | [report render](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/report_render_execution.json)，完整子进程与SVG/PNG/报告写盘、log关闭；收据写盘除外 |
| postresult展示v2 | 1.531206854 | [figure v2](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/figure_layout_v2_execution.json)，源码AST/小SHA、metadata检查、四图/log写盘及核验；收据写盘除外 |
| 新增TRAIN/教师/模型或图构建 | 0 | [protocol](../entry_method_exploration/20261010_m5_residual_regions_v1/protocol.md)，复用已冻GT10/M5/MF/GEO与原图 |

首次build及行政收据失败的耗时未保存，见[原失败记录](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/build_attempt1_admin_failure.json)，不能填0。没有完整独立人工研究/源码审查/所有历史投入计时，已记录阶段小计不能宣称完整项目成本。每dataset跨方法TRAIN≤7200秒的旧约束与历史超额事实保持；本轮新增TRAIN=0不重置旧债，也不授权旧训练队列恢复。

## 必须保留的证据边界

- 全4096 normal plain与独立replay逐位一致，direct全量线性oracle、region全量C/seed/X重建、fresh scalar评分词与独立线性oracle通过。完整trace保存ID/status，评分词仅在untimed原生oracle内核验；timed输出已释放，没有逐轮timed bits的离线证据。独立整数审计不重新计算原图、visited或scalar。
- NDC及plain/count词核验仅固定事前均匀256query；`stats.post_dots`覆盖R+C，`new_distances`覆盖X，两者与主搜索构成完整计数。不能把256统计写成full4096 NDC，也不能用它代替完整wall。
- 描述性paired-query bootstrap的seed、重复2000次与scope被查验，区间端点未被独立重采样。多比较未作总体/同时校正；跨L速度仅按round index对齐，是顺序描述比较。原GT/tie成员定义保持，未新生成距离GT或tie-adjusted GT。
- `mechanisms.new_rescues_vs_M5`及两种U外新增救回仅对M5REG24/96/FIRST96计算；MFREG/GEOREG同名字段的初始化0表示未计算，不能称实际0救回。所有方法真实Recall/救回/损伤以`comparisons`为权威，辅助[独立机制CSV](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/independent_result_audit/independent_mechanisms.csv)另列控制实际救/损（损伤字段为`actual_true_damage_vs_M5`）；U外损伤未单列。U外计数为每query incidence；未单列损伤不能补0。见[analysis schema](../entry_method_exploration/20261010_m5_residual_regions_v1/analysis_schema.md)。
- 四job `native_environment.json`中的`router.binding.callback_symbol`均为`UNRESOLVED`：距离counter回调的符号名无法解析。已有shared_object/image offset、冻结二进制身份和评分词oracle绑定，不能写成符号已识别；参见[Web pilot环境](../entry_method_exploration/20261010_m5_residual_regions_v1/results/confirm_a/webvid2_5m_light_v1/native_environment.json)、[Y confirm环境](../entry_method_exploration/20261010_m5_residual_regions_v1/results/confirm_b/yandex_t2i_official10M_ip_v1/native_environment.json)。资源guard通过，未单独保存实际peakRSS数值。
- [监控partial-speed事件](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/monitoring_visibility_incident.json)记录行政schema查看时confirm_a Yandex部分QPS/seconds/native_calls可见，工具输出被截断。没有解码GT/返回、评价Recall/救回损伤或更改native参数、协议、模型、分析源，四个预锁job继续完成。不能声称中间速度完全不可见。
- 来源/字节与已查历史消费排除只覆盖注册窗口，不能证明全项目未曝光或语义IID。a质量打开后属于开发数据；b策略冻结且在全部native结束后质量打开。仅两dataset、两K及各两L有结果，未测预算/目标/角色不得外推。

## 展示、交付审查与历史保全

全部112点图见[pilot v2 PNG](../entry_method_exploration/20261010_m5_residual_regions_v1/analysis/final_v1/figures_v2/pilot.png)、[confirm v2 PNG](../entry_method_exploration/20261010_m5_residual_regions_v1/analysis/final_v1/figures_v2/confirm.png)及对应[pilot SVG](../entry_method_exploration/20261010_m5_residual_regions_v1/analysis/final_v1/figures_v2/pilot.svg)、[confirm SVG](../entry_method_exploration/20261010_m5_residual_regions_v1/analysis/final_v1/figures_v2/confirm.svg)。v2仅postresult边距/标签改版，不连线、不jitter，不改坐标/颜色/三轮范围；旧图与冻结renderer源码保留。首版renderer报告原字节保存在[report.renderer_v1.md](../entry_method_exploration/20261010_m5_residual_regions_v1/source_before/closing_documents/report.renderer_v1.md)，当前report由root仅作展示文档追加及图链接修订，metrics/CSV/raw未改。

[完成要求](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/completion_requirements.md)、[root完成审计](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/completion_audit.md)（[JSON](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/completion_audit.json)）与[最终交付独审](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/final_delivery_independent_review.md)（[JSON](../entry_method_exploration/20261010_m5_residual_regions_v1/reviews/final_delivery_independent_review.json)）分别承载最终文件/要求核验及独立交付判断，状态以各自收据为准，不能由已有结果审计PASS替代尚未形成的交付审查。

本历史记录与campaign README的RUNNING原字节已单独备份：[备份manifest](../entry_method_exploration/20261010_m5_residual_regions_v1/source_before/closing_documents/campaign_status_backup_manifest.json)，对应[原README](../entry_method_exploration/20261010_m5_residual_regions_v1/source_before/closing_documents/campaign_README.md)、[原历史记录](../entry_method_exploration/20261010_m5_residual_regions_v1/source_before/closing_documents/history174_m5_residual_regions.md)。原E173/E172、旧科学源码、冻结锁、结果raw和失败行政记录不覆盖；本次收尾文档没有新增实验、统计、训练或旧队列动作。
