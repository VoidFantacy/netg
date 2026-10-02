# E45：原批次与完整训练池梯度的确定单步控制

2026-09-12。用户授权持续研究至20:00。E44原入口分层未过门，保留停止结论；此控制不更改分层规则或重训，而检验固定动作反馈替换后，原Adam确定均值更新是否产生真实收益。

## 固定身份与唯一干预

沿用E44全部20个context：双数据集E43 RL第一seed20260921，原step20/40/…/200动作前状态与原八方向。不按GT、正负收益或梯度强度挑状态。不改变P/B/尺度/H/映射、σ.3、原cosine步长、clip、Adamβ/eps、行局部计数、原NSG/IP/L128/K10、query行/GT或原图参数。

从E43完整checkpoint及中间trajectory的mu_after/m_after/v_after/count恢复当前行状态，必须逐位恢复原mu_before。原batch128梯度按原Adam重放得到N_batch，参数与画像next_row须逐位恢复E43；这只是回放。用E44固定八方向下完整train4096的条件梯度替换g，其它输入完全相同，得到N_full。每个context只计算一次新的反事实Adam，20次互相独立，不将结果传给下一个context，不搜索步长或选最佳候选。它消除本八方向下的query抽样误差，不消除方向采样噪声，不是离散检索目标的解析梯度。

保存当前行μ/m/v/count、原/全梯度、两份更新参数和float32行、行位移、完整W来源/SHA。当前C来自E44；N_batch/N_full只替换同一目标行，其他行保持C字节。全池梯度含原命中/总NDC/失败/漂移项；不能把非零成本梯度称命中收益。

## 真实查询与核验

每context C普通构图，run原train前16，保存物理图并16query三路parity；全部返回/拓扑恢复E44。C的完整4096评价复用E44已核验raw，明确0额外完整C查询。

N_batch/N_full各普通构图，完整查询原train4096，保存raw/完整拓扑/物理图，前16query count/serialized plain/原kernel三路parity。W及全部非目标行身份复核。没有新monitor/cal/audit/validation/held-out查询或GT；只用旧隔离train输入，搜索不读取GT。

以C为参照，分别报告两种单步G/L/net、零命中事件、U/J、route/graph/total NDC，另报告N_full−N_batch。将已有八扰动的全池收益与确定更新实际收益并列，不能以采样候选的收益替代均值更新效果。逐query损伤与全池总值完整保留。

## 查询前门与接续

每数据集10个互不传递的context累加，仅作诊断：N_full相对C总净命中>0、平均ΔU>0；相对N_batch总净命中≥0、平均ΔU严格>0；N_full总体graph NDC相对C≤+1%。双集都满足，才说明有继续研究可支付反馈方案的单步依据，仍不是训练/泛化/部署GO，不能把不同context拼成一份W。

若任一数据集不满足，停止以改query采样作为当前版本的直接救援；下一优先隔离画像评分变化与HNSW邻接重建，以及采样候选/确定均值的真实响应。保留已测动作收益，不推广为RL或画像学习不可能；不追加幅度、epoch或近组网格。

## 预算、资源与截止

每context C收费16+3×16=64 NSG；两种确定更新各4096+3×16=4144，总8352。双集20context实际预计167040 NSG、166080 HNSW、60构图；每dataset完整预留83520/native cap84000，全硬限170000，无自动重试，失败不释放。连续训练更新0、新反事实单步20、历史单步回放20分开记。

CPU15实际进程/OMP/OpenBLAS/MKL1，图和数据集串行；每dataset timeout600s，19:40查询截止且19:30后不启动完整job。分析CPU8、地址空间32GiB、目录256MiB、可用至少9GiB；进程wall含加载/构图/计数/写盘/parity，不作QPS。保护E37–E44及原native/NSG依赖；E44权威完成快照为final_artifact_freeze_v2.json（首版日志写入竞争说明保留），根文档前件另存。

交付20对确定行/状态、60物理图、40完整raw、20当前恢复raw、逐query配对与全部正负统计、独立Adam/集合评分/parity审计、报告/历史34及四主文档同步。阶段结束按证据继续20:00目标。
