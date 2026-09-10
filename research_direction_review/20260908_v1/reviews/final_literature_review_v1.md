# 综合报告与新版计划：独立文献复核

状态：**PASS；未发现阻断或实质性文献错误。另有两项不影响结论的措辞建议。**

复核时间：2026-09-08。范围为 `../report.md` 全文与根目录 `s-target.md` 第1–39行的新计划；没有重新审核后者历史协议。核对本轮三份文献表、已保存全文的相关段落，并直接刷新 NGFix、PAG、VIBE、OOD-DiskANN 的一手版本页面。未运行实验，未打开原始 GT/query/base/图，未改主文档。

本次读取对应 SHA-256：

- report.md：`0402fbe37a061fe9ca16980ec15116bae2c9e0233a9e387ed034340359c369f6`
- s-target.md：`b874d2e104cfcca30e233f08d3d8210cee91db653345d3f68b86359642a89716`（全文件哈希，仅审核新首部）

## 核对结果

| 检查项 | 结果 | 依据 |
|---|---|---|
| 14篇核心集合与排除项 | PASS | 表中独立论文链接数为14；路由6篇 GATE/LIRA/kRt/LTR-IVF/TaCo/NeuRoute，加 OOD 图6篇 RoarGraph/OOD-DiskANN/NGFix/PAG/VIBE/Big ANN，再加 root 两篇 Adaptive Beam/Optimistic Routing。没有重复计数。CDMG、Learning Partition Trees 未混入核心。 |
| 时间与发表状态 | PASS | GATE KDD2025、LIRA WWW2025、kRt PVLDB2025、LTR SIGIR2024、TaCo SIGMOD2026 与论文首页一致。NeuRoute明确预印本；OOD-DiskANN明确2022历史工作。NGFix作者版本页注明SIGMOD2026 accepted；PAG v2为2026-07-21，VIBE v3为2026-08-23。Big ANN是2025发表的2023竞赛总结，没有把竞赛年当发表年。 |
| GATE方法与成本 | PASS | report仅称真实hop监督query–hub，符合§4.2；没有将GT区域质量等同于标签，也没有省略全query×hub代价。计划明确受约束适配不冒充原论文复现；raw-IP与计时需要重新验收。 |
| 分片路由的外推边界 | PASS | LIRA复制/分片内HNSW、kRt多代表分片路由、LTR片内精确覆盖、Optimistic独立片区扫描均与证据表一致。没有把它们的收益推成跨区原图静态容量保证。 |
| 搜索过程文献与metric | PASS | Adaptive Beam是metric条件下的距离停止规则；TaCo/NeuRoute改变索引结构，论文L2设置不能作为本地raw-IP结果。NeuRoute GPU训练与并非普遍领先均被保留。 |
| OOD图与反证 | PASS | 没有把PAG随机投影误写为RoarGraph二部投影，也没有把NGFix历史query定理外推到所有新query。VIBE/竞赛只用于提示通用强实现，不当本地性能或纯拓扑归因。 |
| 新颖性与失败范围 | PASS | 明确“query自适应预算”概念已有前作；缩小RoarGraph/NGFix不等于创新。CDMG全文缺口保留。P3负结果不泛化成全部层次路由/固定图策略失败；GT oracle不称全局上界。 |
| 强基线前置及PyANNS状态 | PASS | s-target的R0a在新机制之前；同图归因与完整系统分开，普通大beam/多入口列为必要对照。第18行明说PyANNS尚未本地验收，没有将“优先核验”写成性能承诺。 |
| 筛查与执行边界 | PASS | 六点矩阵是待冻结的新设计；使用旧pilot不是独立测试。Oracle只作诊断，真实API不得含GT。缺匹配/精度不足为INCONCLUSIVE，不自动扩扫；原P3、原关闭状态保持。 |

## 两项非阻断建议

1. **report.md 第35行**：“首次命中仅是可观测标记”建议改为“首次命中仅是在离线GT对照下可识别的诊断标记”。真实在线检索不能知道哪个点属于exact GT；下文无GT接口已经规定清楚，但这里再限定可防止读者误读为在线策略特征。
2. **report.md 第45行**：“核验过的 GATE 受约束适配”建议改为“通过验收后的 GATE 受约束适配”。s-target已把它放在待做R0a中；改时态可避免综合报告单独阅读时被误认作适配已验收。

两项都是表达消歧，不要求新实验，不影响本次文献判断与计划修订通过。若主审采用，可仅改相应句子，旧结论与执行边界无需改变。

## 直接刷新的一手元数据

- [NGFix arXiv v1](https://arxiv.org/abs/2510.22316v1)：2025-10-25提交，作者注明SIGMOD2026 accepted。
- [PAG arXiv v2](https://arxiv.org/abs/2603.06660v2)：2026-07-21修订，作者注明ICML2026 poster；报告仅写版本日期，无夸大。
- [VIBE arXiv v3](https://arxiv.org/abs/2505.17810v3)：2026-08-23修订，注明Journal of Data-centric Machine Learning Research (2026)。
- [OOD-DiskANN arXiv v2](https://arxiv.org/abs/2211.12850v2)：2022-11-30修订，确为历史项。

本复核没有独立复现任何论文，也没有再次逐页复读其全部证明；相关方法判断沿用本轮已实读的全文证据，并对综合报告是否忠实引用进行独立检查。本地P2/P3数值与统计不是本次文献复核的独立验收对象。
