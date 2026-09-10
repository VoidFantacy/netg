# 本地依据与只读范围

当前结论以本轮读取的本地文档、源码和已有聚合结果为准。下表区分完整阅读的设计/交接材料、定向核查的实现和未访问的数据；目录中的论文资产不等同全部逐页精读，具体范围见[papers.md](papers.md)。

## 必读交接和方法设计

按指定顺序阅读当前 [AGENTS.md](../../AGENTS.md)、[summary.md](../../summary.md)、[spec.md](../../spec.md)、[s-target.md](../../s-target.md)、[s-experiment.md](../../s-experiment.md)，继而阅读历史卡片 [08](../../experiment_history/08_fast_router_diagnosis.md)、[09](../../experiment_history/09_research_designs_not_experiments.md)。当前状态与历史建议不一致时，以当前契约和原始证据判定；没有把旧研究计划作为新实验授权。

以下方法目录中的 README、理论/assessment、protocol草案及state均已阅读，来源manifest用作文件身份和追溯入口：

- [AB R0 README](../20260909_ab_joint_r0_v1/README.md)、[theory](../20260909_ab_joint_r0_v1/theory.md)、[state](../20260909_ab_joint_r0_v1/state.json)。
- [A R0 README](../20260909_a_r0_v1/README.md)、[assessment](../20260909_a_r0_v1/assessment/assessment.md)、[protocol](../20260909_a_r0_v1/assessment/protocol_draft.md)、[state](../20260909_a_r0_v1/state.json)、[source_manifest](../20260909_a_r0_v1/source_manifest.json)。
- [B R0 README](../20260909_b_r0_v1/README.md)、[assessment](../20260909_b_r0_v1/assessment/assessment.md)、[protocol](../20260909_b_r0_v1/assessment/protocol_draft.md)、[state](../20260909_b_r0_v1/state.json)、[source_manifest](../20260909_b_r0_v1/source_manifest.json)。
- [v4 report](../../entry_selection_research/20260908_v4/report.md)、[method](../../entry_selection_research/20260908_v4/method.md)、[minimum_gate](../../entry_selection_research/20260908_v4/minimum_gate.md)、[state](../../entry_selection_research/20260908_v4/state.json)，及reviews目录下五份分析文档和resolution记录：graph_entry_literature、policy_compilation_literature、independent_literature_review、independent_design_review、local_failure_audit、resolution.json。
- [v5 joint_entry_design](../../entry_selection_research/20260908_v5/reviews/joint_entry_design.md)、[v5 utility_representation](../../entry_selection_research/20260908_v5/reviews/utility_representation.md)。

v4 的 source_before/source_after 是当时交接文档快照，delivery_manifest、document_checks和completion是交付记录。本轮检查其目录、清单及变更内容，不把历史快照覆盖当前根文档。与本次结论直接相关的论文/作者代码重新核对；其余存档源码不声称完成新的逐行审计。

## 原始结果和实现的定向核查

| 结论 | 本轮依据 | 核查边界 |
|---|---|---|
| E20的单入口空间、ties、跨L及近邻迁移 | [原protocol](../../fast_router_diagnosis/20260908_v1/protocol.md)、[report](../../fast_router_diagnosis/20260908_v1/report.md)、[state](../../fast_router_diagnosis/20260908_v1/state.json)、[analysis/v2](../../fast_router_diagnosis/20260908_v1/analysis/v2/analysis.md)及其analysis.json聚合结构 | 使用已存报告和正式v2；未重新运行搜索或统计bootstrap |
| E20不能提供纯路由时间或部署QPS | [costs_v2.json](../../fast_router_diagnosis/20260908_v1/results/costs_v2.json) | HNSW构建/路由独立和联合结束计时均缺失、字段为null；旧stage=route是开始事件 |
| Fast画像GT1-basin、单位query求和+prior | [build_fast_entry_variants.py](../../benches/run/build_fast_entry_variants.py)，`build_gt_basin_prototypes`约144–182行 | 读取构造函数；未加载或复算原始query/GT/base |
| Fast输入及检索后端 | [test.cpp](../../benches/test.cpp)，EntryPointSearcher约53–162行及在线searchKnn | 使用原query、IP路由；旧正常调用top3 |
| E20的Fast1来自同一top8检索前缀 | [fast_router_diagnosis.cpp](../../fast_router_diagnosis/20260908_v1/src/fast_router_diagnosis.cpp)，Router约85–122行 | M16/efConstruction200/ef10，原真实base ID作为HNSW外部label |
| 原search消费入口及L语义 | [ACSG.cpp](../../ACSG/ACSG.cpp)，约1490–1645行 | mode2只消费前3个位置再去重；合法单元素列表可调用一次原搜索；本轮不改kernel |
| 新的多slot不能使用重复base ID作索引label | [hnswalg.h](../../benches/hnswlib/hnswalg.h)，约1160–1180行 | 相同label调用addPoint会updatePoint，而非新增另一slot |
| IP并不自动单位化向量 | [space_ip.h](../../benches/hnswlib/space_ip.h)，InnerProductDistance与SIMD分派 | `1−dot`；新向量归一化或增加维度会改变模型/运算路径 |
| v4不是teacher先过关的小树模仿器 | [v4 method](../../entry_selection_research/20260908_v4/method.md)和[独立设计审查](../../entry_selection_research/20260908_v4/reviews/independent_design_review.md) | 直接效用树；实际子树动作差；多叶同hub；教师只是独立参照 |
| 历史真实效用和soft labels已存在 | [local_failure_audit](../../entry_selection_research/20260908_v4/reviews/local_failure_audit.md)，并追溯其所列源码/历史卡 | 报告只使用机制层区别，不重分析历史validation结果或将旧失败扩大为普遍NO-GO |

本轮E20引用按原结果的精度与样本边界陈述：全H oracle、C8 oracle与部署策略分离；独立single命中并集不作为真实联合搜索；两L A0交集不作为存在廉价共享函数的证明。当前C分支的既有停止结论仅用于状态定位，不作为A+B实验结果。

## 本轮产物与禁止项

本轮写入范围只在新目录 `entry_method_exploration/20260909_ab_readonly_research_v1/`。产物为报告、论文清单、静态论文/作者源码副本及来源/完整性记录。这里保存的作者`.py/.cpp`不是新写的ACSG trainer/router，也没有被执行。

本轮没有修改ACSG核心源码或根目录summary/spec/s-target/s-experiment；没有实现trainer/router/index；没有生成标签、训练模型、构建ANN索引、运行ANN搜索或打开validation/held-out原始数据。也未读取base/query/GT/图的二进制内容。已有文本报告、源码和manifest中出现数据路径，不代表访问了这些路径对应的原始数据。

开始时工作区已有大量未提交修改及删除，保留原样。保护清单为[protected_before.json](protected_before.json)，结束检查见[integrity_check.json](integrity_check.json)。其作用是证明列出的源文件/文档及tracked状态在本轮前后未变，不将有限清单的核对夸大为所有原始大文件均重新hash过。

当前研究状态为 `RESEARCH_COMPLETE_AWAITING_METHOD_SELECTION`。下一阶段由方法选择决定；报告中的样本量、优化超参数、标签调用算术和gate均为设计，不自动启动。
