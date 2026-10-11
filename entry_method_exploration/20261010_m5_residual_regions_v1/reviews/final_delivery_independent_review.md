# E174 最终交付独立审查

**PASS_INDEPENDENT_FINAL_DELIVERY_WITH_DECLARED_SCOPE**，2026-10-10，审查者 measured_results。

本冻结试验及新增曲线展示完成；可靠 Recall–QPS 综合改进目标仍未达成。保留原 M5 研究与 GT10 默认，停止本冻结一跳/seed/cap 版本。没有阻断发现，不从 a/b 响应继续调参、扩大网格或恢复旧队列。机器详情见[JSON收据](final_delivery_independent_review.json)。

本次实际阅读定稿报告、四份根文档的当前块、README、E174历史、state、原静态完成要求及 root 完成审查，并核对其具体证据文件。未执行科学源，未读取 GT/raw/向量或大输入字节，未重算 Recall、成员集合、距离、CI、ratio 或训练。质量结论绑定此前真实执行的[独立结果审计](independent_result_audit/report.json)与[执行收据](independent_audit_execution.json)，本交付审查不替代数值审计。

- **实测身份与完成范围通过**：112点、336正式批次、4个 exit0/T1 job；评价与两套既存CSV均为112/288/64，主方法完整trace16点。64份full trace尺寸为4096×128×4字节、112份scored产物存在。run_state保留 native collection 的阶段标签；后续评价/独审已实际完成，由独立执行收据及终态state另证。
- **来源与历史通过**：实际小文件重核18科学源码/ELF及6辅助SHA；109输入stat、1193独审来源stat全部匹配，选用metrics与实际独审登记身份一致。8份终态文档SHA匹配 root completion manifest。四root剥离唯一E174块及其末尾两换行后，与 pre-E174 原件逐字节相同；8份 RUNNING/首版报告快照SHA及尺寸也匹配。此处没有全旧历史目录的pre-task全量SHA主张。
- **结果解释通过**：主方法对原M5同L16点为14增/2平，三轮配对QPS变化中位均下降0.13%–0.70%。原协议较强局部门及附加报告门均0；附加范围分离条件明确是报告层条件。唯一主跨L观测双升仅b/WebVid/K1，匹配a的Recall为负；b原M5小L已有跨档优势，区域新增7个真成员及其同L速度代价单列，未将整个优势归给区域。
- **21项完成要求通过且保留范围**：与[原静态清单](completion_requirements.md)、[root实际逐项审查](completion_audit.json)的21项逐项对齐，95处具体证据引用全部存在。原待验清单保持历史身份；实际完成由新收据证明，不回改旧静态状态。
- **图与链接通过**：实看两个全量v2 PNG，标题、轴、图例、L形状及页脚可读；112个点键、Recall/QPS/min-max及圆/方与已存metrics逐字段相同。v2仅展示改版，首版四图保留。旧renderer报告与当前报告的实际diff仅为line5解释补全、四图链接替换及末尾说明追加；原科学结果表与既存数字未改。两收据创建后实际终核14份Markdown的285处本地链接及合法行号，5处此前待写引用全部闭合，没有失效链接。
- **费用与资源通过**：四native总耗时7015.307499284秒，正式wall4069.756376932秒已包含，不重复相加；实际评价19.267431196秒、独审28.088101554秒、首版报告1.730014449秒及v2展示1.531206854秒分开。新TRAIN=0，旧债保持；失败build/行政失败缺耗时标缺，未填0或宣称完整项目总费。写本收据前产物348853501字节，free7313989632字节，分别符合512MiB/至少1GiB；native成功guard与各job少于7200秒有收据，未补造peakRSS值。

新增的新旧方法曲线也已独立实际审核，入口为[comparison_curves_v1](../analysis/final_v1/comparison_curves_v1/README.md)。全文静态读298行新展示源并AST解析，SHA与[成功执行收据](comparison_curves_execution.json)一致；实看pilot、confirm及increment三PNG，均可读。48个主点、16条已存同L比较在图metadata与两CSV中逐字段一致；1310处保护stat、9输出stat、8原终态文档SHA均保持。GT10/原M5对照来自本轮同角色重跑，未拼旧E173公共10K；线段只连接两档实际端点，明确不代表中间L性能。增量直接用已存paired QPS字段，未用点中位数另算比。成功展示实际费1.894599701秒单独记录，首次行政失败耗时null而非0；见[root另行复核](comparison_curves_root_review.json)。

审查结论随以下限制成立：timed packet未保存；NDC/count仅固定256；全4096原生评分词/visited/X顺序沿用先前full native oracle，整数独审与本次交付均不重算；CI端点未独立重生；callback_symbol仍UNRESOLVED、实际peakRSS未单记；partial-speed监控事件保留；MF/GEO未计算的M5-only字段0不当作零救回，U外为逐query incidence、U外damage未单列；角色排除不证明语义IID或全项目未曝光，候选/救回表外不证明跨模态因果或泛化。以上范围在[最终报告](../analysis/final_v1/report.md:304)、[历史正文](/data/netg/ACSG/experiment_history/174_m5_residual_regions.md)及[完成审查](completion_audit.md)明确保留。

本次只创建 final_delivery_independent_review.json 与本Markdown；科学源、锁、raw、metrics、现有文档及state没有修改，没有启动新实验或数值任务。

