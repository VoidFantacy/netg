# GT10晚间研究与E125复测交付

2026-09-22，原17:00报告独立保留，本目录承接工作至22:00的理论与改进研究。用户随后要求E125简单复测及调整一票否决策略，已完成。

- [综合报告](report.md) · [PDF](GT10理论与性能改进研究.pdf) · [HTML](report.html)
- [最新单组新查询复测](stages/e125_web_fresh_check_v1/report.md)：冻结模型，Web K1/L1000，4096条新源query；R1差−0.146484pp、QPS−0.104439%，保留低成本候选，未替换默认。
- [研究判定策略](research_decision_policy.md)：探索与默认替换分开，单点非劣证据不足不一票否决。
- [改进方向](directions.md) · [理论](theory.md)
- [近似监督费用依赖](research/approximate_supervision_scope_v1/report.md)：Web温度继承旧exact GT标定，不能外推为无精确监督冷启动。
- [残差方差核算](research/approximate_residual_variance_v1/report.md)：只读训练统计，随机纠偏不保证少量补标即可改善，未训练候选。

原默认Web GT10-soft-t1、Yandex GT10-hard和生产E99保持。原E125协议/门/STOP结果保留当时身份，新判定与复测另存；新查询不可再当未曝光确认集。当前无后台性能或训练队列。根文档原件、早期报告稿和排版版本均保存在source_before/reviews，图表均由已有统计生成。
