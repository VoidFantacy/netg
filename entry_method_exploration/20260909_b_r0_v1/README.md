# 方向 B：R0 评估包

状态：`CLOSED_AT_R0_NOVELTY_COLLISION_UNRUN`。

> 2026-09-09 后续：该状态只关闭本目录的“H 外64列＋fixed-m＋tree swap”独立版本。用户随后指出组件碰撞标准过严，A 与 B 已重构为[可路由性约束的入口—表示联合设计](../20260909_ab_joint_r0_v1/README.md)。新版本先在现有 H 内解耦 slot 与 entry；它不是直接重启本草案。本目录继续保存原决定和未执行身份。

本目录把 `s-target.md` 中第一个方向 B 收敛为一个可审查、可证伪的版本。用户于2026-09-09选择因新颖性碰撞不投入该pilot，并转向方向A。这个终态记录的是R0研究取舍，**不是实验`NO_GO`**；这里只完成只读证据核查和协议草案，**没有实现新训练器、没有生成新候选或标签、没有启动 ANN 搜索，也没有访问 validation/held-out**。

- [`assessment/assessment.md`](assessment/assessment.md)：R0 结论、前作碰撞、唯一保留的假设和用户关闭决定。
- [`assessment/protocol_draft.md`](assessment/protocol_draft.md)：未获批准、未执行的pilot参考草案；其中接口均为待实现合同，不是现有命令。
- [`source_manifest.json`](source_manifest.json)：本次判断所依赖的当前本地文件身份和一手外部来源。
- [`state.json`](state.json)：机器可读终态与全部未运行标志。若以后重开，必须由用户明确授权并建立新版本，不能把本目录改写成已执行版本。

该版本最初只把“B在R0因新颖性碰撞关闭、未运行，接续A”的时点状态同步到根目录。当前计划以最新 [`s-target.md`](../../s-target.md) 和[联合理论](../20260909_ab_joint_r0_v1/theory.md)为准；本版本仍没有真实实验。
