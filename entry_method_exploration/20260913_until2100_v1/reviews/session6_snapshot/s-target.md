# ACSG 下一阶段目标与接续

2026-09-13，第6串行会话E75–E78完成；整日21:00目标未完成。唯一写入/实验者，不开并行CLI或子代理，本会话15:21:01前安全交接。

1. 不继续扫层级/收缩alpha/质量权重指数：E75/E77/E78各自原门已失败，S/T/uniform仍为机制控制。下一有实质区别的方向是按GT目标空间拆分同hub训练query，再用原query聚合入口画像；尚未实现、训练或查询。先新版本做0ANN、只用已有P-fit20K GT与base的可行性/空间预算检查，不能把目标分组等同NSG效用或直接启动完整网格。详细方法、控制、未知项与停步条件见[next_stage_design_session6](entry_method_exploration/20260913_until2100_v1/next_stage_design_session6.md)。
2. 保留E73/E74 Yandex局部正信号和Web损伤。后续诊断必须同时计算旧收益丢失、旧损失修复与新损伤；不把低支持/三入口关联当单画像因果。资源不够支持一组完整实验时先完成晚间协议和报告准备，不以少量新查询代替完整门。
3. 晚间20:00停新训练、20:40停新增query、21:00完整报告。先按历史开发反馈冻结best_all与实际best_new及选择规则，再开E34历史validation2000，不能回流训练/选型，held-out不自动打开。规定NSG/Fast/GT10匹配起点/实际新方法同批五L五轮完整wall，aligned返回集合独立评分、零命中失败救回/新增、QPS–Recall/QPS–失败率/按L三指标及失败query图齐备，不拼旧批次。

当前disk约7.06GiB，7GiB下限外另留至少32MiB给最终评测；以现场free减下限、最终预留及交接开销计算累计研究预算，不能再沿用64/128MiB旧阶段上限。新训练目标矩阵只在RAM中流式处理，不复制大输入/旧图、不清理任何旧产物。预算不足则不启动依赖步骤。全部ANN仍CPU15/threads1/数值库1线程串行，原base/NSG/rawIP/GT/真实H固定。

[inventory_v6](entry_method_exploration/20260913_until2100_v1/candidate_inventory_v6.json)逐字段保留旧32项，新增6个主候选配置和6个机制控制，共44；后六个控制不能自动转为最终新方法。fit/cal/audit/aux历史暴露，辅助选择计训练，元数据余行不证明全项目未使用。各阶段source_before/root_after及原seal保留。

[E78报告](entry_method_exploration/20260913_until2100_v1/stage19_child_mass_norm_v1/report.md) · [campaign状态](entry_method_exploration/20260913_until2100_v1/state.json) · [监督备注](/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md)。
