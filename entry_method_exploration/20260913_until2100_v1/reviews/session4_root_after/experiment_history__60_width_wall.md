# E71 多画像加宽的完整开发性能比较

2026-09-13，第4独立串行会话。状态`COMPLETE_DEVELOPMENT_WALL_VERIFIED`，65个方法点、325轮完整单线程wall，未找到稳定整体性能改善，默认保持；整日最终交付未完成。

E69证明完整mode前三入口在Y历史aux/L128存在真实NSG增量，Web相对完整P有损伤。E70固定原图将ef10改30，P/duplicate/mode各自控制；Y通过辅助质量接续门，Web未过，但route NDC明显增加。E71据此只检验这次加宽的完整在线收益和成本，不再训练或调参。

原始实验位于[stage12_width_wall_v1](../entry_method_exploration/20260913_until2100_v1/stage12_width_wall_v1/)。[前瞻协议](../entry_method_exploration/20260913_until2100_v1/stage12_width_wall_v1/protocol.md)冻结原NSG、Fast30K/GT1、GT10-hard、Web匹配GT10-soft、P30、mode10、mode30；Web35点/Y30点，L64/128/256/400/800，每点一次全预热及五轮按dataset/repeat/L轮换。mode30的字段best_new只是本阶段固定展示别名，不是今日全局重选。

输入为每集router_train[2048:4096]历史开发2048，直接引用E67源query/GT/row bytes，包含于已经用于选择的7952aux。原base/rawIP/NSG/GT及真实H815/821保持。mode3H=2445/2463画像，一次小HNSW取7slot，按距离/slot排序去重3真实hub，再升序入原NSG。P30为单画像同宽度控制；不能把ef30称10个不同hub或等工作量。

使用E70同SHA二进制，原evaluate/legacy循环未改。graph_file直接加载并校验全W/label，0新图副本。完整wall包含raw-query路由/映射/去重/原NSG/output；GT/count/hash/JSON/build/load在外。进程实际CPU15/线程1，OMP/OpenBLAS/MKL/NUMEXPR/BLIS1，两集和方法串行，实际两个工具terminal exit0后才分析，无混跑。

按五L，mode30相对匹配P10：

| 数据 | ΔRecall pp | QPS中位变化% | 零命中净新增 |
|---|---|---|---|
| WebVid | +.3174/+.0977/+.1611/+.3369/+.1416 | −4.82/−3.42/−1.41/−1.78/−.84 | −7/+1/−2/−3/−2 |
| Yandex | +.4004/+.1123/+.0098/−.0342/+.0635 | −3.76/−2.39/−1.05/−1.13/−.32 | −8/−3/0/0/+1 |

Web相对P30在L128负、其余Recall正；相对mode10质量五点正但QPS中位五点负。Y相对mode10四点Recall负、L256/800失败增加，只有L128质量正。相对P10的五轮QPS交叉范围，Web2点全负/Y3点全负，其余跨0，不能当置信区间。共同Recall区间log-QPS插值Web−2.788/−1.364/+1.154%，Y−1.078/−.944/−.927%，均明确为描述性插值，非实测等Recall提速。局部质量和高Recall机会保留，没有稳定整体前沿改善。

失败严格零GT10命中。Web43/Y41共84不同源query、149跨L事件、420完整五L格，展示图每集最多24例，全表不截断。Web3524全五L0→7、Y2769全0→8/9/10/10/10；Web2618前三入口仅换一个但3/5/5/5/5→0/0/0/0/5，Y3645全10→0。救回/新增失败、GT成员找回/丢失、逐query净命中正负部各自保存；事后案例不进入在线选择。

新增932880 NSG/788480 HNSW，包含1040原kernel对照；55 plain源图加载+55 count加载，0新构图/训练/GT/梯度。Web原生716.218s、Y608.704s，总1324.923s含加载/count/I/O；325轮纯wall合计930.101s。源policy加载校验plain .900s/count .893s；NSG load、route-only/graph-only没有单列计时，null并写原因，不据NDC估QPS。继承E66训练成本不是零，本阶段无重训。

133120返回独立集合/mask及全部plain/count通过；第二种向量化集合验收再核133120，1040原kernel、55源图全W/label、五L同入口/slot及325wall顺序/恒等通过。71680旧基线字节恢复E65、20480 mode10恢复E67、16384 L128恢复E70；这些只验身份，旧QPS没有复用。分析前发现旧slot缓存键缺ef/graph身份，保留原helper、新增v2并在第一次分析前冻结，0额外查询、未改native；见[说明](../entry_method_exploration/20260913_until2100_v1/stage12_width_wall_v1/reviews/analysis_key_extension.md)。

[报告](../entry_method_exploration/20260913_until2100_v1/stage12_width_wall_v1/report.md) · [实测判断](../entry_method_exploration/20260913_until2100_v1/stage12_width_wall_v1/assessment.md) · [点/成本/返回](../entry_method_exploration/20260913_until2100_v1/stage12_width_wall_v1/results/) · [验收](../entry_method_exploration/20260913_until2100_v1/stage12_width_wall_v1/reviews/verification.json) · [QPS–Recall](../entry_method_exploration/20260913_until2100_v1/stage12_width_wall_v1/figures/recall_qps.png) · [失败图](../entry_method_exploration/20260913_until2100_v1/stage12_width_wall_v1/figures/failure_query_cases.png)。

E66原门失败、E70 Y辅助门通过/Web未过均保持。所有fit/旧train/monitor/cal/audit/aux历史暴露，选择反馈计训练，今日E34最终与held-out未进入。下一步仅设计独立真实hub计宽控制，未实施；详见[s-target](../s-target.md)与[具体设计](../entry_method_exploration/20260913_until2100_v1/next_stage_design_session4.md)，不能重启旧runner或按最终反馈调参。
