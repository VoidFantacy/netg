from shared import *
import re,ast
threads(8);resources()
for name in ['prequery_freeze','protected','native_dependencies']:check(O/'reviews'/f'{name}.json')
r=read(O/'results/summary.json');v=read(O/'reviews/verification.json');assert v['status']=='PASS';cost=r['cost']
core=(O/'reviews/interpretation.md').read_text();assert (O/'reviews/visual_review.json').exists()
tab='| 数据集 | 模型 | 干预 | train ΔR pp | monitor ΔR pp | monitor gain/loss hits |\n|---|---|---|---:|---:|---:|\n'
for ds in DS:
 for rec in [x for x in read(O/'inputs/contexts.json') if x['dataset']==ds]:
  for cell in ['A','S','T']:
   tt=next(x for x in r['metrics'] if x['dataset']==ds and x['key']==rec['key'] and x['cell']==cell and x['phase']=='train');mm=next(x for x in r['metrics'] if x['dataset']==ds and x['key']==rec['key'] and x['cell']==cell and x['phase']=='monitor')
   tab+=f'| {"WebVid" if ds==DS[0] else "Yandex"} | {rec["key"].replace("202609","seed")} | {cell} | {tt["delta_recall_pp"]:+.4f} | {mm["delta_recall_pp"]:+.4f} | {mm["gain_hits"]}/{mm["loss_hits"]} |\n'
