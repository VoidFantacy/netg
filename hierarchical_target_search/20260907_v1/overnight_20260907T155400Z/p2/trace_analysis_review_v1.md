# Trace 分析工具独立复核（首轮）

复核对象：`analyze_traces.py`。独立 reviewer 为 `p1_evaluator`；只读审计，没有运行真实数据或 CPU 测试。现版内存 golden trace、输入适配和输出保护自测已通过，证据为 `trace_analyzer_selftest_v2.{json,stdout,stderr}`。

## 必须补齐

1. evaluator 保存相对 `parts_directory` 时，其基准是工作目录 `/data/netg/ACSG`，不是最终 JSON 的父目录。当前解析会重复拼接路径；父任务当前使用绝对输出不触发，但分析接口应正确支持相对输出。
2. 当前 query-ID 并集的 `FULL_REGISTERED_LIST` 仅表示已观察单元的 ID 并集齐全。需要另列预注册 `2 datasets × 2 L × 3 comparisons` 的完整矩阵、缺失单元及每单元 query-ID 覆盖，不能把缺失整个数据集或工作点隐藏在并集之中。

## 增强独立重放完整性

- eviction 的 replacing candidate 必须属于同一队列，且对应下一次 accept；不能仅凭其距离更优就解释淘汰。
- 非种子 discover 的 parent 必须等于当前正在扩展的节点，种子必须在首次 expand 前出现。维护 pending admission，验证 `discover → [evict] → accept/reject` 的顺序；这样用于路径证据的父链由事件顺序独立约束。
- 加入 `cpu_only=true` 与 `heldout_accessed=false` 的输入契约断言。

父任务正在进行五轮 wall 计时，目前按要求暂停代码修改与测试，仅保留这份审计记录。修复与新的自测完成前，不将本文件当作最终工具验收。

复核认可的解释边界：同 route 比较、候选队列拒绝与全局 top-K 分离、GT 各阶段重建、非 GT 中间祖先的保留路径证据、首次发现边上的跨区域计数，以及对部分预选样本不作总体性能或因果必要性推断。
