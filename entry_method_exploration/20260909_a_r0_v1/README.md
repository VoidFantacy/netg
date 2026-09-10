# 方向 A：R0 评估包

当前状态：`SUPERSEDED_BY_AB_JOINT_REFORMULATION_UNRUN`。  
历史状态：`R0_NOVELTY_NO_GO_AWAITING_USER_DECISION`。

> 2026-09-09 更新：用户否决了“组成部件已有便把整体方法降为低原创性”的过严二选一。本目录继续保存 standalone per-hub facet v1 的组件碰撞审计和未执行草案；当前 A 已与 B 重构为[可路由性约束的入口—表示联合设计](../20260909_ab_joint_r0_v1/README.md)。本目录不再是当前计划，也没有被改写成实验失败。

本目录把 `s-target.md` 中方向 A“真实效用驱动的多面入口索引”收敛为一次可追溯的 R0 决策。结论是：**若目标是强算法原创性，建议在 R0 关闭；若接受较低原创性的 systems/empirical 定位，可由用户明确重开一次严格有界的表示诊断。** 这不是性能 `NO_GO`，因为本轮只做了历史、源码和一手前作核查；没有实现训练器、没有生成新标签、没有训练模型、没有启动 ANN 搜索，也没有访问 validation/held-out。

- [`assessment/assessment.md`](assessment/assessment.md)：新颖性裁决、历史证据、前作碰撞、唯一仍可检验的系统假设及强对照。
- [`assessment/protocol_draft.md`](assessment/protocol_draft.md)：仅在用户接受 systems/empirical 定位后才可能重开的参考协议；未获批准、未执行，其中接口名不是当前命令。
- [`source_manifest.json`](source_manifest.json)：本次判断依赖的当前本地文件身份和一手外部来源。
- [`state.json`](state.json)：机器可读状态、未运行标志、成本算术及当前唯一待决项。

本版本当时提出的关键选择是：

1. **按建议关闭 A 并转向 C 的 R0**；或
2. **明确接受“算法原创性较低”的定位，重开一个 systems/empirical 有界诊断**，并承诺在同标签、同总面数和同部署成本下实现普通 MProtSVM/maxout、GAMM/adaptive-LVQ 式通用增删、几何多原型、loss×allocation 析因、v4 树及 Fast 对照。

该二选一现已由新的 A+B 联合重述取代。旧草案仍未获执行授权；后续若继续，须从联合版本另建批准协议，不能把本 R0 目录改写成已执行版本。

本目录最初只把“A 的 R0 已完成并等待上述选择”的状态同步到根目录；该时点记录继续保留。当前计划以最新 [`s-target.md`](../../s-target.md) 和[联合理论](../20260909_ab_joint_r0_v1/theory.md)为准。
