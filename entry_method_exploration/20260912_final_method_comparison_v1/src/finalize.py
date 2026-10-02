from common import *
import re,ast,sys
assert os.sched_getaffinity(0)=={8};resources()
for name in ['prequery_freeze','upstream','protected','native_dependencies','selection_before_validation']:check(O/'reviews'/f'{name}.json')
v=read(O/'reviews/output_verification.json');assert v['status']=='PASS' and read(O/'reviews/contract_verification.json')['status']=='PASS'
r=read(O/'results/analysis.json');core=(O/'reviews/interpretation.md').read_text();assert read(O/'reviews/visual_review.json')['status']=='PASS'
pp=[p for p in r['points'] if p['phase']=='validation'];selection=r['selection'];jobs=read(O/'logs/jobs.json');seconds=sum(x['seconds'] for x in jobs)
labels={'nsg':'NSG','fast30k':'Fast30K','gt10_hard':'FastGT10-hard','baseline_soft':'GT10-soft匹配起点','best_new':'cal选中候选'}
def tab(rows):
 s='| 数据集 | 方法 | L | Recall@10 % | QPS中位数 | QPS五轮范围 | 零命中失败率 %（条数） |\n|---|---|---:|---:|---:|---:|---:|\n'
 for p in rows:s+=f'| {"WebVid" if p["dataset"]==DS[0] else "Yandex"} | {labels[p["model"]]} | {p["L"]} | {p["recall_pct"]:.4f} | {p["QPS"]:.2f} | {p["QPS_min"]:.2f}–{p["QPS_max"]:.2f} | {p["failure_pct"]:.2f} ({p["failed_queries"]}) |\n'
 return s
