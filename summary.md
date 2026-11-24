# ACSG 当前结论

E253 在 E252 的三套经典平方 L2 数据上补入纯 GT10 并重跑三方法。真 K1/K100 共 288 点、576 批。44 个固定召回目标中纯 GT10 最快 41 个，Mixed64 最快 3 个。GIST 的 K1 96% 和 K100 85% 相对纯 GT10 达标 QPS 分别 +14.32% 和 +2.36%，慢遍仍快。SIFT K100 的 99.8% 同 L 只快 0.27%，重复范围交叠。[E253 三曲线报告](entry_method_exploration/20261123_gt10_b32_mixed64_classical_v1/report.md)。

E252 扩到三套经典平方 L2 真数据 Deep10M、BIGANN-SIFT10M、GIST1M，真 K1/K100，共 192 点、384 批单线程完整计时。同 L 的 96 个比较中 Mixed64 提高 62 个、持平 34 个，每查询额外精算约 86–96 个候选。Deep 和 SIFT 的 28 个共同达标目标都由 B32 更快达到。GIST 仅 K1 的 96%（+16.94%）和 K100 的 85%（+6.03%）目标较快，均为小召回增量跨过预设门槛后降低 L。经典 L2 常规补点继续用 B32。[E252 报告](entry_method_exploration/20261123_b64_classical_retest_v1/report.md)。

E251 完成 COCO、Flickr30k、WebVid、Yandex 三方法同期复测。真 K1/K100、465 点、930 批。原 GT10+B32 同 L 由 Mixed64 在 149/155 个组合提高召回，余 6 个持平。相对 B32 在 63 个双边固定目标中 35 个均值领先，32 个慢遍仍领先。代表目标相对 B32/老 B64 的完整 QPS 分别为 WebVid K1 84% +15.65%/+6.43%、K100 75.5% +4.81%/+1.12%，COCO K100 97% +4.14%/+3.19%。Flickr30k K100 97.5% 为 +1.21%/−0.48%。Yandex 两种 K 的 15 个双边目标均由 B32 更快达标。结论依各数据集、K 和召回门槛。 [E251 四集复测](experiment_history/251_b64_four_dataset_retest_v1.md)

2026-11-23 新 B64 的可复现实测收益来自提高有限 L 下的真漏点覆盖。E243 的 Mixed64 在已有 B32 有序前缀上，用 24,192 条训练的三档真实漏点重编 B64，在线保留原三路 raw-IP 精算。WebVid K100 的 75.5% 门槛在公共确认从老 L204 降到 L200、完整 QPS +1.84%，在独立 seed 窗从 L216 降到 L208、+3.37%，第二 seed 窗在新老同用原访问复用时从 L200 降到 L196、+1.90%。三窗慢遍对快遍均保持正。WebVid 同 L 召回改善约 0.3 个百分点，原精算工作和同 L 完整 QPS 接近。 [三窗证据](experiment_history/243_b64_multibudget_training_v1.md) · [独立验证](experiment_history/237_b64_external_validation_v1.md) · [同优化验证](experiment_history/244_b64_equal_fastpath_v1.md)

同样本消融 E247 的 WebVid 最佳单档 L176 与 Mixed64 在 75.5% 均使用 L208，多档仅多 16 个正确成员。新增训练是主要收益，原 16,000 条训练的 L200 原生四种载荷与历史逐字一致。COCO 真 K100 复跑采用 20,096 条训练。97% 从老 B64 L204 到扩样本单档 L200、再到多档 L196，Mixed64 +2.48%，实际精算约持平的 Mixed52 为 +2.46%。COCO 同样本消融最强单 L176 在同 L 比混合略高。较慢的一轮 E248 保留，E250 复测确认 97% 的单 L176 和 Mixed64 分别 +2.44%/+2.49%。WebVid 的 K100 训练表直接用于真 K1，84% 原网格 +7.85%，加密 E249 从老 L180 到 L166、完整 QPS 仍 +7.01%。效益按数据集、真实 K、目标和确认窗适用。同样本证据支持把低 L 单档作为论文与配置的强对照，多档额外优势未稳定建立。 [WebVid 消融](experiment_history/247_b64_teacher_depth_ablation_v1.md) · [COCO 真 K100](experiment_history/245_coco_b64_multibudget_training_v1.md) · [K1 加密](experiment_history/249_webvid_k1_b64_dense84_v1.md) · [COCO 复测](experiment_history/250_coco_b64_target_retest_v1.md)

