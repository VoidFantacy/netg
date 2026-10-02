from common import *

assert (O/'report.md').exists() and not (O/'reviews/docs_updated.json').exists()
a=read(O/'results/analysis.json');key=read(O/'results/report_key_results.json');rel='entry_method_exploration/20260911_hnsw_rl_benchmark_v1'
for p in [R/'experiment_history/README.md']:
 dest=O/'source_before'/'history_README.md';assert not dest.exists();shutil.copy2(p,dest)
def signed(x,d=3):return f'{x:+.{d}f}'
table=['| 数据集 | L | ΔRecall pp | ΔQPS % | 原图→RL失败数 |','|---|---:|---:|---:|---:|']
for p in key['direct_baseline_comparisons']:
 ds='WebVid' if p['dataset']==DS[0] else 'Yandex-IP'
 table.append(f"| {ds} | {p['L']} | {signed(p['recall_delta_pp'])} | {signed(p['qps_change_pct'],2)} | {p['baseline_failed']}→{p['rl_failed']} |")
table='\n'.join(table)
card=f'''# 23 冻结HNSW-RL图的性能补测（E34）

2026-09-11完成，状态`COMPLETE_FROZEN_RL_BENCHMARK`。用户在E33开发门停止后明确要求比较QPS、Recall、查询失败率并画图，因此独立授权本次性能补测。E33原协议、训练、开发门和零QPS记录保留，没有重新选择模型或重启训练。

## 方法、输入与计量

冻结E33 cal选定物理图：WebVid seed20260912/step400，Yandex seed20260911/step300；只改Micro-HNSW底层已有边，原画像/ID/上层及NSG不变。对照NSG原固定入口、原Fast30K、GT10-hard；WebVid额外GT10-soft-t1，它才是该RL图的直接起点。Fast30K的训练量与构图seed不同于20K GT10，不能把两者差异全部解释为GT1→GT10。

原历史validation2000/集、L64/128/256/400/800、K10/raw-IP；WebVid25点、Yandex20点。CPU15及进程/OMP/BLAS/MKL均1线程，两集串行；每点一次完整warmup、五轮轮换独立plain整批wall，QPS取中位数并显示min/max。GT、计数、hash、I/O和加载在timer外。复用E33无训练hook的binary，加载冻结图，没有新构建/优化或held-out访问。

失败严格为Recall@10<0.1即零GT10命中，不是运行异常。保存query-ID对齐的结果，统计相对每个基线的挽救、新增失败、仍失败以及Recall/QPS/失败率变化。

## 相对直接起点的完整结果

WebVid起点GT10-soft-t1，Yandex起点GT10-hard；ΔRecall为绝对百分点，ΔQPS为五轮中位数相对变化。

{table}

{' '.join(key['summary_sentences'])}

相对NSG/Fast/FastGT10-hard的全部35项配对比较，以及原45点、225轮wall，均见报告/CSV。Recall–QPS图保留全部实测点；同Recall分析只在各自非支配曲线共同区间作明确标记的log-QPS插值，无外推/新选点。不能用某个更快点或路由NDC直接推导整条曲线改进。

## 验收、成本和解释边界

90000保存输出独立GT复算，70000旧基线输出的ID/距离bits/入口/hits/mask/路由和NSG NDC回归E30通过。五轮/plain/count/每点16条原kernel结果一致，同方法跨五L图与入口一致，失败挽救−新增=基线失败−RL失败。实际NSG630720，修复0；新增训练/标签/GT生成0。查询进程耗时含加载和验收，不当作QPS；完整既有训练成本见[历史22](22_hnsw_edge_rl.md)。

两组validation有反复历史使用，2000条中一条失败对应0.05pp；bootstrap区间未校正多重比较，五轮计时不是新Recall样本。只测一份预选RL图，没有跨seed性能复现，学习相对随机的归因仍保留E33控制证据。本轮不自动替换默认，也不否定尚未测试的坐标训练/加边/重连。

独立版本前后SHA保护E33完整目录及实际依赖，原大图/向量/模型/标签/结果不改。历史validation本轮已明确授权读取及计时；held-out未读/hash。新增图PNG/SVG/PDF及Excel，最终验收和冻结身份保存。

- [完整报告](../{rel}/report.md)、[协议](../{rel}/protocol.md)、[状态](../{rel}/state.json)、[调用账](../{rel}/logs/jobs.json)。
- [Recall–QPS](../{rel}/figures/recall_qps.svg)、[三指标曲线](../{rel}/figures/metrics_by_search_L.svg)、[相对变化](../{rel}/figures/rl_changes.svg)、[Excel](../{rel}/chart_data.xlsx)。
- [输出验收](../{rel}/reviews/output_verification.json)、[最终验收](../{rel}/reviews/final_audit.json)、[评测控制器](../{rel}/src/run.py)、[独立分析](../{rel}/src/analyze.py)。

本轮预算收口，无排队训练/ANN任务；研究接续见根[s-target](../s-target.md)。
'''
(R/'experiment_history/23_hnsw_rl_benchmark.md').write_text(card)
p=R/'experiment_history/README.md';s=p.read_text();needle='\n\n## 写入规则';assert needle in s;s=s.replace(needle,'\n| [23 HNSW-RL性能补测](23_hnsw_rl_benchmark.md) | E34：用户另授权冻结RL/NSG/Fast/GT10五L，45点225轮单线程wall、Recall与零命中失败率 |'+needle);p.write_text(s)
p=R/'s-experiment.md';s=p.read_text();needle='| E33 ';idx=s.index(needle);s=s[:idx]+f'| E34 冻结RL图性能补测 | 用户另授权原NSG/Fast30K/GT10-hard及RL，WebVid另起点GT10-soft；45点225轮单线程wall与失败率 | `COMPLETE_FROZEN_RL_BENCHMARK`；全量结果保留，90000输出复核，未重训/改选/替换默认 | [23 HNSW-RL性能](experiment_history/23_hnsw_rl_benchmark.md) |\n'+s[idx:]
s=s.replace('当前最近完成实验已为E33','当前最近完成实验已为E34').replace('二十二份详细卡片','二十三份详细卡片');p.write_text(s)
(R/'summary.md').write_text(f'''# ACSG 当前实验总结

2026-09-11。最近完成E34，状态`COMPLETE_FROZEN_RL_BENCHMARK`。[完整报告]({rel}/report.md)、[历史23](experiment_history/23_hnsw_rl_benchmark.md)、[状态]({rel}/state.json)。

## 本轮完成

用户另行要求比较QPS、Recall及失败率，已对E33冻结RL图和NSG、原Fast30K、FastGT10-hard重新同机测量；WebVid另列RL起点GT10-soft-t1。双集各历史validation2000、五L，共45方法点、225轮独立整批wall，CPU15/实际进程与数值库均1线程。没有新训练或seed/checkpoint选择；E33开发停止及原零QPS记录保留。

失败严格为Recall@10<0.1（零命中），与程序异常分开。QPS取五轮中位数并保留min/max；原始query路由、映射、NSG、输出均计时，GT/count/I/O/load/hash在timer外。

## RL相对其直接起点

WebVid为GT10-soft-t1，Yandex为GT10-hard；不能把RL相对NSG或Fast的全部差异归因强化学习。下表保留全部五L正负点。

{table}

{' '.join(key['summary_sentences'])}

所有基线的原45点、35项配对挽救/新增失败和同Recall描述性插值见报告。历史validation反复使用、每集仅2000、单份预选RL图；小速度差及未校正bootstrap不足以自动建立稳定替换结论。当前默认仍为WebVid原GT10-soft-t1/Yandex原GT10-hard；E33相对随机未建立稳定增量的边界保留。

## 图表与验收

[Recall–QPS]({rel}/figures/recall_qps.svg) · [QPS/Recall/失败率随L]({rel}/figures/metrics_by_search_L.svg) · [RL相对各基线变化]({rel}/figures/rl_changes.svg) · [Excel]({rel}/chart_data.xlsx)。PNG/PDF、原值CSV及aligned结果齐备。

全部90000输出独立GT复算、70000旧基线输出逐位回归E30；五轮/plain/count/原kernel、五L图/入口一致与失败配对恒等式通过。实际NSG630720，修复0；新训练/GT生成0，旧E33完整目录及实际依赖SHA保护。held-out未读/hash。[最终验收]({rel}/reviews/final_audit.json)。

E33已完成真实轨迹REINFORCE边训练（4×600步、307200新反馈）；开发WebVid局部信号/Yandex失败，与本次新增性能数据分别保留。[E33报告](entry_method_exploration/20260911_hnsw_edge_rl_v1/report.md)、[历史22](experiment_history/22_hnsw_edge_rl.md)。预算均已收口，无排队任务，下一阶段见[s-target](s-target.md)。
''')
p=R/'s-target.md';s=p.read_text();start=s.index('## 当前判断与保留信号');s='# ACSG 下一阶段方向与实验接续\n\n'+f'2026-09-11。E34冻结RL图性能补测已完成，状态`COMPLETE_FROZEN_RL_BENCHMARK`。[报告]({rel}/report.md)、[历史23](experiment_history/23_hnsw_rl_benchmark.md)。用户新增QPS/Recall/失败率请求已完成；45点225轮wall，无新训练/改选模型，无排队任务。E33开发门停止原件保留。\n\n'+s[start:]
needle='## 优先一：';idx=s.index(needle);s=s[:idx]+f'本轮新增E34实测曲线：'+ ' '.join(key['summary_sentences'])+f' 全部失败率、同L配对及共同Recall区间估计见[数据表]({rel}/results/paired_changes.csv)。后续判断须同时保留E33开发/随机对照与E34独立wall结果，不能再把当前RL图说成完全没有性能测量。\n\n'+s[idx:]
a0=s.index('## 优先三：');a1=s.index('## 接续要求',a0)
s=s[:a0]+f'''## 优先三：已有性能证据与后续复现边界

E34已按用户新增授权完成原图/冻结RL/NSG/Fast/GT10的同机单线程五L曲线与零命中失败率；这次补测不表示E33原开发门通过。先读[全部曲线]({rel}/report.md)，区分相对NSG/Fast、相对GT10-hard，以及相对RL真正起点的增量。保持完整端到端wall，不用路由NDC换算QPS。

如以后需要稳定方法结论，另锁定跨seed/独立查询的复现范围和资源预算；现有历史validation不能重新称盲测，也不能据本次曲线继续选模型或调阈值。新协议应保留学习与简单随机/几何控制、共同Recall区间、计时轮换与全部正负点。当前没有自动授权训练或held-out任务。

'''+s[a1:]
s=s.replace('再进入[历史22]','先进入[历史23](experiment_history/23_hnsw_rl_benchmark.md)及本轮性能原件，再进入[历史22]')
s=s.replace('当前方向均未自动追加训练/ANN/validation','E34仅完成本次已授权性能补测；当前方向均未自动追加训练/ANN/validation');p.write_text(s)
p=R/'spec.md';s=p.read_text().replace('（E33真实轨迹HNSW底层边RL、静态图导出与开发验收已实现；原Fast/NSG kernel不变）','（E34冻结RL图五L/五轮端到端wall与失败率补测已验收；原Fast/NSG kernel不变）')
s+=f'''

## 冻结HNSW-RL图性能补测（E34，2026-09-11）

独立[协议]({rel}/protocol.md)承接用户新增QPS/Recall/失败率授权，E33原开发门和零QPS状态保留。[prepare.py]({rel}/src/prepare.py)逐字复制E33无hook评测binary、冻结E33已选图和已有基线小图、核对历史validation2000输入及模型身份；没有新画像/图训练或按validation选模型。

[run.py]({rel}/src/run.py)配置NSG/Fast30K/GT10-hard/RL，WebVid另GT10-soft起点，五L合计45点。正式wall接口此前未执行，本轮已完成225次：一次完整warmup后五轮按数据集/repeat/L轮换的独立plain整批wall；完整路由/映射/原NSG/输出在timer内，GT/count/hash/I/O/load在外。CPU15、实际进程及OMP/BLAS/MKL1，方法与数据集串行，失败完整预留不释放。接口调用量为每点(5+2)N+16；总630720，修复0。

[analyze.py]({rel}/src/analyze.py)独立复核90000输出的GT10 hits/mask/失败率、两项NDC和QPS=2000/wall；NSG/Fast/GT10共70000旧输出ID/距离bits/入口/hits/mask/NDC逐位回归E30。相同方法五L序列化图及入口保持，五轮/plain/count/reference一致。失败严格hits=0，配对挽救−新增失败=原失败−RL失败；query bootstrap区间与五轮QPS范围分开。

该版本新增实测原值/配对CSV、共同Recall区间内明确标注的非支配曲线log-QPS插值、PNG/SVG/PDF和Excel，不改变原Policy/kernel/metric或默认模型。历史validation已有反复使用，held-out未读/hash。图/模型/query/GT/NSG/计时或L变化需重新评测；不能跨旧轮次拼接QPS。结果见[summary](summary.md)/[历史23](experiment_history/23_hnsw_rl_benchmark.md)，完整验收见[final_audit]({rel}/reviews/final_audit.json)。
''';p.write_text(s)
dump(O/'reviews/docs_updated.json',dict(status='UPDATED_PENDING_FINAL_REVIEW',root_documents=['summary.md','spec.md','s-target.md','s-experiment.md'],new_history='23_hnsw_rl_benchmark.md',E33_unchanged=True))
print('DOCS_UPDATED',flush=True)
