# 第11会话安全交接：E92–E94完成，整日目标未完成

交接准备时间：2026-09-13T19:54:07.723321+08:00。本会话20:00前退出；整日截止21:00 +0800。唯一实验写入者第11会话的四个native任务均已实际terminal0，没有待恢复ANN、拟合、构建或工具任务。CLI本身的实际退出由监督器在本回复结束后确认，不能用本文件代替进程退出证据。

已完成固定组合E92、真实选型E93和历史E34 validation2000最终矩阵E94。**没有更换默认方法的充分证据**。Web组合对compact五L Recall全部改善、失败全部减少；对匹配GT10-soft P五档Recall都下降。Y compact前三档Recall微增、高L损伤。QPS重复范围不支持稳定整体加速。保留局部正向修复，不将它提升为方法胜出。

[完整实测报告与所有图](stage35_final_comparison_v1/report.md) · [QPS–Recall](stage35_final_comparison_v1/analysis_v1/figures/recall_qps.png) · [QPS–失败率](stage35_final_comparison_v1/analysis_v1/figures/failure_qps.png) · [按L三指标](stage35_final_comparison_v1/analysis_v1/figures/three_metrics_by_L.png) · [双向失败案例](stage35_final_comparison_v1/supplement_v1/figures/failure_cases_both_directions.png) · [完整401失败查询五L全表](stage35_final_comparison_v1/supplement_v1/failed_queries_all_L.csv)。

- E92：[协议/结果](stage33_composed_repair_v1/report.md)。Web固定E84补边+E90五组父恢复，1次向量安装，0新拟合/普通build。aux7952对compact+97命中/失败−10，对P+38、两半+45/−7、失败+1，完整门FAIL。Y恢复零更新，组合是E84别名，没有再跑Y。80960 NSG / 80800 HNSW，57.740s。原预算草稿已在首次查询前保留并修正。
- E93：[选型](stage34_final_selection_v1/report.md)。77条catalog保留，41项合格候选真实评分，326032独立集合返回；36项逐项排除。Web best_all=P、best_new=E92失败反证；Y两角色均compact。开发数据早已观察，规则是最终输入打开前的冻结，不能包装成从未观察开发数据的预注册。实际选型与模型身份均在19:24:33首次最终payload哈希之前冻结。
- E94：50点250轮，Web6方法/Y4方法，同一完整批次含原NSG/Fast/GT10/实际新方法，L64/128/256/400/800，预热1+wall5+count1+kernel16。700800 NSG / 560000 HNSW，native994.213s，纯wall695.047s；0新拟合/build/GT/编译。全部100000返回独立评分，800原kernel、70000历史基线全七字段逐位回归通过。失败为零GT10交集；401独立query、812query×L事件/4230事件方法单元、完整五L10730单元，346条有方法失败状态差异。

本会话合计781760 NSG / 640800 HNSW，native1051.953s。全天累计6854176 NSG / 17820080 HNSW / 360普通build；旧220开发QPS点1100轮与本次50最终点250轮分批，禁止拼曲线。四个native工具64045、39746、13856、81975均returncode0；CPU15/实际threads1，库线程1且时间不重叠。[终态台账](session11_closeout/terminal_ledger.json)保留实际成本与终态。当前/data余量6.584240 GiB，维持6.45 GiB安全下限和额外预留；根文档各阶段source_before及所有旧产物未清理。

角色与限制：画像/构图训练及所有用于动作选择的aux反馈都属于训练信息，aux命名空间router_train已暴露；P-fit20K含旧4096train/1024monitor，旧cal/audit历史暴露不重命名为盲测。E34最终namespace=validation、2000条历史使用，仅用于本次冻结对照；最终反馈没有回流训练、选型或阈值。held-out未打开。底层NSG/base/GT/rawIP/kernel固定；Micro-HNSW仅815/821真实入口的画像小图。最终负结果不能触发按本批反馈调参。

下一条命令（只读、无ANN/训练）：

```bash
cd /data/netg/ACSG
python3 -B entry_method_exploration/20260913_until2100_v1/src/resume_inspect_v11.py
```

接着读本handoff、根四文档和`/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md`最新审查。后继可继续图表表达、根据已有逐query表解释救回/损伤及迁移范围、审阅证据并在21:00前交付；不重跑E92–E94、不改变冻结选择，不启动新训练或新增查询。新的实质方法应另立协议、明确独立反馈角色与预算，不能用本次最终反馈找阳性。本次安全结束不等于整日目标完成，state.day_goal_complete保持false。