2026-11-23 B64 迭代的当前证据见[逐轮记录](entry_method_exploration/20261123_b64_until1300/progress.md)。在 WebVid 真 K100 的 E231/E232 两窗，固定提高第三路深度或用最远入口专用尾表都没有建立确认窗的替换依据。E234/E236 的主搜索分数能把尾部候选分配给更需要的查询。E234 确认窗 L204 比固定 Far52 多 72 个正确成员，仍差 40 个到 75.5%，粗网格转到 L208 后完整 QPS 慢 1.74%。E242 逐整数确认 L205 已达标，完整 QPS 约持平，线性门 +0.02%，Budget52 +0.22%。E233 复用访问标记将原返回保持逐字相同，同 L 两窗 QPS 中位 +0.45%/+0.53%。此处均保留同轮老 B64 和原 B32 对照。生产默认保持原合同。

E230 在与 E229 诊断窗隔离的 WebVid 窗完成真 K1/K100 的 105 点、210 批。新 B64 的 K1 三路各 56，K100 按画像分数用 64/64/40。新 K100 对等预算 B56 的 18/18 点召回更高，L208 精算 163.76/163.80 个并多命中 68 个正确成员。相对老 B64，新 K100 同 L 平均少精算 23.50 个，固定目标 7/10 的均值和慢遍均更快。72% 目标较 B32/老 B64 的 QPS 为 +4.03%/+0.96%，75.5% 为 +2.53%/−1.40%。老、新 B64 均保留为目标相关配置。 [E230 报告](entry_method_exploration/20261123_b64_entry_budget_v1/report.md)

E229 正式完成 COCO、Flickr30k、WebVid、Yandex 真 K1/K100 的 218 点、436 批。B64 双边达标目标均值更快 K1 为 8/24，K100 为 15/35。WebVid K1/K100 为 4/7、9/13，慢遍仍快 4/7、8/13。K100 的 72% 目标 L168→160、均值 +0.46%、两遍重叠，75.5% L224→208、+2.97%、慢遍仍快 2.72%。COCO K100 仅 2/7 个目标均值更快，慢遍 0/7。Yandex 两种 K 所有达标对照原 B32 更快，同 L K1 召回持平。保留原版 B32 通用基线，B64 按数据集、K 与召回目标采用。 [E229 报告](entry_method_exploration/20261122_b64_formal_four_dataset_v1/report.md)

E228 以异窗 COCO、WebVid 真 K100 密测原版 B32 与全精算 B64，20 档 L、80 点、160 批。COCO 97.0% 目标由 L216 降到 L204，完整 QPS +1.40%。WebVid 75.5% 由 L220 降到 L208，QPS +2.70%。双边达标目标中 B64 均值更快分别 7/7、5/6，慢遍仍更快 6/7、4/6。两集各有 16/16 个重叠点比 B32 折线快。WebVid 72% 两臂均在 L168，B64 慢 2.97%。全精算 B64 保留为已测两集 K100 的较高召回条件配置。 [E228 报告](entry_method_exploration/20261122_b64_full_confirmation_v1/report.md)

E227 在 COCO、WebVid 的第三公共窗真 K100，11 档 L、44 点、88 批完整单线程。16 维 B32 截止分双塔平均少精算 30.60 / 19.60 个，同 L Recall@100 下降 0.0234–0.0280 / 0.0335–0.0348 个百分点，同 L 完整 QPS 中位数 +0.04% / +0.23%。两集各 3/10 个同召回重叠点比同期 B32 折线更快。原版 GT10+B32 仍为补点基线。 [E227 报告](entry_method_exploration/20261122_b32_cutoff_two_tower_v1/report.md)

