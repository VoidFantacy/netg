# P2 冻结图分区工具

`partition_graph.cpp` 独立运行，保持原 directed NSG 不变。真实数据运行前内部核验 `P1 PASS`、P0 输入审计及已接受的 P2 协议。只用 `O_RDONLY` 映射原索引中的邻接段；过滤 padding 与自环，数组化 count/prefix/fill，逐行排序去重并原地压紧，构造临时对称 CSR。CSR 不写磁盘，不复制 base/索引。

METIS 为既有 v5.2.1、64 位 idx_t，k-way64，seed2026090711、UFACTOR200、NCUTS1、NITER10、NUMBERING0。严格容量使用整数 `floor(6*N/(5*parts))`。v3 对 `options.c:121` 无条件增加的 `0.0000499` 进行固定 ubvec 补偿：输入 `1.199949860572815`，内部有效值 `1.1999998092651367`，保留原 1.2 上限；这是依赖契约适配，不是性能调参。原始参数运行的容量失败及诊断 labels 由 root 单列保存，不接受越界分区。

仅 sort/unique 使用指定 OpenMP 线程；METIS 本身单线程 CPU。输出 `regions.u16` 为无 header 的 little-endian uint16 区域编号，每 base 节点一项。`manifest.json` 成功状态为 `COMPLETE`，记录输入 graph path/当前 P0 SHA256、所有节点覆盖、区域大小/1.2容量、独立复算 edgecut、阶段成本、峰值 RSS、label SHA256。容量/空区失败先保存 labels、所有 sizes、违规区和实际 ubfactor，再以 `FAILED_STRUCTURE_GATE` 和 return3 拒绝使用。

任何 TERM/异常/截止均保留 `INCOMPLETE` manifest；METIS 库调用期间由统一 supervisor 的 TERM/KILL 截止保护。需要从已有 stage checkpoint 判断是否可恢复，不能把 PARTITION COMPLETE 当作 P2 性能通过。

构建（项目根目录）：

```bash
g++ -O3 -std=c++17 -fopenmp -Wall -Wextra \
  -I hierarchical_target_search/20260907_v1/tools/local/include \
  -I build/_deps/json-src/single_include \
  hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/partition_graph.cpp \
  -L hierarchical_target_search/20260907_v1/tools/local/lib \
  -Wl,-rpath,/data/netg/ACSG/hierarchical_target_search/20260907_v1/tools/local/lib \
  -lmetis -lGKlib -lm \
  -o hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/partition_graph
```

先运行 `--help`。真实入口由 root 统一 stage/controller 调度，不能同时运行其他重数据集进程：

```bash
hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/partition_graph \
  --graph /data/netg/ACSG/indices/webvid2_5m_light_v1_index/acosp_nsg.json \
  --dataset webvid2_5m_light_v1 \
  --audit hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p0/full_audit/audit.json \
  --gate hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/gates/P1.json \
  --protocol hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/protocol.json \
  --output NEW_PARTITION_DIRECTORY --threads 16
```

`NEW_PARTITION_DIRECTORY` 必须不存在且父目录已存在。Yandex 只替换 dataset 与对应 graph 路径；不要重新拷贝原图。主 agent 负责重任务前资源核验和实际分钟进度/ETA。

已完成的局部验证：

- [synthetic_test_v1/manifest.json](synthetic_test_v1/manifest.json)：6、24、97 节点，精确 set 对照验证 CSR 对称、去重、无自环、padding 去除；非法邻居拒绝；METIS 标签覆盖、非空区、容量、edgecut 校验均通过，不要求特定标签编号。
- [partition_io_test.json](partition_io_test.json)：1735 字节人工 native-v1 索引，验证不对齐邻接 offset143 的只读 mmap 和 CSR。生产读取使用 memcpy，避免直接解引用不对齐 int32_t 的未定义行为。
- 同一 I/O 测试对 0、3、55、56、63、64、65、127、128、129、1000、65536 字节的 SHA256 与 Python hashlib 比较全部一致，覆盖 padding 边界和多 block。
- [partition_build.json](partition_build.json) 保存初版；[partition_build_v2.json](partition_build_v2.json) 保存失败诊断持久化与严格整数上限修复；[partition_build_v3.json](partition_build_v3.json) 保存固定 METIS epsilon 补偿、源码/二进制 SHA256 与新增有效上限测试。均无新增依赖、无编译 warning，旧源码/二进制有独立快照。
- [capacity_failure_persistence_test.json](capacity_failure_persistence_test.json)：人工 6 节点/5 区域故意不能满足上限，确认失败 return3、实际 sizes/empty/violations、完整 labels 及 SHA256 全部保存。fixture 入口的初次参数漏填按预期被协议核验拒绝，纠正 fixture 参数后测试通过，原日志保留。

本节验证由分区实现 agent 在合成数据上完成；真实数据实验统一由 root 控制器调度，状态与证据见相应目录和 gate，不能把这些合成检查当作 P2 性能通过。
