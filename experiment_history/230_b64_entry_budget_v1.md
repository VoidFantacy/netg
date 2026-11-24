# E230 WebVid B64 入口配额

上轮 E229 公共留出做尾部覆盖诊断，固定原 B32 有序前缀。真实 K1 新 B64 三路皆 56，真实 K100 用保存在 GT10 路由结果的画像距离，最近两路各 64、最远一路 40，原路由迭代与候选原生精算合并规则保留。K100 正式另测均匀 B56 作为等名额控制。用户明确要求曲线只画 B32、老 B64、新 B64 三条。

确认窗为 WebVid 3,072 条历史公共查询，剔除内部一条重复向量，与 E229 诊断窗及原画像拟合向量精确字节互斥。CPU15 真单线程两遍，K1 三臂与 K100 四臂共 105 点、210 批。完整计时后用按行绑定的原官方 GT100，K1 取首名。原生校验 26,880 条额外查询，逐条核候选子集和标量全排序。在共同物理行核验历史 B32 和老 B64 输出，详情见附件。

K100 新 B64 的 18 档同 L 输出均优于均匀 B56，平均精算差 −0.03 个。L208 分别精算 163.76 和 163.80 个，正确成员差 +68。对老 B64，新版两种 K 平均分别少精算 23.69、23.50 个，同 L QPS 差中位数 +0.81%、+0.75%。K100 固定目标上新版 7/10 个比老版快，慢遍对快遍也为 7/10。按实际召回重叠折线，新版与老版在 K100 的速度中位差约 +0.01%，K1 的 10 个折线重叠点均由老版领先。WebVid K100 在 72% 目标新 B64 相对 B32/老 B64 快 4.03%/0.96%。在 75.5% 分别 +2.53%/−1.40%，两者是同门槛实际最快点。按目标保留两版 B64。

[报告与图](../entry_method_exploration/20261123_b64_entry_budget_v1/report.md) · [协议](../entry_method_exploration/20261123_b64_entry_budget_v1/protocol.md) · [固定目标](../entry_method_exploration/20261123_b64_entry_budget_v1/analysis/targets.csv) · [同 L 救损](../entry_method_exploration/20261123_b64_entry_budget_v1/analysis/same_L.csv) · [封存](../entry_method_exploration/20261123_b64_entry_budget_v1/seal.json) · [修改前快照](../entry_method_exploration/20261123_b64_entry_budget_v1/source_before/)
