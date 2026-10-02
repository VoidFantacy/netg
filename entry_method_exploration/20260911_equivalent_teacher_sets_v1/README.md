# E30 等效三入口集合监督

WebVid2.5M推荐GT10 soft；Yandex10M IP推荐GT10 hard。

两集4次训练、2个漂移控制、完整fit/开发和120正式点五轮单线程wall已完成。状态`EQUIVALENT_TEACHER_SETS_COMPLETE_NO_RELIABLE_REPLACEMENT`，原NSG调用3,177,280，新训练标签0。

- [完整报告](report.md)、[主Recall–QPS](figures/recall_qps_main.svg)、[全部方法](figures/recall_qps_all.svg)、[Excel数据](chart_data.xlsx)。
- [协议](protocol.md)、[方法研究](research.md)、[选择判定](results/method_selection.json)、[开发门](results/development_gate.json)、[最终验收](reviews/final_audit.json)。

所有结果为历史query上的本地探索；描述性最快和可靠推荐分别记录。新执行使用独立版本，不覆盖当前模型、标签和原始输出。
