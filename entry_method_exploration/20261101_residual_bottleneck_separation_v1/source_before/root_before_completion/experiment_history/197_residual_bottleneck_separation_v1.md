# E197 候选支持、可预测性与执行方式分离

2026-11-01用户授权“更正主线然后继续实验”。当前实施中，尚无正式结论。主线由预设学习强入口更正为定位候选支持、可预测性和执行路径/时机，再按实际证据决定投入；离线训练费用不作当前排除条件，完整单线程Recall–QPS仍是最终指标。

[协议](../entry_method_exploration/20261101_residual_bottleneck_separation_v1/protocol.md)、[状态](../entry_method_exploration/20261101_residual_bottleneck_separation_v1/state.json)、[角色冻结](../entry_method_exploration/20261101_residual_bottleneck_separation_v1/role_freeze.json)、[代码](../entry_method_exploration/20261101_residual_bottleneck_separation_v1/src/benchmark.cpp)。

七集原图/metric/GT10不改，独立前8K Q8-B32、后8K中2048 fit/1024 cal；新标签K1/K100、L200、全C单seed384。对比原辅助队列、允许未选C作为中间点、允许已主评分未展开中间点，以及只用预先可用信息的提前入口。固定模型/拒绝与完整16K表迁移另列，费用邻近强GT10/OPT-B32以cal完整wall提出预算并事前冻结。教师选择显式不可部署。

已完成七集原生资格：1344捕获/原核字节对齐、6074996缓存评分词核对、8064辅助动作线性合并。七集真实标签/模型均完成，正在核验模型与正常运行各分支；资格不作为新性能证据。两次启动/编译问题及修正保留实际失败收据，不清零费用，不回写旧科学产物。

正式A/B继承E195曝光窗口，非新盲确认；真实K1/K100、CPU15、T1、完整wall。原E195/E196/学习设计封存保留，根文档用本轮source_before桥接。无新PDF，默认E99保持。全部结果与费用待固定矩阵/复算/报告完成后据实际证据补齐。
