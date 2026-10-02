# 2026-09-13 第二个独立串行研究会话交接

状态：`SESSION2_PHASE_COMPLETE_SAFE_HANDOFF`，2026-09-13 10:56:02 +0800已到安全边界，早于本会话11:14:29截止。E63/E64/E65均完成、独立验收及封存；E60–E62原阶段全部保持。本会话完成不代表整日目标完成：21:00交付仍待后续串行会话推进。当前无原生训练/评估进程、无待接管PID、所有执行工具terminal已实际退出。监督者管理下一会话，不再开并行CLI/子代理。今日用户授权持续，无需重复批准。

## 当前结果与证据

- [E63 零命中query质量重权](stage4_zero_hit_mass_v1/report.md)：固定原GT10归属、2倍原zero-hit质量并归一总质量20K，随机query同质量控制。fit真实候选净+32/+120命中、失败−3/−16，随机fit双集负；保留真实难度质量的训练局部正信号。旧cal净−1/−2命中未过门，audit净−9/+3不回选。不能扩大为难度信息无效，也不按sham cal正值改选。Y原全命中→零命中实为11，旧历史52文字误写12已独立[v2修订](../../experiment_history/52_zero_hit_mass_v2.md)，[correction](stage4_zero_hit_mass_v1/reviews/correction.json)保留旧封存。
- [E64 固定模型池扩大辅助复核](stage5_frozen_pool_aux_v1/report.md)：冻结baseline/missing/score/topology/zero及两sham，在双集各7952条历史开发行评估，固定全量/两半/失败/NDC门。WebVid topology净+38命中、两半+31/+7，救回11/新增13未过失败门；Yandex四个真实新端点净命中全负。zero辅助净−2/−18且两半异号。best_all双集baseline，best_new固定Web E62_topology/Y E63_zero_mass，仅供真实新方法展示，非通过门的推荐。不得回写旧cal门。
- [E65 完整开发wall报告](stage6_development_wall_v1/report.md)：五L64/128/256/400/800、五轮轮换，原NSG/Fast30K/FastGT10-hard及上述实际新候选，Web另匹配GT10-soft。45方法点、225独立整批wall；本批是E64选型已用的source[2048:4096]开发2048，不能替代最终validation。

E65相对匹配起点：Web ΔRecall为−0.0391/+0.0244/+0.0781/+0.0635/+0.0195 pp，保留4/5点局部正；失败净新增0/2/1/1/1。共同Recall区间的描述性log-QPS插值+0.570/+0.683/+0.814%，不是实测同Recall点。Y ΔRecall为−0.1318/0/+0.0049/−0.0928/−0.0342 pp，失败+2/−1/0/+1/+1，质量混合。双集10个匹配QPS差的五轮交叉范围均含零方向，尚无稳定加速或双集新前沿证据，默认不替换。

[QPS–Recall图](stage6_development_wall_v1/figures/recall_qps.svg) · [QPS–失败率图](stage6_development_wall_v1/figures/failure_qps.svg) · [按L三指标](stage6_development_wall_v1/figures/three_metrics_by_L.svg) · [配对差与波动](stage6_development_wall_v1/figures/paired_deltas.svg) · [失败query图](stage6_development_wall_v1/figures/failure_query_cases.svg)。各图PNG/SVG/PDF已保存、亲自查看；全部原始225wall在[timings](stage6_development_wall_v1/results/timings.csv)，不拼其它批次QPS。

失败严格为exact GT10零命中，hits1不算。E65共14条独立source query、24次跨L失败转换事件，完整70格及入口已验收。Yandex row3846全部五L从10→0，仅将入口1027687替换为8932769，另两入口不变；L800仍未恢复是已测范围，不能外推所有预算。row2441前三L0→10的救回保留。Web4063低两L10→0，3434后三L1→0。详情[failure_query_summary](stage6_development_wall_v1/results/failure_query_summary.csv)。事后案例不是学习到的在线难query规则。

paired.csv的gain_hits/loss_hits按逐query净命中变化正部/负部记账；实际GT10成员集合找回/丢失另存[member_deltas](stage6_development_wall_v1/results/member_deltas.csv)，35组独立mask核验。Web L128分别33/28与50/45，Y为26/26与34/34；净值+5/0相同，定义不能混淆。

## 实际成本与运行修复

| 阶段 | 新NSG搜索 | HNSW路由 | 新小图构建 | native操作秒（含加载等） |
|---|---:|---:|---:|---:|
| E60–E62第一会话 | 65344 | 971104 | 336 | 127.071 |
| E63 | 9142 | 133056 | 6 | 23.523 |
| E64 | 222880 | 222656 | 0 | 143.010 |
| E65 | 645840 | 501760 | 0 | 905.745 |
| 第二会话新增 | 877862 | 857472 | 6 | 1072.278 |
| 今日累计 | 943206 | 1828576 | 342 | 1199.349 |

操作秒不充当查询QPS，第一会话E62短暂分析重叠的限制保持。E63离线画像构建另7.061秒、独立聚合/准备另有日志；复用历史标签不是其原成本为零。E64/E65另49源图加载/复制、98 plain/count加载，不当49新构建。今日0新GT/梯度更新；E63是闭式离线训练。E65 route-only/graph-only未另测，以null+原因记录，只报告真实整批在线wall。

