# 会话2之后的候选方向（设计，尚未实现/运行）

2026-09-13，会话2基于E63/E64结果和旧E10源码建立；不依据最终validation。E65已按预锁协议完成历史开发wall，不能把这份设计当作已跑的新方法。用户授权持续，下一串行会话可前瞻调整；本文件不新增用户批准流程。

## 当前可沿用证据

E63正向重权原零命中query、保持总质量和GT10成员归属，在fit双集净正且优于同质量随机query控制；旧cal门失败。E64扩大到7952历史辅助行后E63净−2/−18，不能说已转化为稳定迁移；同样不能扩大为“难度标签无效”。WebVid E62纯拓扑在E64净+38、两半+31/+7，但失败净+2；Yandex真实端点均净负。两数据集best_all仍baseline，best_new只是展示身份。

停止E61 lambda、E63倍数、局部随机行步数/seed、当前端点评分或拓扑移除网格。不放宽失败门来追求GO。E64的7952全部已用于辅助选型，属于训练反馈；与E63 fit/cal/audit分区互斥不意味着项目从未使用，Fast30K/早期研究已暴露。

## 一个有实质差异的备选：把多画像放入同一个小索引

这是可证伪表示备选，尚未证实“单画像是瓶颈”。先从[s-experiment](../../s-experiment.md)进入[history04](../../experiment_history/04_utility_and_representation.md)，再读旧[E10 builder](../../benches/run/build_target_basin_modes.py)、[原协议](../../target_basin_mode_diagnostics/v1/design.md)、[router](../../benches/run/route_target_basin_modes.py)及原报告。会话2已读builder、router、原协议、双集build_report和train10K实际结果：旧E10按GT1硬分盆，盆内20轮两均值，min8；primary/两个mode带log(pi)/d，在原Fast top32内重排。原train10K的L64/128 Recall增量为WebVid+0.216/+0.159 pp、Yandex+0.143/+0.095 pp；它们是16线程的离线路由后图搜索结果，不是单线程全wall。旧WebVid局部正值、Yandex历史validation混合及缺完整在线QPS均保留，不换名重跑旧runner。

实质改变候选是：当前GT10归属下每个真实hub绑定原P与两份离线query模态画像，直接装入一张slot-label Micro-HNSW。真实入口集合仍H815/821，画像slot上限3H=2445/2463，明确披露小图容量增加；不是修改10M底层NSG。一条query在线只搜这张图，取7个slot，按距离由近到远去重后前三个真实hub进入原NSG。每hub最多三slot时，7个不同slot至少覆盖3个真实hub；要验收此不变量、ties/不足7/非法映射处理，而不能沿用旧Policy最多3slot直接映射的接口。

建议新协议只锁一个候选和两个必要控制：

1. baseline：原单画像P与原图，完整字节/路由/返回恢复。
2. duplicate control：每hub三份相同P，和候选同3H slot数、slot插入顺序/M/ef/seed及去重逻辑，分离纯扩图/插入影响。
3. weighted two-mode plus P：原P作为首个slot逐字保留；沿当前GT10每query→hub权重a_qh，对每hub的unit query做固定20轮加权球面两均值（确定初始化、空类回退），每子画像由该子簇加权unit query和分配raw先验聚合，两个新增模态内部的总query质量及raw先验须保持原a和prior1；另一个原P是冻结复用，不能声称三个slot合计与原单slot训练质量完全相同。
4. random-partition control：相同hub质量与子簇质量目标、固定随机划分规则；其可精确保持与不能保持的量需明确。若无法以简洁确定规则匹配，缩为duplicate控制并把“语义分群作用未隔离”列为限制，不能伪造完全匹配。

上述具体聚类/先验分配尚未锁定。下一会话须先核验GT10支持/ESS是否足以稳定分两类，提出一个完整数学公式再前瞻冻结，不能看到开发结果后改阈值。不要同时加入门控、MLP、更多mode数、H扩张或多seed网格。其动机是提供一个真实入口的多种query方向并移除旧top32候选限制，同时把全部在线成本纳入普通小索引；不是声称模式数越多越好。

## 最小执行和退出边界

