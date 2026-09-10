"""Synchronize current conclusions, implementation contract, next directions and history."""
from common import DATASETS, ROOT, RUN, read

prefix='entry_method_exploration/20260910_gt_topk_profiles_v1'
s=read(RUN/'results/summary.json');cost=read(RUN/'results/costs.json')
short={DATASETS[0]:'WebVid',DATASETS[1]:'Yandex-IP'}


def main_table():
    lines=['| 数据集 / cal冻结主候选 | L | ΔRecall pp | ΔQPS % |','|---|---:|---:|---:|']
    for ds,family in s['primary_families'].items():
        for c in s['comparisons']:
            if c['dataset']==ds and c['stage']=='validation' and c['family']==family and c['baseline']=='gt1_hard':
                name='GT10软' if family=='gt10_soft' else 'GT10硬'
                lines.append(f"| {short[ds]} / {name} | {c['L']} | {c['delta_recall_pp']:+.3f} | {c['qps_change_percent']:+.2f} |")
    return '\n'.join(lines)


history=f'''# 13｜固定 H 的 GT1/GT10 × 硬/软画像

2026-09-10，E24。状态`EXPLORATORY_LOCAL_FRONTIER_SIGNAL_NO_FORMAL_GO`。用户在四问题调研和详细交接后明确授权第一方向逐阶段执行；P0输入/协议、P1恢复、P2 cal/audit、P3 validation均完成，本版本收口。原只读调研和文档交接保留未执行原件身份，实际继任实验记于本卡。

## 问题、方法与固定项

检验GT1归属丢失多目标信息及硬分组支持不足，能否通过闭式画像在相同H、相同三个入口、相同路由模型规模下改善真实NSG Recall–QPS。与旧GT1 basin内增加modes、多seed/view、single获胜者centroid和E23真实三入口排序不同；本次只改变GT目标归属。

原WebVid2.5M/official Yandex first10M raw-IP、NSG及QGT seed20260828 H815/821固定。fit为router_train[10000,30000)，cal[0,1024)，audit[1024,2048)；GT100宽度/字节数/行身份与原文件核对。target–hub仍为cosine，query方向累加，每query总质量1，GT1/GT10等权，raw-hub prior1。硬归属ties按真实ID，softmax在全部H稳定计算；最终一单位画像对应一个真实ID。

每数据集8份：GT1硬、GT10硬、GT1/GT10软各3温度。T为fit GT1最高/次高hub cosine差中位数×0.25/1/4；WebVid约0.00405/0.01620/0.06480，Yandex0.01089/0.04357/0.17430。GT1硬保留原float32累加，其他加权累加float64后导出float32；不重跑single/triple标签、不训练Full/rank、不改H、vMF、MLP或HNSW几何。

## 恢复、开发选择和数据访问

GT1硬与E23 paired P0逐位相同。fit32旧/新P0×exact/HNSW的ID、距离bits、入口、命中/mask及NDC全部一致，也与E23历史相同行输出回归通过。两数据集全部8份画像先冻结，再在cal1024 L128评估exact/HNSW各一份。模型按HNSW总hits、graph NDC和冻结ties选择，QPS/exact结果不用于选参。

WebVid cal选GT10软T0.0162011（+0.8203pp），Yandex选GT10硬（+0.0488pp）；均通过至少1个额外总命中的弱探索进入门。audit分别+0.5859/−0.0781pp，只报告，不换模型。另每软族保留其cal赢家：WebVid GT1软T0.0648046，Yandex两软族均T0.0108935。两软族在WebVid最终温度不同，因此是校准后画像族比较，不是同T的纯交互项估计。

双数据集选择/画像/binary冻结后，历史validation前2K、L64/128/256/400/800、NSG/Fast30K/Fast20K/GT10硬/GT1软/GT10软共60点全部执行。fit/cal/audit及validation均有历史使用，不能称新盲测；本轮held-out文件未打开。

## 五点主结果及消融

下表相对同批matched Fast20K-3；每点单线程、独立plain wall一次。

{main_table()}

主候选两数据集各3/5点同时提高Recall与QPS；各自五新点均位于与Fast20K五点合并的观测非支配集合，另外点含质量/速度交换，不能称整条新曲线支配旧曲线。9/10项主候选Recall差的未校正95%配对bootstrap跨0，Yandex L128下界也仅约+0.010pp。

GT10硬在Yandex五L Recall均小幅正值，但在WebVid L128/256/400为−0.085/−0.115/−0.110pp；不是统一多目标修复。WebVid GT1软L64为+0.740pp，L800为−0.050pp；软归属不保证更好。GT10软/硬互有高低，不能按validation把主选择切成更好看的消融。

L128零命中，WebVid Fast20K→主候选54→51（挽救15/新增失败12），Yandex38→32（10/4）。各自83.75%/63.65%的validation query更换三入口，入口跨L一致。原Fast30K独立列出：WebVid主候选相对原Fast30K的+0.200pp包含Fast20K输入差异；Yandex主候选L128 QPS仍略低于原Fast30K。

## 支持、近似检索与计时解释

WebVid GT1硬有802/815个画像有query质量，中位ESS16；GT10硬覆盖全部、ESS67.36，主候选GT10软ESS132.28。支持变充分未保住validation L128收益；高T还可能使query权重近乎广泛摊薄。Yandex GT10硬ESS22→60.08。

audit主候选exact3−HNSW3最终Recall为WebVid+0.146pp、Yandex−0.020pp，ANN top3集合覆盖约94.24%/97.85%。精确画像检索不是finite-L入口效用oracle。L128 Fast20K route-only约7.166/4.535μs/query，主候选6.521/4.391μs；该量级仅约独立端到端wall的1%，分项wall不能相加作总wall。Yandex主候选graph NDC微增而QPS较高，不能把全部速度差归为更少距离计算。

## 成本、验收和收口

真实调用543296（恢复768、cal99328、audit33280、validation含分项409920），正常预算完全执行，修复预留8192未用；另1500次合成fixture调用。训练标注0，不依赖E22全H single或E23 triple训练标签。

输入核对/准备22.41s；两数据集GT1硬恢复核心0.447s；其余候选构建阶段合计15.30s。搜索子进程恢复16.63s、cal70.52s、audit34.26s、validation484.65s，含加载/建图/验收/计数/I/O，不能换算查询QPS。已有exact GT、QGT和NSG从零成本未新测，null+reason。观测峰值RSS约9.920GiB，全部查询进程实际1线程、CPU15。

全部116点、169408个输出独立GT10重评分通过；NSG/Fast30K/Fast20K三基线30点60000输出与E23逐位相同。五L图/入口一致，选择独立重算通过；63个绑定上游文件和全部冻结画像/选择/二进制已核验。原资产和修改前文档保留。

局部前沿信号不升级为正式GO：一个构建、validation2K、单次wall、历史使用及cosine丢失raw-IP范数仍是限制。此版本结束，不扩温度/GT数、不看held-out、不恢复旧大实验/C。下一研究建议为固定H的真实finite-L效用分组2A，保留本轮冻结画像；不是已自动启动的新阶段。

## 原始证据

- [完整报告](../{prefix}/report.md)、[协议](../{prefix}/protocol.md)、[冻结配置](../{prefix}/config.locked.json)、[状态](../{prefix}/state.json)、[实际命令](../{prefix}/commands.md)。
- [全部原值](../{prefix}/results/tables.md)、[指标CSV](../{prefix}/results/metrics.csv)、[配对变化](../{prefix}/results/comparisons.csv)、[Recall–QPS](../{prefix}/figures/recall_qps.svg)、[差值图](../{prefix}/figures/deltas.svg)。
- [近似检索](../{prefix}/results/ann_diagnostics.csv)、[支持统计](../{prefix}/results/profile_support.csv)、[前沿实测点](../{prefix}/results/frontier_points.csv)、[明确标记的插值](../{prefix}/results/frontier_interpolation.csv)、[成本账](../{prefix}/results/costs.json)。
- [输入](../{prefix}/inputs/preflight.json)、[恢复](../{prefix}/reviews/recovery_gate.json)、[cal门](../{prefix}/reviews/cal_gate.json)、[validation前冻结](../{prefix}/models/frozen_before_validation.json)、[输出核验](../{prefix}/reviews/result_verification.json)、[保护与选择审计](../{prefix}/reviews/immutable_integrity.json)。
'''
(ROOT/'experiment_history/13_gt_topk_profiles.md').write_text(history)