E226 在 COCO、WebVid 真 K100 各测 11 档 L、共 132 点和 264 批。固定精算 48 的双塔 B32/B64 在四组同池对照的全部 44 个点都比 PCA 召回高。与原版 B32 的重叠区间按折线读图，双塔 B32 为 0/20 点更快，双塔 B64 为 1/20。全精算 B64 有 15/16 点在折线右侧，L200 对同期最快达标 B32 L224 的完整 QPS 分别高 5.34%、6.73%。保留原版 B32，优先复验全精算 B64。 [E226 报告](entry_method_exploration/20261122_b32_b64_two_tower_v1/report.md)

E225 在 COCO 真 K100 验证至多八个新候选的 P64 探针分流，11 档 L、22 点、44 个完整 CPU15 单线程批次。探针 L184 为 96.6380% / 2,728.2 QPS，原版 GT10+B32 L192 为 96.6247% / 2,797.9 QPS，多 41 个正确成员，QPS 慢 2.49%。启用且有同期达标 B32 的八点中四点均值更高、两点慢遍仍更快。B32 召回重叠范围按连线描述只有一个点略快。原版 B32 保持补点基线。 [E225 报告](entry_method_exploration/20261122_p64_candidate_probe_v1/report.md)

E224 完成 COCO 真 K100 的 B32/P64 查询分流，真实留出 3,072 条、66 点、132 完整单线程批次。主比较 L184 对 B32 L192，线性版 96.5410% / 2,752.5 QPS，原版 B32 96.5446% / 2,772.6 QPS，树版 96.4782% / 2,810.7 QPS。两臂均低于主召回目标。相对有限网格中同期最快达标 B32，线性 7/11、树 8/11 均值更快，慢遍仍更快分别 2/11、5/11。按实际门槛保留局部证据，完整 B32 仍为补点基线。 [E224 报告](entry_method_exploration/20261122_p64_residual_gate_v1/report.md)

E223 固定 E222 的单组全候选池，按查询原内积最多换出 16 个 B32-fit 尾部 ID。两集 K100 开发窗与校准窗都兑现离线单组覆盖上限，无原正确成员损伤。校准窗 COCO/WebVid 净增 768/4,829，L192 所需 412/1,349。COCO 32/64 维两窗均过线，66 正式点、132 个完整 CPU15 单线程批次。两臂 22 个测点中 4 个相对最快达标对照均值更快，2 个慢遍仍更快。P64 L200 为 96.7607% / 2,531.1 QPS，对同期达标 Q8-cert L208 的 96.9202% / 2,500.6 QPS 高 1.22%。保留为 COCO K100 条件候选，原版 B32 保持补点强基线。[E223 报告](entry_method_exploration/20261122_group_residual_rerank_v1/report.md)

E222 组内联合短尾表完成 COCO、WebVid 真 K100 的 132 点、264 个 CPU15 单线程完整批次。短表 8/16 两窗均未追平 B32-fit L192。16 位版在校准窗净增 33/35 个正确成员，所需 412/1,349。校准窗单组全候选覆盖上限为 768/4,829，缩到短表后剩 62/116。两个短表共 44 个正式点均由同期强控制覆盖，保留原版 B32 作为补点基线。 [E222 报告](entry_method_exploration/20261122_joint_residual_tail_v1/report.md)

E221 用 Q8 粗分与量化误差上界安全省掉精算候选。11,952 个回放查询的 233,695 次拒绝均核原生分数，结果保持逐字节一致。COCO K100、WebVid K1/K100 共 107 点、214 批。COCO K100 L224 相对 Q8-fast -0.00%，相对同期达标控制 -0.38%，L232 对同期达标控制 -0.67%。WebVid K100 L232 相对 Q8-fast +0.25%，相对同期达标控制 +0.56%，L224 对同期达标控制 +0.25%。WebVid K1 L208 相对 Q8-fast +1.68%，相对同期达标控制 +2.88%，L216 对同期达标控制 +2.31%。[E221 报告](entry_method_exploration/20261121_q8_certified_pruning_v1/report.md)。

