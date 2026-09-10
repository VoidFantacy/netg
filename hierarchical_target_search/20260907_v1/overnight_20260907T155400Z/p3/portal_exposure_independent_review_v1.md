# P3 门户暴露诊断独立审查

**最终 v2 源码和 33 项独立小型合成检查通过。** 源码 SHA：`e76ad3377df984af132596c3dc84f65c9ab3f86c90bbfdbbd1ec7581ce9a9e59`。没有读取真实 count 行、GT、标签、门户数组、向量或图，也没有运行 ANN。

核对了冻结 P3 NOPASS 和诊断协议、4份 verification 的既有 SHA来源、八个固定门户对照、完整 route 不变性、三种实际入口分类、所有空箱和条件权重暴露分数。正权重缺支持使分数为 null，不重新归一化；原始代理增量总和符号单列。

已补齐“同一 query 返回 ID 集合相同，Recall 必须相同”的跨 route 完整性规则。独立样例用已知合成 GT 从返回 IDs 计算 Recall，确认同集合异序、异集合同 Recall、改善和退化均被正确区分；完整 route 相同而 IDs/Recall/计数变化会拒绝。

冻结真实数据诊断仍须 root 单任务执行；本审查不提前宣称实际10K不变性已经通过，也不改变 P3 gate。首次 reviewer 样例中 -.04 的精确浮点比较已改为1e-15容差，失败与原样例保留，implementation无需为此变更。

证据：[独立检查](portal_exposure_independent_checks_v2/report.json)、[完整审查JSON](portal_exposure_independent_review_v1.json)。
