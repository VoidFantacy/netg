# E224 B32 与 P64 的逐查询分流

2026-11-22。COCO 真 K100，三路 GT10 入口和 SPAN4 共享。完整主搜索后读取画像和主返回分差，在原版 B32 或 E223 P64 中只走一个分支。以相对原版 B32 的逐查询实际净正确成员数训练。由 E223 第二公共窗 3,072 条按独立身份分成 2,048 fit、1,024 cal，阈值按 L 和先验完整成本校准。正式第三公共窗为历史曾用的 3,072 条，和 fit/cal/其他模型训练身份隔离。计时全部结束才评分。

CPU15 实际单线程，11 档 L、六臂、66 点、132 个完整批次，405,504 次计时查询。67,584 个门状态与实际原版 B32 或 P64 分支返回位级一致，Python 独立门预测和 Recall 复算通过。

L184 线性分流 96.5410% / 2,752.5 QPS，较原版 B32 L192 96.5446% / 2,772.6 QPS 少 11 个正确成员，慢约 0.73%。树门 96.4782% / 2,810.7 QPS，少 204 个正确成员，快约 1.37%。线性 / 树实际开启 85.8% / 53.7%，L184 净增 657 / 464。事后正收益分流可净增 1,038，需 668，属于质量上限诊断。

有限离散网格，线性和树分别有 7/11、8/11 点快于可达标的原版 B32，慢遍仍胜分别为 2/11、5/11。B32 实测召回范围内按连线描述，两个门各有 10 个可比较点，线性 3 点和树 4 点在连线右侧。插值只描述已有测点。原版 B32 仍为补点基线，生产合同按 E99/E211。

[协议](../entry_method_exploration/20261122_p64_residual_gate_v1/protocol.md) · [报告及图](../entry_method_exploration/20261122_p64_residual_gate_v1/report.md) · [正式点](../entry_method_exploration/20261122_p64_residual_gate_v1/analysis/points.csv) · [门控救损](../entry_method_exploration/20261122_p64_residual_gate_v1/analysis/gates.csv) · [实际达标配对](../entry_method_exploration/20261122_p64_residual_gate_v1/analysis/matched.csv) · [状态](../entry_method_exploration/20261122_p64_residual_gate_v1/state.json) · [封存](../entry_method_exploration/20261122_p64_residual_gate_v1/seal.json)
