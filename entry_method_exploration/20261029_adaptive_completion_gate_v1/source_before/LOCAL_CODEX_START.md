# ACSG 当前接续入口

2026-10-29，/data/netg/ACSG。E192共享必要条件与受控重配已完成，默认E99 GT10保持，无待恢复矩阵。分支/HEAD以git实际值为准，近期成果主要未提交。

先读AGENTS、summary、spec、s-target、s-experiment，再读[E192报告](entry_method_exploration/20261029_sharing_necessity_v1/report_zh.md)、[严格推导](entry_method_exploration/20261029_sharing_necessity_v1/theory.md)、[当前池费用证书](entry_method_exploration/20261029_sharing_necessity_v1/analysis/oracle_cost_certificates.csv)、[冻结](entry_method_exploration/20261029_sharing_necessity_v1/freeze.json)、[state](entry_method_exploration/20261029_sharing_necessity_v1/state.json)。

结论：候选支持为零则补全不能增加Recall；固定ID源受训练遗漏交集上界约束。Deep/SIFT当前池即使理想救回，在当前完整费用下仍被同窗口GT10覆盖；不外推未来更快实现。身份共享不是所有块法的必要条件，已有实际源外反例；不否定GT10主搜索。

新三集真实K100同窗口39点/117T1，资格36点另计；七集两K/L200旧包的32重配是离线诊断，不是新QPS。重配0预定，未挑版本。公共test历史曝光，无新盲确认。新数据/root/acsg-e192-storage，项目storage链接。

E191原PDF/科学产物/seal原件不改；其可变根文档原字节在本轮source_before，[迁移收据](entry_method_exploration/20261029_sharing_necessity_v1/reviews/E191_before.json)关联旧SHA。复核旧seal时按该映射读取旧文档，而非把现行根文档当旧字节。

可复制接续：请先只读核当前HEAD与根文档，再读E192证明、完整报告及费用证书。已完成固定矩阵，无待恢复队列。按我本次明确任务继续，区分身份共享、块支持、主搜索效用和完整费用，不自动新测或修改默认。
