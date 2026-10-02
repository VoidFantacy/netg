from common import *
P=read(O/'results/points.json');B=read(O/'results/paired.json');M=read(O/'results/models.json');G=read(O/'results/development_gate.json');J=read(O/'logs/jobs.json')
names={DS[0]:'WebVid',DS[1]:'Yandex-IP'}
labels={'base':'原top3','random':'随机换点','rl_20260917':'RL seed17','rl_20260918':'RL seed18','exact_20260917':'Exact seed17','exact_20260918':'Exact seed18'}
def table(head,rows):return '| '+' | '.join(head)+' |\n|'+'|'.join(['---']*len(head))+'|\n'+''.join('| '+' | '.join(map(str,r))+' |\n' for r in rows)
def point(ds,phase,m='rl_20260918'):return next(x for x in P if x['dataset']==ds and x['phase']==phase and x['method']==m)
training=table(['数据','训练臂/seed','所选step','所选train Δpp','所选monitor Δpp','3000步train Δpp','3000步monitor Δpp'],[[names[x['dataset']],f"{x['arm']} / {str(x['seed'])[-2:]}",x['selected_step'],f"{x['train_delta_pp']:+.4f}",f"{x['monitor_delta_pp']:+.4f}",f"{x['last_train_delta_pp']:+.4f}",f"{x['last_monitor_delta_pp']:+.4f}"] for x in M])
dev=table(['数据/split','方法','Recall %','ΔRecall pp','失败率 %','总NDC变化 %','改善/受损query'],[[names[x['dataset']]+'/'+x['phase'],labels[x['method']],f"{x['recall_pct']:.6f}",f"{x['delta_recall_pp']:+.6f}",f"{x['failure_pct']:.6f}",f"{x['total_NDC_change_pct']:+.4f}",f"{x['helped']}/{x['harmed']}"] for x in P if x['phase'] in ['cal','audit']])
ci=table(['数据/split','RL18比较对象','ΔRecall pp','描述性95%区间 pp','Δ平均U'],[[names[x['dataset']]+'/'+x['phase'],labels[x['reference']],f"{x['delta_recall_pp']:+.6f}",f"[{x['recall_CI_low_pp']:+.4f}, {x['recall_CI_high_pp']:+.4f}]",f"{x['utility_delta']:+.6f}"] for x in B if x['method']=='rl_20260918'])
wall=table(['数据','方法','Recall %','总NDC','QPS中位数','五轮min–max','ΔQPS %'],[[names[x['dataset']],labels[x['method']],f"{x['recall_pct']:.6f}",f"{x['total_ndc']:.3f}",f"{x['QPS_median']:.2f}",f"{x['QPS_min']:.2f}–{x['QPS_max']:.2f}",f"{x['QPS_change_pct']:+.3f}"] for x in P if x['phase']=='wall'])
brief=table(['数据','所选RL cal ΔRecall','audit ΔRecall','audit ΔQPS'],[[names[d],f"{point(d,'cal')['delta_recall_pp']:+.4f} pp",f"{point(d,'audit')['delta_recall_pp']:+.4f} pp",f"{point(d,'wall')['QPS_change_pct']:+.2f}%"] for d in DS])
cost=table(['阶段','新NSG调用','说明'],[['fit完整56组合',229376,'每集2048×56'],['标签原路由/原kernel回归',192,'每集96'],['fit真实部署与回归',1152,'8模型×64及plain/reference'],['cal全部六方法与回归',12480,'每集512，双seed完整保留'],['audit全部六方法与回归',12480,'cal先选seed并冻结'],['L128 wall及回归',24672,'两集各三方法，warmup+五轮及核验'],['合计',sum(x['actual'] for x in J),'硬上限300000；剩余额度不扩实验']])
report=f'''# E36：query相关的三入口换点策略

2026-09-11。用户确认推进“针对这个query换入哪个点、换出哪个点，用实际三入口联合搜索收益反馈”。已实现、训练并实际部署8个策略：两数据集×REINFORCE/同策略精确期望控制×两seed，每个3000次更新。[冻结协议](protocol.md)、[状态](state.json)、[开发门](results/development_gate.json)、[最终验收](reviews/final_audit.json)。

## 1. 结果与解释

查询相关的组合选择在Yandex保留了局部正信号；当前实现没有通过预定双数据开发门，单点实测也支付了明显推理时间。状态`COMPLETE_QUERY_SWAP_POLICY`，判断`QUERY_SWAP_POLICY_COMPLETE_YANDEX_SIGNAL_WEBVID_AND_COST_NO_GO`。已执行工作收口，默认保持原GT10。

{brief}
这里的对照是同一当前GT10候选源的原top3。Yandex相对Exact的增量只有cal +0.019531pp、audit +0.117188pp，且配对区间跨0，不能宣称采样RL已胜精确优化。WebVid cal/audit均未提高。此结果约束本轮表示、训练数据量和实现，不是否定所有RL、所有query相关选择，也不抹去E24原GT10或E35组合oracle信号。

![开发质量和成本](figures/development_quality_and_cost.png)

## 2. 实际学了什么

固定WebVid GT10-soft-t1与Yandex GT10-hard，H815/821及真实ID、画像、原HNSW M16/efC200/seed20260828/efSearch10和原NSG/raw IP不变。一次HNSW取top8，以原前三个为初态；56个三元素集合，每态为停止或15种单点换出/换入，最多3步。线上模型只看当前query和候选特征，完成选择后执行一次NSG L128/K10，三个真实入口升序使用原共享beam。

策略给完整三入口集合打分，不把三个单入口收益相加。76维特征包含候选rank、原query–profile cosine及相对top1差、query与画像的固定16维投影交互、三个画像pair cosine及query投影。训练1792行的统计量标准化，特征先量化float32、再float64计算。MLP 76→16→16→1/ReLU，共1521参数；集合势函数为原rank先验−0.25×(rank和−3)加MLP。初始贪心停止，后继16个集合的softmax给动作概率；线上按最高分、1e−9同分时优先停止，至多3步。

这是有限状态的查询相关局部改写，未改HNSW图或重新挑选全局H。[方法依据](method_basis.md)说明与NeuRewriter的关系及差别；并非复现其Q-actor-critic。停止只是不再修改当前集合，不使用GT兜底；即使预测分数提高，真实Recall仍可能下降。

## 3. 真实反馈、训练控制和样本

每个fit query的全部56集合都实际运行原NSG，保存返回ID、距离、入口和NDC，GT只在查询结束后评分。U(q,S)=hits(q,S)−hits(q,S0)−0.1×[总NDC(q,S)/总NDC(q,S0)−1]；每步奖励为相邻U之差，γ=1，累计等于终态U。总NDC包括HNSW路由和图距离计算，包含不了特征/矩阵乘等费用，后者进入独立wall。

RL采用REINFORCE，减去只用以往轨迹更新的query×state EMA基线；不使用当前动作的奖励拟合当前baseline。Exact控制对完全同一16动作、3步、停止吸收的策略，以56状态动态规划计算期望终态U并精确反传。两臂表示、初始化、batch顺序、AdamW、学习率和训练日程一致；Exact不是另一个终态softmax，也不是线上GT oracle。每臂两seed、batch64，每100步保存模型/优化器/曲线，固定3000步。反馈缓存源自真实完整联合搜索，优化时复用缓存，不把每个梯度更新伪称一次新NSG。

每集从当前E24 fit20K预选2048行，1792训练、256 monitor，cal/audit各取原对应1024行的前512。四部分行ID不重叠；这些数据历史上均使用过，画像也来自历史fit，不能称全管线盲测。先冻结训练模型才准备cal，cal选seed后冻结再准备audit。checkpoint从100..3000选择monitor平均U最高且图NDC≤原+1%的最早点，两集cal均选RL18和Exact18；audit不换seed。旧E28/E32是两路union C8，本轮是一次当前GT10 top8，因此重新生成全部真实标签。

## 4. 全部训练轨迹与选点

{training}
![训练曲线](figures/training_progress.png)

8次固定训练全部完成，训练进程125.42s、单线程、峰值RSS约624MiB；这不是查询QPS。RL四次共768000条缓存反馈轨迹，8次共24000更新。train收益总体提高，但monitor波动，末点不持续优于早期所选点；例如WebVid RL17从所选monitor +0.0781pp降到末点−0.2344pp，Yandex RL17由+0.7813pp降至−0.1563pp。当前证据不支持简单追加epoch。所选点/末点和全部24000步曲线均保存，没有只展示最佳train点。

## 5. 全部开发结果和配对差值

失败定义为返回top10与GT前10零交集。每个split/方法512查询，表中改善/受损按逐query命中数与原top3比较，其余命中数相同。

{dev}
{ci}
区间为5000次query配对bootstrap、seed20260920；是当前历史样本的描述性区间，不校正历史选择/多重比较，不作显著性GO。Yandex RL18对原top3的audit区间为[−0.5664,+1.3867]pp，对Exact18为[−0.9180,+1.1719]pp。WebVid所选RL18 audit −0.46875pp，另seed17 −0.03906pp，不能看到audit后改选seed17。

预定门要求两集cal≥+0.10pp、audit>0、总NDC≤+1%，且RL合并cal/audit平均U胜随机。两集RL均胜随机的平均U；Yandex通过这些开发点门，WebVid Recall门失败，因此`STOP_DUAL_DEVELOPMENT_GATE`。开发门通过也不能替代端到端性能证据。

## 6. 换点行为与收益集中性

WebVid RL18 audit改变196/512个入口集合、平均0.4043次交换，61.72%第一步停止；6个query改善、7个受损、499个命中数相同，新增2个零命中失败且没有救回。Yandex改变474/512个集合、平均1.4102次交换，7.42%第一步停止；14个改善、11个受损、487个命中数相同，救回3个失败但新增2个。换了很多入口并不意味着大多数query受益。

![交换行为](figures/swap_behavior.png)

完整[动作频次](results/action_counts.csv)、[交换次数](results/swap_counts.csv)、[逐query结果](results/query_results.csv)保留。随机控制使用相同动作域、停止和三步上限，实际步数与学习策略不同，不宣称动作数或wall完全匹配。线上模型不读query row ID；row ID只用于冻结的随机控制。

## 7. 实测在线成本

两数据集各audit512、固定L128，原top3/所选RL/所选Exact，完整warmup后五轮轮换串行plain整批wall。CPU15，进程/OMP/BLAS/MKL1线程，无并发训练或其它方法；timer内含一次HNSW、query投影、56集合特征和全部MLP分数、至多3步选择、真实ID映射、原NSG及输出。模型load、GT、NDC计数、hash与文件I/O在计时外。

{wall}
当前选择器即使早停，也先计算全部56个集合势函数；仅MLP每query约83328次乘加，另有16×d query投影及特征处理。这解释了NDC增加不到1%却无法保证总时间接近原方法的原因，但没有独立分段计时，不能把全部wall差额精确归因某个算子。Yandex得到同L质量与速度的权衡；WebVid此单点质量、速度均较差。只测一个L，不能认定完整前沿优劣或正式方法性能GO。

## 8. 调用、资源、核验和修正

{cost}
新HNSW调用总{sum(x['HNSW_calls'] for x in J)}；标签/部署/计时十个job均完成，实际查询峰值线程1，最高RSS {max(x['peak_RSS_KiB'] for x in J)/2**20:.3f}GiB。训练0新NSG，缓存轨迹复用单列；无新GT生成、validation/held-out访问、多L前沿或全局构图迭代。总新产物上限384MiB、余盘至少10GiB，最终实值见验收。

优化前[preflight](reviews/preflight.json)独立复算229376个完整三入口标签，检查原生/NumPy全部特征相等，枚举3616条终止路径，DP/期望策略梯度/baseline与有限差分通过。[训练核验](reviews/training_verification.json)独立恢复全部248个checkpoint的贪心和期望值、768000条RL轨迹奖励/回报/EMA，以及每100步块首的策略概率和动作RNG；没有声称重新执行所有优化器更新。另4096个原top3输出与E33历史当前GT10完整ID/距离/入口/NDC一致。

[部署核验](reviews/deployment_verification.json)涵盖38个点：C++/NumPy分数最大误差小于1e−12、逐步动作和真实入口完全一致；8个fit点共512查询与缓存完整返回一致；六个wall点与audit结果一致。所有方法count/plain和预定16行原kernel回归通过。最终再以独立集合交集复算标签/实际部署命中，核对CSV/Excel/图源、冻结依赖与根文档链接。

两项版本变化有记录：初始label runner没有导出部署特征核验所需pool距离，新`runner_v2.cpp`仅增加输出/距离byte parity，在任何部署前冻结，原runner保留；第一次报告分析因NumPy布尔无法JSON序列化停止，`analyze_v2.py`只转换两个gate布尔类型，原脚本和部分派生输出在reviews保留，0新查询/训练。实际输入、策略、奖励和选点规则未变。[修正记录](reviews/analysis_correction.json)、[build v2](bin/build_v2.json)。

## 9. 接续判断与证据入口

优先从已有逐query标签分析WebVid泛化和收益/损伤，控制相同目标的Exact，避免直接增加模型/epoch。其次在冻结模型和返回完全一致的条件下减少56集合打分开销，再决定是否值得正式前沿；Yandex局部正值须保留。局部图交换作为补充候选覆盖的后续路线，须另建协议，不能凭本轮质量信号直接运行。详细前三方向、成本与停止条件见[当前s-target](../../s-target.md)。

原始入口为[协议](protocol.md)→[输入](inputs/selection.json)→[标签/部署runner](src/runner_v2.cpp)→[训练](src/train.py)→[独立训练核验](src/audit_training.py)→[真实部署](src/deploy.py)→[结果分析](src/analyze_v2.py)。[CSV/Excel工作簿](results/query_swap_policy.xlsx)含完整模型、checkpoint、24000步曲线、38点、28配对、30轮时间及逐query/动作；嵌套utility区间与时间列表保留在JSON。图有PNG/SVG/PDF，原始标签、模型、轨迹和旧E35原件均保留。复现训练应建新版本和预算，当前完成版本有状态/重复执行保护，不能直接重跑冻结runner覆盖结果。
'''
(O/'report.md').write_text(report)
(O/'README.md').write_text('''# E36 query相关三入口换点策略

已完成8次×3000更新、真实完整三入口反馈、原生在线部署与固定L128单线程成本诊断。Yandex有局部开发信号；WebVid开发门失败，当前推理QPS下降，默认未换。

- [报告](report.md) / [协议](protocol.md) / [状态](state.json) / [开发门](results/development_gate.json) / [最终验收](reviews/final_audit.json)
- [开发质量与成本图](figures/development_quality_and_cost.svg) / [训练图](figures/training_progress.svg) / [交换行为](figures/swap_behavior.svg)
- [Excel](results/query_swap_policy.xlsx) / [完整点CSV](results/points.csv) / [逐query](results/query_results.csv) / [全部训练曲线](results/training_curves.csv)
- [历史25](../../experiment_history/25_query_swap_policy.md) / [下一步](../../s-target.md)

当前版本已收口；方法实现与真实训练完成不等于性能GO。已有cal/audit历史使用，单L成本测量不是完整前沿；无新validation/held-out、多L或改图。
''')
hist=R/'experiment_history/25_query_swap_policy.md'
assert not hist.exists()
hist.write_text(f'''# E36：针对query逐步换入/换出三入口

2026-09-11，独立版本`20260911_query_swap_policy_v1`。用户在E35最小诊断后明确确认推进实际查询相关换点学习，已完成训练/部署/预算收口。状态`COMPLETE_QUERY_SWAP_POLICY`，开发判断`STOP_DUAL_DEVELOPMENT_GATE`。详见[原报告](../entry_method_exploration/20260911_query_swap_policy_v1/report.md)、[协议](../entry_method_exploration/20260911_query_swap_policy_v1/protocol.md)、[验收](../entry_method_exploration/20260911_query_swap_policy_v1/reviews/final_audit.json)。

## 动机与实质差异

E35发现已评分好点没有保留，exact画像top3增量小而真实C8三入口oracle仍有空间。本轮固定原HNSW/H/画像/NSG，使用一次GT10 top8，从原三入口开始，按query学习最多三步换点或停止；没有改图或更换全局聚类点。56完整集合、16动作/态，query投影/画像交互等76维特征和1521参数非加性集合势函数。E28/E32曾用共享画像/真实收益，本次增加明确状态/动作/停止及同一三步策略精确梯度控制，候选由旧两路union改为当前单路top8，因此生成新标签。

奖励来自原NSG raw IP/L128/K10三个真实ID升序共享beam的实际命中及总NDC，使用相邻集合U差、γ1。RL是REINFORCE加历史query-state EMA baseline，训练时复用完整真实标签缓存；Exact是同策略完整期望梯度，线上都只使用query和候选特征，不读GT。stop不保证真实收益不降。

## 样本、选点与实际执行

两集各2048 fit（1792 train/256 monitor）、cal/audit各512，源行与SHA核验、四部分行不重叠，但都历史使用且画像为历史fit构建，非盲测。两臂双seed共8次固定3000更新；monitor按U和NDC门选checkpoint，cal选seed再冻结audit，两集主RL/Exact均seed18。全部另seed、末点、训练和开发正负保留。

新NSG280352/上限300000（完整56标签229376，其余回归/部署/wall），HNSW{sum(x['HNSW_calls'] for x in J)}。RL768000条缓存反馈轨迹单列，不当新查询；训练进程125.42s，24000更新。查询串行CPU15/实际线程1，最高RSS约{max(x['peak_RSS_KiB'] for x in J)/2**20:.3f}GiB。无新GT、validation/held-out、多L前沿、图交换，剩余预算不扩展。

## 结果和成本

{brief}
Yandex RL18 audit Recall88.652344%，原top3 88.261719%；失败率从1.757813%降至1.562500%。WebVid RL18为74.609375%对75.078125%，失败率1.5625%对1.171875%。Yandex RL相对Exact18仅cal +0.019531pp/audit +0.117188pp；audit对原与Exact的配对95%区间均跨0，不能归因RL稳定优势。WebVid两臂都未通过开发，不能看到audit后改选另seed。

单L128成本诊断无论开发正负都按协议完成：原/所选RL/所选Exact，audit512，warmup+五轮轮换独立plain整批wall。计时含全部56特征/MLP/换点/NSG，GT/count/load/IO在外。RL总NDC仅增加WebVid0.388%、Yandex0.283%，QPS却下降9.32%/8.30%，表明NDC未覆盖选择器的主要非距离费用。不能用单L判断完整Recall–QPS前沿。

两集平均U均胜随机，Yandex通过预定开发点门，WebVid未过，因此双集开发停止、默认不换；保留Yandex查询相关组合选择的局部信号，不外推所有RL失败。训练后期train改善未稳定传至monitor，应先定位泛化/推理开销而非盲增epoch。

## 验收、修正和证据

229376真实标签、完整路径DP与期望策略梯度有限差分验收；全部248checkpoint前向/贪心、768000轨迹reward/return/EMA独立核验，38原生部署点动作和真实入口一致，512 fit部署与缓存完整返回一致、4096基线与旧E33同GT10结果一致。原生count/plain和原kernel回归、wall/audit返回及全部图表/工作簿/CSV验收见原报告。

runner v2仅在部署前增加pool距离导出与parity，原label runner保留；分析v1的NumPy布尔序列化错误由v2类型转换修复，原脚本/派生输出保留，0新增查询训练。所有旧源/图/标签/模型/历史保护；该卡是实际结果，E35当时未训练的原协议不回写为已执行。[图](../entry_method_exploration/20260911_query_swap_policy_v1/figures/development_quality_and_cost.svg)、[工作簿](../entry_method_exploration/20260911_query_swap_policy_v1/results/query_swap_policy.xlsx)、[完整点](../entry_method_exploration/20260911_query_swap_policy_v1/results/points.csv)、[当前接续](../s-target.md)。
''')
summary=f'''# ACSG 当前结果摘要

2026-09-11。最近完成E36 query相关三入口换点学习，状态`COMPLETE_QUERY_SWAP_POLICY`。[报告](entry_method_exploration/20260911_query_swap_policy_v1/report.md)、[历史25](experiment_history/25_query_swap_policy.md)、[验收](entry_method_exploration/20260911_query_swap_policy_v1/reviews/final_audit.json)。用户确认实际推进，已完成8次×3000更新、真实联合搜索反馈与在线部署。

## 当前结果

{brief}
一次当前GT10 HNSW top8，从原top3开始，学习至多3步单点换入/换出或停止；对照原top3、同动作域随机策略、同表示/同三步策略的Exact期望梯度，各训练臂双seed。表为cal选定并在audit前冻结的RL seed18，相对原top3。WebVid采用GT10-soft-t1，Yandex采用GT10-hard。

Yandex保留局部正信号，RL相对Exact在cal/audit仅+0.019531/+0.117188pp，配对区间跨0；尚无RL稳定增量证据。WebVid所选RL cal/audit下降，两集联合开发门`STOP_DUAL_DEVELOPMENT_GATE`。总NDC增加不足1%仍伴随8%～9% QPS下降，当前56集合特征/MLP费用进入了wall。单L128、每集历史audit512、五轮单线程成本诊断不能代替完整Recall–QPS前沿，默认未换。[质量与成本图](entry_method_exploration/20260911_query_swap_policy_v1/figures/development_quality_and_cost.svg)、[Excel](entry_method_exploration/20260911_query_swap_policy_v1/results/query_swap_policy.xlsx)。

## 训练、核验和范围

每集fit2048（1792 train/256 monitor）、cal/audit各512，行互斥但历史使用，原画像也来自历史fit，非盲测。新生成每query全部56个真实NSG三入口联合标签，奖励为命中增量减总NDC惩罚的相邻差；RL缓存反馈复用不当新查询。train收益上升未持续传至monitor，不据此追加epoch。

新NSG280352/300000、HNSW{sum(x['HNSW_calls'] for x in J)}；8次共24000更新、RL768000条轨迹，训练进程125.42s。229376标签、全部248checkpoint、轨迹reward/return/EMA与38个原生部署点验收；当前GT10基线4096条与E33原结果一致。查询串行且实测线程1，最高RSS约{max(x['peak_RSS_KiB'] for x in J)/2**20:.3f}GiB。无新validation/held-out、GT生成、多L或改图。

部署runner v2只增加pool距离导出以完成独立特征核验；分析v1的布尔JSON类型错误在v2修复，0新训练/查询，原件保留。旧源/图/标签/模型/结果保护，四根文档与历史同步。

## 与前序和后续的关系

[E35](experiment_history/24_hnsw_selection_diagnosis.md)的“强连通、好点已评分却未保留、当前C8真实组合oracle有空间”仍是动机，不把oracle空间写成E36实际收益。[E34](experiment_history/23_hnsw_rl_benchmark.md)已表明旧删边RL相对原GT10无稳定增量，本次没有重启该算法；E24/E28等局部信号分开保留。

下一步先用已有标签定位WebVid泛化和收益损伤，再降低当前集合评分成本；Yandex信号需要独立质量和完整成本证据。图交换为后续补充覆盖路线，尚未实施。详细方法/控制/成本/停止条件见[s-target](s-target.md)。本轮无排队任务。
'''
(R/'summary.md').write_text(summary)
target='''# ACSG 下一阶段方向与实验接续

2026-09-11。E36已完成用户授权的query相关三入口换点训练和真实部署，状态`COMPLETE_QUERY_SWAP_POLICY`，双集开发门停止。[历史25](experiment_history/25_query_swap_policy.md)、[完整报告](entry_method_exploration/20260911_query_swap_policy_v1/report.md)。以下是尚未实施的接续设计，无排队任务，不回写E36冻结选择或追加原预算。

## 当前依据与问题

E35现有C8真实三入口oracle有空间；E36已将“换入/换出”实现成query相关非加性集合势函数，以实际NSG联合奖励训练，原图/H/画像未变。两集各2048 fit、cal/audit各512，RL/Exact双seed各3000更新。Yandex所选RL相对原top3 cal +0.722656pp、audit +0.390625pp，WebVid−0.175781/−0.468750pp；Yandex RL对Exact的audit +0.117188pp区间跨0。五轮单L完整wall的RL QPS下降9.32%/8.30%，总NDC只增0.388%/0.283%。

因此当前问题分为收益能否泛化、选择器是否值得其时间、候选外是否仍有可补充的空间。不能以更多epoch、强连通或oracle直接推导成功；保留Yandex局部信号和原GT10贡献。

## 第一优先：用已有真实标签定位泛化和误换

先做无新NSG/训练的已有产物分析：按训练/monitor的原始命中、56组合效用平坦度/间隔、画像相似度差、交换步数和收益/受损幅度，比较RL与同策略Exact。将真实U最大值与所选U分开，判断剩余问题是“预测集合分数没学到”还是“有限步贪心没走到自己评分最高处”；后者可以对已有56预测分数离线核对，不能直接当新策略的质量/速度成果。

WebVid audit的RL18只改善6个query却受损7个，Yandex改善14/受损11；零命中失败的救回/新增也应单列。cal/audit只解释已经冻结的结果，不再在这两部分试阈值、选seed或选checkpoint。train/monitor细分需预先定组，样本过少则标不确定。产物为逐query归因表、完整正负、组内区间和下一步可证伪假设。

若信息不足，才设计一个受控表示/停止改动；保持原top3、随机、相同新表示Exact和RL，固定一个因素，不同时扩大投影/隐藏宽度/步数。先注册真正新的开发划分、总标签预算和seed/更新上限。E36标签仅兼容相同query/H/画像/HNSW top8/NSG/raw IP/L128/真实ID顺序；改候选源或图搜索须重新核验并补相应完整标签。

停止条件：若Exact与RL都只提高train而monitor无稳定净收益，优先标记特征/数据泛化未解，不追加epoch；若收益来自极少数query且易新增大损伤，先解决可观测的误换依据。只有相对原top3的净质量和失败配对改善才进入新的开发门，同NDC不是同时间。

## 第二优先：冻结策略下减少实际推理费用

当前每query即使第一步停，也算全部56个76维集合特征和MLP；83,328次MLP乘加外另有query投影/特征处理。先在新独立版本做等价实现：缓存每候选公共特征、复用集合中线性部分、一次构造预分配缓冲区；若按访问状态只算需要的后继，缓存已经算过的集合。保证浮点处理/tie停止/三步轨迹与冻结原模型一致，遇到边界分数差时必须回归，不能默许动作漂移。

此项可复用现有模型/标签，没有新训练；真实输出parity和计时需要新预定小规模调用预算，不能使用E36剩余额度。对照原top3、原E36选择器、等价实现，统一CPU15/线程1、加载预热和五轮轮换plain完整wall，另报分段耗时以定位原因。减少打分的近似/蒸馏若改变动作，属于新方法，转入第一优先的完整质量控制。

阶段产物是源码/模型/输入SHA、原生动作/入口/完整返回一致性、全路径时间和分段成本。如果等价优化仍显著付费且质量净收益不稳，停止扩大正式前沿。只有新开发质量通过且成本有希望，才冻结模型与新评估范围进行同机单线程多L Recall–QPS比较；原NSG/Fast/GT10基线完整计时。不凭NDC或单L结果替换默认。

## 第三优先：局部图交换补充候选访问空间

这不是本轮已实现的query换点策略。E35两原HNSW底层强连通，但WebVid仍有未评分到效用最优点的query；可能需要补充候选可达性。先利用已有E35已评分集合和E36候选内部空间判断是否存在“必须换访问路径”的证据，不能单凭静态度数归因。

若进入实验，固定H/真实ID/画像、度预算、入口和原NSG，以有限边交换（或另一个单独导航坐标方案）作为局部编辑；保护出入可达树/度和原图回退，每次真实构图与原HNSW→NSG反馈都计成本。对照原图、同次数/度分布随机交换、简单启发式及学习；旧E33删边已做，新增交换必须说明保留/补充边的机制差异。图变后候选和联合标签失效部分要重新生成，不能照搬E36的56表。

前置检查是连通性、degree/ID及原kernel一致性，质量门是实际联合收益、总时间和独立开发，不把连通改善当目标成功。先定单一动作域、两seed和有限更新/真实查询上限，开发失败即收口。全局聚类点/pool更换会扩大重建链，优先级更低；没有当前证据自动授权新GT、validation/held-out或无界迭代。

## 接续入口和可复制说明

完整阅读AGENTS→summary→spec→本文件→s-experiment，再从[历史25](experiment_history/25_query_swap_policy.md)读E36协议、模型选择、完整训练/开发/时间与验收；从[历史24](experiment_history/24_hnsw_selection_diagnosis.md)追E35机制原证据，涉及旧训练控制则读[E32](experiment_history/21_direct_reward_policy.md)、[E28](experiment_history/17_gt10_shared_transform.md)，涉及改图则读[E33](experiment_history/22_hnsw_edge_rl.md)/[E34](experiment_history/23_hnsw_rl_benchmark.md)。

接续指令示例：保留E36全部冻结原件，先用已有56联合标签和query相关预测分数，区分WebVid泛化误换、有限步选择损失与Yandex正负贡献；不使用audit调参，不新训练/查询。再据结果提出一个表示或等价成本改动，列清相同策略Exact控制、真实返回核验、历史数据暴露和新调用上限。当前E36已完成，旧NO_GO只针对旧版本，不为新的明确授权制造额外确认。
'''
(R/'s-target.md').write_text(target)
spec=R/'spec.md';s=spec.read_text();s=s.replace('E35当前GT10 HNSW访问/选择最小验证已验收','E36 query相关三入口换点训练/部署已验收')
s+='''
## 查询相关三入口换点策略（E36，2026-09-11）

[协议](entry_method_exploration/20260911_query_swap_policy_v1/protocol.md)固定当前原GT10 H/画像/HNSW与NSG/raw IP，以一次HNSW top8作为候选，原top3为初态。56个rank字典序三元素集合、16动作（停止/15单点交换）、最多3步；真实入口按ID升序执行原NSG L128/K10。未修改原Fast/NSG kernel或全局图/候选库。

[common.py](entry_method_exploration/20260911_query_swap_policy_v1/src/common.py)定义状态图/预算，prepare保存源行/SHA与固定16维query投影、画像投影/pair cosine，fit1792行统计标准化76维特征。每集合特征含三候选rank/query-profile cosine/相对top1差/投影交互、画像pair cosine和query投影；先f32量化，再f64标准化/clip和1521参数MLP。F=rank先验+MLP，16后继softmax形成策略，greedy 1e−9同分优先停止，最多3步。query ID/GT/NSG结果不进入模型特征，随机控制单独使用源row hash。

[runner.cpp](entry_method_exploration/20260911_query_swap_policy_v1/src/runner.cpp)生成每query完整56真实联合返回/距离/入口/NDC；C++不读GT，Python独立评分U=命中增量−0.1×总NDC相对变化。reward为相邻U差、γ1、stop吸收。[model.py](entry_method_exploration/20260911_query_swap_policy_v1/src/model.py)/[train.py](entry_method_exploration/20260911_query_swap_policy_v1/src/train.py)实现REINFORCE加历史query-state EMA基线和同一三步策略完整期望DP控制；相同表示/seed初始化/batch/日程，两臂双seed各3000更新，缓存真实反馈不产生新NSG。checkpoint按monitor U与graph NDC门选，cal按U/NDC/seed选主模型并冻结后运行audit。

[runner_v2.cpp](entry_method_exploration/20260911_query_swap_policy_v1/src/runner_v2.cpp)是部署前增加pool距离导出/parity的独立版本；原label runner不覆盖。[deploy.py](entry_method_exploration/20260911_query_swap_policy_v1/src/deploy.py)执行fit回归、cal/audit六方法、原/主RL/主Exact的单L128五轮plain wall。计时含HNSW、query投影、全部56特征/MLP、最多三次交换、映射、原NSG及输出；GT/count/load/hash/IO在外，CPU15/实际线程1。矩阵/特征运算不记NDC，须以全wall表示费用，单L不能替代完整前沿。

[preflight](entry_method_exploration/20260911_query_swap_policy_v1/reviews/preflight.json)验收完整路径DP/策略梯度/有限差分和标签；[训练核验](entry_method_exploration/20260911_query_swap_policy_v1/reviews/training_verification.json)独立恢复全部checkpoint前向、轨迹reward/return/EMA；[部署核验](entry_method_exploration/20260911_query_swap_policy_v1/reviews/deployment_verification.json)验证原生/NumPy特征分数/动作及缓存/原kernel/wall一致。结果由[analyze_v2.py](entry_method_exploration/20260911_query_swap_policy_v1/src/analyze_v2.py)汇出CSV/JSON配对区间，首版JSON布尔错误保留并记录，0额外查询训练。[最终验收](entry_method_exploration/20260911_query_swap_policy_v1/reviews/final_audit.json)冻结源/模型/返回/图表/工作簿和文档。

输入各2048 fit（1792 train/256 monitor）、cal/audit各512，行互斥但历史使用，画像来自历史fit，非盲测；没有新validation/held-out。E28/E32两路union C8标签不兼容本轮单路top8。若query/H/画像/HNSW/NSG/metric/L/真实入口次序变化，需核验/重生成受影响标签；标准化或投影/模型变化须重导出模型并验证原生动作。当前结果与未来方案分别见summary/s-target，不能把后续图交换或等价加速写成已实现API。
'''
spec.write_text(s)
sx=R/'s-experiment.md';s=sx.read_text();needle='| E35 HNSW选点最小验证';pos=s.index(needle)
s=s[:pos]+'| E36 query相关三入口换点 | 当前GT10一次top8、真实56联合标签、RL/同策略Exact双seed共8×3000更新，38部署点和30轮单Lwall | `COMPLETE_QUERY_SWAP_POLICY`；Yandex局部正值/WebVid开发门失败，RL QPS下降8%～9%，无新validation/held-out，默认未换 | [25 query换点](experiment_history/25_query_swap_policy.md) |\n'+s[pos:];s=s.replace('当前最近完成实验已为E35','当前最近完成实验已为E36');sx.write_text(s)
hp=R/'experiment_history/README.md';s=hp.read_text();needle='\n## 写入规则';assert needle in s;s=s.replace(needle,'| [25 query相关换点](25_query_swap_policy.md) | E36：真实三入口差值反馈、query相关局部换点/停止、RL与同策略精确梯度控制、完整训练开发和单L成本 |\n'+needle);hp.write_text(s)
print('REPORT_AND_ROOT_DOCUMENTS_WRITTEN',flush=True)
