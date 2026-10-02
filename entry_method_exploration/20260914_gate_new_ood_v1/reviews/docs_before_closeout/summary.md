# ACSG 当前结果摘要

2026-09-14 E96 正在执行：WebVid、Yandex、LAION 三集 release10 GATE 新特征/标签/训练及LAION GT10开发选择已完成；Web/Y全量HNSW往返验收通过。LAION已插入全部10004480节点，在最终索引保存时触发/data空余1.5GiB保护而退出；已校验转存本轮未完成构建文件到系统盘，保留原路径链接和完整检查点，继续恢复保存/全量核验。随后运行16预算至1500的192点/576次单线程wall，输出Recall–QPS和零命中失败率。尚无public正式结果，默认GT10保持。[协议](entry_method_exploration/20260914_gate_new_ood_v1/protocol.md) · [采样修正](entry_method_exploration/20260914_gate_new_ood_v1/sampling_amendment.md) · [存储恢复](entry_method_exploration/20260914_gate_new_ood_v1/reviews/storage_recovery_20260914T2113/manifest.json) · [状态](entry_method_exploration/20260914_gate_new_ood_v1/state.json)。以下为已结束E95旧增强分支的结果。

2026-09-14：**停止当前固定H画像/小图增强分支；没有得到稳定优于GT10的新方法。** 默认保持Web GT10-soft-t1 / Yandex GT10-hard。用户要求“持续推进，最后给出结论，要么有更好的方法，要么停止当前分支”，本轮在既有证据复核与三类机制比较后，实际完成E95，并按预锁开发门给出停止决定。[当前结论](entry_method_exploration/20260914_query_moment_graph_v1/decision.md) · [复盘87](experiment_history/87_query_moment_graph_and_branch_stop.md)。

E95用原fit20K查询二阶统计构造full/diag小图，再逐字恢复原GT10画像P用于线上评分；原H815/821、raw-IP、NSG及HNSW3接口不变。两集各7952历史开发query、L64/128及固定两半，identity/full/diag全部实际执行。相对各集原GT10：

| 候选 | L64 / L128 Recall变化pp | L64 / L128零命中失败净新增 |
|---|---:|---:|
| Web full | −2.3868 / −1.4940 | +225 / +130 |
| Web diag | −3.8556 / −2.0297 | +359 / +165 |
| Yandex full | −0.0553 / −0.2364 | +23 / +28 |
| Yandex diag | −0.0478 / −0.0666 | +3 / +3 |

八个全量、16个半集Recall差全部负，四个候选–数据集组合均未过门。路由NDC下降5.50%–52.82%并未带来更好的完整搜索；前三项L128总NDC反增，Y diag略减但质量仍退化。**本轮QPS未测，条件完整wall依门未启动**，不能称新速度或前沿结论。[完整原表](entry_method_exploration/20260914_query_moment_graph_v1/results/aux_paired.csv) · [E95报告](entry_method_exploration/20260914_query_moment_graph_v1/report.md)。

E95实际194304 NSG/193920 HNSW、6次普通小图构建含两identity、4次P恢复安装；统计0.389s、native构图0.270s、四查询进程操作182.810s分开。96960返回独立集合评分、16160基线八字段回归、384原kernel样本、跨L入口及图字节核验通过；CPU15/实际单线程、串行。0新GT、梯度、依赖安装、编译或性能点。aux反馈计开发/训练信息，完整旧GT/P成本未知；E94最终数据未用于本轮设计/调参/查询，held-out未开。

停止依据同时保留不同证据：E50更新转化不足，E52/E53已实际改进更新方式，E56纯构图有局部信号；E60仅固定小动作支持稀疏，E89/90较大动作有查询间增损、并图与迁移问题。不能将这些合并成“全部RL无效”。本轮闭式统计构图实测也失败，故不再扩大相同参数扰动、画像增补/分组、补边/父恢复/组合修补或统计变换网格。保留GT10及全部局部正信号，不宣称整个ACSG或全部离线入口学习无解。[机制复盘86](experiment_history/86_post_closeout_rl_direction_review.md) · [停止范围与接续](s-target.md)。

最近完整五L五轮性能对照仍是9月13日E94：双集各2000查询、50点250wall。Web组合相对compact五档修复，但相对GT10-soft五档Recall仍负；Y compact低L小正、高L损伤，无稳定整体Recall–QPS优势。401独立失败query的完整五L表10730单元、中文图/HTML/六页PDF均已交付。最终集为历史validation，不能称全项目盲集；模型先冻结，本次最终反馈未回流选择。[E94原报告](entry_method_exploration/20260913_until2100_v1/stage35_final_comparison_v1/report.md) · [交互汇报](entry_method_exploration/20260913_until2100_v1/session13_report_v1/report.html) · [PDF](entry_method_exploration/20260913_until2100_v1/session13_report_v1/report.pdf)。

9月13日14会话及21:00监督收口保持历史身份；其全部模型/raw/选择/wall/报告/seal不改。当前无待恢复实验或后继队列；本轮前件见[E95 source_before](entry_method_exploration/20260914_query_moment_graph_v1/source_before/)，完成核验见[completion_audit](entry_method_exploration/20260914_query_moment_graph_v1/reviews/completion_audit.json)。