index=(ROOT/'s-experiment.md').read_text()
row=f'| E24 固定H的GT-topK硬/软画像 | fit GT闭式构建GT1/GT10×硬/软，双数据集各8候选；cal选/audit报、validation2K×五L×六方法，单线程60点完成 | `EXPLORATORY_LOCAL_FRONTIER_SIGNAL_NO_FORMAL_GO`；两主候选各3/5点同时提高Recall/QPS，存在负点及开发波动，软并非普遍更好；本版本收口 | [13 GT-topK画像](experiment_history/13_gt_topk_profiles.md) |\n'
index=index.replace('| E23 真实三入口收益排序 |',row+'| E23 真实三入口收益排序 |',1)
index=index.replace('当前最近实验为E23，研究接续以','当前最近实验已为E24，研究接续以')
index=index.replace('当前根四文件、十二份详细卡片','当前根四文件、十三份详细卡片')
index=index.replace('运行协议待锁定，没有新增方法实验；不回写研究原件状态',
    '该交接原件当时未执行；用户随后授权第一方向E24，已冻结并完成，见历史13；不回写研究原件状态')
(ROOT/'s-experiment.md').write_text(index)
readme=(ROOT/'experiment_history/README.md').read_text()
readme=readme.replace('\n## 写入规则', '\n| [13 GT-topK硬/软画像](13_gt_topk_profiles.md) | E24：固定H、fit GT闭式画像、恢复与cal/audit、单线程validation60点；局部前沿信号，无正式GO |\n\n## 写入规则')
(ROOT/'experiment_history/README.md').write_text(readme)

