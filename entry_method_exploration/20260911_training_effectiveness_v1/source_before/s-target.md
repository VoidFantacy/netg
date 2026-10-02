# ACSG 下一阶段方向与实验接续

2026-09-11。E30等效集合教师的训练、漂移控制、真实Recall–QPS及择优已完成，状态`EQUIVALENT_TEACHER_SETS_COMPLETE_NO_RELIABLE_REPLACEMENT`。WebVid2.5M推荐GT10 soft；Yandex10M IP推荐GT10 hard。 本轮用户要求的依次执行及最终图表交付已经实现，原版本预算收口。

## 1. 当前可采用的结果

| 数据集 | 本批插值速度几何均值最高 | 相对原默认 | 推荐 |
|---|---|---|---|
| WebVid2.5M | GT10 soft | +0.00% | GT10 soft |
| Yandex10M IP | GT10 hard | +0.00% | GT10 hard |

推荐与描述性最快分开；共同Recall插值不等于新增精确等Recall点，也不是新盲测。全部12方法曲线及五轮原值见[报告](entry_method_exploration/20260911_equivalent_teacher_sets_v1/report.md)、[图](entry_method_exploration/20260911_equivalent_teacher_sets_v1/figures/recall_qps_all.svg)、[Excel](entry_method_exploration/20260911_equivalent_teacher_sets_v1/chart_data.xlsx)。

## 2. 本轮之后的研究判断

开发门为`STOP_FURTHER_MODEL_EXPANSION`。G不唯一已被证实，但单/多集合、位移控制、完整fit及开发不能自动串成性能因果证明。若继续研究，应先解释剩余错误发生在已知C8排序、全H画像打分、近似路由还是实际NSG效用；现有[训练/部署分析](entry_method_exploration/20260911_equivalent_teacher_sets_v1/report.md)和[完整fit分组](entry_method_exploration/20260911_equivalent_teacher_sets_v1/results/fit_groups.csv)优先复用，不重复相同网格或直接增加模型容量。

如果目标转为确认当前默认的可靠性，应先建立独立复现协议、明确新的query/图或重复条件与成本；不要将本轮已经反复使用的validation称为新验证。任何新画像、优化、HNSW参数或新query均是独立版本，不能从已有输出推算其QPS。当前没有启动后续训练或新的held-out测试。

## 3. 已完成步骤与停止位置

- 严格并列G、single/multi同竞争域控制：4次训练已完成；新标签0，复用224万逻辑三元组。
- 两集multi均缩到single均方位移，系数仅来自fit，single_matched同字节alias；全部实际画像均完成真实检索。
- 完整fit、cal/audit及exact诊断完成；开发门各条件、正负query和几何/分数梯度限制保留。
- 正式两集12方法×5L×五次单线程wall完成，选出描述性最快及有证据支持的推荐。正常调用3,177,280，修复0，不借余量扩网格。

## 4. 接续与保护

先读AGENTS、summary、spec、本文件、[历史19](experiment_history/19_equivalent_teacher_sets.md)，再沿[协议](entry_method_exploration/20260911_equivalent_teacher_sets_v1/protocol.md)、[状态](entry_method_exploration/20260911_equivalent_teacher_sets_v1/state.json)、[选择判定](entry_method_exploration/20260911_equivalent_teacher_sets_v1/results/method_selection.json)、[验收](entry_method_exploration/20260911_equivalent_teacher_sets_v1/reviews/final_audit.json)核对原件。E24–E30图/H/源码/GT/标签/模型/日志与结果保留，旧runner拒绝覆盖。

正式测试继续CPU15/实际线程1，一次一个方法；训练/标签/重分析不与计时并发。fit/cal/audit/validation都有历史使用，held-out未读取/hash。新任务须先说明它与已经完成的教师身份对照有何实质区别，并锁定预算、比较与停止条件。
