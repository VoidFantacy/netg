<!-- E184_CURRENT_BEGIN -->
# E184 完成：空间难度与残差可复用性需要分开（2026-10-24）

当前默认仍为E99 GT10（Web soft-t1 / Yandex hard），最新性能仍E183。本轮复算七集56K已有查询，新增原metric几何诊断，0新ANN/GT/训练/模型/QPS。L200/K100原未满100查询中净改善比例：Deep0.38%、SIFT0.46%、GIST6.74%、Web60.84%、Y5.08%、COCO73.20%、Flickr42.07%；成员修复率另为0.0719/0.1354/0.6063/7.4210/0.5077/29.4591/15.3251%，不能把补回成员叫整条失败已解决。

Deep/SIFT超过99%的测试遗漏在当前训练残差源外，固定源乐观额外Recall上限仅0.0195/0.0140pp；GIST源4242→路由1117→B32救66，主要损失阶段不同。跨七集，训练残差重复倍率与成员修复率ρ=0.964，原遗漏成员率ρ=0.214；异质七集和结构性源覆盖关系不作因果证明。各集内几何分离与主搜遗漏多数负相关；按原遗漏量粗分层，Web/COCO高分离组改善概率仍高8.17/11.50pp，高残差频次组高44.69/19.61pp。不能简化为几何无关、多模态天然有效或越小越有效。

成功离线诊断170.346秒、第二实现整数核验4.368秒；56K逐条set/Counter及原CSV对齐PASS，每集8条query验证背景矩。首类型错误失败日志保留、失败wall未知。已有同L补全费用1.61%..6.24%QPS下降与Web/COCO同Recall曲线收益分开；未新增性能结论。单图/已曝光测试、8192背景样本、GIST1K、描述性相关/粗分层非因果、GT几何特征不可免费上线等限制保留。本诊断收口，无新实验队列，长期可靠Recall–QPS目标未因此达成。

[完整报告](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/report_zh.md) · [逐集表](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analysis/dataset_summary.csv) · [失败/覆盖图](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analysis/failure_and_coverage.png) · [详细复盘](experiment_history/184_residual_geometry_diagnosis_v1.md) · [第二实现核验](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analysis/integer_audit.json)。旧E183及以前产物/正文保持。
<!-- E184_CURRENT_END -->

<!-- E183_CURRENT_BEGIN -->
# E183 完成：GT10可迁移，残差在非多模态上的收益有限（2026-10-17）

完成Deep10M/SIFT10M/GIST1M原始L2与Web/Yandex/COCO/Flickr原始IP的645点、1935完整单线程批次；hard/soft与各自B8/B32分开，K1八L/K100七L。全部真实计时包三轮逐字一致、完整合并oracle及独立645点/540救损/360覆盖/2088分层/360级联/3600频次复算PASS。224样本全库float64 Top1及Top100集合全同；不是新盲确认。默认保留E99 GT10。

GT10-soft对NSG的K100共同区间折线QPS：Deep +1.60%～+7.94%，SIFT +1.53%～+4.87%；GIST-soft约+0.56%～+1.97%但三轮不全同向，SIFT/GIST K1混合。B32对自身GT10：Deep/SIFT K100曲线较低，GIST K100交叉；Web与COCO两K全共同区间改善、三轮描述同向，Flickr交叉、Yandex K100较低。线段估计不是新增等Recall实测，饱和点的多值分支保留。

事先L200/K100示例，soft Deep/SIFT、hard GIST的补回分别21/29220、25/18468、66/10886个遗漏（0.0719%/0.1354%/0.6063%），净Recall +0.0021/+0.0025/+0.0660pp，QPS -3.44/-3.22/-1.61%；该L200/K1三例救回0。Web-soft为20257/272967（7.4210%）、COCO-hard13715/46556（29.4591%），同L付出费用而完整曲线受益。

源覆盖直接限制：Deep 29220→全局源195→当前路由未截断86→B32救回21；SIFT18468→140→62→25。GIST10886→4242→1117→66，瓶颈分布不同。不能只按模态归因；规模/metric/训练密度未因果配平。全360补全点损伤5事件/2query：Web4近边界未证明特定native因果、COCO1个1ULP排序倒置；严格ID/GT不改。

正式suite18267.58秒（约5.07h，含内部正式wall、预热、保存及核验），独审407.80秒。初次Deep教师仅调度状态拼写修正、0重跑，26.80秒保留；源SHA330.27秒、GT抽审27.98秒部分重叠，不重复加总；继承完整冷启动成本未知。单图/单模型/已曝光测试、GIST1K、同K100教师跨K共表、未独立重算bootstrap/插值等限制保留。有限矩阵收口，未改默认。

[详细PDF](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/delivery_v2/NETG_E183_GT10与残差_七数据集及失败查询_详细报告_20261017.pdf) · [报告](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/delivery_v2/report_zh.md) · [645点](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/final_v1/points.csv) · [独审](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/reviews/independent_results_audit.json) · [费用](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/cost_ledger.json) · [详细复盘](experiment_history/183_gt10_residual_comprehensive_v1.md)。
2026-10-18 简版交付：[四页PDF](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/concise_v1/NETG_E183_NSG_GT10_残差_简版报告_20261018.pdf) · [简版文字](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/concise_v1/report_zh.md)。每图仅NSG、GT10、GT10＋残差三线，另有统一L200失败查询表；315点全部复用既有结果，固定同家族B32，无新增实验，详细版保留。
<!-- E183_CURRENT_END -->

<!-- E182_CURRENT_BEGIN -->
# E182 完成：规模效应受容量配置影响，非普遍“越小越好”（2026-10-16）

当前默认仍为E99 GT10（Web soft-t1 / Yandex hard）。完成WebVid同源100K/300K/1M/2.505M嵌套库、固定H815与密度H33/98/325/815的216点单次T1计时；全库COMMON只测一次。七个唯一N/H模型各有自身GT10-hard基线，14个K1/K100比较的JOINT32折线均在各自共同Recall区间更高。84/84同L Recall提升、83/84 QPS下降；不能用同L成本否定曲线改善。

在四N均覆盖的K100=90%位置，固定组折线QPS增益依次+24.33/+22.66/+19.67/+16.41%；密度组+14.07/+17.75/+17.71/+16.41%，最小库反而最低。这是单次测点折线插值，不是额外等Recall测量或稳定性证明。固定容量的小库优势有证据；密度匹配后不再单调，仍不能归为纯N因果律，因为H同时改变路由和训练/每hub密度。

预选K100/L200固定组净增3.6466/3.1708/2.5278/2.1058pp，密度组2.5146/2.5148/2.3018/2.1058pp；前两密度点仅差1个GT成员。固定组遗漏覆盖18.9686%降至7.7392%，而实际补算候选87.96增至92.93个/query，差异主要体现候选命中遗漏的能力下降，不是补点更少。所有84匹配点损伤0；fullN K1六L各1个候选可用未救回，已定位同一查询的两个完全相同base向量、不同ID及严格等分保留规则。

四档formal native及独立216点/84组整数审计PASS，GT抽样256实例Top1/Top100集合全一致（64角色查询复用四N）。正式外层1716.64秒，单次计时无法估计运行间方差；模型/GT各阶段成本及中断未知成本见费用账本。环境重启仅中断未完成fullN离线建图，正式点为0；成功前三档未重建，正式216点未重测。固定hard、新图、曝光公共查询、单次嵌套抽样限制保留。报告/PDF交付后本有限矩阵停止，无追加队列或默认替换。

[详细复盘](experiment_history/182_m5_scale_control_v1.md) · [报告](entry_method_exploration/20261016_m5_scale_control_v1/analysis/report_zh.md) · [PDF](entry_method_exploration/20261016_m5_scale_control_v1/analysis/NETG_E182_规模与容量对照_20261016.pdf) · [曲线](entry_method_exploration/20261016_m5_scale_control_v1/analysis/curves.png) · [规模趋势](entry_method_exploration/20261016_m5_scale_control_v1/analysis/scale_trends.png) · [216点](entry_method_exploration/20261016_m5_scale_control_v1/analysis/points.csv) · [状态](entry_method_exploration/20261016_m5_scale_control_v1/state.json)。
<!-- E182_CURRENT_END -->

<!-- E181_CURRENT_BEGIN -->
# E181 完成：COCO 曲线改善，Flickr K100 部分区间改善（2026-10-16）

当前默认仍为 E99 GT10（Web soft-t1 / Yandex hard）。已按用户要求下载经典 MS COCO、Flickr30k 的公开 CLIP 特征，独立构图和训练，完成120点、每点一次完整T1计时、实际timed输出保留及独立整数/合并核验。去重base118272/31782，测试查询10000/5000；角色互斥，未使用重合的LAION公共查询。

JOINT32对GT10：COCO K1/K100和Flickr K1的共同Recall区间上，测点折线均更高；Flickr K100有交叉（约95.6079%）。K100同Recall折线QPS差：COCO +7.96%～+21.58%，Flickr −1.27%～+8.76%。这只是既有线段描述，不是额外等Recall测量或稳定性结论。真实已测COCO K100 JOINT32/L1000=99.6977%/592.85 QPS，GT10/L1200=99.6928%/514.23，+0.0049pp/+15.29%；质量优势仅49/100万成员。

事先选定K100/L200：COCO GT10 95.3444%/2336.51 → JOINT32 96.7159%/2180.12；Flickr 97.2072%/2147.87 → 97.6352%/2039.06。两集实际补算约87.5个候选/query，却分别救回1.3715/0.4280个GT成员。候选效用差异有直接证据，但库规模、特征、图和训练密度未因果配平，不能单归因数据内容或外推千万级。

新增构图及训练阶段合计64.022/21.625秒，测试GT4.685/0.708秒；正式native子进程680.928/358.367秒（内含纯计时649.265/334.129，不重复相加）。b32文件均131339B，超原128KiB 267B、满足本轮256KiB。唯一成员损伤为边界float32近并列，已诊断且保留原统计。清理LAION可重建索引21.54GiB，源数据/历史结果保留。单次计时、小库、第三方特征与固定H815是重要限制；有限矩阵收口，未追加点或改默认。

