# 89｜GATE实用复现检查与新评测口径

2026-09-15。用户先要求检查 GATE、再告知新 Deep/SIFT/GIST 应选 GT10-hard 还是 soft，并说明接受合理适配、不要求严格逐代码复现。本轮是 E96 后续审查，不增加训练/性能实验编号。完整证据见[审查报告](../entry_method_exploration/20260915_gate_reproduction_audit_v1/report.md)。

重新核验40项源码/依赖SHA、三套 checkpoint/W 前向及批/单条独立性、训练缓存与标签、192点576轮的计时算术。发现沿用release的负样本阈值会与正例重叠：Web/Y/LA训练query875/449/799条，实际抽样triplet冲突2525/1783/2630条，占0.4044%/0.2495%/0.3716%。512入口中10成功且hop均1的合成例复现两集合完全相同。后继应先做neg减pos，再过滤和构造triplet；未重训练，E96模型/源码/原始结果和seal不改。

核心真实hub→拓扑特征→真实路径监督→对比训练→小HNSW三入口保留。作者HBKM/损失/Transformer维度/搜索初始化和论文有差异，按本次标准不要求照搬错误。所有1536子图触及1000节点上限是需披露的特征限制。缓存monitor上 learned 的最小hop入口准确率比raw低，但单入口GT1成功率略高；这些不是部署Recall@1/QPS，也不能证明修标签后必然有收益。

新三集建议GT10-hard统一主方法，soft-t1仅一份预锁辅助对照；没有证据证明新L2/Recall@1/100上任何变体已是赢家。旧Web软/Y硬默认和LAION的E96选择不回改。新开发与正式评测只测Recall@1/100，分别K1/K100真实计时，历史Recall@10保留。

当前三集旧settings均训练/测试同查询路径；规范索引路径无现成NSG；SIFT所谓10M文件头/长度对应11164866行。新版本须先明确split/base/L2/GT，再运行。此次0新训练/ANN/图/GT/QPS，只有既有缓存分析与合成前向；没有打开三集完整测试GT评估模型。

证据：[缓存与模型核验](../entry_method_exploration/20260915_gate_reproduction_audit_v1/results/cached_checks.json)、[冲突标签及最小复现](../entry_method_exploration/20260915_gate_reproduction_audit_v1/results/label_overlap_verified.json)、[身份/计时](../entry_method_exploration/20260915_gate_reproduction_audit_v1/results/identity_and_timing.json)、[接入元信息](../entry_method_exploration/20260915_gate_reproduction_audit_v1/results/dataset_readiness.json)。
