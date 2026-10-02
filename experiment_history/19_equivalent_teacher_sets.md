# 19 等效三入口集合教师（E30）

2026-09-11结果完成，状态`EQUIVALENT_TEACHER_SETS_COMPLETE_NO_RELIABLE_REPLACEMENT`。WebVid2.5M推荐GT10 soft；Yandex10M IP推荐GT10 hard。 “本次数值最快”与达到预设替换条件的推荐分别记录，不能将计时波动中的微小领先称为稳定胜出。

## 问题与实质变化

延续[E29](18_teacher_objective_alignment.md)的教师拟合/实际检索缺口。原C8中最高hits且最低graph NDC的教师经常不唯一；新G保留全部严格并列三元组。single只接受原T0，multi接受G；二者使用相同56组合竞争域、共享linear、固定λ100/τ.05/μ.1、Adam.003、80轮最后epoch。损失max(F+.1×非接受)减max接受F只约束已标注C8域，未知组合不当作已知负例。

两集4次训练后，multi均稍有更大位移。仅由fit模型将multi沿normalize(P+t(W−P))缩到single的均方位移，形成multi_matched；single_matched是single同字节alias。整体位移匹配不匹配逐hub方向或实际入口。在线仍一份HNSW3→真实hub→原NSG，无新增在线网络或组合重排。

## 执行与比较

标签224万逻辑条全量ID→GT复核，新标签0。完整fit20k L128、cal/audit1024 L64/128及audit exact3；原validation2k、12方法×5L×两集120正式点，各5次单线程独立warm/plain。所有新画像在开发前冻结，开发门失败不触发重新调参；按用户要求保留最终完整曲线。

| 数据集 | 本批插值速度几何均值最高 | 相对原默认 | 推荐 |
|---|---|---|---|
| WebVid2.5M | GT10 soft | +0.00% | GT10 soft |
| Yandex10M IP | GT10 hard | +0.00% | GT10 hard |

上表在预设WebVid75/80/85%、Yandex90/95/98%的实测非支配曲线上作Recall–logQPS插值，不外推，不是新增精确等Recall测量。原默认为WebVid GT10 soft/Yandex GT10 hard；替换要求覆盖三点，其中至少两点中位+3%且五轮比值均>1，其他点无≥3%退化。

## 完整五L结果

以下相对同批GT10 hard，同L两项变化不等于等Recall加速。全部正负和各轮计时在原报告/表中。

| 数据集 | L | E29 margin ΔRpp / ΔQPS | single ΔRpp / ΔQPS | multi ΔRpp / ΔQPS | multi matched ΔRpp / ΔQPS |
|---|---|---|---|---|---|
| WebVid2.5M | 64 | -0.020 / -0.05% | -0.025 / -0.02% | -0.035 / +0.04% | -0.030 / -0.02% |
| WebVid2.5M | 128 | -0.010 / +0.08% | -0.080 / +0.03% | -0.080 / +0.16% | -0.070 / +0.11% |
| WebVid2.5M | 256 | +0.055 / -0.08% | -0.040 / -0.07% | -0.045 / +0.02% | -0.045 / -0.09% |
| WebVid2.5M | 400 | +0.025 / -0.02% | +0.010 / -0.09% | +0.005 / -0.07% | +0.005 / -0.05% |
| WebVid2.5M | 800 | -0.005 / -0.02% | -0.040 / -0.01% | -0.045 / -0.02% | -0.045 / +0.04% |
| Yandex10M IP | 64 | +0.060 / -0.05% | +0.060 / -0.09% | +0.040 / +0.02% | +0.040 / -0.00% |
| Yandex10M IP | 128 | -0.020 / +0.09% | -0.020 / +0.04% | -0.025 / +0.13% | -0.025 / +0.05% |
| Yandex10M IP | 256 | -0.045 / +0.04% | -0.045 / -0.03% | -0.055 / +0.05% | -0.055 / -0.21% |
| Yandex10M IP | 400 | -0.035 / -0.07% | -0.035 / -0.05% | -0.045 / +0.00% | -0.045 / +0.03% |
| Yandex10M IP | 800 | -0.040 / -0.01% | -0.040 / -0.01% | -0.040 / -0.06% | -0.040 / -0.00% |