**E180解释修正：用户对WebVid的观察成立。** 旧K100共同Recall区间中，JOINT32对GT折线QPS在Web全程+3.1642%～+15.2966%，Yandex全程−3.1652%～−0.2493%。旧“0/120严格跨L测点双升”不能否定Web整体曲线改善；下方旧正文保留原始时点身份，当前解释以此补充为准。

[详细复盘](experiment_history/181_m5_multimodal_transfer_v1.md) · [中文报告](entry_method_exploration/20261016_m5_multimodal_transfer_v1/analysis/report_zh.md) · [PDF](entry_method_exploration/20261016_m5_multimodal_transfer_v1/analysis/NETG_E181_经典多模态迁移实验_20261016.pdf) · [交付曲线](entry_method_exploration/20261016_m5_multimodal_transfer_v1/analysis/figures_delivery/curves.png) · [120点](entry_method_exploration/20261016_m5_multimodal_transfer_v1/analysis/points.csv) · [状态](entry_method_exploration/20261016_m5_multimodal_transfer_v1/state.json)。
<!-- E181_CURRENT_END -->

<!-- E180_CURRENT_BEGIN -->
# E180 完成：K100扩容有增益，当前五L尚无跨L双升（2026-10-15）

当前默认仍为 E99 GT10（WebVid GT10-soft-t1，Yandex GT10-hard）。E180 已完成两集各10K公开查询、K1/K100、五L、七方法的140点与420轮完整T1计时，独立结果核验通过；全量untimed返回与计时返回的证据范围分开。

WebVid K100/L1000：CAP8 89.8015% / 345.05 QPS → JOINT32 90.2816% / 342.69，Recall +0.4801 pp、QPS -0.68%；实际评分由23.3326增至93.6718个/query。它仍低于GT/L1200的90.4250% / 291.00 QPS，质量差0.1434 pp。Yandex K100/L200：88.8016% / 1472.32 → 88.8294% / 1442.21，+0.0278 pp、QPS -2.05%。扩容有质量收益，但两集K100六post方法全部跨L对为0/120严格双升，其中四新增策略0/80；这不排除未测预算。

WebVid K1 出现新增局部信号：FREQ32/JOINT32 的L800分别为92.53% / 427.22、92.51% / 426.70，均超过GT/L1200的92.33% / 290.59；对应+0.20/+0.18 pp与+47.02%/+46.84% QPS。两种策略共享同一预算对，不是两份独立确认。四扩展同L对CAP8共80对：67升/13平/0降，0/80严格双升；跨L共160对10次严格双升，全部属于Web K1。

新增成功编表完整子进程合计11.041秒；正式矩阵外层12179.351秒（约3.38小时，含加载/预热/审计，不能与内部420轮wall再相加）。b32单表文件131339/132185B、runtime加辅助145835/146681B，超原128KiB，满足本轮256KiB限额。历史训练债和失败尝试另列。公开10K和诊断尾4K均已曝光；未获得盲确认，不改默认，按冻结边界结束，不自动追加b64、L、轮次或教师。

[中文报告](entry_method_exploration/20261015_m5_k100_capacity_v1/analysis/share_v2/report_zh.md) · [可转发PDF](entry_method_exploration/20261015_m5_k100_capacity_v1/analysis/share_v2/NETG_E180_K100容量实验复盘_20261015.pdf) · [全140点](entry_method_exploration/20261015_m5_k100_capacity_v1/analysis/final_v1/points.csv) · [240跨L对](entry_method_exploration/20261015_m5_k100_capacity_v1/analysis/final_v1/cross_L.csv) · [独立结果审计](entry_method_exploration/20261015_m5_k100_capacity_v1/reviews/independent_results_audit.json) · [费用账本](entry_method_exploration/20261015_m5_k100_capacity_v1/analysis/cost_ledger_v2/README.md) · [状态](entry_method_exploration/20261015_m5_k100_capacity_v1/state.json)。
<!-- E180_CURRENT_END -->

<!-- E179_CURRENT_BEGIN -->
# E179 已完成：K100 目标带来小幅召回收益，默认仍为 GT10（2026-10-14）

**当前默认仍为 E99 GT10：WebVid GT10-soft-t1、Yandex GT10-hard，不替换。** 本轮同容量 K100 专用补全表 M5K10016，相对同训练量混合表 M5BASE16，两集五档 Recall@100 全升：WebVid +0.1131～0.1516 个百分点，Yandex +0.0026～0.0056 个百分点；QPS 小幅正负变化，没有稳定提速。相对 GT 同 L 的 20 点 Recall 全升、QPS 全降，没有同 L 双升；较低 L 对 GT 较高 L 的 40 对只有原 M5 已有的两个 WebVid K1 双升，新增为 0。

以下代表点在本轮新GT分析前[单独选定并记录](entry_method_exploration/20261014_m5_k100_objective_v1/reviews/presentation_point_selection.json)，单元格为 **Recall(%) / 完整单线程 QPS**；完整五档曲线与所有对照见[报告](entry_method_exploration/20261014_m5_k100_objective_v1/analysis/final_v1/report.md)。

| 数据集 / K / L | GT | 原 M5OPT20 | 同16K混合表 | 新 K100 表 |
| --- | --- | --- | --- | --- |
| WebVid / 1 / 800 | 90.7500 / 421.73 | 91.9400 / 419.95 | 91.8200 / 419.98 | 91.8900 / 420.12 |
| WebVid / 100 / 1000 | 89.2628 / 338.33 | 89.7014 / 336.43 | 89.6840 / 336.42 | 89.8015 / 336.30 |
| Yandex / 1 / 200 | 93.6800 / 1488.24 | 93.7700 / 1476.06 | 93.7900 / 1476.97 | 93.7700 / 1473.61 |
| Yandex / 100 / 200 | 88.7724 / 1471.46 | 88.7978 / 1463.67 | 88.7960 / 1464.12 | 88.8016 / 1462.63 |

主因果对照是同源前16K、同 H×8 容量、同在线实现的两张表。原20K表比较同时改变训练量，不能单独归因于目标。WebVid K1 相对同16K表略升，相对原20K表略降。WebVid K100 新 L1000 仍比 GT L1200 的 90.4250% 少 0.6235 个百分点，尚未填补更高预算的质量差距。

本轮完成两集×K1/K100×五L×五方法，共100点、每点两次正式完整wall计时；曲线采用两次QPS中位数（两次时等于均值），误差线为min–max。新增编表外层共10.733秒；完整native作业6845.359秒（114.09分钟），其中200次纯计时4338.219秒，不能重复相加。另计构建10.070秒、分析19.346秒、独立复核10.162秒；复用教师的历史TRAIN为WebVid22194.116秒/Yandex16062.192秒，未清零。新表文件分别53099/53369 bytes，native单表驻留计账59771/60041 bytes（非实测RSS），固定数组scratch588 bytes。

独立实现复核100点整数GT集合Recall、200轮wall/QPS、60个旧方法锚点的240个原始文件与冻结哈希，全部通过。Recall来自独立全10K未计时输出，未保存两次计时返回包。两集均为已曝光public前10K，每点两次只支持初步速度观察，非盲确认。**本冻结版本已收口；保留目标对齐的小幅质量发现，不据公开结果自动追加门控、教师、候选预算或调参。**

[实验复盘](experiment_history/179_m5_k100_objective_v1.md) · [主曲线](entry_method_exploration/20261014_m5_k100_objective_v1/analysis/final_v1/plots/recall_qps_main.png) · [同16K控制曲线](entry_method_exploration/20261014_m5_k100_objective_v1/analysis/final_v1/plots/recall_qps_control.png) · [可转发PDF](entry_method_exploration/20261014_m5_k100_objective_v1/analysis/final_v1/NETG_K100目标补全表_实验结果与曲线_20261014.pdf) · [最终状态](entry_method_exploration/20261014_m5_k100_objective_v1/state.json)。下方旧记录完整保留其历史身份。
<!-- E179_CURRENT_END -->

<!-- NORM_AWARE_THEORY_20261011_BEGIN -->
# 理论文档补充：范数敏感画像路由（2026-10-11）

按用户要求完成[理论归档](entry_method_exploration/20261011_norm_aware_profile_theory_v1/theory.md)，状态为 **THEORY_ONLY_UNIMPLEMENTED_UNTESTED**。方案在候选生成阶段联合画像匹配与真实入口原始内积，并推导保留联合排名的补维变换；条件性扩展为按组合向量范数分组。它尚无实现或测量收益，区别于 E178 已测的原画像候选池内重排。

本次仅改文档，没有训练、构图、新 GT 或新实验。**最新实测仍为 E178，默认仍为 E99 GT10；当前数据上的局部风险与有限范数影响结论不变。** 范数跨 1–几百的数据不在 E178 证据范围；精确评分等价不证明有限图搜索的 Recall–QPS 提升。理论和后续问题由[s-target](s-target.md)登记，下方原实测记录完整保留。
<!-- NORM_AWARE_THEORY_20261011_END -->

<!-- E178_CURRENT_BEGIN -->
# E178 当前结果：画像方向风险诊断（2026-10-11）

**最新实测为E178：48点/144完整单线程批次完成。观察到有限预算下的局部路由损失；当前证据不支持范数丢失已经造成系统性严重退化。GT10继续默认，有限矩阵结束。** 下方E177及以前全文保留历史身份。

两集各复用E177固定1024已曝光公共query，真实K1/K100、L200/800。对照原GT10、同画像top16候选按画像/真实入口余弦/raw-IP选3、全H精确余弦/IP选3；全部同H/主图/kernel/三入口，在线全部成本入wall。0新训练/GT。

