# E245 COCO B64 扩训练与多预算遗漏监督

E243 教师与编表合同在 COCO 原 raw-IP 底库、E229 原图、GT10 hard、SPAN4 上重跑。冻结原 E183 16,000 条及前 6,144 个公共查询源组中筛出的 4,096 条额外训练。源组和向量精确字节避开确认和原拟合。使用原 exact GT，20,096 条真实训练查四档 L。More64 取 L200 真遗漏，多档 Mixed64 合 L176/192/208，Mixed52 截多档表最远一路。确认用 E229 原 3,072 个源组，查询和确切 GT 曾用于早期公共研究。

真 K100 90 点、180 个完整 CPU15 单线程批次。97% 门槛，B32 L216 为 2,387.7 QPS，老 B64 L204 为 2,428.6。More64 L200 的 97.0684% / 2,462.0 高 1.37%。Mixed64 L196 97.0254% / 2,488.9，较老 B64 +2.48%（慢遍仍 +2.31%），较 B32 +4.24%。Mixed52 同 L 97.0013% / 2,488.3，较老 B64 +2.46%。在 L196，多档完整表实际精算 171.82，老 B64 161.30。Mixed52 161.32，实际精算相当，召回从 96.8929% 到 97.0013%。多档版同 L QPS 中位比老 B64 低 0.24%，曲线收益由候选质量和较小 L 获得。

首次离线摘要误用了上一数据库的 75.5% 目标而结束。计时批次和返回已全部完整。按预先协议的 97% 重作聚合，保留首次部分评分及恢复说明。

[完整报告](../entry_method_exploration/20261123_coco_b64_multibudget_training_v1/report.md) · [协议](../entry_method_exploration/20261123_coco_b64_multibudget_training_v1/protocol.md) · [训练划分](../entry_method_exploration/20261123_coco_b64_multibudget_training_v1/models/train/roles.json) · [逐点](../entry_method_exploration/20261123_coco_b64_multibudget_training_v1/analysis/points.csv) · [封存](../entry_method_exploration/20261123_coco_b64_multibudget_training_v1/seal.json)
