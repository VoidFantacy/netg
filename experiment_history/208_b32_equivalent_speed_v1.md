# E208 四集 B32 等价优化

2026-11-20 完成。COCO、Flickr30k、WebVid、Yandex 共四集，各取公共最前3,072条。真实 K1/K100，L100/200/400，96个点、192个完整CPU15单线程批次、589,824次正式查询，每点两遍。48个优化点均与原 B32 逐字节一致。9个点通过局部正向条件，0个点通过镜像下降条件。连续两个预算达到正向条件的组合有3个，包括WebVid K1 B32-PF4、WebVid K100 B32-PF4、WebVid K100 B32-BOTH。默认 E99 GT10，原 B32 作为固定补点强对照。

PF4 提前4个候选预取原向量，SKIP 的真实 K100 阶段仅在全候选未超过原门槛时免去合并，BOTH 两项叠加。验证每组原 B32、优化版本位级等价，公共GT在结束后评价。同批原GT10/B32、四集完整壁钟、32个资格、前缀旧包复核、全部局部正负例均保留。

[报告](../entry_method_exploration/20261120_b32_equivalent_speed_v1/report.md) · [协议](../entry_method_exploration/20261120_b32_equivalent_speed_v1/protocol.md) · [对照](../entry_method_exploration/20261120_b32_equivalent_speed_v1/analysis/matched_deltas.csv) · [状态](../entry_method_exploration/20261120_b32_equivalent_speed_v1/state.json) · [验收](../entry_method_exploration/20261120_b32_equivalent_speed_v1/reviews/delivery_validation.json)
