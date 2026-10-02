from common import *
import re,ast
assert os.sched_getaffinity(0)=={8};resources();assert read(O/'reviews/contract_verification.json')['status']=='PASS';assert read(O/'reviews/output_verification.json')['status']=='PASS'
r=read(O/'results/analysis.json');selection=read(O/'results/cal_selection.json')['selection'];gate=read(O/'results/development_gate.json');jobs=read(O/'logs/jobs.json')
status='COMPLETE_FROZEN_LOCAL_RL_EVALUATION_NO_DUAL_FRONTIER_GAIN'
tab='| 数据集 | cal选定模型 | cal ΔR pp | audit ΔR pp [配对95%区间] | audit gain/loss hits | audit改善/损伤query | audit Δtotal NDC % |\n|---|---|---:|---:|---:|---:|---:|\n'
for ds in DS:
 for arm in ARMS:
  m=selection[ds][arm]['model'];cal=next(x for x in r['points'] if x['dataset']==ds and x['phase']=='cal' and x['model']==m);au=next(x for x in r['points'] if x['dataset']==ds and x['phase']=='audit' and x['model']==m)
  ci=next(x for x in r['paired'] if x['dataset']==ds and x['phase']=='audit' and x['model']==m and x['reference']=='baseline')
  tab+=f'| {"WebVid" if ds==DS[0] else "Yandex"} | {m} | {cal["delta_recall_pp"]:+.4f} | {au["delta_recall_pp"]:+.4f} [{ci["CI_low_pp"]:+.4f},{ci["CI_high_pp"]:+.4f}] | {au["hits_gained"]}/{au["hits_lost"]} | {au["helped"]}/{au["harmed"]} | {au["total_NDC_delta_pct"]:+.4f} |\n'
curve='| 数据集 | 模型 | L | ΔRecall pp | QPS中位数 | ΔQPS % | 失败数/1024 |\n|---|---|---:|---:|---:|---:|---:|\n'
for ds in DS:
 for arm in ARMS:
  name=selection[ds][arm]['model']
  for x in [x for x in r['points'] if x['dataset']==ds and x['phase']=='frontier' and x['model']==name]:
   curve+=f'| {"WebVid" if ds==DS[0] else "Yandex"} | {arm.upper()} | {x["L"]} | {x["delta_recall_pp"]:+.4f} | {x["QPS"]:.2f} | {x["delta_QPS_pct"]:+.3f} | {x["failed_queries"]} |\n'
