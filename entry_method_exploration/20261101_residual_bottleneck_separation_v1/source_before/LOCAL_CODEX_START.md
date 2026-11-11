# ACSG 当前接续入口

2026-11-01，/data/netg/ACSG。E195七集详细定位与E196费用邻近对照均完成，默认E99 GT10保持，无待恢复矩阵。先读AGENTS、summary、spec、s-target、s-experiment，再读[E196定位结论](entry_method_exploration/20261101_residual_navigation_cost_controls_v1/findings_zh.md)、[报告](entry_method_exploration/20261101_residual_navigation_cost_controls_v1/report_zh.md)、[51配置](entry_method_exploration/20261101_residual_navigation_cost_controls_v1/analysis/stability.csv)、[核验](entry_method_exploration/20261101_residual_navigation_cost_controls_v1/analysis/validation.json)和[E195来源/导航定位](entry_method_exploration/20261101_residual_navigation_diagnosis_v1/findings_zh.md)。

用户最新优先级：离线训练费用当前不重要，重点提高残差导航入口质量并筛掉不适合的入口。[新方法及旧法对比](entry_method_exploration/20261101_learned_residual_navigation_design_v1/report_zh.md)已整理；新算法THEORY_ONLY_UNIMPLEMENTED_UNTESTED，已有探针复算不等于新训练或性能验证。当前计划以s-target为准，E196旧报告的“先省直接费用”保留历史身份。

原1260点与后继837点分别冻结，不混拼QPS或回写旧原件。粗网格机会不记作成功；新控制仍是有限曝光窗口/单图证据。保留M5/B32/SQ历史正面场景。低度/密度不是删答案规则；直接已评分C无效重算证书不取消其导航资格；新跳过优化、完整续搜、修图/评分器仍未实现。

输出分别/root/acsg-e195-storage、/data/acsg-e196-storage，经storage链接。旧科学原件/PDF/seal和根文档快照保留。按用户后续任务继续，不自动扩大当前窗口、训练至通过、改默认或生成PDF。
