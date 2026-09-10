# 10｜C 同状态一次有限入口干预：C0/C1/C2

执行日期2026-09-09；版本[20260909_c_stage1_v1](../entry_method_exploration/20260909_c_stage1_v1/README.md)。当前状态 **`NO_GO_UNCONDITIONAL_HEADROOM_STOP_C`**。C0协议锁和C1实现验收通过，C2完成但四点共同实质门失败；C3、C4未运行。

## 1. 动机与旧负证据

[E14](05_probe_reroute.md)已使用paid trace、frontier/topology和merged Recall/NDC预测替代入口，最终WebVid chooser失败，最终Yandex扩展未运行。C正面保留该负证据；新检验点限定为从同一个完整搜索状态克隆、一次有限force动作、共同剩余graph-NDC cap，并保留实际成本。不能复用E20或A+B的独立single效用`u_L(q,e)`作为标签，也不以C挽救A+B。

[C R0](../entry_method_exploration/20260909_c_r0_v1/README.md)属于设计未运行历史；其QING/ANNiE等前作边界不改变。本次用户另行明确授权C0→C1→最多每dataset2K drl_train的C2，并将C设为第一优先级；不是从旧R0自动推导许可。

## 2. 冻结协议与访问范围

WebVid2.5M和official Yandex first10M，原始IP、原NSG R64，K10、L64/128。起始策略是QGT seed20260828、后20K `[10000,30000)`画像的paired Fast3（M16/efConstruction200/efSearch10，direct top3）。另一次固定top7查询的零基rank3:7提供最多四个query-only候选，去重不补位；图/base/metric/GT/Fast模型都不改。

每数据集PCG64 seed20260909在drl_train前10K中不放回取2000行，保持抽样顺序。前128条只做GT-free完整native成本校准：每L取两数据集扩展数中位数的较小值之一半向下取整，得到33/65完成扩展checkpoint；单全局B按四点最大P75完整NDC的一半向上取64倍数，得到1856。该公式在校准前写入protocol，数值与SHA在C2质量前锁定。没有扫checkpoint或B。

前16条作C1真实验收，前4条作smoke，C2主诊断仍完整2000条；没有新增query或自动扩样本。它是历史开发训练池，不是新鲜held-out。只读训练侧向量/GT，validation/held-out只出现于旧manifest元数据，未打开其数据文件。GT在两数据集全部raw分支完成后才由独立脚本离线评分。

## 3. 状态机与C1

独立[`state_machine.hpp`](../entry_method_exploration/20260909_c_stage1_v1/src/state_machine.hpp)保存有序L+1 retset/float distance/pending、有效长度、cursor/updated_pos、独立visited/expanded、query/入口/身份、消耗/剩余NDC、partial-row node/offset及最多16条GT-free历史。深clone和JSON持久化不共享可变visited/pool；base/graph只读共享。原`search_new`源码未修改，新实现不覆盖旧API。

natural支付candidate距离并按原pool规则插入/rewind。force在同样插入尝试后启动一次强制row，后续resume实际扫描，不论candidate是否保留；expanded独立记录，防止重复扩展。cap在下一次新距离前截断，未评分ID不标visited；能跳过padding/visited并自然终止。返回原retset topK，不换global topK。

最终C1：180组合、5961组断言、960个partial-row、159个force/natural控制、全相等tie等均通过。显式手算用例验证pool拒绝、accepted→evicted、保留三种动作的完整后继顺序。两真实图各16query×2L共64条记录，pause→clone/serialize→resume在无cap无注入时与真原kernel ID、float bits、NDC和完整扩展/距离顺序一致。原kernel顺序由机械提取且仅加observer的reference辅助记录，reference先与真kernel对照。

独立审阅代理另行实跑精确cap之后零距离尾部自然终止、DC query重绑定、partial序列化和终态no-op。非法初始入口只在新API拒绝，不调用原kernel的未定义越界路径。plain/count/trace、重复continue和跨branch隔离均通过。

第一次synthetic也通过；v2补shape防御和显式覆盖，未改变原kernel或C0科学协议。C2别名复制成本后来显式分列；统计预审在真实质量前修复+0.5pp浮点边界，改用精确增命中≥100，并补齐失败reservation与raw别名不变量。这些是验收/统计实现修正，不是事后改变gate。

## 4. C2执行与主结果

smoke每dataset4query×2L通过后，完整2000query×2L。主raw物理执行（含prefix及count/plain重复）WebVid74596、Yandex79604；smoke152/160。每query最多9个逻辑分支：continue、四natural、四force；无资格槽alias同一continue，不额外搜索。全部early/no-eligible/visited/no-op进入N=2000无条件均值。

主oracle只在continue与合法force间按Recall选最佳，ties先continue再固定槽序；natural作为同候选配对控制。20000次query-paired bootstrap，四点Bonferroni族95%区间，每点还必须平均≥+0.5pp。

| 数据集 | L | capped continue | finite force oracle | 无条件Δ pp | 校正CI pp | 点gate |
|---|---:|---:|---:|---:|---|---|
| WebVid | 64 | 65.595% | 66.575% | +0.980 | [+0.620,+1.410] | PASS |
| WebVid | 128 | 74.800% | 75.435% | +0.635 | [+0.365,+0.975] | PASS |
| Yandex-IP | 64 | 83.150% | 83.380% | +0.230 | [+0.040,+0.495] | FAIL |
| Yandex-IP | 128 | 89.440% | 89.580% | +0.140 | [+0.005,+0.360] | FAIL |

