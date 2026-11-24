# E228 B64 全精算异窗密集复测

随 E226 的实际全精算 B64 局部优势，用户授权在另一批真实查询上密测。冻结 E226 的原版 B32、B64 表、底库、图、GT10 路由、SPAN4 与原生精算合并。每路 B64 保留原 B32 前缀，三行并集去重和排除主返回之后全部精算。

COCO hard、WebVid soft-t1，真 K100，各 3,072 条。选择从物理行 6144 开始，COCO 匹配源组，WebVid 跳过两条与旧查询窗精确重复的记录后补齐。WebVid 另与归档画像拟合的全部 20,000 条向量比对，精确字节重合为零。此公共查询窗已在历史上用于其他实验，独立于 E226 的 B64 正式窗和拟合/校准窗。固定 L168–244 步长 4，共 80 点、160 批 CPU15 单线程。两遍输出逐字节一致。20,480 条额外标量合并核验，另确认 E226 原窗的 12 组两方法前 256 条输出一致。COCO 和 WebVid 对 E227 同物理查询，11/11 档 B32 的四份载荷一致。

同 L，B64 在 COCO 多精算 73.60 个候选，WebVid 多 93.47 个，完整 QPS 中位数分别下降 2.77%、2.90%。召回分别增加 0.1833–0.3073、0.6989–0.8135 个百分点，40 个同 L 配对均未损失原正确成员。达到同一固定召回目标时，COCO 7/7、WebVid 5/6 个双边达标目标均值更快，慢遍仍快 6/7、4/6。各集 16/16 个召回重叠点在 B32 折线右侧，折线用于描述。COCO 97.0% 目标 L216→204 报 +1.40% 完整 QPS。WebVid 75.5% 目标 L220→208 报 +2.70%。WebVid 72% 两臂卡网格下限 L168，B64 −2.97%。全精算 B64 保留为已测两集 K100 的条件配置。

[报告与图](../entry_method_exploration/20261122_b64_full_confirmation_v1/report.md) · [协议](../entry_method_exploration/20261122_b64_full_confirmation_v1/protocol.md) · [固定目标](../entry_method_exploration/20261122_b64_full_confirmation_v1/analysis/targets.csv) · [封存](../entry_method_exploration/20261122_b64_full_confirmation_v1/seal.json) · [修改前快照](../entry_method_exploration/20261122_b64_full_confirmation_v1/source_before/)
