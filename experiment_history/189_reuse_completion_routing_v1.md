# E189：复用GT10信息的稀疏补全路由

2026-10-28，用户明确要求“继续研究吧”。正式两集K100共70点/210完整T1轮，校准64点/192轮，预定范围全部完成。默认E99 GT10保持。

18个新复用点中18个被实测GT10同时覆盖Recall与QPS；离散速度筛选通过0点，预算召回筛选通过0点。

复用路由可以减少部分费用，但三种固定版本均未形成对GT10的可靠Recall–QPS改进。本轮直接选块方案在COCO与Deep暴露出不同瓶颈，后续应分别研究近似排序损失和候选来源覆盖。

同批L200下，COCO REUSE-REG的额外平均耗时由BLOCK-R2048的137.47降至74.69μs（减少45.7%），成员救回次数2555→2376（召回增量0.2555→0.2376pp）；Recall为95.5820%、QPS1823.14，仍被GT10 L216的95.7947%/1983.71覆盖。Deep REUSE-REG额外耗时140.98→137.90μs（仅减少2.2%），粗代表评分1024→21.52并未带来同等wall收益；原/新扫描量基本相同，未单独插桩归因。新法97.2993%/1438.90仍被GT10 L216的97.3854%/1672.83覆盖。

直接块主候选REUSE-BLOCK在L200：COCO原遗漏46556，候选块覆盖18932、实际扫描覆盖18747，PQ96仅保留2131并全部救回；Deep原遗漏29220，候选块仅覆盖1091（3.73%），扫描覆盖1090、PQ96覆盖938、最终救回847。事后固定256query的float64原metric诊断：COCO扫描内486个遗漏用精确Top96可全部保留，现有PQ96仅53个；此为排序诊断，不是免费在线性能承诺。Deep两种直接块法各91个短名单到最终返回的损失全部有已返回的相同向量不同ID对应，保留严格GT-ID口径，不改GT或tie规则。

三个新方法：REUSE-REG将三个入口每hub8区域与主返回最高8区域合并，最多32粗代表评分，沿冻结REG-R模型选最多2区，其余沿E188每区1024码/48候选；REUSE-BLOCK对应每hub8块与主返回最高8块，最多32块代表评分，整块访问上限2048码、全局PQ96；MAIN-BLOCK只保留主返回8块。旧图/PQ/块/metric/GT10不改，主核仍E183冻结scalar。区域与直接块的候选分配不同，不作纯路由因果。与E174的posting seed/NSG一跳不同，本轮不以主图邻接扩展候选。

新表只用合法前12K L200教师遗漏及入口频次，ties按ID，无超参选择；末4K只是诊断，不决定或取消正式范围。旧16K B32明确排除校准，正式保留参考，不是训练量匹配对照。原16K完整遗漏并集作为旧来源外审计，不能与新12K源混称。向量SHA交集：coco fit/cal=0、fit/test=0、cal/test=0；deep10m_l2_v1 fit/cal=0、fit/test=0、cal/test=0；历史GT10训练及公开测试曝光仍须披露。

CPU15、实际1线程、单方法串行；warm256、三轮轮转，完整Batch正常分配初始化/GT10路由主搜/补全/六数组复制销毁。首轮实际包保留，另两轮字/SHA一致；真实主包全排序PQ/合并oracle、预算上限、旧控制完整包、另一实现整数统计与原metric分数通过。块候选池/扫描选择/PQ阈值另用第二实现抽检64query/方法/数据集；L200全部覆盖链从实际主包重建oracle trace。第二实现同一执行者，不称独立人员审查。严格0–9命中失败及救损见完整表，不从稀少尾部外推。

新持久数组约COCO0.55MiB/Deep38.24MiB，主要为N×4 ID→block映射；旧全库后端常驻成本仍在，进程共同装载的RSS不是新增量。构建、suite、内部wall分别见报告，内含费用不相加。E188 2145件seal未变，当前根文档旧版另存source_before，不回写旧交付身份。

固定版本收口，后续方向见当前s-target；无新盲确认/K1/其他五集证据或默认替换。

[完整报告](../entry_method_exploration/20261028_reuse_completion_routing_v1/report_zh.md) · [六页PDF](../entry_method_exploration/20261028_reuse_completion_routing_v1/ACSG_复用路由与补全成本实验_20261028.pdf) · [协议](../entry_method_exploration/20261028_reuse_completion_routing_v1/protocol.md) · [冻结](../entry_method_exploration/20261028_reuse_completion_routing_v1/freeze.json) · [核验](../entry_method_exploration/20261028_reuse_completion_routing_v1/reviews/results_audit.json)。
