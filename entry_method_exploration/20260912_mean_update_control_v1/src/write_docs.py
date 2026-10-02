from shared import *
import re
threads(8);assert read(O/'reviews/verification.json')['status']=='PASS'
rr=read(O/'results/analysis.json');gate=read(O/'results/gate.json');assert gate['status']=='PASS_FULL_FEEDBACK_SINGLE_STEP_RESEARCH_GATE'
status='COMPLETE_MEAN_UPDATE_CONTROL_SMALL_FULL_FEEDBACK_SIGNAL'
tab='''| 数据集 | 原batch单步G/L/净 | 全池单步G/L/净 | 全池相对原步G/L/净 | 全池正/负状态数 | 全池平均ΔU | 全池graph NDC变化 |
|---|---:|---:|---:|---:|---:|---:|
'''
for d,name in zip(rr['datasets'],['WebVid','Yandex']):
 fmt=lambda tag:f'{d[tag+"_gain_hits"]}/{d[tag+"_loss_hits"]}/{d[tag+"_net_hits"]:+d}'
 tab+=f'| {name} | {fmt("batch")} | {fmt("full")} | {fmt("full_vs_batch")} | {d["full_positive_contexts"]}/{d["full_negative_contexts"]} | {d["full_mean_delta_U"]:.8f} | {d["full_graph_NDC_change_pct"]:+.5f}% |\n'