- 同向冲突：两集真实hub都无cos≥0.99的对；Web画像有39对、Y0，均无cos≥1−1e-7近数值重合。范数Web≈1，Y0.871463–0.991270。
- 范数匹配对照：Web选点和返回完全不变；Y同16候选134/1024换集合，但四点只在K100/L200净少1个成员；全H169条换集合，仅K1/L200多1命中、K100/L200少1成员，其余平。
- 默认三入口全落在现有H的IP top10外：Web113/1024、Y41/1024。L200在该组按同池IP重排，K1救回/损伤分别5/2、3/0；Y K100净+5.0732pp（229救回/21损伤，6条净改善/2条净损伤）。同组L800 K100反降Web0.6903pp/Y0.3415pp，风险和修正效果都依赖预算。
- 全样本：同池IP相对默认R2升/1平/5降、QPS3升/5降、严格双升1/8；全H IP R3升/1平/4降、QPS2升/6降、双升2/8。三点速度仅+0.0804%..+0.3335%、范围重叠；这两方法对默认全部质量区间跨0。保持默认，不能将局部救回升级为可靠替换。

计数覆盖全部1024，默认回归与同入口主返回、原生路由float64参考、两种整数计分均通过；同一执行者审查，非独立人员审计。正式native186.425/199.437秒，准备/编译/评价/诊断另列，行政未知不填0，历史训练债保留。样本已曝光、单图、两L、组间难度混杂、描述CI未多重校正；未测在线风险门控或离线归属范数改造，不把诊断全H排名当免费特征。

[风险判断与实测案例](entry_method_exploration/20261011_profile_routing_risk_v1/analysis/interpretation.md) · [48点/完整报告](entry_method_exploration/20261011_profile_routing_risk_v1/analysis/report.md) · [详细复盘](experiment_history/178_profile_routing_risk.md) · [对比图](entry_method_exploration/20261011_profile_routing_risk_v1/analysis/risk_effects.png)。
<!-- E178_CURRENT_END -->

<!-- E177_CURRENT_BEGIN -->
# E177 当前结果：入口表示小测（2026-10-11）

**最新实测为E177，48点/144完整单线程批次已完成。当前仍选GT10画像；代表query→GT1的单入口和三入口版本各自8/8点Recall、QPS都更低。默认仍为E99 GT10，Web soft-t1/Yandex hard。** 下方E176及以前全文保留历史身份。

两集各预锁1024条已曝光公共query，K1/K100、L200/800；比较原GT10、同字节重建控制、单位真实入口、代表query→原H、代表query→GT1的3/1入口。原代表query和全H从保存trace恢复，0新训练/GT。

| 对默认GT10 | Recall升/平/降 | QPS升/降 | 同L双升 |
|---|---:|---:|---:|
| 单位真实入口3 | 1/1/6 | 3/5 | 0/8 |
| 代表query→原H 3 | 0/0/8 | 0/8 | 0/8 |
| 代表query→GT1 3 | 0/0/8 | 0/8 | 0/8 |
| 代表query→GT1 1 | 0/0/8 | 0/8 | 0/8 |

GT1三入口ΔRecall −1.1719..−0.1035pp、ΔQPS −2.9988%..−0.8346%；单入口 −1.2695..−0.2246pp、−4.0110%..−1.4346%。真实入口更接近默认，但有取舍；相同GT10图仍出现−0.2711%..+0.6503%计时波动。很多Recall配对描述区间跨0，不把8/8点估计方向说成每点显著。20个预锁跨L比较无双升。

画像是离线构造，当前线上也只检索约800个向量。前128条计数显示代表query路由和主图搜索均未省NDC，符合其更慢；聚合查询方向的质量解释尚非独立因果证据。一个seed、历史曝光样本、两个L只支持小规模探索，默认不替换，不自动扩测。

全部默认输出回归、同字节控制、count128核验与两种整数计分通过；无独立人员审计、无timed逐轮返回保存。正式native整job153.858/164.866秒，离线/失败恢复/费用另列，继承训练成本不归零。见[详细复盘](experiment_history/177_entry_representation_quick.md)、[完整报告](entry_method_exploration/20261011_entry_representation_quick_v1/analysis/report.md)、[48点CSV](entry_method_exploration/20261011_entry_representation_quick_v1/analysis/points.csv)、[结果图](entry_method_exploration/20261011_entry_representation_quick_v1/analysis/comparison.png)。
<!-- E177_CURRENT_END -->

<!-- E176_CURRENT_BEGIN -->
# E176 当前结果摘要（2026-10-10）

**最新实测为 E176：冻结 160 点/480 个完整 wall 批次、800 个比较、60 个机制记录与独立整数/wall/trace 审计均完成。默认仍为 E99 GT10（Web `GT10-soft-t1`、Yandex `GT10-hard`），原 M5 保留；本有限版本完成后 STOP。** 下方 E175/E174/E173 及更早正文完整保留，其停止、预算和状态只对应各自历史范围。

本轮完整保留原 M5 的监督表、三入口主搜索及全部 C≤24；新 `M5OPT` 在完整返回逐词等价前提下复用主搜索已付的 R 分数。`M5RES12` 在该优化基础上，用合法 TRAIN 中 `GT_K−原M5最终返回` 的剩余遗漏，按 `(route,原C winner)` 查询 K/L 专用补全表，额外目标≤12；没有丢弃原 M5，也没有重开图搜索。

| 本轮同 L 证据 | 实际判断 |
|---|---|
| M5RES12 对原 M5 | 20 点 Recall 14 升/6 平/0 降，12460 个 query–GT 成员救回、0 损伤；以两个工作点 QPS 中位数判严格双升为 8/20，原冻结三轮配对速度比口径为 9/20。 |
| Web K100，M5RES12 对原 M5 | 五个 L 均增加 Recall `+0.1543..+0.4168 pp`，点 QPS 中位数变化 `+0.3769%..+1.8872%`。这是组合实现收益。 |
| M5RES12 对 M5OPT | 严格双升 0/20；点 QPS 中位数变化 `−0.6993%..+0.0321%`，所有 Recall 增长点都更慢。M5OPT 对原 M5 的完整返回字词 20/20 相同，因此组合收益的速度来源是工程省费，不能归给残差补全本身。 |
| PAIR 对 route-only WIDE12 | Recall 1 升/5 平/14 降，双升 0/20。两者在线上限相同，但离线键数、总目标槽和 resident 未配平，不能作 winner 条件化的纯因果判断。 |
| M5RES12 对 GT，同 L | 仅 Y K100/L1200 有弱双升信号：`+0.0064 pp`、点中位数 QPS `+0.082284%`（配对口径 `+0.176726%`）；三轮并非全更快，速度范围未分离，不能据此替换默认。 |

跨 L 的 12 个方法比较双升只覆盖两个 Web K1 预算对：L800→GT L1000、L1000→GT L1200；原 M5 在同小 L 已有优势。没有新增 K100/Yandex 跨 L 双升，也没有插值到未测 L。两种速度定义不一般相等：原端点是三轮 `QPS_A/QPS_B` 比值的中位数，曲线端点是两个已存 QPS 中位数之比；全部 800 原比较及标志保留，解释补充列出整体 3 个双升标志分歧，没有改策略门或挑选点。

范围为两集各已曝光的公共前 10K、真实 K1/K100、L=200/400/800/1000/1200、八方法、CPU15/T1、三轮完整正常 Batch 生命周期，只有 `public_test`，没有新确认。全量单次 untimed scalar/linear oracle 与完整字词资格已过；没有第二整批 native replay，也不保存 timed 输出。NDC 是固定256样本，候选 trace 为完整10K；CI 仅描述性，独审未重生 bootstrap 端点。表外 ID、U 外救回和监督覆盖不直接证明跨模态泛化。

新增 FIT 获单次每集≤900秒明确授权，实际 Web **469.143610秒**、Y **472.986268秒**；保留旧 TRAIN 债后累计分别 **22194.116446秒**、**16062.191988秒**，旧7200秒限额超支不清零。实际预算计时包含 native/compiler 两子进程完整生命周期，不含随后 manifest load/hash 与行政收尾；这些未计量部分保留未知，不填0。正式 native 整 job 分别 **6970.796179秒**、**7089.322895秒**，包括 startup/oracle/count 等，不能再与其内部 QPS wall 相加；RSS 为约0.25秒采样观测峰，非精确峰值。工程构建、资格、评价、独审和展示费用按实际收据分别披露。

交付入口：[E176历史与归因](/data/netg/ACSG/experiment_history/176_m5_residual_completion_curve_v1.md)、[冻结报告](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/report.md)、[全部800比较解释](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/interpretation.csv)、[实际费用账](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/cost_ledger_supplement.md)。交付图：[主曲线 PNG](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/figures_delivery_v3/recall_qps_budget_curves.png) / [SVG](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/figures_delivery_v3/recall_qps_budget_curves.svg)、[机制曲线 PNG](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/figures_delivery_v3/mechanism_budget_curves.png) / [SVG](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/figures_delivery_v3/mechanism_budget_curves.svg)。[结果独审](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/independent_result_audit/report.json)、[最终交付复核](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/final_delivery_review.json)。

不恢复旧队列，不自动新 fit、适配方法或启动确认；GT10 默认、原 M5 研究与全部历史科学源/锁/raw 保留。
<!-- E176_CURRENT_END -->

<!-- E175_CURRENT_BEGIN -->
## 最新实测：E175 五档 Recall–QPS 曲线已完成（2026-10-10）

当前默认保持 production E99、WebVid `GT10-soft-t1`、Yandex `GT10-hard`；原 M5 保持研究方法和独立对照。新方法 `M5REG96` 保留原 M5，再从其候选种子的一跳邻居补全。此次扩展实际完成 **80 点、240 完整单线程计时批次**：两数据集各公共前10,000查询、真实K1/K100、L=200/400/800/1000/1200、NSG/GT10/原M5/M5REG96。四方法均本轮匹配重测；QPS为三轮中位，误差线min–max。

同 L 相对原 M5，M5REG96 的20点 Recall **17升/3平/0降**，增量0～+0.1600百分点；配对QPS **20点均降**，变化−3.261940%～−0.034929%。新扩展共救回4138个命中成员、损伤0；这是跨工作点成员次数和，不是唯一ID数。此次仍为 Recall/速度取舍，没有同 L 双升。

