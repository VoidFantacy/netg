# 129 E122 动作关联的预测函数正则

2026-09-22，22:00总体改进任务的第二阶段。状态 **STOP_ACTION_COUPLED_RIDGE_V1**，原默认与生产E99保持；总体研究继续。

先在E118旧全H真实K1/K100响应上检验冻结8邻居关系。真实hub去均值响应差相对节点置换小22%–29%，双集双K通过结构门；GT10 Profile未通过全部门。这支持动作侧关联试验，不等于查询可预测性或性能提升。

E122沿用冻结四折、单位raw-query与全H效用目标，以训练查询上的动作预测函数图能量正则，闭式求解α10、β1，无调参。主候选FunctionSmooth对照Independent、同谱PermutedFunction、仅诊断CoefficientSmooth及Default/GlobalCost；不使用E121状态或扩展旧表。结构筛选看过整批响应，外折仍为历史开发，旧graph-only成本未计新路由。

主候选ΔR1/R100为Web−0.1709/−0.1182pp、Y−0.2197/+0.0139pp；对应旧图时间增加5.14%/2.62%、9.83%/7.15%。等K效用u×100为−0.5326/−0.9519，98.75%描述区间均负。正确图优于独立模型，但没有双集稳定胜过置换图，全部必要门未通过。平均MSE小幅下降而所选动作仍被过高估计，不以局部结构或微小Y K100召回正值晋升。

理论明确响应平滑只控制查询协方差度量，不自动控制欧氏参数差；给出闭式谱解、条件偏差方差和选择误差桥。多任务图正则、输出核本身已有前作，不包装为原创。动作集合不变、原NSG与主搜索不改。

64个ridge拟合头、16个均值头，训练与统计10.391秒；独立核验4.770秒。98304动作/294912值、144谱模式直接解、205文件身份检查通过，最大差8.89e−15。0新ANN/NSG/GT/搜索图/QPS；同一agent独立实现审计。停止本版，不调α/β/k/模型续跑，其他控制不能事后晋升。

原件：[完整报告](../entry_method_exploration/20260922_until2200_improvement_v1/stages/e122_action_coupled_ridge_v1/report.md)、[协议](../entry_method_exploration/20260922_until2200_improvement_v1/stages/e122_action_coupled_ridge_v1/protocol.md)、[理论](../entry_method_exploration/20260922_until2200_improvement_v1/stages/e122_action_coupled_ridge_v1/theory.md)、[结果与门](../entry_method_exploration/20260922_until2200_improvement_v1/stages/e122_action_coupled_ridge_v1/results/information.json)、[独立审查](../entry_method_exploration/20260922_until2200_improvement_v1/stages/e122_action_coupled_ridge_v1/reviews/independent_audit.json)、[前置动作局部性](../entry_method_exploration/20260922_until2200_improvement_v1/research/action_response_locality_v1/report.md)。
