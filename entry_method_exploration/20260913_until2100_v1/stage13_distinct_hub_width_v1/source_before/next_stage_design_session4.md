# 会话4后的研究接续（后继设计，尚未实现/运行）

先完整读取五份主文档、当前handoff、E69/E70/E71报告及监督备注，运行只读`src/resume_inspect_v4.py`。阶段1–12均不重跑；E71执行/封存状态以state与最终handoff为准。下一会话是唯一写入/实验者，不开并行CLI或子代理，监督管理后续会话。

## 已获得的机制证据

E69固定完整评分前三的实际NSG：Y精确mode比精确P净+132命中/失败−10，比原approx P +97/失败−8；Web对精确P净−109/失败+7。精确单画像P在Web有增量而Y反而−35，排序更准不是NSG效用上界。每个结论限定历史aux7952/L128，不能推断未测L。

E70单个ef10→30：Y mode30相对P10净+77、两半+8/+69、失败−7；相对P30+89/两半+28/+61/失败−7，辅助质量门通过。Web相对P10仅+6且失败+5、两半−16/+22，对P30−100，保留反证。排名一致率mode Web77.73%→93.00%、Y86.38%→98.06%；route NDC相对P10 +87.32%/+111.69%，total +5.26%/+3.93%。不是等工作量或稳定加速。

E71已完成mode10/mode30/P30及规定基线同批65点325wall。两集相对P10五L QPS中位均负；Web五L Recall正但原7952门失败保持，Y相对mode10四L Recall负。原生1324.923秒、完整325wall合计930.101秒，没有稳定整体前沿改善，见[报告](stage12_width_wall_v1/report.md)及[判断](stage12_width_wall_v1/assessment.md)。下一方向须从其完整成本结论出发，不凭上面的NDC或同LRecall判断收益，也不按曲线加大ef/改seed。

## 第一优先：一个按真实hub计宽的受控实现

E71完整wall已显示加宽费用限制收益，因此优先考虑：固定E66原P/duplicate/mode图/W，保持原NSG/三入口，只将小图保留宽度由physical node换为10个不同真实hub。目标是在mode30接近完整排名的质量和mode10较低成本之间找实际可部署改进；不能预设会更快或更好。

这不是新概念：本地`BaseSearchStopCondition`与`MultiVectorSearchStopCondition`已存在。[会话4只读源码记录](reviews/session4_local_stop_semantics.md)已说明四个重要边界：callback接收external label；`searchStopConditionClosest`最后返回internal ID；移除callback的dist实参不对应被弹出点；本地MultiVectorSpace既追加docID，又有IP构造器dim_未赋值疑点。不要直接加载已有float-only图到该space，也不要在原hnswlib里临时修代码。独立适配通过label→hub计数、忽略移除dist，显式internal→external slot→真实ID。若不确定上述语义，重新读原函数，不猜。

候选实现为单个`BaseSearchStopCondition<float>`：维护结果heap中每hub的引用数和不同hub总数；新增/移除按原生实际label更新，stop/consider/remove-extra沿现成doc-count形式。每query状态清零，仍让原图负责邻接与距离计算。不要另维护一个假定tie顺序相同的dist/doc heap。回调返回的候选按实际distance/slot排序，以每hub最早槽为代表，取3hub升序入原NSG。明确与当前固定7slot去重的接口差异。

12:57监督review_065补充了singleton tie边界：原top_candidates的CompareByFirst只比distance，旧searchKnn先在原堆pop到k才转external；stopCondition反向pop输出完整堆。单画像恢复若先把完整ef数组按(distance,label)重排再取3，可能改掉原k3子集。若两分支原堆相同且filter不修改，数组前3才对应原截断保留集；再映射/canonical。必须在合成tie验证两堆/停止行为，不把这个条件化结论当已验收。新mode方法可另定distance/slot排序合同，旧singleton恢复控制与新方法明确分开。

候选physical数最多30（10hub×每hub最多3slot），可使用固定容量trace或带offset的变长artifact保存实际候选/计数；不要强行塞入原7slot数组或把前7称完整候选。单画像singleton控制必须确认可恢复原ef10，不能假定callback分支与bare-bone搜索在tie/早停上一致；任何意外差异先定位控制语义。