## 开发与停止位置

| 数据集 | multi fit ΔRpp | 同漂移multi−single pp | cal平均ΔRpp | audit平均ΔRpp | 推进条件 |
|---|---|---|---|---|---|
| webvid2_5m_light_v1 | +0.123 | +0.010 | +0.063 | -0.186 | 未通过 |
| yandex_t2i_official10M_ip_v1 | -0.009 | +0.004 | -0.078 | +0.034 | 未通过 |

推进状态`STOP_FURTHER_MODEL_EXPANSION`。预设fit各≥+0.20pp、成本增幅≤1%、共同位移下multi胜single及两开发split平均收益均正。该门控制进一步研究扩展，不代替最终QPS；最终曲线按用户要求完成。等效数量、共同G接受率、实际HNSW接受、完整fit有/无空间组、分数梯度改变比例分别保存；代理或梯度不是性能因果证明。

关键机制：T0原本就在G内按锚点分数择优，因此初始化时两目标选中的最高分好组合完全相同。有真实命中空间组仅1.04%/0.65%的query改变分数梯度，没有空间组则为15.06%/12.11%；最终multi分数下前者为6.40%/3.42%。这些初末检查及很小的实际单/多差值，削弱“唯一教师身份是当前主要瓶颈”的判断，但不证明整条优化轨迹或QPS因果。多教师与漂移匹配相对推荐方法的三目标插值QPS几何均变分别为WebVid−1.38%/−1.40%、Yandex−0.79%/−0.83%。

## 成本、保护与边界

4次训练共24.52s(CPU8，含训练诊断)。原NSG调用3,177,280，repair0/synthetic0；180点491200个query输出独立评分，9条原曲线180000输出逐位回归E29。原库/图/kernel不变，新评测源码只将3轮合同改为5轮。正式CPU15/实际进程与OMP线程1，无训练或重分析并发。

只有历史fit/cal/audit/validation、一个H/图、一个优化seed和固定80轮；没有收敛证书、fresh blind confirmation或held-out读取/hash。G的相同命中数/NDC不要求相同GT成员，也不保证相同wall。E24 GT10/E28 MLP历史局部信号保留，本次增强边界不反推原方法无效。

## 原始证据

- [协议](../entry_method_exploration/20260911_equivalent_teacher_sets_v1/protocol.md)、[完整报告](../entry_method_exploration/20260911_equivalent_teacher_sets_v1/report.md)、[方法研究](../entry_method_exploration/20260911_equivalent_teacher_sets_v1/research.md)。
- [主Recall–QPS](../entry_method_exploration/20260911_equivalent_teacher_sets_v1/figures/recall_qps_main.svg)、[全部曲线](../entry_method_exploration/20260911_equivalent_teacher_sets_v1/figures/recall_qps_all.svg)、[漂移控制](../entry_method_exploration/20260911_equivalent_teacher_sets_v1/figures/drift_control.svg)、[Excel](../entry_method_exploration/20260911_equivalent_teacher_sets_v1/chart_data.xlsx)。
- [选择判定](../entry_method_exploration/20260911_equivalent_teacher_sets_v1/results/method_selection.json)、[开发门](../entry_method_exploration/20260911_equivalent_teacher_sets_v1/results/development_gate.json)、[原始点](../entry_method_exploration/20260911_equivalent_teacher_sets_v1/results/all_points.csv)、[调用账](../entry_method_exploration/20260911_equivalent_teacher_sets_v1/logs/evaluation_jobs.json)、[最终验收](../entry_method_exploration/20260911_equivalent_teacher_sets_v1/reviews/final_audit.json)。

本版本预算收口；接续见当前[s-target](../s-target.md)，不重启旧runner。
