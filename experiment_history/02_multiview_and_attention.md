# Multi-view 与 confidence-attention 实验复盘

本页依据各阶段原 decision、protocol、report 及计时源码整理，核对日期为 2026-09-08。最终状态是 Multi-view `NO_GO_ROUTING_COST`、confidence 当前共享-alpha 公式 `no_go`；早期 GO 只代表当时同 L 的局部 gate，不能覆盖后来的正式停止。当前研究入口为 [s-target.md](../s-target.md)。

## 1. 动机、方法与输入

单 Fast 的 GT-basin 划分依赖聚类初始化。Three-view 的假设是不同 QGT 划分提供互补候选：复用 seeds 20260828/20260829/20260830 的三组 Fast hubs/prototypes；每 view 取 top-8，真实 entry ID 去重时保留最高 cosine 分数；固定第一 view rank-0 为 anchor，再取两个补充入口，以 top-3 搜原冻结 NSG。并集至多 24 个候选。三个 views 合起来是一个 ensemble instance，不是三次独立重复，也不是元学习 task。

输入沿用 [Fast 历史契约](01_fast_and_legacy.md)：WebVid/IP/source 近单位与 Yandex official first-10M/raw-IP；R64/L_build100/C512；三个 view 复用同一份 QGT 5K 与同一份旧 prototype-train 30K，仅改变聚类 seed。QGT 与 prototype-train 彼此独立，不是三个 view 各自重新抽样；对应 Fast manifest 的输入 SHA 相同，hub 数为 815/821。在线无 query GT、probe label 或额外 graph probe。Python 历史参考是 exact prototype scoring，初期 C++ 第一 view 用 Micro-HNSW、后两 view dense；因此不能默认两者 route 完全相同。

## 2. 早期 validation：同 L 的小幅质量改善

[旧 decision](../target_basin_ensemble_diagnostics/v1/decision.json)使用两数据集 validation 10K、K10、L64/128，与 seed-20260828 Fast 比较：

| 数据集 / L | Python Recall 差 | Python graph NDC 差 | C++ Recall 差 | C++ graph NDC 差 |
|---|---:|---:|---:|---:|
| WebVid / 64 | +0.871 pp | −2.2783% | +0.822 pp | −2.1272% |
| WebVid / 128 | +0.369 pp | −1.3884% | +0.340 pp | −1.3142% |
| Yandex / 64 | +0.250 pp | −1.7087% | +0.214 pp | −1.7040% |
| Yandex / 128 | +0.209 pp | −0.9920% | +0.148 pp | −0.9990% |

这通过了当时“两个数据集×两个 L 的 Recall/utility 非负”gate，故旧文件状态写 `go_to_stability_tail_and_full_cost`。它只是一组冻结 ensemble 的质量信号；没有 routing NDC，也没有独立 ensemble 重复或 tail。旧 Python/C++ route cell mismatch 为 2.6767%/1.2833%。Python 10K 路由 wall 0.81/0.75 s 含进程与 I/O；C++ 16 线程有效 routing wall 52.313/19.101 μs/query。不能将这些整批分摊时间与线程内 graph mean latency 相加得到端到端 latency。

## 3. E0：工程对齐已通过，计时证明范围后来被收窄

正式化目录为 [target_basin_formalization/20260907_v1](../target_basin_formalization/20260907_v1/)，[protocol](../target_basin_formalization/20260907_v1/protocol.json)绑定两数据集 manifest/图 SHA、原 NSG 与 stop rule。E0 在每数据集 128 个 train 查询上检查 Python/C++ merge 完全一致，真实 anchor 保存，固定 query route 可重复，count 开关不改 route，原/新搜索在 K10、L64/128 的返回 ID/Recall/graph NDC 一致；另做合成 merge、拒绝 K>L、拒绝隐式 held-out。共 16 项 PASS。

[E0 报告](../target_basin_formalization/20260907_v1/audit/report.md)测到 WebVid/Yandex mean routing NDC 1758.648/1764.789，其中 exact component 每 query 固定 1638/1650，已远大于同 L 节省的少量 graph NDC。E0 完成接口与结果一致性，不是方法有效性验证。

后续对 [bench_target_basin_eval.cpp](../benches/bench_target_basin_eval.cpp) 的计时审计确认 `evaluate_query` 的 GT 评分仍在整批 timer 内，线程工作区也在 timer 内创建；旧 E0 没有覆盖这两项。因此旧 count JSON 的 QPS 不可发布，E0 不能被描述为当前纯 wall 边界完全验收。此限制不改变实际 NDC 的 E1/E1b no-go。

## 4. E1 dense：不启动无意义的后续 sweep

[E1 报告](../target_basin_formalization/20260907_v1/pilot/dense/report.md)在前 1,000 个 `drl_train` 查询测量。WebVid/Yandex routing alone 分别 1759.172/1765.384 NDC/query，paired Fast L64 的 total NDC 仅 1037.866/1763.126。两个 L64 点在进入 graph search 前已无法满足预算。

由于 gate 要求两数据集×两个目标均通过，dense 的更多 graph/timing sweep 无法改变结果，故未运行；E1 `FAIL_TRIGGER_E1B` 只允许一次固定后端修订，没有扫 HNSW 参数。

## 5. E1b：HNSW 后端减少了成本，但仍挤占图搜索预算

固定三 view 为 Micro-HNSW，M16/efConstruction200；primary efSearch10/seed100，后两 view efSearch32/seeds101/102，top-8 exact IP rerank；anchor、top-3 和 tie-break（score 降序、entry ID 升序）保持。实际 train-10K gate 结果如下，所有匹配点 NDC 不超过对应 Fast target：

