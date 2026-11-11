# ACSG 当前结论

更新于2026-10-28。**默认保留GT10：WebVid GT10-soft-t1、Yandex GT10-hard，E99共享NSG优化保持。** 最新正式实验是[E187实验报告](entry_method_exploration/20261028_adaptive_completion_pilot_v1/report_zh.md)，七集两K综合证据仍为E183。E187已完成，没有正在等待恢复的矩阵；长期可靠Recall–QPS目标尚未达成。

**本轮区域补全的单位新增召回成本过高，未取得完整Recall–QPS综合提升。默认保留GT10，暂不将这版区域后端接入动作选择器。** 区域补全18点中，18点被本轮某个实测L的GT10在Recall和中位QPS两项同时覆盖；达到事前速度筛选的点0个，达到预算筛选的点0个。 全量见[六页图表PDF](entry_method_exploration/20261028_adaptive_completion_pilot_v1/ACSG_自适应残差补全_实验对比_20261028.pdf)。

## 最新两集K100实际结果

COCO/Deep保留原base、图、metric和GT10。原46点加6个GT10控制，52点、每点10K query、3轮、实际单线程完整wall；原GT10测11个L，每集另补3个L，B32及REG-NN/Q/R在L100/200/400。下面固定L200；QPS是本轮中位数，不拼接旧kernel或计时批次。

| 数据 | 方法L200 | Recall@100 | 完整QPS | 对GT10 ΔRecall pp / ΔQPS |
| --- | --- | --- | --- | --- |
| COCO | GT10 | 95.3444% | 1906.51 | — |
| COCO | B32 | 96.7159% | 1803.71 | +1.3715 / -5.39% |
| COCO | REG-NN | 95.5523% | 1511.32 | +0.2079 / -20.73% |
| COCO | REG-Q | 95.5102% | 1483.92 | +0.1658 / -22.17% |
| COCO | REG-R | 95.5793% | 1474.49 | +0.2349 / -22.66% |
| Deep10M | GT10 | 97.0780% | 1785.59 | — |
| Deep10M | B32 | 97.0801% | 1725.05 | +0.0021 / -3.39% |
| Deep10M | REG-NN | 97.5345% | 1154.98 | +0.4565 / -35.32% |
| Deep10M | REG-Q | 97.5599% | 1106.34 | +0.4819 / -38.04% |
| Deep10M | REG-R | 97.5601% | 1098.14 | +0.4821 / -38.50% |

另冻6个GT10控制用于排除原网格错觉，原46点及首轮分析保留，未改模型或补全参数；补充与原候选时间窗口不同，不作为精确速度估计或盲确认。

区域后端覆盖全base，允许提出旧训练残差源外ID；突破候选来源与获得净性能是两项证据。REG-Q只看q与区域，REG-R另看原始返回；同样top8选2、96精算上限不意味着同扫描量。R相对Q的三L结果、源内外救回/损伤、真实更大L的离散预算对照均保留[全部CSV](entry_method_exploration/20261028_adaptive_completion_pilot_v1/analysis/)。不按测试挑赢家，不把曲线插值当新增等Recall测量。

原区域模型12K训练、4K校准（不选参数）；B32为完整16K训练的冻结参考。原测试历史曝光，非盲确认；本轮未验证K1/其他五集，未实现逐query动作开关，未替换默认。

## 单位新增召回的访问成本

这版区域补全的主要瓶颈是救回量不足以偿还额外访问费用。固定L200，按完整中位QPS倒数推算平均查询耗时：COCO B32增5.70%、REG-R增29.30%；Deep B32增3.51%、REG-R增62.60%。这与上表QPS降幅不是同一数值，不能混用。

Deep REG-R救回4821个成员，其中4794个在旧训练残差源外；平均扫描约26134个PQ码/query，COCO约282个/query。Deep不使用学习模型的REG-NN仍增耗时54.60%，说明基础区域补查已有显著费用。当前只测完整wall与扫描/精算计数，尚未测粗路由、LUT、扫描/堆、精算和合并的分段占比，不能宣称某一项已被确认为最大瓶颈。

