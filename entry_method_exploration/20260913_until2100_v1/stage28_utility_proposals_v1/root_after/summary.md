# ACSG 当前结果摘要

2026-09-13第9串行会话完成E86/E87两组离线静态小图改进，双集完整接受门均FAIL；保留Web局部修复，默认未替换。整日21:00目标未完成，E34最终矩阵尚未运行。

| 方法/数据 | 接受边 | fit并图对compact：净命中/失败变化 | aux7952对compact | aux对匹配P |
|---|---:|---|---|---|
| E86 Web | 29 | +191/−13 | +18/−3 | −41/+8 |
| E86 Y | 3 | +13/−1 | −4/0 | +116/−13 |
| E87 Web | 16 | +94/−4 | +16/−3 | −43/+8 |
| E87 Y | 0 | 0/0 | 0/0 | +120/−13，全部继承compact |

E86直接测实际加边的全fit NSG效用后筛选原几何候选；E87改变候选来源，用P优于compact的完整策略响应提出缺失hub目标，再实际测边。策略差只提议，不作单边信用。两版均测合并后的相互作用，线上仍固定小图/三真实入口/原NSG。原画像/全部旧边/base/GT/rawIP不变。

E87 Web aux两半+7/+9，救回3/新增0，但对E84−26命中、对E86−2，均不及P。E86 Web两半+6/+12、救回4/新增1。训练增益不能当泛化或性能结论；Y E87零更新明确不是新方法收益。两版停止固定规则，不扩候选/阈值或读最终反馈调参。

新增365054 NSG/7756544 HNSW、10非零边安装（含4首边回归图）+2零更新副本，4离线筛边拟合，0普通构图/梯度/GT/新增QPS。E86编译13.345s，两版训练/辅助操作合计412.247s，含load/count/cache/I/O，不作QPS。继承GT/P总成本未知。所有ANN实际CPU15、进程与各库1线程、串行；完整集合/mask、缓存/图字节、原kernel与旧对照回归通过。

E87完整六配置失败并集413条、173状态变化，全部GT10/入口/返回保存。P-fit20K含旧train/monitor；aux7952/两半、cal/audit历史使用，接受反馈计训练。E34最终原始query/GT/row和held-out本会话未打开；晚间准备仅配置/模型及输入stat，不是最终选择。

旧局部信号保持：E84 Web对compact+42/失败−4仍不及P；E73/E74 Y五L对P命中+99/+59/+38/+1/+15、失败−10/−7/−4/−1/0，但五轮QPS范围跨零，约1.9%–3.0%只作描述性插值。最近完整QPS仍E74，不与本轮质量点拼接。

[E86报告](entry_method_exploration/20260913_until2100_v1/stage27_edge_utility_v1/report.md) · [E87报告/失败图](entry_method_exploration/20260913_until2100_v1/stage28_utility_proposals_v1/report.md) · [最近完整QPS曲线](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/report.md) · [晚间准备件](entry_method_exploration/20260913_until2100_v1/session9_final_preparation/readme.md) · [下一阶段](s-target.md)。详细旧实验均在s-experiment和experiment_history，根文档前件已快照。
