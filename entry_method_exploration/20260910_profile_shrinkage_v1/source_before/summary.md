# ACSG 当前实验总结

> 更新至2026-09-10夜间。最近完成E25选择性保留E24改道。实现见[spec.md](spec.md)，接续见[s-target.md](s-target.md)，历史见[s-experiment.md](s-experiment.md)。

## 当前总体结论

**E25未得到跨数据集稳定保留收益、减少损失并改善端到端性能的选择规则。WebVid有小幅质量修复，额外路由成本抵消了收益；Yandex主规则减少受损时丢掉了大多数有效改道。** 状态`SELECTIVITY_NOT_GENERALIZED_NO_FORMAL_GO`，本版本全部预定阶段已收口。

A0固定E24 matched Fast20K/GT1硬，A1固定E24按旧cal选定的WebVid GT10软T0.0162011385、Yandex GT10硬。BaseGate用旧路由7特征、按需再跑路由A1；DualGate固定两路13特征。二选一在主图搜索前完成，随后只执行一次原NSG，不在线probe或restart。

## 保留收益与避免损失

预设目标：有效query×L事件保留R≥75%、受损事件避免A≥25%，正命中保留Rh≥75%、负损失避免Ah≥25%，且净命中≥max(0,always-A1净命中)。下表合并L64/128，全部query保留分母。

| 数据集 / cal主规则 | 分段 | R | A | Rh | Ah | 净命中 vs A0 / always-A1 | 目标 |
|---|---|---:|---:|---:|---:|---:|---|
| WebVid / DualGate | cal | 86.88% | 25.44% | 87.26% | 29.62% | +84 / -20 | PASS |
| WebVid / DualGate | audit | 79.48% | 21.95% | 80.12% | 27.12% | +141 / +127 | NOT_MET |
| WebVid / DualGate | validation | 80.66% | 24.77% | 84.17% | 24.62% | +123 / +91 | NOT_MET |
| Yandex-IP / BaseGate | cal | 61.43% | 44.05% | 69.83% | 40.94% | -40 / -110 | NOT_MET |
| Yandex-IP / BaseGate | audit | 38.71% | 47.14% | 48.58% | 32.55% | -81 / -51 | NOT_MET |
| Yandex-IP / BaseGate | validation | 31.08% | 62.90% | 38.41% | 54.05% | +21 / +91 | NOT_MET |

WebVid validation离25%门槛仅差约一个受损事件、两个命中损失单位，不能据此否定整个机制；主要问题是audit不稳定、质量增量小且付出时间。Yandex主规则在cal已失败，只按协议完成反证，不是部署推荐。

## 单线程五点的完整主结果

相对本轮同时重测的A1/E24；每点三次独立warm/plain，QPS报告中位数。

| 数据集 / cal主规则 | L | ΔRecall pp | ΔQPS % |
|---|---:|---:|---:|
| WebVid / DualGate | 64 | +0.070 | -6.50 |
| WebVid / DualGate | 128 | +0.090 | -4.08 |
| WebVid / DualGate | 256 | +0.025 | -2.24 |
| WebVid / DualGate | 400 | +0.070 | -1.36 |
| WebVid / DualGate | 800 | +0.025 | -1.01 |
| Yandex-IP / BaseGate | 64 | -0.115 | -1.15 |
| Yandex-IP / BaseGate | 128 | -0.235 | -1.35 |
| Yandex-IP / BaseGate | 256 | -0.130 | -0.62 |
| Yandex-IP / BaseGate | 400 | -0.090 | -0.91 |
| Yandex-IP / BaseGate | 800 | -0.075 | +0.69 |

非主规则及NSG/Fast30K/Fast20K全部对照保留。两个门控×两数据集×五L相对A1的20项Recall差，描述性95%配对query bootstrap区间全部跨0；没有一点同时Recall提高且三轮对应QPS均提高。粗L网格的非支配点不直接转成等Recall加速结论。

## 机制与成本解释

- 8192 fit query中真正提供非零监督的只有WebVid1081、Yandex401；命中权重ESS约556.85/190.96。权重最高1% query贡献27.47%/57.79%的信号，尤其Yandex效应稀疏集中。
- WebVid DualGate weighted AUC从cal0.6132到audit0.4923、validation0.5693；Yandex BaseGate为0.5552→0.3754→0.4962。求解器已收敛；分段波动尚不能分离为抽样或分布变化的因果结论。
- fit若oracle允许按L分别选择，仅比固定query两L同一选择多98/30个命中，不能把主要失败归于模型不读L。免费oracle没有线上QPS。
- L128路由单测A1→Base/Dual：WebVid6.532→16.076/19.140μs/query，Yandex4.368→6.542/10.223。Base新增3次画像重评分且选新才再跑路由；Dual固定两路和6次重评分。所有计算计入独立端到端wall，分项不相加作QPS。

## 实际执行与验收

fit为router_train后20K固定抽8192；cal[2048,4096)、audit[4096,6144)各2048，配对L64/128。两数据集各30候选、合计12个凸模型，四规则及全部输入/候选/代码/binary在audit前冻结；audit只报告，随后才读历史validation前2000。E24画像见过fit query，各池有历史开发使用；held-out未打开。

六方法×五L×两数据集共60正式点、每点三次计时全部完成。124点219584个输出独立评分；四条原曲线80000个validation输出与E24的ID、距离bits、入口和route/graph NDC逐位相同。门控等于所选策略、全部新增收费、五L选择/logit/入口/微型图一致均通过。

真实调用1,089,152，修复预留0，另合成5144；全部查询实际线程1、CPU15。真实搜索进程1227.50s含加载/构建/预热/计数/I/O，最高RSS10.193GiB；不能换算QPS。63项上游hash、冻结文件与cal选择独立复核通过。原GT/QGT/NSG/E24从零成本未新测。

## 权威证据与接续

- [E25复盘](experiment_history/14_selective_profile_gate.md)、[完整报告](entry_method_exploration/20260910_selective_profile_gate_v1/report.md)、[全部原值](entry_method_exploration/20260910_selective_profile_gate_v1/results/tables.md)、[曲线](entry_method_exploration/20260910_selective_profile_gate_v1/figures/recall_qps.svg)、[收益保留图](entry_method_exploration/20260910_selective_profile_gate_v1/figures/retention_harm.svg)。
- [分析](entry_method_exploration/20260910_selective_profile_gate_v1/results/analysis.json)、[成本](entry_method_exploration/20260910_selective_profile_gate_v1/results/costs.json)、[选择冻结](entry_method_exploration/20260910_selective_profile_gate_v1/models/frozen_before_audit.json)、[审计](entry_method_exploration/20260910_selective_profile_gate_v1/reviews/immutable_integrity.json)。

用户另授权夜间深入分析并可适当探索，最终汇总从9月11日北京时间07:00开始。E25不扩模型或阈值；若做直接相关的单路画像收缩对照，须另立版本/协议/预算。2A等其它研究方向仍在s-target，旧C/probe大队列保持停止。E24局部画像信号保留[历史13](experiment_history/13_gt_topk_profiles.md)身份，所有旧资产保留。
