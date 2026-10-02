# 167 有限搜索响应与目标访问成本研究

日期2026-10-02；用户授权理论/方法探索并阅读相关论文至13:00（UTC+8）。本轮理论研究已于13:00结束并封存。最新真实性能仍166，默认Web GT10-soft-t1/Y GT10-hard、生产E99保持；旧9月30日runner和22:00计划不恢复。

166性能时钟来自共享span+batch4研究核、并回归原E99输出；本轮引用它只说明历史控制与成本量级，不宣称生产E99现场QPS。新性能需冻结实际核并共同重测。

## 范围与原件

[独立冻结协议](../entry_method_exploration/20261002_theory_until1300_v1/protocol.md)、[主报告](../entry_method_exploration/20261002_theory_until1300_v1/report.md)、[原论文实读清单](../entry_method_exploration/20261002_theory_until1300_v1/literature_manifest.json)。仅理论/原文/源码/旧已曝光ID及响应；0新真实ANN/NSG/GT、训练、构图、未曝光query与正式性能。根四文档事前完整快照及SHA/size身份保留。

## 当前研究结果

- [搜索响应条件](../entry_method_exploration/20261002_theory_until1300_v1/search_effect_theory.md)：严格共同评分序/合法行/自然展开下，发现集top-L不变量；全局前L安全闭包及来自outside-expanded边界的精确发现分解；合法同pool状态的返回等价但费用不等价；双动作差分支持；native区间充分条件。原GTK排序一致、评分路径/tie/停止条件显式，未知真实条件不冒充满足。ICML2020诱导子图、SPD及BQ-NCO直接前作均核对，不宣称独立原创性或免费online特征。
- [只读三桶核算](../entry_method_exploration/20261002_theory_until1300_v1/bucket_feasibility.md)：Web/Y物理M均值107.330/86.837、unique82.121/85.385；旧近似TargetBank slot覆盖33.765%/45.728%。Web主R1旧50次救回40次选点桶外，不能继承旧收益；不是新精排选择/Recall/QPS预测。8192行/12点、95输入身份经第二实现核验。
- [访问前作与native合同](../entry_method_exploration/20261002_theory_until1300_v1/access_literature.md)：学习粗路由、精确MIPS、条件计算、距离memo、角/残差剪枝有直接前作；原近似队列保真与全bank argmax不同。Panorama/Tribase实现的heap/阈值变化不能给原ef10输出保真。
- [完整成本条件](../entry_method_exploration/20261002_theory_until1300_v1/full_cost_conditions.md)：memo基础四控制保留，另补两路UpperHandoff简单控制，胜更快默认需S_target>D+max(0,S_default,S_handoff)，防止劣化默认制造假成功。旧Web R1/L1000 D=23.282μs/query只说明量级，不是未来时钟证书。真实重复trace与完整wall缺失；[局部复用接口](../entry_method_exploration/20261002_theory_until1300_v1/memo_interface_note.md)已确定一次上层终点重算，未计时。
- [规约/概率边界](../entry_method_exploration/20261002_theory_until1300_v1/metric_transfer_limits.md)：入口hop上界不等实际效用；IP-to-L2保排序不保原图导航/近似效用/native bits；局部RoutingTest概率不直接成为query Recall保证。
- [旧终局返回类](../entry_method_exploration/20261002_theory_until1300_v1/response_equivalence_protocol.md)：36全点方法对、114输入身份与独立代理第二实现核验147456行/828字段。Web主R1 Default3/Target3998同返回中2887图NDC不同，另20same hits但返回不同。支持返回/工作量标签分开，不是合法中间pool汇合率/逐query wall/跨query迁移。
- [历史缺口](../entry_method_exploration/20261002_theory_until1300_v1/history_gap_audit.md)：旧真实组合奖励/成本敏感监督已经执行；E164关闭E126旧缺口。E116槽绑定H外ID也随query变化；未覆盖组合仅为直接20Kraw目标访问再与原rank1/2联合，不是首次H外/联合/query-specific学习。

## 候选状态与停止边界

[最小具体方案](../entry_method_exploration/20261002_theory_until1300_v1/candidate_gates.md)：优先保留输出保真memo成本隔离；确定性原阈值拒绝、固定三桶、raw-target联合动作依次HOLD。无真实访问/原生parity/完整wall或真实联合反馈前不GO；没有运行命令、后继实验授权、默认替换或训练模型。构建费用仍为附属事实。

数学穷举/第二实现通过只是研究正确性审查，没有证明真实库证书机会或性能改善。本轮已于13:00完成理论交付并停止自动推进，性能主目标未完成；后续真实实验须用户明确授权。旧协议/停止门/负结果与全部产物保持。

补充[直接入口GATE](../entry_method_exploration/20261002_theory_until1300_v1/latest_entry_literature.md)与[Query-scaled/PSP/MAG](../entry_method_exploration/20261002_theory_until1300_v1/latest_mips_literature.md)原文/release核对；共20篇原论文相关章节实读。GATE为已适配前作，PSP/MAG改变图/metric/停止前件，均未提供新执行GO。