| 数据集 / Fast target | Fast total NDC | Fast R@10 | 匹配 Multi-view L | Multi-view total NDC | R@10 | Recall 差 |
|---|---:|---:|---:|---:|---:|---:|
| WebVid / L64 | 1039.041 | 0.65938 | 22 | 1017.778 | 0.51241 | −14.697 pp |
| WebVid / L128 | 1768.466 | 0.74830 | 80 | 1718.644 | 0.69870 | −4.960 pp |
| Yandex / L64 | 1759.520 | 0.82798 | 44 | 1753.074 | 0.78695 | −4.103 pp |
| Yandex / L128 | 2971.207 | 0.89630 | 104 | 2931.855 | 0.88167 | −1.463 pp |

train-10K 上 mean routing NDC 由 dense 的 WebVid 1760.299→642.337、Yandex 1766.112→549.376；anchor mismatch 均 0，final route change 为 2.47%/0.31%。后两 view 对 scalar-float exact top-8 的集合 recall 很高：WebVid 0.98731/0.98834，Yandex 0.99719/0.99757。因此不能把失败简单解释成后两 HNSW 完全找错邻居。证据指向剩余 routing NDC 仍迫使 graph L 降低，四个相近总成本点的 Recall 均低于 Fast。

[E1b 原表](../target_basin_formalization/20260907_v1/pilot/hnsw/report.md)与[总 gate](../target_basin_formalization/20260907_v1/gate.json)判定 `NO_GO_ROUTING_COST`，返回 Fast v1。等 total NDC 与等 wall 是合取要求；NDC 已失败，故 wall 未运行，不能说 wall 也实测失败，也不能靠 wall 改写已失败的合取 gate。

E2（三组独立 ensemble）、E3（tail/容量/完整 GT-inclusive 成本与归因）、E4（held-out）按规则 `NOT_RUN`，不是待补任务。该批 held-out 未访问；停止后没有继续 top-m/HNSW 扫参。已验证的是固定修订能显著减少路由距离开销，不是部署 Pareto 收益、跨构建稳定性、tail 改善或互补性因果结论。

## 6. Confidence-attention：早于成本正式化的 train-only 公式检验

动机是让“更自信”的 view 获得更高合并权重。固定公式 `s'_v(q,e)=s_v(q,e)+alpha*(s_v(top1)-s_v(top2))`，margin 为该 view top1−top2 分差；其余 top-8 合并、anchor 和 top-3 搜索保持。alpha=0 必须逐字节复现原 ensemble route，先验 gate 才允许检验非零 alpha。

实际仅使用双数据集 `drl_train` 的 10K 查询、K10/L64/128；候选 alpha 为 −2/−1/−0.5/0/+0.5/+1/+2。route 生成不使用标签、不增加在线 graph probe，评价读取训练侧 GT；本批没有 validation 或 held-out 访问。[两份 route report](../target_basin_meta_diagnostics/v1/webvid_train/route_report.json)记录 alpha=0 的顺序/集合变化率均为 0，Yandex 同样通过。

要求一个共享非零 alpha 同时在两个数据集、两个 L 的 Recall 和旧 utility 上非负。实际 WebVid 仅 −0.5 通过其两个点，Yandex 仅 +0.5 通过，交集为空：

| 单数据集通过项 | L64 Recall / graph NDC 差 | L128 Recall / graph NDC 差 |
|---|---|---|
| WebVid alpha=−0.5 | +0.018 pp / +0.035% | +0.065 pp / +0.035% |
| Yandex alpha=+0.5 | +0.039 pp / +0.112% | +0.019 pp / +0.001% |

[decision.json](../target_basin_meta_diagnostics/v1/decision.json)判 `no_go`，当时保留 alpha=0 ensemble、拒绝加入 confidence attention/MAML/Reptile。随后 alpha=0 Multi-view 自身又在正式化 E1b 被成本否决，因此“保留 alpha=0”不能解读为当前仍选择 Multi-view。结论只否决这个共享 margin 修正公式，不能外推为所有 attention 无效、元学习不可能或理论不可学习。

## 7. 原始材料与实现索引

- 历史 ensemble：[decision](../target_basin_ensemble_diagnostics/v1/decision.json)、[Python 路由](../benches/run/route_multiseed_target_basin_ensemble.py)、[旧 C++ evaluator](../benches/bench_entry_oracle.cpp)。
- 正式化：[总报告](../target_basin_formalization/20260907_v1/report.md)、[总 gate](../target_basin_formalization/20260907_v1/gate.json)、[protocol](../target_basin_formalization/20260907_v1/protocol.json)、[E0 JSON](../target_basin_formalization/20260907_v1/audit/report.json)、[E1 JSON](../target_basin_formalization/20260907_v1/pilot/dense/report.json)、[E1b JSON](../target_basin_formalization/20260907_v1/pilot/hnsw/report.json)。
- 正式化实现：[reference merge](../benches/run/route_target_basin_reference.py)、[独立 evaluator](../benches/bench_target_basin_eval.cpp)、[stage runner](../benches/run/run_target_basin_protocol.py)、[E1b 汇总](../benches/run/summarize_target_basin_e1b.py)。
- Confidence：[decision](../target_basin_meta_diagnostics/v1/decision.json)、[WebVid route report](../target_basin_meta_diagnostics/v1/webvid_train/route_report.json)、[Yandex route report](../target_basin_meta_diagnostics/v1/yandex_train/route_report.json)、[路由源码](../benches/run/route_confidence_attentive_target_basin.py)。
