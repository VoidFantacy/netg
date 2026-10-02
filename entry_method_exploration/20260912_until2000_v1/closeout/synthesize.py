from pathlib import Path
import json,hashlib,re,ast,os,time,csv
R=Path('/data/netg/ACSG');D=R/'entry_method_exploration';O=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
E52=D/'20260912_direct_candidate_commit_v1';E53=D/'20260912_feedback_step_rl_v1';E56=D/'20260912_construction_only_rl_v1';E57=D/'20260912_expanded_final_comparison_v1';E58=D/'20260912_accepted_action_conflicts_v1';E59=D/'20260912_frozen_pool_transfer_v1'
DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
assert os.sched_getaffinity(0)=={8}
for p in [E52,E53,E56,E57,E58,E59]:assert read(p/'reviews/final_audit.json')['status']=='PASS'
for x in read(E59/'reviews/final_artifact_freeze.json')['files']:assert sha(Path(x['path']))==x['sha256'],x['path']
assert read(O/'next_input_inventory.json')['status']=='PASS_EXISTING_SCOPE_VERIFIED'
data=read(E57/'results/analysis.json');points=[x for x in data['points'] if x['phase']=='validation'];small=[x for x in points if x['L']==128]
labels={'nsg':'NSG','fast30k':'Fast（GT1、30K）','gt10_hard':'FastGT10-hard','baseline_soft':'GT10-soft匹配起点','best_new':'cal选中新候选'}
table='| 数据集 | 方法 | Recall@10 % | QPS五轮中位数 | 五轮QPS范围 | 零命中失败率 % |\n|---|---|---:|---:|---:|---:|\n'
for x in small:table+=f'| {"WebVid" if x["dataset"]==DS[0] else "Yandex"} | {labels[x["model"]]} | {x["recall_pct"]:.3f} | {x["QPS"]:.2f} | {x["QPS_min"]:.2f}–{x["QPS_max"]:.2f} | {x["failure_pct"]:.2f} |\n'
costs=[]
for stage,root in [('E52',E52),('E53',E53),('E56',E56)]:
 c=read(root/'results/cost.json');costs.append(dict(stage=stage,NSG_calls=c['NSG_calls'],HNSW_calls=c['HNSW_calls'],physical_builds=c['builds'],gradient_updates=c['gradient_updates'],accepted=c.get('accepted_updates',c.get('accepted_submissions')),process_seconds=c['training_process_seconds']))
