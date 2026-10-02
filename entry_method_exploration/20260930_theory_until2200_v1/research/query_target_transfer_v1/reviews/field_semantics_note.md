# 统计字段语义说明（构图冻结后、统计执行前）

主分析源码中的 `best_entry_cosine_query_scaled_mean` 字段名不精确。其明确实现为 `max_h raw_query·raw_base_h / ||raw_query||`，只归一化query，base未单位化，因此应称“单位query对原始入口的最大内积分数均值”，不能称cosine。为保持执行前的源锁，原字段和计算不改；报告采用正确用语。真正最近训练query的cosine诊断则同时归一化两侧，无此问题。本说明不改模型、选择、Recall/QPS、资源或停止规则。
