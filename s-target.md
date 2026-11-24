# ACSG 后续研究边界

当前新 B64 的研究主线为复用原 B32 前缀，扩大真实漏点监督，提高同 L 的候选质量，再用实测挑达标的 L。WebVid K100 三窗、COCO K100 与 WebVid K1 已分别形成实测正证据。WebVid 同样本最佳单 L176 与多档在 75.5% 达标使用同 L，COCO 97% 的二次复测同样如此。同样本对比未建立混合相对强单档的可重复额外收益。下一轮论文对照保留同一样本最佳单档、样本规模对照、原 B32 与老 B64。四集同期 E251 将速度证据最明确的区间定位于 WebVid K1/K100 和 COCO K100。Flickr30k K100 有相对 B32 的局部条件，Yandex 复用 B32 对照。按数据集、实际 K 和召回门槛选择，完整时间与原生返回并重。 [四集复测](experiment_history/251_b64_four_dataset_retest_v1.md) · [逐轮记录](entry_method_exploration/20261123_b64_until1300/progress.md)

E253 的经典 L2 三方法证据以纯 GT10 为优先速度对照，同期仍保留 B32 量化补点收益。GIST1M 的两个达标速度正点按具体门槛和实测 L 解读。若扩展这两处，需要相同条件下的密集 L 及另窗复测。[E253 报告](entry_method_exploration/20261123_gt10_b32_mixed64_classical_v1/report.md)。

E230 已验证 WebVid 的 B64 配额分配。K100 在相同实际候选工作下，按画像距离的 64/64/40 稳定提高同 L 质量，和老 B64 的端到端速度取舍随目标变化。按 E230 固定目标表选用；若继续优化，可在独立训练角色上探索每路尾部收益，保留原 B32 前缀、均匀 B56 和老 B64 控制。 [E230 报告](entry_method_exploration/20261123_b64_entry_budget_v1/report.md)

E229 已完成 E228 的四集真 K1/K100 扩测与 WebVid 低 L 补点。近期按同期固定召回目标使用两臂实测配置，WebVid K1/K100 优先检查已证实的 B64 区间，Yandex 使用原版 B32。COCO K100 的可用收益以 E228 密集窗口与 E229 固定网格的共同证据为准，Flickr30k K1 仅保留单个达标正例。其他查询范围和硬件仍按新场景实测。 [E229 报告](entry_method_exploration/20261122_b64_formal_four_dataset_v1/report.md)

E228 完成了 E226 全精算 B64 的异窗密集复测。COCO 和 WebVid K100 在多个固定召回目标上能用较小 L 获得更高完整 QPS。按实际召回目标选 B32/B64 和各自 L。若扩大采用范围，先测相应的数据集和 K，并补齐 WebVid 低召回目标的 L168 以下范围。 [E228 报告](entry_method_exploration/20261122_b64_full_confirmation_v1/report.md)

E227 关闭这轮 B32 截止分双塔的默认替换。若继续 B32 内筛选，先用校准中真实补回成员设定损失界，并在完整链路上证实新筛选开销低于省下的精算；重点看同召回达标点与两遍速度范围。固定 16 维当前实现与上一轮 48 名短名单已具备同校准窗质量对照。 [E227 报告](entry_method_exploration/20261122_b32_cutoff_two_tower_v1/report.md)

E226 的下一比较对象为原版 B32 与全精算 B64。优先冻结扩表和路由，在另外的未参与双塔拟合/校准的查询窗密集测相同召回区间，复核跨窗完整 QPS、容量与实际候选数。若继续学习选点，以全精算 B64 和原版 B32 同时作对照，直接核真漏点保留率及完整费用；固定精算 48 的当前线性双塔已完成两集比较。 [E226 报告](entry_method_exploration/20261122_b32_b64_two_tower_v1/report.md)

E225 至多八个新候选的探针验证了已算分数的位级等价复用。L184 校准比旧线性门少触发 65 条、多净增 20 个。正式 L184 达到 B32 L192 召回，仍慢 9.13 μs/query。后续优化以同期原版 B32 完整前沿判定，区分探针固定成本与触发后动作时间。 [E225 报告](entry_method_exploration/20261122_p64_candidate_probe_v1/report.md)

E224 用主返回及已有画像分数对 B32/P64 分流，在 COCO 真 K100 保留局部实测达标点。L184 的两个门均未达到原版 B32 L192 召回。事后分流净命中上限 1,038 个，达到同期目标需 668 个，当前线性/树实际 657/464 个。后续采用判断依据近邻 L 的同期完整前沿及查询救损。 [E224 报告](entry_method_exploration/20261122_p64_residual_gate_v1/report.md)

E223 确认原距离可兑现 E222 单组候选的全部离线覆盖，COCO 的低维短码也保留了达标质量。正式优势只在局部实测点，按同期达标前沿保留条件候选。WebVid 校准组池中位数 430，P90 为 2,470，已测原型为全精度回放。评估 WebVid 低维版本时，按组池大小报告实际扫描量、救损和完整端到端费用。[E223 报告](entry_method_exploration/20261122_group_residual_rerank_v1/report.md)

