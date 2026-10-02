# ACSG 当前结果摘要

2026-09-13，第5串行会话完成E72–E74。精简多画像在Yandex保留局部前沿信号，尚未形成稳定整体改善或默认替换结论。E74已完成规定基线和fullmode/compact同批55点、275轮单线程完整wall；整日21:00目标未完成，E34晚间最终仍待执行。

精简仅去掉同hub字节完全相同画像，Web2445→1771、Y2463→2067，真实H815/821不变，每hub完整max评分集合保持；普通重建小图改变近似遍历，仍ef10/7slot去重3入口→原NSG。

| E74历史开发2048，相对匹配P10 | L64/128/256/400/800净命中变化 | 零命中失败净新增 | QPS中位变化% |
|---|---|---|---|
| WebVid（GT10-soft） | +9/−23/+2/+28/+2 | +2/+6/0/−1/+1 | −1.44/−.81/−.53/−.60/−.15 |
| Yandex（GT10-hard） | +99/+59/+38/+1/+15 | −10/−7/−4/−1/0 | −1.56/−.96/−1.20/−.04/−.19 |

两集十个QPS五轮交叉范围均跨零（不是置信区间）。Y共同Recall三个内部点的log-QPS插值+1.873/+2.455/+2.965%，只保留为描述性开发前沿信号，不称实测等Recall提速或独立泛化。Web L128召回−.1123pp且失败+6，明确保留损伤。相对完整mode，Y四L召回正/L800负；不能将节点减少比例当速度增量。

E73完整aux7952原门保持：Y相对P +120命中/失败−13、对fullmode+71/−9，两半均正；Web对P−59/失败+11、对fullmode+47/−2，未过门。E72 distinct10双集接续门失败，保留Y局部质量正与比mode30低的路由NDC，该版本停止且0QPS；其合成“不足3hub拒绝”未实际覆盖，独立更正保留原封存。E66/E70/E71历史结论不由本开发子集回写。

E74保存91个独立失败转换query、174个跨L事件及455个五L格。Y row2769全零变8/9/10/10/10，row3846全10变全零；Web row3524全零变全7，row2391变全零。图每集展示24例，CSV全量保留。失败严格零GT10命中，成员找回/丢失与逐query净值另列。

E74新增789360 NSG/645120 HNSW，0构图/训练/GT；原生1101.761秒，275轮纯完整wall合计772.446秒。会话E72–E74共1080816 NSG/936000 HNSW/2实际小图，合成另4图/512HNSW；编译42.049秒，精简.031秒、构图.348秒，继承E66画像训练30.286秒及早期GT成本未重测、不记零。CPU15/实际进程和数值库1线程，方法串行；112640集合/mask、880原kernel、全部slot/源图/旧返回和计时轮换独立核验通过，主监督13:56另独立验收原物/计时/五图。

P-fit含旧train/monitor，cal/audit/aux均历史暴露，辅助选择计训练；E74的2048包含于已用aux7952，E34最终与held-out今日未进入。旧产物与source_before/root_after均保留。下一方向与晚间冻结/最终评估门见s-target，不由这些诊断直接宣告方法成功。

[完整报告](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/report.md) · [判断](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/assessment.md) · [QPS–Recall](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/figures/recall_qps.png) · [失败query图](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/figures/failure_query_cases.png) · [下一阶段](s-target.md)。