80个预锁跨 L 比较仅4个双升，实际只对应 WebVid K1 两组预算：M5/REG L800 对 GT L1000，及 M5/REG L1000 对 GT L1200。REG 两组 ΔRecall/QPS 为 +0.30pp/+23.459832%、+0.37pp/+18.822102%；**原 M5 已在相同两组双升，区域扩展没有新增双升预算组合**。WebVid K100、Yandex K1/K100均无跨 L 双升。

所有native full replay、原M5/region全量oracle通过；独立结果审计实核80点/240轮/200比较/20机制，曲线再独核80点映射与min–max。新增TRAIN=0；原监督/构建债保留。native阶段总8798.964398秒（含加载、warmup、oracle、正式搜索、保存），评价25.032714秒、独审35.906468秒，绘图0.920985秒；正式QPS不含离线阶段，阶段费用不可和内含搜索wall重复相加。

这是 E173 已曝光公共窗口的离散描述，单public_test角色，没有新独立确认；不支持默认替换或连续L性能推断。此次用户有限授权的五L扫描、图和报告全部交付后停止，E173/E174原件与历史STOP保持原范围。

入口：[PNG曲线](entry_method_exploration/20261010_m5_region_budget_curve_v1/analysis/final_v1/figures/recall_qps_budget_curves.png)、[SVG](entry_method_exploration/20261010_m5_region_budget_curve_v1/analysis/final_v1/figures/recall_qps_budget_curves.svg)、[80点CSV](entry_method_exploration/20261010_m5_region_budget_curve_v1/analysis/final_v1/points.csv)、[完整报告](entry_method_exploration/20261010_m5_region_budget_curve_v1/analysis/final_v1/report.md)、[详细复盘](experiment_history/175_m5_region_budget_curve_v1.md)、[终态](entry_method_exploration/20261010_m5_region_budget_curve_v1/state.json)。以下E174原文完整保留其历史身份。
<!-- E175_CURRENT_END -->

# ACSG 当前结果摘要

<!-- E174_CURRENT_BEGIN -->
2026-10-10：最近完成实测为 **E174：M5 残差区域扩展**。冻结112点、336正式批次及四job全部成功；完整4096评价和独立整数/成员/wall/trace审计已实际通过。原 M5 完整保留，M5REG96 只是从原候选 C 选种子并沿原 NSG 一跳追加 X，原 M5 始终是对照。

主方法相对原 M5 的16个同 L点中，14点Recall增、2点持平，三轮按序QPS比中位数全部下降 **0.13%–0.70%**；相对同L GT也全部为Recall/速度取舍。跨L只有WebVid K1的b组观测双升（Recall +0.8301百分点、QPS +23.46%），a组Recall仍−0.0732百分点；b组原M5已有+0.6592百分点/+23.94%的跨档优势。**原协议与更严格报告的主方法复现门均为0合格**，不能把原M5优势全归给扩展。停止本冻结一跳/seed/cap版本，保留原M5研究与历史结果；GT10仍默认（production E99，WebVid GT10-soft-t1 / Yandex GT10-hard）。

新增TRAIN/拟合/教师/画像或主图构建=0，历史每集TRAIN超额不重置。四native实际总耗时7015.3075秒，其中336正式owned wall为4069.756秒，已包含在native总时长内；评价19.2674秒、整数独审28.0881秒，工程/身份/展示费另见报告。只有两角色各4096、K1/K100及两档L；NDC仅固定均匀256，timed packets未保存，CI端点未由整数独审重生，native回调符号UNRESOLVED的绑定范围保留。期间行政监控曾看到部分a组速度，没有看到质量或改动冻结策略，事件已留痕。见[完整报告](entry_method_exploration/20261010_m5_residual_regions_v1/analysis/final_v1/report.md)、[固定入口](entry_method_exploration/20261010_m5_residual_regions_v1/README.md)、[E174详细记录](experiment_history/174_m5_residual_regions.md)与[独立解释](entry_method_exploration/20261010_m5_residual_regions_v1/reviews/result_interpretation_independent.md)。以下E173及以前文字保持历史身份。
<!-- E174_CURRENT_END -->

<!-- E173_CURRENT_BEGIN -->
2026-10-09：E173 已完成两集×三方法×两 K×五 L 的 60 点、180 批完整单线程复测，**M5 正在研究**，基于 GT10 增加冻结残差补全。WebVid/Yandex 各公共 test 前 10K；L=200/400/800/1000/1200，K=1/100 分别真实搜索。无新训练或 test 调参。

同 L 相对 GT，M5 的 20 点 Recall 全部提高、真值近邻成员损伤 0，QPS 配对中位约降 0.16%–4.85%。WebVid K1 提高 0.97–1.92 pp；Yandex 提升很小。WebVid K1 的 M5 L800 相对 GT L1000、M5 L1000 相对 GT L1200 有实测双升，QPS 中位比约 +24.25%、+19.25%；其他三场景没有跨 L 实测双升。相对 NSG，同 L 的 GT/M5 全部 20 点 Recall 与 QPS 中位数均更高，各 19/20 点三轮配对速度都提高。默认保留 GT，不据本轮局部优势宣称 M5 全面替代。

先读[本轮结论与网页阅读入口](research_snapshots/20261009_nsg_gt_m5/README.md)，再读[完整实验报告](entry_method_exploration/20261009_nsg_gt_m5_test_v1/analysis_v2/report.md)、[五档曲线](entry_method_exploration/20261009_nsg_gt_m5_test_v1/figures_v2/recall_qps_nsg_gt_m5.png)、[全部60点CSV](entry_method_exploration/20261009_nsg_gt_m5_test_v1/analysis_v2/metrics.csv)。方法说明：[3页PDF](entry_method_exploration/20261009_nsg_gt_m5_test_v1/advisor_report/concise_v1/GT与M5方法说明.pdf)、[简洁正文](entry_method_exploration/20261009_nsg_gt_m5_test_v1/advisor_report/concise_v1/method_report.md)。

Native 含加载和核验：WebVid 44.90 分钟、Yandex 46.18 分钟；新增训练 0。公共 test 有历史曝光，不称新盲测。计数/parity 只覆盖预锁256条，全10K返回、Recall及M5线性合并核验通过。下文为此前时点的保留记录。
<!-- E173_CURRENT_END -->

当前见[Git结论交接](research_snapshots/20261006_results/README.md)和[八方法详细报告](research_snapshots/20261006_results/report.md)，核实时点2026-10-06T21:32:45.619435+08:00。

每dataset跨全部方法TRAIN限7200秒；历史已超额，禁止新增训练。

阶段快照：8方向均已开始探索，7有阶段边界；已接受134/288 native（120normal+14audit），正式评价1/4；无可靠默认替换。

第12行起均为历史快照；旧预算解释、旧运行状态与未执行描述不覆盖上述当前结论。


2026-10-04 最新用户约束：用户原话“一个数据集的训练预算是两个小时以内吧”。Root按当前多方法探索上下文解读为每个方法×单个数据集的累计训练／拟合不超过7200秒；这是root解释，不是用户逐字说了“每方法”。同方法同数据集的K1/K100、FIT0、FIT1、refit及全部轮次共用一项累计预算，不按K点、轮次或阶段重置。监督／标签生成、构建、验证分别计时披露；用户未确认整条离线流水线总成本也是7200秒。详见[训练预算约束记录](entry_method_exploration/20261003_all_methods_experiments_v1/m2/training_budget_constraint_20261004_v1.json)。

训练预算已确认，但累计账本、实际timeout与执行guard尚未实现或运行，精确cost-check上限仍null；此前1小时只是历史root工作假设。不能靠阶段改名规避用户拒绝天级工期，预计整条路线仍需天级时不推进。M2原stage03未进入训练；最近进程事实只引用root于2026-10-04 10:32:35（上海）的观察：PGID 90589/100130可逆SIGSTOP、原六PID T/Ts，partial proof仅STAT为129566205B／inode1319835／mtime10:32:32.040776279，原件保留、未终止或恢复、不是完整六stage成功。本次没有fresh进程／proof核实，挂起不能替代实际终态；见[此前成本挂起记录](entry_method_exploration/20261003_all_methods_experiments_v1/m2/runtime_budget_hold_20261004_v1.json)。

目标仍是可靠的完整 Recall–QPS 综合改进；生产E99、Web GT10-soft-t1、Yandex GT10-hard不变，尚无可靠新综合收益或默认替换。M5已有局部SELECT信号，独立审计和CAL／confirm仍未完成；本次没有新增性能证据。 [M2等价几何降成本源码独审](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/m2_exact_geometry_budget_source_v1_independent_static_v1.json)与[B4精确拟合降成本源码独审](entry_method_exploration/20261003_all_methods_experiments_v1/m4/b4_exact_fit_budget_source_v1_independent_static_v1.json)均仅条件SOURCE-only；两候选尚未执行，实际等价、提速及≤2h训练满足均未证明。saved-M5审计v1 canonical-state lease执行路线已被root拒绝；独立local-state只作静态建议，未实现或放行。

本段及新预算记录是当前约束；以下“预算待回复／pending”“1小时假设”“仍live／离线投入不限”等完整保留此前时点，不覆盖本次预算和挂起边界。


2026-10-04 10:32:35（上海）最新状态：M2原stage03长作业已被Root可逆SIGSTOP，六个原进程均停止；partial完整保留，当前不是compiler/checker成功、六阶段终态或方法失败。[行政记录](entry_method_exploration/20261003_all_methods_experiments_v1/m2/runtime_budget_hold_20261004_v1.json)保存Root已观察的动作与元数据，本轮文档同步未查询进程或读取proof。此前3–4天是全量精确证明生成＋全量复核的预计工期，未进入该M2方法训练，不能写成“训练已耗时3天”。

用户明确不接受天级离线工期，单方法训练／构建／验证合计预算待回复。完整M2/M5/M4/C1-F2/B4与J25/J45/JBP探索目标仍ACTIVE、未完成；生产E99、Web GT10-soft-t1、Yandex GT10-hard及既有Recall/QPS保持。原M4/J45冻结族SELECT停止范围不扩，其他源码／行政资格不等于运行或可靠综合收益；待研究源码等价降成本与合法推进路径，尚无实现提速／预算满足证据。下文live或继续运行措辞保留旧阶段身份，当前执行边界为SOURCE/admin-only。