E220 Q8 等价 A/B 在两集 11,952 个回放状态候选及输出逐字节相同，去除热路径错误字符串和限制排序范围使补点回放省时。两集 K100 正式 80 点、160 批。COCO K100 代表 L224 的 Q8-fast 对最快达标控制 -0.75%，相邻 L232 +0.06%。WebVid K100 代表 L232 的 Q8-fast 对最快达标控制 +0.61%，相邻 L224 +0.93%。WebVid 扩表诊断校准窗跳过 11.69% 的四表扫描，等于 B32-fit L192 命中。[E220 报告](entry_method_exploration/20261121_q8_equivalent_speed_v1/report.md)。

E219 直接粗排真实漏点 ID 与 B32 尾部，保留逐查询精算数。COCO K100、WebVid K1/K100 均过两窗回放门，第二公共窗完成 主网格 162 点、324 批，加密 60 点、120 批，CPU15 单线程。主网格 COCO K100 最佳同召回 QPS 差 +3.62%，慢遍仍快 2/8 点。WebVid K1 最佳同召回 QPS 差 +0.33%，慢遍仍快 1/9 点。WebVid K100 最佳同召回 QPS 差 +2.66%，慢遍仍快 2/8 点。局部加密 COCO K100 Q8-2 L224 相对加密最快达标控制 -0.95%。WebVid K100 Q8-4 L232 相对加密最快达标控制 -2.22%。[E219 报告](entry_method_exploration/20261121_bucket_id_reranking_v1/report.md)。

E218 对 COCO K100 / WebVid K1 的 E217 桶训练净命中预测。三个身份隔离折真实合并 509,823 个动作，另回放 7,953 个 dev/cal 状态。摘要版 COCO K100 校准净增 +206（原桶 +199，L192 所需 +412）；WebVid K1 +3（原桶 +6，所需 +7）。无场景进入端到端计时。另枚举 WebVid K100 双表 949,006 个动作，当前同预算校准上限由单表低于 L192 129 个变为高于 59 个。[E218 报告](entry_method_exploration/20261121_bucket_gain_selection_v1/report.md)。

E217 在 COCO、WebVid 真 K1/K100 已有主返回回放 GT10 入口分桶取候选，共 15,906 个 dev/cal 状态。BKT8 比同期 CACHE 每条补点重放省 10.30–11.99 微秒，四个场景均未达到质量资格。COCO K100 校准窗同 L 净增 199，精确枚举桶内动作上限 994，L192 所需 412。WebVid K100 同窗的桶内上限仍差 129。正式点 0。[E217 报告](entry_method_exploration/20261121_gt10_bucket_residual_v1/report.md)。

E216 在 COCO、WebVid 进行在线相近查询补点的完整计时。五臂、真 K1/K100 各 8 档 L，160 点、320 批。相对完整 B32 同 L 的 64 个新点都提高召回并降低完整 QPS。两代表点补做 59 点、118 批局部加密。WebVid K1 CACHE L192 为 83.4635% / 1,571.0 QPS，最快达标 B32-fit L208 为 83.4961% / 1,545.3 QPS，+1.67%。COCO K100 CACHE L200 比完整 B32 L208 慢 2.65%。CACHE 保留为条件候选，整体替换证据不足。[E216 主报告](entry_method_exploration/20261121_neighbor_residual_online_v1/report.md) · [加密对照](entry_method_exploration/20261121_neighbor_residual_online_v1/confirmation_result.md)。

