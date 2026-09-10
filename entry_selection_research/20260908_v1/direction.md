# 当前主要方向：改进入口选择方法

> 2026-09-08 用户明确指定。状态：`DIRECTION_SET_RESEARCH_PENDING`。本次完成方向记录与下一对话交接；新方法未确定、未实现、未运行新实验。本文是研究决策，不是实验 gate。

## 1. 研究问题与优先级

在有限历史查询和 CPU 成本约束下，固定原始 NSG 与搜索语义，研究如何低成本选择少量真实 base 入口，使完整路由加搜索的 Recall–QPS 前沿得到改善。Fast v1 保留为基线，其入口构造、表示和选择规则均允许成为研究对象；不能把 Fast 已优于旧方法解释为入口已经充分优化。

优先回答“已有好入口为什么选不中”，并区分候选池缺口、短名单遗漏、排序误差与组合收益。固定图和搜索用于隔离入口贡献；当前不把修改队列、停止规则、区域容量或辅助图作为主要方向。算法形式由下一轮调研与证据决定，不预先指定 MLP、GNN、联合选择或任何新方法名称。

用户认为当前设计工程性较强。对应研究要求是：用明确问题、可解释机制和可证伪预测统一设计，并提供区别于已有工作的实质贡献；模型复杂度本身不构成贡献，启发式也不因没有神经训练而自动缺乏价值。

## 2. 当前实现与证据边界

| 层次 | 当前实现事实 | 待研究问题，尚非已证实原因 |
| --- | --- | --- |
| 候选池 | QGT 查询球面聚类；按簇内查询接近中心的顺序，从其 exact GT 中选未重复的真实 base 节点 | 代表性与实际可导航性是否错位；改候选池是否比改选择器更有价值 |
| 查询匹配 | top-1 GT 向量按 cosine 归入最近 raw hub；归一化查询均值加 raw-hub prior 得到单一 prototype，Micro-HNSW 选入口 | 单一平均画像是否损失可预测的结构；短名单与精排各损失多少 |
| 少量入口组合 | 在线返回少量入口，共享有限搜索池及 visited；Fast 使用 top-3 | 独立排名是否产生冗余或竞争；额外入口的实际条件收益能否低成本预测 |

源码：[Fast builder](../../benches/run/build_fast_entry_variants.py)，重点为 `choose_unique_gt_hubs`、`build_gt_basin_prototypes` 和 `--qgt-only` 分支。旧 `search_new` mode 2 最多消费三个入口；新路径的入口顺序已在夜间 P1 修正。后续比较必须固定真实消费的入口、顺序、去重和搜索语义，不能只看路由输出的 top-m 数字。

已有[WebVid 入口诊断](../../oracle_entry_diagnostics/webvid_validation_1k_current_hubs_v1/results.json)：815 个现有候选、历史 validation 1K、K=10/L=64，Fast Top-3 Recall=0.6523、graph NDC=923.564；遍历现有候选后按真实搜索效果选择的单入口 oracle Recall=0.8024、graph NDC=913.376。差值为 +15.01 pp，支持该历史池存在选择空间。这里使用旧 30K Fast 和旧评测路径，不能与新 paired 20K Fast 混用；免费穷举选择的成本未计入，graph-only 延迟不是部署 QPS，三轮计时不是三个独立 Recall 样本。只引用 K≤L 的有效行；这些结果不证明新方法、双数据集、现行计时契约下能取得同样提升。

同一文件的 `CurrentHub_Diverse_Top3_GreedyProxy` 是单入口命中集合的贪心并集后再真实重放，Recall=0.7617；它不是最佳联合三入口，也不是所有入口策略的上界。真实共享 beam 下增加入口会影响竞争、淘汰和停止，不能未经证明套用单调性、子模性或集合覆盖最优性。

必须共同阅读负证据：[静态 utility ranker](../../sparse_utility_ranker_results/analysis.md)、[probe-reroute](../../probe_reroute_results/analysis.md)、[拓扑特征 chooser](../../trace_conditioned_rerouter_results/webvid_probe10_top32_topology_v4/report.json)、[Multi-view 成本否决](../../target_basin_formalization/20260907_v1/report.md)。它们未建立跨数据集完整成本收益；不能通过扩大普通模型、重扫同类参数或改名恢复旧分支。上述历史报告中的“下一步”受当前 `summary.md`/`s-target.md` 覆盖，尤其不能再按静态 ranker 旧报告自动启动 probe-reroute。

