# ACSG 当前接续入口

2026-11-02，工作区/data/netg/ACSG，HEAD96cf05d5410cf51272048cd1f90b4bb194e23c62。E197七集瓶颈分离完成9434点/28302完整T1，默认E99 GT10保持，无待恢复矩阵。先读AGENTS、summary、spec、s-target、s-experiment，再读[定位结论](entry_method_exploration/20261101_residual_bottleneck_separation_v1/findings_zh.md)、[详细表格](entry_method_exploration/20261101_residual_bottleneck_separation_v1/report_zh.md)、[交付核验](entry_method_exploration/20261101_residual_bottleneck_separation_v1/delivery_validation.json)。

336学习器窗口点均被强GT10/B32/SQ覆盖；入口内有教师空间，识别和拒绝尚未兑现可靠完整收益。保留WebVid DIST1-FULL/K1/L200和Q8-B32/K100/L100两个有限观察及历史M5/B32/SQ正面场景。新强监督、两段选择和前置拒绝只是后继建议，不是已实现方法。

2026-11-02关机事件已收口：285冻结身份完好；1原持久窗口、11原三轮六数组包SHA恢复窗口、2新测GIST窗口。恢复动作witness为重放来源，旧中断GIST不拼入结果。所有新证据都已持久化：/root/acsg-e197-storage是真实目录，经storage链接；部分归档在/data/acsg-e197-durable-overflow，以持久文件链接访问。RAM只剩可重建临时内容，不是证据依赖。原日志字节不变，部分移动到持久root并保留原路径链接。

读[恢复与持久化](entry_method_exploration/20261101_residual_bottleneck_separation_v1/reviews/persistent_storage_delivery.json)、[恢复完成](entry_method_exploration/20261101_residual_bottleneck_separation_v1/reviews/reboot_recovery_complete.json)、[存储修正](entry_method_exploration/20261101_residual_bottleneck_separation_v1/storage_amendment_20261102.md)。不要按旧PID、旧session或运行中状态重启。原E195/E196/旧设计科学文件及seal保持，根文档以source_before精确桥接。无新PDF，不自动训练/重跑/发布或改默认。