with (O/'training_costs.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(costs[0]));w.writeheader();w.writerows(costs)
ct='| 方法 | 训练NSG调用 | 实际HNSW路由 | 物理构图 | 接受步/800 | 四run总进程秒 |\n|---|---:|---:|---:|---:|---:|\n'
for x in costs:ct+=f'| {x["stage"]} | {x["NSG_calls"]} | {x["HNSW_calls"]} | {x["physical_builds"]} | {x["accepted"]} | {x["process_seconds"]:.2f} |\n'
body=f'''# 2026-09-12 研究收口：动作收益/损伤、离线RL与最终性能

今晚完成了收益/损伤归因、局部RL更新诊断、真实步长接受、纯离线HNSW构图RL，以及19候选固定选择后的NSG/Fast/FastGT完整对比。当前没有证据替换WebVid GT10-soft、Yandex GT10-hard默认。已证明局部机会存在，也测到了它转化为新query收益时的稀疏性和损伤；尚未得到超过匹配起点的稳定Recall–QPS增量。

## 诊断回答

**不是单一原因。早期主要有更新没有跨过离散响应边界的问题，修正后仍存在有限覆盖和少量关键损伤。**

1. E50在原RL两seed各400状态中，WebVid214步、Yandex97步有净正候选；其中原Adam均值分别184/93步命中完全不变。E51沿同一Adam方向放大，在预定正候选且均值无响应的状态救回WebVid9/12、Yandex4/4；最大半径也能新增损伤。因此局部可用动作确实存在，旧均值更新未充分实现它们。
2. E58重放E52贪心、E53联合RL、E56纯构图RL全部12条200步轨迹，908个接受动作中，monitor质量不变占WebVid73.5%–88.9%、Yandex90.0%–96.6%。WebVid三方法monitor单步内部增损并存分别7/9/0步，Yandex全部0。整体表现以稀疏响应为主，不能把全部未迁移收益归于同一步查询冲突。
3. 损伤虽少，足以抵消小收益。E53 WebVid两轨迹累计monitor命中增加80、损失84，Yandex8对8；WebVid E52/E53各轨迹前5个受损query占累计损伤70.0%–77.8%。这些是固定轨迹重复事件合计，不是独立query数，也不是最终测试表现。
4. E59固定19模型cal有限池中，任一模型能帮助的query只有WebVid11/1024、Yandex7/1024。即使知道GT并对每query免费选最佳模型，上界也仅+0.293/+0.117 pp，填补现有漏检1.19%/1.14%。与cal最佳单一模型的差额分别18/3个命中，分成未覆盖17/2、自身损伤1/1。这个位置的剩余差额主要是覆盖不足；有限池上界不能外推整个画像/图表示空间。

综上，已有动作确实对不同query产生收益和损伤，但尚未证明共享表示存在不可兼容的硬冲突。只减少损伤、只扩大步幅或只在现有19模型中做查询选择，都还没有足够的性能证据。下一步要验证新动作对独立开发query的支持和损伤约束。

## RL实际放在哪里

构图对象为WebVid815、Yandex821个入口画像节点组成的Micro-HNSW，底层仍为原NSG索引。E53离线用真实NSG效用估计RL梯度，再用实际反馈接受确定步长，输出静态画像W和普通HNSW图G(W)。E56离线用坐标C构图得到G(C)，全部训练评价和导出图始终用原画像P评分；C不进入在线评分。它实现了“训练怎样构造HNSW图”的一种形式，即学习构图坐标，尚不是直接学习每条边。

```mermaid
flowchart LR
  T[训练query和GT] --> U[离线RL与动作接受]
  U --> G[静态画像及HNSW图]
  Q[线上query] --> H[普通HNSW取3个入口]
  G --> H
  H --> N[原NSG搜索]
  N --> K[返回top10]
```

线上没有RL策略推理或每步RL选邻居。E52是Greedy候选接受对照，不能把它叫作RL。E56四个selected都出现monitor局部正值，但cal双seedWebVid−0.0195/−0.0684 pp、Yandex−0.0488/+0.0684 pp，统一19候选cal规则未改选。

## 最终同机单线程比较

WebVid选中新候选为E52 seed21拓扑单独部署，Yandex为E53 seed22联合RL。选择由原cal的U、低totalNDC、固定池顺序决定，最终结果未回流选择。E57加入E56双seed后身份不变，按事先规定整组继承E55已测矩阵；没有混用不同批次的同组方法。

L128代表点；每集历史validation2000，CPU15实际进程/OMP/BLAS/MKL均1线程，QPS来自五轮纯端到端wall。失败率为GT10零命中查询比例。

{table}

完整五L为64/128/256/400/800，45个最终点、225轮计时全部保留。相对匹配GT10起点，WebVid新候选五L Recall变化−0.120/−0.045/−0.065/−0.025/−0.005 pp；Yandex−0.075/−0.075/−0.050/−0.050/−0.050 pp。全部QPS差异的五轮波动包络包含0，未显示稳定增量。Fast/FastGT对原NSG的原有收益保留，不能归为本次RL贡献。Fast与FastGT除GT1/GT10外还有30K/20K和seed差异。

L128新候选相对匹配起点：WebVid27个增益命中、36个损失，4条失败被救回、2条新失败；Yandex0个增益、15个损失，2个受损query均变为零命中。平均差小不能掩盖这些稀疏损伤。历史validation曾用于研究，不是全项目新盲测；只使用已冻结2000条副本，未打开原完整validation/held-out。

[完整比较与45点](../../20260912_expanded_final_comparison_v1/report.md)、[Recall–QPS](../../20260912_expanded_final_comparison_v1/figures/recall_qps.svg)、[失败率–QPS](../../20260912_expanded_final_comparison_v1/figures/failure_qps.svg)、[全部L三指标](../../20260912_expanded_final_comparison_v1/figures/three_metrics_by_L.svg)。

## 成本和验证

以下三个后续方法各为两集×两seed×200步，成本均实际计量，不作等wall因果比较：

{ct}

纯构图训练当前每个逻辑图经过build(C)、build(P)、拓扑安装及全P字节检查，额外构图完整计入。E56虽然变化入口需要的NSG更少，整体进程仍比E53更长；减少NSG调用不等同减少wall。精确缓存只在同query和完整三个入口、同NSG/metric/L/K一致时复用原NSG，路由NDC每次重新测量。

E56的8张selected/last导出图独立解析全部层邻接和6544行评分向量，保证W恒P；6400候选、2400确定点、800梯度/接受链及512三路parity通过。E57独立133776行集合评分、所有19模型fit恢复、原17模型cal五字段回归、固定选择/五L图和实际线程计时合同通过；新增88768 NSG、0新最终计时。E58新增3146 NSG、943104 HNSW、1185build，完整重放2400步，132 checkpoint/675840行train+monitor恢复，512物理parity及逐query求和守恒通过。E59新增搜索和训练均0，233472集合评分及12288逐query分解通过。

E53历史一次运行日志封存时序问题已保留原v1并用稳定v2封存修复；E56原启动仅因预测窗口退出，native创建前0查询/0构图，有效v2只改预测窗口，算法和实际21:15训练硬停保持。E58图表仅修正布局，原图保留。各阶段修正和边界均留在原报告，未抹去失败入口或负结果。

## 接续与产物

下一轮优先验证辅助反馈上的动作支持/损伤约束，与相同候选和梯度的E53接受规则对照。辅助反馈进入接受决策即属于训练信息，另外保留迁移验证；当前monitor全1024属于初始P拟合20K，不能充当未见数据。数据角色、40状态支持控制、两臂预算推导、停止条件和可复制只读启动命令见[下一轮设计](next_experiment_design.md)。该设计尚未训练或排队。

[E50更新转化](../../20260912_candidate_commit_diagnosis_v1/report.md)、[E51方向半径](../../20260912_update_direction_radius_v1/report.md)、[E54评分/拓扑拆分](../../20260912_learned_model_factorial_v1/report.md)、[E56纯构图RL](../../20260912_construction_only_rl_v1/report.md)、[E58逐动作损益](../../20260912_accepted_action_conflicts_v1/report.md)、[E59固定池覆盖](../../20260912_frozen_pool_transfer_v1/report.md)、[训练成本CSV](training_costs.csv)、[数据角色检查](next_input_inventory.json)。原代码、索引、GT、标签、模型、日志和全部历史实验保留；未提交、推送或更换默认部署。
'''
(O/'final_report.md').write_text(body)
summary='''# ACSG 当前结果摘要

2026-09-12，今晚离线RL、动作诊断和最终基线比较已完成。主结论：局部动作有收益，旧更新步幅的转化问题已经得到真实控制支持；修正后仍以稀疏支持和少量关键损伤为主，尚未获得超过匹配GT10起点的稳定Recall–QPS增量。

E58完整12条轨迹、2400步、908个接受动作：monitor命中完全不变占WebVid73.5%–88.9%、Yandex90.0%–96.6%；E53两seed累计monitor收益/损伤分别80/84和8/8。WebVid有同一步跨query增损并存，Yandex该监控样本未观察到；不能把这些结果概括为共享表示不可调和的硬冲突。

E59固定19模型cal池只有WebVid11/1024、Yandex7/1024个query可获益，逐query免费选优的有限上界为+0.293/+0.117 pp，仅填补约1.2%的起点漏检。cal最佳单模型与该上界的差额主要为未覆盖，而非自身损伤。该上界仅覆盖已测模型，不是全画像/图空间上界。

本轮学习对象是815/821入口画像节点的Micro-HNSW，底层NSG固定。E53是离线联合画像/拓扑RL，E56是离线学习构图坐标C、以固定P评分的G(C)；在线均普通HNSW取3入口后原NSG，无RL策略推理。纯构图双seed加入后，19候选cal仍选中WebVid E52 seed21拓扑部署、Yandex E53 seed22联合RL；E52本身是贪心对照。默认继续WebVid GT10-soft、Yandex GT10-hard。

以下L128代表点：历史validation2000/集，实际单线程，五轮纯端到端wall；失败为GT10零命中。完整五L的新候选Recall均未超过匹配起点，QPS差异处于五轮波动内。Fast/FastGT对NSG原有收益不能归给新RL。

'''
(R/'summary.md').write_text(summary+table+'\n[完整收口报告](entry_method_exploration/20260912_until2000_v1/closeout/final_report.md)、[最终五L/225轮](entry_method_exploration/20260912_expanded_final_comparison_v1/report.md)、[动作诊断](entry_method_exploration/20260912_accepted_action_conflicts_v1/report.md)、[19模型迁移](entry_method_exploration/20260912_frozen_pool_transfer_v1/report.md)。\n\nmonitor曾参与初始P拟合和选点；cal已用于模型选择；历史validation非项目盲测。全部局部正信号、负结果、独立集合评分/图身份/计时和数据范围核验保留。下一轮设计未运行，见[s-target.md](s-target.md)。\n')
(R/'s-target.md').write_text('''# ACSG 下一阶段目标与接续

2026-09-12，今晚授权实验与最终比较已完成，新增训练和查询已停止，默认未替换。

下一轮先验证离线动作在独立开发样本上的支持，再检验逐query损伤约束。E58显示稀疏关键损伤，E59显示当前19模型池覆盖有限；不能假定只增加训练预算或增加在线选型器就会有足够收益。

1. 固定每集40个已有E53状态，当前+3个原确定点，在新锁定的辅助反馈上检验有多少动作获得正命中且不新增零命中；状态和候选不由新增反馈挑选，最坏172592 NSG/集、预留180000。支持不足则不进入连续训练。
2. 若支持门通过，原J接受与J加支持/损伤约束两臂，保持原两个seed、200步、8候选及3确定点，从共同起点独立运行。辅助反馈参与接受即算训练，另设迁移验证；预算随实际分区大小锁定。先证明损伤下降且收益保留，再评最终Recall–QPS。
3. 上述通过后再讨论画像/构图动作家族扩展，先核对历史失败和实质差异，保持静态普通HNSW→NSG部署。当前纯构图只学C→G(C)，不代表直接逐边RL已有效。

当前monitor1024全在初始P拟合20K内且参与过选点；cal虽不在P拟合内，也已经选过模型。下一轮须核对数据源命名空间、历史曝光和各阶段角色，不能重命名旧分区冒充盲测。已经提供实际运行过的只读ID检查器，未读取新query/GT或启动训练。

[详细设计、支持门/停止条件/成本与接续命令](entry_method_exploration/20260912_until2000_v1/closeout/next_experiment_design.md)，状态为设计完成、尚未运行；新训练runner未实现。今晚[E57最终性能](entry_method_exploration/20260912_expanded_final_comparison_v1/report.md)、[收口报告](entry_method_exploration/20260912_until2000_v1/closeout/final_report.md)保持冻结。
''')
p=R/'spec.md';s=p.read_text();s+='\n收口[只读范围检查器](entry_method_exploration/20260912_until2000_v1/closeout/next_stage_inspect.py)读取既有row IDs和来源元数据，验证E37 train/monitor对E24 P-fit的集合关系及cal/audit互斥；不读query向量/GT标签，不导入原生搜索。它不判定全项目未使用样本或启动训练，training_plan_ready=false只表示下一轮数据角色尚未冻结。\n';p.write_text(s)
p=R/'s-experiment.md';s=p.read_text();s+='\n2026-09-12 [今晚完整收口](entry_method_exploration/20260912_until2000_v1/closeout/final_report.md)汇总E50–E59机制证据、19候选最终选择和NSG/Fast/FastGT三指标，新增下一轮设计保持未运行身份；原48份历史卡片均保留。\n';p.write_text(s)
roots=[R/x for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']]
links=0
for p in roots+[O/'final_report.md',O/'next_experiment_design.md']:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in link or link.startswith('#'):continue
  assert (p.parent/link.split('#')[0]).exists(),(p,link);links+=1
for p in O.glob('*.py'):ast.parse(p.read_text())
assert len(points)==45 and len(small)==9
assert all(read(E57/'results/final_sources.json')[ds]['reused_E55'] for ds in DS)
review=dict(status='PASS',links=links,final_points=45,wall_repeats=225,L128_points=9,source_stages=['E52','E53','E56','E57','E58','E59'],default_replaced=False,new_training_in_closeout=0,new_search_in_closeout=0,next_design_unrun=True,completed_at=time.time())
(O/'synthesis_verification.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
print('SYNTHESIS PASS; preserve E59 historical root seal and seal current closure after independent review',flush=True)
