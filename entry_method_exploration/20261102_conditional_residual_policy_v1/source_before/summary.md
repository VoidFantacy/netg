# ACSG 当前结论

更新于2026-11-02。E197七集候选支持、可预测性与执行方式分离已完成9434点/28302完整T1批次，默认E99 GT10保持（WebVid soft-t1、Yandex hard），无待恢复矩阵。**336个学习器窗口点全部被同窗GT10、OPT-B32或REUSE-SQ覆盖。** 当前prototype不作默认替换；这不否定所有学习器或残差补全。

主要定位：有限C里有可用入口，当前模型只兑现约15.9%–34.0%的同池单入口GT教师增量。下表为FULL、K100/L200、两窗合计，相对完整直接B32的百分点；教师用GT逐query选最好，不能部署，未付识别费用。

| 数据 | FULL单入口GT教师增量pp | 模型增量pp | 模型兑现教师% |
| --- | --- | --- | --- |
| COCO | 1.2490 | 0.4248 | 34.0 |
| Flickr | 1.0293 | 0.2773 | 26.9 |
| WebVid | 5.3057 | 1.7900 | 33.7 |
| Yandex | 2.6816 | 0.8213 | 30.6 |
| Deep10M | 0.8643 | 0.1377 | 15.9 |
| SIFT10M | 0.6914 | 0.1211 | 17.5 |
| GIST | 2.2780 | 0.6000 | 26.3 |

在上述FULL/K100/L200比较中，COCO/Flickr/GIST两窗的模型选点均优于同数量距离单入口，WebVid/Yandex一窗正一窗负，Deep/SIFT两窗更差；完整QPS均慢约14.7%–44.2%。例如COCO A距离法97.2148%/1550.16 QPS，模型97.2871%/905.50 QPS；选点小幅增量没有抵消在线成本。更大L及强B32/SQ控制基于本轮实际完整wall，不能只比同L GT10。

筛选局部有效但不稳：FULL/K100/L200中COCO/Flickr/Yandex/SIFT保留约93%–96%的已选正收益；WebVid/GIST全部启用；Deep仅保留58.2%，Q8亦仅45.5%，低于cal的90%目标。门在全C预测后才拒绝，只省后续展开。K1多集正例稀疏，全关不等于学会识别。

CBRIDGE增量近零；SHARED在FULL/K100/L200对同适配层AUX追加约0.01–0.30pp，完整QPS慢约3.5%–18.9%；提前入口有救回也有损伤。三类动作均无两窗共同未被强控制覆盖的配置，仍不能外推完整状态续搜或所有实现。生产主核未实现pause/resume。

770个配置对仅保留两个简单观察：WebVid K1/L200 DIST1-FULL（A86.9141%/1134.02，B85.1563%/1140.67 QPS，描述区间含0）和K100/L100 Q8-B32（A64.2852%/2544.02，B63.8535%/2530.67，较更高质量B32仅快约0.38%–0.50%）。有限网格未覆盖不叫默认替换。历史M5/B32/SQ正面场景继续保留其原协议和费用，[历史索引](experiment_history/_maintenance/20261029_residual_positive_evidence_sync_v1/conclusion_zh.md)不因本轮结果失效。

后继建议改为部署状态一致的真实效用监督、以DIST1为参照的query内排序、离线强表示/在线两段选择及前置便宜拒绝；均未实现、未测试，详见s-target，不把教师空间当可学习保证。

证据：3485197标签、28候选拟合/14选定模型；全部9434包/28302轮、2768568候选witness、5403128探针、728旧包对齐及独立stdlib整数/hash/wall通过。正式batch wall16018.96秒，其他阶段为嵌套口径。关机后来源分1原持久/11原三轮包SHA恢复/2新GIST；恢复窗work/seed/witness为重放身份。所有证据均在持久磁盘，原日志字节不变、旧seal/PDF不回写，无新PDF。

先读[定位与新方案](entry_method_exploration/20261101_residual_bottleneck_separation_v1/findings_zh.md)、[详细表格](entry_method_exploration/20261101_residual_bottleneck_separation_v1/report_zh.md)、[跨窗](entry_method_exploration/20261101_residual_bottleneck_separation_v1/analysis/stability.csv)、[强控制](entry_method_exploration/20261101_residual_bottleneck_separation_v1/analysis/comparisons.csv)，再读[核验](entry_method_exploration/20261101_residual_bottleneck_separation_v1/delivery_validation.json)。A/B均曝光，单图/画像、有限预算、K1稀疏事件、Q8迁移和未校正多比较的描述区间限制保留。原E195/E196各自收口，不混拼旧绝对QPS。
