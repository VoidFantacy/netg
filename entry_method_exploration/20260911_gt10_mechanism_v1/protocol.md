# GT10机制分析：既有证据阶段

2026-09-11。依据用户本轮接续指令与根s-target第3节。E24/E25/E26保持已完成身份，本目录独立保存分析、输入指纹和后续解释，不重启第一方向。

当前阶段新增NSG搜索调用上限为0。只读已有fit/query/GT、画像、逐query返回、计数与计时；按E24原float32目标评分和float64归属累加规则重算fit权重，核对已有digest。所有输出写本目录。不得访问held-out，不生成新训练标签，不训练新方法，不覆盖旧画像。若A–C显示必须补测，先另存补测协议、配置和硬预算，再执行依赖步骤。

主对照为两数据集GT10 hard与GT1 hard/matched Fast20K，五L全保留。GT1/GT10 soft为辅助，使用原cal冻结温度；额外保留cal全部温度表，不能重新挑选。NSG/Fast30K为上下文。E25/E26重复只按真实画像身份连接，WebVid A1是GT10 soft，Yandex A1是GT10 hard。

1. 复核E24全部cal/audit/validation原输出的GT10集合评分、row IDs、线程与计时字段。分别报告同L变化、原始实测非支配点和各历史计时批次；不插值宣称等Recall加速。
2. 保存fit每rank真实hub归属、GT1向其它hub的质量转移、每hub mass/ESS/支持query数/方向集中度及画像角位移。每query权重和1。支持与画像几何只作描述。
3. 对全部query连接三入口、命中/mask、route/graph NDC；相同实际三入口的结果bits及graph NDC必须相同。按全部正/零/负事件、零命中救回/新增失败、入口重合数、原支持与画像位移分层。预先固定分层特征为A0所选入口平均log1p(ESS0)、平均画像角位移、入口重合0/1/2/3；分位边界只用E24 cal特征，不由validation标签选择。跨L仍以同query连接，不挑正点。
4. 使用原cal/audit exact3与HNSW3，计算hard主对照在两种检索下的真实联合搜索收益。两者的差只表示检索后端的交互，不是效用oracle。必要时只读计算画像精确分数与边界间隔，不调用NSG。
5. Recall与速度分别解释。route NDC、graph NDC、独立route/graph wall与总wall分开；无逐扩展trace或硬件计数器时，不声称已经观察到更短路径或更好cache。

所有分段均已被历史开发使用；validation启发过本次问题，不能称盲测。配对query bootstrap仅描述既有样本，固定seed20260911、2000次、不作多重校正确认性结论。重复计时不增加Recall样本。E25/E26的75%/25%只解释增强方案，不用于否定GT10。

本阶段交付existing_evidence.json、完整CSV/逐queryNPZ、来源manifest、验收、已有证据报告；据此固定最小补测或明确尚未区分项。最终同步summary/spec/s-target/s-experiment及独立历史记录；不自动启动2A、3A、聚类或rank。
