# E174：M5 残差候选作为区域入口

2026-10-10，状态：RUNNING。原 M5 没有放弃；新增机制针对原冻结候选支持有限的问题，从这些候选的原 NSG 一跳邻居中发现新 ID。跨模态性质目前体现在原残差表使用查询侧漏召回监督；一跳扩展器本身是通用操作，不能据此宣称跨模态独有创新。

本轮目录：[20261010_m5_residual_regions_v1](../entry_method_exploration/20261010_m5_residual_regions_v1/README.md)。[协议](../entry_method_exploration/20261010_m5_residual_regions_v1/protocol.md)与四个 job 在新查询响应前锁定；不新增 TRAIN、不重训 GT10 或 M5、不改原图/度量/数据。源表、图、数据共109项身份通过校验；原图设备号迁卷差异由当前全文件 SHA 闭合。编译和两集72个 smoke点通过，GT/M5 的112个原始文件与 E173 原二进制逐位一致（16查询/点）。这些是运行前资格，不能代替正式结果。

正式范围为 WebVid L800/1000、Yandex L1000/1200；K1/K100分别真实搜索。confirm_a 4096 queries×九方法×四KL，共72点；confirm_b4096×五方法×四KL，共40点。每点三轮完整T1/CPU15 wall，共112点336批。GT、原M5、M5REG96、MFREG96、GEOREG96在两个角色都有；REG24/FIRST96/MFDIRECT/GEODIRECT仅pilot。

完整 M5 C≤24 保留；每路由行在 C 中选最佳种子（至多三seed，按路由顺序去重），物理邻居槽 round-robin，排除 main-vt已见/C/X重复；额外评分X≤24或96并严格合并。不继续主图搜索，不将已见称作已展开，不把不同路由行称为已证实不同盆地。全量独立 replay 重建候选、评分词和线性合并；全量 trace 记录 C/X/seed ID，NDC/count仅预锁256抽样。

正式质量与性能、真实表外救回、费用、独立结果审查和默认决定待全部采集完成后填入。默认继续 GT10，最新已完成性能仍为 E173。本版跑完预锁范围后给出保留/停止决定；不从角色反馈追加参数。历史其他队列和TRAIN超额事实保持。
