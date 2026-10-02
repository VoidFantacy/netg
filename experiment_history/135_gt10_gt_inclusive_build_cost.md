# 135 GT10包含训练GT的入口层重建成本

2026-09-22完成。原QGT5K+画像20K各集重新生成exact raw-IP top100，当前Web soft/Y hard的H815/821、画像逐位恢复，Micro-HNSW结构及路由恢复；默认、生产与原GT不变。

Web/Y exact GT搜索395.684/1770.125秒，base/GT/H/画像/小图不重叠核心阶段合计403.997/1780.232秒，GT占97.94%/99.43%。CPU0–7、每库池8线程、驻留15线程；整个GT过程2185.114秒、峰值15.338GiB，未清缓存单次测量。不是完整查询QPS，也不含公共NSG、下载、嵌入及历史选型费用；top100用于完整复核，画像实际只用top10，不声称最小标签成本。

50000条GT全部排名恢复；所有H/W、图层级/有序边/标签/向量及50000对路由ID/距离bits/NDC一致。独立Python完整GT比较与两对图序列化解码通过，32小文件身份、大base stat保持。50000新exact GT、100000新ANN、2次当前路由图重建，0NSG/新QPS/新测试来源。前件另有2次原H选择，实际构建另2次，不称零拟合。

支持GT10通过一次性离线监督换取廉价在线表示，并修正“几秒画像=全部构建”的口径；尚未验证低成本标签替代。原始分阶段文件保持历史身份，最终状态由cost_summary和router_complete给出。

证据：[报告](../entry_method_exploration/20260922_until2200_improvement_v1/research/gt_inclusive_build_cost_v1/report.md)、[协议](../entry_method_exploration/20260922_until2200_improvement_v1/research/gt_inclusive_build_cost_v1/protocol.md)、[成本](../entry_method_exploration/20260922_until2200_improvement_v1/research/gt_inclusive_build_cost_v1/results/cost_summary.json)、[独立核验](../entry_method_exploration/20260922_until2200_improvement_v1/research/gt_inclusive_build_cost_v1/reviews/independent_audit.json)。
