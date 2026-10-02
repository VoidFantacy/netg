import sys,csv
from pathlib import Path
RUN=Path(__file__).resolve().parents[1];sys.path.insert(0,str(RUN/'src'))
from common import *
assert read(RUN/'reviews/analysis_complete.json')['status']=='PASS' and not (RUN/'report.md').exists()
metrics=list(csv.DictReader((RUN/'results/metrics.csv').open()));pairs=list(csv.DictReader((RUN/'results/paired.csv').open()));exact=list(csv.DictReader((RUN/'results/ANN_vs_exact.csv').open()));routes=list(csv.DictReader((RUN/'results/routing.csv').open()));sums=list(csv.DictReader((RUN/'results/summary_by_K.csv').open()));old=list(csv.DictReader((Path(LOCK['reference_E107'])/'results/metrics.csv').open()))
decomp=[]
for ds in LOCK['datasets']:
 for K in [1,100]:
  for L in LOCK['K_L'][str(K)]:
   def value(rows,name):return float(next(x for x in rows if x['dataset']==ds and x['method']==name and x['K']==str(K) and x['L']==str(L))['recall'])
   au,ap=value(metrics,'UnitHub'),value(metrics,'GT10Default');iu,ip=value(old,'UnitHub3'),value(old,'GT103');parts=[(iu-ip)*100,(au-iu)*100,(ap-ip)*100];assert abs(parts[0]+parts[1]-parts[2]-(au-ap)*100)<1e-10
   decomp.append(dict(dataset=ds,K=K,L=L,exact_Unit_minus_GT10_pp=parts[0],Unit_ANN_minus_exact_pp=parts[1],GT10_ANN_minus_exact_pp=parts[2],observed_Unit_ANN_minus_GT10_ANN_pp=(au-ap)*100))
dump(RUN/'results/quality_decomposition.json',decomp)
lines=['# E108：GT10画像还改变了小图可检索性','',
'2026-09-20，完整54方法点、162轮单线程plain已完成并核验。保留当前GT10原小图，加入同seed重建GT10和单位原hub的小图；同原H、raw query、固定NSG。两集各4096条E105已曝光开发query，K1五L64/128/256/400/800、K100四L128/256/400/800。**单位hub是必要强基线，但没有形成跨两集稳定默认替换。**','',
'Web单位hub的同L召回均值均高于原GT10，小幅速度差与轮次范围重叠；Yandex K100召回均值全低，部分失败query增加，速度总体更低。原默认保持。这不是“简单基线无效”：它说明原GT10画像的精确入口质量并无普遍优势，真实小图的近似和成本会改变最终结论。','',
'## 1. 完整主比较','',
'下表UnitHub相对GT10Default，ΔR为pp，ΔQPS为同L三轮QPS均值比；不表示等Recall加速。Web九点速度范围均重叠；Yandex五点重叠，另四点UnitHub整段范围更慢（K1/L64、128、256，K100/L128）。没有任何点的UnitHub三轮范围整体更快，不以小百分比均值宣布稳定提速。','',
'| 数据 | K | L | ΔRecall pp | 95%配对区间 | Δ平均QPS | 失败query 原→Unit |','|---|---:|---:|---:|---|---:|---|']
for x in pairs:
 if x['baseline']=='GT10Default' and x['method']=='UnitHub':lines.append(f"| {'WebVid' if x['dataset'].startswith('webvid') else 'Yandex'} | {x['K']} | {x['L']} | {float(x['delta_recall_pp']):+.4f} | [{float(x['CI95_low']):+.4f}, {float(x['CI95_high']):+.4f}] | {float(x['delta_mean_qps_pct']):+.2f}% | {x['baseline_failed']}→{x['method_failed']} |")
lines += ['', '按同K全部L平均的query配对质量变化，以及各L吞吐比的几何均值如下；预算相关，平均不是独立重复。','',
'| 数据 | K | 平均ΔR pp（95%区间） | L间QPS比几何均值变化 |','|---|---:|---|---:|']
for x in sums:
 if x['baseline']=='GT10Default' and x['method']=='UnitHub':lines.append(f"| {'WebVid' if x['dataset'].startswith('webvid') else 'Yandex'} | {x['K']} | {float(x['mean_L_delta_recall_pp']):+.4f} [{float(x['CI95_low']):+.4f}, {float(x['CI95_high']):+.4f}] | {float(x['geomean_L_qps_change_pct']):+.2f}% |")
