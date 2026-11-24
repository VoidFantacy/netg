# ACSG 本地 Codex 入口

经典 L2 三曲线同期比较见 [E253](experiment_history/253_gt10_b32_mixed64_classical_v1.md)，288 点、576 批。纯 GT10 在 44 个固定目标中最快 41 个，GIST 有两个慢遍也更快的 Mixed64 达标点。

经典平方 L2 的 Mixed64 迁移见 [E252](experiment_history/252_b64_classical_retest_v1.md)。Deep10M、BIGANN-SIFT10M、GIST1M 的 192 点、384 批已结束，除 GIST 两个局部门槛外 B32 达标更快。

四集三方法最新同期比较为 [E251](experiment_history/251_b64_four_dataset_retest_v1.md)，已核真 K1/K100 的 465 点、930 批。WebVid 和 COCO K100 有明确达标速度优势，Flickr30k 与 Yandex 的适用区间见报告。

2026-11-23 B64 实验主线以 E243 扩训练、多档真遗漏表为当前研究候选。WebVid K100 三窗、COCO K100 与 WebVid 真 K1 的实际完整对照可从[逐轮记录](entry_method_exploration/20261123_b64_until1300/progress.md)进入。WebVid 同样本最佳单档的对照见[E247](experiment_history/247_b64_teacher_depth_ablation_v1.md)。生产继续按已发布的 GT10/SPAN4 合同。

2026-11-20 完成 E211 并切换默认。标准 Flat raw-IP 的 `ACSG::search_new(mode=2)` 默认走 SPAN4，L2 等其他距离路径走标量。四个真实数据集各3,072条，真实K1/K100各7个L，224点、448个完整CPU15单线程批次。112个新旧配对返回逐字节相同，112/112个配对通过逐点速度筛选。纯GT10完整QPS变化+13.74%至+28.35%，GT10+B32变化+13.16%至+27.94%。 当前无待恢复实验。

E230 WebVid 按入口分配 B64 实测 105 点、210 批，三方法曲线已完成。[E230 报告](entry_method_exploration/20261123_b64_entry_budget_v1/report.md)。

E229 四集真 K1/K100 B32/B64 正式比较完成 218 点、436 批，WebVid 低 L 已补测。[E229 报告](entry_method_exploration/20261122_b64_formal_four_dataset_v1/report.md)。

E228 全精算 B64 的两集 K100 异窗复测完成 80 点、160 批，保留为按目标选用的条件配置。[E228 报告](entry_method_exploration/20261122_b64_full_confirmation_v1/report.md)。

E227 两集 K100 B32 截止分双塔完成 44 点、88 批，生产补点基线为原版 GT10+B32。[E227 报告](entry_method_exploration/20261122_b32_cutoff_two_tower_v1/report.md)。

E226 两集 K100 双塔 B32/B64 完成 132 点、264 批。全精算 B64 为待复验候选，原版 B32 保留。[E226 报告](entry_method_exploration/20261122_b32_b64_two_tower_v1/report.md)。

E225 COCO K100 的候选探针分流完成 22 点、44 批，原版 B32 保留。[E225 报告](entry_method_exploration/20261122_p64_candidate_probe_v1/report.md)。

E224 COCO K100 的 B32/P64 分流完成 66 点、132 批，原版 B32 保留。[E224 报告](entry_method_exploration/20261122_p64_residual_gate_v1/report.md)。

E223 两集 K100 全精度回放过线，COCO 32/64 维粗排完成 66 点、132 批。[E223 报告](entry_method_exploration/20261122_group_residual_rerank_v1/report.md)。

E222 组内联合短尾表完成 COCO、WebVid K100 的 132 点、264 批，原版 B32 保留。[E222 报告](entry_method_exploration/20261122_joint_residual_tail_v1/report.md)。

E221 Q8 安全上界完成两个 K100 场景与 WebVid K1 的 107 点、214 个完整批次。[E221 报告](entry_method_exploration/20261121_q8_certified_pruning_v1/report.md)。

E220 等价 Q8 提速完成 11,952 状态回放及两个 K100 场景 80 点、160 批 CPU15 单线程验证。[E220 报告](entry_method_exploration/20261121_q8_equivalent_speed_v1/report.md)。

E219 完成候选 ID 粗排和尾部交换。COCO K100、WebVid K1/K100 的 主网格 162 点、324 批，加密 60 点、120 批，CPU15 单线程 已核验。[E219 报告](entry_method_exploration/20261121_bucket_id_reranking_v1/report.md)。

E218 完成入口桶选择器和同预算双表精确回放。COCO K100 / WebVid K1 三版线性选择均未过两窗质量资格；WebVid K100 双表上限在校准窗超过 L192 59 个正确成员。[E218 报告](entry_method_exploration/20261121_bucket_gain_selection_v1/report.md)。

E217 复用三路 GT10 入口做代表查询桶。两集真 K1/K100 共 15,906 个回放状态，四场景正式资格为 0。较宽桶在 COCO K100 和 WebVid K1 有精确动作上限余量。[E217 报告](entry_method_exploration/20261121_gt10_bucket_residual_v1/report.md)。

E216 在 COCO、WebVid 跑在线近邻补点，主网格 160 点、320 批，局部加密 59 点、118 批。加密 WebVid K1 CACHE 相对最快达标控制 +1.67%，COCO K100 −2.65%。[E216 主报告](entry_method_exploration/20261121_neighbor_residual_online_v1/report.md) · [加密对照](entry_method_exploration/20261121_neighbor_residual_online_v1/confirmation_result.md) · [E215 候选来源](entry_method_exploration/20261121_b32_cross_budget_tails_v1/report.md) · [E214 四路补点](entry_method_exploration/20261121_b32_batch4_scoring_v1/report.md)。

先读 AGENTS、summary、spec、s-target、s-experiment，再读 [E211 报告](entry_method_exploration/20261120_span4_production_default_v1/report.md)、[E211 历史卡片](experiment_history/211_span4_production_default_v1.md)、[状态](entry_method_exploration/20261120_span4_production_default_v1/state.json)及[发布验证](entry_method_exploration/20261120_span4_production_default_v1/reviews/release_dispatch.json)。

后续 raw-IP GT10 性能实验链接新构建的 ACSG 或使用[发布构建记录](entry_method_exploration/20261120_span4_production_default_v1/release/build.json)。查历史实验时使用其冻结二进制。[切换前源码与文档](entry_method_exploration/20261120_span4_production_default_v1/source_before/)及[旧数据简档](experiment_history/_maintenance/20261119_obsolete_payload_prune_v1/archive_index.md)。

GitHub 阅读入口与外部数据依赖见[本次发布](research_snapshots/20261124_acsg_research/README.md)。
