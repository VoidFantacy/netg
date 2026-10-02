from common import *
d=read(O/'results/diagnosis.json');ss=d['contexts'];v=read(O/'reviews/independent_verification.json')
assert v['status']=='PASS'
rel=O.relative_to(R).as_posix();status='COMPLETE_PAYOFF_ATTRIBUTION_LOCAL_OPPORTUNITY_WITH_CANCELLATION'
actions=list(csv.DictReader((O/'results/actions.csv').open()));events=list(csv.DictReader((O/'results/entry_events.csv').open()))
labels=['WebVid / 初始化','WebVid / 已选点','Yandex / 初始化','Yandex / 已选点']
table='| 固定点 | 有可获益query / 1024 | 九配置逐query上界 ΔR pp | 单一配置最佳 ΔR pp | 最佳配置增益−损伤（命中数） |\n|---|---:|---:|---:|---:|\n'
for s,label in zip(ss,labels):
 table+=f"| {label} | {s['positive_queries']} | +{s['ceiling_pp']:.4f} | +{s['best_static_pp']:.4f} | {s['best_static_gain']}−{s['best_static_loss']}={s['best_static_net_hits']} |\n"
conclusion='现有局部动作有非零但稀疏的改进空间；收益分散与正负抵消同时存在。32个全局扰动均帮助一部分query、损伤另一部分，单一已测配置仅保留有限逐query上界的0%–23%。这支持停止给同一全局扰动训练器加预算，先定位联动损伤；它尚未证明共享参数表示在数学上无法兼顾这些query。'
gap='| 固定点 | 逐query上界−最佳静态净增益 | 未覆盖收益 | 最佳静态实际损伤 |\n|---|---:|---:|---:|\n'
for s,label in zip(ss,labels):gap+=f"| {label} | {s['ceiling_static_gap']} | {s['uncovered_gain']} | {s['collateral_loss']} |\n"
pairtable='| 固定点 | 全池最近5邻居中双方可获益的pair | 无共同改善动作的pair | pair cosine中位数 |\n|---|---:|---:|---:|\n'
for s,label in zip(ss,labels):
 p=s['pair_preferences']['nearest5_all'];pairtable+=f"| {label} | {p['pairs']} | {p['improvement_incompatible']} | {p['median_query_cosine']:.3f} |\n"
cases=[]
all_groups=list(csv.DictReader((O/'results/transition_groups.csv').open()))
for ds in DS:
 candidates=[]
 for row in all_groups:
  if row['dataset']==ds and row['kind']=='added_hub' and int(row['helped'])>0 and int(row['harmed'])>0:
   g=dict(row)
   for key in ['events','unique_queries','helped','harmed','gross_gain','loss','closest_positive_row','closest_negative_row']:g[key]=int(g[key])
   g['closest_conflict_cosine']=float(g['closest_conflict_cosine']);candidates.append(g)
 # Prefer the selected context when a mixed added-hub group exists; otherwise use initialization.
 chosen_pool=[g for g in candidates if g['context']=='selected'] or candidates
 g=sorted(chosen_pool,key=lambda g:(-min(g['gross_gain'],g['loss']),-g['closest_conflict_cosine'],g['action'],int(g['key'])))[0]
 observed=[e for e in events if e['dataset']==ds and e['context']==g['context'] and e['action']==g['action']
           and int(e['row']) in [g['closest_positive_row'],g['closest_negative_row']]]
 assert len(observed)==2 and all(g['key'] in e['added'].split(';') for e in observed)
 cases.append(dict(dataset=ds,context=g['context'],action=g['action'],hub=int(g['key']),
                   group=g,observations=observed))
dump(O/'results/attribution_cases.json',dict(selection_rule='selected context if mixed added hub exists, otherwise zero; max min(gain,loss), max conflict cosine, action and hub ties',cases=cases))
case_text='# 可追溯入口关联实例\n\n以下为事后从全部混合新增hub组选择的机制案例，非独立验证，也不是相同完整交换。选择规则及原行见[JSON](results/attribution_cases.json)。\n'
for c in cases:
 case_text+=f"\n## {c['dataset']} / {c['context']} / {c['action']} / 新增hub {c['hub']}\n\n两条query的cosine为{c['group']['closest_conflict_cosine']:.6f}；其余删除/保留入口不同。\n\n| E37 train行 | 原始source行 | 中心三入口 | 动作三入口 | hits变化 | 几何边界变化 |\n|---|---:|---|---|---:|---:|\n"
 for e in c['observations']:
  case_text+=f"| {e['row']} | {e['source_row_id']} | {e['center_entries']} | {e['action_entries']} | {e['center_hits']}→{e['action_hits']} | {float(e['center_margin']):.6f}→{float(e['action_margin']):.6f} |\n"
