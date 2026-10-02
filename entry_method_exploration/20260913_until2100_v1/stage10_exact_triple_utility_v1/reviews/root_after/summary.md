# ACSG 当前结果摘要

2026-09-13，第4串行会话完成E69精确画像前三真实NSG诊断。Yandex通过有限辅助质量接续门，WebVid未通过；原默认未替换，整日21:00目标未完成，E34最终validation仍待晚间冻结对照。

E69固定历史aux7952/L128。精确mode相对精确P：Web净−109命中（−0.1371pp）、失败+7，两半−86/−23；Y净+132（+0.1660pp）、失败−10，两半+32/+100。相对原approx P：Web+85/失败−6、Y+97/失败−8。相对原approx mode：Web+191、Y+48。精确P本身Web改善194而Y损失35，画像排序更准不保证NSG更好。

38,942新NSG含全baseline plain/count回放、3535唯一补缺plain/count与64原kernel对照；31808逻辑精确结果中28102复用旧缓存、171别名。79520返回独立集合与mask评分、15904原baseline字节恢复、全部plain/count/reference及线程1验收通过。0HNSW/构图/新GT/梯度/QPS，原生操作37.904秒不是完整在线wall。后继仅一次ef10→30受控比较尚未运行。

E66双集原开发门失败保持；Y fit/aux局部正值保留。E67同批55点275wall：Y五L有4个Recall正点且失败不增，L64 QPS−2.298%；Web质量混合且QPS中位五点均负。其余多数QPS交叉范围跨0，无稳定整体改善证据。E65另45点225wall保留，今日100个历史开发性能点不得跨批拼方法曲线。

P-fit含旧train/monitor；cal/audit/aux均历史暴露，辅助选择反馈计训练。E69没有使用E34最终validation或held-out。E68近似缺口及两条相反失败案例的事实保持，E69只为L128新增反事实，不推断其余L。

[E69报告与图](entry_method_exploration/20260913_until2100_v1/stage10_exact_triple_utility_v1/report.md) · [E67完整wall](entry_method_exploration/20260913_until2100_v1/stage8_multimode_wall_v1/report.md) · [下一阶段](s-target.md)。
