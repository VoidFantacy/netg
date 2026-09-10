# C 第一阶段实际执行报告

**结论：C0、C1全部通过，C2完成后停止当前冻结C配置。** WebVid两点通过common-cap headroom门，Yandex两点仅+0.230/+0.140pp，低于预注册+0.5pp。最终 `NO_GO_UNCONDITIONAL_HEADROOM_STOP_C`。不进入C3，不运行C4，不扩模型/候选/B，不联动A+B。

## 1. C0协议锁与实际范围

paired Fast20K、QGT seed20260828、原IP和冻结NSG；CPU-only单worker，OMP/BLAS1，最大允许16线程。每dataset在drl_train前10K中PCG64 seed20260909不放回取2000行；这属于历史开发池，与paired后20K画像fit隔离，但不是新鲜held-out。前128条只做GT-free成本校准，前16条做C1真实验收，前4条smoke；没有增加不同query。

锁定checkpoint为完成33/65次邻接扩展（L64/128），全局额外graph-NDC cap B=1856。起始入口来自direct HNSW top3；独立top7调用的后四槽生成候选，去重不补位。每候选分别做natural insert与force-expand；每个分支只动作一次。候选真实距离计入B，两个路由调用各自付费。原位continue是相同cap下的继续，**不能把它误标为无cap完整Fast**。

见[协议](protocol.md)、[锁定配置](config.locked.json)、[lock SHA](protocol_lock.json)、[C0独立审阅](reviews/c0_protocol_review.md)、[状态身份展开](inputs/state_identity_contract.json)。后者由已绑定的图/base SHA和索引头明确原IP语义；不修改任何原始state。

## 2. C1实现与验证

独立state保存L+1有序pool、flag、有效长度、cursor/rewind、visited/expanded、query/入口/身份、预算及partial-row offset、有界history。原search_new源码与库不改。reference机械提取自冻结源码，只增加外部observer，并先与真原kernel比对；不以两个手写实现相互佐证。

最终synthetic v2：180组合，5961组断言，960个partial-row案例、159个force/natural控制、3个tie fixture全部通过；显式手算用例覆盖pool拒绝、插入后淘汰、保留时的完整后继扩展顺序。两真实图各16query×2L，共64条记录，无cappause/clone/serialize/resume的ID、float bits、NDC、完整扩展与距离调用顺序一致。原plain/count/trace一致，分支无污染、共享search_L改变不影响state。独立补充测试实跑精确cap后零距离自然结束、DC错误query重新绑定、partial序列化与终态no-op。

第一版synthetic也通过；v2增加防御式shape检查与显式边界证据，未修改C0动作或预算。非法初始ID只在新API拒绝，不对原kernel执行未定义越界输入。C1结果：[gate](results/c1_gate.json)、[synthetic](results/c1_synthetic_v2.json)、[WebVid](results/c1_webvid_v2.json)、[Yandex](results/c1_yandex_v2.json)、[独立kernel审阅](reviews/kernel_final_review.md)。

## 3. C2主结果：无条件均值与校正区间

每点N=2000；所有early-finished、无合法候选、visited和no-op query均纳入。主oracle只在continue与四个合法force中选最大Recall，ties先continue再冻结槽序。20K query-paired bootstrap，Bonferroni4族95%（每项98.75%）；+0.5pp实质门用精确累计增命中≥100判断。四点区间均正，但Yandex没有达到实质门。

| 点 | continue R@10 | oracle R@10 | Δ pp | 校正CI pp | 新增命中 | 点gate |
|---|---|---|---|---|---|---|
| WebVid L64 | 65.595% | 66.575% | +0.980 | [+0.620, +1.410] | 196 | PASS |
| WebVid L128 | 74.800% | 75.435% | +0.635 | [+0.365, +0.975] | 127 | PASS |
| Yandex-IP L64 | 83.150% | 83.380% | +0.230 | [+0.040, +0.495] | 46 | FAIL |
| Yandex-IP L128 | 89.440% | 89.580% | +0.140 | [+0.005, +0.360] | 28 | FAIL |

## 4. 覆盖与oracle动作比例

effective指扩展轨迹或最终retset改变，严格质量改善另列。它不等于正Recall收益；force仅改变轨迹亦可算effective。已visited槽均映射continue，无额外动作距离。

| 点 | early % | no eligible % | 所有force均语义no-op % | 至少一个有效force % | oracle严格增益 % |
|---|---|---|---|---|---|
| WebVid L64 | 0.00 | 0.15 | 0.15 | 99.85 | 4.05 |
| WebVid L128 | 0.00 | 0.65 | 0.65 | 99.35 | 2.90 |
| Yandex-IP L64 | 0.00 | 0.00 | 0.00 | 100.00 | 0.45 |
| Yandex-IP L128 | 0.00 | 0.00 | 0.00 | 100.00 | 0.30 |

以下比例分母均为全部2000query，F0–F3对应固定四候选槽。

| 点 | continue % | F0 % | F1 % | F2 % | F3 % |
|---|---|---|---|---|---|
| WebVid L64 | 95.95 | 1.45 | 1.20 | 0.80 | 0.60 |
| WebVid L128 | 97.10 | 1.15 | 0.85 | 0.55 | 0.35 |
| Yandex-IP L64 | 99.55 | 0.15 | 0.10 | 0.15 | 0.05 |
| Yandex-IP L128 | 99.70 | 0.00 | 0.10 | 0.15 | 0.05 |

## 5. 实际graph NDC与envelope

