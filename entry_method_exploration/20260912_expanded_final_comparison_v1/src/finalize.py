from common import *
import re,ast,sys
assert os.sched_getaffinity(0)=={8};resources()
for name in ['prequery_freeze','upstream','protected','native_dependencies','selection_before_validation']:check(O/'reviews'/f'{name}.json')
v=read(O/'reviews/output_verification.json');assert v['status']=='PASS' and read(O/'reviews/contract_verification.json')['status']=='PASS'
r=read(O/'results/analysis.json');completion=read(O/'results/deployment_complete.json');sources=read(O/'results/final_sources.json');core=(O/'reviews/interpretation.md').read_text();assert read(O/'reviews/visual_review.json')['status']=='PASS'
pp=[p for p in r['points'] if p['phase']=='validation'];selection=r['selection'];jobs=read(O/'logs/jobs.json');seconds=sum(x['seconds'] for x in jobs)
labels={'nsg':'NSG','fast30k':'Fast30K','gt10_hard':'FastGT10-hard','baseline_soft':'GT10-soft匹配起点','best_new':'cal选中候选'}
def tab(rows):
 s='| 数据集 | 方法 | L | Recall@10 % | QPS中位数 | 五轮QPS范围 | 零命中失败率 %（条数） |\n|---|---|---:|---:|---:|---:|---:|\n'
 for p in rows:s+=f'| {"WebVid" if p["dataset"]==DS[0] else "Yandex"} | {labels[p["model"]]} | {p["L"]} | {p["recall_pct"]:.4f} | {p["QPS"]:.2f} | {p["QPS_min"]:.2f}–{p["QPS_max"]:.2f} | {p["failure_pct"]:.2f} ({p["failed_queries"]}) |\n'
 return s
