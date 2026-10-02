# 访问范围的最终审查更正

E32没有把validation query/GT用于训练、模型选择或新的检索评测；开发门失败后没有运行validation/QPS。**但不能据此写成“validation文件从未读取或hash”。**

本轮preflight和最终旧产物保护校验继承了E31的完整保护链，逐文件计算SHA256。该链包含E23/E24的两套数据、各三个历史validation文件：queries.f32、gt.i64、row_ids.i64，共12个唯一文件。SHA256读取了文件字节，没有将它们解码为query/GT/row数组，也没有进入本轮梯度、β计算、checkpoint选择、cal/audit判断或新validation搜索。完整路径与保护身份见[访问记录](reviews/access_scope.json)。held-out没有被读取或hash。

原协议同时要求旧链完整身份保护和按阶段隔离实验读取，未明确区分保护性hash与实验数据读取；早期报告“新validation输入未读/hash”和计划元数据`validation_access=false`的表述过宽。最终报告、summary、历史21及spec已更正，并将访问拆为“字节hash、数组解码、训练/选择使用、评测使用”分别记录。此更正披露已经发生的保护性I/O，不追溯修改训练/评测规则或把额外实验授权写回原协议。

修改前文件、首次结构审计及修改前后身份保存在[更正记录](reviews/access_scope_correction/corrections.json)。原模型、全部原始结果、收益门、图、Excel均未改变；最终审计核对原冻结文件对应的修改前副本以及更正后的当前文件。停止原因仍为WebVid cal未胜默认，完整性能尚未测试。
