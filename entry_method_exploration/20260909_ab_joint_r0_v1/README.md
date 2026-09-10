# A+B 联合方向：R0 理论更新

状态：`R0_THEORY_REFORMULATED_DESIGN_ONLY_UNRUN`。

本目录记录 2026-09-09 对方向 A、B 的联合重构。用户指出，先前 R0 把“组成部件是否首次出现”当成了整体方法原创性的近似必要条件，标准过严；GATE 等系统也由已有聚类、表示学习和图索引部件构成，其贡献来自新的 ANN 问题定义、约束耦合和端到端机制。经重新审视，当前结论改为：

> **“可路由性约束的入口—表示联合设计”具有可辩护的条件性方法／系统原创性；其原创性候选位于 Fast 可恢复、固定容量的 flat slot/action codebook，以及 frozen-graph、finite-L 真实搜索效用下的入口动作与受限分区共同设计，而不在 maxout、affine、cost-sensitive loss、portfolio 或 MIPS 任一单独部件。**

- [`theory.md`](theory.md)：最新问题定义、数学对象、A/B 新分工、原创性边界、affine 约束及验证门槛。
- [`state.json`](state.json)：机器可读状态和全部未运行标志。
- [`source_manifest.json`](source_manifest.json)：本轮理论更新使用的本地证据与外部一手来源。

原独立版本 [`A R0`](../20260909_a_r0_v1/README.md) 与 [`B R0`](../20260909_b_r0_v1/README.md) 保留当时组件碰撞审计和未执行协议，现均视为被本联合版本取代的历史记录。它们的“关闭／待关闭”不再约束本联合方向，也不能改写为实验失败。

本轮只更新理论和文档状态：没有实现 trainer/router/index，没有生成新标签，没有训练模型，没有启动 ANN 搜索，也没有访问 validation/held-out。下一步须先把 `theory.md` 收敛成独立、可批准的最小协议；目录和公式本身不构成性能或首次性证明。
