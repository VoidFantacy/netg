from common import *

train=read(O/'results/analysis_tables.json');real=read(O/'results/deployment_tables.json');support=read(O/'results/reward_support.json')
short={DS[0]:'WebVid2.5M',DS[1]:'Yandex10M IP'}
budget=read(O/'models/training_budget.json');ver=read(O/'reviews/deployment_verification.json')
def table(fields,rows):
    return '\n'.join(['|'+'|'.join(fields)+'|','|'+'|'.join(['---']*len(fields))+'|']+['|'+'|'.join(map(str,row))+'|' for row in rows])
cached=[]
for ds in DS:
    ms={m['method']:m for m in train['cache_metrics'] if m['dataset']==ds and m['group']=='all'}
    p=next(x for x in train['paired_cache'] if x['dataset']==ds and x['method']=='reward' and x['reference']=='teacher' and x['group']=='all')
    cached.append([short[ds],f"{ms['anchor']['greedy_recall_pct']:.4f}%",f"{ms['teacher']['greedy_recall_pct']:.4f}%",f"{ms['reward']['greedy_recall_pct']:.4f}%",
        f"{ms['reward']['greedy_recall_pct']-ms['anchor']['greedy_recall_pct']:+.4f}",f"{p['greedy_delta_recall_pp']:+.4f}",f"[{p['ci95_low_pp']:+.4f},{p['ci95_high_pp']:+.4f}]"])
dev=[]
for ds in DS:
    default='gt10_soft' if ds==DS[0] else 'gt10_hard'
    for split in ['cal','audit']:
        a=next(x for x in real['real_paired'] if x['dataset']==ds and x['split']==split and x['method']=='reward' and x['reference']==default)
        t=next(x for x in real['real_paired'] if x['dataset']==ds and x['split']==split and x['method']=='reward' and x['reference']=='teacher')
        dev.append([short[ds],split,f"{t['delta_recall_pp']:+.4f}",f"{a['delta_recall_pp']:+.4f}",f"[{a['ci95_low_pp']:+.4f},{a['ci95_high_pp']:+.4f}]",f"{a['graph_ndc_change_pct']:+.3f}%",f"{a['total_ndc_change_pct']:+.2f}%"])
optimization=[]
for m in train['model_comparison']:
    optimization.append([short[m['dataset']],m['cell'],m['selected_epoch'],f"{m['initial_objective']:.6f}",f"{m['selected_objective']:.6f}",f"{m['objective_change_pct']:+.3f}%",f"{m['selected_drift']:.7f}"])
flat=[]
for ds in DS:
    r=next(x for x in support if x['dataset']==ds and x['group']=='constant_action_hits')
    flat.append([short[ds],r['queries'],f"{r['fraction']*100:.3f}%",f"{r['initial_teacher_loss_mass_fraction']*100:.2f}%",f"{r['initial_teacher_positive_loss_fraction']*100:.2f}%"])
