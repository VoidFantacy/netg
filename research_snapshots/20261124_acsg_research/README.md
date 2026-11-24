# ACSG 当前研究与实验

2026-11-24 发布。论文主线为 GT10 查询条件化入口与搜索后直接补点。多模态数据是补点的主验证场景，Deep10M 和 BIGANN-SIFT10M 保留 GT10 入口迁移的对照。

- [当前结论](../../summary.md) · [实现契约](../../spec.md) · [实验索引](../../s-experiment.md) · [论文写作约定](../../论文写作约定.md)
- [多模态四集 Mixed64](../../experiment_history/251_b64_four_dataset_retest_v1.md)，WebVid K1/K100 与 COCO K100 的达标提速证据最明确。Flickr30k 收益局部，Yandex 保留 B32 对照。
- [三套经典 L2 的三方法曲线](../../experiment_history/253_gt10_b32_mixed64_classical_v1.md)，纯 GT10 在 44 个固定目标中最快 41 个。两处 GIST 的新表局部收益按具体门槛和 L 解读。
- [五集入口对照](../../entry_method_exploration/20260916_optimized_five_dataset_r1_r100_v1/report.md) · [NSG 与 GATE 多模态对照](../../experiment_history/213_span4_gt10_b32_nsg_gate_v1.md)
- [发布文件清单](manifest.json)

本次包含项目文档、E213–E253 已记录实验的卡片和报告、主要对照的曲线、实测表、源码、输入配置及小型补点表。完整底库向量、索引、测试真值、训练数据、编译产物和逐查询原始包保存在实验环境。冻结和 seal 文件描述服务器上的原始实验，部分路径需要本地依赖才能重放。

E251 的四集对照为 B32、老 B64、Mixed64。E253 的经典 L2 三臂为纯 GT10、GT10+B32、GT10+Mixed64。多模态的同口径纯 GT10 三臂比较仍是后续工作。
