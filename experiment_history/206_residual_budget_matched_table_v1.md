# E206 按较小预算构建固定残差表

2026-11-20 完成。COCO/WebVid 离线验证真实 K1/K100，生成128,000次真实训练 ANN，完成384,000次表合并。仅 WebVid K100 通过预锁继续条件并完成32点、64个完整CPU15单线程批次，每点两遍。

B32-L184 和 B32-L200 复用同一 fit 身份、K100、原三路联合嵌套贪心和在线32表位。校准 L184 对同 fit 旧表，COCO K100 净增28个、WebVid K100 净增45个，只有后者通过。两集 K1 未过继续条件。WebVid K100 校准中，新表相对 L192 旧 fit 表仍少1,304个正确成员。缺口从训练源和三路候选阶段累积，进截断池的参考正确成员均由实际精算救回。

WebVid K100，B32-L184 在 L184 为 73.4082% / 1469.37 QPS，旧完整 B32 在 L192 为 74.1992% / 1407.59 QPS，变化为 -0.7910 个百分点和 +4.39% QPS。正式网格中，新表4点有0点被完整 B32 的同期测点覆盖，0点在两遍QPS范围完全分离的口径下被覆盖。GT10、完整 B32、REUSE-SQ 取并集时分别覆盖0/4、0/4点。四个同 L 点全部较完整 B32 少 0.1310–0.1343 个百分点，平均 QPS 高 0.08%–0.40%，无新点在实测网格同时超过完整 B32 的两项指标。本轮未建立 L184 对旧完整 B32 L192 的替换依据。当前默认采用 E99 GT10（WebVid soft-t1），保留完整 B32 已验证的条件有效区间。 公共10K已用于历史方法比较，作为固定公开性能场景，方法比较仅使用同期 QPS。原训练角色、审计与原包保留，现无待恢复队列。

[报告](../entry_method_exploration/20261120_residual_budget_matched_table_v1/report.md) · [冻结协议](../entry_method_exploration/20261120_residual_budget_matched_table_v1/protocol.md) · [正式点](../entry_method_exploration/20261120_residual_budget_matched_table_v1/analysis/formal_points.csv) · [缺口](../entry_method_exploration/20261120_residual_budget_matched_table_v1/analysis/gap_coverage.csv) · [状态](../entry_method_exploration/20261120_residual_budget_matched_table_v1/state.json) · [验收](../entry_method_exploration/20261120_residual_budget_matched_table_v1/reviews/delivery_validation.json)。
