# E83 compact同hub画像连接补全

双集固定追加边实验完成。双集预锁质量门失败，停止本固定追加规则，不扫连边数/顺序或改选控制。 整日21:00目标未完成，原compact局部信号保留。

| 数据 | 主方法相对 | 净命中 | 救回 / 新增零命中 | 两半命中 | 路由 / 总NDC变化 |
|---|---|---:|---|---|---|
| WebVid | baseline10 | -60 | 44 / 54 | [-20, -40] | +8.97% / +0.51% |
| WebVid | compact10 | -1 | 1 / 0 | [-4, 3] | +5.16% / +0.32% |
| WebVid | neighbor10 | +8 | 2 / 2 | [-2, 10] | +3.50% / +0.21% |
| Yandex | baseline10 | +120 | 41 / 28 | [39, 81] | +23.05% / +0.83% |
| Yandex | compact10 | +0 | 0 / 0 | [0, 0] | +2.35% / +0.10% |
| Yandex | neighbor10 | +0 | 0 / 0 | [0, 0] | +1.54% / +0.06% |

原compact每hub最多3画像，主方法仅在原32容量内追加缺失同hub有向边，旧边及次序不变；控制同节点同新增度，改为最高完整画像内积的其他hub非邻居。两者不匹配新边长度，不能从边数控制单独宣称语义因果。Web新增1359、Y1285条/臂，图旧边15834/23063全部保留；缺边节点1140/1264，实际修改1139/1263，容量有限节点2/1。画像/label/header/层级/上层和原NSG均不变，没有新聚类或在线补偿。

全部4物理图独立解析、原边前缀/只改计数与未用邻接槽/回填原字节恢复及逐节点度匹配通过；近邻控制固定受影响行独立内积排序检查。在线原E73同SHA evaluator保持ef10/七slot去重三入口。所有ANN CPU15/实际进程及数值库1线程，四工具实际退出后分析。

实际129,536 NSG / 129,280 HNSW、4静态边安装、0普通build/训练/新GT/编译；native操作wall 111.127s，非QPS。安装/第一次prepare耗时未保存为未知；成功恢复检查耗时 3.297s。继承GT/画像训练成本未知。

完整集合/mask 64,640行、旧P/compact全字段31,808行恢复、原kernel256与完整plain/count、7slot/图身份通过。同三入口比较56,485行返回保持。失败并集410条，其中169条状态变化，全GT10/三入口/返回ID保留。旧收益丢失、旧损失修复、新损伤和GT成员变化分别在完整表。

准备阶段两个纯I/O元数据修正均保留：首次freeze把__pycache__目录当文件；恢复后四图均已安装/验收，但NumPy整型计数JSON失败。最终脚本仅核验既有图与转为Python int、冻结剩余配置，0重新安装/ANN。原源/失败记录/图不覆盖；未知耗时不填0。

全部aux7952/固定两半是历史router_train[2048:10000]选择训练反馈；P-fit包含旧train/monitor，cal/audit有历史暴露。E34最终/held-out未读，不改变旧门或默认。

[前瞻协议](protocol.md) · [完整配对](results/paired.csv) · [原值](results/points.csv) · [收益保留](results/gain_retention.json) · [质量门](results/gate.json) · [完整失败query](results/failure_queries.csv) · [质量/成本图](figures/sibling_links.png) · [失败图](figures/failure_queries.png) · [构图记录](results/construction.json) · [验收](reviews/verification.json) · [成本](results/cost.json)
