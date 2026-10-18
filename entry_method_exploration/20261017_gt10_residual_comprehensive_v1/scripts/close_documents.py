from pathlib import Path
import json,re,hashlib,time
REPO=Path('/data/netg/ACSG');R=Path(__file__).resolve().parents[1];L='entry_method_exploration/20261017_gt10_residual_comprehensive_v1';D=L+'/analysis/delivery_v2';pdf='NETG_E183_GT10与残差_七数据集及失败查询_详细报告_20261017.pdf'
blocks={
'LOCAL_CODEX_START.md':f'''# 当前接续：E183 七集综合测试与详细PDF完成（2026-10-17）

最新完成E183：七集（含Deep/SIFT/GIST原L2）、645点/1935完整T1批次；[32页详细PDF]({D}/{pdf})、[中文报告]({D}/report_zh.md)、[详细复盘](experiment_history/183_gt10_residual_comprehensive_v1.md)、[状态]({L}/state.json)。GT10在Deep/SIFT可迁移；B32在这两集收益很小、K100曲线较低；GIST混合。Web/COCO补全曲线受益，Flickr交叉、Yandex K100较低。默认仍E99 GT10，有限矩阵完成，无待恢复队列。先读AGENTS与四根文档顶部E183，再读报告/审计；不要启动旧runner。

基底HEAD仍96cf05d5410cf51272048cd1f90b4bb194e23c62、research/state-20261002；E183是本地新产物，未提交/发布。旧结果和失败收据完整保留。
''',
'summary.md':f'''# E183 完成：GT10可迁移，残差在非多模态上的收益有限（2026-10-17）

完成Deep10M/SIFT10M/GIST1M原始L2与Web/Yandex/COCO/Flickr原始IP的645点、1935完整单线程批次；hard/soft与各自B8/B32分开，K1八L/K100七L。全部真实计时包三轮逐字一致、完整合并oracle及独立645点/540救损/360覆盖/2088分层/360级联/3600频次复算PASS。224样本全库float64 Top1及Top100集合全同；不是新盲确认。默认保留E99 GT10。

GT10-soft对NSG的K100共同区间折线QPS：Deep +1.60%～+7.94%，SIFT +1.53%～+4.87%；GIST-soft约+0.56%～+1.97%但三轮不全同向，SIFT/GIST K1混合。B32对自身GT10：Deep/SIFT K100曲线较低，GIST K100交叉；Web与COCO两K全共同区间改善、三轮描述同向，Flickr交叉、Yandex K100较低。线段估计不是新增等Recall实测，饱和点的多值分支保留。

事先L200/K100示例，soft Deep/SIFT、hard GIST的补回分别21/29220、25/18468、66/10886个遗漏（0.0719%/0.1354%/0.6063%），净Recall +0.0021/+0.0025/+0.0660pp，QPS -3.44/-3.22/-1.61%；该L200/K1三例救回0。Web-soft为20257/272967（7.4210%）、COCO-hard13715/46556（29.4591%），同L付出费用而完整曲线受益。

源覆盖直接限制：Deep 29220→全局源195→当前路由未截断86→B32救回21；SIFT18468→140→62→25。GIST10886→4242→1117→66，瓶颈分布不同。不能只按模态归因；规模/metric/训练密度未因果配平。全360补全点损伤5事件/2query：Web4近边界未证明特定native因果、COCO1个1ULP排序倒置；严格ID/GT不改。

正式suite18267.58秒（约5.07h，含内部正式wall、预热、保存及核验），独审407.80秒。初次Deep教师仅调度状态拼写修正、0重跑，26.80秒保留；源SHA330.27秒、GT抽审27.98秒部分重叠，不重复加总；继承完整冷启动成本未知。单图/单模型/已曝光测试、GIST1K、同K100教师跨K共表、未独立重算bootstrap/插值等限制保留。有限矩阵收口，未改默认。

[详细PDF]({D}/{pdf}) · [报告]({D}/report_zh.md) · [645点]({L}/analysis/final_v1/points.csv) · [独审]({L}/reviews/independent_results_audit.json) · [费用]({L}/analysis/cost_ledger.json) · [详细复盘](experiment_history/183_gt10_residual_comprehensive_v1.md)。
''',
'spec.md':f'''# E183 已实现并验收：跨metric残差与实际计时包合同（2026-10-17）

隔离目录[{L}]({L}/README.md)。七集直接引用已确认原base/图/画像/实际小图，三套非多模态保持squared L2、四套跨模态保持raw-IP；E97五集入口sorted_ids，E181两集heap_pop。已有hard/soft分别用合法16K、K100/L200遗漏训练单位query-target token的B8→16→32嵌套表；正式只测B8/B32，未截断TRAIN全局源/每hub源及token保留。测试GT不进入native搜索或编表，画像与残差训练可共享的来源如实标记。

native支持teacher/compile/qualification/benchmark；原scalar主核与模式2入口保持，POST只补算排除原返回/重复后的候选并合并。645点/1935批T1/CPU15全部完成，wall含正常Batch创建初始化、路由/主搜/补点、统一六向量复制与正常销毁；首轮实际四数组保存，另两NDC数组为零布局而非测量，counts_collected=false/NDC=null。其余两轮完整bits/SHA核验，全部POST相对同K/L实际GT10主包的独立标量/线性合并oracle通过；没有额外整批ANN替代计时包。

配置/旧源当前全SHA/阶段源码与binary/新表由各锁绑定。源抽审112文件完整SHA与224个全库float64样本通过；资格76个baseline对照256query逐字回归通过。独立集合脚本核645点、1935轮wall/QPS、540救损、360覆盖、2088分层、360级联、3600频次及全部TRAIN源。该独审不重算bootstrap、折线或全实际greedy序列。Deep首次父状态字符串误配的原FAIL及独立更正收据保留，科学native/查询未重跑。最终报告、PDF和视觉验收见[交付目录]({D})，旧科学源/默认未改。
''',
's-target.md':f'''# E183 授权范围完成：七集与详细PDF收口（2026-10-17）

用户要求的全面测试与详细PDF已完成：七集含Deep/SIFT/GIST非多模态L2、645点/1935完整单线程批次，GT10和残差分项、全L、失败救损/分层/级联/频次/来源覆盖及费用均有原始证据和独审。[最终报告]({D}/report_zh.md) · [32页PDF]({D}/{pdf}) · [状态]({L}/state.json)。当前没有待恢复性能队列，默认仍E99 GT10。

实际判断：GT10可迁移至Deep/SIFT；当前静态残差在两集的测试源覆盖不足，GIST为路由/容量限制和混合收益；Web/COCO保留补全曲线收益，Flickr/Yandex不作普遍正结论。后续问题是合法新训练遗漏源能否覆盖未知失败，以及容量/可部署困难识别是否值得在线费用；本轮诊断不启动新模型、追加teacher、种子、门控或补测。新的研究问题另定范围，旧历史原件保持。
''',
's-experiment.md':f'''# E183 当前实验索引（2026-10-17，已完成）

[183 GT10与残差跨数据集及失败查询综合评测](experiment_history/183_gt10_residual_comprehensive_v1.md)：七集含三套非多模态原L2，645点/1935完整T1批次；GT10在Deep/SIFT有迁移收益，B32对两集K100曲线较低，GIST混合；Web/COCO两K曲线受益、Flickr交叉、Yandex K100较低。独立整数/source/救损/频次审计PASS，5边界损伤事件/2query保留。32页详细PDF已交付；单图、已曝光测试与未独立重算CI/插值限制明确，默认不变、有限矩阵结束。

[报告]({D}/report_zh.md) · [PDF]({D}/{pdf}) · [全645点]({L}/analysis/final_v1/points.csv) · [独审]({L}/reviews/independent_results_audit.json) · [费用]({L}/analysis/cost_ledger.json)。
'''}
for name,body in blocks.items():
 p=REPO/name;text=p.read_text();pattern=r'<!-- E183_CURRENT_BEGIN -->.*?<!-- E183_CURRENT_END -->\n?'
 assert len(re.findall(pattern,text,re.S))==1
 text=re.sub(pattern,'<!-- E183_CURRENT_BEGIN -->\n'+body+'<!-- E183_CURRENT_END -->\n',text,count=1,flags=re.S);p.write_text(text)
 assert p.read_bytes().endswith((R/'source_before'/name).read_bytes()),name
