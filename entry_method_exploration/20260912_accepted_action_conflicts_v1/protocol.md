# E58 已接受动作的跨查询收益/损伤追溯（固定轨迹）

2026-09-12，继续用户“区分局部改进空间小，还是共享画像调整对不同查询冲突”的诊断。须在E57最终模型/性能完成并冻结后执行，不允许本次监控反馈更改模型、seed、checkpoint或最终选择。固定E52/E53/E56全部双集双seed共12条200步轨迹，无新训练。

每run从原P/G0开始，只沿原真正已接受的next_row更新；不动直接复用同一图/评分/查询身份，不新增查询。每接受步重建完整C/W并核验原commit/accepted W和拓扑SHA；E52/E53按学成W普通build并评分，E56按C构图取G再固定P/安装G，真实全画像字节检查。原monitor1024全部实际HNSW，仅三入口变化query新增原NSG，routeNDC每步真实更新。train4096命中仅由已有被接受候选patch重放，不生成任何新训练反馈。

0/20/…/200完整monitor五字段必须逐位恢复原checkpoint；0/selected/200去重各物理图16monitor query三路parity。保存每步monitor routeNDC/改变入口的NSG patch/全cache hash、train与monitor逐query命中差、原选择和目标hub、完整checkpoint/图身份。所有2400步必须重放，不能只保留损伤或正值步骤。

主要统计：同一接受步在train/monitor净命中增减分类，单步内部gain与loss并存，训练正而监控负的频次；每query累计gain/loss、反复正负转换、失败救回/新增/再失败，最终差与全轨迹求和守恒，损伤集中度。按stage/dataset/seed完整报告，区分E52贪心、E53联合RL、E56纯构图RL。历史monitor参与原选点且P拟合曾用过，不称盲测；本阶段只作固定动作机制诊断，不据其曲线重选最佳步。

每集单native实例CPU15实际进程/OMP/BLAS/MKL1线程串行，无并行训练/性能工作；分析CPU8。预算新NSG60000（每集30000）、HNSW2000000（每集1000000），全部实际接受数从已完成模型读取锁定，原生构图<7500/实例；每集≤360秒，artifact128MiB/free7GiB/RSS32GiB，21:30后不启动，21:40硬停，22:00收口。0cal/validation/held-out新查询、0新GT、0优化、0QPS；源保护会hash已有冻结副本，不把最终validation响应作为诊断标签或学习反馈。旧全部产物保留，新日志/结果独立目录。

独立重建全monitor缓存并集合评分变化patch，恢复132 checkpoint的monitor1024、原接受选择/W/拓扑/训练命中patch、最多36图/576原kernelparity行及实际调用账/线程/源SHA；不将本次诊断计数换算为线上QPS。若预算或时间停止，明确未完成范围，不以少量已跑结果概括全部轨迹。
