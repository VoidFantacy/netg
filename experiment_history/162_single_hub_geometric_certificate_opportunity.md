# 162 单球/单hub质量证书训练侧机会检查

2026-09-30，沿161推导的固定球/半空间公式，在Web/Yandex原fit各20K完整检查。两集旧exact与approx候选阈值均0/20000可通过；归一化最佳余量分别−0.568694/−0.358309，全部远离1e−10缓冲。Web仅为反事实hard参照，Y为实际hard目标。没有原生float32标签替换或soft证书。

全base范数扫描、全query/hub几何与40万候选点积/集由另一归约实现复算通过；47/48条直接差向量边界审查。主26.069秒、审计13.489秒，CPU0–7/池8。第一次审计启动127只因python命令不存在，未执行数值；原日志与后续同码一次成功均保留。0新GT/NSG/ANN/模型/图/测试数据。

状态STOP_SINGLE_BALL_SINGLE_HUB_CERTIFICATE。原因是这份全局球界过松，不泛化为所有标签认证无用；不改M/删离群点/分块/调教师续跑。默认仍Web soft/Y hard、E99。旧E121已经运行并失败，后续不将更早E126提案当尚待实现的新分支。

[报告](../entry_method_exploration/20260930_theory_until2200_v1/research/single_hub_certificate_opportunity_v1/report.md) · [协议](../entry_method_exploration/20260930_theory_until2200_v1/research/single_hub_certificate_opportunity_v1/protocol.md) · [审计](../entry_method_exploration/20260930_theory_until2200_v1/research/single_hub_certificate_opportunity_v1/independent_audit.json)。