E64原prepare缺shared import，在无新查询前修复，原log及[repair](stage5_frozen_pool_aux_v1/reviews/prepare_repair.md)保留。原run监控到taskset exec前继承CPU8而退出，2ms/4KiB/空native log，已kill/wait、实际0查询，但111440完整预留保留。一次明确[启动修正](stage5_frozen_pool_aux_v1/launch_repair_amendment.md)改子进程preexec绑定CPU15，修复后222880实际/累计334320预留，旧runner/log保留。E65沿修正启动，无新增失败。

所有ANN串行CPU15、实际进程和OMP/OpenBLAS/MKL/NUMEXPR/BLIS线程1，计时无并发训练/标签/评分。正式wall含完整路由→三真实ID→原NSG→预分配输出；GT/count/hash/JSON/build/load在外，一次完整warmup加五轮轮换。E65独立92160集合/mask、720原kernelparity、8192 E64相同query L128字节、35物理图、五L同图同入口、225轮QPS恒等和顺序均通过。所有native工具terminal实际返回后才分析。logs/active.json是历史最后采样，不能把其旧RUNNING当活进程；以jobs.json返回码、native_jobs_closed.json、工具退出和/proc核验为准。

## 数据角色、保护和接续

P-fit20K=router_train[10000:30000]，包含旧4096 train/1024 monitor，全部历史训练。cal[0:1024]/audit[1024:2048]已历史与今日使用；audit不再称未观察。E64辅助[2048:10000]7952全部用于预锁选择，计训练反馈；两半为[2048:6024]与[6024:10000]。E65固定其[2048:4096]子集做开发wall。Fast30K已使用前30K，旧E10还完整评估前10K，所以余行/分区不相交不能证明全项目新盲集。源query/GT SHA及旧22048行回归通过。

E34历史validation2000今日未进入训练/选型/评测，旧E10 validation原结果本会话未再打开；held-out未打开。晚间允许冻结后最终比较，但最终反馈不得回流训练、改候选或换门。best_all/best_new今日当前选择见[candidate_inventory_v2](candidate_inventory_v2.json)，14个既有候选及图/W/mapping身份；原inventory与[第一会话交接](handoff_session1.md)完整保留。

根文档、源码、历史脏树均未清理/删除/推送/外发，Codex配置未改；所有新大输入只在/data且尽量引用旧文件。各阶段source_before保留根文档，freeze引用root_after快照，后续可合法更新当前根文件。E63旧历史52已用v2纠正，不能静默覆盖原卡。昨日39保护文件和六阶段封存/候选共2644次文件身份校验通过，见[read-only resume核验](reviews/session2_final_resume_check.json)。E65最终489文件已封存。

当前/data余量约7.526GiB，本会话新增约173MiB、本campaign约457MiB；精确字节/时间见[session2 closeout](reviews/session2_closeout.json)。下一阶段现场核对free≥7GiB、建议新增≤128MiB，并留晚间输出空间，不删除历史。主监督notes已读至stage7序列化接口提醒，接续后及主要阶段后继续读`/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md`。

下一会话完整读AGENTS、summary、spec、s-target、s-experiment和本交接，再运行只读命令：

```bash
cd /data/netg/ACSG
env PYTHONDONTWRITEBYTECODE=1 .venv_cpu/bin/python entry_method_exploration/20260913_until2100_v1/src/resume_inspect_v2.py
```

该脚本不导入NumPy/native，不运行ANN、训练或最终query。禁止重跑已完成stage1–6或沿用其过期时间常量。新stage7必须另建版本、根文档source_before、前瞻完整公式/控制/输入角色/预算与会话截止。

有依据的优先备选在[next_stage_design_session2](next_stage_design_session2.md)：固定H/三真实入口，把原P+两份加权GT10 query模态放同一3H小索引，搜7个unique slot后按明确排序去重为3真实hub，duplicate3P容量控制。当前**尚未实现/运行**，单画像瓶颈和两个有效模态均未证实。须回查history04→旧E10 builder/router/报告，锁父/子质量与ESS、低支持重复P、raw先验、dense soft归属与成本；不能暗中稀疏化。现有graph_file标签断言/k3/tie_ids接口不支持该映射，须实现真实slot序列化及plain/count/原单画像回归，不仅改searchKnn数值。3H=2445/2463画像，unique H=815/821分账。只锁单容量，停止当前lambda/weight/seed/local-action盲扫。

## 整日仍待完成

20:00停止新训练、20:40停止新增查询、21:00完整交付。E65只完成历史开发曲线，晚间仍须在E34历史validation2000上，用冻结的best_all与今天真实best_new，同批完整NSG/Fast30K/FastGT10-hard/Web匹配soft对照、五L五轮wall、aligned逐query集合评分和失败报告。现有接口静态图可复用E34同SHA evaluator，多slot则必须先完善新接口。

即使没有新方法过门，也诚实展示今天真实候选的最终曲线及损伤；不只用baseline自身或昨日图交差，不把局部Recall、NDC、有限oracle、描述性插值或一次QPS包装成最终改进。本会话安全交接不将整日目标标为完成。