E215 在 COCO、WebVid 用 E206 训练角色离线研究 L184 的补点。三种尾表在 WebVid K100 的并集有候选供给缺口。改用相近 fit 查询的全部遗漏，替换最多 16 个尾部 ID 并保持每查询实际精算数，COCO Recall@100 校准窗从 96.1770% 到 96.4807%，高于 L192 参考 96.3866%。WebVid 从 72.5607% 到 73.1924%，与 L192 的 73.2403% 还差 95 个正确成员，开发窗超过 43 个。K1 的 WebVid 两窗均超过 L192。结果为真实距离离线合并，候选查找及投票的线上代价留待完整计时。[E215 候选来源](entry_method_exploration/20261121_b32_cross_budget_tails_v1/report.md)。

E214 四集测了固定原表的候选四路精算。真实 K1/K100 各 7 档 L，168 点、336 个完整 CPU15 单线程批次。56 组 B32 返回逐字节相同，完整 QPS 变化 −0.52% 至 +2.44%，中位数 +0.35%，均值更快 48/56，四路慢遍快于原版快遍 34/56。WebVid 两种 K 的中位数为 +1.23%、+0.91%，Yandex 效果接近零。保留为等价工程候选。较小 L 带来的完整收益仍更大，WebVid Recall@100 目标 80% 时，四路 B32 在 L320 为 80.801% / 1,039.4 QPS，纯 GT10 在 L400 为 81.576% / 868.0 QPS。[E214 四集结果](entry_method_exploration/20261121_b32_batch4_scoring_v1/report.md)。

E213 同期复测 COCO、Flickr30k、WebVid、Yandex first10M。每集 3,072 条，真实 K1/K100 各 7 档 L，CPU15 单线程，每点两遍完整 wall。GT10+B32、NSG 固定单入口和 GATE 的主图统一使用 SPAN4。GATE 的小 HNSW 路由照原合同运行。GATE 标量 A/B 的 56 组返回逐字节一致，SPAN4 完整 QPS 提升 11.97%–27.96%。[E213 四集报告](entry_method_exploration/20261121_span4_gt10_b32_nsg_gate_v1/report.md)。

E213 同 L 下，GT10+B32 相对 NSG 和 GATE 分别在 52/56、54/56 个点提高召回，在 28/56、39/56 个点同时提高召回和吞吐。21 个有达标点的离散召回目标中，GT10+B32 最高平均 QPS 14 个，NSG 6 个，GATE 1 个。WebVid Recall@100 目标 90% 由 GT10+B32 在 L960 达到 90.221% / 374.6 QPS。[E213 门槛表](entry_method_exploration/20261121_span4_gt10_b32_nsg_gate_v1/analysis/recall_thresholds.csv)。

默认标准 Flat raw-IP 的 `ACSG::search_new(mode=2)` 使用 E211 SPAN4。L2 等路径使用标量。显式标量回退调用 `acsg.set_flat_ip_batch4_enabled(false)`，在启动查询线程前设定。画像的配置以冻结输入为准。

E212 的 NSG 和新 GT10 使用同一 SPAN4，分别采用图的固定单入口和画像三入口。E212 固定同 L 补点平均 Recall 增加 52/56 点，完整 QPS 降低 56/56 点。完整 B32 的部署取舍依据同内核的纯 GT10 与 B32 曲线及实际达标配置。E212 新旧 B32 的 56 组返回逐字相同，完整 QPS 变化 +13.43% 至 +27.54%。

[E212 逐配置](entry_method_exploration/20261120_gt10_nsg_b32_four_way_v1/analysis/same_l.csv) · [E212 门槛表](entry_method_exploration/20261120_gt10_nsg_b32_four_way_v1/analysis/recall_thresholds.csv) · [E211 默认切换](entry_method_exploration/20261120_span4_production_default_v1/report.md) · [修改前文档](entry_method_exploration/20261120_gt10_nsg_b32_four_way_v1/source_before/)。

[E210 独立适配](experiment_history/210_span4_four_dataset_retest_v1.md)、[E209 两窗](experiment_history/209_webvid_b32_span_confirmation_v1.md)、[E208 四集补点](experiment_history/208_b32_equivalent_speed_v1.md)及历史证据按原配置索引。旧数据范围见[存储简档](experiment_history/_maintenance/20261119_obsolete_payload_prune_v1/archive_index.md)。
