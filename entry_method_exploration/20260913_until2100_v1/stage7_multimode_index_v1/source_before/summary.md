# ACSG 当前结果摘要

2026-09-13，第二串行会话完成E63–E65。尚无通过完整开发门的新方法替换当前WebVid GT10-soft、Yandex GT10-hard；WebVid的局部曲线正信号保留。今日已有45个历史开发QPS方法点、225轮完整wall；E34最终validation尚未执行，整日21:00目标未完成。

E63保持GT10归属、固定2倍原零命中query质量并归一总质量20K。真实模型fit净+32/+120命中、失败−3/−16，明显区别于E61 fit净负；cal净−1/−2仍未过门，audit净−9/+3不回选。随机质量控制fit负、cal正，不能由小cal差值推断难度信息无效，也不把sham改成推荐。

E64冻结今日7模型，在每集7952条其余历史开发行复核。WebVid纯拓扑净+38命中、两半+31/+7，但救回11/新增13未过失败门；Yandex四个真实新端点净命中全部负。E63在全辅助净−2/−18且两半方向相反。best_all双集baseline，best_new仅作展示为WebVid E62_topology、Yandex E63_zero_mass，原cal失败保持。

E65固定上述真实新候选及NSG/Fast/FastGT10，WebVid另匹配soft起点，在协议预定source[2048:4096]开发2048上同批五L五轮。WebVid ΔRecall为−0.0391/+0.0244/+0.0781/+0.0635/+0.0195 pp，共同Recall描述性log-QPS插值+0.570/+0.683/+0.814%；局部信号保留，但失败净新增0/2/1/1/1。Yandex为−0.1318/0/+0.0049/−0.0928/−0.0342 pp，质量混合。双集全部10个QPS差范围均含零方向，尚无稳定加速或双集新前沿证据。所有曲线使用本批独立完整在线wall，不拼旧批次。

失败严格为GT10零命中。E65共14个独立source query/24次跨L转换事件：Yandex3846在全部五L从10变0，只换一个入口，扩大到L800仍未恢复；2441前三L从0救回到10。WebVid4063低两L从10变0。完整命中/入口及损伤图保存，事后案例不当在线可预测机制。

E60–E62原结论保留：辅助支持0/40、遗漏目标画像fit/cal净负、评分与拓扑混合致损。第二会话新增877862 NSG/857472 HNSW/6build；本日累计943206 NSG/1828576 HNSW/342build，E64/E65另49物理源图加载/复制。无新GT/梯度更新。E65的92160集合/mask、720原kernelparity、8192历史同query回归和225wall验收通过；CPU15实际线程1、串行。E64启动竞态0查询、111440失败预留和一次修正均保留；未覆盖旧产物。

P-fit含旧train/monitor；cal/audit及7952辅助均历史暴露，E64辅助反馈计选型训练。Fast30K与旧E10已使用前10K，不能称余行为项目新盲集。E65子集已用于E64选择，开发曲线不替代最终验证。E34最终反馈不得回流训练，held-out未打开。下一未运行表示备选及晚间正式交付见s-target。

[E65完整报告与图](entry_method_exploration/20260913_until2100_v1/stage6_development_wall_v1/report.md) · [E64报告](entry_method_exploration/20260913_until2100_v1/stage5_frozen_pool_aux_v1/report.md) · [E63报告](entry_method_exploration/20260913_until2100_v1/stage4_zero_hit_mass_v1/report.md) · [交接](entry_method_exploration/20260913_until2100_v1/handoff.md)。