新的stage7独立目录；原P/H/base/NSG/raw-IP/GT只读。画像训练仅用P-fit20K及原GT，不把7952辅助反馈混称独立测试。先完成一slot原路径恢复、三slot唯一性/映射/排序、图向量bytes、plain/count/原kernel同三入口返回验收，之后再测完整fit/预定辅助集。新的真实搜索响应不能用旧不同三元组标签代理；完整三入口相同可在核验query/NSG/L/K/顺序身份后复用原返回，route NDC重新测。

建议普通开发上限：两集4模型×(fit20K+aux7952)的完整路由；若用缓存精确补测，新NSG硬上限250000（不足即停止保留），HNSW上限230000，图构建≤8，parity每图64行另行准确计入预算。若改用plain/count全量新搜索，必须重算并锁新预算，不能套用缓存数字。无新GT/全H标签。输出≤128MiB、free≥7GiB，避免复制大输入。离线加权聚合可单独8线程并记录成本，所有ANN与正式查询仍CPU15实际单线程且无训练并发。

开发候选先按固定fit/辅助Recall净值、两半稳定性、零命中与完整成本门判定，两个控制分开报告；新画像slot增加意味着必须通过真实整批wall才能声称收益。若开发无净增益或成本超限，就停止该模式数版本，不扫更多簇/插入seed。仍未证明整个表示空间不可能。

## 晚间不可丢失的正式交付

E65是历史开发子集曲线，E34最终validation2000保持未进入今日训练/选型；其晚间冻结后的独立全方法比较仍需执行。20:00停新训练，20:40停新查询，21:00交付。固定best_all和今天真实best_new；原NSG/Fast30K/FastGT10-hard及WebVid匹配soft同批五L五轮，失败严格zero GT10。最终反馈不回流训练或换候选，不能混合旧不同批次曲线。若全天仍无稳定新方法，报告真实负结果与局部正值；本会话收口不是整日目标完成。

历史暴露补充：E10原build_report确认fit[10000:30000]、route[0:10000]，原train10K结果已完整评估两集前10K；所以E64辅助7952除了Fast30K拟合暴露，还属于E10已评估范围。下一会话不能称这些行只是元数据余行。会话2此次未打开E10旧validation原结果或E34最终输入。

设计修订（10:38后、未实现）：参考主监督最新只读建议，将首版2H替换为保留原P的3H单容量候选，主张不运行2H/3H网格；首稿另存next_stage_design_session2_initial2H.md。保留P不保证原HNSW路由或检索不退化，7slot去重及同容量重复P对照必须实测。当前只有一个优先设计，仍待下一阶段完整公式与前瞻协议。

## 10:50父画像支持复核，下一协议需处理

监督只读复用E63父support/assignment_sample（review_028_profile_mode_support.json），无新模型/ANN。Web父质量中位17.373、205个hub质量<8，ESS中位132.278、25个ESS<16；Y父质量中位21.5、37个质量<8，ESS中位60.082、5个ESS<16。这里的阈值仅描述，未选新门。Web抽样query的815个soft权重全正，不能用非零query计数证明有效支持；Y每query有效hub中位2.632、Web10.885。两子簇必须分别核验质量和ESS，不能以父ESS代替；低支持回退重复P、raw prior分配须预锁。Web保留原A意味着每hub20K条dense weighted输入；不能悄悄截断小权重。如确需稀疏化须把它列为独立表示改变并前瞻冻结，而非声称原A未变。以上尚未证明存在两个有效模态或检索收益。

## 下一接口改动的定位（监督只读review_029，未实现）

下一会话应重读E34 evaluate所含benchmark_with_nsg.cpp的Policy：原graph_file校验externalLabel(j)==mapping[j]与unique slot j/重复真实hub不兼容，须按slot_labels区分标签合同，保持物理图校验；不能通过普通重建绕过身份。原searchKnn最多3、Decision/NativeWork固定3真实入口；新增分支应显式7slot候选与最终3hub分开，图reader/loader/plain-count一起验收。tie_ids为唯一slot ID，去重的距离/tie次序预锁，最终三元组保持旧canonical real-ID顺序。一画像旧分支保留原字节/回归。该源码定位不表示本会话已修改这些接口。