finding='''完整训练反馈在同状态单步中产生小正值，不能把它写成训练已成功。WebVid在step60新增1个命中、无新增损伤；Yandex在step40两种更新都增加3个命中，在step100原batch更新损失5而全池更新没有损伤。因而全池相对原步分别+1/+5，而不是Yandex额外获得3个新收益。两集各9/10全池单步命中不变，局部响应依然稀疏。

新旧画像行的平均位移基本同量级：WebVid约0.00346/0.00347、Yandex约0.00306/0.00317。这里改变的是由反馈决定的更新方向/坐标，不是扩大扰动半径或步长。原八采样动作在WebVid7个/Yandex3个状态有正收益，但确定全池单步各只有1个正状态；不能用候选收益代替均值更新收益，也不能断言所有差距都由采样噪声造成。

上述G/L及净值按10个互不传递的context累加，仅作诊断，不能拼成一个部署模型的Recall；每处正信号只涉及一个query。预锁单步门双集通过，允许继续研究可支付的完整反馈，不允许直接宣布RL优势、泛化或性能GO。E44原入口分层失败不被翻案，也不按此结果调分层名额。
'''
next_text='''下一目标是精确反馈复用的实现与成本验收。原NSG只消费raw query和三个已排序真实入口，在query/L/K/metric/原图/kernel相同且三入口逐位相同时，复用已有完整ID/距离/graph NDC；HNSW仍须真实查询全部4096，并按当前图支付route NDC。只有入口变化的query重新运行原NSG，不能把未测变化填0。

E44已有80候选/集共327680 candidate-query配对中，入口变化仅WebVid971、Yandex362（事后预算线索，不是已测加速）。必须实现独立的route-only与显式三入口NSG接口，恢复全部原始输出/奖励/梯度，实测实际路由/构图/新NSG和复用成本；初始完整反馈费用单列，不能藏在cache里。该后继E46尚未实现或查询，先验收再按剩余时间决定是否开新的全池反馈训练版本。'''
body=f'''# E45 确定均值单步的完整反馈控制

2026-09-12，`{status}`，`{gate['status']}`。完整反馈保留小的无损单步信号，多数确定更新仍无质量响应。

{tab}
{finding}
## 固定控制

全部沿用E44预锁20状态：E43 RL第一seed step20/40/…/200动作前W/μ/m/v/count及原八方向。由完整checkpoint与中间行更新恢复状态，原Adam/next_row全部逐位恢复。N_full只用E44全4096条件梯度替代原128梯度，原σ.3、cosine步长、clip、Adam局部计数和P/B/尺度不变；仅目标画像行变化，其余行复制当前W字节。

每context独立计算一次新反事实单步，不向下一个context传递；新反事实20，原单步回放20，连续训练0。完整梯度只消除固定八方向的query采样误差，不是离散检索目标解析梯度。GT只作返回后评分，没有新方向、候选选优或步长网格。

当前C复用E44完整raw，每context新build/run16/物理图三路parity恢复身份；N_batch/N_full各真实run4096并16条三路parity。所有60图保存完整拓扑、物理图与身份，40完整更新raw及20当前恢复raw保留。两种更新均报告全池收益/损伤/零命中/U/J/route和graph NDC，漂移计入J。

## 成本和验收

167040 NSG=164160正常新查询+2880三路parity，166080 HNSW、60构图；当前81920行完整结果复用E44已支付反馈。两query进程共92.652s，含加载/构图/计数/写盘/parity，不是QPS；CPU15实际进程/OMP/BLAS/MKL1，双集串行。没有新GT/monitor/cal/audit/validation/held-out/QPS。

独立集合评分245760条完整返回（其中81920复用当前），核验320当前bit回归、960条三路parity、60图/W/topology、40次逐坐标Adam（20历史+20新）、全池梯度身份与原/新行构造；E37–E44和原native/NSG SHA、query前冻结保持。新近完整snapshot使用E44 final_artifact_freeze_v2，首版日志竞争说明与原件都保留。

## 接续与边界

{next_text}

默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。E43监控门失败、E44分层失败、旧局部正值与条件责任全部保留。阶段完成不结束20:00持续研究目标。

[协议](protocol.md)、[冻结配置](config.locked.json)、[状态表](results/contexts.csv)、[门](results/gate.json)、[成本](results/cost.json)、[独立核验](reviews/verification.json)、[图](figures/mean_update_control.svg)。
'''
(O/'report.md').write_text(body);(O/'conclusion.md').write_text(finding+'\n'+next_text+'\n')
dump(O/'reviews/visual_review.json',dict(status='PASS',files=['figures/mean_update_control.png'],method='Viewed PNG; actual net hits and sampled best control clearly separated'))
hist=body.replace('# E45 确定均值单步的完整反馈控制','# 34. E45 同状态确定单步完整反馈控制');hist=re.sub(r'\]\(([^)]+)\)',lambda m:'](../entry_method_exploration/20260912_mean_update_control_v1/'+m.group(1)+')',hist)
(R/'experiment_history/34_mean_update_control.md').write_text(hist)
p=R/'s-experiment.md';s=p.read_text();i=s.index('| E44 局部动作全池/采样诊断');s=s[:i]+'| E45 确定均值单步完整反馈 | 固定20状态只替换原八方向的query梯度，原/全确定行真实全池查询 | `COMPLETE_MEAN_UPDATE_CONTROL_SMALL_FULL_FEEDBACK_SIGNAL`；WebVid净0→+1、Yandex−2→+3，小正值/避损；167040 NSG、20独立反事实步，0连续训练 | [34 确定单步](experiment_history/34_mean_update_control.md) |\n'+s[i:];s=s.replace('三十三份详细卡片','三十四份详细卡片');p.write_text(s)
p=R/'experiment_history/README.md';s=p.read_text();s+='\n- [34 确定均值单步控制](34_mean_update_control.md)：E45完整反馈的小正值和避损，多数更新仍质量不变，进入精确反馈复用可行性验收。\n';p.write_text(s)
(R/'summary.md').write_text(f'''# ACSG 当前结果摘要

2026-09-12，最近完成E45，`{status}`，门`{gate['status']}`。[报告](entry_method_exploration/20260912_mean_update_control_v1/report.md)、[历史34](experiment_history/34_mean_update_control.md)、[核验](entry_method_exploration/20260912_mean_update_control_v1/reviews/verification.json)。20:00持续研究目标继续，默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。

{tab}
{finding}
167040 NSG、166080 HNSW、60构图；新反事实单步20、历史回放20、连续训练0。245760完整集合评分/320原结果恢复/960三路parity/40 Adam计算及全部图身份通过；CPU15实际单线程、数据集串行，无新GT/开发/QPS。E37–E44原件保留。

E44全池WebVid9/10状态有命中响应、原batch1/10，Yandex3/10与0；原入口分层方差比1.074/0.978未过门。收益损伤多数在补集，不能把原入口相关组当完整影响集。E43 WebVid ES+0.0781pp局部正值保留，Yandex未过monitor门；无RL额外优势。最近完整Recall–QPS仍E37。

{next_text} 详细接续见[s-target](s-target.md)。
''')
(R/'s-target.md').write_text(f'''# ACSG 下一阶段目标与接续

2026-09-12，E45同状态确定单步已完成，[历史34](experiment_history/34_mean_update_control.md)、[报告](entry_method_exploration/20260912_mean_update_control_v1/report.md)。用户授权持续推进至北京时间20:00，总目标继续。

## 证据与首要问题

完整反馈使WebVid净0→+1、Yandex−2→+3，后者主要避免原步5个命中损伤，均未扩大步长。两集各9/10更新质量不变，每处正点仅一query，单步门通过不等于训练/泛化/性能GO。E44原入口分层仍停止，不扫近组名额。

{next_text}

## E46最小实现与恢复门，待独立预锁

沿用E44全部20固定context和原C+八候选。各图真实route全部4096，逐位核验真实三个入口及route NDC；相对对应C三入口不变则复用原NSG返回/距离/graph NDC，变化才调用原NSG。只有query与完整真实三入口/L/K/metric/原图/kernel都匹配才能复用；原HNSW路由费用不复用或隐去。

新增接口放独立版本，包含原E37 environment，不改原kernel/库/旧binary。验证全737280返回五字段与E44完全一致、奖励/条件梯度一致、所有复用有准确入口身份，新搜索记录实际调用。代表图仍原count/plain/kernel parity；按冻结全部状态计费，失败完整预留，不能按收益筛query。当前C种子原完整反馈费用明确列出；未来训练每次均值更新也须真实route并补齐变化query，不能长期使用过期C。

恢复门为全量bit一致；成本门须实际NSG占原完整调用≤10%，报告新增route/build/查表/复制/序列化费用，并保守估算原两臂双seed200步能否在19:35前完成且留出核验时间。若可行，另建唯一全池反馈训练版本，原局部参数化/方向σ/步数/两臂/monitor门保持；若不可行，不启动注定超时任务，转缓存机制分析。

## 次优先与截止

画像评分与邻接重建2×2隔离、有限动作收益覆盖/损伤结构保留为后续优先，不据这两个单query小正值扩模型/幅度网格。完整反馈的方向噪声和每hub暴露仍未排除。19:35后不训，19:40后不查询，20:00收口；不因观察超时重启。默认及E37–E45原件保持，E45两query进程已采集exit0。

> 读四主文档及AGENTS，从历史34进入原始单步控制和门。不要重训E43或复活E44分层；下一步独立实现原NSG完整三入口精确反馈复用，逐位恢复全部E44结果并测实际费用，再按剩余时间判断是否执行新的全池反馈训练。
''')
p=R/'spec.md';s=p.read_text().replace('E44全池采样诊断已验收','E45确定均值单步控制已验收');s+='''

## 同状态确定均值单步完整反馈控制（E45，已验收）

[协议](entry_method_exploration/20260912_mean_update_control_v1/protocol.md)固定E44原20状态、原八ε和E43局部表示/Adam参数。[prepare.py](entry_method_exploration/20260912_mean_update_control_v1/src/prepare.py)逐行恢复μ/m/v/count，原batch梯度生成原next_row需逐位相同，再只用E44全4096条件梯度替换g生成一行。20个新反事实步互不传递，原回放20、连续训练0；输入/两行参数/画像/W来源hash全部冻结。

[run.py](entry_method_exploration/20260912_mean_update_control_v1/src/run.py)仍复用E37原native，C run16恢复E44，其完整4096缓存明确复用；batch/full各完整run4096，全部60图保存物理图/拓扑并16query三路parity。实际167040 NSG/166080 HNSW/60图，CPU15实际1线程。没有新增线上Policy或NSG复用API。

[独立核验](entry_method_exploration/20260912_mean_update_control_v1/src/verify.py)完成245760完整集合评分（含81920当前复用）、320旧输出恢复、960条parity与40次逐坐标Adam/画像构造及图身份。[分析](entry_method_exploration/20260912_mean_update_control_v1/src/analyze.py)同时保存相对C和full−batch的全池G/L/U/J/NDC及位移；跨context累加只作诊断。后继route-only/精确三入口反馈复用尚未实现，不能写成现有能力。状态和效果由summary/历史34维护。
''';p.write_text(s)
dump(O/'state.json',dict(status=status,gate=gate['status'],NSG_calls=167040,counterfactual_single_steps=20,continuous_training_updates=0,campaign_complete=False))
print('E45 report/history/root docs synchronized',flush=True)
