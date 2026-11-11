# ACSG 当前接续入口

更新于2026-10-28；工作区`/data/netg/ACSG`，分支`research/state-20261002`，HEAD `96cf05d5410cf51272048cd1f90b4bb194e23c62`。E174–189主要是本地未提交工作，HEAD/旧远端不代表完整产物。E189已完成，无待恢复矩阵。

## 阅读顺序

1. [AGENTS.md](AGENTS.md)，再读[summary](summary.md)→[spec](spec.md)→[s-target](s-target.md)→[s-experiment](s-experiment.md)。
2. [E189报告](entry_method_exploration/20261028_reuse_completion_routing_v1/report_zh.md)、[六页PDF](entry_method_exploration/20261028_reuse_completion_routing_v1/ACSG_复用路由与补全成本实验_20261028.pdf)、[70点](entry_method_exploration/20261028_reuse_completion_routing_v1/analysis/points.csv)、[实际预算比较](entry_method_exploration/20261028_reuse_completion_routing_v1/analysis/discrete_comparisons.csv)。
3. [覆盖链](entry_method_exploration/20261028_reuse_completion_routing_v1/reviews/formal_trace_audit.json)、[角色/模型审计](entry_method_exploration/20261028_reuse_completion_routing_v1/reviews/role_model_audit.json)、[核验](entry_method_exploration/20261028_reuse_completion_routing_v1/reviews/results_audit.json)、[状态](entry_method_exploration/20261028_reuse_completion_routing_v1/state.json)。旧方案先从历史卡片进入原协议与产物。

## 已收敛结论

18个新复用点中18个被实测GT10同时覆盖Recall与QPS；离散速度筛选通过0点，预算召回筛选通过0点。 默认E99 GT10保持。复用路由可以减少部分费用，但三种固定版本均未形成对GT10的可靠Recall–QPS改进。本轮直接选块方案在COCO与Deep暴露出不同瓶颈，后续应分别研究近似排序损失和候选来源覆盖。

直接块主候选REUSE-BLOCK在L200：COCO原遗漏46556，候选块覆盖18932、实际扫描覆盖18747，PQ96仅保留2131并全部救回；Deep原遗漏29220，候选块仅覆盖1091（3.73%），扫描覆盖1090、PQ96覆盖938、最终救回847。事后固定256query的float64原metric诊断：COCO扫描内486个遗漏用精确Top96可全部保留，现有PQ96仅53个；此为排序诊断，不是免费在线性能承诺。Deep两种直接块法各91个短名单到最终返回的损失全部有已返回的相同向量不同ID对应，保留严格GT-ID口径，不改GT或tie规则。

新表12K fit、末4K诊断，无配置选择；旧16K B32不进校准、只做正式参考。仅两集K100、历史曝光test，无新盲确认。旧E188的2145件seal未变。

## 可复制接续提示词

```text
请接续/data/netg/ACSG，先只读核分支/HEAD与LOCAL_CODEX_START、AGENTS和四根文档，再读E189报告/覆盖链/角色审计。
E189已完成正式70点/210完整T1轮与校准64点/192轮，默认E99 GT10保持，没有待恢复矩阵。
稀疏入口/主返回候选的费用、覆盖、PQ筛选和最终救回分别见实测；不把少评分/少扫码等同可靠Recall–QPS。
旧B32只作正式参考，禁止用表内校准决定泛化。两集K100历史曝光，不外推其他K/数据。
旧E188/E189科学seal保持；不自动重跑、扩池、修改默认或恢复旧队列。按我的当前明确任务继续。
```

本轮修改前根文档在[E189 source_before](entry_method_exploration/20261028_reuse_completion_routing_v1/source_before/)，旧根SHA保持当时身份；本轮交付收据在[E189目录](entry_method_exploration/20261028_reuse_completion_routing_v1/)。