summary=f'''# ACSG 当前实验总结

> 更新至2026-09-10。最近完成E24固定H的GT1/GT10×硬/软画像。实现见[spec.md](spec.md)，下一方向见[s-target.md](s-target.md)，历史见[s-experiment.md](s-experiment.md)。

## 当前总体结论

**E24已完成并收口：有低成本的局部Recall–QPS正信号，尚未得到跨数据集、全部预算都稳定更优的统一画像。GT10值得保留，软归属并非普遍更好。** 状态`EXPLORATORY_LOCAL_FRONTIER_SIGNAL_NO_FORMAL_GO`。

cal冻结主候选为WebVid GT10软T=0.0162011385、Yandex GT10硬。两数据集各validation2000、一个QGT构建、L64/128/256/400/800，NSG/原Fast30K-3/matched Fast20K-3/GT10硬/GT1软/GT10软共60点全部完成；每点单线程独立plain wall一次。两主候选各3/5点同时提高Recall和实测QPS，另外点有交换；不存在整条新曲线稳定支配旧Fast的证据。

## 相对matched Fast20K-3的全部主候选点

{main_table()}

WebVid L128的cal/audit原先+0.820/+0.586pp，validation却−0.070pp；Yandex cal+0.049pp、audit−0.078pp，validation五点小正值。主候选10项配对Recall差中9项未校正95% query bootstrap区间跨0，Yandex L128下界也仅约+0.010pp；不能据单次wall的小百分比变化宣称稳定加速。

L128实值：WebVid Fast20K 74.260%/1938.54QPS→主候选74.190%/1968.53；Yandex89.720%/1873.77→90.055%/1921.79。零命中分别54→51和38→32，同时仍有12/4个新增失败query。原Fast30K保持独立口径；其Yandex L128为89.830%/1934.67QPS，新主候选并未在两指标同时超过原Fast30K。

## 消融与成本解释

- GT10硬在Yandex五L Recall均小幅正值，在WebVid L128/256/400却下降0.085/0.115/0.110pp。不能把增加GT目标当作统一修复。
- WebVid GT1软L64为+0.740pp，L800为−0.050pp；GT10软相对GT10硬互有高低。validation未用于重新选族或温度。
- WebVid有query支持的画像802→815，GT10软主候选中位ESS16→132.28，但支持变充分没有保证validation L128收益。高T广泛摊薄权重不等于高信息支持。
- audit主候选exact3−HNSW最终Recall为+0.146/−0.020pp；exact画像选择不是实际入口效用oracle。L128 Fast20K路由单测约7.166/4.535μs/query，仅约独立端到端wall的1%；分项wall不相加作为QPS。
- 输入准备/核对22.41s；GT1硬恢复核心合计0.447s，其余七候选/数据集构建阶段合计15.30s。cal/audit/validation搜索子进程70.52/34.26/484.65s，含加载/建图/计数等，不能称查询wall。exact GT/QGT/原NSG从零成本未新测。

## 实际范围与验收

原base、raw-IP、NSG、QGT seed20260828及H815/821固定，三个互异真实ID；matched方法均M16/efConstruction200/ef10、seed20260828、升序消费，原Fast30K保留seed100/heap顺序。GT仅用于fit构建画像和搜索后评分；fit20K、cal/audit各1024，选择和全部画像冻结后才读取历史validation2K。held-out未打开。

GT1硬画像逐位恢复P0，真实搜索恢复通过。每数据集8候选，共16份闭式画像，无single/triple训练标签、Full/rank8训练或其它变量。实际543296次原NSG调用，修复预留0，另1500次合成fixture调用。116点169408输出独立GT10评分通过，三基线60000个validation输出与E23逐位相同；各画像五L的HNSW图及query入口一致。所有查询进程实际线程数1、CPU15，63个绑定上游文件及冻结资产检查通过。

## 权威证据与接续

- [E24复盘](experiment_history/13_gt_topk_profiles.md)、[完整报告]({prefix}/report.md)、[全部原值]({prefix}/results/tables.md)、[Recall–QPS]({prefix}/figures/recall_qps.svg)、[差值图]({prefix}/figures/deltas.svg)。
- [结果JSON]({prefix}/results/summary.json)、[配对CSV]({prefix}/results/comparisons.csv)、[成本]({prefix}/results/costs.json)、[输出核验]({prefix}/reviews/result_verification.json)、[保护审计]({prefix}/reviews/immutable_integrity.json)。

一个构建、validation2K、单次wall、历史开发/验证访问及cosine归属的raw-IP范数缺口限制结论。E24已收口，不扩网格、不按validation换主候选；若继续，建议固定H的真实finite-L效用分组2A，保留本轮冻结画像作为对照，待用户明确下一分支。全部其它方案仍保留在s-target，不自动串行执行。

E23保留[真实三入口排序的小Recall信号、无明确整体QPS优势](experiment_history/12_three_entry_rank_exploration.md)历史身份；E22旧大矩阵和C保持停止。所有旧源码、图、GT、标签、模型和结果保留。
'''
(ROOT/'summary.md').write_text(summary)

