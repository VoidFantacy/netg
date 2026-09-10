# 五点单线程探索比较

2026-09-09用户授权：L=64、128、256、400、800，其他按精简探索方案；随后询问为何模型不能适应所有L。模型本身只接收query并选择入口，可用于任意L。本轮统一固定同一个L128标签训练的冻结模型，检验其跨L表现，不按测试预算更换模型。

- 数据：WebVid2.5M、Yandex official first10M，原raw IP、原冻结NSG，K10。各取现有validation名单前2000行，行号固定且三方法相同；不读held-out。
- 单个QGT构建seed20260828。仅比较NSG-Medoid、历史Fast30K direct3、A+B联合新候选。Fast原M16/efConstruction200/ef10、HNSW seed100及heap顺序保留。A+B采用L128模型在原1024 calibration中选定的新checkpoint，五个L使用同一W和mapping，不重训练、不重选、不使用Fast fallback。
- NSG沿用项目定义：固定index.acsg.enterpoint，直接调用原search_new(mode2)，无query条件路由。所有方法使用同一图和kernel。
- 五个L下，三个方法各一次完整2000query warmup和一次独立完整batch wall。单线程，OpenMP/OpenBLAS/MKL均为1；按L和dataset轮换方法先后顺序。只测端到端，不另测route-only/graph-only，不增加种子、消融、exact对照或计时重复。
- wall包含路由、ID映射、原图搜索和正常预分配输出；GT评分、hash、JSON、索引加载/构建和正确性检查在timer外。每点仅16条query做count/plain/独立原kernel入口重放；完整warmup和计时输出逐query核对。高L的retset预留801槽，实际原kernel按L+1使用。
- 主指标Recall@10、QPS、失败数量和失败率；失败严格Recall@10<0.1，即GT10零命中。对NSG和Fast分别计算Recall差值pp、QPS百分比、失败率差值pp/相对变化，以及挽救/新增失败query数。
- 单seed、validation2000、单次计时仅用于探索，完整呈现收益和损失，不给正式显著性或跨构建稳定性结论。L128模型用于其他L是预算迁移评测；不会把高L结果写成对应L已训练。
- 仅产生30个方法×L×dataset组合，共120,000次正式图搜索调用（warmup与timed各一次），另有960次小样本原kernel正确性调用。旧大矩阵和队列均保持停止，原标签、模型、结果不覆盖。

产物：原始aligned结果、配置与源码/模型身份、CSV、相对比较JSON、两数据集Recall–QPS和失败率图、简明报告。当前实验收口以此用户修订范围为准，不再以已取消的大矩阵为完成要求。
