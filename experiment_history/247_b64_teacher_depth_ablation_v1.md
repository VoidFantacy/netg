# E247 WebVid 同样本单档与多档漏点监督

冻结 E243 24,192 条同样训练及原 GT。L176、192、208 的单档表由原生实际训练主包重编，L200 及混合直接沿用 E243。用同一 E226 联合贪心编译，从原 B32 有序前缀扩到 64。老 B64、B32 和五个新表在 E237 的异源确认窗 3,072 条真 K100，12 档 L、84 点、168 个完整 CPU15 单线程批次。各法原图、三入口、raw-IP、候选数上限、去重和精算相同。共同 L 的历史对照返回全部按原始字段校验。

各在线 L 最佳的单档均是 Single176。Mixed64 对其净命中变化为 −16 至 +31 个，五档为负、一档持平、六档为正。主要 75.5% 两者都用 L208，Single176 75.5863% / 1,614.0 QPS，Mixed64 75.5915% / 1,619.5，多 16 个成员。同期最快的单档为 Single208 1,617.4 QPS。相对老 B64 L216，所有新增训练表在 75.5% 快 2.99% 至 3.39%。WebVid 的混合额外提升很小，充足训练与单低 L 已可兑现主要收益。

E243 用发布 SPAN4 重算原有 16,000 条的 L200 训练主结果，IDs、距离、入口和画像四种载荷与 E183 原版本逐字一致。新增训练样本对单 L200 扩表是独立于训练核变动的比较。

[完整报告](../entry_method_exploration/20261123_b64_teacher_depth_ablation_v1/report.md) · [协议](../entry_method_exploration/20261123_b64_teacher_depth_ablation_v1/protocol.md) · [原训练主包核对](../entry_method_exploration/20261123_b64_teacher_depth_ablation_v1/analysis/original_training_l200_parity.json) · [同期逐点](../entry_method_exploration/20261123_b64_teacher_depth_ablation_v1/analysis/points.csv) · [封存](../entry_method_exploration/20261123_b64_teacher_depth_ablation_v1/seal.json)