JBP 自有启动观察 V3 已通过[根组合源码审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_capture_own_startup_source_v3_root_composed_source_review_v1.json)及[独立组合审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_capture_own_startup_source_v3_independent_static_v1.json)：补齐实际 helper 登记、同一完整执行前／sealed body／执行后来源图，以及汇总时当前 stat 与探针历史 stat 的逐项比较。[V1 来源图 HOLD](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_capture_own_startup_source_v1_independent_static_hold_v1.json)、[V2 stat HOLD](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_capture_own_startup_source_v2_independent_static_hold_v1.json)及原封件保留。审查明确采用当前 V2 四模块全文加完整 V3 差异的组合基准；当前仅 SOURCE_ONLY、未编译／未运行，16 实际前件仍 null、16 flags 全 false。观察范围是首 K1 factory 与完整 workspace、首 JOIN 前的零评分前缀；原双 K／40K 行／七计划／全 E、σ、Γ保持，完整采集及 Recall/QPS 仍待。M2 原第3/6阶段继续，全五方法三联动尚未完成，M5实测与 E99／Web soft-t1／Y hard 默认保持。

JBP构建接线V2已完成[根条件SOURCE复核](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_capture_build_admin_source_v2_root_full_source_review_v1.json)和[独审](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_capture_build_admin_source_v2_independent_static_v1.json)：修复终态／构建授权／资源核对／恢复四处来源分类，冻结完整16字段构建环境并取消继承。原V1及[HOLD](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_capture_build_admin_source_v1_independent_static_hold_v1.json)保持；原科学配置和构建配方保持。当前仅未编译／未运行源码，16实际前件仍null、14flags全false；未来实际配置须完整绑定登记的73项来源，代码直接最低检查capture44，不能把这项外部root前件称为已执行。M2原stage03仍运行，完整五方法三联动未完成，M5实测及E99/Web soft-t1/Y hard默认不变。

JBP原生采集后端V1已完成[根条件整链源码审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_actual_capture_backend_final_root_composed_source_review_v1.json)和[组合独审](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_actual_capture_backend_full_independent_composed_source_v1.json)，66/65显式安全来源前后闭合；当前为SOURCE_ONLY、未编译／未运行。独审明确8份当前全文、1份完整旧admin加453行修正基准，作者sidecar由另一位审查者独审组合，未自签。通过范围仅条件代码契约与producer/consumer ABI，未授实际机器、全域费用、GTK、签名或资源资格。原两K/40K/七计划/全E/σ/Γ保持，两模式均完整枚举签名类，实际基数及资源可行性未知；13实际前件仍null/14flags全false。原M2同六stage仍在stage03，全五方法三联动未完成，M5实测和E99/Web soft-t1/Y hard默认保持。本轮V1登记窄审及“整包审查进行中”头部完整保存在[V1阶段备份](entry_method_exploration/20261003_all_methods_experiments_v1/source_before/root_before_jbp_capture_composed_source_sync_v2/original/summary.md)；下文UNIMPLEMENTED属于此前阶段，不代表实验已经执行。

当前 J25 修复版 V2 的[根全文源码审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/j25_joint_source_v2_root_full_source_review_v1.json)及[独审](entry_method_exploration/20261003_all_methods_experiments_v1/b4/j25_joint_source_v2_independent_static_v1.json)已通过：原 64MiB 仅限完整 Export 文件，额外驻留、scratch、上下文、加载暂存及代码内存完整另报，未新增总 RAM 门。根读完整 15 份当前源码并重建 12 AST/7 个科学函数体，159 个安全来源闭合；独审闭合 158 个。原 V1/HOLD 保留，四点、43 控制及原费用范围保持。目前只完成 SOURCE_ONLY，22 项实际前件全 null，未编译、运行或签实际预算/联合性能；JBP 真实采集后端仍未完成。完整五方法、三联动继续，已有实测及生产 E99/Web soft-t1/Y hard默认不变。下文“V2正在修”的段落保留此前阶段身份。

当前新增源码进度：[G1求解/五控制导出根源码审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_global_reference_solver_source_v1_root_full_source_review_v1.json)及[独审](entry_method_exploration/20261003_all_methods_experiments_v1/m4/jbp_global_reference_solver_source_v1_independent_static_v1.json)已关闭原同域两阶段重评、F-only全局表、固定A/固定pi2/full G1求解与五控制原格式byte导出接口；6源全文、根70安全来源与独审69来源闭合，仅SOURCE_ONLY_UNRUN。[Inputs V2独审](entry_method_exploration/20261003_all_methods_experiments_v1/b4/jbp_global_reference_inputs_source_v2_independent_static_v1.json)已确认完整F-family原GTK补项，实际采集后端仍UNIMPLEMENTED，尚未采集/构模型/求解/导出真实native或新增性能。

[J25新joint接线v1独审HOLD](entry_method_exploration/20261003_all_methods_experiments_v1/b4/j25_joint_source_v1_independent_static_hold_v1.json)确认误把原64MiB whole Export限额改成totalRAM cap；V1保留，V2正按原范围修复。这是实现缺口，不是算法或联合性能失败。[原envelope部署范围勘误](entry_method_exploration/20261003_all_methods_experiments_v1/b4/jbp_global_reference_solver_source_v1_export_metadata_erratum_v1.md)说明原完整FIT0 grid/metadata保留并应全计预算。完整M2/M5/M4/C1-F2/B4与J25/J45/JBP仍未完成；生产E99/Web soft-t1/Y hard和既有实测不变。M2原同六stage作业仍在stage03 Web K1全Ω几何，未重启。

当前新增进度：[J25 lower reference v3根源码审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/j25_lower_reference_source_v3_root_full_source_review_v1.json)及[v3独审](entry_method_exploration/20261003_all_methods_experiments_v1/b4/j25_lower_reference_source_v3_independent_static_v1.json)已关闭lower唯一全四first-freeze/full48四filter前端的源码缺口；原all6→原四lower SELECT硬链保持。v1差异文件runtime-map、v2把atime纳入首hash稳定性的SOURCE HOLD原件保留；v3只修稳定stat与行政身份，保留四lower/primary Y K1/20K/4096、全部48功能/23计数、8原价格和7 whole-plan。[JBP全局参考core根审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_global_reference_model_core_v1_root_full_source_review_v1.json)及[core独审](entry_method_exploration/20261003_all_methods_experiments_v1/b4/jbp_global_reference_model_core_v1_independent_static_v1.json)保持SOURCE_ONLY，实际完整输入/排他费用与签名资格、solver/bound/native导出仍待。J25实际all6/all4、唯一首锁及full48未运行，distinct12factor/provider/caller及完整Recall-QPS仍待；源码审通过不授实际资格或收益。

[M5 startup v7根源码审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/m5_cal_confirm_own_startup_v7_root_full_source_review_v1.json)及[v7独审](entry_method_exploration/20261003_all_methods_experiments_v1/m4/m5_cal_confirm_own_startup_v7_independent_static_v1.json)已关闭原CAL/confirm自有startup接线：同原gate/role/4096-prefix/source闭包后，同sealed memfd送原v9子进程，恢复后继续原warmup/五wall，phase→CAL→confirm消费同binding。v5遗漏context两路径键、v6遗漏相对目录引用的SOURCE HOLD保留，v7修正两项；原12job/16版本、有限非空S事前锁/全4-8 ledger、CAL1/80和confirm1/160保持。own registry/allpath/unsigned6角色+2profile/外部root六资格等实际前件仍null，未prepare/执行CAL或confirm。JBP unposted FIT1 v3源审保持；[JBP 44 post教师v2根源码审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_post_teacher_own_startup_source_v2_root_full_source_review_v1.json)及[v2独审](entry_method_exploration/20261003_all_methods_experiments_v1/b4/jbp_post_teacher_own_startup_source_v2_independent_static_v1.json)已关闭三项行政源码缺口：NONE哨兵、完整probe/unsigned来源根绑定、actual/expected SHA分列；v1 SOURCE HOLD原件保留。原140任务/44教师/20K/三tick及全部控制保持，实际own registry/六义务/all44 probe仍缺，未prepare或执行；真实FIT/求解/联合仍待。原M2同六stage作业仍在stage03；本次仅SOURCE_ONLY/安全元数据，完整八方向目标、已测结果和E99/Web软t1/Y硬默认保持。

当前目标是可靠的 Recall–QPS 综合改进。生产E99、Web GT10-soft-t1、Yandex GT10-hard保持。172五方法/三联动仍执行中，M5四点实际SELECT已评估，尚无可靠新综合收益、默认替换或完整请求完成。

J45独立caller v4已通过[根全文源码/最终身份复核](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/j45_fullcaller_v4_root_full_source_review_v1.json)及[独立静审](entry_method_exploration/20261003_all_methods_experiments_v1/m4/j45_fullcaller_v4_independent_static_v1.json)；267安全来源前后闭合，另核固定两image的SHA身份。原四点、四角色、16×42全部对象/顺序、M5强控制和科学函数保持。初次三seal原字节另存，仅修正非消费cache_schema标签V1→V2后重封；10核心代码不改。[近似provider](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/j45_approx_provider_source_root_full_review_v1.json)、[独立cached-R oracle](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/j45_cached_packet_oracle_source_root_full_review_v1.json)、[SHA bootstrap](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/j45_buffer_sha_bootstrap_source_root_full_review_v1.json)、[四点trace空结果](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/j45_trace_empty_results_root_acceptance_v1.json)均已具各自根/独审范围，并已集成到v4源码。四点trace为typed empty/lookup-disabled，proof未构造；源码PASS不签实际ELF、实例、完整cap/驻留、reuse或性能。尚未编译/运行，没有新增Recall/QPS或默认变化。

