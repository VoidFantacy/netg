# P2 预选 trace 分析接口

`analyze_traces.py` 只重放既有 evaluator trace，不运行 ANN、训练、分区或 bootstrap。它生成逐查询候选竞争证据，不自动决定 P2 gate，也不把 oracle 或预选小样本写成部署性能。

## 调用

从 `/data/netg/ACSG` 执行。下面仅为可复现命令；实际运行由主任务串行调度：

```bash
TRACE_RUN=hierarchical_target_search/20260907_v1/overnight_20260907T155400Z
.venv_cpu/bin/python "$TRACE_RUN/p2/analyze_traces.py" \
  --protocol "$TRACE_RUN/protocol.json" \
  --inputs "$TRACE_RUN/p2/webvid_eval/trace.json" "$TRACE_RUN/p2/yandex_eval/trace.json" \
  --model "$TRACE_RUN/p2/webvid_model/model.json" \
  --model "$TRACE_RUN/p2/yandex_model/model.json" \
  --output "$TRACE_RUN/p2/trace_analysis_v1"
```

`--inputs` 接受 evaluator 最终 trace JSON、单个完成的 batch JSON，或 `.parts` 目录。`.parts` 只读取已保存的完整 batch；缺失单元和未配对 query IDs 单独报告。相对 `parts_directory` 按 evaluator 工作目录 `/data/netg/ACSG` 解释。若移动了历史文件，可直接传当前 `.parts` 目录。

`--model` 可重复传入不同数据集的 model JSON。工具通过只读 mmap 对 trace 中实际出现的节点/parent 查询 uint16 区域文件；不读 base、GT 或图。完整标签 checksum 继承已经校验的 model manifest，并记录此次实际观察的 `(node ID, region)` 对的 checksum。没有提供 model 时，跨区域统计明确为 `NOT_AVAILABLE`，不会把 queue 0 当作真实 region 0。

输出目录必须不存在。中断/错误保留 `started.json` 与 `failure.json`，成功输出 `report.json`、`report.md`；不覆盖旧产物。

## 验证与统计

- 只接受 P2、CPU、无 held-out 访问、pilot 的独立 trace，K=10、L∈{64,128}，query IDs 必须在 protocol 的预选列表中。
- 逐事件独立验证 visited/NDC、固定容量、队列排序、加权轮转、当前扩展 parent、种子顺序和 `discover → [evict] → accept/reject`。evict 的 parent 字段是替换它的 incoming candidate，与 discover 的图 parent 分开保存。
- 用所有 discover 事件按真实距离稳定排序，独立重建全局 top-K；候选队列拒绝不等于结果丢失。利用计时外附加的 GT flags 重建 Recall，与 aligned row 对照。
- 配对比较为 `geom_unified` 对 `geom_uniform/geom_probability`，以及 `oracle_unified` 对 `oracle_probability`。要求实际 seeds、顺序、默认入口、Fast anchor、激活区域和权重完全一致；否则失败。
- 记录 GT 的发现、接受、拒绝、扩展前淘汰、扩展后淘汰、扩展和返回；同时记录所有节点的状态转移、额外扩展、未扩展淘汰及被谁替换。
- 对新增/丢失的 GT 结果对称追溯首次发现路径。一个保留路径 witness 必须是**非终点祖先**：当前方法实际扩展了它，配对方法拒绝它或在扩展前淘汰它。它可以是非 GT 节点；不把 GT 标签本身当作“桥”。证据只说明观察到的路径，不证明该节点必要、唯一或排除其他未观察路径。
- 跨区域计数只覆盖首次发现边；重复/已 visited 的邻接访问没有 trace，因此不声称是全部跨区边访问量。
- 阈值 `0.1/0.2/0.5/0.8` 的失败定义是 `Recall@10 < threshold`，与既有 ACSG tail 汇总一致。rescued/newly_harmed 只对实际同 query 配对计算。

`selection_coverage` 明确只是观察单元的 query-ID 并集。`registered_matrix_coverage` 另列完整 **2 datasets × 2 L × 3 comparisons** 的单元覆盖、各单元实际 query IDs、缺失数据集/工作点、未配对查询和未观察的预选 IDs。仅运行 `0..15` 时必须报告为部分预选集合，不称完整 trace 矩阵或总体结论。

## 实现验证

最终源码 SHA256：`86cd04bef327ed7d35c072f1f59562487aa9dd595eeff5e668f02c9dc9d0bdd3`。

`--self-test` 使用手写 golden traces，覆盖非 GT 保留路径、共享池/区域池的容量和调度、两类淘汰、图 parent 与替换节点、全局 top-K、坏 trace/不同 route 拒绝、最终 JSON/parts 输入、相对路径、缺失整个数据集/工作点以及文件保护。最终结果见 `trace_analyzer_selftest_v5.{json,stdout,stderr}`：实际 UTC 2026-09-07 16:39:12，约 0.037 秒，退出码 0。

首轮独立 review 见 `trace_analysis_review_v1.md`。v3 在增强事件语法时发现 scheduler 局部变量误覆盖 admission 状态，失败日志保留；改名隔离后 v4/v5 均通过。这里只验收分析器实现，尚未包含实际 P2 trace 分析结果。
