# ACSG 当前结论

更新于2026-11-02。E198条件残差导航已完成1,480点/4,440完整单线程批次，默认E99 GT10保持（WebVid soft-t1、Yandex hard）。本轮范围COCO/WebVid，真实K100/L100、200、400及K1/L200；两曝光A/B窗口各512。无正在运行或待恢复矩阵。

**完成1,480点、4,440轮完整CPU15/T1测量。7种新学习动作共112个窗口点，其中112个被同窗GT10/OPT-B32/REUSE-SQ强控制覆盖。默认保持E99；有限网格未覆盖也不直接成为默认替换证据。** 最终POLICY相对达到不低于其Recall的最快已测强控制，QPS变化为-47.11%至-2.81%；这是质量门槛比较，控制Recall可能更高，不能一概称严格同Recall。

14个有正增量的窗口中12个前置门仍全部放行；仅WebVid/K100/L400实质筛选，正增量保留80.55%/92.36%，一窗未达到cal90%目标。固定384级联相对最近单入口11正/1平/4负，但完整QPS全部慢11.8%–34.2%；不同种子的实际展开量也不同，不能全部归因模型推断。详见[机制结论](entry_method_exploration/20261102_conditional_residual_policy_v1/findings_zh.md)。

已实现状态匹配的真实单seed效用监督、双塔蒸馏、至多6点教师重排、前置门及0/96/384预算选择。全部直接C始终保留，筛选只决定额外导航入口；不修图、不恢复主beam。完整说明见[方法](entry_method_exploration/20261102_conditional_residual_policy_v1/method_zh.md)，无需重复解释GT10。

缓存共享特征的旧模型返回逐字节等价，完整QPS变化范围+10.74%至+36.70%；这证明有限工程省费，不自动证明达到强前沿。门相对无前置门ADAPT的正增量保留率（有正增量的窗口）为80.55%至100.00%；校准90%目标必须与正式实测分开，全关/全开不自动算识别成功。

| 数据 | 窗 | POLICY K100/L200 Recall / QPS | 质量门槛强控制 Recall / QPS |
| --- | --- | --- | --- |
| COCO | A | 97.1309% / 1469.77 | OPT-B32/L223: 97.3281% / 2321.21 |
| COCO | B | 96.7305% / 1460.63 | OPT-B32/L223: 96.9785% / 2294.49 |
| WebVid | A | 76.6504% / 1052.45 | OPT-B32/L223: 76.6914% / 1530.78 |
| WebVid | B | 76.5508% / 1062.17 | OPT-B32/L223: 76.5879% / 1545.18 |

离线产生2,187,156个候选行、两预算共4,374,312个单seed动作标签；标签进程415.91秒，训练进程196.46秒。正式完整batch wall共1817.20秒；它包含于正式进程耗时，不能重复相加。模型文件量不是驻留RAM，辅助精算/邻接计数不是总NDC或全部访问，完整wall才是费用判据。

所有三轮返回/工作/决策一致，1480包、444416条query witness全排序和73728项独立策略决策检查通过；另有原生/NumPy全标签推断、stdlib整数/hash/wall/强前沿及旧兼容返回包核验。独审为同执行者不同实现。所有新证据持久化，旧科学文件和seal保留，根文档由source_before桥接，无新PDF。

学生fit2048、开发兼门fit512、独立cal512；Q8银行与模型角色沿E197分离，原画像监督交叠披露。开发阶段epoch/λ/门fit共享512，不称完全独立开发。正式两窗已曝光、单图/画像、有限预算与网格、K1稀疏事件、多比较描述区间限制保留。本轮未重做公开窗口GT穷举入口oracle；TEACHER384是学习预测器。

历史E197七集定位与E173/E191/E194条件有效的M5/B32/SQ继续保留原范围和费用；本轮局部结果不否定全部残差方法。参见[历史正面证据](experiment_history/_maintenance/20261029_residual_positive_evidence_sync_v1/conclusion_zh.md)。

当前停在固定验证与方法解释交付边界，不自动追加数据/参数或改默认。后继问题读[s-target](s-target.md)。证据：[完整报告](entry_method_exploration/20261102_conditional_residual_policy_v1/report_zh.md) · [全部点](entry_method_exploration/20261102_conditional_residual_policy_v1/analysis/points.csv) · [强控制](entry_method_exploration/20261102_conditional_residual_policy_v1/analysis/comparisons.csv) · [门](entry_method_exploration/20261102_conditional_residual_policy_v1/analysis/mechanisms.csv) · [交付核验](entry_method_exploration/20261102_conditional_residual_policy_v1/delivery_validation.json)。