text=f'''# E32：直接检索收益策略优化的有界实验

2026-09-11完成。状态`DIRECT_REWARD_POLICY_COMPLETE_FIT_GAIN_MIXED_DEVELOPMENT_STOP`。

**直接收益目标学出了比原教师目标更强的训练集检索信号，cal/audit相对教师四点均为正；但相对当前默认画像的四个开发点只有三个为正，且完整C8候选生成显著增加路由工作。本轮未通过预设开发门，不进入validation/QPS，不替换当前默认。** 这比“训练完全无收益”更具体，也尚不构成RL方法成功或图结构优化成功。

## 1. 实验做了什么

用户同意一次小规模“原教师目标 versus 直接真实检索收益”的对照。固定原raw-IP NSG、真实入口H、GT10-hard锚点、fit20K、原56组合标签和共享linear变换，只改变数据目标及预锁的初始梯度尺度。模型为`W=normalize(P+P A^T)`，`A=0`开始，`τ=.05`，锚定`100 mean_H ||W-P||²`。

每条query的动作是C8的56个完整三入口组合。C8由两个固定GT1-hard/GT10-hard Micro-HNSW direct3合并，再用原GT10-hard全H精确得分填充到8；完整动作按真实ID排序后调用原NSG。训练和本轮新部署都在同一个C8域，不复用单入口收益，也不把未知全H组合当作负标签。

teacher为E31并列G hinge：G包含最高hits中最低graph NDC的全部并列动作。reward为`β Eπ[(max hits-hits)/10]`，`π=softmax(F)`，`F`为三入口分数之和；减去每query最高收益只改变目标常数，梯度就是负期望Recall梯度。全部56个动作收益已知，因此使用精确枚举，不需要采样REINFORCE/PPO。本轮属于全信息上下文策略优化，没有多步状态转移、策略与环境反复采样训练或NSG/HNSW拓扑重连。

β只在A=0用fit数据匹配两组数据梯度范数，冻结为WebVid110.404375、Yandex91.075940；对应初始梯度方向余弦0.116457、−0.089516。两组共4次、各1200步，CPU8/float64/fullfit累积，Adam固定小步长warmup及cosine日程，同E31。每步记录期望/贪心Recall和graph NDC；在期望与贪心成本均不超各自初始化1%的点中，选本组fit总目标最低的最早点。没有用cal/audit、缓存Recall或QPS选迭代。

{table(['数据集','目标','选中步','初始总目标','选中总目标','相对本组初始','画像位移均方'],optimization)}

四组全部1201个含初始化的点都满足成本可行域。两个teacher的选中/末点A与W共8个文件逐位等于E31 multi；8个新选中/末点模型均通过独立NumPy恢复。两目标的绝对loss数值不可横向排名。reward最终位移约为teacher的5.22倍/3.61倍，初始梯度匹配不等于全程等位移或等有效正则；因此本轮对照不能把全部差异严格归因于目标语义一个因素。末段变化小和梯度小也不构成全局最优证明。

## 2. 训练集的真实标签收益

下表统一导出float32 W，在同C8中选一个完整三元组，查原实测NSG L128/K10标签。这里的anchor是C8域原画像选点，不是旧HNSW direct3或当前默认。

{table(['数据集','C8 anchor R@10','teacher','reward','reward−anchor pp','reward−teacher pp','后者fit配对95%区间'],cached)}

reward期望Recall相对anchor增加0.340684pp/0.132411pp，实际贪心选择增幅更大；二者分开记录。reward相对同C8 anchor的graph NDC为+0.08685%/+0.03378%，两集缓存门都通过。相对teacher净增命中1831/610，来自WebVid2067增−236损、Yandex678增−68损；所有负query保留，不能只报被挽救样本。bootstrap用2000次配对query重采样，仅描述这批历史fit数据。

![训练中的期望收益与实际选择](figures/reward_and_greedy.png)

## 3. 真实检索与开发门

实现完整GT-free C8 Policy并编译独立二进制。fit20K×两集×两个C8模型共8万逻辑路由逐条核对，C8候选、56动作slot和真实三入口均与冻结计算完全一致；plain/count也一致。随后真实fit7点、cal/audit14点全部完成；154336个query结果独立重算GT10命中，所有C8 fit hits/NDC与标签缓存完全一致，原kernel16条/点回归和实际单线程通过。

与当前默认的真实fit Recall差为WebVid+1.1795pp、Yandex+0.4035pp；默认是WebVid GT10-soft-t1 direct3与Yandex GT10-hard direct3，因候选域不同，这两个差值不能替代上表同C8对照。

开发门要求两集cal/audit分别严格胜teacher及当前默认、graph NDC≤默认+1%。每个开发split1024query，无重新训练或选点。

{table(['数据集','split','reward−teacher pp','reward−默认 pp','后者配对95%区间','图NDC变化','总NDC变化'],dev)}

相对teacher四点均正，说明训练之外也有方向一致的小信号；相对默认则为三正一负，且全部对应95%区间覆盖0。WebVid cal只差2个命中，−0.01953125pp；这是预设门未通过，不是稳定退化的证明。不事后放宽门或合并cal/audit来继续。状态`STOP_DEVELOPMENT_GATE`，validation未用于本轮训练、选点或新检索评测；旧保护链的12个validation query/GT/row_ids文件曾做SHA256身份校验，未解码为评测数组，未运行任何QPS点或wall重复。

![开发集收益与完整候选成本](figures/development_and_cost.png)

图NDC近似持平掩盖了路由代价。audit中，WebVid路由距离从默认111.77增至1069.16，总NDC1766.32→2715.85（+53.76%）；Yandex路由107.43→1047.00，总NDC2913.88→3849.86（+32.12%）。它包含两个候选HNSW、H次填充得分和8次学习画像得分；完整计时接口也包含query归一化、排序、组合选择、映射及NSG。当前只有NDC实测，没有纯wall证据，不能把这些比例直接换算成QPS下降或宣称前沿失败。

## 4. 为什么直接收益更有信号

一个事后只读诊断发现，大量query的56个动作有完全相同的hits。对这些query，直接Recall数据项的梯度严格为0；teacher仍会因为NDC tie-break和margin而学习不同选择。

{table(['数据集','动作hits全相同的query','占fit比例','占初始化teacher数据loss','该组teacher loss>0比例'],flat)}

这与“目标在优化什么”有关：原teacher初始数据loss的53.02%/75.64%来自无法改变当前C8 Recall的query，直接收益目标把数据梯度集中在动作确有命中差异的query上。loss占比不等于梯度范数占比，组间梯度也可能抵消；这是可核对的机制线索，不是完整因果分解。共享变换的表示限制、较大画像位移、固定温度及历史fit过拟合等仍未分离。本轮没有追加漂移匹配臂、容量、seed、PPO或新标签。

![各自目标下降与最终缓存收益](figures/objective_and_final_utility.png)

## 5. 实际成本、修正与验收

训练阶段{budget['elapsed_seconds']:.2f}s，训练子进程315.98s，低于600s上限；4次4800更新。复用224万逻辑训练标签，新训练标签0。8万逻辑route parity外另有21个真实诊断点，共{ver['real_NSG_calls']}次原NSG调用、总计805056次在线HNSW查询（含route parity/plain/count；不含建图距离）；诊断进程wall合计213.77s含一次加载失败。训练、诊断wall不能作为QPS。

首次WebVid fit的默认画像路径漏了`t1`，在第二个Policy加载阶段退出，尚无NSG查询。失败目录/原配置/日志/旧控制器全部保留；依据E30已用默认配置修正，新fit_v2目录执行。该零查询失败保留gross预留160064，并由独立证据显式释放实际调用预留；实际NSG309008、gross预留469072，本轮停止时两者都低于800000。失败wall仍计入预算。完整说明见[配置修正与记账例外](configuration_repair.md)，未改变模型、阈值、温度选择或丢弃检索结果。

数学验收包含12组完整枚举、48处共享A有限差分、logit策略梯度恒等式、常收益零梯度、平移不变性及加性MAP检查；β另用独立NumPy完整fit梯度复核。E31及旧保护链9211个历史文件保持身份。根文档旧版本保留source_before；原源码/NSG/H/GT/标签/模型无覆盖。三张图均保存PNG/SVG，所有表格及原始aligned输出保留，Excel逐单元核验见最终审计。当前仍为一个H/seed/λ/τ，fit/cal/audit都有历史使用，没有独立盲测或held-out读取/hash。

## 6. 结论与接续

本轮支持继续认真研究“直接优化完整入口组合的真实收益”，而不是把旧teacher loss下降当作Recall改善。它已学出较强fit信号及较小的开发集对照信号；当前方案还受开发收益波动和C8路由成本限制。尚无端到端性能收益证明，原GT10正信号与WebVid GT10-soft/Yandex GT10-hard默认继续保留。

后续优先问题是收益能否在更明确的独立选择/评估中保留，以及能否用更便宜且训练/部署一致的候选机制实现它；其次才是共享模型容量或多步RL。更换候选域必须重新核对组合标签覆盖，不能直接把此模型塞回单路HNSW后宣称保留C8收益。具体下一阶段条件写入根s-target，本轮停止后不自动追加实验。

- [原预锁协议](protocol.md)、[条件部署清单](deployment_plan.md)、[状态](state.json)、[缓存门](results/cache_gate.json)、[开发门](results/development_gate.json)、[未运行性能原因](results/performance_gate.json)。
- [训练/缓存表](results/analysis_tables.json)、[完整真实结果表](results/deployment_tables.json)、[机制诊断](results/reward_support.json)、[Excel](chart_data.xlsx)。
- [模型和梯度复核](reviews/model_and_cache_verification.json)、[完整路由parity](reviews/route_parity.json)、[真实输出复核](reviews/deployment_verification.json)、[最终验收](reviews/final_audit.json)。
'''
(O/'report.md').write_text(text)
(O/'README.md').write_text('''# E32 直接真实收益策略优化

状态：`DIRECT_REWARD_POLICY_COMPLETE_FIT_GAIN_MIXED_DEVELOPMENT_STOP`。双集fit缓存门与完整路由/NSG验收通过；开发集相对教师四点为正，但WebVid cal未胜当前默认，按预设门停止。新validation/QPS为0。

入口：[报告](report.md)、[原协议](protocol.md)、[部署清单](deployment_plan.md)、[配置修正](configuration_repair.md)、[开发门](results/development_gate.json)、[Excel](chart_data.xlsx)、[最终验收](reviews/final_audit.json)。

图：[训练策略与贪心收益](figures/reward_and_greedy.svg)、[优化与最终缓存](figures/objective_and_final_utility.svg)、[开发集与路由成本](figures/development_and_cost.svg)。

源码和日志保存实际执行路径。`run_deployment.py`和`deployment_common.py`为初始原件，`*_v2.py`为修正后的有效控制器；共享同一已验收evaluate二进制。`final_audit.py`仅用于缓存门停止分支，本次实际进入部署后的验收由`final_audit_deployment.py`完成。旧输出不可覆盖，未运行的validation入口不应直接启动。
''')
dump(O/'reviews/report_tables_used.json',dict(cache_rows=cached,development_rows=dev,optimization_rows=optimization,flat_action_rows=flat))
print('REPORT_WRITTEN',flush=True)
