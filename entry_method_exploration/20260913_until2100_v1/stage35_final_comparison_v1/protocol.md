# E94 冻结候选的最终完整性能对照

第11唯一串行会话，2026-09-13。E93已按历史aux7952完成实际选择，E92/E73模型不再变化。Web best_all=GT10-soft原P、best_new=E92组合（完整开发门失败的反证展示）；Y两个角色均E73 compact。Web额外保留compact作为组合起点。所有角色在打开E34最终载荷前写入selection/配置和preselection seal。

完整Web六方法：原NSG/Fast30K/GT10-hard/GT10-soft/E92组合/compact；Y四方法：原NSG/Fast30K/GT10-hard/compact。每方法L64/128/256/400/800，固定2000 query，一次全批warmup、五轮轮换独立plain wall、一次全count和每点16条原kernel。50点250wall，700800 NSG、560000 HNSW，0新训练/图构建/GT/编译。所有alias仅一份实测。两集严格串行，每次一个被测方法，不并发训练、ANN、编译或数值分析。

CPU15，配置threads=1及OMP/OpenBLAS/MKL/NUMEXPR/BLIS=1，实际/proc线程与affinity核验。计时覆盖raw query完整小图路由（含七slot排序/去重/映射）、原NSG和输出；GT/count/hash/JSON/build/load在外。warmup只在五轮之前一次，后续轮换warm-cache；route/graph组件wall不另测，缺项为null，不由计数拼出QPS。原底层NSG/base/rawIP/GT与815/821真实hub保持；图是1771/2067画像小索引，原Fast历史30K训练量/seed100/heap规则保留。

E34历史validation2000来自原validation命名空间，历史已经多轮观察；今天只在完整实际选型seal之后首次读取/hash并作最终对照。不能称全项目盲集，不与router_train源行数值混淆。最终返回/质量/QPS禁止回流选型/训练/参数/L/图修改，held-out不开。源数据query/GT/row与E34身份核验并引用，不复制大输入；base/NSG只对照E74继承stat/SHA记录，不重新hash数GiB文件。

全部aligned返回IDs/距离bits/三真实入口/七slot/路由与图NDC/GT10 mask保存。失败严格GT10零命中；完整所有方法零失败并集，保存源namespace/row/GT10/返回和三入口。独立集合评分、全plain/count/原kernel、五轮/跨L身份、同三入口graph返回一致。原基线另按相同E34query重放历史返回身份，不拼其QPS。报告救回/新增失败、query净增损与GT成员增损，五轮范围和query不确定性分开。

QPS–Recall、QPS–失败率、按L三指标图与失败查询全表均必须交付。保留全部正负点；只有同机同批完整前沿支持才讨论改善，单LRecall/NDC/局部开发增益不能升级GO。若画相同Recall插值，只在双方实测非支配共同区间25/50/75%位置作log-QPS插值，明确描述性并带五轮交叉范围，不作新测量或默认替换。

使用E91 run_frozen_v3/analyze_frozen_v3与E73同SHA binary，不更改原kernel。Web预算780s、Y600s，单job1200s；19:40停止新启动，19:53本次query硬止以预留20:00安全交接；整日20:40硬止不放宽。失败保留完整预留及原文件，不自动重试或跑半组替代完整对照。最终目录64MiB、session11累计128MiB（含E92/E93/closeout）、free>=6.45GiB再余8MiB，RSS32GiB，大文件只/data，不清理旧封存。

实际完成后独立分析、图目检、完整成本/历史解释/根文档同步、source_before/root_after/finalseal及无遗留任务handoff。本会话完成不表示整日21:00用户目标完成。
