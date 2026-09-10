# ACSG 当前研究方案：真实搜索效用驱动的轻量入口决策树

> 2026-09-08。`RESEARCH_COMPLETE_DESIGN_ONLY`。新方法调研已完成，推荐研究允许多个叶子选择同一入口的真实效用斜切树；query-only重参照与树共同拟合、分别审计，质量通过的树再检验完整在线成本。尚无新方法实现、训练、性能GO或待续实验进程。

## 当前证据

本文件统一记录“现在做什么、下一步是什么”；实现与复现契约见[spec.md](spec.md)第18–20节，研究结论见[summary.md](summary.md)。

- 当前[调研报告](entry_selection_research/20260908_v4/report.md)、[方法定义](entry_selection_research/20260908_v4/method.md)、[最小验证草案](entry_selection_research/20260908_v4/minimum_gate.md)。
- [本地旧方法审计](entry_selection_research/20260908_v4/reviews/local_failure_audit.md)、[入口相关论文/作者实现](entry_selection_research/20260908_v4/reviews/graph_entry_literature.md)、[策略树与编译文献](entry_selection_research/20260908_v4/reviews/policy_compilation_literature.md)。

- [根因报告](fast_router_diagnosis/20260908_v1/report.md)：六个诊断问题、数值、理论边界与决策。
- [32项完整统计](fast_router_diagnosis/20260908_v1/analysis/v2/analysis.md)、[机器可读结果](fast_router_diagnosis/20260908_v1/analysis/v2/analysis.json)、[执行台账](fast_router_diagnosis/20260908_v1/state.json)。
- [冻结协议](fast_router_diagnosis/20260908_v1/protocol.md)、[复现说明](fast_router_diagnosis/20260908_v1/README.md)、[独立执行审计](fast_router_diagnosis/20260908_v1/reviews/independent_execution_audit.md)、[独立统计复核](fast_router_diagnosis/20260908_v1/reviews/independent_analysis_review.md)。

两数据集同20K paired Fast、原NSG/raw-IP，各512历史pilot，全H单入口及C8全部pair/triple、最近fit/随机fit控制，共2,770,770次搜索。输入、画像逐字节复算、真实执行与独立分析均通过。仅新版本内增加诊断工具/副本/结果，方法源码和历史产物保护；原始validation/held-out未访问。

| 诊断问题 | 实际发现 | 当前判断 |
|---|---|---|
| 是否实现错了 | 图/base/ID/画像一致，count/plain/repeat及真实入口消费通过 | 检查项内没有发现实现错误，不能扩大成整个算法无缺陷证明 |
| HNSW近似是主因吗 | exact3相对Fast3变化WebVid+0.35/+0.63 pp，Yandex−0.45/−0.31 pp | 效果小、方向不一致，不先扫HNSW补主要缺口 |
| 几何标签代表好入口吗 | 即使直接知道GT1 basin，全H最佳single仍高4.80–13.07 pp | 当前监督代理不等于真实搜索效用；单均值、多模态、prior等尚未分别干预 |
| C8够用吗 | 全H最佳single仍比exact C8最佳single高3.16–6.66 pp | 短名单内外均有损失，不能默认完美C8重排足以解决 |
| 固定anchor/三入口合理吗 | anchor限制损失0.84–3.11 pp；四点C8最佳single平均均略高于最佳triple | 撤下两个默认限制；oracle未证明single部署最优 |
| 理论上不可学习吗 | 四个最近fit−随机fit主区间均跨0；跨L A0仍有92.19%/96.09%相交 | 当前简单近邻信号不稳定，既无普遍不可学习证明，也无廉价可预测性GO |

所有表中差值限定当前H、给定L、Recall@10和动作家族。同L不等于同NDC/同wall；oracle使用目标标签、免费选择。32项区间来自历史pilot配对bootstrap近似，不能代替三独立构建或正式held-out。

## 当前推荐方法

**离线可以重，在线预测要轻。** 本次推荐对固定NSG/raw-IP、K10与L64/128，保存每个训练query从全H单入口出发的真实Recall/NDC；叶子按到达它的训练查询总收益选入口，分支按当前左右子树实际输出的收益差加权训练。允许多叶同hub，不依赖Fast先给C8/C32，不默认anchor或三个入口。树划分query输入空间，不切base或恢复旧P3区域搜索。

部署只用现有query向量，最多10次线性分支取得一个真实base ID，然后执行原搜索。深度8/10、节点64非零/全维、最少叶样本32是首轮拟议容量；“全H可选”不表示模型最终能输出所有H。多个叶子允许同一入口服务不同查询区域，但不保证20K数据能学好。

它借用TAO式交替优化并适配为逐query实测效用目标，属于本地未测试的方法候选，不宣称树、蒸馏、全H或真实搜索监督首次出现。GATE/LRSG与旧NETG已有离线复杂表达/在线轻量评分；旧ranker已有真实Recall/NDC及软标签。重模型只是query-only高容量参照，树直接优化实测效用，不必复制教师唯一ID，也不能把教师视为理论上界。

## 下一步验证顺序

1. 另立执行版本并冻结输入/split/模型/统计/资源。拟合只用后20K；前10K仍是历史开发池，拟议分校准1024、审计1024，排除已诊断512仅防本轮重用，不变成新鲜测试集。原始validation/held-out保持关闭。
2. 验收完整动作标签和原kernel一致性；重参照与树在同一拟合集共同训练、分别审计。重参照失败只否定当前模型和数据设置，不证明不可学习，也不否决质量成功的树。
3. 测直接效用树的样本外增益，并在重参照增益为正时检查保留比例；比较同结构唯一ID模仿树与简单全H基线，分别记录叶动作集合覆盖损失和分支选择损失。不得用训练loss或ID准确率代替真实Recall。
4. 只有质量门槛通过才把树推理接入完整纯wall，比较Fast1、Fast3和强基线；双数据集、两相邻工作点、三独立构建、尾部及冻结后held-out10K×3要求保留。

草案按22,048行×两L×双数据集H规划72,141,056次标签搜索，总搜索上限80M、搜索wall4h、拟合wall8h，CPU16线程；这些是新方法的拟议有界验证预算，不是正在运行的任务或训练时间预测，也不是沿用旧诊断3M预算。完整参数/验收/停止/产物见[minimum_gate.md](entry_selection_research/20260908_v4/minimum_gate.md)。这里没有已实现、可直接继续运行的新训练命令，也没有新方法GO。

## 保留边界

原`entry_selection_research/20260908_v2`的[调研报告](entry_selection_research/20260908_v2/report.md)、[推荐](entry_selection_research/20260908_v2/recommendation.md)和[最小gate草案](entry_selection_research/20260908_v2/minimum_gate.md)保留历史交付身份。其固定anchor/三入口与40维联合选择器均不是当前默认主线，未训练；诊断前计划见[历史快照](fast_router_diagnosis/20260908_v1/source_before/s-target.md)，本次方法调研前版本见[v4快照](entry_selection_research/20260908_v4/source_before/s-target.md)。

旧R0–R2、分层P3 NOPASS、Multi-view成本NO-GO和夜间state/gate/CLOSED不恢复。候选/base/预处理/metric/图/GT/split变化时按spec联动重建相应下游，保留旧产物。新方法仍须双数据集、强基线、三独立构建、尾部、两相邻工作点与完整成本验证，方法冻结后才使用held-out10K×3。诊断完成不等于长期方法目标完成。