J25接续准备：原四lower-L点的discovery队列已由root实际生成/封签，v3独审及126份安全源码/元数据身份闭合；仅复制12项原始来源SHA声明，未读取数组/GTK字节、未执行搜索或几何。随后root在CPU0–5实际生成六个不可执行DRAFT：四点各自几何、全四汇总和route-word桥，primary仍Y K1，未来cache SHA均为null；125份独审身份及root前后127份安全来源闭合。M2完成门v2已通过源码独审，尚未调用、没有实际六stage终态/root审查。J25草案未封或运行，SELECT、same-R/provider核验及Recall/QPS仍待。见[discovery准备](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/j25_lower_discovery_actual_materialization_root_v1.json)、[六DRAFT实际生成](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/j25_lower_continuation_actual_draft_root_v1.json)和[M2完成门v2源码独审](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/m2_core_v10_terminal_gate_v2_root_independent_static_v1.json)。

172已完成两集全121920条新角色GT及64条独立float64全库抽检、四点原scalar响应/source核验、全部未抽样20K Ω和8项参考费用实测。8项费用已按原64全样/25类exact ceil归因独立审查并冻结；这是参考模型，不是实际helper税或QPS。M5两集共享表、全TRAIN整数greedy独审、必要质量门及全库/同U/Tiny强控制模型均已完成，正式四点SELECT强控比较及评估已完成，独立质量审计待完成。

M4两集各20K×4096=81,920,000个跨key配对均被保守外包盒排除，全部17嵌套尺度的可能SELECT覆盖上限为0；两集独审PASS，停止这个冻结共同证书族的SELECT准入。J45原四lower-L点同族几何lineage已独审并由[root停止证书命中准入](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/j45_common_family_select_hit_admission.root_decision_v1.json)：proposal几何不依赖L，零命中可继承，response/recipe/native资格仍独立；普通融合/缓存或整个联合的Recall/QPS未知。两项停止均不外推其他几何/总体/CAL/QPS。M5 Web @1必要门仍开但未质量通过；Web @100原A及Y两K同U的固定lower-L偿债失败，强控制与合法联合仍继续。

C1两集原ELF零query对象探针、A0/A1标量与A2自身batch4资格独审/实际汇总及root资格已闭合；原四组/clean补测完整packet和source核验后，按唯一clean Web @100/L1250首1024五wall总和全局冻结M0=scalar-span、Bcmp=strong166/span-batch4，两集共用。五wall总和依次20.380581246/18.781061241/15.852274359秒；其他点不参与选择。真实CLASSMAP/16384 witness/编图/replay及CAL尚未执行，未来不同ELF/角色仍须自有绑定。

M5原16版本×四点SELECT完整native及原五stage评估已完成：Web @1冻结主候选Recall +0.146484pp、五轮配对QPS比中位+24.1638%，召回差描述95%区间[−0.341797,+0.634766]pp跨零；Web @100/Y @1/Y @100分别损失1.008301/1.757813/2.239990pp，虽提速但未达到主质量门。Web @1 missing_frequency简单控制达到相同Recall/392.316 QPS，主候选信息优势未建立。独立实现/GT/全强控制审计尚待，未执行CAL/confirm或切默认。 B4原九stage first128及四点c/B已实际完成，完整source/terminal闭合、单线程无quota；Web K1(c=500,B=4928)、Web K100(625,5952)、Y K1(65,1152)、Y K100(129,2176)。c/B仅用原FIT0首128观察，不解码GTK作选择；完整20K全部七计划教师、原有限Π精确fit及JBP真实两阶段仍待。 详细当前证据、默认及成本见[172报告](entry_method_exploration/20261003_all_methods_experiments_v1/report.md)。

C1/B4原v14教师自有startup观察已通过两份独审及[root全文审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/c1_b4_own_teacher_v2_root_full_source_review_v1.json)，原六/六十八科学任务获[有条件授权](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/c1_b4_own_teacher_conditional_phase_decisions_v1/C1_FIT_AFTER_M0_FROZEN.decision.json)（[B4决定](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/c1_b4_own_teacher_conditional_phase_decisions_v1/B4_FIT0_TRUE_TEACHER_EXACT_POLICY.decision.json)）；新11/73 stage尚未prepare或执行。必须先有M2完整终态/root审查、固定M5终态和串行空窗，再核零query前件，并在每个真实教师自身首评分前观察对象/机器/全words/严格FP；不跨进程移借资格。新增行政成本计入作业wall，B4原三tick保持；[RET停点勘误](entry_method_exploration/20261003_all_methods_experiments_v1/b4/teacher_own_qualification_v2.observer_stop_erratum_v1.md)另存，原README/源不改。

M5 CAL/confirm v2已通过[root源码复核](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/m5_cal_confirm_frontends_v2_root_source_review_v1.json)，原12科学job、16版本及科学函数保持；实际saved-record v3审计、v9自有六评分义务、全四scope根决定与IID前提仍缺，未生成或执行CAL/confirm队列。这些源码审查没有签实际质量、QPS或默认资格。

接续状态：M2原core_v10两集全N exact-native96缓存生成及逐原ID检查已实际完成：Web N=2,505,000/d=512，Y N=10,000,000/d=200，均96B、sampled=false、实际线程1/无quota。原Web根/独审保持，[Y stage02根核对](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/m2_core_v10_y_fullN_actual_stage02_root_metadata_v1.json)及[Y独审](entry_method_exploration/20261003_all_methods_experiments_v1/b4/m2_y_fullN_actual_stage02_root_independent_metadata_v1.json)已闭合；cache/base payload未由根或metadata独审重读，payload SHA是producer声明。原同一六stage队列当前执行stage03 Web K1/L1000全部Ω几何；后四项Ω/compiler/checker与whole/root完整终态仍待。这是离线生成与检查进度，不是helper税或线上QPS。 M5 saved-record独审v3已完成root全文及242安全源码/元数据身份复核，实际审计仍待串行空窗。B4原69stage队列已实际生成（重复语义门+原68任务），四点全20K/24列/三真实tick及原17次tie solve保持；队列尚未执行，C1/B4教师各自ELF的实际DC对象/严格FP/机器观察仍待执行，不能借v15、另一ELF或独立probe地址；新源码/有条件授权不代表实际资格。原B4生成器还对两集旧FIT0 GTK和行号四文件做SHA校验，未解码或执行teacher/solver；该例外已单列保留，不声称生成器零数值字节读取。 证据见[M5独审排期](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/m5_saved_record_audit_v3_root_readiness_v1.json)、[B4原队列生成](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/b4_fit0_original_69_queue_root_materialization_v2.json)。

172工程恢复只调整本轮行政存储：7772份任务产物逐SHA/link/mode/mtime迁至另一持久卷，通过bind保持原路径；行政v2总12GiB、双卷空闲6GiB、RSS32GiB，全部方法Export/resident/数据/质量/计时门不变。原2.5GiB失败、旧config/protocol及Y partial均保留。下面各理论/暂停段保留其历史阶段身份。