spec=(ROOT/'spec.md').read_text()
spec=spec.replace('（独立三入口排序模块已完成双数据集五点单线程探索验收）',
    '（固定H的GT-topK画像模块及双数据集60点单线程比较已完成验收）',1)
spec+=f'''
## 固定 H 的 GT-topK画像 v1（2026-09-10）

独立[E24版本]({prefix}/protocol.md)实现从fit exact GT闭式构建GT1/GT10×硬/软画像，不修改原Fast builder或原ACSG。原Fast链仍为第2节；该画像分支是额外的独立实现，不表示所有新画像性能通过。

- [initialize.py]({prefix}/src/initialize.py)：核验原base/图/训练query/GT hash、H真实ID与raw向量、E23 fit/cal原行及GT100列宽；不运行旧prepare_fit的single提议/训练标签路径。仅用fit GT1 cosine最高/次高间隔确定T尺度。
- [build_profiles.py]({prefix}/src/build_profiles.py)接口`recover|candidates`。先以原builder float32逐位恢复GT1硬，真实搜索恢复PASS后才允许其它候选。每GT目标对全部H作cosine硬argmax（ties升序真实ID）或stable softmax，K_gt名次等权平均，a每query总质量1；p=unit(unit(raw_hub)+sum a*unit(query))。其它加权累加float64，导出float32。K_gt与Recall@10的K分别命名；无新的归一化预处理/正式metric变更。
- 每数据集8份画像，T表在cal前锁定；fit query/GT/目标/hub不接受cal/audit/validation样本。manifest保存W/hash、K_gt/T、支持质量/ESS/熵、画像变化和成本。GT1硬保留dense归属，后续候选保留完整支持统计和float64归属矩阵digest，可按fit重算以控制存储；无梯度/搜索训练标签依赖。
- [evaluate.cpp]({prefix}/src/evaluate.cpp)复用E23 GT-free Policy与原kernel，支持原NSG、HNSW direct3、exact3；matched统一真实ID升序，原Fast30K保留legacy seed100/heap。新版本增加/proc进程线程数及冻结CPU affinity检查、启动前预计调用cap、实际调用记账、policy构建/加载时间，以及协议内L128独立route-only/graph-only warmup和wall；不得相加代替独立端到端wall。
- [jobs.py]({prefix}/src/jobs.py)逐job预留完整调用、拒绝已有输出，强制OMP/OpenBLAS/MKL1和taskset CPU15，记录actual team/process threads、RSS、时间/磁盘上限。正常调用543296、仅身份/parity修复预留8192；失败job按预留全额记账，不能通过重启规避上限。
- [run_development.py]({prefix}/src/run_development.py)只按cal HNSW hits、graph NDC和固定ties选族/T，exact和QPS不参与选择；audit只有冻结候选。两数据集cal主候选均严格胜Fast才能进入validation。[run_validation.py]({prefix}/src/run_validation.py)先验证并写入冻结文件，再核对/复制历史validation前2K，六方法五L、原值全保留。
- [analyze.py]({prefix}/src/analyze.py)独立评分所有返回ID/mask/NDC、三入口及row alignment；query bootstrap仅描述，不使用timing轮作Recall样本。[frontier.py]({prefix}/src/frontier.py)仅处理实测非支配点和明确标记的事后插值，无新搜索或模型选择。

实际GT1硬恢复逐位通过；全部116点169408输出独立评分，三条基线60000个validation输出E23逐位回归、各画像五L相同图与入口、单线程/预算/冻结身份检查均已通过。模型选择只用cal，audit/validation均有历史使用披露，held-out未读取。结果与方法判断见summary及[E24报告]({prefix}/report.md)；实现验收不升级为性能GO。
'''
(ROOT/'spec.md').write_text(spec)

