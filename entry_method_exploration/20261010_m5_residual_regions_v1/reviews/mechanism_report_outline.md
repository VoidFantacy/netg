# E174 机制报告静态提纲

仅根据已冻结 protocol.md 与 evaluate.py/region.hpp 的接口、指标和控制设计整理；未打开本轮响应、GT 或向量，未进行数值分析、编译、查询或大型数据哈希。本提纲不含实验结论，不改变参数、停止门或原审查收据。

1. **先给实际判定。** 每个 dataset/K/原锁定 L 给出原 GT、M5、M5REG96 的 Recall、三轮完整 wall/QPS、同 L 配对 query rescue/damage 和速度比；独立列出较小 L 的区域法对较大 L GT。先说明双升、取舍或无收益，再解释机制。pilot_a 与 confirm_b 分开；后者没有 FIRST/24/direct 控制，不能把 pilot 的控制差异冒充确认结果。

2. **清楚描述实际干预。** 原 GT 主搜索返回 R、路由与搜索 visited 不变；原 M5 全 C 仍按原 fresh scalar 分数严格合并。从 C 每个路由行选 query-best seed，最多三颗且去重不补位，按原 NSG 一跳物理槽轮转生成 X；过滤主搜索已见、原 C、本次 X 重复。X 追加预算 24/96，C+X 总候选至多 48/120，最多 K 个原 R 重评分另计。本版只做候选生成；终局不能称为同状态续搜、桥节点展开或主图重建。失败/非有限 X 回退完整原 M5 结果，已付费用仍保留。

3. **先验证产生了什么，再解释救回。** 全 4096 的 trace 支持 C/X/seeds 域、唯一性、容量、来源与主返回互斥检查，并由独立 untimed 原标量评分/线性合并 oracle 绑定真实 plain 输出。报告 C/X/seed 均值、queries_with_X、extension_aborted、X 表外比例；这些是按 query 的成员出现次数，不能称为全局 distinct ID 数。X_outside_original_M5_U 说明越过冻结 posting ID 支持，X_outside_original_TRAIN_GT100_U 进一步说明越过原 20K TRAIN GT100 ID 并集；二者均不等同于本 query 的新目标或最终救回。

4. **用返回结果连接质量。** 对 M5REG 与原 M5，新增返回的 GT 成员必须来自 X；同时列新增救回、损伤和净质量差，以及新增救回中位于两种支持集合外的数量。对 K=1/100 分别用净命中差除以 nK，百分点变化为 100×净命中差/(nK)。保留全 C 意味着保留可供排序的候选支持，不意味着最终 K 个 ID 是原 M5 的超集；实际 GT 的 tie/数值边界仍由 rescue/damage 检查，不能直接宣称 Recall 必然不降。当前机制表只有新增救回；损伤应取 comparisons，不得把 new_rescues_vs_M5 当成净收益。

5. **用冻结控制限定解释。** pilot 中 M5REG96 对 M5FIRST96 检验同份 C 上 query-best 与 first 的策略差异；对 M5REG24 检验冻结的额外预算差异。MFREG96/MFDIRECT、GEOREG96/GEODIRECT 给出各自原表增加同一扩展器后的结果；M5REG96 对 MFREG96/GEOREG96 检验原监督来源的局部差异。这些是完整策略控制，实际 C/X 数、槽读取和费用可能不同，不能声称严格同 wall 或只改变一个几何因素。若 MF/GEO 同样有效，应将结论缩小到通用原图区域扩展；若 M5 较强，仍只能支持这些冻结源/预算/角色上的差异。

6. **解释费用与证据边界。** 样本 NDC/post_dots/new_distances/槽过滤计数仅覆盖事前均匀 256；它们帮助定位工作量，不能代替全 4096 的完整 wall，不能从时间差精确归因 seed、邻接或 IP 单项费用。三轮 same-L 比为同 KL 顺序匹配；cross-L 速度只按 round index 对齐，须保留非同时、非随机配对范围说明。多点 bootstrap 仅为描述区间，无总体/同时支配保证。不同路由行没有证明不同 basin；冻结跨模态残差监督没有证明当前模态 gap、低秩、语义桥或原因。没有新 fit 不等于免除查询/校验/存盘成本；成本表单列。默认 GT10 保持，按原协议完成全部冻结点并停止本版本，任何后续假设另立研究。

可直接采用的机制句式：

> 在这组冻结 query、K、L 与预算上，原 M5 残差 posting 提供的 seed 经原 NSG 一跳生成了 [X] 个候选出现，其中 [A] 个位于原 posting ID 并集之外、[B] 个位于原 TRAIN GT100 ID 并集之外。相对原 M5，最终新增救回 [r]、损伤 [d]，净 Recall 变化为 [Δ]；完整 wall 的三轮速度比为 [ratios]。这些观测支持 [局部覆盖/质量/费用结论]，尚不能据此认定模态 gap 或跨 basin 桥接是原因。
