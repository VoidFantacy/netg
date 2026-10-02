# 2026-09-13 第三个独立串行研究会话交接

状态：`SESSION3_PHASE_COMPLETE_SAFE_HANDOFF`。E66/E67/E68全部完成、验收并封存，实际安全边界时间/磁盘/进程见[session3 closeout](reviews/session3_closeout.json)，早于本会话12:13:18截止。**本会话完成不代表整日目标完成**；21:00完整交付、晚间E34最终对照仍待后续串行会话。唯一写入/实验者，无并行CLI/子代理；监督者负责安全退出后的下一会话，无需再问批准。

## 当前结果

- [E66 单3H多画像](stage7_multimode_index_v1/report.md)：固定原P+两GT10加权query模态，同一小HNSW七slot去重为三真实hub，duplicate3P同容量控制。Web合格478/815hub，fit净−496/aux−106命中、aux失败+13；Y合格623/821hub，fit+164/aux+49、失败−4，但固定两半−14/+63。两集原门失败保持；Y局部正信号不能被后续损伤抹去。相对重复P控制mode双集更好，但尚不足替换原P。
- [E67 完整开发wall](stage8_multimode_wall_v1/report.md)：原NSG、Fast30K、GT10-hard、Web匹配soft、mode与duplicate同批；L64/128/256/400/800，五轮轮换。55方法点、275独立wall。源为既有aux[2048:4096]2048，历史开发，不能代替最终validation。
- [E68 完整画像排序诊断](stage9_profile_ranking_diagnosis_v1/report.md)：0新ANN，111808完整评分参照+55904重复alias。原P/duplicate完整评分相同，aux完整前三一致率Web86.38%/59.09%、Y93.61%/72.75%；mode相对自身参照77.73%/86.38%。确认物理索引/近似检索组合存在损失，未唯一归因，也未测精确路由的NSG反事实。

E67相对匹配GT10，五L顺序：

| 数据 | ΔRecall pp | QPS中位变化% | 失败净新增 |
|---|---|---|---|
| WebVid | +.2197/+.0391/−.0586/+.1953/+.0732 | −2.471/−.962/−1.507/−1.470/−.184 | +3/+4/+2/−1/0 |
| Yandex | +.4199/+.0879/+.1074/−.0098/+.1123 | −2.298/−1.099/+.305/−.407/+.141 | −7/−2/−1/0/0 |

Y保留4/5档Recall提高且失败不增的局部信号；L64 QPS五轮交叉范围全负，Web L400亦全负，其余8点跨零。共同Recall描述性log-QPS插值Web−.791/−1.297/−.503%，Y+.277/+.385/+2.548%，只是实测点间插值，不能叫测得同Recall增速或稳定新前沿。E67 subset不能回写E66完整aux两半门；原GT10默认未替换。

[QPS–Recall](stage8_multimode_wall_v1/figures/recall_qps.png) · [QPS–失败率](stage8_multimode_wall_v1/figures/failure_qps.png) · [按L三指标](stage8_multimode_wall_v1/figures/three_metrics_by_L.png) · [配对差](stage8_multimode_wall_v1/figures/paired_deltas.png) · [失败query图](stage8_multimode_wall_v1/figures/failure_query_cases.png)。五图PNG/SVG/PDF均保存并亲自查看，监督独立复核通过；全部275轮wall在[timings](stage8_multimode_wall_v1/results/timings.csv)。E65旧批45点225轮完整保留，不拼接为同批曲线。

失败严格exact GT10零命中。E67共93条独立query（Web52/Y41）、182个跨L转换事件（96/86）、465个五L格；图每集展示24例，全量CSV保留。Y row3846五L10→0，mode已与完整画像前三一致；Web3849五L0→10，mode与其完整前三0重合。更准的画像排序可能保留损伤或改变已有救回，不能从agreement断言质量。全部93例的[排序注释](stage9_profile_ranking_diagnosis_v1/results/failure_ranking_annotation.csv)已连接原始入口/命中。mode aux精确组Web−1/Y+108、非精确组−105/−59均事后关联，不是可加回的反事实收益。

paired.csv gain_hits/loss_hits是逐query净命中正部/负部；实际GT10成员找回/丢失单列[member_deltas](stage8_multimode_wall_v1/results/member_deltas.csv)，45组恒等验证。失败救回/新增和成员损益不能混称。

## 实现与成本

原底层NSG/base/raw-IP/GT/H不变。E66离线20轮加权球面两模式，Web dense soft全部保留；父mass>=8/ESS>=16、子mass>=2/ESS>=8，低支持重复P，raw prior按子质量分配。原assignment SHA与P逐字恢复，模式/先验/质量/归一独立核验。H仍815/821真实入口，物理画像2445/2463，不是10M新HNSW。

新接口只在stage7隔离副本：unique slot标签、many-to-one mapping、唯一tie_ids、七slot距离/slot排序去重三真实ID后canonical升序、physical与unique count分账。图源加载及count重载同时验W字节和slot/real标签，新增trace保存七候选slot/距离；输入容器显式input_total_rows允许fit20K前缀。原E34 binary不能直接加载3H图；后续多画像正式对照应复用已验收E66/E67 binary或另行回归新接口。原NSG kernel与hnswlib没改。

| 阶段 | 新NSG | 新HNSW调用 | 新小图 | native操作秒 |
|---|---:|---:|---:|---:|
| E66 | 337248 | 336960 | 4 | 250.863486 |
| E67 | 789360 | 645120 | 0 | 1110.551495 |
| 会话3合计 | 1126608 | 982080 | 4 | 1361.414981 |
| 今日累计E60–E68 | 2069814 | 2810656 | 346 | 另见各阶段成本 |