case_text+='\n这些观测不隔离目标hub画像、其它画像或普通HNSW重建的影响；不能将某个新增hub标签直接标成普遍好/坏，也不能把完整三入口效果分配成独立单入口标签。\n'
(O/'cases.md').write_text(case_text)
next_control='''## 唯一优先接续：目标入口画像与其余画像的2×2隔离

本轮只设计、不执行。E40发现混合新增hub关联，但没有相同完整交换的正负重复证据；缺的是“只动这个画像会怎样”的真实反事实，继续重复缓存求上界不能回答它。

从E40已存attribution_cases锁定每集一个案例：优先已选点，若无混合新增hub组则回到初始化；按min(总增益,总损伤)、正负query cosine及确定ties排序。该选择使用已有GT，属于机制案例选择，不可包装为无偏验证。两集案例身份、正负source rows必须在任何新查询前冻结，不再按新结果回选。

对每案例建立四份静态画像：C=全中心；F=原完整扰动；S=只有目标hub这一行取扰动值，其余取中心；R=目标hub取中心、其余取扰动。每一行都复制已有单位float32画像，不训练、插值或新采样；四份均按原参数普通重建HNSW，保持H/真实ID/原NSG/IP/L128。S/R一般不属于原共享变换的可达像，因此是隔离干预，不称原RL新checkpoint。

复用原1024名单，各格完整报告gain/loss/net及案例query，比较F−S−R+C的逐query交互。若S保留指定正例改善同时消除负例损伤，支持其它画像联动对该案例损伤有贡献；若S自身复现损伤，则不能靠只隔离其余画像解释它。R另检查其它画像单独作用。整个1024池的新增损伤必须计入，不能只看两条选中案例。

两个数据集×4格×1024=8192正常NSG；每图16条count/plain/original核验另384，预计8576、建议硬上限10000，8次普通构图、0optimizer、新GT/validation/held-out为0、无QPS。C/F必须恢复E39原输出，新增S/R不能假称已有NSG标签。该调用账是待冻结建议，当前实际新增调用仍0。新版本先落实输入SHA、单线程CPU15、拒绝覆盖和失败完整预留再执行。

这是画像联动的局部因果控制，普通重建可能同时改变评分与邻接，不能单独归因为HNSW访问或证明全部共享表示不足；不由个案GO直接扩自由W训练。若两格隔离没有保留收益/减少损伤，则停止该局部拆分方向；若有信号，再按固定真实预算设计一项训练修订及非RL控制。当前没有新任务排队。
'''
(O/'next_control.md').write_text(next_control)
history_review='''# 接续前的旧表示路线复核

本轮完整阅读历史11、17–21，并核对当前spec相应合同及原源码/协议的目标部分，没有运行旧脚本、解码其原评估输入或重做模型。

- E22 [详细11](../../experiment_history/11_ab_fixed_slot_exploration.md)：自由低秩W加可学习mapping已做过，原[src/train.py](../20260909_ab_experiment_v1/src/train.py)使用效用软遗憾；映射与画像作用不能混为共享低秩的因果证据。
- E28 [详细17](../../experiment_history/17_gt10_shared_transform.md)：[原train.py](../20260911_gt10_shared_transform_v1/src/train.py)明确实现独立H×d的free delta及共享linear/MLP，normalize后静态部署。存在free参考不能证明原共享模型容量是失败主因。
- E29 [详细18](../../experiment_history/18_teacher_objective_alignment.md)：教师/目标2×2与原画像保留控制仍是全局拟合；未隔离某个新增hub画像与其余画像。
- E30 [详细19](../../experiment_history/19_equivalent_teacher_sets.md)及[原协议](../20260911_equivalent_teacher_sets_v1/protocol.md)：等价完整集合及平均位移匹配不匹配逐hub方向，更不等于单hub反事实。
- E31 [详细20](../../experiment_history/20_training_effectiveness.md)及[原协议](../20260911_training_effectiveness_v1/protocol.md)：同表示/教师只改优化日程，未验证新增局部自由度。
- E32 [详细21](../../experiment_history/21_direct_reward_policy.md)及[原train.py](../20260911_direct_reward_policy_v1/src/train.py)：已有真实收益与完整动作目标，不能简单以“改为直接reward”换名复跑。

所提2×2只复制既有W的行以定位局部联动，区别于旧全局训练，也不声称新模型族或新性能方法。本轮只读复核；更完整的新训练选择仍须追溯旧协议/实现/结果，不能因个案通过直接扩模型。
'''
(O/'historical_review.md').write_text(history_review)
report=f'''# E40 既有画像动作收益与损伤归因

2026-09-12。状态`{status}`。[协议](protocol.md)、[原始统计](results/diagnosis.json)、[独立核验](reviews/independent_verification.json)、[最终验收](reviews/final_audit.json)。本轮完成用户要求的既有反馈归因，新增NSG/HNSW/构图/训练/GT全部0。

## 判断

{conclusion}

{table}

全部差值相对各自确定中心，九配置是本参数点的八个原扰动加中心。表中最佳是同池事后诊断，未部署、未改变E37 cal选择；逐query最佳有GT信息，不可免费实现。不能将0.41–0.93pp称为当前所有画像/入口的空间上界，只是这九配置的已测范围。样本有历史训练暴露，无新泛化测试。

## 局部空间有多少，哪里被抵消

可获益query仅1.46%–3.42%，有限上界只覆盖中心剩余漏检的1.70%–6.77%。因此它既不是“零空间”，也不是多数query都有可用改进。6508次action-query入口变化中，6037次（约92.76%）没有改变命中数；26260次相同入口的NSG IDs/距离bits/graph NDC完全一致。

令O为逐query已测最佳总增益，B为最佳静态净增益，G/L为该静态动作的正收益/损伤。O−B=(O−G)+L，前项是没有覆盖到的收益，后项才是损伤；不能把整段差距全部称为表示冲突。

{gap}

单位为命中数，除以1024×10后换成Recall。WebVid初始化差距76中54来自未覆盖、22来自损伤；Yandex初始化51=30+21，已选点53=26+27。三个有正净收益的最佳动作，损伤分别吞掉其gross gain的53.7%/58.3%/64.3%。WebVid已选点最佳为保持中心，因此42=42+0只是该静态最优的恒等分解，不能说此处没有扰动损伤：八扰动全部净负，最好action0也仅增加9命中却损失20，净−11；八动作平均增加12.25、损失42.25，净−30。

四点各八动作都正负共存；逐query在不同动作下既正又负的却只有0/1/0/0条，说明相对中心，观测冲突主要发生在不同query之间。首512择优的动作在另一半分别净−22/−34/−11/−5命中；反向择优则为+13/0/+3/+8。方向不对称与历史暴露都保留，不能挑一半当泛化结论。

## 能否定位为相同入口的硬冲突

按同动作+同移除/新增hub的单交换分组，共5879组，观察到正负共存组0；同动作+完整三入口转移6502组，正负共存也0。单交换仅5953条事件，绝大部分组只有一个query，故缺少重复支持，不能把0当没有冲突的证据。

放宽为同动作新增同一hub时，四点有4/12/3/0组正负共存；移除同hub为10/6/2/0组。其它移除/保留入口常常不同，且一个全局动作同时改变全部画像，所以这些只是入口参与关联。[两个可追溯案例](cases.md)及其完整source行/入口/得分见[JSON](results/attribution_cases.json)。不把联合收益平均摊成单hub标签，不凭最终入口编造HNSW访问路径。

单交换有4852/5953次（81.51%）在float64离线几何重算中跨过新旧入口得分边界，5414/5953次（90.95%）动作下新增入口得分更高。这说明画像得分变化与多数入口交换相符；没有隔离小图重建，也没有访问trace，不能据此把剩余交换全部归为ANN错误。

## 相似query的动作偏好

{pairtable}

这是整个1024池每query最近5邻居的对称并集，再观察双方均可获益的有限pair；13/7/5/4条很少，不能声称系统性的语义群冲突。另在可获益子集内部定义最近5并保留全部1161个pair，约42%–61%的该子集邻居pair没有共同改善动作，但它是GT条件化子集、相对相似性且pair相关。无共同动作只针对已测九配置，不证明任意连续共享参数无法兼顾。

## 成本、核验与历史

新增搜索/构图/optimizer/GT为0。主分析单线程CPU8，约{d['seconds']:.3f}s、RSS约{d['peak_RSS_KiB']/1024:.1f}MiB，另独立评分约{v['seconds']:.3f}s；不含编写、保护hash、绘图/阅读，也不是QPS。离线query cosine矩阵有2097152个有序元素计算，属于缓存几何分析，不是ANN查询。E39此前实际38592次NSG的取得成本保留，不重算成免费标签。

独立集合评分36864输出、四点精确G/L/O/B分解、36动作、6508入口事件及13016个标量得分边界、23369分组、1161偏好pair全部复核；另核验10240条最近query关系。E37/E38/E39整目录前后SHA保护，未读取/hash新的原validation/held-out，未改变模型/默认。原根文档前件保存。历史自由W/共享表示/目标路线已复核，见[旧方法审阅](historical_review.md)，不直接以容量或换reward重启。

[动作表](results/actions.csv)、[query表](results/queries.csv)、[入口事件](results/entry_events.csv)、[交换/参与分组](results/transition_groups.csv)、[query pairs](results/query_pairs.csv)、[收益图](figures/payoff_gap.svg)、[32动作正负图](figures/action_gain_loss.svg)。

{next_control}

## 实际分析命令

独立目录已冻结，脚本拒绝覆盖；重新分析须建立新版本。实际使用以下环境串行运行src/prepare.py、analyze.py、verify.py、verify_neighbors.py、plot.py，日志保存在logs；没有执行上游runner：

```bash
env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 taskset -c 8 timeout 600 .venv_cpu/bin/python {rel}/src/analyze.py
```
'''
(O/'report.md').write_text(report)
(O/'conclusion.md').write_text(conclusion+'\n\n'+table)
card=f'''# 29. E40 已有画像动作的收益、损伤与入口归因

2026-09-12，状态`{status}`。[报告](../{rel}/report.md)、[协议](../{rel}/protocol.md)、[验收](../{rel}/reviews/final_audit.json)。用户要求继续分析E39已有动作，区分局部空间和不同query冲突；本次没有新搜索/构图/训练。

## 输入、定义与结论

四个E39固定参数点各八扰动+中心、相同1024训练query，原H/画像/ID/NSG/raw-IP/L128不变。仅从原输出集合评分和画像字节重算，主要参照各自中心。G为正Δhits之和、L为负Δhits绝对值，O为九已测配置逐query最大增益、B为最佳单一静态配置净增益；O−B=(O−G_best)+L_best。原GT10只用于奖励分母/旧返回回归，不混作各点中心。

{conclusion}

{table}

逐query上界非全画像空间上界、非部署/泛化结果；只覆盖中心剩余漏检1.70%–6.77%。单一最佳动作未覆盖的收益和实际损伤分别为54/22、42/0、30/21、26/27个命中。WebVid已选最佳为中心，其余八动作全负，最好也增加9损失20，不能由中心loss0推断没有扰动损伤。

## 机制与限制

32扰动全部有正负query；跨query抵消有直接证据，但同query正负俱有仅0/1/0/0。6508次入口变化约92.76%未改命中。单交换5953事件/5879组，完整转移6502组，均未观察到相同动作+相同交换的正负重复；大多数只有单条query，不支持证明硬冲突或证明没有冲突。同动作新增某hub有4/12/3/0个混合组，移除有10/6/2/0个；其它入口同时变化，需[隔离案例](../{rel}/cases.md)反事实，不能分配单hub因果标签。

全1024池最近5中双方可获益的pair仅13/7/5/4，其中5/4/3/1没有共同改善动作；在有收益子集最近5的比例更高但GT条件化。相似性是有限样本内cosine，不等同语义类。单交换81.51%跨几何边界、90.95%动作下新增分数更高；不含HNSW访问trace，不能把余项当ANN错误。

## 执行、保护与接续

主分析CPU8/实际线程1约{d['seconds']:.3f}s、RSS约{d['peak_RSS_KiB']/1024:.1f}MiB；独立集合评分36864条，13016得分边界、23369分组、1161pair及最近query关系复核通过。所有新NSG/HNSW/构图/optimizer/GT均0；旧E37/E38/E39保护SHA与根文档前件保留，无新的原validation/held-out访问。E39标签取得的38592次真实NSG成本不能省略，诊断时间不是QPS。

下一步唯一优先为同一固定动作的目标hub/其它hub 2×2隔离：中心、全扰动、仅目标行、仅其余行，真实重建普通HNSW并全1024计入损伤；约8576次NSG/硬限10000是未执行建议。它区分局部画像与其余画像联动，仍不隔离评分与拓扑，也不升级free-W训练。旧自由表示/目标路线的[复核](../{rel}/historical_review.md)保留；新控制尚无构图/搜索或任务排队，默认/E37开发门保持。详见[s-target](../s-target.md)。

[完整动作](../{rel}/results/actions.csv)、[逐query](../{rel}/results/queries.csv)、[入口事件](../{rel}/results/entry_events.csv)、[有限上界图](../{rel}/figures/payoff_gap.svg)。
'''
(R/'experiment_history/29_profile_payoff_attribution.md').write_text(card)
p=R/'s-experiment.md';text=p.read_text();assert '| E40 ' not in text
text=text.replace('| E39 ',f'| E40 画像动作收益损伤归因 | 对E39九配置逐query上界、单一最佳、覆盖/损伤分解及入口/相似query关联；全部缓存复算 | `{status}`；局部机会稀疏、正负抵消明确，未证共享表示硬冲突；0新搜索/训练 | [29 收益损伤](experiment_history/29_profile_payoff_attribution.md) |\n| E39 ',1)
text=text.replace('最近完成记录已为E39诊断','最近完成记录已为E40诊断').replace('二十八份详细卡片','二十九份详细卡片');p.write_text(text)
p=R/'experiment_history/README.md';text=p.read_text();line='| [28 固定参数批次诊断](28_fixed_profile_batch_diagnosis.md) | E39：固定双集两μ/八扰动，另取1024训练query，四点512方向全负，0更新并停止预算扩大 |'
assert line in text;p.write_text(text.replace(line,line+'\n| [29 画像收益与损伤](29_profile_payoff_attribution.md) | E40：已有动作有限上界/静态最佳差距、覆盖与损伤分解、入口变化及query偏好，0新搜索 |'))
(R/'summary.md').write_text(f'''# ACSG 当前结果摘要

2026-09-12。最近完成E40已有画像动作收益损伤归因，状态`{status}`。[报告]({rel}/report.md)、[历史29](experiment_history/29_profile_payoff_attribution.md)、[验收]({rel}/reviews/final_audit.json)。E39仍是最近新搜索，E37仍是最近训练/完整性能评测；默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。

## 当前判断

{conclusion}

{table}

数值均相对各固定点确定中心。上界和最佳只针对原八扰动+中心，使用历史训练query的GT，不是部署选择或新泛化结果。可获益query仅15–35/1024；九配置只能恢复中心剩余漏检的1.70%–6.77%，局部机会有限但非零。

三个有正净收益的最佳扰动分别增加41/36/42个命中，同时损失22/21/27个；WebVid已选点八扰动全负，最佳为保持中心，最好的扰动也仅增加9却损失20。有限上界到静态最佳的差距同时包括未覆盖收益和实际损伤，不能全归为表示冲突。[完整增益损伤图]({rel}/figures/action_gain_loss.svg)。

同一全局动作对不同query产生正负有直接证据；但同动作/同入口交换的正负重复实例为0，5953单交换事件分成5879组，重复支持很少。同hub新增/移除的混合关联存在，但其它入口与画像也变化；相似query证据也稀疏，尚未识别共享参数化的不可兼容性。约92.76%的入口变化未改变命中，不从最终输出推断HNSW访问路径。

## 实际执行与边界

0新NSG/HNSW/构图/optimizer/GT；独立复核36864既有返回、6508入口事件、13016离线得分边界、23369分组和1161query pair。主分析实际单线程约{d['seconds']:.3f}s、RSS约{d['peak_RSS_KiB']/1024:.1f}MiB，不含编写/保护hash/绘图或阅读，不能当QPS。E37/E38/E39整目录SHA保持，根文档前件保存，无新的原validation/held-out读取/hash。

E39四点512-query方向稳定门仍全部失败；E37主RL开发门仍停止，cal/audit变化为WebVid−0.1172/−0.0391pp、Yandex−0.0195/+0.0391pp，L128 QPS约+0.069%/+0.078%。E24 GT10、E36局部正信号保留，没有新默认替换。

下一步设计为目标入口画像与其余画像的2×2隔离，以原画像行拼出静态反事实，检验损伤是否来自其它画像联动；不是再训练自由W或增加epoch。该控制尚未执行，预计8576次NSG、建议硬限10000、0optimizer，详见[s-target](s-target.md)。无排队任务。
''')
(R/'s-target.md').write_text(f'''# ACSG 下一阶段目标与接续

2026-09-12。E40已有动作收益损伤归因已完成，状态`{status}`。[当前结果](summary.md)、[历史29](experiment_history/29_profile_payoff_attribution.md)、[报告]({rel}/report.md)。不重复E38/E39/E40旧分析或runner。

## 主目标与证据

用户主目标继续为离线学习静态入口画像或小图，在线普通HNSW→原NSG。E37已实现部署形式；E39没有稳定的批次梯度，E40进一步看到有限动作有0.41–0.93pp逐query空间，但共用一份已测配置只保留0–0.19pp。局部机会稀疏、未覆盖收益和正负损伤并存；共享表示硬冲突尚未证明。

32扰动全部正负共存，但相同完整交换的重复非常少，没有正负共存实例。同hub关联与query相似性不足以识别因果；下一步要回答只改一个目标画像/只改其余画像分别怎样，继续增加batch、epoch或缓存oracle不会补上这个证据。

{next_control}

## 第二优先：隔离信号成立后才设计训练修订

E22自由低秩/mapping、E28 free/linear/MLP、E29目标2×2、E30等价教师、E31优化日程和E32真实收益均已由历史11/17–21复盘，本轮核对相关原源码/协议，见[审阅]({rel}/historical_review.md)。不能简单重启自由W或换reward。2×2案例不是新learner，按其结果仅允许提出一个有针对性的动作自由度/损伤控制修订，再建立同表示/同真实调用预算的非RL控制与独立开发门。

训练继续锚定原画像、固定H/真实ID/大NSG/IP和普通在线HNSW，原画像恢复/成本完整记账。是否减少损伤必须连同保留收益、其它query新损伤和完整Recall–QPS一起判断；禁止只优化被选案例、按训练上界替换默认。新训练没有协议冻结、实现或排队。

## 第三优先：小图构造仍是独立备选

E40没有HNSW访问trace，画像行干预也会自然改变重建邻接；若后续证据指向访问覆盖/效率，另做评分固定与图变化的控制，不能将画像效应归给图。E33删边/E34成本/E35已评分漏选边界保持；不直接扩邻居、改大图或重启旧runner。

## 接续状态与启动指令

E40的收益/损伤和入口归因已执行验收，0新搜索；目标hub与其余画像2×2仍是设计未运行。历史记录、默认、E37开发门保持，无排队任务。

> 在/data/netg/ACSG完整阅读AGENTS.md、summary.md、spec.md、s-target.md、s-experiment.md，再由历史29读取E40协议、完整四点结果、cases.md及独立验收，并核对E39原冻结W/行名单。不要重复缓存上界分析。审查目标hub与其余画像的2×2隔离控制，以E40固定案例建立新版本/协议，落实正常8192+parity384、建议硬限10000、CPU15单线程和原C/F回归；只进行获授权的局部反事实控制，不自动重训、改默认或读新的validation/held-out。
''')
p=R/'spec.md';text=p.read_text().replace('E39固定参数批次诊断已验收；E37部署及原Fast/NSG kernel不变','E40既有动作归因已验收；E37部署及原Fast/NSG kernel不变')
text+=f'''

## 既有画像动作收益与入口归因（E40，2026-09-12）

[协议]({rel}/protocol.md)及独立[analyze.py]({rel}/src/analyze.py)不导入上游native/train/runner，仅用E39已有36配置W、完整返回、原训练query/GT与E37同源基线。每点原八动作+中心，aligned Δhits以当前确定中心为参照；原U/NDC分母仍用E37anchor。逐query有限O与静态最佳B满足O−B=(O−G_best)+L_best，best ties先中心后原动作序号；该事后统计不导出新模型。

输出actions/queries/entry_events/transition_groups/query_pairs/query_neighbors CSV、aligned NPZ和JSON。入口事件保留完整三元组/新增/移除/source row，单/多交换分开，重复参与hub不拆成独立收益。已存W与unit query的float64得分边界仅为离线几何诊断，不模拟HNSW路径或声称SIMD逐位parity。query-query dense cosine/最近5只是已有向量分析，不调用ANN；有收益子集邻居明确GT条件化。

[独立核验]({rel}/src/verify.py)以集合交集、逐query循环/精确恒等式和标量内积重算36864返回、36动作、6508事件、13016边界、23369分组/1161pair；[邻居复核]({rel}/src/verify_neighbors.py)检查10240关系与pair资格。所有新搜索/构图/optimizer/GT为0，E37/E38/E39整目录SHA保持，根文档前件独立保存。派生分析变更只重做缓存统计；目标hub/其余画像2×2目前仅为s-target设计，未生成反事实W/图或标签。结论见[summary](summary.md)/[历史29](experiment_history/29_profile_payoff_attribution.md)。
''';p.write_text(text)
print('Report, cases, next control, historical review, history29 and root documents written.')
