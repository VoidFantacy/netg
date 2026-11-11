# ACSG 后续研究问题

更新于2026-10-27。目标仍是相对当前默认的**可靠Recall–QPS综合改进**。GT10默认与E99共享核保持；E185/E184离线诊断、E183性能矩阵已完成。新的[E186适配补全设计](entry_method_exploration/20261027_adaptive_completion_design_v1/design_zh.md)状态为**THEORY_ONLY_UNIMPLEMENTED_UNTESTED**，只记录本次讨论形成的方案与验证顺序，没有启动实验队列。

## 当前判断

当前固定ID表依赖遗漏目标在新query中重现、路由可取到和有限槽位可保留。E184显示Deep/SIFT源外主导，GIST还受路由/选择限制；E185支持局部几何连续性与遗漏共享有关，不支持简单“越低维越有效”，也没有给出净收益准入器。当前数值、费用和证据限制以[summary](summary.md)为准。

用户的失败定义保持单条Recall@100<10%，即0–9个GT100命中。该查询比例、平均Recall、成员救损和完整QPS分开；不以广义遗漏改善替代严重失败修复。

## 优先一：先证明一个新候选来源有成本优势

E186的主候选是：从独立覆盖整个base的几何分区/倒排后端检索候选，用合法训练query的**区域级遗漏**及主搜索真实返回摘要引导补查，最后按原metric精算合并。现有ID表作为基线与可保留动作。全base登记不等于有限扫描预算能覆盖全部目标；必须验证实际候选域。

提案先选COCO与Deep作正/负类型对照，真实K100、L=100/200/400，保留目标规模base和原图；比较GT10、固定B32、仅q区域选择与加入主结果R的区域选择。辅助分区/码本、额外RAM、扫描上限、独立角色和结束边界要在实施前冻结。候选域乐观覆盖不足以偿还开销时，停止该后端，不先训练复杂选择器。该pilot尚未运行。

## 优先二：证明主结果条件化优于简单区域检索

q-only与R-conditioned两策略必须用同后端、同成员来源/码本、同RAM及可选工作机会。主结果的区域数量不是正确GT数量；在线模型不能读取实际缺失、GT分离度、GT100局部PCA。若条件化没有额外收益，则保留简单策略或停止复杂主张。

E174/E175已有“残差候选作seed的一跳扩展”，E176已有PAIR/WIDE，旧理论也讨论return-ID键和预算器。新方案须实质改变候选来源；标准IVF/PQ与adaptive probing不作为创新本身。差异与前作见[E186](entry_method_exploration/20261027_adaptive_completion_design_v1/design_zh.md)。

## 优先三：在独立query上选择动作，允许不补全

先在独立校准角色选固定数据集/K/L配置：ID表、区域补全或不补全。只有来源确有收益、且同一数据内query异质性值得额外费用时，再做逐query选择。输入限线上可取得且已计费的入口/分数/结果摘要、离线支持统计及区域摘要；校准证据不能替代未参与选择的确认。

原E185样本和旧公共query已曝光，不能充当新的盲确认。SIFT/GIST/Web/Y/Flickr保留为扩展与反例，不按结果剔除；后续正式评估仍须覆盖真实K1/K100，分别核质量与端到端费用。

## 进入与退出条件

统一单方法串行、实际threads=1。记录辅助路由/选择器/码扫描/访存/去重/原metric精算/合并/输出完整wall，另披露索引RAM与构建成本。新增候选数相同不等于费用相同。

相同完整耗时下比较实际Recall，或同目标Recall下比较速度；更大L的GT10必须在预算附近充分测量，不能利用稀疏网格或插值制造优势。最低实际效应、计时波动、质量不确定性、损伤与严格低召回尾部指标事前固定，不按确认反馈增加样本或改表到通过。

当前只有设计文档，没有已实现辅助后端、区域模型、动作选择器、确认角色或新性能。历史STOP/预算与旧runner保留原身份，不自动恢复。范数敏感路由等旧提案仍为[理论归档](entry_method_exploration/20261011_norm_aware_profile_theory_v1/theory.md)。

## 历史目标与接续

旧阶段期限/旧CAL与confirm前件全文见[归档](experiment_history/_maintenance/20261024_current_state_cleanup_v1/archive/s-target.md)，不是今天的执行队列。2026-10-27修改前的本文快照在[E186 source_before](entry_method_exploration/20261027_adaptive_completion_design_v1/source_before/s-target.md)。

<a id="2026-10-03-新对话接续入口"></a>

历史交接锚点仅兼容旧链接；当前接续从[LOCAL_CODEX_START.md](LOCAL_CODEX_START.md)开始。
