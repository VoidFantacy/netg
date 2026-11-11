# ACSG 后续研究问题

2026-10-29。E192固定范围已完成，无待恢复矩阵，默认E99 GT10保持。当前结论读[summary](summary.md)，完整证明与实测读[E192报告](entry_method_exploration/20261029_sharing_necessity_v1/report_zh.md)。

本轮证明候选支持是必要条件，并给出Deep/SIFT当前池在当前费用下即使完美救回也被GT10覆盖的证据；没有证明所有低共享数据集永久无用。后继应针对支持与费用的具体限制，不继续仅优化已经接近上限的池内排序。

## 下一门（提案，未启动）

1. 固定ID源补全先在合法开发query计算遗漏源覆盖上界；源支持近零时不扩大表容量到通过。若换训练源或训练规模，另冻角色与来源，不能沿用旧上界声称新版本不行。
2. 当前池oracle在当前费用下被GT10覆盖的点，后继需实质降低完整费用或改变候选来源。若研究新块源，先审计合法开发query的廉价候选支持，再冻结T1矩阵；只读oracle不是免费线上方法。
3. 若要证明数据分布的共享因果，需另冻生成/采样干预并配平规模、metric、维数、图和标签角色；hub表重配只改变表对应关系，不能改称零共享数据集。保留反例检查和预先固定的结束边界。
4. E191保留点仍需已有B32的密集费用匹配与合法新查询/图确认；本轮没有自动启动该矩阵，已有公共test不能改称盲确认。

[当前池费用证书](entry_method_exploration/20261029_sharing_necessity_v1/analysis/oracle_cost_certificates.csv) · [源覆盖上界](entry_method_exploration/20261029_sharing_necessity_v1/analysis/support_bounds.csv)。当前授权已收口，未来门均未实施；旧科学产物/seal不回写。
