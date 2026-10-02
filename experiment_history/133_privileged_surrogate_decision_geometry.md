# 133 特权服务代理与真实决策误差分解

2026-09-22，E124停止后的只读诊断，0新训练/搜索/GT/QPS，默认保持。

19k对3k在Web/Y真实K1/K100四格的语义MSE、中心服务MSE及特权代理决策损失均改善；真实效用却两升两降、等K双集下降。对原特权动作a*及学生动作a，严格分解u(a*)−u(a)=g(a*)−g(a)+(u−g)(a*)−(u−g)(a)。残差对比可为负，不是非负或因果份额。服务表先按目标区域平均再回到query，不自动恢复查询条件效用；特权策略有正价值不等于其评分对学生可达动作已校准。

合法概率MSE反例、共同分数偏移不变性、K100精确成员池化反例通过。全部32768条模型-query-K分解、2048标量评分及原动作恢复；独立3184检查/219文件身份通过。分析4.615秒、附加审计14.844秒。初版仅动作参照下标错误被首折断言阻止，v2按原arms名称索引，不改旧模型/标签/门。

理论区分GT10归一化加权方向与后验式区域估计，明确服务代理偏差及计算意义的特权；核对广义蒸馏和SPO校准原文条件，不提名更大网络或换损失。证据：[报告](../entry_method_exploration/20260922_until2200_improvement_v1/research/semantic_decision_geometry_v1/report.md)、[推导](../entry_method_exploration/20260922_until2200_improvement_v1/research/semantic_decision_geometry_v1/theory.md)、[一手文献](../entry_method_exploration/20260922_until2200_improvement_v1/literature/privileged_surrogate_scope.md)。
