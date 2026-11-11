# E197 候选支持、可预测性与执行方式分离

2026-11-01启动，2026-11-02完成。用户授权更正主线并继续实验，训练费用不作当前否决条件。固定范围9434点/28302完整CPU15/T1批次已收口，默认E99 GT10保持，无新PDF。

## 动机与机制

原预设先训练强入口，现分开候选支持、收益可预测性及执行路径/初始化方式。前8K合法角色编Q8-B32，后8K固定2048 fit/1024 cal；COCO/Flickr身份组及精确向量排重，原GT10监督身份披露。旧16K B32作为强控制，学习器在Q8/L200拟合校准，FULL及其他L为固定迁移。

七集真实K1/K100全C单seed384标签3485197条；比较ridge/HGB并选14模型，门可不展开但保留全部直接C答案。与同数量DIST1、原3seed AUX、同适配层AUX-FAST、CBRIDGE、SHARED、捕获空动作、预先可用信息的EARLY初始化和强GT10/OPT-B32/SQ比较。GT逐query教师不可部署；SHARED不是主beam恢复，EARLY替换入口集合。

## 实测判断

336学习器窗口点全部被本轮强控制覆盖。FULL/K100/L200模型兑现同池教师约15.9%–34.0%；COCO/Flickr/GIST两窗选点胜距离，WebVid/Yandex交叉，Deep/SIFT更差，完整QPS均慢约14.7%–44.2%。门在COCO/Flickr/Yandex/SIFT保留约93%–96%已选正收益；WebVid/GIST全开，DeepFULL58.2%、Q845.5%，未达到cal90%目标。

| 数据 | FULL单入口GT教师增量pp | 模型增量pp | 模型兑现教师% |
| --- | --- | --- | --- |
| COCO | 1.2490 | 0.4248 | 34.0 |
| Flickr | 1.0293 | 0.2773 | 26.9 |
| WebVid | 5.3057 | 1.7900 | 33.7 |
| Yandex | 2.6816 | 0.8213 | 30.6 |
| Deep10M | 0.8643 | 0.1377 | 15.9 |
| SIFT10M | 0.6914 | 0.1211 | 17.5 |
| GIST | 2.2780 | 0.6000 | 26.3 |

共享在固定距离seed上有真实追加救回，但当前完整费用未胜强控制；提前入口有损伤，WebVid负、Yandex局部正。770配置对仅WebVid DIST1-FULL/K1/L200、Q8-B32/K100/L100两窗未覆盖，前者描述区间含0，后者较更高质量完整B32只快约0.38%–0.50%；均不记默认替换。历史有效M5/B32/SQ不受此有限结果否定。

## 成本与恢复

离线标签进程672.13秒，模型拟合117.40秒（含失败环境启动）；正式batch wall16018.96秒。校准、构建、诊断、恢复与归档是嵌套口径，不相加成完整项目耗时。关机后包恢复额外3350.63秒；旧GIST中断进程完整时长未知。

首窗原始证据量触发存储保护，COCO B一次286.94秒尝试全部原字节单独存档后完整重跑。后续关机清空RAM，285冻结身份全保留；COCO A原磁盘包、11窗原三轮SHA恢复包、GIST两窗新测组成正式结果。恢复先以60点/416原件payload字节资格通过，再对全部恢复点匹配每轮六数组SHA；仅如此才复用旧wall。work/seed/witness为重放身份，不声称原丢失文件各自SHA已恢复。每窗验证并持久化后再继续，最终无RAM依赖，部分归档及原日志以持久文件链接访问。

## 验证与边界

原捕获1344调用、6074996评分词、8064线性合并；精简核全分支资格和952旧包对齐。最终9434包/28302轮、2768568候选witness、5403128探针和728旧包对齐；逐候选native/NumPy推断、门分支、stdlib全部GT整数/hash/wall与1624项费用提出检查通过。同执行者不同实现，不独立重采样bootstrap或重跑全部标签。A/B曝光、单图/画像、固定预算、K1少量事件、迁移和多比较限制保留。

后继状态一致监督、query内排序、离线强表示/在线两段选择及前置拒绝均未实现、未测试；本轮不自动扩大实验。旧E195/E196/设计科学文件、原PDF和seal保持，根文档按精确source_before桥接。

## 原始证据

- [定位与新方案](../entry_method_exploration/20261101_residual_bottleneck_separation_v1/findings_zh.md) · [详细报告](../entry_method_exploration/20261101_residual_bottleneck_separation_v1/report_zh.md) · [协议](../entry_method_exploration/20261101_residual_bottleneck_separation_v1/protocol.md) · [freeze](../entry_method_exploration/20261101_residual_bottleneck_separation_v1/formal_freeze.json)。
- [实际点](../entry_method_exploration/20261101_residual_bottleneck_separation_v1/analysis/points.csv) · [强控制](../entry_method_exploration/20261101_residual_bottleneck_separation_v1/analysis/comparisons.csv) · [跨窗](../entry_method_exploration/20261101_residual_bottleneck_separation_v1/analysis/stability.csv) · [瓶颈](../entry_method_exploration/20261101_residual_bottleneck_separation_v1/analysis/bottlenecks.csv)。
- [主核验](../entry_method_exploration/20261101_residual_bottleneck_separation_v1/analysis/analysis_receipt.json) · [stdlib](../entry_method_exploration/20261101_residual_bottleneck_separation_v1/analysis/stdlib_audit.json) · [成本](../entry_method_exploration/20261101_residual_bottleneck_separation_v1/analysis/cost_ledger.json) · [持久化](../entry_method_exploration/20261101_residual_bottleneck_separation_v1/reviews/persistent_storage_delivery.json) · [最终交付](../entry_method_exploration/20261101_residual_bottleneck_separation_v1/delivery_validation.json)。
