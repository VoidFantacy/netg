# 168 GT10代理、可见信息与局部有限搜索条件

2026-10-02下午独立阶段，用户指令“再研究到下午四点，先完善理论，不开始实验”。已按16:00（Asia/Shanghai，UTC+8）截止收口，COMPLETED_THEORY_ONLY_NO_EXPERIMENTS。最新真实性能166，默认Web GT10-soft-t1/Y GT10-hard、生产E99保持。

后续口径：“不需要节省训练时间甚至可以增加训练时间，但是综合qps recall要提高”。更充分离线训练/准备可以接受，在线所有新增费用和共享最快默认仍必须计入；此次不开始训练或实验。

## 范围与证据

[独立协议](../entry_method_exploration/20261002_theory_until1600_v1/protocol.md)、[主报告](../entry_method_exploration/20261002_theory_until1600_v1/report.md)。只做手推证明与解析反例、原论文和静态源码/封存结论审阅。0真实/合成搜索、0枚举、0新旧数组诊断、0训练/GT/构图/画像/性能、0新query/base向量。上午167的seal及41份artifact不修改、不重跑。

## 理论结论与未知前件

[GT10与真实效用](../entry_method_exploration/20261002_theory_until1600_v1/surrogate_to_search_theory.md)：画像精确最大化归属加权query一阶矩目标，目标ID不够确定有限响应；固定H画像算子可以代理最优而真实效用失配，同单位线性族存在更优规则。补共同vMF方向模型与真实响应桥的充分前件，区分服务类排序、有限搜索联合动作和完整QPS。

[决策信息与费用](../entry_method_exploration/20261002_theory_until1600_v1/decision_information_theory.md)：固定索引下target分数是完整query的昂贵函数，区分统计信息、表示与计算；正确signed效用/成本监督、条件校准、纯信息VOI和实际访问计划不能混用；付费回退与共享最快默认必须计入完整费用。

[前作与可否证性](../entry_method_exploration/20261002_theory_until1600_v1/theory_prior_and_falsifier_audit.md)：target-only响应与线性矩恢复的明确条件；归一化幅度/截距限制及E04/E25/E36/E118/E133/E164等直接碰撞。Bayes、vMF、loss embedding、utility residual均有直接前作，不以新名字重开旧分支。

[局部有限搜索](../entry_method_exploration/20261002_theory_until1600_v1/finite_search_strengthening.md)：完整行/满pool局部封闭、native ID/FIFO保护、安全路径与有序响应汇合；同实际入口容量前缀及额外Recall前件；ID/strict-score混合匹配。任意GTK的“新GT＋保护旧ID”粗界受K槽容量限制永不正，已独立修正，不能写成严格改善证书。

[整原拒收组省评分](../entry_method_exploration/20261002_theory_until1600_v1/certified_group_elision_theory.md)：全部原路径native上界≤满pool cutoff时，可保持原分组/visited/后续callback而保护逐ID输出；pivot正交或正交子空间残差给非空充分例。完整metadata和FP包络可更重离线准备，但在线覆盖率/净费用未知；FINGER/球界是直接前作，状态HOLD，无新实现。

[多入口与目标rank](../entry_method_exploration/20261002_theory_until1600_v1/joint_response_and_target_rank_theory.md)区分single、joint和K1/10/100；[增加离线投入](../entry_method_exploration/20261002_theory_until1600_v1/offline_training_and_online_gain.md)说明正确teacher合同与完整在线门。[论文清单](../entry_method_exploration/20261002_theory_until1600_v1/literature_manifest.md)记录19项下午独立工作的相关章节与3项上午复用，版本不重复计数、未称全文通读。

[命题台账](../entry_method_exploration/20261002_theory_until1600_v1/proof_ledger.md)、[实质修正](../entry_method_exploration/20261002_theory_until1600_v1/review_notes.md)及[人工审阅身份](../entry_method_exploration/20261002_theory_until1600_v1/proof_review_completion.json)分别记录条件、交审和三份冻结专题稿。交审通过不证明真实前件/净收益。无实现或实验GO；本轮已于16:00结束，旧实验停止门与产物保持。截止根交接文档以source_after副本、独立identity与本版本seal保留；行政核对不验证数学或性能。