最小预检：合成重复/tie/内部外部ID不相等/完整映射/引用计数/移除/状态复位/不足3hub/源图加载，另冻结128真实aux前缀。可先仅路由比较以便零NSG发现接口问题，所有真实HNSW/合成构图仍分账。未通过不启动全量。

下一协议可固定六policy：普通P10、singleton-callback P10、普通duplicate10、distinct10 duplicate、普通mode10、distinct10 mode。只做一个distinct宽度10，不同时做多ef/新模式或两条实现。旧E70 P30/mode30可作身份一致的离线质量参照，正式QPS必须在新的同批矩阵重测。

预算草案不是已锁runner：若两集128预检+7952主批、每点plain/count+16原kernel，则6policy合计194304 NSG/193920 HNSW；额外route-only预检和合成分别先锁，不隐含加费。0新训练/构图（合成另计），source graph直接引用。新版本建议<=64MiB；现场核对累计free与晚间预留，不降旧协议floor，不删旧产物。

质量接续至少按全aux及固定两半分别比较新mode与P10、原mode10、原mode30，严格zero失败不增与净命中方向；P-singleton恢复、duplicate容量控制与实际候选占位/距离工作量分开。沿预锁规则决定是否完整wall；不按新反馈选一个更有利的半区、query群或更宽ef。计数/进程wall/更高排名agreement都不能当完整效率结论。若仍损伤或路由费用没有减少，停止此单个实现，不无限修正停止条件。

## 第二优先：保留机制反证后回到离线表示

WebVid两轮均不胜匹配单画像，说明不能把它的问题全部归因近似宽度。若distinct控制也无效，优先分析已有exact-P与exact-mode的真实救回/新增失败及训练支持，确认合格mode父hub/子质量与损伤关联；只用现有artifact，不新增最后评估反馈。仅凭这种事后关联不足以学习query门控或扩大模式数。

单个原生完整3H扫描可以作为将来成本控制候选，但E69当前仅离线注入、float64排名，尚未实现完整在线SIMD扫描/三hub聚合计时，不能称其不可部署或已更快。若后续有明确成本理由，另立唯一控制、核验native float32与float64近tie身份及真实返回；不要与distinct实现同时开网格。本会话没有跑这一候选。

补充备选来自12:55主监督只读review_057/061，尚无新实现或查询：同hub字节相同的fallback画像可精简，Web报告674/2445重复槽、Y396/2463；完整max评分理论上保持，但构图拓扑/层级、近似路由和NSG不保证保持。若后续改走此备选，应先按[监督备注](/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md)追溯并复核源W，而非把returned-slot浪费当已知节时。当前Policy要求每hub恰3、h=3H；variable 1–3槽必须新接口与plain/count/旧对照验收。与distinct控制择一执行，不同时开两线或扫宽度。

## 第三优先：晚间最终对照和用户交付

20:00停新训练，20:40停新增query，21:00完整报告。E34历史validation2000可作为最终对照，须先冻结best_all（允许原方法）和实际best_new；当前inventory_v4保留旧18条及6个ef30配置，展示字段best_new=mode30不是全局最佳重选。最终选型规则只能用已披露开发反馈；E34最终结果不回流训练/阈值/模型/参数，held-out不自动打开。

最终矩阵仍包含原NSG/Fast30K/GT10-hard/Web匹配起点和真实新方法，同机CPU15/threads1、五L五轮轮换、完整路由+原NSG+输出独立wall；GT/count/hash/build/load在外。保留aligned ID/GT集合评分、救回/新增、GT成员损益、完整成本及三指标/失败图；不同批不能拼方法曲线。若没有稳定改善，明确说没有找到，并保留Y局部质量与Web损伤。E69/E70有限质量门不等于最终方法GO，今日最终验证仍未完成。

所有P-fit/旧train/monitor/cal/audit/aux均历史暴露，辅助反馈计训练，不能把元数据余行说成全项目新盲集。所有旧原物/脏树/封存保留，每阶段source_before与root_after；不发消息给外部、不发布/推送、不改Codex配置。
