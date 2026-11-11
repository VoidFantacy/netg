# ACSG 后续研究边界

2026-11-10，当前授权任务为[E200四方法完整重测](entry_method_exploration/20261110_multimodal_four_method_retest_v1/protocol.md)：COCO/Flickr/WebVid/Yandex、NSG/GT10/GT10＋直接残差/GATE、K1/K100、每K20档L、每点两遍。冻结640点/1280批次，完整wall及两轮QPS算术平均；当前准备COCO/Flickr缺失的GATE模型，正式矩阵待资格核验和冻结。当前进程身份读[state](entry_method_exploration/20261110_multimodal_four_method_retest_v1/state.json)，必须现场核活性，避免重复启动。

先完成全部资产与角色核对、资格回归，再串行完整矩阵、原返回评分/独立核验及图表交付。保留所有实测点与两遍，不按结果增删到通过。用户未要求PDF，本轮交付文字/CSV/PNG/SVG。默认不自动替换。

本轮GATE为E97修正标签的外部入口基线；此前已停止的残差学习选点、短名单精排导航和前/后置门控仍停止扩展。原搜索与直接补点为当前研究主线；16K/8K为同法表版本，历史M5/SQ条件有效证据保留。原beam续搜、修图或新GNN不在本次范围。

论文要求见[写作约定](论文写作约定.md)。前一阶段完整目标和报告交付边界见[E200修改前快照](entry_method_exploration/20261110_multimodal_four_method_retest_v1/source_before/s-target.md)，E199及E183历史原件保留。本轮完成后依据实际曲线报告具体有效区间、完整成本与证据限制，不据准备或单个正点宣告完成。
