# ACSG 长期研究计划：目标邻域驱动的分层搜索

> 2026-09-07；版本 `hierarchical_target_search/20260907_v1`。用户已授权按本计划实现、实验和证据 gate 自动推进。约 8–10 周为优先级参考；阶段由证据决定。实现契约见 spec.md，研究判断见 summary.md。

## 1. 目标、范围与状态

目标是形成有明确机制贡献、可复现性能提升和完整实验论证的新方法。Fast v1 保留为可靠基线，主线联合设计目标区域、查询到区域的映射，以及区域在图搜索中的候选保留机制。负结果关闭分支，不代表整个研究目标完成。

- 先在冻结 NSG 上研究；证据指向连接瓶颈后才进入独立辅助图分支。
- WebVid-2.5M 和 Yandex official 10M/IP 都须稳定改善：同 Recall 提升 QPS，或同 QPS 提升 Recall。LAION 只作跨 base corpus/scale 迁移。
- 当前研究执行已获用户明确恢复授权：`P2_REVIEW`；P0/P1 已通过，P2初测有负结果及oracle潜力，机制gate尚在审查。依赖已就绪，见 `hierarchical_target_search/20260907_v1/dependencies/README.md` 和 `manifest.json`；机器台账为版本目录 `state.json`。

历史：旧 Multi-view 在原协议下终止为 `NO_GO_ROUTING_COST`，E2–E4 按 gate 未运行；旧实现、结果及停止结论保留在[历史报告](target_basin_formalization/20260907_v1/report.md)，不补跑旧阶段。

## 2. 方法设计与实现边界

### 2.1 目标区域与门户

