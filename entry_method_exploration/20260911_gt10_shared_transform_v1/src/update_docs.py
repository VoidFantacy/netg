from setup import *
import csv
P='entry_method_exploration/20260911_gt10_shared_transform_v1'
SHORT={DS[0]:'WebVid',DS[1]:'Yandex-IP'}
def link(s):return f'{P}/{s}'
def table(headers,data):return '| '+' | '.join(headers)+' |\n|'+'|'.join(['---']*len(headers))+'|\n'+''.join('| '+' | '.join(map(str,row))+' |\n' for row in data)
def main():
 nums=json.loads((O/'results/report_numbers.json').read_text());status=nums['conclusion']['status'];no_go=not nums['conclusion']['shared_GO'];dsnames={'WebVid2.5M':'WebVid','Yandex10M IP':'Yandex-IP'}
 stats=nums['stats'];dif=list(csv.DictReader((O/'results/validation_differences.csv').open()));td=json.loads((O/'results/teacher_diagnostics.json').read_text())
 judgment='本轮没有建立共享线性或小MLP优于原GT10的稳定双数据证据，保留原已冻结GT10路线。' if no_go else '共享变换通过本轮预设本地必要门，但仍需要新独立验证，不能升级为论文或部署GO。'
 chart_table=table(['数据集','模型','共同原GT10召回点数','插值QPS几何均变','同L两指标均升'],[[dsnames[x['dataset']],x['method'],len(x['common_anchor_recalls']),'无覆盖' if x['geomean_interpolated_qps_delta_pct'] is None else f"{x['geomean_interpolated_qps_delta_pct']:+.2f}%",f"{x['positive_same_L_points']}/5"] for x in stats])
 delta_rows=[]
 for ds,short in dsnames.items():
  for L in [64,128,256,400,800]:
   vals=[]
   for m in ['linear','mlp','free']:
    x=next(x for x in dif if x['dataset']==ds and x['method']==m and int(x['L'])==L);vals.append(f"{float(x['delta_recall_pp']):+.3f} / {float(x['delta_qps_pct']):+.2f}%")
   delta_rows.append([short,L]+vals)
 dt=table(['数据集','L','linear ΔRpp / ΔQPS','MLP ΔRpp / ΔQPS','free ΔRpp / ΔQPS'],delta_rows)
 summary=f'''# ACSG 当前实验总结

> 更新至2026-09-11。最近完成E28 GT10共享入口变换研究；状态`{status}`。实现合同见[spec](spec.md)，接续见[s-target](s-target.md)，历史见[s-experiment](s-experiment.md)。

## 当前结论

**{judgment}** 两数据集、原GT10 hard锚定的共享linear/小MLP/free同目标训练已经完成，并与NSG、原Fast30K、GT1 hard、GT10 hard及原cal冻结GT1/GT10 soft同批比较，完整90点各三次单线程wall。不能从候选教师上界、训练损失下降或同L增量代替完整Recall–QPS判断。

当前匹配比较均以GT10 hard作锚点；历史正式画像仍是WebVid GT10 soft、Yandex GT10 hard。Fast30K保留其30K/seed100/旧入口顺序身份。

## 完整五L新模型变化

同一批次相对GT10 hard；R为Recall@10百分点，QPS为同L三轮中位数之比。全部正负点保留。配对95%区间和原六基线的绝对值见[完整报告]({link('report.md')})。

{dt}
下表仅对四主方法共同覆盖的原GT10实测Recall点作log-QPS插值，是粗网格描述，不是新增实测等Recall点或新选择规则。

{chart_table}
## 机制上新增的认识

fit20k/集的C8教师比原GT10 hard有+4.626/+2.850pp Recall空间，同时平均graph NDC由1642.94/2862.29降至1621.29/2822.89。但教师逐query使用GT从56个完整三元组中选优，不能部署，也不是全H或等工作上界。

固定H的MLP只是在离线生成静态W；上线仍为qᵀW，不能声称具有比自由W更大的query函数族。12次训练都使目标下降，独立NumPy前向/归一化重算通过，但共享linear/MLP的fit精确top3教师入口重合度没有提升。模型MAP等于top3不意味着每次代理损失下降都会改善top3；报告给出可复算反例。

cal两集均选linear λ100、MLP λ10、free λ100，冻结后才执行audit/validation。audit呈数据集/L差异；HNSW与exact诊断单列，不把精确画像排名当作真实有限L入口oracle。教师命中空间与同命中下NDC选优的分组分析见[teacher_diagnostics]({link('results/teacher_diagnostics.json')})；标签内预测评价是条件子集，不外推到全fit或HNSW性能。

## E24–E27结论保留

E24 GT10的局部正信号不因E25/E26/E28增强未稳定成功而消失。E27原机制链为query相关多目标归属→画像变化→实际三入口变化→少量正负query净收益；两个原正点在exact3下仍保留。其WebVid五L速度+0.34%–1.36%是旧独立批次结论，Yandex原+2.56%未稳定复现；不与E28混拼绝对QPS。详见[历史16](experiment_history/16_gt10_mechanism.md)。

## 执行与证据边界

本轮224万逻辑三元组标签独立GT重评分；新标注1,971,899、标注parity256，268,101次复用兼容缓存。开发/正式评测150点、235,296个query输出独立评分，原六曲线120,000个输出回归E24。实际NSG调用{nums['total_real_calls']:,}，修复0，合成搜索0；训练12次，共{nums['training_seconds']:.2f}s（8线程）。正式查询CPU15/实际线程1/OMP与BLAS1，原kernel、图、base、H和旧标签/画像/结果保持身份。

fit/cal/audit/validation均有历史使用，一个hub/图构建；三次wall不增加Recall样本，bootstrap未做多重校正。held-out未访问/hash。精确GT、QGT、原画像和主图从零成本未新测。当前结果是本地探索，不是新盲测或论文等级结论。

## 交付

- [研究与全部实测报告]({link('report.md')})、[四主方法图]({link('figures/recall_qps_main.svg')})、[全部基线图]({link('figures/recall_qps_all.svg')})、[数据工作簿]({link('chart_data.xlsx')})。
- [协议]({link('protocol.md')})、[原始数据]({link('results/all_points.csv')})、[最终验收]({link('reviews/final_audit.json')})、[历史17](experiment_history/17_gt10_shared_transform.md)。
- 原E27 summary完整保存在[E28修改前快照]({link('source_before/summary.md')})；旧实验各自原产物继续保留。
'''
 (R/'summary.md').write_text(summary)
 target=f'''# ACSG 下一阶段方向与实验接续

2026-09-11。E28共享入口变换研究已完成并收口，状态`{status}`。{judgment} 本轮授权的标注、训练、五L三轮比较、图与报告均已完成；下面是未执行的下一研究建议，不自动借用本轮或历史剩余额度。

## 1. 优先处理监督压缩，暂不增加网络容量

E28完整三元组教师有+4.626/+2.850pp训练侧候选空间，但共享模型的集合CE下降未提高教师top3入口重合度。先检验“哪些教师更改值得学”和“损失是否惩罚真正的top3错误”，比直接扩大MLP/加query塔更有依据。固定H时离线MLP仍导出静态W，并未新增在线非线性边界。

完整证据：[E28报告]({link('report.md')})、[教师分组]({link('results/teacher_diagnostics.json')})、[训练核验]({link('reviews/model_verification.json')})、[完整曲线]({link('figures/recall_qps_main.svg')})。标签内预测子集带选择偏差，不当作全fit或部署收益。

## 2. 若明确继续，下一版本先作最小监督对照

建议保留GT10锚点、固定H、同原NSG、一次microHNSW top3。研究对象是教师和损失，先固定共享linear及单一事先正则；不同时扩大网络、rank、温度、候选数或query端模型。

| 对照轴 | 未执行的具体比较 | 要解决的问题 |
|---|---|---|
| 教师 | 现有max-hits/min-NDC教师，对比无额外命中空间时保留原GT10三入口的教师 | 大量同命中NDC标签是否稀释少数质量改进信号；新教师可能放弃成本收益，必须计量 |
| 损失 | 当前集合CE，对比完整教师成员与最强非教师入口之间的top3 margin | 单个完整query教师下无旧E23多上下文pair冲突；检查第三入口错误是否真正减少 |

两轴不能一次一起改后把收益全归于其中一项；需冻结最小2×2控制或先选一轴。可复用本轮兼容C8标签，不需要重新全H单入口标注；新模型训练和开发/正式查询比较仍需独立协议及明确预算。SoftSort/SOFT top-k只列为文献备选，不优先加一层复杂松弛；它们不解决教师偏差。

停止规则应在新搜索前定量锁定：先验证导出/梯度和训练侧top3目标确实改善，再看cal真实三入口Recall与完整工作，最后只对冻结配置补完整wall；缺少训练/开发改善就不扩大模型。必须保留旧损失/原教师负结果，不能靠事后换门、换L或挑seed取正点。

## 3. 保持的数据与计量边界

- 继续保留matched GT1 hard、GT10 hard、原cal冻结GT1/GT10 soft；WebVid正式原画像是GT10 soft，Yandex为GT10 hard。NSG/Fast30K保持独立身份。
- E24–E28原源码/图/H/画像/标签/结果/日志均保留。基座、度量、query、GT、图、H或路由参数改变，相关标签/选择/计时随依赖失效，不能直接复用。
- fit/cal/audit/validation均有历史使用。held-out不自动开启，新图/新seed/新数据也不在现有预算中。
- 本轮预算已经收口；actual calls={nums['total_real_calls']:,}，repair=0。空余预算不转成新网格。
- 只有独立同机完整Recall–QPS证据才能支持性能判断。教师上界、exact ranking、NDC或单次QPS差均不替代它。

## 4. 历史路线与恢复入口

E27机制分析已完成，其余2A/3A等历史建议保存在[E28修改前s-target]({link('source_before/s-target.md')})，不是当前自动执行队列。E25选择性改道、E26收缩的负结果不抹去E24/GT10局部正信号；本轮共享变换的结果也只约束本教师/目标/容量/样本范围。每次接续先读AGENTS、summary、spec、本文件、s-experiment和相应历史卡，再核对源与原始测量。
'''
 (R/'s-target.md').write_text(target)
 spec=R/'spec.md';text=spec.read_text();text=text.replace('## GT10共享入口变换 v1（E28，2026-09-11，执行中）','## GT10共享入口变换 v1（E28，2026-09-11，已完成）').replace('当前训练进行中。','12次训练完成；每族cal仅选λ，随后冻结再执行audit/validation。')
 text+=f'\nE28实现验收：完整150点235296个query输出独立评分，原六对照120000个输出回归E24；全部三轮warm/plain/count/reference结果按bit核验，五L入口和microHNSW身份一致。独立NumPy重算12份模型前向/单位化与最终集合CE通过。实际真实NSG调用{nums["total_real_calls"]}、repair0、synthetic0；原上游资产和冻结选择核验见[最终验收]({link("reviews/final_audit.json")})。方法结果状态`{status}`，效果与不确定性见summary/[历史17](experiment_history/17_gt10_shared_transform.md)，不由实现通过升级性能GO。\n'
 spec.write_text(text)
 card=f'''# 17 GT10共享入口变换（E28）

状态`{status}`，2026-09-11收口。{judgment} 原始目录[{P}](../{P}/report.md)。

## 动机与实现

延续E27对GT10机制的分析，检验离线共享变换能否让一次microHNSW直接找出更好的三入口。W=normalize(P_GT10+f(P_GT10))，linear无偏置d×d，MLP为d→64→d/ReLU，另有free H×d残差容量参考。在线raw query→HNSW3→真实ID→原NSG，不增加query塔或组合重排，不修改主图、H、metric或base。

fit20k/集，C8由GT1/GT10 hard实际HNSW3并集补齐，枚举56个完整三元组L128真实标签。教师max hits/min graphNDC/anchor score/realID；目标为全H三元素集合似然+画像锚定正则。它的MAP为top3，但不是任意互补性的模型；其normalizer属于diagonal k-DPP已知形式，不宣称新概率理论。

## 实验与冻结

两数据集各3族×λ10/100，固定80epoch、Adam.003、batch1024全fit梯度累积、seed20260911。cal1024 L64/128每族选λ；两集都选linear100/MLP10/free100。audit1024含exact诊断，fitprobe256仅诊断；原使用validation2000×9方法×5L共90正式点，每点三次单线程完整warm/plain。选择前后身份见[freeze](../{P}/models/frozen_before_validation.json)。

## 完整结果

{dt}
以上同L对GT10 hard差值；不能解释成等Recall加速。共同原GT10召回点的log-QPS插值描述如下，不外推、不当作新增测试点：

{chart_table}
教师候选空间为+4.626/+2.850pp，不能部署。共享模型目标下降而fit精确教师入口重合度未提高；audit与validation的完整正负和exact差异见[报告](../{P}/report.md)。模型损失/MAP/真实搜索三个层次分别判断。旧E24GT10正信号保留，本版不能否定所有共享表示学习，也不能用MLP组件本身宣称论文创新。

## 成本与核验

224万逻辑标签，新增1971899实际标签调用+256parity，268101缓存复用；全部标签独立GT评分。开发/正式150点235296输出独立评分，原六曲线120000输出回归E24。总NSG调用{nums['total_real_calls']:,}，修复0，合成0，预算收口。训练12次{nums['training_seconds']:.2f}s，CPU8；标注CPU16仅离线，不用其吞吐充查询QPS。正式CPU15/线程1/OMP-BLAS1，GT/计数/I/O在timer外，模型与图加载构建费用另列。

所有fit/cal/audit/validation有历史使用，一个既有hub/图，held-out未访问/hash。先验构建/精确GT从零成本未新测。旧源/图/画像/标签/结果保留，根文档修改前快照在[source_before](../{P}/source_before/summary.md)。

## 证据入口

- [协议](../{P}/protocol.md)、[文献与推导](../{P}/research.md)、[源清单](../{P}/sources/inventory.json)。
- [所有点](../{P}/results/all_points.csv)、[图表数据](../{P}/chart_data.xlsx)、[主图](../{P}/figures/recall_qps_main.svg)。
- [教师分析](../{P}/results/teacher_diagnostics.json)、[调用账](../{P}/logs/evaluation_jobs.json)、[最终验收](../{P}/reviews/final_audit.json)。

接续只按当前[s-target](../s-target.md)和新明确授权进行；本卡的原命令不自动重启训练或查询。
'''
 (R/'experiment_history/17_gt10_shared_transform.md').write_text(card)
 p=R/'s-experiment.md';text=p.read_text();needle='| E27 GT10收益机制分析 |';assert needle in text;new=f'| E28 GT10共享入口变换 | C8完整三入口教师、共享linear/MLP/free同目标12次训练；冻结选择后90正式点三轮wall | `{status}`；教师有空间但共享模型loss下降未提高教师top3重合；完整正负保留，版本收口 | [17 共享入口变换](experiment_history/17_gt10_shared_transform.md) |\n';text=text.replace(needle,new+needle,1);p.write_text(text)
 p=R/'experiment_history/README.md';text=p.read_text();needle='| [16';line=next(l for l in text.splitlines() if l.startswith(needle));text=text.replace(line,line+'\n| [17 GT10共享入口变换](17_gt10_shared_transform.md) | C8真实三入口教师、共享linear/MLP/free、完整Recall–QPS比较与监督压缩边界 |',1);p.write_text(text)
 initial=O/'reviews/scope_initialized.md'
 if not initial.exists():shutil.copy2(O/'scope.md',initial)
 (O/'scope.md').write_text(f'# E28研究范围与状态\n\n状态`{status}`，本版本已完成并收口。研究比较GT10 hard锚定的共享linear、小MLP和free静态入口表；在线raw query→单份microHNSW top3→真实hub→原NSG。完整协议和调用预算在[protocol](protocol.md)，结果在[report](report.md)，最终核验在[final_audit](reviews/final_audit.json)。\n\n初始化阶段的临时表述保存在[scope_initialized](reviews/scope_initialized.md)，不作为当前状态。历史fit/cal/audit/validation边界保持，held-out未访问。所有后续训练/搜索需新的独立版本与授权，不重启本目录。\n')
 (O/'README.md').write_text(f'# GT10共享入口变换实验\n\n`{status}`。{judgment}\n\n- [完整研究与实测报告](report.md)\n- [主Recall–QPS图](figures/recall_qps_main.svg)、[全部基线](figures/recall_qps_all.svg)、[相对速度插值图](figures/interpolated_speed.svg)\n- [Excel图表数据](chart_data.xlsx)、[全部点CSV](results/all_points.csv)\n- [冻结协议](protocol.md)、[方法/文献依据](research.md)、[最终验收](reviews/final_audit.json)\n\n输入按绝对路径绑定既有E24/E23数据和原NSG，身份见reviews/protected_before.json；依赖环境见reviews/machine.json，编译参数见bin/*.build.json。脚本拒绝覆盖已有搜索和训练输出。本版本真实NSG调用{nums["total_real_calls"]:,}次，训练12次，held-out未访问。\n')
 dump(O/'reviews/documentation_update.json',dict(status='UPDATED',timestamp=time.time(),files=[identity(R/x) for x in ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/17_gt10_shared_transform.md','experiment_history/README.md']]))
 print('E28 report/history/root documents synchronized')
if __name__=='__main__':main()
