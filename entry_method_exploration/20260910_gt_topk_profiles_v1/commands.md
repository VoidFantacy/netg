# E24 实际执行与复现边界

工作区 `/data/netg/ACSG`，独立目录 `entry_method_exploration/20260910_gt_topk_profiles_v1/`。没有安装依赖、修改主build、原ACSG或旧模型/图/标签。画像准备用项目 `.venv_cpu/bin/python`；评测调用已有CPU静态库、独立编译的新二进制。

## 执行顺序

1. 完整阅读五份主文档、四问题报告与论文阅读记录；由历史04/05/08/12追溯原设计、E20 protocol/state/analysis-v2及E23 protocol/prepare/evaluate/原结果。阅读输入记录在[保护清单](reviews/protected_before.json)；原根文档和git差异分别在[source_before](source_before)、[git状态](reviews/git_status_before.txt)、[原差异](reviews/git_diff_before.patch)。
2. `src/initialize.py`：核对原base/NSG/query/GT校验和、E23 fit/cal与原始行逐项一致、H真实ID和base向量。仅用fit GT1分数间隔确定三个温度。OMP/OpenBLAS/MKL=16；没有图搜索、validation/held-out或训练标签访问。日志[initialize.log](initialize.log)。
3. 在任何新画像、cal搜索和validation读取之前写入[protocol.md](protocol.md)、[config.locked.json](config.locked.json)与[锁定时间/hash](reviews/protocol_lock.json)。正常真实搜索543296，修复预留8192，总上限551488。
4. `src/build_profiles.py recover`：原builder恢复GT1硬；[日志](logs/recover_profiles.log)。`src/build.py`编译独立evaluator；精确argv/源码与binary身份在[build manifest](bin/evaluate.build.json)。`src/check_synthetic.py`验证五L、三入口、独立GT评分和线程拒绝，[验收](reviews/synthetic_gate.json)。
5. `src/recover_search.py`：每数据集fit32、旧/新P0×exact/HNSW，核对全部返回ID/距离bits/入口/NDC并与E23前32条回归；[恢复验收](reviews/recovery_gate.json)。随后 `src/build_profiles.py candidates` 构建剩余七份/数据集；[日志](logs/candidate_profiles.log)。构建16线程，正式查询1线程。
6. `src/run_development.py cal`：先冻结两数据集全部画像及执行源码，再依次跑两数据集各16个L128点，所有点完成后按冻结规则选择。实际每个子进程由 `taskset -c 15` 固定CPU，环境OMP/OPENBLAS/MKL=1。所有精确argv、PID、exit、进程wall、实际线程/RSS、预留及真实调用在[search_jobs.json](reviews/search_jobs.json)，正式点QPS取各自results中的plain wall。cal日志[cal_driver.log](logs/cal_driver.log)。
7. `src/run_development.py audit`：先核对冻结模型及选择，再读取audit对应行；所有候选只报告，不重新选参。[日志](logs/audit_driver.log)。
8. `src/run_validation.py`：要求cal门通过且audit完成，先写[validation前冻结记录](models/frozen_before_validation.json)，再读取并核对历史validation前2000条；依次完成双数据集各六方法×五L。独立route/graph分项仅在L128，不能相加替代端到端wall。[日志](logs/validation_driver.log)。
9. `src/analyze.py`：全部输出独立GT10重评分、两基线配对比较、bootstrap描述、近似检索与支持统计、三条基线E23逐位回归、五L入口/微型图一致性、表与图。`src/verify_integrity.py`在所有计时结束后重新hash原base/图/源码/输入、冻结模型，并独立重算cal选择；不与正式计时并行运行。
10. 最后形成完整报告、成本和E24历史卡，更新四份主文档；交付链接与状态再检查。阶段退出码以ledger/日志为准，不把代码编译和画像恢复当作方法性能通过。

## 保留与调用边界

所有runner拒绝已有输出目录，控制器在job前预留完整调用；失败时保留日志、partial输出和调用预留。协议不变的实现修复才可使用预留。若后续复现，应创建新版本、重新绑定源码/输入/输出身份，不直接重跑这些脚本覆盖本目录。

新画像不使用E22全H single或E23 triple训练标签。已有GT100、QGT H和NSG是明确复用依赖，其从零生成成本未新测。`GT1_hard`的旧通用builder辅助字段`requires_aco_dpc=true`只是原始元数据，实际调用没有ACO/DPC；新manifest明确无需搜索标签或梯度训练。

初始恢复产物保留了GT1硬的dense归属矩阵。后续候选在cal前改为只保存完整支持统计和精确float64矩阵digest，归属可按fit及冻结公式重算；画像公式/数值及参数不变，控制总存储低于2GiB。
