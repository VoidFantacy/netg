# ACSG 当前结果摘要

2026-09-13第10串行会话E89/E90研究与E91工具准备已完成，双集方法完整门均FAIL，默认未替换。整日21:00目标未完成，E34最终完整矩阵仍待执行。

| 阶段/数据 | 训练实际合并收益 | 接受区对compact命中/失败变化 | 对P | 判断 |
|---|---|---|---|---|
| E89 Web | fit20K +224，失败−27 | aux7952 +18/−6 | −41/+5 | 局部修复未胜P/随机 |
| E89 Y | fit20K +114，失败−10 | aux7952 −39/+5 | +81/−8 | 损失compact增益 |
| E90 Web | fit20K +61；支持3976 +49 | 后3976 +21/−1 | −22/+2 | 部分迁移，完整门仍FAIL |
| E90 Y | 0动作/零更新 | 后3976 0/0 | +81/−8 | 逐字compact别名，无新改善 |

E89固定同hub两个子画像恢复父P、32候选真实NSG筛选13/8，再实测并图。E90只用这些13/8固定动作，另3976行训练支持筛选5/0个，两个来源均重测合并，后3976接受完整预冻模型。原1771/2067slot、815/821真实入口、图全部非向量bytes保持；线上仍单小图七slot去重三入口与原NSG。

局部收益与损伤并存：E89 Web31/32、Y26/32动作同时救与伤，事件命中正负部1334/1274与610/625；筛选后单项和297/125，实际合并224/114。E90 Web接受对随机+4命中但多1失败，分半也未稳定。停止这些固定版本，不从接受反馈扫阈值/子集/幅度。训练收益与计数变化不作性能结论。

本会话这两阶段新增346556NSG/3578928HNSW，10物理导出含8非零向量安装/2零更新副本，4离线筛选拟合；0普通构图/梯度/GT/QPS。实际训练104.978s、辅助260.991s操作wall，E89编译13.194s；操作含load/count/cache/I/O，不是QPS，继承GT/P总成本未知。CPU15，实际进程及各库1线程，查询串行。

E90完整421失败并集/185变化、E89 427/193分别保留，不把两批并集数直接相加。P-fit含旧train/monitor；E90支持区明确训练，全部aux/cal/audit历史使用，后半不是盲验证。E34最终query/GT/row和held-out未打开。E89原因表查询后从预冻输入补录；训练图为独立封存补充，原结果不改。

旧正信号保留：E84 Web对compact+42/失败−4仍未及P；E73/E74 Y五L对P命中+99/+59/+38/+1/+15、失败−10/−7/−4/−1/0，五轮QPS范围跨零。最近完整QPS仍E74，不能将本次质量点拼入旧曲线。

[E90报告](entry_method_exploration/20260913_until2100_v1/stage31_cross_source_restore_v1/report.md) · [E89报告](entry_method_exploration/20260913_until2100_v1/stage30_local_parent_restore_v1/report.md) · [E89训练损益补充](entry_method_exploration/20260913_until2100_v1/stage30_local_parent_restore_v1/supplement_training_v1/report.md) · [最近完整QPS](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/report.md) · [下一阶段](s-target.md)。

E91当前最终工具v3已通过旧112640返回/275旧wall及2000内存评分110000行回归、32负例与选型资格闸；0新ANN/QPS，实际final controller与best选择尚未执行。candidate_inventory_v11保留68旧+8新共76项，不代表76项都已排名。七配置本会话质量汇总独立评分111328行后保留428失败并集/194变化；E74重分析全方法414失败query/825query×L事件/4627单元，和旧91配对变化query范围不同。

[第10会话综合报告](entry_method_exploration/20260913_until2100_v1/session10_report/report.md) · [最终工具具体步骤](entry_method_exploration/20260913_until2100_v1/stage32_final_tooling_v1/readme.md)。