合成验收另1 tiny图/15 HNSW/0 NSG，未混入表中实际数据构建。E66离线画像构造30.286秒，E68主分析10.674秒、独立复核1.774秒，准备/编译/绘图另计日志；不是QPS或零训练成本。0新GT/梯度更新，E66加权聚合是离线训练。E66另2原图源加载+12后续源加载、18 count副本加载；E67另45源图加载/复制、90 plain/count加载，不能当新构图。route-only/graph-only未另计时，以null及原因保留。

所有ANN CPU15、实际进程和OMP/OpenBLAS/MKL/NUMEXPR/BLIS线程1，单方法串行；正式整批wall包含路由→去重/真实ID→原NSG→输出，GT/count/hash/JSON/build/load在外。E66六native、E67两native全部工具terminal exit0，之后才进行E68；目前无训练/ANN/分析遗留任务。logs/active.json是历史采样，不凭其旧RUNNING判断进程；看jobs返回码、工具退出及/proc。

E66独立168480返回集合、56160原baseline恢复、288原kernelparity及全部slot/图/模式恒等通过。E67独立112640返回、880原kernelparity、71680 E65原基线与12288 E66 L128回归、45图及275wall轮换/QPS恒等通过。E68主P112条/mode14条标量完整排名、167712入口集合重算、93失败连接通过，监督另全量111808排名/167712 regret重算通过。E66首分析numpy.bool_ JSON导出失败，原log/source保留，analyze_v2仅bool转换与旧CSV等价核验，没有新查询。

## 数据角色、保护及候选身份

P-fit=router_train[10000:30000]含旧4096train/1024monitor；cal[0:1024]/audit[1024:2048]均历史使用。aux[2048:10000]7952用于E64/E66辅助选型及E68诊断，任何选择反馈都计训练。Fast30K/旧E10已暴露这些源行，元数据余行和分区不交不证明全项目未观察。E65/E67开发2048亦已观察。源query/GT/原P/图身份保持。

E34历史validation2000今日未被本会话训练/选型/评测使用；held-out未打开。晚间最终反馈必须冻结后一次性对照，不回流选型。candidate_inventory_v3保留18候选及W/graph/mapping/tie_ids身份，旧v2和E64选择不改；E67的best_new只是固定mode分支展示，**不是全局新best_new已重选**。最终best_all/真实best_new仍须按已公开开发规则前瞻冻结。

所有旧源码/图/标签/GT/日志/脏工作区与昨日封存保留，无清理/删除/推送/外发/Codex设置变化。根文档每阶段source_before及root_after保留，详细历史55/56/57已同步四主文档/索引。封存E66 332项、E67 617项、E68 42项；后续不可静默改旧字节，当前根文档可合法继续更新并保存新前件。[会话2交接](handoff_session2.md)原字节已保存。预交接3675项身份核验通过，最终计数见[最终只读复核](reviews/session3_final_resume_check.json)。

当前free约7.28GiB，本会话新增约245MiB，精确字节见closeout。下一阶段现场核对free>=7GiB，优先引用冻结图/大query而非每L复制，给晚间曲线预留空间；不得删旧文件或临时降旧协议门。

## 下一会话第一步

完整读AGENTS、summary、spec、s-target、s-experiment和本交接，再运行：

```bash
cd /data/netg/ACSG
env PYTHONDONTWRITEBYTECODE=1 .venv_cpu/bin/python entry_method_exploration/20260913_until2100_v1/src/resume_inspect_v3.py
```

脚本只读，不导入NumPy/native、不训练/ANN/读最终输入，核验stage1–9、历史修订、18候选、昨日39保护路径及会话2/3封存；禁止重跑已完成runner或沿用已过期会话时间。

优先方向见[next design v2](next_stage_design_session3_v2.md)：先冻结E68完整P/mode前三的真实NSG离线诊断，固定aux7952/L128与两半，加入原approx P回放控制。当前没有新反事实查询、模型或ef30结果。监督11:58只读[cache覆盖](reviews/supervisor_cache_coverage_readonly.json)提示31808逻辑流中28102可复用、去重后仅3535未测query×三入口；此覆盖本会话只读报告，下一会话先自行验证完整源key/字节再锁预算。可按E46精确反馈缓存思路仅补缺，plain/count正常调用7070外还须显式计预检/回归/原kernelparity；实际数/旧复用/逻辑alias分账，不能把离线查表当QPS。

已有history35及E46 cache_environment.cpp/config已读；E46显式三入口接口可参考，但其旧train4096容器和过期runner不能重启。E66/E67 evaluator没有逐query入口注入路径，适配须在独立版本验收。若精确mode无净效用，停止仅修近似的解释；若有信号再锁单ef10→30（P/duplicate/mode均有ef30参照）或一个有证据的实现，不扫seed/容量/多ef，也不并行两方向。当前hnswlib已有distinct-document stop_condition，不能称新概念或直接加载不兼容float-only图。

主要阶段后继续读`/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md`，本会话读至12:01最终验收。所有新方向另立协议/预算/源前件，监督建议不是额外批准门。

## 全天仍未完成

20:00停止新训练，20:40停止新增查询，21:00交付完整报告。今天已有100个历史开发性能点、500轮wall，**最终E34性能点仍为0**。晚间先冻结best_all与今天实际best_new，再同批原NSG/Fast30K/GT10-hard/Web匹配soft/真实新方法五L五轮、aligned集合评分、QPS–Recall/QPS–失败率/按L三指标和失败query汇报。若没有稳定改善就如实报告，不用baseline自比、旧批拼图、训练收益或单次QPS代替用户目标。
