# E47：局部画像的完整训练池反馈RL/ES

2026-09-12。用户要求持续至20:00，并强调大胆假设、小心证明。明确检验假设：小批次遗漏质量反馈是局部画像学习失效的重要瓶颈，完整反馈可以改善真实确定模型。E45同状态全池单步有小正值，E46精确反馈复用/费用门已通过；本版本执行真正训练检验，保留E43/E44停止结论，不追加幅度或epoch网格。

## 唯一训练反馈修订

保持E43原P/B/scale/H、独立H×16行参数化、σ.3、200步、cosine步长.03→.003、Adamβ.9/.999/eps1e−8、梯度clip1、μclip±2、每hub局部计数。两集RL/ES双seed20260921/22，共8次；hub日程逐位复制E43的GT无关baseline三入口多重集合抽样，ε仍同seed按原RL8独立或ES4对生成。不改变原NSG/raw-IP/L128/K10/三真实入口升序/HNSW M16/efConstruction200/efSearch10/seed20260828。

每步当前J与八候选J都用完整train4096，原命中/总NDC/零命中/画像漂移权重不变。RL/ES估计器和局部Adam沿用E43。query batch128不再用于奖励；旧batch日程只保留对照身份。它与E43是反馈覆盖/实际计算量都变化的跨版本修订，不称等query费用消融；本轮RL/ES两臂具有同完整信息、步数/候选数和HNSW次数，实际新增NSG由入口变化决定并单列。

使用E46已验收二进制和空增量安全封装：候选真实route4096，只有相对当前C三入口改变的query新调用原NSG；其它query复用当前C完整结果，全部当前route NDC更新。GT只评分新真实返回，未变入口的命中从同身份当前缓存复制。每次确定均值Adam更新后也build/route4096并补齐变化query，替换当前完整缓存；下步不得使用过期C。

## 冷启动、监控与产物

每次训练开始都普通build(P)并实际run4096，逐位恢复原E37基线及GT命中；不把初始反馈免费记为缓存。每20步及0点评估monitor1024真实查询，train512从该步已测全池缓存提取；完整checkpoint保存全W/μ/m/v/count、train4096完整缓存与monitor1024返回。monitor只用于原非零checkpoint选择：U最高且graph NDC≤+1%，无可行者记录fallback，不选采样最佳动作。

每步保存动作前行参数/动量/计数、ε/候选行/W与拓扑hash、全部J/梯度/Adam和确定next_row；候选/均值各保存完整route NDC、实际路由entries hash、变化行及其完整ID/距离/三入口/graph NDC patch，足以重放完整4096反馈。只省去已知相同返回的重复存储；不能用未测格填0。保存当前/候选/均值完整缓存hash。最终selected/last保存静态W/μ/物理HNSW，32train+32monitor三路parity。

独立分析从冷启动和patch重放所有逻辑反馈，独立GT集合评分全部新增返回、核验所有复用键与路由hash、完整奖励/梯度/Adam/参数/W身份、全部checkpoint和16导出。逻辑反馈数量、实际新增NSG、复用行数和独立新GT评分数分别计账，不声称复用行又发生真实搜索。

## 预锁判断

原E43 monitor门保持：每数据集每arm至少一seed选中非零checkpoint ΔRecall>0、U>0、graph NDC≤+1%；双集同时满足才考虑冻结后的下一开发控制。未满足停止本完整反馈版本预算扩展，保留局部正值，不调σ/epoch或替换默认。所有monitor已有历史使用，不能称盲测/泛化或完整性能GO；RL相对ES的优势须由同轮实际结果判断，不能因两臂均有进步就归因RL。

主比较为同模型族训练后的实际train/monitor质量、收益损伤/零命中/NDC、采样候选响应频次、确定均值响应频次及成本。当前版本没有新增cal/audit/validation/held-out/GT/QPS；任何后继另建身份，不偷换monitor为正式性能。

## 预算与截止

每run初始4096+11×monitor1024+两导出3×64=15744固定NSG，另加候选及每步均值真实变化query；每run完整预留100000，8run共800000硬限，失败不释放、不自动重试。每dataset native NSG cap400000；每个调用前核对run剩余预算。实际HNSW每run7388416，总59107328；native每集HNSW cap30000000，全硬限60000000。每run1803 build（初始1+200×9+导出2），总14424，硬限15000；原native per-dataset7500保持。

CPU15、实际进程/OMP/OpenBLAS/MKL1，方法/seed/数据集串行；分析CPU8，地址空间32GiB，产物512MiB、可用至少9GiB。每dataset进程timeout3600s，19:35训练硬截止；启动第一数据集前以E46保守投影重新检查预计结束<19:25，后续dataset据实际已用时间及剩余工作核对，不以晚启动重置截止。

实现/离线成本含真实route/build/查表/复制/新NSG/monitor/导出，计数进程wall不是线上QPS。保护E37–E46及原native/NSG依赖、根文档前件。20:00前完成验收/文档；如果时间/调用预算触发，保留已完成/部分模型与完整账，不拿partial冒充8次完成。训练反馈与缓存的实际信号/成本将决定接续，默认保持。