core='''冻结RL的局部正值只在WebVid部分工作点保留，没有形成双集Recall–QPS改进。WebVid RL在audit L128新增9个命中、无损伤，但L256/400/800各丢4个命中；Yandex选中RL和ES在五L全部没有命中变化。WebVid RL相同Recall的三个描述插值位置为+0.436%、−1.095%、−0.743%，不构成整条曲线提高。五轮QPS小差异方向不一致，不能归为稳定性能优势。

ES的局部结果也保留：WebVid在L64/128/256各新增10命中、无损伤，L400/800相同；L128失败从11降到10。RL L128失败仍11，Yandex所选两模型五L失败与基线完全相同。WebVid的配对Recall区间下界均为0，收益query很少，不能据正均值宣称稳定泛化。E47 monitor没有显示WebVid ES正值，独立开发却有该局部信号，说明不能以某一内部统一门替代所有后续固定模型事实。

预锁可比开发门仍为STOP：两集RL cal +0.0391/+0.0781pp均未到+0.1pp，且Yandex audit为0。保持E47统一训练门原身份，E49也不替换默认。原默认WebVid GT10-soft-t1 / Yandex GT10-hard保留。
'''
next_text='''接着执行已写明的E50原轨迹诊断：固定1600动作前状态/12800已测候选，比较包含不动的原J-best、有限hit-best和实际Adam均值，检查“有正候选而确定更新无质量响应”的比例，0新搜索。若证据支持，再做独立步长/方向反事实或连续有限候选择优提交对照；后者必须明确称贪心局部搜索，不包装成RL，也不能使用旧分岔状态的反馈。

用户已延长到22:00并追加最终比较要求：最后将冻结的最佳候选与NSG、原Fast、FastGT10-hard同批测QPS/Recall/失败率，WebVid另列GT10-soft匹配起点。Fast身份已由历史23和E34原配置核对。E49的WebVid矩阵缺hard基线，不能称已经完成最终要求；最终阶段另冻完整矩阵及模型选择规则。21:15前为最终比较留出窗口，21:40停止新查询，22:00收口。'''
body=f'''# E49 冻结完整反馈局部画像的开发与性能评测

2026-09-12，`{status}`，开发门`{gate['status']}`。0新训练，80个质量/性能点和250轮plain wall完成。

{tab}
{core}
## 完整五L所选候选结果

相对当前GT10起点。全部NSG/Fast/基线原值、所有seed cal/audit及五轮范围见CSV，不仅报告以下所选模型。

{curve}
## 方法与核验

全部E47 selected模型在cal前冻结，fit各128query对train0:64和monitor4096:4160逐位恢复；cal按原平均U、较低total NDC、较小seed选择并冻结，再开启audit，未依audit换seed。两开发池各1024，source IDs与train/monitor5120及彼此不交，但历史研究已使用这些开发数据，不是项目盲测。所有模型仍raw query→一次普通HNSW→三个真实入口→原NSG。

固定五方法×两dataset×五L，原E37同SHA静态binary；CPU15实际进程/OMP/BLAS/MKL1，方法和dataset串行，每点一次warmup和五轮轮换完整plain wall。计时包括路由/映射/原NSG/预分配输出，GT/count/I/O/load/build在外；L128分项独测不代替总wall。GT在所有原始返回产生之后打开评分。失败严格GT10零命中，timing重复不是新质量样本。

实际423680 NSG，8job均完整预留并完成、无失败查询job；累计{sum(x['seconds'] for x in jobs):.3f}s，含加载/输出/核验而非线上wall。独立72960集合评分/命中mask、1280原kernel parity、1280 fit checkpoint位恢复、4096旧基线回归、6144 audit128→curve128位恢复，全部跨L图/入口及五轮/plain/count一致。所有source/model/原E37–E48/native SHA保持。

准备阶段仅一次manifest字段兼容错误：E48冻结清单没有旧helper强制mtime字段，查询前修正为有该字段时检查；bytes/SHA始终检查，0搜索损耗，原记录保留。0新GT/训练/原validation/held-out访问，默认未替换。

## 接续与最终交付

{next_text}

[协议](protocol.md)、[全部点](results/points.csv)、[配对区间](results/paired.csv)、[逐query](results/query_results.csv)、[五轮计时](results/timings.csv)、[描述插值](results/frontier_interpolation.csv)、[原开发门](results/development_gate.json)、[输出核验](reviews/output_verification.json)、[合同核验](reviews/contract_verification.json)、[Recall–QPS](figures/recall_qps.svg)、[相对变化](figures/quality_cost_changes.svg)。
'''
(O/'report.md').write_text(body);(O/'conclusion.md').write_text(core+'\n'+next_text+'\n')
hist=body.replace('# E49 冻结完整反馈局部画像的开发与性能评测','# 38. E49 冻结局部画像开发与性能');hist=re.sub(r'\]\(([^)]+)\)',lambda m:'](../entry_method_exploration/20260912_frozen_local_rl_evaluation_v1/'+m.group(1)+')',hist);(R/'experiment_history/38_frozen_local_rl_evaluation.md').write_text(hist)
p=R/'s-experiment.md';s=p.read_text();i=s.index('| E48 评分/邻接四格');s=s[:i]+'| E49 冻结局部画像性能 | E47全部selected固定，cal选seed后audit及五L五轮 | `COMPLETE_FROZEN_LOCAL_RL_EVALUATION_NO_DUAL_FRONTIER_GAIN`；WebVid局部正值，Yandex质量全平；423680 NSG/80点250wall | [38 冻结模型评测](experiment_history/38_frozen_local_rl_evaluation.md) |\n'+s[i:];p.write_text(s.replace('三十七份详细卡片','三十八份详细卡片'))
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n- [38 冻结局部画像性能](38_frozen_local_rl_evaluation.md)：E49完成开发与完整曲线，局部WebVid正值保留，未形成双集前沿增益。\n')
(R/'summary.md').write_text(f'''# ACSG 当前结果摘要

2026-09-12，最近完成E49，`{status}`。[报告](entry_method_exploration/20260912_frozen_local_rl_evaluation_v1/report.md)、[历史38](experiment_history/38_frozen_local_rl_evaluation.md)。

{tab}
{core}
实际423680 NSG、80质量/性能点、250独立wall，单线程同机串行；72960返回独立评分和完整parity验收。最近完整Recall–QPS已更新到E49，默认保持。

E48证明WebVid更多邻接响应、Yandex更多评分响应，单因素均不能双集保留收益并减半损伤。接着E50检查已见候选到确定更新的转化，0新查询。用户目标持续至22:00；最终最佳候选对NSG/Fast/FastGT的完整比较尚未执行，详见[s-target](s-target.md)。
''')
(R/'s-target.md').write_text(f'''# ACSG 下一阶段目标与接续

2026-09-12，E49已完成，[历史38](experiment_history/38_frozen_local_rl_evaluation.md)。用户要求持续至22:00，大胆假设、小心证明，并最终比较最佳方法与NSG/Fast/FastGT的QPS、召回率、失败查询率。

## 已有证据

{core}
E48四格显示单独固定评分/邻接都未过双集保收益降损伤门；WebVid原有限动作oracle63/最佳静态35差额主要未覆盖24、自身损伤4，Yandex仅3/10状态有机会但oracle=最佳静态26。不能外推表示空间无机会，也不能泛称所有共享画像调整必然冲突。

## 立即接续E50

[协议](entry_method_exploration/20260912_candidate_commit_diagnosis_v1/protocol.md)和分析源码已准备，尚未冻结执行。固定E47全1600状态/12800候选，不挑正例，用原缓存重建真实C/A/M，对照J-best/hit-best/实际Adam。0新搜索。两集RL若≥20%步有净正候选，且其中≥半数M质量全空、J-best合计净值高于M且选中系数合法，则进入独立有限候选择优提交研究；统计合计不是部署模型。实际Adam方向扩大到GT无关候选半径与候选方向中间点的固定状态控制可进一步区分步长/方向。

{next_text}

最终Fast=原30K GT1/seed100/legacy堆，FastGT=E24 GT10-hard/20K/seed20260828。最终候选按独立cal规则冻结，不用最终audit/QPS换模型；若没有新候选稳定超过当前GT10，照实说明并保留最佳新候选对照。最终默认现有历史audit1024，五L五轮、失败=零GT10命中，完整曲线/全部点/配对失败转换/实际线程验收。详见[最终交付合同](entry_method_exploration/20260912_until2000_v1/final_comparison_contract.md)。
''')
p=R/'spec.md';s=p.read_text().replace('冻结模型E49评测已独立冻结并启动，完整验收尚未完成。','冻结模型E49评测已完成并验收。').replace('结果未完成时不声称部署收益。','结果由summary维护，未形成双集前沿增益，不替换默认。');s+='\nE49 [analyze.py](entry_method_exploration/20260912_frozen_local_rl_evaluation_v1/src/analyze.py)独立72960集合hits/mask及失败评分、全部NDC/wall核验，4096旧基线回归与6144 audit→curve返回位一致；[verify_contract.py](entry_method_exploration/20260912_frozen_local_rl_evaluation_v1/src/verify_contract.py)验收8串行job/423680 NSG、1280原kernel parity、250wall、cal选择冻结和split隔离。0新训练；最新性能证据为E49。E50轨迹诊断尚未执行，用户最终NSG/Fast/FastGT矩阵尚未测量。\n';p.write_text(s)
dump(O/'reviews/visual_review.json',dict(status='PASS',files=['figures/recall_qps.png','figures/quality_cost_changes.png'],method='Viewed both rendered charts; full curves and small deltas legible'))
dump(O/'state.json',dict(status=status,NSG_calls=423680,optimizer_updates=0,development_gate=gate['status'],default_replaced=False,campaign_complete=False))
roots=[R/x for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/38_frozen_local_rl_evaluation.md']];links=0
for p in roots+[O/'report.md',O/'protocol.md']:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in link or link.startswith('#'):continue
  assert (p.parent/link.split('#')[0]).exists(),(p,link);links+=1
resources();dump(O/'reviews/final_audit.json',dict(status='PASS',NSG_calls=423680,points=80,wall_repeats=250,protected_files=len(read(O/'reviews/protected.json')['files']),local_links=links,artifact_bytes=sum(p.stat().st_size for p in O.rglob('*') if p.is_file()),
 contract=read(O/'reviews/contract_verification.json'),outputs=read(O/'reviews/output_verification.json'),campaign_complete=False,default_replaced=False))
freeze(O/'reviews/final_artifact_freeze.json',[p for p in O.rglob('*') if p.is_file()]+roots)
print('E49 FINAL AUDIT PASS',flush=True)
