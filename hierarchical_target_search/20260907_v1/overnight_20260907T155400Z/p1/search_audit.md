# P1 区域搜索合成正确性审计

状态：**SYNTHETIC_SEARCH_PASS**。本审计发现并修复距离相同时的结果 ID 不一致；最终 11 组检查及 ASan/UBSan 均通过。未读取真实数据，不能将此结论写成整个 P1 gate 或方法性能通过。

## 修改与失败证据

- `ACSG/RegionalSearch.h` 原来的全局结果按 `(distance, id)` 排序，候选池和 legacy 则对相同距离保持发现顺序。原套件只覆盖互异距离而通过；增加 ties 后第 400 个 trial 立即失败，距离值相同但返回 ID 不同。改为全局结果按距离稳定插入，保持两种池的相同结果收集规则；800 个 ties 查询回归通过。原失败完整保存在 [synthetic_ties_before_20260907T1559.stderr](synthetic_ties_before_20260907T1559.stderr)。
- 不足 K 的输出距离由 infinity 改成 legacy 的 `maxfloat`；新增无边图上的 IDs、distances、NDC 逐项一致检查。
- 补充非法 region count、空 region map、weight 总和溢出、非有限搜索距离、shared seed、图尺寸和空输出指针拒绝；reserve 容量计算先转 `size_t`。搜索函数签名和 GT 隔离不变。
- `benches/test_regional_search.cpp` 扩展语义测试，不改原 `ACSG.cpp`、Fast 默认路径、CMake、数据或历史产物。
- 独立 sanitizer 编译首次缺少 `-Ibenches` 而失败，已保留 [编译日志](sanitizer_build.log)；补回已有 target 的 include 目录后编译和运行通过。这是命令配置问题，不是方法失败。

## 实际测试

权威机器结果为 [synthetic_final.stdout](synthetic_final.stdout)、[search_audit.json](search_audit.json)。随机种子固定为 `2026090711`。

| 检查 | 实际覆盖 | 结果 |
| --- | --- | --- |
| 同入口 legacy / 统一池 parity | 1,200 个随机图查询；400 互异距离、800 有 ties；IDs、distances、NDC 一致 | PASS |
| count / plain、单区域退化 | 上述 1,200 查询 | PASS |
| 候选保护桥接、跨区域边、空区域 | 同一合成图与入口，统一池不扩展桥接点，区域池访问到目标；NDC 分别 42 / 43 | PASS，仅合成机制检查 |
| trace 独立重放 | 验证发现、入池、拒绝、淘汰、扩展、容量、终止和四类汇总计数 | PASS |
| 重复入口、共享 visited、epoch wrap | 520 次重复搜索，IDs/NDC 稳定，每节点只计算一次；工作区存储地址不变 | PASS |
| 容量与非法输入 | L=21..128，均匀与概率分配；区域至少 4 槽，总和严格等于 L；区域 ID 决定最大余数 ties；K>L 等边界拒绝 | PASS |
| 全局 top-K 公平性 | 部分 top-K 节点被区域候选池拒绝，仍进入独立结果池；与统一池返回一致 | PASS |
| HNSW top-m 实际消费 | 内存 HNSW，m=3/4/6/8/18；maxheap 反转为 best-first；逐入口 ID 顺序及实际距离调用数一致，重复入口只消费一次 | PASS |
| 不足 K | 无边图 top-3 输入，legacy 与新路径的 IDs/distances/NDC 一致 | PASS |
| 随机多区域 trace | 300 查询，1–4 激活区域、随机容量/图/有 ties 距离、均匀或概率容量；43,595 个事件独立重建；count/plain 一致 | PASS |
| 最小容量 | 单节点、零出度、K=L=1 | PASS |

合成保护桥接图只确认代码能表达预定机制，不证明真实数据收益。独立重放按所有 discover 事件稳定排序重建全局 top-K，GT 没有进入搜索 API 或这些测试。

## 工具、时间与资源

使用原 CPU 构建 target，`cmake --build build --target test_regional_search -j 4`；所有运行和编译都有 `timeout 120s`。最终普通测试于实际 UTC **2026-09-07 16:02:58** 运行，耗时约 **0.040 秒**。独立 ASan/UBSan 二进制于 **16:04:38** 运行，耗时约 **0.165 秒**，退出码 0，stderr 为空。时间仅为测试执行耗时，不是 ANN QPS 或训练成本。

精确命令、起止时间、退出码见 [verification_runs.json](verification_runs.json)、[sanitizer_build_retry.json](sanitizer_build_retry.json)、[sanitizer_runs.json](sanitizer_runs.json)。部分早期文件名末尾是手写标签，**不能当作实际执行时刻**；采用这些运行记录与 [source_and_log_manifest.json](source_and_log_manifest.json) 中的文件 mtime。Sanitizer 只重编译新 header 和测试单元，复用未重新插桩的旧静态库；不能外推为整库内存审计通过。

所有测试为 CPU 内存中的小合成数据；没有真实 base/GT/冻结图读写，没有长驻研究进程，没有删除文件。修改前源码由主任务保存在 `../source_before`；当前源码和正常二进制 checksum 在 `search_audit.json`。

## 尚未通过的完整 P1 条件

1. 双数据集真实 distance kernel 上的同入口 legacy / 统一池 IDs、distances、NDC parity。
2. 新 evaluator 的真实路由 count/plain IDs 一致、HNSW 实際 top-m 数量/顺序/去重与公平初始化。
3. 纯 wall timer 实证和源码审计：计时前创建工作区/输出，计时内必要归一化/路由/重置/搜索/结果写入，计时外 GT/trace/hash/JSON。
4. 主任务同步 `spec.md`、`summary.md` 和阶段台账后，结合其他 P1 证据决策。

做旧 top-3 parity 时使用相同三个有序入口并令 `shared_seed=-1`；正式统一池/区域池对照必须双方同样加入 default shared seed，且同样保留 paired Fast 首入口。不能把初始化差异算作队列机制收益。
