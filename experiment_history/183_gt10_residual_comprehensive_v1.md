# E183：GT10与残差的七数据集及失败查询综合评测

2026-10-18 按用户要求新增[四页简版PDF](../entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/concise_v1/NETG_E183_NSG_GT10_残差_简版报告_20261018.pdf)：仅NSG/GT10/GT10＋残差、统一L200失败表；每集全L固定家族与B32。复用315个既有实测点，仅展示重排，原完整结果及详细PDF保留。

2026-10-17，用户授权范围完成。交付[32页详细中文PDF](../entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/delivery_v2/NETG_E183_GT10与残差_七数据集及失败查询_详细报告_20261017.pdf)及[报告](../entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/delivery_v2/report_zh.md)。本轮目的为分别评价GT10入口方案和固定入口后的残差增量，覆盖非多模态数据、失败查询和完整Recall–QPS。

## 当前结论

GT10在Deep与SIFT有实际效率迁移收益；GIST的K100小幅优势及K1混合结果保留。残差B32在Deep/SIFT的新增召回很小，K100共同区间曲线均低于各自GT10；GIST部分K100区间有小收益。Web/COCO的K1/K100补全曲线均改善，三轮描述同向；Flickr交叉、Yandex K100较低。默认E99 GT10保留，不从本轮选一个跨数据/家族拼接赢家。

## 实际配置与实现

Deep10M96维/SIFT10M128维/GIST1M960维保持原squared L2；Web2.505M512维/Yandex10M200维/COCO118272点/Flickr31782点512维保持raw-IP。测试各10K/10K/1K/10K/10K/10K/5K。五集原hard/soft与各自B8/B32，加NSG，共7方法；COCO/Flickr只沿已有hard，共4方法。K1八L16/32/64/100/200/400/800/1200，K100七L100/128/200/400/800/1000/1200；645点、1935三轮T1、15615000正式query。CPU15，各数值库1线程，所有离线结束后才正式串行。

每个家族用合法16K非test查询、K100/L200遗漏编单位query-target表，保存未裁剪源、路由关联和B8→32前缀。L2与Web/Y残差可共享原画像fit；COCO/Flickr为独立残差角色，不能混称相同控制。E97五集保留真实ID升序入口，E181两集保留heap-pop；原scalar主核和后置候选精确评分合并，未改变主搜索。

完整wall含正常Batch创建/初始化、路由、主搜、补点、统一六向量复制及正常销毁。首轮实际包保存、后两轮bits/SHA一致，POST全部由对应实际GT10主包独立标量/线性oracle复核。没有另跑完整ANN冒充计时包。NDC未采集，零数组只保持布局，不称0次距离。绝对QPS与E103不同优化核不拼接。

## 失败查询与覆盖

预定L200/K100下，soft Deep21/29220、soft SIFT25/18468、hard GIST66/10886个遗漏被救回；修复0.0719%/0.1354%/0.6063%，同L QPS下降3.44%/3.22%/1.61%。三个L200/K1示例均救回0；全L的B32 K1最大增益Deep0.01pp/SIFT0/GIST0.30pp，不能把单点写为全预算无机会。

soft Web20257/272967（7.4210%），hard COCO13715/46556（29.4591%），hard Flickr2140/13964（15.3251%），hard Yandex570/112276（0.5077%）。同L附加费用与同Recall曲线收益分开。K100同时保留成员损伤、六难度层、90/100门槛、GT新增失败再救回与两类训练频次，不能把补一个成员叫整条失败已解决。

Deep源链29220→195→86→21，SIFT18468→140→62→25（测试遗漏→训练残差全局源支持→当前路由未截断支持→B32救回），固定源外目标不可由扩大当前表救回。GIST10886→4242→1117→66体现其他瓶颈。未将这些观察单归因模态/语义/规模。

全部360补全点损伤5成员事件，涉及2条query。Web4为近边界，特定原生舍入倒置未证明；COCO1为1ULP原生次序相对精确有理数度量倒置。原GT和严格ID计数保持，重复工作点不作独立样本。

## 验收、修正与成本

训练前112源文件完整SHA通过；224固定query全库float64 Top1/Top100集合全同，非全queryGT第二次证明。76个256query历史baseline ID/距离/入口字词回归通过。独立脚本未导入主analyzer，复算645点、1935轮、540组救损、2088分层、360覆盖、360级联、3600频次，且重建全部TRAIN遗漏源和各表训练覆盖。全部PASS；bootstrap/插值和真实greedy全部选择序列不属于独审复算范围。

首次Deep教师实际exit0，父调度误期待旧状态拼写而标FAIL；保留原launcher/原FAIL/独立修正收据后复用已完成32K教师查询，0科学重跑。最终正式645点没有重测或挑最快轮。

正式suite18267.58秒约5.07h，包含1935内部wall、预热、保存/核验，不能重复加总；主分析139.83秒、独审407.80秒。离线接续suite160.94秒另保留先前Deep教师26.80秒；源SHA330.27秒与GT抽审27.98秒部分重叠。所有构建、阶段与嵌套边界见[费用账本](../entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/cost_ledger.json)。复用旧资产的完整冷启动成本未知，不清零；文件大小不冒充精确RSS。

## 局限与结束边界

本轮单图/单画像实例、已曝光公共测试，三轮不是三份质量样本；GIST仅1K，固定16K/K100L200教师跨K共表不证明各K最优，跨数据的metric/规模/维度/容量/训练密度未因果配平。无NSG+残差额外组，只识别在GT10上的增量。单点同L救损、实测跨L点和折线插值分别报告。

[协议](../entry_method_exploration/20261017_gt10_residual_comprehensive_v1/protocol.md) · [全645点](../entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/final_v1/points.csv) · [1935轮](../entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/final_v1/timings.csv) · [独审](../entry_method_exploration/20261017_gt10_residual_comprehensive_v1/reviews/independent_results_audit.json) · [边界](../entry_method_exploration/20261017_gt10_residual_comprehensive_v1/reviews/boundary_diagnostics.json) · [实际计时输出](../entry_method_exploration/20261017_gt10_residual_comprehensive_v1/results/) · [状态](../entry_method_exploration/20261017_gt10_residual_comprehensive_v1/state.json)。源、旧报告及delivery_v1保留；delivery_v2只补解读，不改科研结果。最终PDF实际视觉检查收据在delivery_v2/pdf_visual_review.json。

固定矩阵收口，无待恢复队列，默认不变。本轮基底HEAD96cf05d5410cf51272048cd1f90b4bb194e23c62、分支research/state-20261002，未创建提交或发布。