每query每branch满足`total=prefix+suffix`、`suffix<=1856`。共同上限不是相同实际工作。下表为全部query实际graph NDC；逐query envelope min/max及所有9动作完整分布保存在[JSON](results/analysis_v1/report.json)及aligned CSV。

| 点 | continue均值 | oracle均值 | oracle中位 | oracleP95 | oracle最大 | continue自然结束 % |
|---|---|---|---|---|---|---|
| WebVid L64 | 918.845 | 922.654 | 870.5 | 1503.05 | 2230 | 99.90 |
| WebVid L128 | 1644.670 | 1644.929 | 1586.0 | 2512.05 | 3516 | 97.85 |
| Yandex-IP L64 | 1636.601 | 1637.428 | 1587.0 | 2629.00 | 3315 | 98.75 |
| Yandex-IP L128 | 2787.633 | 2787.601 | 2764.5 | 4244.10 | 4788 | 82.20 |

oracle相对continue的ratio-of-means graph-NDC变化依次为 +0.4146%, +0.0157%, +0.0506%, -0.0011%；不是逐query比值均值，也不是完整routing+graph成本。

Fast3与额外candidate top7两次调用各自平均routing NDC：WebVid各129.6415、Yandex各111.2445；即新候选路由成本必须额外支付。所有样本的direct top3与top7前三槽一致，但起始策略仍使用独立direct top3。

## 6. Force相对同候选natural的机制描述

以下每槽均用相同candidate的force−natural，单位pp，全2000query均值；属于描述性次比较，不冒充主族显著性。

| 点 | F0−N0 pp | F1−N1 pp | F2−N2 pp | F3−N3 pp | natural oracle−continue pp |
|---|---|---|---|---|---|
| WebVid L64 | +0.220 | +0.095 | +0.100 | +0.130 | +0.300 |
| WebVid L128 | +0.180 | +0.045 | +0.075 | +0.075 | +0.245 |
| Yandex-IP L64 | +0.080 | +0.025 | +0.085 | +0.035 | +0.045 |
| Yandex-IP L128 | -0.045 | -0.015 | +0.005 | -0.015 | +0.045 |

按主force oracle所选同一candidate对比其natural分支，平均差依次 +0.715pp, +0.410pp, +0.185pp, +0.095pp。该赢家条件比较有GT选择偏差，不能证明在线可学性；force oracle与natural oracle可能选不同e，二者差也不称纯机制效应。

## 7. Clone/state成本及时间边界

以下为单线程诊断中实测均值，单位微秒；JSON保存完整分布。clone为每物理branch的深拷贝，序列化/恢复用于诊断持久化，不是未来线上必需操作。state初始化含前三入口距离，prefix resume包含图搜索；没有把差值假称纯bookkeeping开销。

| 点 | clone μs/branch | 序列化 μs/query | 恢复 μs/query | 初始化 μs/query | prefix resume μs/query | state bytes均值 |
|---|---|---|---|---|---|---|
| WebVid L64 | 25.43 | 104.08 | 275.66 | 8.23 | 121.19 | 18446.6 |
| WebVid L128 | 39.57 | 145.45 | 375.20 | 8.38 | 256.22 | 23806.2 |
| Yandex-IP L64 | 40.68 | 105.32 | 280.93 | 6.57 | 168.57 | 16425.6 |
| Yandex-IP L128 | 64.83 | 166.38 | 431.96 | 6.58 | 374.71 | 24338.1 |

无资格alias明确复用同一continue计时，其输出materialization成本单列。每个物理branch另用plain DC独立计时，与count/trace完整终态相等，GT/hash/JSON/DC分配/clone在branch timer外。候选/clone/prefix/suffix wall都是诊断分项；没有独立整批方法QPS、正式Recall–QPS或Pareto GO。

主raw运行：WebVid38.728秒，Yandex58.824秒（包含装载、路由、clone、两种branch执行、检查及I/O；不含后续GT评分）。WebVid一分钟前完成，Yandex约57秒时1936/2000，按实际吞吐预计余约2秒。持续资源采样、执行命令、stdout均保存；静态输入hash在搜索计时外。

## 8. 停止与未运行

C2触发的是**双数据集四点实质headroom门失败**；不能写成“完全无空间”或把WebVid正信号抹去。Yandex仅9/6条query被oracle严格改善，虽校正区间为正，均值仍不足+0.5pp。实际候选覆盖很高，因此当前记录也不能简单解释为全部候选都visited。该结论仅否决冻结checkpoint/B/Fast3/四候选配置，不推出所有同状态策略无效。

C3 learner、state×reuse训练、query-only对照学习、restart/merge析因、C4正式QPS、validation/held-out、全H动作、多checkpoint、多步RL均未运行。A+B仍设计未实施；没有联动或synergy证据。停止后只做评分复核、文档与provenance校验，不再运行ANN。

原E14强负证据继续保留；C2的WebVid有限oracle正值不挽救旧chooser，更不证明C可学。未来若两边分别通过，仍必须在最终deployed micro A+B诱导状态重新cross-fit后才做{Fast,AB}×{off,policy-specific C}，正交互才称协同。

## 9. 实际命令与证据

[完整实际命令](commands.md)、[机器argv/UTC/退出码](logs/commands.jsonl)、[状态](state.json)、[原始WebVid](results/c2_main_webvid_v1/)、[原始Yandex](results/c2_main_yandex_v1/)、[正式统计JSON](results/analysis_v1/report.json)、[gate](results/analysis_v1/gate.json)。`bin/*build.json`绑定源码/静态依赖/可执行SHA，`source_before`保留dirty工作区与旧根文档/源码快照。