lines += ['', 'Web K100平均质量变化的描述性区间为正；这是一项应保留的开发信号，不把它扩写成跨数据、全召回范围或显著加速。Yandex K100平均−0.0991pp、QPS比几何均值−0.84%，L128失败24→34。','',
'## 2. 可检索性是画像作用的另一部分','',
'这里的“入口成员召回”是ANN取出的3个hub与同表示精确top3的重合数/3，不是三入口集合完全一致比例，也不是最终NSG Recall。','',
'| 数据 | 方法 | 精确top3成员召回 | 完全相同集合 / 4096 | 路由NDC/query |','|---|---|---:|---:|---:|']
for x in routes:lines.append(f"| {'WebVid' if x['dataset'].startswith('webvid') else 'Yandex'} | {x['method']} | {float(x['exact_top3_entry_recall'])*100:.3f}% | {x['same_exact_entry_sets']} | {float(x['route_ndc']):.2f} |")
lines += ['', '单位hub使用相同M/ef仍需要更多路由距离计算，恢复其精确目标集合的比例更低；同seed重建GT10控制与原GT10接近。这个事实支持继续研究表示的可索引性，但单次构建不是构建方差实验，亦未证明query分布匹配是唯一原因。','',
'## 3. 精确入口质量与ANN作用的可核验分解','',
'定义I为各自全H精确入口的真实NSG Recall，A为普通ANN入口的真实Recall，则逐query及均值都有差值恒等式：','',
'`A_Unit − A_GT10 = (I_Unit − I_GT10) + (A_Unit − I_Unit) − (A_GT10 − I_GT10)`','',
'两个ANN项是有符号变化，不能预设为非负损失：有限beam非单调使近似入口有时反而提高最终命中。全部18点恒等式独立核对通过，L128示例如下。','',
'| 数据 | K | 精确Unit−GT10 | Unit ANN−精确 | GT10 ANN−精确 | 实际Unit−GT10 |','|---|---:|---:|---:|---:|---:|']
for x in decomp:
 if x['L']==128:lines.append(f"| {'WebVid' if x['dataset'].startswith('webvid') else 'Yandex'} | {x['K']} | {x['exact_Unit_minus_GT10_pp']:+.4f} | {x['Unit_ANN_minus_exact_pp']:+.4f} | {x['GT10_ANN_minus_exact_pp']:+.4f} | {x['observed_Unit_ANN_minus_GT10_ANN_pp']:+.4f} |")
lines += ['', '因此“GT10为何有效”至少要分为原H上的query自适应入口、精确表示的动作质量、该表示下的小图检索误差及成本、原NSG有限beam反馈。画像优化只追逐几何或训练loss，可能改变其中一个环节，却破坏其他环节。上述分解是可观测差值恒等式，不是已经完成的唯一因果解释或性能保证。','',
'## 4. 同seed控制与当前判断','',
'GT10Rebuilt相对原图的平均L质量变化，Web R1/R100为+0.1074/+0.0284pp，Yandex +0.0195/+0.0023pp；四个描述性区间均跨0。UnitHub相对重建GT10的结论同样是Web小幅质量正值、Yandex K100负值，全部点保留在paired.csv。没有在多个seed中选最好的图，也不追加ef/seed/预算。','',
'本阶段完成强基线补全，默认Web soft/Yandex hard与生产E99保持；E103仍是最新完整五集前沿，本矩阵未覆盖所有90/95/99%召回目标。新方法应同时解释代理、精确动作、小图可检索性和完整wall。下一阶段已锁定真实目标信息的fit代理门，先看完美代理本身能否超过GT10与单位hub，再决定是否有依据学习它。','',
'## 5. 验证与成本','']
search=read(RUN/'reviews/search_complete.json');graphs=read(RUN/'reviews/graphs_built.json');analysis=read(RUN/'reviews/analysis_complete.json')
lines += [f"真实NSG {search['NSG_calls']:,}次，在线路由{search['router_calls']:,}次；四个小图构建加验证{sum(x['seconds'] for x in graphs['graphs']):.3f}秒，总搜索编排{search['seconds']:.2f}秒，分析{analysis['seconds']:.2f}秒。0新GT/底图/梯度训练/K10。CPU15/实际线程1，方法和数据集串行；完整warm/plain/count一致、链接E99 smoke、GT10Default全量E105输出/入口/route及graph NDC恢复通过。",'',
'54点独立评分、同L K1/K100首返回与NDC、同入口跨方法返回/距离bits、E107 exact对齐检查通过。原source/输入/模型/图和四新图身份封存，两张PNG已实际查看、PDF同源导出。阶段状态COMPLETE_UNIT_HUB_ONLINE_NO_DEFAULT_CHANGE；16:00目标继续。','',
'[Recall–QPS图](figures/recall_qps.png) · [同L吞吐差](figures/same_L_qps.png) · [协议](protocol.md) · [解释口径](reviews/interpretation_notes.md) · [指标](results/metrics.csv) · [完整配对](results/paired.csv) · [ANN与精确](results/ANN_vs_exact.csv) · [代数分解](results/quality_decomposition.json) · [全部计时](results/timing.csv) · [验收](reviews/completion_audit.json)。']
(RUN/'report.md').write_text('\n'.join(lines)+'\n');dump(RUN/'reviews/report_source.json',dict(source=identity(Path(__file__)),report=identity(RUN/'report.md')));print('REPORT_WRITTEN')
