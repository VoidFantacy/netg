# ACSG 当前结论

更新于2026-11-04。E199四个多模态数据集的门时机与精排成本实验已完成736点/2208完整单线程批次；主门策略80个窗口点中79个被同期强控制覆盖。 当前默认E99 GT10保持；无运行中或待恢复矩阵。 唯一未覆盖的主门点为WebVid A/K1，速度差仅+0.0254%、三轮范围重叠、B窗未复现；没有两窗共同未覆盖的新门配置。用户本轮明确要求PDF，已交付[详细PDF](entry_method_exploration/20261104_gate_timing_cost_v1/E199_残差门控时机与精排成本_20261104.pdf)，并提供[结论解释](entry_method_exploration/20261104_gate_timing_cost_v1/findings_zh.md)和[文字/表格报告](entry_method_exploration/20261104_gate_timing_cost_v1/report_zh.md)。

本轮三层决策：STATIC按dataset/K/L离线固定开关；PRE在query/route可用、主搜索前预测；POST在相同完整主搜索后预测。PRE-LATE复用完全相同PRE模型/阈值，只移动执行位置，返回、动作和工作量一致。PRE/POST不是主搜索循环内早停，主搜索总是完整执行。

F语义控制整段C＋CASCADE384，关闭返回主结果；N语义始终保留全部C答案，只控制追加导航，并有利用C摘要的CPOST。两种off语义分别比较，不能把删除直接补点带来的省费当成门位置单变量。完整耗时和校准正增量保留必须同时评估。

| 数据 | K | 语义 | PRE90 Recall/QPS | POST90 Recall/QPS |
| --- | --- | --- | --- | --- |
| COCO | 1 | F | 99.3164% / 1169.30 | 99.3164% / 1170.29 |
| COCO | 1 | N | 99.3164% / 1788.82 | 99.3164% / 1795.77 |
| COCO | 100 | F | 96.9482% / 1132.60 | 96.9482% / 1133.63 |
| COCO | 100 | N | 96.9482% / 1136.51 | 96.9482% / 1136.37 |
| Flickr | 1 | F | 99.9023% / 1709.16 | 99.9023% / 1695.67 |
| Flickr | 1 | N | 99.9023% / 1721.52 | 99.9023% / 1725.77 |
| Flickr | 100 | F | 97.8799% / 1191.01 | 97.8799% / 1186.75 |
| Flickr | 100 | N | 97.8799% / 1192.35 | 97.8799% / 1191.91 |
| WebVid | 1 | F | 85.2539% / 930.74 | 85.2539% / 925.11 |
| WebVid | 1 | N | 85.2539% / 933.39 | 85.2539% / 927.31 |
| WebVid | 100 | F | 76.4395% / 946.09 | 76.6807% / 920.47 |
| WebVid | 100 | N | 76.6807% / 908.39 | 76.6807% / 922.00 |
| Yandex | 1 | F | 94.5312% / 913.59 | 94.5312% / 913.19 |
| Yandex | 1 | N | 94.5312% / 906.81 | 94.5312% / 911.87 |
| Yandex | 100 | F | 90.0098% / 928.52 | 90.0762% / 894.38 |
| Yandex | 100 | N | 90.0107% / 931.69 | 90.0762% / 895.60 |

表为A/B各512的合并描述：Recall按命中合并，QPS由平均每query时间取倒数；不是新独立确认。逐窗原值与门误拒、无效启用、正增量保留、强前沿见[门表](entry_method_exploration/20261104_gate_timing_cost_v1/analysis/gates.csv)、[完整点](entry_method_exploration/20261104_gate_timing_cost_v1/analysis/points.csv)和[强控制](entry_method_exploration/20261104_gate_timing_cost_v1/analysis/frontier.csv)。75%/90%只为独立cal目标，测试结果另核；零正增量记NA，全开/全关不自动算识别成功。

精排成本已分为重特征、树预测和实际扩展；FAST384/同池距离/短名单CASCADE384/全C教师均同期测量。[精排表](entry_method_exploration/20261104_gate_timing_cost_v1/analysis/rerank_costs.csv)保留最终召回、完整增加µs、局部特征/模型费用与入口改变后的实际工作差。门特征可被后续复用，分段归属变化不等于同额新增开销；cal全关时当前PRE/POST仍构造特征再关闭，STATIC免去这笔费用，是可优化实现差异。

正式路径无阶段插钟，完整wall含Batch创建、全部查询工作、六数组复制与销毁。另行profile逐条返回/动作对齐，阶段均值/条件均值/P50/P95为诊断，不能拼成正式QPS；其batch边界亦不含正式六数组复制销毁；基线分段使用返回等价逐query适配层，非原优化batch严格分解。正式batch wall共1119.37秒，包含于正式进程1711.39秒。COCO/WebVid复用E198，Flickr/Yandex本轮新标签/模型成本分别286.38/110.19秒；继承债未清零。

四集raw-IP、原图/画像、固定Q8来源、单入口384/L200、两旧曝光窗口、K1稀疏事件、共享开发512和多比较限制保留。未实现主循环早停、pause/resume或修图。历史E173/E191/E194条件有效M5/B32/SQ与E198返回等价缓存优化保持原身份；本轮不否定全部残差方法。所有旧科学文件/seal/PDF保留，根文档由source_before桥接，全部新证据持久化。[交付核验](entry_method_exploration/20261104_gate_timing_cost_v1/delivery_validation.json)。