history=REPO/'experiment_history/183_gt10_residual_comprehensive_v1.md'
(R/'source_before/history183_pre_closeout.md').write_bytes(history.read_bytes())
history.write_text(f'''# E183：GT10与残差的七数据集及失败查询综合评测

2026-10-17，用户授权范围完成。交付[32页详细中文PDF](../{D}/{pdf})及[报告](../{D}/report_zh.md)。本轮目的为分别评价GT10入口方案和固定入口后的残差增量，覆盖非多模态数据、失败查询和完整Recall–QPS。

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

正式suite18267.58秒约5.07h，包含1935内部wall、预热、保存/核验，不能重复加总；主分析139.83秒、独审407.80秒。离线接续suite160.94秒另保留先前Deep教师26.80秒；源SHA330.27秒与GT抽审27.98秒部分重叠。所有构建、阶段与嵌套边界见[费用账本](../{L}/analysis/cost_ledger.json)。复用旧资产的完整冷启动成本未知，不清零；文件大小不冒充精确RSS。

## 局限与结束边界

本轮单图/单画像实例、已曝光公共测试，三轮不是三份质量样本；GIST仅1K，固定16K/K100L200教师跨K共表不证明各K最优，跨数据的metric/规模/维度/容量/训练密度未因果配平。无NSG+残差额外组，只识别在GT10上的增量。单点同L救损、实测跨L点和折线插值分别报告。

[协议](../{L}/protocol.md) · [全645点](../{L}/analysis/final_v1/points.csv) · [1935轮](../{L}/analysis/final_v1/timings.csv) · [独审](../{L}/reviews/independent_results_audit.json) · [边界](../{L}/reviews/boundary_diagnostics.json) · [实际计时输出](../{L}/results/) · [状态](../{L}/state.json)。源、旧报告及delivery_v1保留；delivery_v2只补解读，不改科研结果。最终PDF实际视觉检查收据在delivery_v2/pdf_visual_review.json。

固定矩阵收口，无待恢复队列，默认不变。本轮基底HEAD96cf05d5410cf51272048cd1f90b4bb194e23c62、分支research/state-20261002，未创建提交或发布。
''')
print('root documents closed; old suffixes preserved')
