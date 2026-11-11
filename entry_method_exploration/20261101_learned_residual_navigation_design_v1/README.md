# 学习残差导航入口：方法设计与旧方法对比

2026-11-01，按用户要求将研究重心转向提高残差导航入口质量和筛除不适合的入口，离线训练费用不作为当前设计约束。

先读[中文报告](report_zh.md)，再看[原有单入口探针复算](analysis/seed_quality_summary.csv)及[核验](analysis/reanalysis_validation.json)。新方法为THEORY_ONLY_UNIMPLEMENTED_UNTESTED；数值只复用已封存E195探针，没有新训练、ANN、GT或QPS。默认E99不变。

原根文档见[source_before](source_before/)，源身份见[source_manifest](source_manifest.json)。文档交付状态见[state](state.json)，根链接、数值与E196封存桥接见[validation](validation.json)。本目录不是新实验编号，不恢复旧runner，不生成PDF。