selected='\n'.join(f'- {"WebVid" if ds==DS[0] else "Yandex"}：`{selection[ds]["best_new"]["model"]}`，cal ΔRecall {selection[ds]["best_new"]["delta_recall_pp"]:+.4f}pp；含默认best_all=`{selection[ds]["best_all"]["model"]}`；最终矩阵{"完整复用E55" if sources[ds]["reused_E55"] else "本轮E57同批新测"}。' for ds in DS)
nexttext='''本轮19候选的最终模型与性能证据冻结，不再用最终validation回流训练、改seed或选checkpoint。剩余时间仅追溯E52/E53/E56已接受动作：同一真实修改在train与历史monitor上分别带来多少收益/损伤，是否集中于少数查询；该固定轨迹诊断不能改写本轮最终选择。21:40停止新查询，22:00交付。'''
status='COMPLETE_EXPANDED_POOL_FINAL_COMPARISON'
body=f'''# E57 加入纯构图RL后的最终比较

2026-09-12，`{status}`，19候选/集固定选型与最终三指标比较完成。

{core}

## 选择与测量来源

{selected}

原E55池17模型加E56两个seed，顺序与原cal规则在E56训练前已约定，未按monitor或最终validation删候选。全部19模型重新fit128恢复并cal1024评估，原17模型cal五字段全量逐位恢复。cal原U/低totalNDC/固定序选出best_all与best_new；最终矩阵和选择先冻结，然后才测有改选的数据集。未改选数据集完整继承E55同组结果及全部五轮原始时间，不重复测速，也不把一组方法的不同批次结果拼在一起。全部模型始终静态一次HNSW再原NSG；纯构图模型查询画像P固定，construction_W没有进入查询配置。

## L128代表点

{tab([p for p in pp if p['L']==128])}

QPS同机CPU15、实际进程/OMP/BLAS/MKL1线程、五轮纯端到端wall中位数；失败为GT10零命中。L128只作紧凑展示，完整五L与波动范围如下。

## 全部最终实测点

{tab(pp)}

## 比较身份、数据与核验

NSG原固定入口；Fast30K原GT1闭式画像/seed100/legacy heap；FastGT明确E24 GT10-hard/20K/seed20260828/sorted3，WebVid另soft匹配起点，Yandex FastGT即匹配起点。Fast与FastGT还有训练量和seed区别。历史validation2000与router_train的fit/monitor/cal/audit属于不同源分区，复制SHA与实际query字节零重叠；局部row IDs不能跨源直接比较。历史validation曾用于研究，不能称全项目新盲测。0原完整validation/held-out访问、0新GT/训练。

本阶段实际新增{completion['NSG_calls']} NSG，其中38 fit点+38 cal点固定88768，新增最终{completion['new_final_points']}点/{completion['new_wall_repeats']}轮；完整交付仍45最终点/225可用wall轮，其余明确继承E55。新job进程累计{seconds:.3f}s。独立121可用点/133776行集合评分、hitmask/失败与收益损伤、4864 fit返回恢复、34816原17模型cal五字段回归、2048更早默认cal回归，1936可用原kernel parity、五L图/入口一致全部通过。可用历史parity与本轮新增调用分开，线程/串行/GT时序/选择冻结/源SHA和调用账通过。

公共Recall域内log-QPS插值只作描述，不冒充实测同Recall点；五轮范围与稀疏query不确定性保留。默认代码配置没有自动替换。

{nexttext}

[协议](protocol.md)、[最终45点](results/final_points.csv)、[五轮计时](results/timings.csv)、[配对收益/损伤](results/paired_comparisons.csv)、[逐query](results/query_results.csv)、[选型](results/cal_selection.json)、[整组测量来源](results/final_sources.json)、[调用范围](results/deployment_complete.json)、[独立输出验收](reviews/output_verification.json)、[合同验收](reviews/contract_verification.json)。

[Recall–QPS](figures/recall_qps.svg)、[失败率–QPS](figures/failure_qps.svg)、[三指标全部L](figures/three_metrics_by_L.svg)，同名PNG/PDF可导出。
'''
(O/'report.md').write_text(body);(O/'conclusion.md').write_text(core+'\n\n'+tab([p for p in pp if p['L']==128])+'\n'+nexttext+'\n')
hist=re.sub(r'\]\(([^)]+)\)',lambda m:'](../entry_method_exploration/20260912_expanded_final_comparison_v1/'+m.group(1)+')',body.replace('# E57 加入纯构图RL后的最终比较','# 46. E57 扩展池最终比较'))
(R/'experiment_history/46_expanded_final_comparison.md').write_text(hist)
p=R/'s-experiment.md';s=p.read_text();i=s.index('| E56 纯');s=s[:i]+f'| E57 扩展池最终比较 | 原17候选加纯构图RL双seed，19模型cal选型 | `{status}`；新增{completion["NSG_calls"]} NSG/{completion["new_final_points"]}性能点，最终45点225轮可追溯 | [46 扩展池最终比较](experiment_history/46_expanded_final_comparison.md) |\n'+s[i:];p.write_text(s.replace('四十五份详细卡片','四十六份详细卡片'))
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n- [46 扩展池最终比较](46_expanded_final_comparison.md)：19候选固定选型与最新完整三指标，未改选整组保留E55。\n')
(R/'summary.md').write_text('# ACSG 当前结果摘要\n\n2026-09-12，E57最终19候选选型与三指标比较已完成，[报告](entry_method_exploration/20260912_expanded_final_comparison_v1/report.md)。\n\n'+core+'\n\n'+tab([p for p in pp if p['L']==128])+'\n完整五L/五轮范围、收益/损伤与每集整组来源均保留。历史validation2000、单线程，最终结果未回流选型；默认配置尚未替换。\n\n'+nexttext+'\n')
(R/'s-target.md').write_text('# ACSG 下一阶段目标与接续\n\n2026-09-12，E57的19候选固定选型和完整最终比较已完成。\n\n'+nexttext+'\n\n最新性能入口[E57报告](entry_method_exploration/20260912_expanded_final_comparison_v1/report.md)，旧E55/全部训练与负结果保留。后续只能沿冻结轨迹做收益/损伤诊断；不得重开超参网格或更换已选最终模型。\n')
p=R/'spec.md';s=p.read_text().replace('E56纯构图RL已验收','E57扩展候选池最终比较已验收');s+='\nE57 [deploy.py](entry_method_exploration/20260912_expanded_final_comparison_v1/src/deploy.py)固定原17+纯构图2模型/集，19候选全fit/cal复核后按原规则冻结；只为改选dataset新增同组五L五轮，未改选整组继承E55且核对每个模型W/graph/mapping身份。final_sources.json绑定逐集来源，不同批次方法不得在同一组内拼接。121可用点及133776独立集合评分、原17模型cal五字段回归通过；新增调用与继承wall/parity分账。\n';p.write_text(s)
roots=[R/x for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/46_expanded_final_comparison.md']];links=0
for p in roots+[O/'report.md',O/'protocol.md']:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in link or link.startswith('#'):continue
  assert (p.parent/link.split('#')[0]).exists(),(p,link);links+=1
for p in (O/'src').rglob('*.py'):ast.parse(p.read_text())
dump(O/'state.json',dict(status=status,new_NSG=completion['NSG_calls'],new_final_points=completion['new_final_points'],available_final_points=45,available_wall_repeats=225,default_replaced=False,campaign_complete=False))
dump(O/'reviews/final_audit.json',dict(status='PASS',protected_files=len(read(O/'reviews/protected.json')['files']),local_links=links,artifact_bytes=sum(p.stat().st_size for p in O.rglob('*') if p.is_file()),verification=v,new_NSG=completion['NSG_calls'],campaign_complete=False))
print('E57 FINAL AUDIT PASS; seal externally after log closes',flush=True)
