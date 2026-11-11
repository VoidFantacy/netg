# ACSG 当前结论

更新于2026-10-28。**默认保留E99 GT10：WebVid GT10-soft-t1、Yandex GT10-hard。** 最新完成[E189复用信息的补全路由实验](entry_method_exploration/20261028_reuse_completion_routing_v1/report_zh.md)：两集真实K100，正式70点/210完整单线程轮，另64点/192轮校准。固定矩阵已收口，无待恢复队列；可靠Recall–QPS研究目标尚未完成。

**18个新复用点中18个被实测GT10同时覆盖Recall与QPS；离散速度筛选通过0点，预算召回筛选通过0点。** 复用路由可以减少部分费用，但三种固定版本均未形成对GT10的可靠Recall–QPS改进。本轮直接选块方案在COCO与Deep暴露出不同瓶颈，后续应分别研究近似排序损失和候选来源覆盖。

## 本轮实际结果：固定L200

| 数据 | 方法 L200 | Recall@100 | 完整QPS |
| --- | --- | --- | --- |
| COCO | GT10 | 95.3444% | 2110.54 |
| COCO | B32 | 96.7159% | 1996.31 |
| COCO | BLOCK-R2048 | 95.5999% | 1635.90 |
| COCO | REUSE-REG | 95.5820% | 1823.14 |
| COCO | REUSE-BLOCK | 95.5575% | 1711.94 |
| COCO | MAIN-BLOCK | 95.4933% | 1798.87 |
| Deep10M | GT10 | 97.0780% | 1795.08 |
| Deep10M | B32 | 97.0801% | 1733.54 |
| Deep10M | BLOCK-R2048 | 97.3027% | 1432.54 |
| Deep10M | REUSE-REG | 97.2993% | 1438.90 |
| Deep10M | REUSE-BLOCK | 97.1627% | 1481.05 |
| Deep10M | MAIN-BLOCK | 97.1500% | 1556.04 |

QPS是本轮同一二进制的三轮中位数；含正常分配、GT10路由/主搜、补全、六数组复制和销毁，不拼接E188绝对速度。实际离散阈值对照不等于精确等Recall，完整曲线见[六页PDF](entry_method_exploration/20261028_reuse_completion_routing_v1/ACSG_复用路由与补全成本实验_20261028.pdf)。

## 成本与实际救回

同批L200下，COCO REUSE-REG的额外平均耗时由BLOCK-R2048的137.47降至74.69μs（减少45.7%），成员救回次数2555→2376（召回增量0.2555→0.2376pp）；Recall为95.5820%、QPS1823.14，仍被GT10 L216的95.7947%/1983.71覆盖。Deep REUSE-REG额外耗时140.98→137.90μs（仅减少2.2%），粗代表评分1024→21.52并未带来同等wall收益；原/新扫描量基本相同，未单独插桩归因。新法97.2993%/1438.90仍被GT10 L216的97.3854%/1672.83覆盖。

直接块主候选REUSE-BLOCK在L200：COCO原遗漏46556，候选块覆盖18932、实际扫描覆盖18747，PQ96仅保留2131并全部救回；Deep原遗漏29220，候选块仅覆盖1091（3.73%），扫描覆盖1090、PQ96覆盖938、最终救回847。事后固定256query的float64原metric诊断：COCO扫描内486个遗漏用精确Top96可全部保留，现有PQ96仅53个；此为排序诊断，不是免费在线性能承诺。Deep两种直接块法各91个短名单到最终返回的损失全部有已返回的相同向量不同ID对应，保留严格GT-ID口径，不改GT或tie规则。

REUSE-REG用入口小表与主返回提出最多32区域，沿旧ridge选择最多2区；REUSE-BLOCK直接提出最多32块，MAIN-BLOCK只用主返回最多8块。块/PQ只读复用，总上限2048码/96精算；区域每区48与直接块全局96不同，不能把全部差额解释为纯路由因果。新池与原全1024粗路由的可见信息不同，不是返回等价工程优化。

## 角色、核验与限制

新表前12K fit、后4K诊断，不做配置选择；旧16K B32含末4K标签，完全排除本轮校准，保留正式参考。历史GT10可能使用合法fit，正式10K历史曝光，无新盲确认。源行角色分开；相同向量SHA交集计数：coco fit/cal=0、fit/test=0、cal/test=0；deep10m_l2_v1 fit/cal=0、fit/test=0、cal/test=0。这些计数不证明语义独立。

全部timed包/三轮SHA、真实主包补全oracle、逐query预算、旧完整包一致、第二份stdlib集合统计、原metric分数及路由/PQ抽检已核验；E188的2145文件seal保持。第二实现为同一执行者，非独立人员复现。失败严格为单query Recall@100<10%（0–9命中），改善、脱离、成员救损、源外救回分开；稀少尾部不外推。

新映射/小表相对E188新增存储与旧后端常驻负担分别报告；suite内含formal wall，不相加。仅COCO raw-IP/Deep squared-L2真实K100，无其他五集/K1新证据；没有逐query跳过或完整搜索状态复用。

七集两K综合证据仍为[E183](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/delivery_v2/report_zh.md)；E184/E185为关联诊断；E188的预算负结果及角色修正保留[历史记录](experiment_history/188_completion_cost_budget_v1.md)。

[实现合同](spec.md) · [下一门](s-target.md) · [历史索引](s-experiment.md) · [70点](entry_method_exploration/20261028_reuse_completion_routing_v1/analysis/points.csv) · [实际预算对照](entry_method_exploration/20261028_reuse_completion_routing_v1/analysis/discrete_comparisons.csv) · [核验](entry_method_exploration/20261028_reuse_completion_routing_v1/reviews/results_audit.json)。
