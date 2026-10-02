# E67 多画像与重复画像控制完整wall

2026-09-13，55方法点、275轮同批完整单线程wall已完成。E66固定mode3P双集展示，duplicate3P为同容量控制；原E66开发门失败保持，不依本批调参。原NSG/Fast30K/GT10-hard与Web匹配soft同批，真实H/原NSG/base/raw-IP/GT不变。

webvid2_5m_light_v1：L64/128/256/400/800相对匹配GT10的ΔRecall=+0.2197/+0.0391/-0.0586/+0.1953/+0.0732 pp，QPS中位变化=-2.471%/-0.962%/-1.507%/-1.470%/-0.184%，失败净新增=+3/+4/+2/-1/+0；4/5个QPS交叉范围跨零。全部曲线为本批独立完整wall，不能与E65拼接。

yandex_t2i_official10M_ip_v1：L64/128/256/400/800相对匹配GT10的ΔRecall=+0.4199/+0.0879/+0.1074/-0.0098/+0.1123 pp，QPS中位变化=-2.298%/-1.099%/+0.305%/-0.407%/+0.141%，失败净新增=-7/-2/-1/+0/+0；4/5个QPS交叉范围跨零。全部曲线为本批独立完整wall，不能与E65拼接。

source router_train[2048:4096]历史开发2048已用于E64/E66辅助选型，全部是历史暴露开发，不称最终泛化。E34最终validation及held-out未打开。GT在全部raw后评分；完整wall含一次7slot路由/去重/真实映射/原NSG/output，GT/count/hash/JSON/build/load在外。实际CPU15/进程与库1线程，单方法串行，两个native工具terminal实际退出后分析。

新增789360 NSG、645120 HNSW，45物理图源加载/复制与90 plain/count加载，0新图/训练/GT。112640集合/mask、880原kernelparity、全slot映射与五L图/入口/275wall、71680 E65基线及12288 E66 L128原返回回归通过。操作1110.551秒不是QPS。

[报告和全部曲线](../entry_method_exploration/20260913_until2100_v1/stage8_multimode_wall_v1/report.md) · [协议](../entry_method_exploration/20260913_until2100_v1/stage8_multimode_wall_v1/protocol.md) · [原始wall](../entry_method_exploration/20260913_until2100_v1/stage8_multimode_wall_v1/results/timings.csv) · [逐query失败](../entry_method_exploration/20260913_until2100_v1/stage8_multimode_wall_v1/results/failure_query_summary.csv) · [验收](../entry_method_exploration/20260913_until2100_v1/stage8_multimode_wall_v1/reviews/verification.json)。
