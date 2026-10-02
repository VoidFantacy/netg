# ACSG 当前结果摘要

2026-09-13，第7串行会话完成E79。GT10目标方向分组画像与固定行置换控制已经完整双集辅助查询。两集均未通过预锁门，停止本目标分组版本，不选置换控制或扫参数。整日21:00目标未完成，E34晚间最终尚未进入。

原A归属、P画像、E66完整Q分区/子质量/ESS/聚合/W字节恢复。新分组按unit(sum GT10 unit target)，仍聚合原query生成子画像，原P首槽不变；去重后target画像Web1957/Y2239，置换控制1873/2239，真实H815/821/原NSG/raw-IP固定。置换同时影响支持与图，不能只归因于目标身份。

| aux7952主候选 | 对P：净命中 / 失败变化 | 对compact | 对permuted |
|---|---|---|---|
| WebVid | -11 / +7 | +48 / -4 | +73 / -10 |
| Yandex | +0 / -2 | -120 / +11 | +213 / -21 |

完整旧收益保留/丢失、避免旧损失与新损伤、GT成员增损和原门见[E79报告](entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/report.md)。失败严格GT10零命中：完整并集495个dataset/source-row，其中292个失败状态变化，全表保留入口/GT/返回ID。

E73/E74 Yandex局部信号保留：五L相对P命中+99/+59/+38/+1/+15、失败−10/−7/−4/−1/0；五轮QPS范围均跨零，约1.9%～3.0%仅描述性插值。Web L128−23命中/失败+6损伤保留。E75/E77/E78原门失败保持，默认未替换。

E79新增129536 NSG/129280 HNSW/4真实build；4新离线分组、2旧Q复现，0梯度/新GT/编译/QPS。离线88.252s，构图0.754s，native110.052s含加载/count/I/O不当QPS，继承GT/P成本未重测。CPU15/进程及数值库1线程串行，四工具terminal0后独立集合评分，P/C31808行全字段回归、256原kernel与全部7slot/图身份通过。

P-fit20K含旧train/monitor；aux7952及两半已暴露且反馈计训练，cal/audit历史使用。E34最终只留冻结后对照，held-out未打开。E79在实验前另锁6.9GiB下限、64MiB上限和额外36MiB晚间/交接预留，旧版本7GiB及全部seal不改。所有主文档前后快照保持。

[E79失败查询图](entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/figures/failure_queries.png) · [E74完整QPS图](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/report.md) · [下一阶段](s-target.md)。
