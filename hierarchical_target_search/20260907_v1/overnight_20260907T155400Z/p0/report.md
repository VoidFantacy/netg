# P0 输入与协议审计

输入证据检查通过，root 已于 UTC 2026-09-07 16:05:27 接受并冻结最终协议，正式 gate 为 [P0 PASS](../gates/P0.json)。此次结果只证明输入、隔离与历史证据可追溯，不证明区域搜索正确或具有性能收益。没有运行 validation/held-out 性能，也没有打开 held-out query/GT 文件。

## 输入核验

| 项目 | WebVid | Yandex |
| --- | ---: | ---: |
| base 规模 | 2,505,000 × 512 | 10,000,000 × 200 |
| metric / normalization | IP / source_unit_norm_no_additional | IP / none |
| 外部 base 字节 | 5,140,260,000 | 8,040,000,000 |
| 冻结索引字节 | 5,791,560,103 | 10,640,000,103 |
| 图有效边槽 | 49,612,453 | 294,844,816 |
| `-1` padding 槽 | 110,707,547 | 345,155,184 |
| 非 padding 非法邻居 | 0 | 0 |
| 原图自环 | 996 | 22 |
| raw QGT hubs / seed | 815 | 821 |
| 外部/内嵌 base 固定点字节相等 | 68 / 68 | 68 / 68 |

正式配置位于 `benches/datasets/settings.json`；数据 manifest 位于两个正式数据目录。全量 base、冻结索引、QGT、router_train、validation query/GT 的 SHA256 与既有 manifest/冻结协议相符，数据 manifest 与图 sidecar 本身也匹配旧 protocol SHA256。原 exact-IP GT 的来源通过相同 checksum 继承；本次没有重算 exact GT。

完整证据：[full_audit/audit.json](full_audit/audit.json)。全审计由 root 统一截止保护控制器串行运行，脚本记录 wall 35.2675 秒。具体进程 RSS 以 `../control` 的该任务 registry/resource 记录为准，不能把脚本 checksum 吞吐当作方法离线构建性能。

图文件虽名为 `acosp_nsg.json`，实际为 `IndexACSG` 二进制 v1，不是 JSON；sidecar 的真实名称为 `acosp_nsg.json.info`。二进制内含定宽 64 邻接、原 base 向量，以及 pheromone/weight 数组。`audit_inputs.graph_header(path)` 只 seek 读取头部和长度，可用于只读 mmap，不需要复制图。WebVid 邻接/向量 offset 为 `20040095 / 661320103`，Yandex 为 `80000095 / 2640000103`。文件总长度为 `103 + n*(8 + 64*4 + d*4)`。

自环是原图的一部分，不是越界坏边；不得据此改写 NSG。分区使用的独立对称邻接应过滤 `-1`、去自环并去重，搜索保留原 directed NSG。固定点抽查 seed 为 `2026090711`，每数据集抽 64 个随机 ID 加首/末/中点/默认入口，共 68 点，完整 ID 列表与样本哈希见 [embedded_base_sample.json](embedded_base_sample.json)。抽查只支持这些点字节一致，不声称全量向量逐字节比较。

## Split 与 Fast 配对

`router_train[0:10000)` 是历史已使用的 development pilot；`[10000:30000)` 是本次 20K fit。审计针对 QGT5K、pilot10K、fit20K、validation10K 重新计算逐 query 指纹，四组内部重复均为 0、六组两两 overlap 均为 0。fit/pilot query 值、GT 值和父 row IDs 分别记录 SHA256。held-out 隔离继承相同数据 manifest 内的零 overlap 记录；为保持 P6 访问边界，没有重新读取 held-out 内容。

允许复用 seeds `20260828/29/30` 的独立 QGT raw hubs。三个 seed 的 hub/ID checksum、唯一性和范围均通过；raw hub 向量在对应 base ID 上逐字节相等。旧 `qgt_gt_basin_prototype` 的 manifest 明确记录拟合 30K，不能作为新模型输入。

