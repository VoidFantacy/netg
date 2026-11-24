# E220 Q8 等价提速与按需扩表回放

2026-11-21 完成。COCO K100、WebVid K1/K100 的 11,952 状态全部通过原精算和返回字节检查。两种改动分别为错误构造移入失败分支、前至多16项局部排序。合并版独立补点回放每条省 3.14 / 5.36 / 8.44 微秒。

两集 K100 共 80 点、160 个 CPU15 单线程完整批次。COCO K100 代表 L224 的 Q8-fast 对最快达标控制 -0.75%，相邻 L232 +0.06%。WebVid K100 代表 L232 的 Q8-fast 对最快达标控制 +0.61%，相邻 L224 +0.93%。WebVid K100 扩表诊断只跳过 11.69% 的四表扫描，校准窗命中数与 B32-fit L192 持平。

[报告](../entry_method_exploration/20261121_q8_equivalent_speed_v1/report.md) · [协议](../entry_method_exploration/20261121_q8_equivalent_speed_v1/protocol.md) · [达标结果](../entry_method_exploration/20261121_q8_equivalent_speed_v1/analysis/matched.csv) · [状态](../entry_method_exploration/20261121_q8_equivalent_speed_v1/state.json)。
