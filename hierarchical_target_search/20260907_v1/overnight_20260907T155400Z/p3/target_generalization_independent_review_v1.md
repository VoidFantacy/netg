# P3 目标泛化诊断独立审查

**冻结源码和24项独立小型合成检查通过，无剩余修复项。** 源码 SHA：`798e9e3b4b61bc4380879b71aedaec1fae28cf1db38df3595ba2b210b498a5b5`。本审查没有读取真实GT、标签、count行、向量或图，没有运行ANN。

独立 Counter/sorted 对照核对24条合成查询的256叶 top4、D、绝对覆盖及分组贡献；另验证高ID/零质量同分、不可独立分组选top4的反例、空组null、回迁any-pass和重复目标的节点/slot不同分母。已知GT与返回IDs交集确认命中重建和配对方向。

物理GT测试以单次严格定长读取保护前缀，确认不seek、不读suffix、不哈希整个parent；rank99值变化、第二条记录header变化和短读都被拒绝。真实路径仍由冻结P0/fit/模型/分析SHA链绑定，实际执行由root控制。

源码完整保留双数据集×两L×10个固定搜索对照和11个seen数量分箱，不分析Fast未测量事件计数，不为seen/unseen目标分摊NDC。报告只解释已失败分支的结构与目标支持，不证明记忆化、连接瓶颈或预测泛化，不改变P3 NOPASS。

证据：[24项独立检查](target_generalization_independent_checks_v1/report.json)、[完整审查JSON](target_generalization_independent_review_v1.json)。