selected='\n'.join(f'- {"WebVid" if ds==DS[0] else "Yandex"}：`{selection[ds]["best_new"]["model"]}`，cal ΔRecall {selection[ds]["best_new"]["delta_recall_pp"]:+.4f}pp；含默认的best_all=`{selection[ds]["best_all"]["model"]}`。' for ds in DS)
nexttext='''E56已准备“查询画像P固定、RL只优化离线构图坐标产生的G(C)”四训练。它保持E53同Gaussian/方向/步长接受/反馈池，单独改变训练时真实奖励作用的图；区别于E33只删原底层边。算法源码与协议写成时间早于本次WebVid结果生成，随后在读取任何本次最终结果前封存；严格“结果可用前封存”的首次检查未通过，时间边界如实记录。完整E55性能验收后才启动，不与测速并行。若预算完成，原候选池加两个新模型/集按原cal规则重新冻结；原E55完整结果保留，不用最终validation换seed或修改算法。21:15停止训练、21:40停止新查询、22:00收口。'''
status='COMPLETE_FROZEN_POOL_FINAL_METHOD_COMPARISON'
body=f'''# E55 固定候选池与NSG/Fast/FastGT的完整比较

2026-09-12，`{status}`。本轮17候选/集选型及最终完整比较完成，默认实现尚未替换。

{core}

## 固定cal选型

{selected}

候选池含匹配默认、E47 RL/ES各双seed及E52/E53各双seedA/S/T，17个全部预先锁定。cal按原U均值、低totalNDC、固定顺序择优，默认排首；best_all与best_new分开。选中模型与完整矩阵在本次validation查询前冻结，最终结果不回流选型。“最佳”仅指该有限池与此规则，不是所有ANN方法或参数的全局最优。

## L128代表点

{tab([p for p in pp if p['L']==128])}

QPS为同机CPU15、实际进程/OMP/BLAS/MKL1线程，五轮纯端到端wall中位数；范围保留全部五轮。失败是GT10零命中，不是程序报错。L128用于紧凑展示，方法判断必须看完整五L曲线。

## 全部实测点

{tab(pp)}

## 比较身份和数据

NSG原固定入口；Fast是原30K/GT1闭式画像、HNSW seed100、legacy heap；FastGT明确是E24 GT10-hard/20K/seed20260828/sorted3。WebVid额外保留GT10-soft-t1匹配起点；Yandex FastGT同时是匹配起点。Fast与FastGT还存在训练量/seed差别，不能把差异全部归因GT数量。当前候选均为静态物理图，一次普通HNSW取三个真实入口后走原NSG，无在线RL策略。

每集历史validation2000，沿用E34冻结副本。cal/audit来自router_train，validation来自另一原始分区，局部行号均可从0开始；本次核验原来源记录、复制SHA、与train/monitor/cal/audit的完整query字节零重叠。历史validation曾用于旧研究，不能称全项目新盲测。0原完整validation/held-out访问，0新GT/训练反馈。

## 成本和独立核验

34 fit点+34 cal点+45最终点，真实710144 NSG，6个串行job、225wall轮，进程累计{seconds:.3f}s；全部113点/129168行独立GT集合评分与hitmask/失败通过，4352 fit返回五字段恢复、2048旧baseline cal回归、1808原kernel parity，五L入口/物理图一致、完整plain/count/重复输出一致。逐query收益/损伤/失败救回与新失败、五轮QPS范围及公共Recall域内描述性插值完整保存，插值不是实测同Recall点。无新增训练或默认替换。

{nexttext}

[协议](protocol.md)、[45实测点CSV](results/final_points.csv)、[五轮计时](results/timings.csv)、[配对收益/损伤](results/paired_comparisons.csv)、[逐query结果](results/query_results.csv)、[选择冻结](reviews/selection_before_validation.json)、[数据隔离](reviews/split_isolation.json)、[输出核验](reviews/output_verification.json)、[合同核验](reviews/contract_verification.json)。

[Recall–QPS](figures/recall_qps.svg)、[失败率–QPS](figures/failure_qps.svg)、[三指标全部L](figures/three_metrics_by_L.svg)，同名PNG/PDF可导出。
'''
(O/'report.md').write_text(body);(O/'conclusion.md').write_text(core+'\n\n'+tab([p for p in pp if p['L']==128])+'\n'+nexttext+'\n')
hist=re.sub(r'\]\(([^)]+)\)',lambda m:'](../entry_method_exploration/20260912_final_method_comparison_v1/'+m.group(1)+')',body.replace('# E55 固定候选池与NSG/Fast/FastGT的完整比较','# 44. E55 固定候选池最终比较'))
(R/'experiment_history/44_final_method_comparison.md').write_text(hist)
p=R/'s-experiment.md';s=p.read_text();i=s.index('| E54 完整');s=s[:i]+'| E55 固定池最终比较 | 17候选cal选型，NSG/Fast/FastGT完整五L五轮 | `COMPLETE_FROZEN_POOL_FINAL_METHOD_COMPARISON`；45最终点225wall、710144 NSG，三指标已交付 | [44 最终比较](experiment_history/44_final_method_comparison.md) |\n'+s[i:];p.write_text(s.replace('四十三份详细卡片','四十四份详细卡片'))
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n- [44 固定候选池最终比较](44_final_method_comparison.md)：cal预选候选与NSG/Fast/FastGT三指标同机单线程完整实测。\n')
(R/'summary.md').write_text('# ACSG 当前结果摘要\n\n2026-09-12，E55固定池完整比较已完成，[报告](entry_method_exploration/20260912_final_method_comparison_v1/report.md)。\n\n'+core+'\n\n'+tab([p for p in pp if p['L']==128])+'\n完整五L/五轮范围与失败转换均保留；历史validation2000、单线程，最终结果未回流选型，默认仍WebVid GT10-soft-t1/Yandex GT10-hard。\n\n'+nexttext+'\n')
(R/'s-target.md').write_text('# ACSG 下一阶段目标与接续\n\n2026-09-12，E55固定17候选池的最终比较已完成，710144 NSG/45最终点/225wall，独立核验通过。\n\n'+nexttext+'\n\n[E56协议](entry_method_exploration/20260912_construction_only_rl_v1/protocol.md)、[训练源码](entry_method_exploration/20260912_construction_only_rl_v1/src/train.py)、[设计时间证据](entry_method_exploration/20260912_construction_only_rl_v1/reviews/design_before_result_inspection.json)。原native每seed独立实例，19224真实构图/9612安装/36107264 HNSW，NSG62976+真实变化；四run预留600000，free7GiB/artifact384MiB新合同。启动前按E53总时间×1.65+180秒投影21:10前完成，后续最终比较保留完整窗口。\n')
p=R/'spec.md';s=p.read_text().replace('E54完整模型干预已验收','E55固定候选池完整比较已验收').replace('最新性能证据为E49','E49历史性能证据保留，最新固定池比较为E55').replace('用户最终NSG/Fast/FastGT矩阵尚未测量','用户要求的NSG/Fast/FastGT矩阵已由E55测量')
s+='\nE55 [deploy.py](entry_method_exploration/20260912_final_method_comparison_v1/src/deploy.py)固定17候选/集，128条独立checkpoint恢复、cal原U/低NDC/固定序选择后冻结最终矩阵；E34历史validation2000独立同机单线程五L五轮，FastGT显式GT10-hard，WebVid另匹配soft起点。原同SHA无策略评测二进制、GT全部raw后评分、full plain/count及原kernelparity保持；[analyze.py](entry_method_exploration/20260912_final_method_comparison_v1/src/analyze.py)独立129168集合评分与113点/225wall/710144 NSG核验。局部row IDs需绑定router_train/validation源命名空间，复制SHA及向量零重叠共同验收。\n';p.write_text(s)
roots=[R/x for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/44_final_method_comparison.md']];links=0
for p in roots+[O/'report.md',O/'protocol.md']:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in link or link.startswith('#'):continue
  assert (p.parent/link.split('#')[0]).exists(),(p,link);links+=1
for p in (O/'src').rglob('*.py'):ast.parse(p.read_text())
dump(O/'state.json',dict(status=status,NSG_calls=710144,final_points=45,wall_repeats=225,default_replaced=False,campaign_complete=False))
dump(O/'reviews/final_audit.json',dict(status='PASS',protected_files=len(read(O/'reviews/protected.json')['files']),local_links=links,artifact_bytes=sum(p.stat().st_size for p in O.rglob('*') if p.is_file()),verification=v,NSG_calls=710144,campaign_complete=False))
print('E55 FINAL AUDIT PASS; seal externally after log closes',flush=True)
