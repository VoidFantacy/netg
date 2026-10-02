# 144 2048标签替换与温度因素的真实搜索检查

2026-09-30，`RETAIN_FIXED_CANDIDATE_PENDING_COST_AND_TRANSFER`，默认不变。承接record143训练方向信号，固定原seed0，不选最好样本；Web旧/2048-GT1温度×近似/直接替换，Y-hard近似/替换，加双集默认共5/3方法。4新画像/小图先冻结，再用E105已曝光4096query/集跑K1/K100两个固定L、CPU15实际单线程三次完整wall。

预定低标签候选Web HybridPilotTemperature对默认ΔR1/R100=−0.048828/−0.015381pp，Y HybridFixedTemperature=+0.146484/+0.004639pp；QPS变化+0.598%/+0.347%、−0.066%/−0.256%，不能称显著加速。相对旧Approx分别为Web+0.048828/−0.012695pp、Y+0.048828/+0.020996pp。完整表、三轮与描述区间见报告；曝光开发与多控制不构成确认性检验。

Web保留旧温度的替换控制有更好均值，但仍依赖完整20K精确GT1，不事后晋升。2048温度从0.0162011385变为0.0158979893后，组合仍改善方向误差16.89%，真实收益却不单调。Y方向误差降8.09%。几何改善不直接保证Recall。

预定Web/Y候选更换1088/846条三入口，K1仅15/26条返回改变；相同三入口全部返回bits和graph NDC一致。目标ID替换重聚合4个W均逐位恢复；旧默认/Approx全数组、warm/plain/count/E99、65536个向量重评分、20区间与58身份核验通过。同一代理独立实现。

327936 NSG、327680 ANN、16方法点/48次wall，0新GT/新来源；控制器721.829秒、分析8.321秒、审计10.889秒。缓存标签不能证明完整冷启动成本；后继固定模型做路由分解和实测费用，不调参数补过。

证据：[报告](../entry_method_exploration/20260930_theory_until2200_v1/research/hybrid_temperature_factorial_v1/report.md)、[协议](../entry_method_exploration/20260930_theory_until2200_v1/research/hybrid_temperature_factorial_v1/protocol.md)、[指标](../entry_method_exploration/20260930_theory_until2200_v1/research/hybrid_temperature_factorial_v1/results/summary.json)、[审计](../entry_method_exploration/20260930_theory_until2200_v1/research/hybrid_temperature_factorial_v1/reviews/independent_audit.json)。
