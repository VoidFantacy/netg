# 50. E61 全fit遗漏GT成员画像

2026-09-13，`COMPLETE_MISSING_TARGET_DEVELOPMENT_NO_CAL_GO`。E60支持空后，实际实现并验证完整P-fit20K遗漏GT成员重构，固定lambda0.5与同query同遗漏数的随机目标对照。所有query总质量保持1，原hard/soft归属、H815/821、NSG/IP/GT不变。E33完整40K原P基线标签显式复用，原A0/P字节恢复后冻结六画像；不同于E08全H赢家、E09单入口signed residual和E22自由映射，不作新颖性声称。

| 数据集 | missing fit/cal/audit ΔRecall pp | cal增益/损伤hits | cal零命中数 | sham fit/cal/audit ΔRecall pp |
|---|---|---|---|---|
| WebVid | −0.1020/−0.3906/+0.0195 | 49/89 | 22→25 | −0.0885/−0.0098/−0.1367 |
| Yandex | −0.0260/−0.1465/+0.0684 | 13/28 | 16→19 | −0.0160/−0.2344/−0.0488 |

按预锁cal净正、失败数不增、totalNDC≤+1%规则，两集保留原P。audit小正值不回改选择。missing改变全部画像、fit入口8284/5602条，但fit已净负；因此不是仅跨split迁移弱。两模型位移不等，真实遗漏身份也未显示一致效果，不追加lambda或sham seed网格。

真实missing在fit原全命中群分别损失191/224个命中，其中14/20条变零命中贡献140/200损失；原零命中群救回45/32条，增222/277命中。m=0/10时自己的归属按公式不变，但共享画像/图仍改其入口。部分遗漏群净−235/−105；成员恢复/丢失与query净gain/loss分开。这些分组尚不等于评分或拓扑的因果归因。

新增28484 NSG/133056 HNSW/6build，原生阶段34.190s含加载；画像assignment/聚合8.617s、独立流式验证15.799s，旧标签构建成本与身份hash另计。132288集合与mask评分、44096原基线路由、384三路parity、六图字节和全部缓存通过。CPU15实际线程1串行，0新GT/梯度更新/正式QPS；原默认保持。fit/cal/audit都历史暴露，E34最终validation不作为输入/反馈。

下一最小控制可固定当前missing画像/图，交叉S=(W,G0)、T=(P,G)检验原全命中群关键损伤来源；需独立版本/前瞻协议并回查E48/E54，只适用于该闭式全画像端点，不根据聚合表自称因果。E61本身不含S/T。

[报告与图](../entry_method_exploration/20260913_until2100_v1/stage2_missing_targets_v1/report_v2.md)、[协议](../entry_method_exploration/20260913_until2100_v1/stage2_missing_targets_v1/protocol.md)、[全部点](../entry_method_exploration/20260913_until2100_v1/stage2_missing_targets_v1/results/points.csv)、[cohort](../entry_method_exploration/20260913_until2100_v1/stage2_missing_targets_v1/results/fit_cohorts.csv)、[固定选择](../entry_method_exploration/20260913_until2100_v1/stage2_missing_targets_v1/results/selection.json)、[输出验收](../entry_method_exploration/20260913_until2100_v1/stage2_missing_targets_v1/reviews/verification.json)、[画像独立验收](../entry_method_exploration/20260913_until2100_v1/stage2_missing_targets_v1/reviews/profile_verification.json)。

2026-09-13接续修正：E61报告v2只澄清复用行数为E33 fit40,000加E60开发4,096，合计44,096；原报告/源码/封存保留，指标和门未改。S/T控制现已由[历史51](51_missing_profile_factorial.md)独立完成，不回写E61原协议。