既有 `benches/run/build_fast_entry_variants.py` 的 CLI 没有 fit-range 参数，`--qgt-only` 仍默认用全部 router_train30K。paired Fast 必须使用隔离 wrapper，只将 20K fit query、相应 GT 和 GT top1 base vectors 传入同一 `build_gt_basin_prototypes` 函数，prior=1。root 新增 [build_paired_fast.py](build_paired_fast.py) 已完成静态 split 审查：query/GT 均切 `[10000:30000]` 并各自核对 P0 values SHA256，旧 prototype 不加载。该审查不替代 builder 实际完成和后续 P1/P2 评测。

## 历史逐 query 证据

[historical_diagnostics_inventory.json](historical_diagnostics_inventory.json) 索引旧 E1b 两数据集 `*_fast10k_count.json`。L=64/128 的 10K 数组均按 query IDs `0..9999` 对齐，结果 ID、入口 ID 和 routing/graph/total NDC 完整，逐 query 求均值重现旧 Recall，`total_ndc = routing_ndc + graph_ndc` 全部成立。

这些文件用于说明当前 pilot 已被历史开发使用和选择可追溯诊断入口。旧 Fast 拟合 30K，旧 evaluator 计时混入 GT 评分，因此旧 QPS 不发布，也不能把这组结果冒充新 paired20K 基线。没有基于旧结果给新方法做性能判断。

## 协议与 gate

[protocol_candidate.json](protocol_candidate.json) 保留原 P0–P8 顺序、5 组 P2 机制对照、P2 K10/L64/128、64 区域、每区 2 门户、激活 4、CPU-only、seed2026090711、几何 softmax temperature1、5 rounds 预记 AB/BA、纯 wall 与独立 count/trace、deadline 和资源边界。P2 没有新造数值通过线，按原计划要求“可重复机制收益，或 oracle 潜力且瓶颈可定位”。P5/P6 的双数据集、相邻工作点、10% QPS 或 1pp Recall 与校正区间门槛没有降低。

root 已在 [最终 protocol.json](../protocol.json) 绑定区域查询画像为归一化 fit query 按 GT10 区域占比加权均值；门户为区域内 fit GT10 频次 top2，ID 破同分，不足时取区域最小节点补足。零画像先退回归一化门户向量和，仍为零则取第0坐标单位向量。每方法/L 预热 min(128,nq) 条初始 query，具体 trace ID 列表也已冻结。只有 P1 必要正确性与计时检查通过，才能执行 P2。paired20K 完成是 P2 输入依赖，不是性能 gate。真实 oracle 只作训练诊断，不能进入部署 frontier；完整层次结构和学习系统必须等 P2 通过。

候选机器 gate [gate_candidate.json](gate_candidate.json) 保留接受前状态；当前权威状态为 [../gates/P0.json](../gates/P0.json)。源码快照 11 项内容 SHA256 均匹配 root 的 `source_before_manifest.json`；审计脚本当前 SHA256 与 full result 一致，当前原读取器、builder、settings 标识见 [source_contract_identity.json](source_contract_identity.json)。P0 没有修改旧源码、base、GT、图或历史结果，没有删除文件。

## 复现

从项目根目录，先执行脚本 `--help`。full audit 必须由本次独立控制器调度，不能与另一重数据集任务并跑，输出目录必须不存在：

```bash
.venv_cpu/bin/python hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p0/audit_inputs.py --mode full --output NEW_P0_OUTPUT
timeout --kill-after=5s 60s .venv_cpu/bin/python hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p0/check_embedded_base.py --audit NEW_P0_OUTPUT/audit.json --output NEW_SAMPLE_OUTPUT.json
```

两脚本都内置本次 UTC 2026-09-07 23:00 截止；该时间后不能为补报告再次运行。已有成功结果无需重复大 checksum。P0 的直接下游是 P1 搜索/纯计时正确性 gate；后续进展以 `../gates/` 和 root 执行台账为准。