target=(ROOT/'s-target.md').read_text()
tail='## 4. 全部实验方向'+target.split('## 4. 全部实验方向',1)[1]
tail=tail.split('## 6. 可复制的新对话启动指令',1)[0]
tail=tail.replace('| 1，当前主线 | 固定H的GT-topK软画像 |', '| 1，E24已完成收口 | 固定H的GT-topK软画像 |')
tail=tail.replace('下面的方案均未执行，也不构成一张自动全部跑完的实验队列。',
    '除第一方向的E24已完成外，下面其它分支尚未执行，也不构成一张自动全部跑完的实验队列。')
tail=tail.replace('默认新对话启动仍先执行第2–3节主线。',
    'E24已经结束；后续按用户明确选择进入2A/3A/聚类/rank等独立分支，不默认复跑第一方向。')
tail=tail.replace('- 当前研究：[四问题报告]',
    f'- 已完成第一方向：[E24完整报告]({prefix}/report.md)、[协议与预算]({prefix}/protocol.md)、[冻结选择]({prefix}/models/frozen_before_validation.json)；全部消融及负点保留。\n- 当前研究：[四问题报告]')
head=f'''# ACSG 下一阶段方向与实验接续

2026-09-10。第一方向E24已完成并收口，状态`EXPLORATORY_LOCAL_FRONTIER_SIGNAL_NO_FORMAL_GO`。原四问题研究与文档交接的未执行身份保存在其原件；本次用户另行授权的实际实验见[E24复盘](experiment_history/13_gt_topk_profiles.md)。**下一步建议优先固定H的真实finite-L效用分组2A；尚未自动启动，仍按用户指定分支另锁协议。** 全部此前讨论方向保留在第4节，不是一张自动执行队列。

## 1. 已完成第一方向给出的判断

固定H的GT1/GT10×硬/软已完成16份画像、cal/audit和双数据集validation2K六方法五L共60点。cal冻结WebVid GT10软T0.0162011385、Yandex GT10硬，两主候选各3/5点同时改善Recall与实测QPS；有局部非支配点扩展，但没有跨数据集全部预算都稳定更好的统一画像。

WebVid cal/audit L128的+0.820/+0.586pp在validation变为−0.070pp；Yandexaudit−0.078pp，validation五L小正值。GT10硬在WebVid中间三L下降；GT1软和GT10软也有负点。支持/ESS增加不保证真实搜索收益，软归属不应默认优于硬归属。完整结果与成本只在[summary](summary.md)/[E24报告]({prefix}/report.md)维护，本文件不追加流水账。

## 2. 本轮冻结资产与继续时的必要对照

- 原base、raw-IP、NSG、QGT seed20260828、H815/821、三个互异真实入口均未变；fit20K、cal/audit1024，历史validation2K；GT1硬逐位恢复P0。全部输入、模型和冻结选择见[E24目录]({prefix}/README.md)。
- 下一独立方法必须保留matched Fast20K、E24按cal冻结的主画像及相关GT10硬/软对照，不能根据validation重新换掉主候选。原Fast30K仍另列输入与seed/顺序差异。
- 本轮没有生成single/triple训练标签，没有训练Full/rank，没有新H/vMF/MLP/拉伸。其它方向不能写成已经执行。原GT/图/标签依赖的复用必须按spec核对，不整段重跑旧E23准备器。
- E24协议内P0–P3全部结束，实际543296真实调用、修复预留0；无待续阶段。原协议与调用上限不能用于另开温度、GT数、seed或参数队列。

## 3. 后续研究建议及进入边界

优先2A的理由是：更丰富的几何分组已经有局部信号，却不能稳定对应有限L入口效用；同时画像近似检索并非明显主要瓶颈。E24 audit主候选exact−HNSW为WebVid+0.146pp/Yandex−0.020pp；L128 Fast20K route-only仅约7.166/4.535μs/query，约为独立端到端wall的1%。不能把路由NDC比例误作wall，也没有依据优先扩大微型图拉伸。

若用户下一次选择2A，应固定H、核对旧single标签身份，只将其作为效用分组/候选提议，真实三入口结果仍由原kernel联合测量；保留旧single赢家centroid及E24画像作为对照，先检查query画像能否表达并在cal保留真实服务关系。不要默认进入2B新H或同时加集合交互、rank、MLP。

若用户改选3A/聚类/rank，按下面对应分支独立建立小协议；一个方向的成本、标签和停止条件不能替另一个方向授权。所有正式查询仍单线程、单方法独立plain wall、全部路由成本计入QPS。任何新validation范围在方法冻结后使用并披露历史，held-out仍不默认打开。

'''
ending=f'''## 6. 新对话启动与分支选择

本轮第一方向已结束，不再使用旧的“启动第一方向”指令重跑；原指令和全部建议范围保存在[E24修改前s-target]({prefix}/source_before/s-target.md)及[锁定协议]({prefix}/protocol.md)。

下一次若明确选择建议的2A，可使用：

```text
工作目录 /data/netg/ACSG。
完整阅读AGENTS.md、summary.md、spec.md、s-target.md、s-experiment.md，
再读E24完整报告、四问题调研以及历史04/05/08/12/13指向的相关原始证据。
推进s-target 4.1的2A：固定现有H，比较GT几何归属与真实finite-L效用分组。
先核对旧标签兼容性、冻结独立小型protocol和调用预算；保留matched Fast20K、
E24按cal冻结画像及旧single赢家centroid对照，不按validation换E24主候选。
GT/标签只在fit构建目标，cal选参数，audit只报告；冻结后按协议小validation评估。
原base/raw-IP/NSG/QGT seed20260828/H及三个真实入口保持不变。
不默认进入2B新H，不同时加rank/MLP/vMF/HNSW拉伸，不恢复旧大实验/C，不打开held-out。
正式查询单线程、单方法独立plain wall，全部路由成本计入QPS；保留旧资产。
达到停止条件保留结果并收口，交付全对照/图/成本局限，同步四份主文档和历史。
```

以上是供未来明确选择2A的指令，不表示本轮已经启动它。其它分支可替换任务段：

| 要启动的方向 | 任务说明 |
|---|---|
| 微型HNSW拉伸 | 按4.2的3A固定matched Fast20K W，比较受限正对角成对变换；先恢复评分/身份，再重建Micro-HNSW并测完整wall，不改NSG。 |
| 聚类替代 | 按4.3先定位支持/单峰问题，固定目标和输出预算，只选一种相关聚类备选；不同时改变H、画像和路由。 |
| rank容量 | 按4.4先明确同一目标，核对兼容标签后比较rank4/8/16/32与Full；cal联合选rank/λ，不扩大其它变量。 |

每次只执行明确指定的分支及其锁定协议；第一方向的局部正信号或结束都不会自动开启这些队列。
'''
(ROOT/'s-target.md').write_text(head+tail+ending)
print('FOUR_ROOT_DOCS_AND_E24_HISTORY_UPDATED',flush=True)
