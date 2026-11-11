# E194 残差后端等价省费与查询稳定性

2026-10-30用户授权“先优化和稳定方法，开始实验”。[协议](../entry_method_exploration/20261030_residual_optimization_stability_v1/protocol.md)在新性能前固定：COCO/WebVid、public及角色去重confirmation各2048条、真实K1/K100，256点/768完整T1，另20资格点，均完成并通过原生及stdlib核验。默认E99 GT10保持。

OPT-B32用固定512槽哈希保留三hub候选次序，并简化K1严格合并；OPT-SQ保持pool/2048码/96精算，只改连续数组Top96选择。全部56配对点的六数组、候选次序和访问等价。4/56点通过>=2%完整QPS且三轮配对同向，2/28配置在两窗均通过。保留2个跨窗口均通过的具体优化配置；其他配置保留原始效应，不默认推广。

| 数据 | 优化 | 通过点 | 两窗均通过配置 | 完整QPS增幅中位数 |
| --- | --- | --- | --- | --- |
| coco | OPT-B32 | 2/16 | 1/8 | +0.87% |
| coco | OPT-SQ | 0/12 | 0/6 | +0.22% |
| webvid2_5m_light_v1 | OPT-B32 | 2/16 | 1/8 | +0.62% |
| webvid2_5m_light_v1 | OPT-SQ | 0/12 | 0/6 | -0.11% |

本轮只证明这些组合实现的实测费用，不把全部QPS变化归因于单一操作。GT10/B32共同11档L控制，原SQ独立保留；是否被强控制覆盖另见全部点。确认query来源、GT、质量区间、实际费用、局限见[完整报告](../entry_method_exploration/20261030_residual_optimization_stability_v1/report_zh.md)。配对和跨窗表保留全部配置，不只展示阳性。无新图/画像、无新门拟合或默认替换。

新产物/root/acsg-e194-storage经storage链接，实际返回/三轮hash/完整wall及独立实现收据保留。旧E193科学封存不改，旧可变根文档通过source_before/SHA桥接。固定范围已收口，无待恢复队列，无新PDF。