2026-10-03已按用户要求完成[新对话交接同步](experiment_history/_maintenance/20261003_new_conversation_handoff/README.md)；完整阅读顺序、五方法/三联动优先级、未知门与可复制启动指令集中在[s-target.md新对话入口](s-target.md#2026-10-03-新对话接续入口)。此次仅更新交接文档，无新实测、默认替换或实验授权；171封存状态、170及DOCX原件保持。

当前[171纯理论研究](experiment_history/171_overnight_algorithm_collision_and_certificates.md)已按最新用户期限研究至2026-10-03 **08:00（Asia/Shanghai）**并完成，状态COMPLETED_THEORY_ONLY_NO_EXPERIMENTS；先完成独立三首版，再结合指定本地DOCX完成五机制去重与联动分析，其后只交接和行政封存。0训练/GT/构图/ANN/性能/合成数值/旧数组新统计，未恢复runner。最新实测166，生产E99、Web GT10-soft-t1/Yandex GT10-hard不变，可靠Recall–QPS改善仍未达成。170及更早封存保持。

[独立三首版报告](entry_method_exploration/20261002_overnight_algorithm_audit_v1/report.md)与[统一首版伪代码](entry_method_exploration/20261002_overnight_algorithm_audit_v1/current_algorithms.md)推荐M2保序区间评分省略→M5残差posting补输出→M4响应证书复用，含比较、完整费用、证明/反例、原作与[冻结验证](entry_method_exploration/20261002_overnight_algorithm_audit_v1/frozen_validation.md)。本轮明确M2方位/恢复/离散/native损失与满池前必付评分，补精确整数元数据规格；核M4实际负IP输出recipe、M5 cal4/confirm8及选择范围。全部为文稿和条件推导，未生成artifact/价格/证书，未改首版参数，创新和真实综合收益未知。

[合并五方法与联动报告](entry_method_exploration/20261002_overnight_algorithm_audit_v1/combined_report.md)在原三方案之后结合DOCX保留C1-F2/B4两个不同机制，基础推荐仍M2→M5→M4；三条优先联合为M2+M5、M4+M5一次评分、七计划missing共享表后重拟B4。完整八项方案/比较和[联合冻结协议](entry_method_exploration/20261002_overnight_algorithm_audit_v1/joint_frozen_validation.md)已具体化、交叉审查并完成理论交付；0实验、创新/收益未知。当前q资格与默认回退完整计费、RMS候选覆盖边界、B4跨branch复用机会均已明确；完整线上费用不借离线预算预测文件。

[当前源码身份](entry_method_exploration/20261002_overnight_algorithm_audit_v1/local_source_identity_refresh.md)确认完整Faiss工作树/静态archive存在且本地修改与snapshot一致；实际linked程序/FP/helper/comparison/caller仍THEOREM_ONLY_UNBOUND。源码兼容、独立手审或代理优化不能代替该绑定及真实完整wall。详细理论增量留171记录，不在本摘要累积执行流水。

2026-10-02本次[170理论算法研究](experiment_history/170_recall_qps_algorithm_theory.md)已完成：广泛探索后交付[四个机制不同的完整方案](entry_method_exploration/20261002_recall_qps_algorithm_theory_v2/report.md)、比较表、前三优先级与最小冻结验证。没有训练/GT/画像/图/ANN/性能/合成数值实验或旧数组新统计；创新、native前件与真实综合收益仍待验证。容量归属仅候选审查，不预设为主线；最新真实性能166，生产E99与Web软/Y硬默认不变。指定743ee8c提交本地缺失，实际本地HEAD96cf05d，接续限制已记录；167–169封存保持。

2026-10-02 Git状态整理补充：[快照交接](research_snapshots/20261002/README.md)保存当前方法、实验记录及源码身份；[刚提出的容量约束图服务归属](research_snapshots/20261002/current_method.md)仅为未实现、未实验提案。最新实测166、理论交付169与现行默认保持，不增加性能结果。

当前项目目标为**可靠的 Recall–QPS 综合改进**，具体判定见[s-target.md](s-target.md)。截至性能记录166尚未达成；构建费用与代理指标改善不能替代完整线上收益。默认不变。

2026-10-02新任务[169 GT10算法与CCF B论文理论](experiment_history/169_gt10_algorithm_paper_theory.md)已补齐：选择完善现行GT10，形成[完整伪代码/中文主稿](entry_method_exploration/20261002_gt10_paper_theory_v1/paper_manuscript.md)、真实rank与hard/median-t1 soft三入口共同pool正反构造、相关rank方向风险/actual质量链、组件发现与完整费用条件，并完成交叉手审和原作对照。论文主线为“多rank query画像与有限图服务对齐”，不将小图/均值/标准lemma报首创。CCF B投稿充分性仍缺真实机制、最近方法区分和独立来源完整费用证据；0实验/程序数学/旧数组新统计/训练/GT/画像/图/性能。167/168封存保持，最新实测仍166，默认/生产E99不变；见[本轮报告](entry_method_exploration/20261002_gt10_paper_theory_v1/report.md)。

2026-10-02下午新指令：“再研究到下午四点，先完善理论，不开始实验”。[168独立纯理论阶段](experiment_history/168_theory_proxy_information_local_certificate.md)已按16:00（Asia/Shanghai，UTC+8）截止收口，COMPLETED_THEORY_ONLY_NO_EXPERIMENTS；只做手推证明/反例、原论文与静态源码/封存结论审阅。已交叉手审GT10代理的失配及正面条件、实际多入口/目标rank、局部返回保护/容量前缀、完整原评分组证书、策略校准/迁移及收费决策。[报告](entry_method_exploration/20261002_theory_until1600_v1/report.md)与[命题台账](entry_method_exploration/20261002_theory_until1600_v1/proof_ledger.md)区分解析结论与真实未知前件；线上可得性/数值界/覆盖率/净费用仍HOLD。0真实/合成实验、枚举及旧数组新诊断，上午167原件保持封存，没有新性能或默认替换。

用户随后明确：“不需要节省训练时间甚至可以增加训练时间，但是综合qps recall要提高”。训练/离线准备可以增加投入；以真实Recall与计全部新增费用的完整在线QPS评价，默认须共享相同优化机会。本轮继续理论，不开始训练或预处理。

2026-10-02用户授权先探索理论与方法，并阅读相关论文，至今天13:00（UTC+8）。本次[独立研究协议](entry_method_exploration/20261002_theory_until1300_v1/protocol.md)已冻结：研究历史/原论文、条件理论与反例，以及仅用旧ID/slot/已存响应的桶访问可行性诊断；不读取新query向量，不启动真实ANN/NSG、GT、训练、构图或正式性能。本轮理论研究已于13:00结束并封存，性能实验保持暂停，最新实测仍为166。

[167研究结论](experiment_history/167_theory_search_response_access_cost.md)已补有限pool发现/安全前沿/合法返回类与native区间条件，核对直接前作；只读三桶物理M均值Web107.330/Y86.837，旧TargetBank slot仅覆盖33.765%/45.728%，Web主R1旧50次救回40次桶外。已补读20篇原论文相关章节，包括已在E96/E97/E103适配的GATE和需改变图/搜索合同的PSP/MAG。该覆盖不是新Recall/QPS；粗筛不能继承旧局部收益。优先保留原路由距离memo的成本隔离问题，但须与原版/UpperHandoff/同memo默认中更快版本比较，旧Web主R1完整wall缺口约23.282μs/query。memo、原阈值拒绝、三桶及新联合动作均HOLD、未实现/运行；[主报告](entry_method_exploration/20261002_theory_until1300_v1/report.md)与[具体后继门](entry_method_exploration/20261002_theory_until1300_v1/candidate_gates.md)分开于真实性能。

2026-09-30 19:44按用户“先停下来”暂停该日作业；原22:00推进安排已暂停。已完成至记录166并封存。目标桶粗筛仅保留设计，未实现或运行，默认不变。

[166冻结目标库曲线](experiment_history/166_target_bank_frozen_curve.md)已完成36点/108轮完整wall与独立核验。**冻结目标库保留WebVid R1的质量/速度取舍，尚无已测点的稳定Recall–QPS综合改善；结束本次有限曲线核验，不扩网格、ef、样本或重复。默认保持Web GT10-soft-t1、Yandex GT10-hard与生产E99。**

下表为166共享span+batch4研究核的默认入口策略/TargetBank实测；原E99输出回归通过，绝对QPS不作为生产E99现场计时，生产未切核。

| 组合 | 各自最快实测R90的L | 默认实际Recall / QPS | TargetBank实际Recall / QPS |
|---|---:|---:|---:|
| WebVid R1 | 1000 | 90.454102% / 417.190 | 90.991211% / 413.177 |
| WebVid R100 | 1250 | 90.581543% / 334.895 | 90.576416% / 333.291 |
| Yandex R1 | 128 | 90.625000% / 2364.615 | 90.625000% / 2283.658 |
| Yandex R100 | 256 | 91.044434% / 1289.884 | 90.885010% / 1264.985 |

Web R1三个预算的质量差+0.659180/+0.537109/+0.390625pp，QPS−1.8363/−0.9620/−1.0204%；保留局部取舍。12个同预算点目标库均更慢，72个跨预算比较无经验支配，未实测同Recall更快。历史4096开发query/稀疏网格，不外推全预算或独立确认。全部147456返回及统计复算通过。

[165查询→真实目标迁移](experiment_history/165_query_target_transfer_online.md)已完成独立核验。**直接查询→GT1迁移未形成相对默认的稳定Recall–QPS综合提高，停止本固定迁移版本；保留目标侧简单对照的Web R1质量/速度取舍。默认仍为Web GT10-soft-t1、Yandex GT10-hard与生产E99。**

| 工作点 | Default3 Recall / QPS | QueryTarget1 Recall / QPS | ΔRecall pp及95%描述区间 | ΔQPS |
|---|---:|---:|---|---:|
| WebVid R1/L1000 | 90.454102% / 423.710 | 90.551758% / 416.559 | +0.097656 [-0.292969, +0.488281] | -1.6878% |
| WebVid R100/L1250 | 90.581543% / 335.485 | 90.591064% / 332.523 | +0.009521 [-0.063477, +0.083252] | -0.8828% |
| Yandex R1/L128 | 90.625000% / 2386.805 | 90.112305% / 2260.786 | -0.512695 [-1.098633, +0.097656] | -5.2799% |
| Yandex R100/L256 | 91.044434% / 1329.735 | 90.688232% / 1276.806 | -0.356201 [-0.634033, -0.082269] | -3.9804% |

目标侧简单控制在Web R1为90.991211%/420.254 QPS，相对默认+0.537109pp [0.122070,0.952148]、QPS−0.8156%，保留局部质量/速度取舍；未证明同Recall更快或跨集稳定。Web查询配对相对打乱有局部信息，仍不足以超过默认与简单控制。全98304返回/映射/四图/原生/统计核验通过，停止本版扩实例/ef/近邻/GT数/模型。

[164状态/rank完整在线验证](experiment_history/164_router_rank_pareto_online.md)已核验。**本固定状态/rank版本没有形成稳定的Recall–QPS综合改善，停止继续调状态、trace、支持阈值、深度、L、样本或seed。默认仍为Web GT10-soft-t1、Yandex GT10-hard与生产E99。**

| 数据集/工作点 | Default Recall / QPS | StatePareto Recall / QPS | ΔRecall pp及95%描述区间 | ΔQPS |
|---|---:|---:|---|---:|
| WebVid R1/L1000 | 90.722656% / 419.773 | 90.600586% / 418.127 | -0.122070 [-0.292969, +0.024414] | -0.3922% |
| WebVid R100/L1250 | 90.679443% / 339.305 | 90.649902% / 340.938 | -0.029541 [-0.067139, -0.006836] | +0.4812% |
| Yandex R1/L128 | 91.577148% / 2391.821 | 91.455078% / 2373.680 | -0.122070 [-0.415039, +0.170898] | -0.7585% |
| Yandex R100/L256 | 91.399658% / 1314.626 | 91.302002% / 1322.325 | -0.097656 [-0.197272, -0.016846] | +0.5856% |

两K1区间跨零、两K100区间负；K100轻微提速伴随召回下降，未证明相同Recall更快。State四点召回均未超过置换控制。完整在线/原生/64规则与全部统计复算通过；历史开发数据和OOF模型切换不冒充独立确认。

用户于2026-09-30 17:44明确：**主目标是完整端到端Recall–QPS综合提高，构建费用不是优化重点。** 下列构建费用收益只保留为附属事实，不视为主要目标完成。尚未执行的目标质量压缩诊断已取消；接下来回到廉价入口信息与真实线上效用，见[目标修订](entry_method_exploration/20260930_theory_until2200_v1/online_priority_steering.md)。

2026-09-30原定理论研究至22:00，现已按用户指令暂停。**默认保持Web GT10-soft-t1／Yandex GT10-hard、生产E99；Energy选样未获得稳定新源召回改善，停止本版调参，低标签成本候选继续保留。** [157四模型两批新源验证](experiment_history/157_energy_selection_two_source_batches.md)已全部核验，每集8192 query、真实K1/K100、CPU15实际单线程：

| 数据集／点 | 默认Recall／QPS | Energy Recall／QPS | ΔRecall (pp)及描述95%区间 |
|---|---|---|---|
| WebVid R1/L1000 | 91.198730%／412.839 | 91.088867%／413.549 | -0.109863 [-0.219727, -0.012207] |
| WebVid R100/L1250 | 90.605103%／334.329 | 90.578979%／334.938 | -0.026123 [-0.039185, -0.014526] |
| Yandex R1/L128 | 91.516113%／2335.782 | 91.467285%／2339.041 | -0.048828 [-0.195312, +0.097656] |
| Yandex R100/L256 | 91.037231%／1306.000 | 91.034058%／1303.324 | -0.003174 [-0.088989, +0.080203] |

[160共享三方完整构建](experiment_history/160_shared_batch_full_build_identity.md)已审计：Web Default／Uniform／Energy为332.954／119.980／130.046秒，完整身份都恢复；Yandex为602.533／149.230／163.878秒，但新Default因1条近并列目标跨hub变化，W两行及图改变，不能沿用旧质量。两份Y候选身份恢复；本轮0新线上性能。原默认不变，费用与身份不合并判定。

[163误差条件链](experiment_history/163_soft_mass_transport_pipeline_conditions.md)已补齐目标/温度、平均归属、归一化、评分间隔、实际入口到固定搜索的保真条件，并通过独立合成核验；不能推出召回提升或费用保证，0新真实数据/模型。

[162单球/单hub证书](experiment_history/162_single_hub_geometric_certificate_opportunity.md)在两集各20K训练query均0通过，exact阈值也远低于上界；全量独立核验通过，停止这份过松的固定球界，不调参续跑。0新搜索/模型，默认不变。

[161完整hard质量条件](experiment_history/161_hard_mass_interval_certificate.md)的固定枚举与独立子集核验通过：ID不定仍可计数固定，多数类别稳定则不足够。这只是数学条件，真实界/成本未证；没有新模型或搜索。

[159共享精确标签检查](experiment_history/159_exact_label_batch_and_rank_dispatch.md)已核验：batch1024/k100对原batch256/k100的Web/Y费用比0.9796/0.3489，消费前10有序ID改变0/0条；主费用门通过。这是各1024条的离线微测，旧完整费用不外推替换，完整模型身份仍需验证。

[158只读连接诊断](experiment_history/158_energy_profile_routing_search_bridge.md)进一步确认：Energy对默认分数的平方差较Uniform低13.3%／28.0%，但648／772条换入口只改变11／24条R1返回。几何改善在新query上存在，仍非Recall保证；观察性分组不归因于拓扑。另澄清[145旧R100计数](entry_method_exploration/20260930_theory_until2200_v1/research/routing_member_count_clarification_v1/report.md)为每query净差累计，真成员增损已补表，旧净Recall不变。

Energy相对同2048预算Uniform的ΔR1/R100为Web+0.012207/−0.001343pp、Y−0.061035/+0.003784pp，四区间均跨0；Web R1净+1／Y净−5，R100都跨批异号。Web相对Default两点两批均负，质量损失保留；Y仍有较大不确定性。相对Shuffled也未形成稳定信息优势，一个打乱模型不是随机化检验。完整QPS、全部轮次、两批与全部6方法对均保留，不自动称非劣／线上更快或切默认。

[156固定r0完整构建](experiment_history/156_energy_selection_actual_full_build.md)Energy131.133／259.137秒，对[154同享按需QGT的默认](experiment_history/154_fair_default_demand_build_cost.md)336.051／1519.754秒，单次少60.98%／82.95%；包含教师、选择、两次载入和补标，未清缓存、非随机重复。[148原均匀混合](experiment_history/148_demand_qgt_full_build_cost.md)114.023／243.072秒及[151原主混合新源质量](experiment_history/151_frozen_hybrid_two_source_batches.md)保留各自身份，不把不同Web温度候选的费用拼接。共享批处理微测已完成，原完整构建费用仍保持实测身份。

[155训练信息门](experiment_history/155_energy_selection_without_exact_temperature.md)的方向误差均值少6.811%／23.330%仍成立，但没有保证检索收益；复杂LOO原153失败不回改。四模型分数到搜索的只读分解已完成，不按曝光query继续补标。[145二阶矩用语澄清](entry_method_exploration/20260930_theory_until2200_v1/research/routing_bridge_clarification_v1/theory.md)和[152温度／标签交叉项](experiment_history/152_temperature_label_error_interaction.md)保留理论边界。

2026-09-22晚间。**原默认保持；ApproxTarget10保留为低成本候选，不再因一个区间未过而直接停止探索。** Web默认GT10-soft-t1，Yandex默认GT10-hard，生产主搜索E99。

## 9月22日历史单批复测

用户要求的E125冻结模型Web单组复测已于21:21前完成核验。4096条新源query、K1/L1000、CPU15实际1线程、三次完整wall：

| 方法 | Recall@1 | 命中 | 完整QPS |
|---|---:|---:|---:|
| GT10-soft-t1 | 90.795898% | 3719/4096 | 419.559 |
| ApproxTarget10 | 90.649414% | 3713/4096 | 419.121 |

候选救回6/损伤12，差−0.146484pp，95%配对bootstrap描述区间[−0.341797,+0.048828]；QPS−0.104439%，三轮范围重叠。旧批同点为−0.097656pp、3救回/7损伤；两批均小幅为负，不能说无损或线上更快，但仍可评估费用与质量取舍。新批与登记split、旧E105整个20K窗口及原画像拟合输入字节互斥，源顺序窗口不是全源随机/语义独立。全返回、原E99、线程/身份、精确GT和区间独立复核通过。[记录138](experiment_history/138_e125_web_fresh_check_and_policy.md) · [复测报告](entry_method_exploration/20260922_until2200_improvement_v1/stages/e125_web_fresh_check_v1/report.md)。

## 近似监督的价值与成本口径

原E125两集12点、三次完整wall中，所有召回均值损失不超过0.10pp，QPS差−0.2161%至+0.0893%；只有Web主点旧98.75%非劣下界没有过预定−0.25pp。原STOP门/结果保留。现在按用户修订策略，将探索与默认替换分开，状态为**RETAIN_LOW_COST_CANDIDATE**。单点区间未过不一票否决；保留实际损失及不确定性，不把放宽探索资格写成统计通过。[策略](entry_method_exploration/20260922_until2200_improvement_v1/research_decision_policy.md)。

20K画像近似目标完整作业Web64.591秒、Y28.040秒；对应exact20K搜索312.862/1417.293秒。近似单线程、exact受8个CPU限制，阶段/资源不同，不称同资源加速比。QGT5K精确监督仍保留。GT-inclusive当前默认核心构建合计403.997/1780.232秒，其中exact GT占97.94%/99.43%；不含公共底图、嵌入/下载/历史选型。[成本135](experiment_history/135_gt10_gt_inclusive_build_cost.md) · [原试验137](experiment_history/137_approximate_target_profile_cost_pilot.md)。

补充费用范围：Web继承的soft温度源于原20K精确GT1，Y-hard无该依赖。当前是固定既有H/参数下的近似标签费用改进，尚非新数据集从零构建验证；新复测有效性不变。[依赖与纠偏方向](experiment_history/139_approximate_supervision_scope.md)。

## 本轮机制结论

GT10的优势有具体证据：真实GT选H、十目标形成较稳定且保留语义对应的query方向、静态画像和廉价小图推理。固定20K两半下，Web GT1/hard10/soft10的画像夹角中位24.5°/12.1°/8.5°，Y GT1/hard10为27.2°/16.5°；去共同方向后仍保持，真实对应跨半亲和胜置换。闭式亲和最优与稳定性不等于Recall最优。[记录134](experiment_history/134_gt10_profile_direction_stability.md)。

E123真实目标区域服务策略有正值；E124预测更准仍未形成净收益，原因需要区分代理偏差与学生预测误差，不能仅归为模型弱。目标预算固定256-query全H诊断仍有余量，Web/Y K100 single+默认oracle为+1.586/+2.641pp，但只是历史query事后上限，不是可部署收益。[记录133](experiment_history/133_privileged_surrogate_decision_geometry.md) · [记录136](experiment_history/136_target_budget_fullH_opportunity.md)。

只读训练缓存已补核算：随机残差校正要在合力归一化的向量总和MSE上优于直接近似，Web/Y解析临界m约3269/8517，占20K的16.34%/42.58%。残差方差虽小，直接近似偏差也已部分抵消，少量补标不必更好。没有据此训练模型或选择m；这不是Recall门或否定混合监督，只用于评估投入。 [记录140](experiment_history/140_approximate_target_residual_variance.md)。

已有入口/返回的补充只读对齐显示：新Web1150/4096条换三入口集合，只有21条最终K1返回ID改变；当前预算下路由改变不等于搜索增益，不说明轨迹相同或全H无余量。[记录138](experiment_history/138_e125_web_fresh_check_and_policy.md)。

## 完整性能证据的位置

E103仍是最新完整五数据集重测，E118是最近宽预算候选比较；今晚E125是双集三预算及Web单点补测，不冒充五集新前沿。E103最快已测R90达标点上，Web K1/K100 QPS520.79/340.46（对NSG+24.99%/+0.79%），Y为2406.16/1241.64（+9.63%/+6.96%）；实际Recall分别90.7500%/90.6868%、91.0500%/90.9805%，方法L/Recall并非完全一致，非同Recall显著性结论。GIST收益基本持平，不能称所有数据全面占优。

当前无默认替换。9月22日流水已完成；9月30日研究已按用户指令暂停，已完成实验的原协议和证据保留。下一步见[s-target.md](s-target.md)。本轮[总报告](entry_method_exploration/20260922_until2200_improvement_v1/report.md) · [PDF](entry_method_exploration/20260922_until2200_improvement_v1/GT10理论与性能改进研究.pdf) · [理论](entry_method_exploration/20260922_until2200_improvement_v1/theory.md) · [改进方向](entry_method_exploration/20260922_until2200_improvement_v1/directions.md)。此前流水摘要已完整保存在[原文快照](entry_method_exploration/20260922_until2200_improvement_v1/reviews/root_docs_before_closeout/summary.md)，历史事实由[s-experiment.md](s-experiment.md)与详细卡片索引维护。