每个 base 节点都有区域编号；区域标注不限制跨区域访问，搜索边仍取原 NSG。初始化采用 [METIS v5.2.1](https://github.com/KarypisLab/METIS/tags)，64 位索引；仅为分区构造对称化邻接。

完整版本固定 **16 粗区域 ×16 细区域**。目标：
`J(Π)=CutFraction_G(Π) + λ mean_q((distinct_regions(GT10(q))-1)/9)`。
各层大小上限为该层平均大小的 1.2 倍；λ=1，λ=0 为消融。初始化后两轮确定性局部移动，只接受满足容量且降低 J 的移动。必须覆盖未出现于训练 GT 的节点。

门户是真实 base 节点。完整版本每细区域 2–4 个，总数不超过 WebVid 815、Yandex 821。每区最多 8 个候选、128 条拟合查询；离线 K=10,L=32 固定搜索，按目标覆盖增量选择。这是离线代理，不保证在线共享搜索最优。

### 2.2 层次化目标预测

标签 `y_r(q)=|GT10(q)∩V_r|/10`。粗区域概率乘区域内条件概率得到细区域概率。初版线性 softmax、交叉熵、L2=1e-4、CPU L-BFGS 最多 100 次迭代。查询归一化只用于路由；原 base、搜索 query、GT、raw-IP 契约不变。

最多展开 4 个粗区域，激活细区域数 {2,4}。学习目标分布，不预测逐入口 Recall/NDC utility。先测真实区域占比 oracle，分开诊断结构、门户和预测损失。

### 2.3 区域候选保留

总候选容量严格为 `L_shared + sum(L_r) = L_total`。共享队列占 25%，其余按区域概率分配；每激活区域至少 4 槽，余数采用最大余数法、区域 ID 破同分。单次查询容量固定，不使用动态扩容或失败预测。

所有队列共享 visited、距离计算与全局 top-K 结果；每节点每查询最多计算一次真实距离。激活区域内节点进入其区域队列，其余进入共享队列，跨区域边照常访问。保留 paired Fast 首入口，以图默认入口初始化共享通道；重复 ID 去重。队内按真实距离排序，队间加权轮转。所有保留候选扩展后终止；L 是容量，不是 NDC/扩展上限。

统一池对照也采用独立全局 top-K，避免结果收集差异混入机制收益。图默认入口强制归共享通道作为种子例外；重复入口只按第一次归属保留。

### 2.4 接口与隔离

- 路由：query＋model → 区域、权重、入口、provenance，无 GT。
- 搜索：query＋冻结图＋route＋workspace → top-K，无 GT。
- GT 在评测层事后评分；oracle 独立 train-only 适配，不能进入正式方法/held-out。
- runner 显式要求 stage、split、measurement、output，拒绝覆盖和跳过上游 gate。
- 旧 Fast 默认路径不变；新 top-m 对照消费全部入口、纠正 HNSW 返回顺序，并记录实际入口数。

## 3. 分阶段路线

| 阶段 | 时间参考 | 必须产物 | 下一阶段条件 |
| --- | --- | --- | --- |
| P0 证据与协议 | 第1周前半 | checksum、split、源码快照、现有逐查询诊断、协议台账 | 输入正确，探索与正式证据分离 |
| P1 搜索与测量 | 第1周后半 | 纯计时、独立计数、统一池、区域池、候选 trace | 正确性与测量测试全部通过 |
| P2 机制证伪 | 第2周 | 固定区域/门户/路由的队列对照 | 可重复机制收益，或 oracle 潜力及可定位瓶颈 |
| P3 结构与门户 | 第3周 | 图＋GT 共现分区、门户、结构报告、离线成本 | 优于仅图分区，收益传递到搜索 |
| P4 层次预测 | 第4周 | 线性模型、oracle 差距、推理成本 | 真实预测保留收益且成本可接受 |
| P5 端到端 | 第5周 | 完整曲线、Fast top-m、方法冻结清单 | 双数据集达到实质性能门槛 |
| P6 稳定性归因 | 第6–7周 | validation 三构建、消融、强基线、tail、完整成本 | 稳定改善且关键机制有因果对照 |
| P7 冻结复验 | 第8周 | held-out 10K×3 timing、LAION、成功/失败报告 | 复现主要结论，否则收窄/撤销 claim |
| P8 论文复现 | 第9–10周 | 方法、机制、图表、限制、复现入口 | 每项 claim 对应有效证据 |

**先完成 P2，不能提前搭完整学习系统。** P2 固定 64 个仅图结构区域、区域查询画像、每区 2 门户、激活 4 区域。五项对照：

1. 几何路由＋统一池；
2. 相同路由＋区域池、均匀容量；
3. 相同路由＋区域池、预测占比容量；
4. GT 区域占比 oracle＋统一池；
5. 相同 oracle＋区域池。

真实路由计全部成本；oracle 单列，不贡献部署 Pareto 点。oracle 有效才诊断预测/门户；oracle 也无收益则停止当前配置，不立即增加模型。

P6 必要消融：去候选保护、去 GT 共现、均匀容量、平面预测、相同入口数 Fast top-m、相同预算几何门户。强基线优先 [GATE](https://arxiv.org/html/2506.15986v1)、[LIRA](https://arxiv.org/html/2503.23409v1)、[kRt](https://www.vldb.org/pvldb/vol18/p1649-gottesbueren.pdf)；原方法与受约束适配分别标注。[RoarGraph](https://arxiv.org/html/2408.08933v1) 属于改图系统比较，不混入同图归因。

## 4. 数据、测量与验收

### 4.1 Split 与矩阵

复用独立 QGT 5K。`router_train[10000:30000)` 20K 拟合区域/门户/路由；`[0:10000)` 为已有历史使用的开发 pilot。paired Fast 同样只用 20K 拟合；旧 30K Fast 单列较强参考。允许复用独立 QGT raw hubs，禁止复用含 pilot 标签的旧 30K prototypes 作为新模型输入。

validation 为独立 10K；held-out 仅 P6 通过、方法冻结后执行。P2 K=10,L={64,128}；P5 扫 {32,48,64,96,128,192,256}。Fast m={3,4,6,8} 必须实测入口数、顺序和去重。K=100 仅 L≥100。

### 4.2 纯计时

旧 evaluator 整批计时含 GT 评分，不能发布新 QPS。P1 新路径预分配线程工作区/结果缓冲；计入 query 归一化、路由、调度、去重、搜索、必要状态重置、结果写入；GT 评分、trace、hash、JSON 在计时外。

主指标为同机/同图/同线程单方法整批 wall QPS。固定 warm-up 和预记录 AB/BA 配对顺序；pilot/validation 每点 5 rounds，held-out 每构建每点 3 runs。三独立 build seeds 与 timing rounds 分开，不把 timing 当 Recall 样本。分列 routing/graph/total NDC、模型 MAC、routing wall、batch wall、峰值 RAM、索引大小。NDC 解释成本，不设 equal-NDC 硬 gate。

paired Fast L=64/96/128 定义三个工作点；匹配只用实测点，插值仅绘图。bootstrap 内重新做成本匹配与最佳可行点选择，不在挑点后固定该点计算 CI。

### 4.3 实质门槛

P5 开发筛查，P6/P7 确认结论。每数据集至少两个相邻工作点满足同一种门槛：

- 匹配 Recall，平均 QPS ≥+10%，校正 CI 支持正收益；或
- 匹配 QPS，平均 Recall@10 ≥+1 pp，校正 CI 支持正收益。

两个数据集可走不同门槛，逐一报告。预注册比较族 2 datasets×3 anchors×2 families=12，10,000 次配对 bootstrap，Bonferroni 整体错误率目标 .05，同时给普通 95% 与校正 CI。三个构建分别报告，不以均值掩盖单构建退化。

其他预定点检查同 Recall QPS 下降 >3%、同 QPS Recall 下降 >0.2 pp；确认退化则限定有效区间。测量/预算不能区分写 INCONCLUSIVE。

### 4.4 必要正确性、机制与成本

P1 必测：同入口统一池与旧实现 parity；单区域退化；重复入口、空区域、非法编号、容量边界；visited/距离计数共享、跨区域边；count/plain IDs 相同；真实方法无 GT 输入；拒绝 K>L；重复稳定；trace 重建发现/入池/淘汰/扩展，GT 事后关联。

最终报告阈值 .1/.2/.5/.8 的 rescued/newly_harmed、低尾、独立 1-thread p50/p95/p99。完整离线成本 `T_exactGT+T_partition+T_portal+T_router`，分从零与复用 GT 两情景；缺失项 null＋原因。[Adaptive Beam Search](https://arxiv.org/html/2505.15636v1) 等依赖 metric-space 的理论不能直接用于 raw IP。

## 5. 失败后的确定动作

| 证据 | 下一步 |
| --- | --- |
| 正确性/计时失败 | 修实现/测量，同协议重跑，不判算法失败 |
| oracle 有效、预测无效 | 分解预测/门户；最多一次表示或划分修订 |
| 统一池/区域池近似等效 | 检查竞争 trace；无支持则关闭保护分支 |
| 路由成本抵消 Recall | 一次保持语义的实现优化；仍失败则否决在线实现 |
| 仅一个数据集有效 | 检查适用条件，不挑数据集宣称通用性 |
| 正确区域/门户仍有连接瓶颈 | 独立稀疏门户辅助图分支 |
| validation/held-out 失败 | 负结果并冻结版本，不用 held-out 调参 |

辅助图保留原 NSG 文件，单独存门户附加邻接；每门户最多 4 出边，候选来自训练 GT 共现和实际搜索。对照无边、等边数几何边、目标驱动边，支付额外距离/空间；重新 P1–P7，不能继承冻结图 GO，不能声称未改变搜索图。

每版本最多两次有新证据的机制修订。统计不显著不自动重跑；加参数、seed、阈值不算新进展。

## 6. 持续接续、资源与完成定义

每次接续：读阶段/gate/下一行动/阻塞；核实活进程、输入、代码，不凭旧日志重启；完成有产物和验收的任务单元；保存证据更新 gate；通过自动下一阶段，失败依表分流；报告发现、阶段、下一步与实测吞吐 ETA。

每周复盘排除/支持了什么、是否继续、下一周唯一最高优先项；已有投入不降低门槛。

版本目录至少包含 protocol、manifest、regions、models、count、timing、traces、gates、report、state。台账记录阶段状态、版本假设、证据、具体下一行动、PID/日志/ETA、阻塞及解除条件。

重任务前复查资源。16 vCPU、约 123 GiB RAM，初始 /data 余约 21 GiB；仅一个重数据集进程，保留 ≥10 GiB 空闲，首轮 artifact ≤8 GiB。紧凑区域编号，trace 只录预选小样本，不复制 base/冻结图。长任务独立日志并观察约一分钟估 ETA。

三个交接文件保持当前状态与必要契约；长日志、失败历史和逐查询表在 artifact。完成须有可复现实现、双数据集稳定提升、关键消融、适当强基线、完整成本、冻结测试和逐条有证据的论文主张。程序退出或 pilot 通过不等于完成，不能保证投稿接受。

## 7. 当前执行台账

| 项目 | 当前值 |
| --- | --- |
| 阶段 | P2_REVIEW；初测完成，gate待诊断 |
| 已完成 | P0输入审计；P1搜索/计时验收；两数据集P2 count、5轮wall、16查询trace |
| 证据 | 本轮 gates/P0.json、P1.json；p2/analysis_v1/；control/jobs/ |
| 下一行动 | 重建竞争轨迹及绝对区域预测质量，按P2 gate分流 |
| 活跃重任务 | p2_trace_analysis_v1；实时状态见 control/watchdog_status.json |
| 阻塞 | 无外部阻塞；P3须先通过P2证据gate |
| P3–P8 | NOT_STARTED；validation/held-out未读 |

夜间接续提示词已保存到版本目录 `overnight_prompt.md`。用户指定新对话的方法开发和实验截止于北京时间 2026-09-08 07:00（UTC 2026-09-07 23:00）；本次已建立仅作用于注册任务的截止保护，控制台账见下方。07:00 停止研究任务后，整理既有证据并生成 `/data/netg/ACSG/实验总结.md`：标题后第一段简洁概括整晚成果，后文详细报告实现、实验结果、gate、证据、资源与下一步。若该路径已有历史文档，保留原文件，在新时间戳 artifact 子目录保存同名文档并报告路径；报告整理不作为截止后继续实验的理由。

### 本次夜间接续（更新于北京时间 2026-09-08 00:45）

本轮产物位于 `hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/`。用户已恢复全 CPU 自主研究授权；`control/taskctl.py` 保存独立进程组、命令、启动身份、日志、超时和资源，watchdog 于06:59关闭研究任务、07:00硬截止，随后仅整理报告。所有原有产物保留；旧 Fast 默认源码未改。

P0/P1 已 PASS：完整输入 SHA、split 隔离、图内 base 抽样核对；搜索合成和 sanitizer、两数据集512 pilot查询×L64/128的结果/NDC/新纯wall一致性、m4/6/8实际入口消费均通过。新 evaluator 使用配对20K Fast、纠正 HNSW入口顺序；同入口搜索核与legacy parity不等于旧端到端Fast入口顺序相同。

P2 两数据集10K development pilot已完成独立count、5轮纯wall、预选0..15查询trace（注册23条中只运行16条子集）。64图区域满足严格1.2容量，2门户/区和区域画像仅用20K fit。METIS内部额外容差曾令WebVid12区各超2节点；保留失败产物，补偿库内容差后硬上限通过，未放宽门槛。分区时间27.78/171.64秒，不含exactGT。

真实预测下，区域概率池相对同路由统一池在WebVid L64/128退化5.431/3.640 pp、Yandex退化6.867/3.488 pp，且更慢。oracle同路由区域池分别提高5.413/5.252 pp与3.155/3.359 pp，但仍付出额外wall和NDC。所有真实方法在当前两点均被paired Fast支配，**当前没有有效端到端性能改善证据**。证据为 `p2/analysis_v1/{analysis.json,report.md}`；10K配对bootstrap区间是探索性普通95%，5轮计时不是5个独立Recall样本。

当前 `P2_REVIEW`：轨迹竞争重建与区域预测缺口诊断正在补齐。P2 gate尚未通过，P3–P8未开始；validation/held-out未读取，未触发辅助图。下一行动是完成两项诊断后按原机制gate作决定，不能用oracle优势替代部署性能门槛。更详细的失败历史、命令和阶段状态见本轮 `ledger.md`、`control/jobs/` 与版本 `state.json`。