status='COMPLETE_WHOLE_LEARNED_MODEL_FACTORIAL'
nexttext='''下一阶段E55固定17候选/集：匹配默认、E47 RL/ES各双seed，以及本次E52/E53双seed的全部A/S/T共12模型；候选池在四格查询前已经锁定，不按此处结果删选。先独立128条普通二进制恢复，再cal1024原U/低NDC/固定序择优，冻结best_all和best_new。最终WebVid五方法/Yandex四方法与NSG、Fast30K、FastGT10-hard同机单线程五L五轮，历史validation2000，Recall/QPS/零GT10失败率三指标；总710144 NSG/225wall轮。若默认优于新候选，明确说明；最终结果不回流换模型。21:40停止新查询，22:00交付。'''
body=f'''# E54 完整学成模型的画像与邻接干预

2026-09-12，`{status}`。

{core}

{tab}

C(P,G0)为匹配起点，A(W,G)完整学成模型，S(W,G0)只换评分画像，T(P,G)只换实际邻接。固定E52/E53所有四模型/集，selected点不再变化。所有26物理静态图实际查询，全部向量字节/拓扑身份和64条三路parity通过；S/T不是用其评分W普通构图会得到的图，部署时载入已导出实际图。

实际{cost['NSG_calls']} NSG={cost['normal_new_NSG']}变化query补测+4992parity，136448 HNSW、18普通构图、16邻接安装，进程累计{cost['query_seconds']:.3f}s。133120独立集合评分、51200 C/A五字段逐位恢复、1664物理parity行，以及全部patch复用/逐query交互身份通过。0训练更新/0cal或最终validation查询/0新GT/0QPS。

监控参与旧checkpoint选择，不能称盲测。本实验固定学成端点的静态因果干预，不推断所有训练步骤机制相同，不撤销E48旧单因子门失败；默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。

E54首次prepare在任何原生调用前检查到E53冻结v1收尾日志失配，改引用稳定v2后完成；原失败日志保留，无查询重试。

{nexttext}

[协议](protocol.md)、[逐模型/阶段指标](results/metrics.csv)、[交互项](results/interactions.csv)、[完整结果](results/summary.json)、[独立验证](reviews/verification.json)、[四格图](figures/whole_model_factorial.svg)。
'''
(O/'report.md').write_text(body);(O/'conclusion.md').write_text(core+'\n'+nexttext+'\n')
hist=re.sub(r'\]\(([^)]+)\)',lambda m:'](../entry_method_exploration/20260912_learned_model_factorial_v1/'+m.group(1)+')',body.replace('# E54 完整学成模型的画像与邻接干预','# 43. E54 完整模型画像/邻接四格'))
(R/'experiment_history/43_learned_model_factorial.md').write_text(hist)
p=R/'s-experiment.md';s=p.read_text();i=s.index('| E53 RL');s=s[:i]+f'| E54 完整模型四格 | E52/E53全部selected固定W/G交换 | `{status}`；26物理图，{cost["NSG_calls"]} NSG，0训练 | [43 完整模型四格](experiment_history/43_learned_model_factorial.md) |\n'+s[i:];p.write_text(s.replace('四十二份详细卡片','四十三份详细卡片'))
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n- [43 完整模型画像/邻接四格](43_learned_model_factorial.md)：固定学成模型的评分与邻接作用，训练和监控分开。\n')
(R/'summary.md').write_text('# ACSG 当前结果摘要\n\n2026-09-12，最近完成E54，[报告](entry_method_exploration/20260912_learned_model_factorial_v1/report.md)。\n\n'+core+'\n\n'+nexttext+'\n\n默认保持WebVid GT10-soft-t1 / Yandex GT10-hard，最新完整曲线仍E49，最终完整比较尚未执行。\n')
(R/'s-target.md').write_text('# ACSG 下一阶段目标与接续\n\n2026-09-12，E54完整模型四格完成并独立验收。\n\n'+nexttext+'\n\n[E55查询前协议](entry_method_exploration/20260912_final_method_comparison_v1/protocol.md)和源码已准备，尚未冻结执行。原17候选/集不按四格结果删选；单线程串行、旧源保护、最终GT不进训练。cal来自router_train，validation来自另一源命名空间，局部行号重合不等于查询重合；源记录与实际向量双重核验。\n')
p=R/'spec.md';p.write_text(p.read_text()+'\nE54 [完整模型run](entry_method_exploration/20260912_learned_model_factorial_v1/src/run.py)复用E48原生拓扑安装器，在所有学成W/G端点构造A/S/T实际物理图并对完整train4096+monitor1024查询；全部26图导出/64行三路parity、完整向量和图身份检查，C/A旧结果五字段逐位恢复。新增接口无线上策略或kernel改变；静态干预图必须加载冻结graph，不能按评分W重新普通构建来代替。\n')
p=R/'spec.md';s=p.read_text()
for before,after in [
 ('E47完整反馈训练已验收；E37部署及原Fast/NSG kernel不变','E54完整模型干预已验收；E37部署及原Fast/NSG kernel不变'),
 ('E47连续全池训练已独立实现并启动','E47连续全池训练已完成并验收'),
 ('后继评分/拓扑installer和冻结模型评测尚未执行','后继评分/拓扑installer和冻结模型评测已在E48/E49完成'),
 ('E51步长方向控制已完成验收，连续提交尚未执行','E51步长方向控制及E52连续提交均已完成验收'),
 ('RL反馈步长接受仅后继设计，未实现','RL反馈步长接受已由E53实现并验收'),
 ('E53 RL方向+真实反馈步长接受源码/输入/协议已冻结，训练进行中，完整验收尚未完成','E53 RL方向+真实反馈步长接受四训练及独立重放已完成'),
 ('当前尚无完整四训练结果','四训练完整结果与独立核验由E53报告维护')]:s=s.replace(before,after)
p.write_text(s)
roots=[R/x for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/43_learned_model_factorial.md']];links=0
for p in roots+[O/'report.md',O/'protocol.md']:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in link or link.startswith('#'):continue
  assert (p.parent/link.split('#')[0]).exists(),(p,link);links+=1
jobs=read(O/'logs/jobs.json');assert len(jobs)==2 and all(x['status']=='COMPLETE' for x in jobs) and sum(x['actual'] for x in jobs)==cost['NSG_calls']
for p in files(O/'src'):
 if p.suffix=='.py':ast.parse(p.read_text())
dump(O/'state.json',dict(status=status,cost=cost,campaign_complete=False));dump(O/'reviews/final_audit.json',dict(status='PASS',protected_files=len(read(O/'reviews/protected.json')['files']),local_links=links,cost=cost,verification=v,artifact_bytes=sum(p.stat().st_size for p in files(O))))
print('E54 FINAL AUDIT PASS; seal externally after process/log close',flush=True)