WebVid总增命中196/127、Yandex46/28，各点实质门为100。四点校正区间均正，但Yandex均值未达门槛，因此整版停止。严格改善query比例4.05%/2.90%/0.45%/0.30%；Yandex只有9/6条严格获益。没有删除survivor之外的query，也不能抹去WebVid正信号后概括成“完全无空间”。

## 5. 覆盖、机制、实际成本

四点early-finished均0；无合法候选0.15%/0.65%/0/0，语义有效force覆盖99.85%/99.35%/100%/100%。有效定义为轨迹或retset变化，与严格Recall收益不同。oracle选continue比例95.95%/97.10%/99.55%/99.70%，每槽选择率与visited/no-op细分均在原report。

同候选force−natural的四槽无条件均值（pp）分别为WebVid L64 `[+.220,+.095,+.100,+.130]`、L128 `[+.180,+.045,+.075,+.075]`，Yandex L64 `[+.080,+.025,+.085,+.035]`、L128 `[−.045,−.015,+.005,−.015]`。这是描述性机制对照，未训练selector；按oracle赢家再看同candidate自然插入有GT选择偏差，不称状态可学性证明。

| 点 | continue实际graph NDC均值 | oracle均值 | oracle P50/P95/max | continue自然结束 |
|---|---:|---:|---|---:|
| WebVid L64 | 918.8445 | 922.6540 | 870.5/1503.05/2230 | 99.90% |
| WebVid L128 | 1644.6705 | 1644.9290 | 1586/2512.05/3516 | 97.85% |
| Yandex L64 | 1636.6005 | 1637.4280 | 1587/2629/3315 | 98.75% |
| Yandex L128 | 2787.6330 | 2787.6010 | 2764.5/4244.1/4788 | 82.20% |

所有分支suffix≤1856、total=prefix+suffix；逐query实际envelope和9动作全分布保留。共同cap不保证相等NDC；表中continue也是capped suffix，尤其Yandex L128有17.8%被cap截断，不能混为无cap完整Fast。两次路由各自收费，平均NDC为WebVid各129.6415、Yandex各111.2445。

单物理branch深clone均值25.43/39.57/40.68/64.83μs，状态JSON序列化均值104.08/145.45/105.32/166.38μs，恢复275.66/375.20/280.93/431.96μs；全部为单线程诊断成本。state初始化包含种子距离、resume包含图搜索，不能把它们称纯bookkeeping开销。每物理branch独立plain计时与count/trace全state一致，GT/hash/JSON/DC分配/clone在branch timer外；alias明确复用continue的wall且另外记materialization成本。

主raw runner wall38.728/58.824秒，包括装载、路由、clone、count/plain搜索、检验和I/O，不含之后GT评分；不是方法QPS。CPU-only单worker、最大RSS约10GiB量级，完整资源数值见commands/resource日志。输入准备最初的逐进程资源时长未独立保存，不补造完整端到端离线时长。

## 6. 停止边界与未运行

结论仅为该固定Fast3/checkpoint/B/四候选动作集的跨数据实质headroom门失败；不是所有同状态干预不可行。WebVid oracle通过也不证明状态条件预测可学，不撤销E14旧chooser失败。

按用户要求完成C2即停：不运行C3 learner/state×reuse、C4完整Recall–QPS、validation/held-out、全H动作、多checkpoint、多步RL，也不改B/候选/模型救场。A+B保持设计未实现，无联动与协同GO。未来两者分别通过后仍需在最终micro A+B诱导state重新cross-fit，再做{Fast,AB}×{off,policy-specific C}并检验预注册正交互。

## 7. 原始证据

- [完整报告](../entry_method_exploration/20260909_c_stage1_v1/report.md)、[准确命令](../entry_method_exploration/20260909_c_stage1_v1/commands.md)、[执行状态](../entry_method_exploration/20260909_c_stage1_v1/state.json)。
- [协议](../entry_method_exploration/20260909_c_stage1_v1/protocol.md)、[配置锁](../entry_method_exploration/20260909_c_stage1_v1/config.locked.json)、[source manifest](../entry_method_exploration/20260909_c_stage1_v1/source_manifest.json)、[C1 gate](../entry_method_exploration/20260909_c_stage1_v1/results/c1_gate.json)。
- [正式统计](../entry_method_exploration/20260909_c_stage1_v1/results/analysis_v1/report.json)、[C2 gate](../entry_method_exploration/20260909_c_stage1_v1/results/analysis_v1/gate.json)、[WebVid原始state/分支](../entry_method_exploration/20260909_c_stage1_v1/results/c2_main_webvid_v1/)、[Yandex原始state/分支](../entry_method_exploration/20260909_c_stage1_v1/results/c2_main_yandex_v1/)。
- [独立kernel终审](../entry_method_exploration/20260909_c_stage1_v1/reviews/kernel_final_review.md)、[统计预审](../entry_method_exploration/20260909_c_stage1_v1/reviews/c2_statistics_pre_review.md)。其后最终统计/文档审阅同版本reviews目录保留。
