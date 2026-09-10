# P2 原注册 trace 补全独立审查

**源码和小合成检查通过。** 仅补原23条中未执行的7条查询，固定5方法×2L×2数据集，共140条；完成后须由冻结 analyzer 将全部460条重新 replay，不能由本 runner 的退出状态替代该验收。

已关闭启动前发现的 provenance 缺口：DataLoader 隐式 settings 与 P0 SHA 对齐，模型/Fast绑定同一 P0，原命令 index 路径与 P0 对齐；每个子任务前重核 settings、审计、runner、冻结 evaluator、模型和 Fast 文件。

命令仅改 query offset、查询数、warm-up数、输出路径；新记录必须逐字段等于原完整10K的同一 query/方法/L 行。10项微型命令和SHA校验通过，没有运行ANN或读取真实GT/标签/完整count行。P3 NOPASS保持不变，不产生新的性能/CI/模型选择。

源码 SHA：`a0c31bcc91e78efc754ec89f6c84ea8a0a904ac8f91e6eeb6f3928b486fd4cc2`。完整证据见 [JSON](trace_completion_independent_review_v1.json)。
