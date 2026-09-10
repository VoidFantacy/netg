# ACSG 当前实验总结

> 更新至2026-09-10。当前最近实验为E23三入口收益排序探索。实现见[spec.md](spec.md)，接续边界见[s-target.md](s-target.md)，历史见[s-experiment.md](s-experiment.md)。

## 当前结论

**E23已完成：小幅Recall正信号，尚无明确整体QPS优势。** 固定真实入口，匹配Fast三个互异入口，用真实三入口条件收益训练Fast锚定完整W，并与同目标rank8对照。两数据集各validation2000、一个QGT构建、L64/128/256/400/800、单线程，NSG/Fast30K3/Fast20K3/Full3/Rank8-3共50点全部完成。状态`EXPLORATORY_SMALL_RECALL_SIGNAL_NO_CLEAR_QPS_GAIN`，不自动追加模型、rank、seed或计时。

完整W的固定训练目标优化到位，且目标值低于同λ的rank8，但未取得一致的最终搜索优势；Yandex五点Recall均是rank8高于完整W。不能把更低训练损失直接写成方法性能更好，也没有依据丢弃低秩或直接加MLP。

同日完成用户提出的[GT入口/聚类/rank/OOD路由图四问题调研](entry_method_exploration/20260910_ood_hubs_clustering_router_research_v1/report.md)：核对14项一手工作及已有诊断，澄清代表query的GT候选选hub与GT1构建画像是两步；rank8未做充分容量比较，精确画像top3也不是实际入口效用oracle。此项为`RESEARCH_COMPLETE_METHOD_UNSELECTED_UNRUN`，没有新实验结果；候选与接续见[s-target.md](s-target.md)。

用户随后要求详细整理全部讨论方向及优先级。[s-target.md](s-target.md)现以`NEXT_EXPERIMENT_DIRECTION_DEFINED_UNRUN`记录：优先固定H的GT1/GT10×硬/软画像，其次真实finite-L效用分组/挑入口，另有保分数拉伸微型图效率支线；聚类器、rank容量、三入口联合评分及raw-IP范数问题分别展开。各方向给出方法、必要对照、进入/停止依据、产物和新对话指令，运行协议待启动时冻结。本次仅文档交接，没有新实验结果，E23结论不变。

## 相对matched Fast20K-3的五点变化

每格为ΔRecall百分点 / ΔQPS百分比；每点一次独立plain wall，小幅差异不作稳定加速或显著性解释。匹配相同20K画像输入、H、三个入口、HNSW参数/seed和入口消费顺序。

| 数据集 | L | Full-3 | Rank8-3 |
|---|---:|---:|---:|
| WebVid | 64 | +0.070 / +0.23% | +0.035 / +0.45% |
| WebVid | 128 | +0.160 / +0.59% | +0.140 / -0.09% |
| WebVid | 256 | -0.005 / +0.87% | +0.010 / -1.10% |
| WebVid | 400 | +0.045 / +0.91% | +0.055 / +0.92% |
| WebVid | 800 | +0.030 / -0.95% | +0.045 / -0.07% |
| Yandex-IP | 64 | -0.065 / -0.00% | +0.100 / +0.05% |
| Yandex-IP | 128 | +0.105 / +0.53% | +0.290 / -0.09% |
| Yandex-IP | 256 | +0.005 / -2.96% | +0.120 / -1.50% |
| Yandex-IP | 400 | -0.030 / +0.52% | +0.095 / -0.68% |
| Yandex-IP | 800 | +0.015 / -1.11% | +0.060 / -0.25% |

L128原值：WebVid Fast20K→Full为74.260%/1997.81QPS→74.420%/2009.57QPS，零命中54→52；Yandex Fast20K→Rank8为89.720%/1960.73QPS→90.010%/1958.90QPS，零命中38→34。原Fast30K和NSG始终另列；例如WebVid Full对原Fast30K的+0.430pp包含matched Fast20K本身的+0.270pp，新增学习为+0.160pp，不能全部归于学习器。

## 实际执行与证据边界

- 原raw-IP/NSG不变，QGT seed20260828；一向量对应一真实hub，在线raw query→HNSW direct3→原kernel。matched Fast20K与学习模型按真实ID升序消费三入口，原Fast30K保留原heap顺序。模型不输入L，每query入口跨五L完全不变。
- fit20K×24个逻辑组合：两数据集合计96万逻辑标签，缓存后88万实际标注搜索，另2304次parity。Full/rank8各三个λ，共12候选；cal1024选λ，audit1024不参与选择；双数据集全部模型冻结后才读取validation2K。该开发池是历史开发数据，held-out未打开。
- Full在WebVid/Yandex均选λ=10/0.1，rank8相同。两数据集cal都选新候选；audit中Full均小幅正值，Yandex rank8小幅负值；最终validation结果全部保留，没有按validation换模型。
- 全部100000个validation输出独立GT评分、单线程及原kernel/plain/count验收通过；NSG/Fast30K共40000个query输出、入口与距离bits和E22逐位相同。
- 标签子进程58.89秒、训练137.45秒、fit-probe/cal95.68秒、audit29.05秒、最终五点比较381.64秒。均含各自过程工作，不能称查询QPS。完整W六个模型核心拟合约7.35秒、rank8约125.78秒。
- 本轮复用旧全H single标签提出候选；按当前提议器从零复现还依赖3272万份single标签。88万新增联合标注不是完整从零成本；exact GT/QGT/原图和single子集专属重建成本未新测。
- graph NDC变化很小，Yandex路由NDC略增。fit中观察到同一query的a/b偏好随另外两个入口改变，说明条件排序标签存在不能同时满足的部分；未将它定量归因为全部性能差距。一个构建、validation2K、单次wall不支持正式性能GO。

## 权威证据

- [E23详细复盘](experiment_history/12_three_entry_rank_exploration.md)、[完整报告](entry_method_exploration/20260910_three_entry_rank_v1/report.md)、[全部50点原值](entry_method_exploration/20260910_three_entry_rank_v1/results/tables.md)、[Recall–QPS图](entry_method_exploration/20260910_three_entry_rank_v1/figures/recall_qps.svg)。
- [结果JSON](entry_method_exploration/20260910_three_entry_rank_v1/results/summary.json)、[指标CSV](entry_method_exploration/20260910_three_entry_rank_v1/results/metrics.csv)、[配对比较CSV](entry_method_exploration/20260910_three_entry_rank_v1/results/comparisons.csv)、[成本账](entry_method_exploration/20260910_three_entry_rank_v1/results/costs.json)。
- [输出核验](entry_method_exploration/20260910_three_entry_rank_v1/reviews/result_verification.json)、[模型冻结](entry_method_exploration/20260910_three_entry_rank_v1/models/frozen_before_validation.json)、[最终审计](entry_method_exploration/20260910_three_entry_rank_v1/reviews/final_audit.json)。

E22保留`EXPLORATORY_NO_OVERALL_FAST_GAIN`历史身份，原大矩阵不恢复；C仍按E21停止，无C联动。所有原源码、图、GT、标签、模型和结果保留。
