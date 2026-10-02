# 141 归一化画像方向误差与补标机会

2026-09-30原fit20K只读诊断，0新GT/ANN/NSG/部署画像/图/QPS。默认保持，今天理论研究继续至22:00。

将record140总和误差投影到精确画像切空间后，Web/Y均匀无放回补标的解析临界m从3269/8516升至7462/9501。切向偏差占原尺度17.95%/52.57%，方差占54.69%/64.16%，说明直接近似偏差减少得更多；不能称少量随机补标会改善。Web线性化偏差仅为真实弦长误差63.92%，最小径向分母比0.298，归一化分母也不能省略。

方向残差能量在最高1%训练query集中54.47%/42.40%。使用全部真值的理想有放回抽样方差为同设计均匀的14.42%/12.51%；仅是诊断机会，不能部署或当Recall结果。后继应测试近似画像可得的廉价信号。真值最优全局控制变量只能减少约2.2%/2.5%切向方差，暂不优先扫λ。

统计83.625秒、独立公式审计11.277秒。原assignment/合力/旧方差恢复；32hub显式中心化、64query能量及32控制变量检验通过；几何反例与有限总体枚举通过。同一agent独立实现，无新的确认集访问或参数选择。

[报告](../entry_method_exploration/20260930_theory_until2200_v1/research/directional_error_v1/report.md) · [理论](../entry_method_exploration/20260930_theory_until2200_v1/research/directional_error_v1/theory.md) · [协议](../entry_method_exploration/20260930_theory_until2200_v1/research/directional_error_v1/protocol.md) · [审计](../entry_method_exploration/20260930_theory_until2200_v1/research/directional_error_v1/reviews/independent_audit.json)