固定ID表的来源问题仍独立存在：Deep B32开销较小，却只增加0.0021pp；COCO同表增加1.3715pp。因此不能把所有残差问题简化为执行慢，也不能把当前结果概括成所有补全都不值得。分段计时、硬访问预算、成本感知选区和按query跳过补全均是后续提案，未实施或测试。详见[费用结论与新对话接续](experiment_history/_maintenance/20261028_completion_cost_handoff_v1/conclusion_zh.md)。

## 失败率与救回率

用户定义的失败为单query Recall@100<10%，即0–9个GT100命中；恰好10个排除。失败率以同数据/方法/L全部query为分母；改善与升至≥10%分别统计。E187两集三L及配对尾部见报告，不能把平均Recall增加或成员修复率解释为严重失败修复。

七集已有全L失败分布继续见[全L修正版](reports/20261024_failure_rescue_residual_lt10_v2/report_zh.md)及其PDF；其147点引用E183既有返回。旧“未满100”图保留历史身份，不作当前失败率口径。两集尾部样本很少，不用0/1、1/2推导普遍规律。

## 残差、几何与跨集判断

E184/E185支持局部连续性与遗漏共享存在关联，不支持单一“越低维越有效”，也没形成免费在线净收益准入器。COCO局部有效秩高于Deep/SIFT，不能以PCA秩作为真实流形维数或残差适用标签。根本研究问题是可迁移的剩余目标结构能否在有限访问预算下被利用，不能只看失败量或源内重现。

固定ID表受遗漏目标在训练中重现、当前路由覆盖及有限容量约束；Deep/SIFT源外主导，GIST还受路由/选择限制。E187用独立全base后端检验源外可达性与费用，结论只及这组固定实现/模型。不能把区域法失败解释为数据没有流形，也不能把源外救回当已发现流形因果。

E183七集两K：WebVid/COCO旧残差共同Recall区间折线受益，Flickr/GIST混合，Deep/SIFT及Yandex K100未支持统一替换。旧数值与边界见[E183报告](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/delivery_v2/report_zh.md)，本轮未重新测另外五集，不跨核拼QPS。

## 核验、成本与限制

coco正式内部wall 644.09s，suite 671.56s；deep10m_l2_v1正式内部wall 744.13s，suite 931.05s。内部wall已在suite中，不能相加。后端构建8线程、训练/查询1线程，数组RAM与每query扫描/精算见报告；B32原JSON计数0为未插桩，不是0精算，第二实现已重构。

旧程序前128query ID/score/route逐字一致，全base分区、4096编码抽查、全部补全从同L实际主包重构oracle、52真实包/156轮bits/SHA、冻结输入/大资产stat及第二份stdlib质量统计通过。第二实现由同一执行者完成，不称独立人员审查。技术失败过程留[说明](entry_method_exploration/20261028_adaptive_completion_pilot_v1/reviews/process_notes.md)。

单图/单模型、曝光公共query、两集pilot、固定模型跨L迁移与计时波动限制保留，无新盲确认、流形因果、跨集准入器或默认替换。原科学产物/历史seal保持；根文档旧版本见[E187快照](entry_method_exploration/20261028_adaptive_completion_pilot_v1/source_before/)。

## 证据入口

[E187实验报告](entry_method_exploration/20261028_adaptive_completion_pilot_v1/report_zh.md) · [六页图表PDF](entry_method_exploration/20261028_adaptive_completion_pilot_v1/ACSG_自适应残差补全_实验对比_20261028.pdf) · [52点](entry_method_exploration/20261028_adaptive_completion_pilot_v1/analysis/points.csv) · [救损](entry_method_exploration/20261028_adaptive_completion_pilot_v1/analysis/paired.csv) · [实际预算对照](entry_method_exploration/20261028_adaptive_completion_pilot_v1/analysis/discrete_comparisons.csv) · [第二实现核验](entry_method_exploration/20261028_adaptive_completion_pilot_v1/reviews/results_audit.json) · [E185](entry_method_exploration/20261024_manifold_residual_probe_v1/report_zh.md) · [E184](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/report_zh.md)。
