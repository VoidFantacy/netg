# ACSG 当前结果摘要

2026-09-13限时探索与汇报已收口，共14个串行会话；监督器于21:00:01.595123按截止退出，最终检查确认无待恢复任务。实际最终实验仍为E94：双集各2000查询、五L五轮、50原点/250wall已完整实测。**尚未找到稳定优于当前GT10起点的新方法，默认保持Web GT10-soft-t1 / Yandex GT10-hard。** 限时任务完成不等于研究目标达成；[监督最终检查](entry_method_exploration/20260913_post_closeout_handoff_v1/evidence/review_217_final_goal_audit.json)接续了第14会话“等待收口”的历史状态。原报告、campaign state与封存保留。

顺序均L64/128/256/400/800，Recall为百分点，失败为零GT10命中净新增。

| 最终同批2000对比 | Recall变化 pp | 失败净新增 |
|---|---|---|
| Web组合 / compact | +.095/+.270/+.080/+.085/+.030 | −3/−4/−1/−1/−1 |
| Web组合 / 匹配GT10-soft P | −.340/−.385/−.410/−.125/−.105 | −7/−1/+4/+2/+1 |
| Y compact / GT10-hard P | +.090/+.070/+.120/−.030/−.125 | +3/−2/−4/−1/+2 |

Web局部修复有迁移，未补齐相对P损失；Y低L正、高L损伤。组合/compact与Y/P的五档QPS交叉范围均跨零；组合/P L128略负，其余跨零。同Recall插值只作描述，不是新增等Recall测量或GO。

E93核对77目录、41项同aux7952评分后冻结：Web best_all=P、best_new=E92反证，Y两角色compact。之后才打开E34历史validation2000；最终反馈未回流训练/选型，held-out未开。P-fit含旧train/monitor，aux/cal/audit历史使用，动作接受反馈算训练，不能称全项目盲验证。

E92线上1771画像slot/815真实入口，Y compact为2067/821；一次小HNSW七slot去重三入口+原NSG/rawIP。E60有限小动作辅助支持稀疏，E89较大父恢复训练中同时增损与并图交互明显；两种证据不混为共享表示无解。

收口后与用户讨论的当前判断：**保留离线学习入口画像/小图的目标，下调现有参数扰动型RL及局部修补分支的优先级，先重新设计方法。** E50已证实正候选到确定更新的转化缺口，E52直接择优、E53反馈步长及E56纯构图RL均有局部信号，尚未建立稳定额外价值；不能把全部失败归因于RL，也不能只靠扩大训练预算。当天多数新方法是确定性离线构造，后期相对compact的修复未补齐相对原P的损失。完整依据见[复盘86](experiment_history/86_post_closeout_rl_direction_review.md)，后续范围见[s-target](s-target.md)。本次只更新文档，0新增实验/训练/ANN/构图/GT/QPS。

E94实际700800NSG/560000HNSW，native操作994.213s与纯wall695.047s分开；8源小图、40plain+40count加载、0新拟合/普通build/GT。继承100000集合评分、70000原基线回归、800原kernel及跨L图/七slot验收通过。401独立失败query的完整五L为10730单元，原812query×L零事件为4230单元，两表分开。全日6854176NSG/17820080HNSW/360普通build不变，旧四开发QPS批不拼最终曲线；完整训练/GT成本未知项保持。

第13会话核对50点/250轮/65配对表级算术、10730呈现单元逐字段一致；未重复原raw评分。中文四图、六页PDF、单文件离线HTML已生成。监督侧实际桌面/手机浏览器穷举401query×五L及两种CSV下载通过；第13执行沙箱的两次浏览器启动失败记录与独立成功证据分开。监督208随后已实际逐页查看完整六页PDF；第14会话核对交付身份并继承该验收，不重复浏览器或原始评分。当前入口见[交付清单](entry_method_exploration/20260913_until2100_v1/session14_closeout_v1/delivery.md)。

[当前收口后交接](entry_method_exploration/20260913_post_closeout_handoff_v1/handoff.md) · [整日中文汇报](entry_method_exploration/20260913_until2100_v1/session13_report_v1/report.md) · [离线查询浏览](entry_method_exploration/20260913_until2100_v1/session13_report_v1/report.html) · [六页PDF](entry_method_exploration/20260913_until2100_v1/session13_report_v1/report.pdf) · [机制边界](entry_method_exploration/20260913_until2100_v1/session13_report_v1/mechanism_note.md) · [E94完整原报告](entry_method_exploration/20260913_until2100_v1/stage35_final_comparison_v1/report.md) · [下一步](s-target.md)。
