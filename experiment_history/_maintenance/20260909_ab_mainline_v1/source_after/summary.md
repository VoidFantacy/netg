# ACSG 当前实验总结

> 实测与停止状态更新至2026-09-09。本文维护最近真实实验结果；实现契约见[spec.md](spec.md)，下一步见[s-target.md](s-target.md)，历史见[s-experiment.md](s-experiment.md)。

## 1. 当前结论

**下一阶段主线已按用户最新指令切换为A+B：可路由性约束的入口—表示联合设计。** 当前只有联合理论设计，下一项是最小协议；本次优先级更新没有新增实现、标签、训练或搜索。完整计划由[s-target.md](s-target.md)维护，A+B尚无性能GO。

**最近完成的方案C已实际执行C0→C1→C2，当前冻结配置在C2门停止，不进入C3。** 版本`entry_method_exploration/20260909_c_stage1_v1`，状态`NO_GO_UNCONDITIONAL_HEADROOM_STOP_C`。WebVid两点有实质oracle空间，Yandex两点未达到预注册+0.5pp；不能写成所有点无空间，也不能把common-cap oracle当成可部署方法或Recall–QPS GO。

C已退出当前推进队列，不与A+B联动；其停止不证明A+B有效。原C R0仍保留当时设计未运行身份，本轮真实执行属于新的stage1版本。此前E20 Fast根因诊断及E14/E15/E16的证据边界不变。

## 2. 实际完成

- C0：完整读取主文档、历史复盘、C R0及原kernel；从各2000条预定drl_train名单中取128条，只用原Fast3的GT-free成本分布锁定checkpoint33/65（L64/128），全局额外B=1856。paired Fast20K、QGT seed20260828、K10、原IP/NSG不变。
- C1：独立版本状态机完成pause、深clone、JSON序列化/恢复、单次natural/force动作和partial-row预算。原search_new未修改。180组合合成、64条双真实图query×L及独立边界harness通过；ID、float bits、NDC、扩展/距离顺序、重复确定性、分支隔离、plain/count/trace与原Fast回归均通过。
- C2：每dataset4query smoke后，完整运行各2000query×2L。固定direct Fast3起始；另取top7后四槽，去重不补位。最多continue＋四natural＋四force，GT只在两数据集所有raw分支完成后由独立评分脚本读取。全部early/no-eligible/visited/no-op纳入无条件均值。
- 停止后只做独立统计/文档复核与provenance校验；没有扩候选、改B、多checkpoint或补跑ANN。

## 3. C2无条件主结果

每点N=2000；主oracle是continue与最多四个合法force的事后最佳，ties先continue。20000次query配对bootstrap，Bonferroni4族95%区间；四点都要均值≥+0.5pp、校正lower>0并有实际NDC envelope内有效覆盖。

| 数据集 | L | capped continue R@10 | oracle R@10 | Δ pp | 校正CI pp | gate |
|---|---:|---:|---:|---:|---|---|
| WebVid | 64 | 65.595% | 66.575% | +0.980 | [+0.620, +1.410] | PASS |
| WebVid | 128 | 74.800% | 75.435% | +0.635 | [+0.365, +0.975] | PASS |
| Yandex-IP | 64 | 83.150% | 83.380% | +0.230 | [+0.040, +0.495] | FAIL |
| Yandex-IP | 128 | 89.440% | 89.580% | +0.140 | [+0.005, +0.360] | FAIL |

四点区间均为正，但Yandex只增加46/28个总GT10命中，低于各点100个的实质门。oracle严格改善query比例为WebVid4.05%/2.90%、Yandex0.45%/0.30%；全部query均保留。不能仅据survivor子集解释成功。

## 4. 机制、成本和证据限制

- 四点early-finished均为0；无合法候选比例为0.15%/0.65%/0/0，至少一个有效force覆盖为99.85%/99.35%/100%/100%。有效指轨迹或retset改变，严格Recall改善单列，不能混用。
- oracle相对continue的实际graph NDC均值变化为+0.4146%/+0.0157%/+0.0506%/−0.0011%；所有分支额外NDC≤1856。相同cap不是相同工作，更不是同wall。Yandex L128的continue有17.8%被cap截断，不能将本表capped continue称为无cap完整Fast。
- 同候选force−natural的四槽无条件平均增量在WebVid多为小正值；Yandex L128为−0.045/−0.015/+0.005/−0.015pp。完整机制表见报告，均为描述性次比较，未证明状态增量可学性或复用优越性。
- 物理branch深clone均值约25.43/39.57/40.68/64.83μs，状态序列化和恢复等另计。两个routing调用也分别收费；每branch的plain timer排除GT/hash/JSON/clone。主raw runner含装载、计数、复制、检验和I/O的wall为38.728/58.824秒，不换算方法QPS。
- 样本为历史drl_train开发池、单paired构建，bootstrap只反映固定协议下query变异。C2是共同剩余cap的有限动作headroom门，没有正式性能或原创性GO。

C3 learner/state×reuse、C4完整Recall–QPS、validation、held-out、A+B训练和联动全部未运行。当前失败仅否决冻结C配置，不外推所有同状态策略不可能；也不通过扩大模型、候选或预算救场。

## 5. 权威证据

- [C第一阶段完整报告](entry_method_exploration/20260909_c_stage1_v1/report.md)、[实际命令](entry_method_exploration/20260909_c_stage1_v1/commands.md)、[状态](entry_method_exploration/20260909_c_stage1_v1/state.json)。
- [主统计与逐分支成本](entry_method_exploration/20260909_c_stage1_v1/results/analysis_v1/report.json)、[C2 gate](entry_method_exploration/20260909_c_stage1_v1/results/analysis_v1/gate.json)、[C1 gate](entry_method_exploration/20260909_c_stage1_v1/results/c1_gate.json)。
- [历史10：C真实执行](experiment_history/10_c_state_intervention.md)；[此前E20](experiment_history/08_fast_router_diagnosis.md)；[E14](experiment_history/05_probe_reroute.md)与[E15/E16](experiment_history/06_finite_beam_and_atlas.md)。
- 下一阶段主线与协议交付要求见[s-target.md](s-target.md)；设计依据为[A+B联合理论](entry_method_exploration/20260909_ab_joint_r0_v1/README.md)，尚未形成执行协议或实验结果。
