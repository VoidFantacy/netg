# 当前方法与刚提出的改进候选

这是2026-10-02 Git状态快照的补充说明，保存169交付之后的对话提案。**提案未实现、未训练、未实验，没有Recall或QPS改善结果。** 最新真实性能记录仍为166，169为已封存的GT10理论与论文框架。

## 已实现与当前默认

生产使用E99搜索核；WebVid默认GT10-soft-t1，Yandex默认GT10-hard。沿用冻结底图、真实hub、闭式query画像、Micro-HNSW路由及真实三入口联合搜索。现行构建代码为[build_fast_entry_variants.py](../../benches/run/build_fast_entry_variants.py)，架构与计时口径以[spec.md](../../spec.md)为准。现行GT10算法、理论前件及证据边界详见[169算法稿](../../entry_method_exploration/20261002_gt10_paper_theory_v1/algorithm_and_falsifier.md)与[论文主稿](../../entry_method_exploration/20261002_gt10_paper_theory_v1/paper_manuscript.md)。

当前问题是：目标与hub在向量空间接近，不保证有限候选池搜索能从该hub到达目标。169补齐了条件理论与正反构造，但没有改变生产算法，不能把理论稿称为已经改善性能的新方法。

## 候选：容量约束的图服务归属监督

只提议替换离线GT10归属权重；保留原hub集合H、画像维度、画像数量、先验、Micro-HNSW及线上三入口主搜索。较重离线工作可以接受，成功仍须表现为完整在线Recall–QPS改善。

训练预算L0在观察新反馈前固定，B=floor(L0/3)。对训练query q，用固定原生评分sigma_q(v)定义所有hub和目标共用的阈值tau。C_tau(q,h)是从h出发、仅沿sigma_q(v)>=tau节点可达的有向组件；sigma_q(h)<tau时组件为空。合格hub集合为：

    E_tau(q) = {h in H : sigma_q(h)>=tau and |C_tau(q,h)|<=B}

对真GT1至GT10的每个目标t_j，记n_j(tau)为E_tau中可以在该组件到达t_j的hub数。tau必须满足|E_tau|>=3且所有n_j>=1；否则不具备本提案的监督前件。

在有限基础评分阈值集合中，按事先固定的字典序选择tau*: 最大化min_j n_j，再最大化sum_j n_j，最后取最大tau。所有hub/rank共享一个tau*，不能各自选择阈值后拼接证书。

    w_h(q,t_j) = 1[h in E_tau* and t_j in C_tau*(q,h)] / n_j(tau*)
    a_h(q) = (1/10) * sum_{j=1..10} w_h(q,t_j)
    p_h = normalize(unit(h) + sum_i a_h(q_i) * unit(q_i))

若不存在合格tau，则整条query回退现行GT10归属，不按rank混合回退。画像仍由unit(query)聚合，训练目标向量不进入线上。**不存在这些权重的实际生成器或新画像文件**；上式是待研究的算法定义。线上也不执行阈值枚举、组件查询或全base扫描。

## 条件保证与未解决问题

只有当新query实际选出的三个hub都属于它在同一tau下的E_tau，且实际L>=max(L0,K)、评分/候选池满足169原生组件前件时，组件并集才有|union C_tau|<=3B<=L0的容量界，并能使用169的有限搜索发现结论。GTK的最终保留还需要真实GT及严格评分分离条件。若原生浮点评分并非可复用的固定势函数，还需有效评分区间/安全势函数版本；不能直接把实数证明套入任意实现。

训练时每个目标存在至少一个合格hub，**不保证预测出的top3覆盖全部GT10，更不保证覆盖GT100**。新query的合格率、画像学习的泛化、真实NSG上的组件规模均未知。L>L0时仍可能展开组件外节点，组件容量界也不是完整QPS界。线上结构规模保持不能证明相同wall时间；缓存、访存、路由、主搜索、输出及增量费用都必须实测。

潜在区别是“具有联合容量界的目标服务归属”，不是泛称graph teacher、效用监督或更重训练。E08、E22、E28、E118已经涉及实际搜索反馈与联合动作；不能用换名重复这些方法。后续最小控制须包含原GT10、E08 winner-centroid及E28真实联合teacher，并匹配query监督、H、物理容量、线上调用链与费用口径。阈值、预算和失败后的调整规则须在新反馈前冻结。

## 接续边界

目前仅保存提案。下一步首先审查容量条件是否过严、对新query怎样产生可迁移监督、以及与最接近前作的实质区别；这些未解决前不能声称创新已经成立或足以发表CCF B期刊。用户要求“先完善理论，不开始实验”仍有效，本次Git提交没有启动训练、GT、构图、ANN或性能测试。
