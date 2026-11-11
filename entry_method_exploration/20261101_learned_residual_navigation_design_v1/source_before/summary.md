# ACSG 当前结论

更新于2026-11-01。E196费用邻近强控制完成837点/2511完整T1；重测E195的51个固定配置、102窗口点，其中97个窗口点被当前强GT10/OPT-B32覆盖，0个配置两窗均未被这组强控制覆盖，加入本轮其他重测导航后为0个。均为有限曝光窗口证据，未覆盖不称成功或默认替换。默认E99 GT10保持（WebVid soft-t1，Yandex hard），固定矩阵均已收口。

| 数据 | 被强控制覆盖窗口点 | 两窗未被强控制覆盖配置 | 两窗全方法未覆盖配置 |
| --- | --- | --- | --- |
| coco | 15 / 16 | 0 / 8 | 0 |
| flickr30k | 14 / 14 | 0 / 7 | 0 |
| webvid2_5m_light_v1 | 19 / 22 | 0 / 11 | 0 |
| yandex_t2i_official10M_ip_v1 | 12 / 12 | 0 / 6 | 0 |
| deep10m_l2_v1 | 6 / 6 | 0 / 3 | 0 |
| sift10m_bigann_l2_v1 | 13 / 14 | 0 / 7 | 0 |
| gist1m_l2_v1 | 18 / 18 | 0 / 9 | 0 |

先读[E196定位结论](entry_method_exploration/20261101_residual_navigation_cost_controls_v1/findings_zh.md)、[完整报告](entry_method_exploration/20261101_residual_navigation_cost_controls_v1/report_zh.md)、[102比较](entry_method_exploration/20261101_residual_navigation_cost_controls_v1/analysis/candidate_comparisons.csv)、[51配置](entry_method_exploration/20261101_residual_navigation_cost_controls_v1/analysis/stability.csv)，再读[E195完整来源/导航定位](entry_method_exploration/20261101_residual_navigation_diagnosis_v1/findings_zh.md)。E195原1260点/3780T1与837点控制是独立冻结阶段，不混拼绝对QPS、不回写旧结果。总2097正式点/6291完整批次；不是2097份独立质量样本。

E195源链显示COCO/Flickr/WebVid有较多重复遗漏支持，Yandex较弱，Deep/SIFT当前源只覆盖不到1%的K100/L200遗漏；GIST有来源/路由/容量多层损失。多数遗漏有来自已评分未展开集合的一步边，WebVid该比例较低；该集合包含被拒绝/淘汰点，不是可免费恢复的pending beam。本轮独立辅助队列只主动展开选中seed，后续跳过main visited及已评分C/代表，不代表所有状态共享。

当前度数/背景r8没有给出普遍可靠的导航准入规则；低度/密度不作为删正确答案规则。3952550个C评分事件中401354个此前主搜索已评分，均不能严格改善终止K阈值；这是直接补全的有限域省费证书，不是已实现优化或QPS收益。导航仍可使用已评分未展开的seed，不能据证书剔除入口资格。

历史M5/B32/SQ正面证据保留原身份和完整费用：[历史正面索引](experiment_history/_maintenance/20261029_residual_positive_evidence_sync_v1/conclusion_zh.md)。E194两个K100/L100 OPT-B32约2.2–2.5%等价省费、E173/E191有效场景不因新控制而抹去；E193有限门结果不否定所有残差/自适应。旧绝对QPS不拼入新窗口。

全部C1三轮真实包/工作相同，旧包字节对齐、原生线性oracle及NumPy/stdlib整数/hash/wall核验通过。A/B都是曝光公共query，单图/画像、固定窗口、小K1事件与有限L/容量限制保留；quality-threshold speed可对应更高Recall，不称精确等Recall。费用分段在wall外，完整wall权威。详见各报告和cost_ledger。旧科学文件/PDF/seal不回写，根文档由本轮source_before桥接；无新PDF。
