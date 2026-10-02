# E71 搜索宽度改进的同批完整wall（前瞻协议）

2026-09-13，第4串行会话。E70 Yandex质量接续门通过，WebVid未通过，原E66门保持。完整wall只验证既定候选成本/收益，不依曲线再调ef、模型、阈值、图或seed。E34历史最终validation留晚间，held-out不打开。

固定同一历史开发2048=router_train[2048:4096]，它是E64/E66/E70已用于辅助训练/选择的子集，不能当独立泛化。输入逐字引用E67冻结query/GT/row IDs。两dataset同一原base/rawIP/NSG/H/GT，完整返回aligned。baseline P为WebGT10-soft-t1、YGT10-hard；原Fast30K是GT1历史训练量对照。

每dataset包含NSG、Fast30K、GT10-hard、P30、mode10、mode30；Web另匹配P10 soft，Y P10即hard。mode30是本阶段实际新候选，best_new仅作为绘图字段别名；mode10与P30用于区分模式和通用宽度成本。全部L64/128/256/400/800，Web35点、Y30点，总65点325wall，不拼E67/E65旧曲线。每点一次完整warmup、五次独立整批plain wall，按dataset/repeat/L轮换方法；没有训练/标签生成/其它测试同时运行。

使用E70已经通过原baseline/多slot验收的同SHA binary。ef_search10或30，graph_file直接引用冻结图，plain/count均全W/label校验；0训练/构图/图物理复制。完整在线raw-query HNSW路由、7slot排序去重或原单画像映射、canonical真实入口、原NSG、预分配输出在计时内。GT/count/hash/JSON/build/load及全部评分在外。route-only/graph-only本阶段不额外测，null并说明；不可由离线缓存或NDC估QPS。

所有ANN及性能CPU15、显式threads1、OMP/OpenBLAS/MKL/NUMEXPR/BLIS1；启动后核验/proc线程/affinity，单native串行，工具terminal exit0后才开始下一集或重分析。每点全plain/count和五轮返回bits一致、16query原kernel对照；旧NSG/Fast/GT10全五L恢复E65，mode10全五L恢复E67，P30/mode30及匹配P10/mode10 L128恢复E70前2048。源图SHA及五L完全相同路由/slot保持，独立集合评分与GT成员增损核验。

新NSG=65*(7*2048+16)=932880，HNSW=55*7*2048=788480，原kernelreference1040包含于NSG总数；55 plain源图加载+55 count加载，0build/0新GT/0梯度。Web预留502320、Y430560，硬限960000，失败全预留且不自动重试。单job<=1200s，13:00后不启动本阶段query、13:08硬停，13:20:37前安全封存交接。free>=7GiB、累计新目录<=64MiB、RSS<=32GiB；引用大输入/小图，不删旧字节，给晚间最终批次留余量。

评分：Recall@10集合、严格零GT10失败、救回/新增与GT成员找回/丢失分别保存；逐query净命中正负部不混同成员。输出全部65点/325轮、QPS–Recall、QPS–失败率、按L三指标、配对差和失败query图，全量失败CSV，图最多每集24例并明确省略。描述性query bootstrap2000次与五轮QPS交叉范围分开；共同Recall范围的log-QPS插值只能描述，不当测得等Recall点。局部正信号/损伤/不确定性并列，不由同LRecall、单轮差、训练或有限精确分数声称最终改善。若没有稳定整体前沿改善就如实报告，不因开发子集局部结果回写E70两半或E66门。

完成后详细历史60、四主文档、candidate inventory含ef接口身份、campaign handoff/state及全成本。整日20:00训练停/20:40新增query停/21:00最终交付保持未完成。