旧 NETG 已使用真实 graph reachability；[GATE](https://arxiv.org/html/2506.15986v1) 已使用真实搜索 hop 监督 query–hub 适配。因此“学习入口”“使用搜索轨迹”“图感知”本身不足以支持新颖性。先复用[已有文献复审](../../research_direction_review/20260908_v1/report.md)及其证据表，再针对入口选择补充原论文与作者源码。该复审中优先修改搜索过程、先做 P2 六点成本筛查的建议现已被本次决策替代；原文保留为历史记录。

## 3. 下一对话交付

下一轮只做方法调研、现有证据复核和实验设计，允许阅读本地源码/已保存结果及联网查原论文/作者实现、写隔离调研文档；不启动训练、构图、ANN 性能评测、参数扫描或新 GT 生成，不读取原始 validation/held-out 查询或 GT，不安装依赖或改方法源码。不要求完成旧 R0b/P2 六点筛查，不恢复旧夜间 runner，也不继承已结束的 07:00 截止授权。

1. 以当前方法为起点，画清候选构造、入口表示、短名单生成、排序/组合选择与实际搜索的调用链。每个缺口区分实现事实、观测证据与假设。
2. 定向调研图 ANN 入口选择、低成本 query–entry 匹配与多入口选择。直接比较 GATE、已有 Fast/NETG 及本地失败分支；IVF/shard 路由只能作为相关机制，需说明与共享图搜索的差别。原文未取得、结论仅来自摘要或假设推断的地方必须标明。
3. 比较 2–3 个有实质区别的候选，推荐一个优先研究方向或给出“暂无足够依据”。逐项说明机制、目标、离线监督与采样成本、在线可用信息、推理/索引成本、CPU/raw-IP/20K 适配、前作重合、失败风险，以及怎样用对照推翻它。不要堆模块，也不要把设计建议说成已验证算法。
4. 设计一个有界的最小证伪方案。可先比较当前短名单内最好入口、现有全池最好入口、预先限定的扩展池最好入口；只有证据需要时再限定少量候选实测单/双/三入口组合。它们是候选诊断，不是本轮已冻结或必须全部执行的实验矩阵。单点 oracle、独立命中并集与真实联合搜索必须分开。
5. 方案明确待新增接口/命令草案（未实现命令须标为草案）、数据和输入绑定、预注册样本/预算/比较族、验收与停止条件、artifact schema、总资源上限。不得从旧 1K oracle 直接设置预期提升。产出调研报告、相关工作比较表、唯一推荐及最小 gate 草案；同步三份交接，完成后汇报，不自动转为实验执行。

## 4. 后续实验的继承边界

后续若另立执行任务，沿用 WebVid-2.5M 与 Yandex official first-10M/raw-IP、CPU、冻结 NSG/base/GT/预处理；保留独立 QGT 5K，20K fit 与历史使用的 10K development pilot 分离，paired Fast 同 20K。旧 30K prototype 只作历史参考，不进入新训练链。pilot 不是未见测试集。完整 validation 文件曾在旧分支做性能评测；分层搜索夜间批次对 validation 只做输入完整性检查，二者不得混为“项目从未使用 validation”。新一轮须记录全部历史使用，held-out 在方法冻结及相应验证通过前不用于新选择。

目标是完整在线成本的性能改善：计入候选检索、打分、组合选择、归一化、去重/重置、搜索与结果写入；GT 评分、hash、trace、JSON 在 timer 外，count/plain 独立并验收。NDC 解释成本，不能代替纯 wall。完整离线成本包括 exact train GT、额外标签/搜索轨迹、候选构造、模型训练与路由索引，缺失项写明。oracle 只作独立离线诊断，真实在线 API 无 GT。

保留双工作负载、至少两个相邻工作点同 Recall QPS ≥+10% 或同 QPS Recall@10 ≥+1 pp 且校正区间支持的最终实质目标，三独立构建、尾部/失败分析及方法冻结后的 held-out 10K×3。具体 pilot 门槛、成本匹配、统计与资源在新协议另行冻结；不照搬旧区域六点矩阵。强基线可比性仍须前置设计，固定图机制比较与完整系统比较分开，论文 QPS 和依赖 smoke 不算本地结果。

旧 P3 NOPASS、P4–P8 未启动、Multi-view NO_GO_ROUTING_COST 及关闭控制全部保留；`state.json`、`CLOSED.json`、旧提示词、实验总结和历史结果不改。当前新方向状态见[交接台账](state.json)，可直接使用[下一对话指令](next_dialogue_prompt.md)。
