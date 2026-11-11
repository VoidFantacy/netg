# ACSG 当前结论

更新于2026-11-01。E195七集残差来源与导航增量详细定位完成：完成七集、两曝光公共窗口、真实K1/K100的1260正式点/3780完整T1批次；另140新资格点和56旧二进制控制点，42对应包逐字节一致。504个导航点中341个同L相对B32净Recall正、319个被同窗GT10/B32/OPT-B32/SQ覆盖。252个方法/K/L配置中78个两窗均正且未被已有离散网格覆盖。默认E99 GT10保持。当前无待恢复矩阵。

| 数据 | 导航同L净增益正点 | 被已有方法覆盖点 | 两窗正且未覆盖配置 |
| --- | --- | --- | --- |
| coco | 47 / 72 | 46 / 72 | 10 / 36 |
| flickr30k | 43 / 72 | 51 / 72 | 9 / 36 |
| webvid2_5m_light_v1 | 67 / 72 | 30 / 72 | 20 / 36 |
| yandex_t2i_official10M_ip_v1 | 55 / 72 | 47 / 72 | 11 / 36 |
| deep10m_l2_v1 | 39 / 72 | 55 / 72 | 5 / 36 |
| sift10m_bigann_l2_v1 | 40 / 72 | 56 / 72 | 7 / 36 |
| gist1m_l2_v1 | 50 / 72 | 34 / 72 | 16 / 36 |

分数据解释与后继见[定位结论](entry_method_exploration/20261101_residual_navigation_diagnosis_v1/findings_zh.md)。完整结论见[E195报告](entry_method_exploration/20261101_residual_navigation_diagnosis_v1/report_zh.md)、[全部点](entry_method_exploration/20261101_residual_navigation_diagnosis_v1/analysis/points.csv)、[机制](entry_method_exploration/20261101_residual_navigation_diagnosis_v1/analysis/mechanisms.csv)、[两窗一致性](entry_method_exploration/20261101_residual_navigation_diagnosis_v1/analysis/stability.csv)。本轮六种导航动作保留完整B32直接C，比较一跳、距离多步、未访问邻居选点和真实入邻居静态代表；不是原search_new续搜，不修改主图或训练新门。诊断逐query复制核与原主搜索ID/距离字节一致，Python全排序另核504点全部候选事件/最终返回，详见analysis_receipt。

遗漏分为已评分未返回、未评分但邻接已评分未展开集合、无该一步边。后者不等于全图不可达；边界包含被拒绝或淘汰节点，不是终止beam的pending状态。七集全图均无零入度节点，低入度/出边/密度仍需与实际有限动作区分，不能据此删直接正确答案。逐query/GT事后相关与单seed机会不能冒充部署收益或联合beam结果。

A/B源行不重叠，均为曝光公共测试；一套图/画像、固定小窗口、离散控制和K1小计数限制保留。有限未覆盖不等于全局最优；三轮只重复费用。所有正式QPS计完整正常生命周期、选择和扩展；分段微计时在wall外，不相加代替完整wall。成员损伤/严格K100<10%尾部保留原定义。

历史有效M5/B32/SQ继续保留：[历史正面证据](experiment_history/_maintenance/20261029_residual_positive_evidence_sync_v1/conclusion_zh.md)。前序[E194](entry_method_exploration/20261030_residual_optimization_stability_v1/report_zh.md)的COCO/WebVid两窗口、256点/768T1及两集K100/L100 OPT-B32约2.2–2.5%等价省费仍成立；B32为强参照。E191 COCO/K1 SQ L400的99.64%/1072.26对GT10 L693的99.64%/817.09属于原窗口，不能混拼新QPS。E193有限学习门失败不否定所有残差/自适应。旧科学文件、PDF、seal不回写；根文档原字节由E195 source_before及前序理论桥接保留。
