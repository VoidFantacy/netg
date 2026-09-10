# 当前执行状态

2026-09-09 20:19（北京时间）单线程正式评测已启动。

- 全部169,857,792次正式标签调用和12个冻结模型复用；不重新标注或训练。
- 原16线程评测已按用户指令停止，日志和结果保留，最终主表不使用。
- Fast及全部新方法/对照统一1线程，配置、OpenMP team、Linux进程线程数均已在启动时确认。
- 控制器PID 5513；日志logs/controller_single_thread.log。
- 结果独立落在single_thread_v1/results/。最终报告尚未生成。
- 单线程耗时将比此前16线程估计增加；计划北京时间20:55（12:55 UTC）首次检查，用已完成批次估算余量，期间不反复查看。

规则与修订：[evaluation_single_thread_amendment.md](evaluation_single_thread_amendment.md)。

2026-09-09 20:34（北京时间）新增用户要求：最终比较NSG、Fast和A+B的Recall@10、QPS、失败数量/率。NSG自动队列8259已注册等待当前单线程任务退出，之后同批重测基线；当前任务不被打断。见[baseline_pipeline.json](baseline_pipeline.json)与[比较修订](baseline_comparison_amendment.md)。

2026-09-09 20:53（北京时间）按用户询问进行一次估时核对：单线程12个校准/audit批次完成；首个正式WebVid批次已完成2轮计时，含warmup每轮约466秒。预计全部正式比较、NSG补测和汇总还需8–10小时，约9月10日05:00–07:00完成；不沿用16线程估计。详见[估时依据](eta_single_thread_20260909T1253Z.json)。

用户指出探索阶段测量过多后，已停止单线程控制器和NSG后续队列，保留全部产物。已完成12个校准/audit批次及WebVid seed20260828的完整单线程validation批次（1661.5秒）。其余大矩阵不再自动继续，之前8–10小时ETA已经失效；当前先说明测试规模并缩减探索范围。

最终：五点精简探索完成并复核，两个数据集过程wall合计165.16秒；NSG/Fast/A+B三指标及五L入口不变均已核验。结论EXPLORATORY_NO_OVERALL_FAST_GAIN。完整结果见exploration_5point_v1/report.md，所有旧队列保持取消。