E222 的单张组内 8/16 位短尾表已完成。单组选中后的训练遗漏并集有可达余量，当前离线压缩丢失大部分候选覆盖，两集无端到端达标吞吐收益。原版 B32 为补点基线。后续如继续条件化补点，围绕逐查询选 ID 的收益与完整开销比较，报告组内候选覆盖、实际救损和同期前沿。 [E222 报告](entry_method_exploration/20261122_joint_residual_tail_v1/report.md)

E211 已完成四集正式入口验证与默认切换。后续 raw-IP GT10 及该链路上的残差成本比较采用 SPAN4，旧标量内核可作显式对照。L2 采用标量，并完成了发布兼容性验证。当前无待恢复实验。

B32 的候选质量和额外开销依据实际召回门槛、同内核原方法与完整链路验证。E206 候选缺口、E207 分段和 E209 预取跨窗证据各按原合同；历史原始 QPS 各自保留来源。

E214 四路精算为等价工程候选，E215 相近查询补点为离线质量来源。E216 在线近邻补点保留 WebVid K1 CACHE 的局部正例，COCO K100 加密点仍由完整 B32 更快达标。后续若优化该方案，重点是降低 CACHE 在线近邻查找和重排费用，并以密集同期控制测完整 Recall–QPS。[E216 加密对照](entry_method_exploration/20261121_neighbor_residual_online_v1/confirmation_result.md) · [E215 离线报告](entry_method_exploration/20261121_b32_cross_budget_tails_v1/report.md)。

E217 的低成本入口桶保留足够的 COCO K100 和 WebVid K1 候选动作，但全维最近代表的实际质量不足。若继续，优先在 COCO K100 与 WebVid K1 用 fit 内交叉拟合的最终 Top-K 净救回监督验证低成本代表选择；WebVid K100 另需扩充校准窗的动作可达性。候选进正式前仍需两窗回放与同期密集控制。 [E217 桶内精确上限](entry_method_exploration/20261121_gt10_bucket_residual_v1/report.md)。

E218 的线性余弦、主返回重合和候选均值摘要未达到 COCO K100 / WebVid K1 两窗资格。后续若探索同桶选择，使用更直接的查询到漏点候选信号做固定动作诊断，测上限可实现比例、实际救损与成本。WebVid K100 两表上限到达 L192，但校准仅多 59 个，需要先证实低成本选择可用再开展完整计时。 [E218 报告](entry_method_exploration/20261121_bucket_gain_selection_v1/report.md)。

E219 验证真实 ID 粗排后可在同预算取得回放质量净增。主网格 COCO K100 最佳同召回 QPS 差 +3.62%，慢遍仍快 2/8 点。WebVid K1 最佳同召回 QPS 差 +0.33%，慢遍仍快 1/9 点。WebVid K100 最佳同召回 QPS 差 +2.66%，慢遍仍快 2/8 点。局部加密 COCO K100 Q8-2 L224 相对加密最快达标控制 -0.95%。WebVid K100 Q8-4 L232 相对加密最快达标控制 -2.22%。后续按实测前沿保留场景，若扩测先冻结其他数据来源和端到端费用。[E219 达标配对](entry_method_exploration/20261121_bucket_id_reranking_v1/analysis/matched.csv)。

E220 去热路径字符串和局部排序已通过 Q8 等价回放。COCO K100 代表 L224 的 Q8-fast 对最快达标控制 -0.75%，相邻 L232 +0.06%。WebVid K100 代表 L232 的 Q8-fast 对最快达标控制 +0.61%，相邻 L224 +0.93%。后续判断按实际同期前沿。扩表诊断只有约 0.45 微秒的省时估算，结合侧路读码和表结构考虑。[E220 报告](entry_method_exploration/20261121_q8_equivalent_speed_v1/report.md)。

E221 已验证 Q8 保守上界的原精算剪枝和输出等价。COCO K100 L224 相对 Q8-fast -0.00%，相对同期达标控制 -0.38%，L232 对同期达标控制 -0.67%。WebVid K100 L232 相对 Q8-fast +0.25%，相对同期达标控制 +0.56%，L224 对同期达标控制 +0.25%。WebVid K1 L208 相对 Q8-fast +1.68%，相对同期达标控制 +2.88%，L216 对同期达标控制 +2.31%。后续研究优先依据同窗完整 wall 取舍。 [E221 达标配对](entry_method_exploration/20261121_q8_certified_pruning_v1/analysis/matched.csv)。

[E213 GT10+B32、NSG 与 GATE](entry_method_exploration/20261121_span4_gt10_b32_nsg_gate_v1/report.md) · [E212 纯 GT10 与 B32](entry_method_exploration/20261120_gt10_nsg_b32_four_way_v1/report.md) · [E211 报告](entry_method_exploration/20261120_span4_production_default_v1/report.md) · [E210 独立适配](experiment_history/210_span4_four_dataset_retest_v1.md) · [历史索引](s-experiment.md)。
