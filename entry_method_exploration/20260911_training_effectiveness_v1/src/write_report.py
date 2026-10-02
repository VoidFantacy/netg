from common import *

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers)]+['| '+' | '.join(map(str,r))+' |' for r in rows])

t=read(O/'results/analysis_tables.json');gate=read(O/'results/cache_gate.json');budget=read(O/'models/training_budget.json')
assert gate['status']=='STOP_CACHE_UTILITY_GATE'
short={DS[0]:'WebVid2.5M',DS[1]:'Yandex10M IP'}
model_table=table(['数据集','教师','原80步总目标','新选中总目标','变化','选中步','末100步最佳目标再降'],[
    [short[r['dataset']],r['cell'],f"{r['old_objective']:.6f}",f"{r['new_objective']:.6f}",f"{r['objective_change_pct']:+.3f}%",r['selected_epoch'],f"{r['best_improvement_last100_pct']:.6f}%"] for r in t['model_comparison']])
utility_table=table(['数据集','画像','缓存Recall@10','相对锚点pp','相对原同教师pp','图NDC变化'],[
    [short[r['dataset']],r['cell'],f"{next(x['candidate_recall_pct'] for x in t['cache_metrics'] if x['dataset']==r['dataset'] and x['method']=='new_'+r['cell'] and x['group']=='all'):.4f}%",
     f"{r['candidate_gain_pp']:+.4f}",f"{r['old_cell_gain_pp']:+.4f}",f"{r['graph_ndc_change_pct']:+.4f}%"] for r in gate['by_dataset']])
bound_table=table(['数据集','画像','未知query','全H Recall下界','全H Recall上界'],[
    [short[r['dataset']],r['method'],r['unknown_queries'],f"{r['full_exact_recall_lower_pct']:.4f}%",f"{r['full_exact_recall_upper_pct']:.4f}%"] for r in t['cache_metrics'] if r['group']=='all' and r['method'] in ['anchor','new_single','new_multi']])
group_table=table(['数据集','冻结分组','query数','新增命中','损失命中','净Recall变化pp','95%配对区间'],[
    [short[r['dataset']],r['group'],r['queries'],r['gained_hits'],r['lost_hits'],f"{r['candidate_delta_recall_pp']:+.4f}",f"[{r['ci95_low_pp']:+.4f}, {r['ci95_high_pp']:+.4f}]"]
    for r in t['paired_cache'] if r['method']=='new_multi' and r['reference']=='old_multi'])
sensitivity_table=table(['数据集','教师','选中/最后步','最后−选中总目标','最后−选中缓存Recall pp','改变的C8选择query'],[
    [short[r['dataset']],r['cell'],f"{r['selected_epoch']}/{r['last_epoch']}",f"{r['objective_last_minus_selected']:.3e}",f"{r['last_minus_selected_recall_pp']:+.4f}",r['candidate_changed_queries']]
    for r in t['checkpoint_sensitivity']])
text=f'''# E31 训练有效性检查

2026-09-11。已完成两集single/multi各一次、每次1200步的固定优化检查，训练阶段总耗时{budget['elapsed_seconds']:.2f}秒，低于600秒上限。结论为`TRAINING_EFFECTIVENESS_COMPLETE_OPTIMIZATION_IMPROVED_CACHE_GATE_FAILED`。

原80步配置确实还有优化余地；同一目标优化得更好后，WebVid出现进一步的局部缓存收益，Yandex仍基本不变。结果未达到预先锁定的双集效用门，故本次在缓存检查收口，新HNSW/NSG调用和QPS测量均为0。默认仍为WebVid GT10 soft、Yandex GT10 hard，依据是[E30既有同批曲线与择优](../20260911_equivalent_teacher_sets_v1/report.md)，不是本次训练耗时。

## 1. 检查的是哪一个疑点

E30原训练用Adam lr.003、80步最后点；第1步总目标在WebVid multi从0.548784升至5.034720，Yandex multi从0.938976升至3.491240，之后大部分早期步骤回落。单凭上冲或非零梯度不能证明bug；本次直接核对了目标、梯度累积和导出。

[preflight](reviews/preflight.json)逐字核验E30数学核心、teacher masks及输入，独立NumPy恢复4份旧A/W和第80步目标；[objective tests](reviews/objective_tests.json)通过90个小域枚举/有限差分及共享归一化A累积梯度测试。未发现所检验的损失、梯度或模型恢复错误。测试通过不等于所有潜在软件问题均已排除。

## 2. 固定方案与实际优化

保持W=normalize(P+AP)、A=0、无偏置shared linear、λ100×全H平均平方弦长、τ.05、margin.1、seed20260911、fit20k、float64和CPU8。single接受原T0；multi接受所有C8最高hits且最低graph NDC的严格并列完整三元组。仍是56个已标注组合上的损失增强最大分数减可接受最大分数，没有改变教师或添加未知负例。

唯一日程：1–20步lr从3e-5升至3e-4，21–200步保持，201–1200步余弦降至3e-6。每步使用完整fit梯度；仅按fit总目标最低选择checkpoint，同值取较早步，不按缓存效用或开发集选点。共4次训练、4800次更新，无重复启动或超参网格。实际训练曲线与独立数值核验见[CSV](results/model_comparison.csv)、[模型验收](reviews/model_and_cache_verification.json)。

{model_table}

同教师原/新目标可直接比较；single和multi拥有不同的可接受集合，二者目标绝对值大小不能当作性能排名。新方案四次第1步均低于初始化，避免了本例原日程的大幅早期上冲。末100步目标变化很小只是本日程末段的数值表现，不能证明全局最优或严格收敛。

![优化与缓存效用](figures/optimization_and_utility.png)

图中实线/虚线分别为新日程/原80步，比较同教师；轨迹效用用float64训练W，菱形为所选float32导出。原早期上冲在主图纵轴外，完整数值另见[前20步图](figures/first_steps.png)。

## 3. 目标下降是否转化成命中收益

以下对所有画像统一使用float32导出、float64独立打分及固定tie规则。在每query已测量的56个三元组中选最高分组合，再读取它原有的真实L128/K10 NSG标签。这里的Recall基准是锚点在相同C8域选出的组合，分别为75.1875%和90.1815%；不等于原实际HNSW入口的fit Recall。graph NDC也来自相应组合的既有原NSG计数，不等于端到端wall。

{utility_table}

WebVid multi相对原80步再增0.0910pp，配对fit-query bootstrap 95%区间为[+0.0455,+0.1340]pp；相对锚点增0.2115pp。局部信号保留，不能因为双集门未过而写成“完全无收益”。Yandex multi相对原80步为−0.0025pp，区间[−0.0185,+0.0110]pp；相对锚点−0.0040pp，区间[−0.0320,+0.0230]pp。Yandex应解释为没有观察到有效提升，而非证明稳定退化。

![缓存效用与区间](figures/cache_utility.png)

上述区间使用2000次配对query bootstrap、固定seed、无多重比较修正。样本已经用于训练，区间不是泛化置信或新盲测。原始命中差和每画像query选择保存在[paired_cache](results/paired_cache.csv)及results中各dataset的npz。

新multi相对原multi的分组如下。headroom标签沿用E30“C8 oracle是否优于原实际HNSW入口”的冻结定义；这里比较的参考画像是原multi的C8选择，所以无headroom组也可能出现相对原multi的正向修复，不能将组名误解为本表的理论零增益约束。

{group_table}

WebVid净增182个命中，其中headroom组净增171；Yandex净减5个命中。该分解定位缓存域的变化，不证明线上HNSW与NSG性能因果。

## 4. 全H、导出精度与停机边界

全H精确top3可能超出已测C8，未知组合没有被赋予“0效用标签”。表中的下界仅为最坏情况数学界，上界允许未知query命中全部10个GT；已知子集均值另存，不代替全量值。

{bound_table}

WebVid新multi相对锚点的最坏净收益界为+0.1610pp，未达到+0.20pp；其C8域的+0.2115pp仍成立。Yandex覆盖为100%，全H精确排序的已知结果同样没有训练收益，因此本次缺口在近似路由之前就存在。即使放宽WebVid未知组合的保守界，Yandex也会使预设双集门失败，停止结论不只依赖这个保守界。

浮点导出与离散top3需要区分。WebVid multi选中float64训练W的候选Recall为75.4010%，统一float32导出后为75.3990%；主结论使用后者。目标末段平稳也不保证离散选择完全不变：

{sensitivity_table}

这项只读[checkpoint诊断](reviews/checkpoint_diagnostics.json)没有更改选点规则或更新模型。即使采用最后点，Yandex差值仍远小于推进门；不能在看过效用后改选更有利迭代。优化充分性是相对这一次固定日程的经验检查，无全局最优证书；较小的梯度范数也不是非光滑模型的终止证明。

## 5. 明确停止位置与下一步

预锁[协议](protocol.md)要求同一种cell在两集均：C8 Recall相对锚点≥+0.20pp、胜过对应原cell、graph NDC≤+1%，全H已知覆盖≥99.5%且最坏净Recall界≥+0.20pp。[缓存门](results/cache_gate.json)为`STOP_CACHE_UTILITY_GATE`，single/multi均未满足。当前没有进入真实fit/cal/audit补测，也没有读取新validation或held-out、产生新的QPS点。

这次验证支持：原80步未耗尽可获得的目标下降；额外下降在WebVid能换来一部分真实标签收益，但未使Yandex受益。不能把当前固定方案缺少双集提升全归因于优化不足。它不证明所有共享画像、所有正则强度或其他目标都不可能有效。

按事先约定，收口这一固定教师/共享画像/λ100的优化支线，保留WebVid局部缓存改善及GT10既有成果。接续优先做原GT10方法的独立复现与公平基线比较，先锁定新的复现问题、数据/seed/图身份与预算；不以本次结果自动启动下一轮训练或held-out。当前推荐仍由E30的完整单线程Recall–QPS证据决定。

## 6. 成本、保护与交付

训练阶段的合计计时包含数据加载和训练诊断，共{budget['elapsed_seconds']:.2f}s；4次fit函数耗时合计{sum(r['training_seconds'] for r in t['model_comparison']):.2f}s。完整训练进程含启动与冻结核验的wall为{read(O/'logs/training_process.json')['wall_seconds']:.2f}s，同样低于600s硬限。训练前身份/数学复核与训练后NumPy分析、图表和文档不计作训练或查询QPS。新标签0；复用224万逻辑条真实标签。新原NSG调用0、HNSW查询0、开发/validation测试0、QPS点0，未用历史预算扩大矩阵。

E30及其保护链9098个旧文件身份逐项核验；根文档修改前快照保存在source_before。全部源码/输入与新模型各有冻结清单；完整模型、gate、图表、Excel和文档复核见[最终验收](reviews/final_audit.json)。图表不是合成性能曲线；三图均提供PNG/SVG，Excel含完整数值。

- [训练与效用图](figures/optimization_and_utility.svg)、[原始早期轨迹](figures/first_steps.svg)、[所选画像效用](figures/cache_utility.svg)、[Excel](chart_data.xlsx)。
- [完整训练轨迹](results/training_curve.csv)、[缓存指标与全H界](results/cache_metrics.csv)、[逐组配对差值](results/paired_cache.csv)、[停机敏感性](results/checkpoint_sensitivity.csv)。
- [历史20](../../experiment_history/20_training_effectiveness.md)、[当前总结](../../summary.md)、[下一阶段](../../s-target.md)。

本目录是已完成的独立版本，脚本会拒绝覆盖训练产物。复现应先建立新的目录、协议与冻结身份；原执行顺序为preflight→test_objective→run_training→analyze→diagnose_checkpoints→plot→report/docs→独立最终验收。不能直接重启本版本runner。
'''
(O/'report.md').write_text(text)
dump(O/'results/conclusion.json',dict(status='TRAINING_EFFECTIVENESS_COMPLETE_OPTIMIZATION_IMPROVED_CACHE_GATE_FAILED',
    optimization_improved_both_datasets=True,cache_gate=gate['status'],passing_cells=[],new_labels=0,real_search_calls=0,new_QPS_points=0,
    recommendation={'webvid2_5m_light_v1':'gt10_soft','yandex_t2i_official10M_ip_v1':'gt10_hard'},
    basis='E30 measured frontier retained; E31 only verifies fixed-objective training and cached utility',
    next='close fixed teacher/shared-linear/lambda100 optimization branch; plan independent GT10 replication'))
dump(O/'results/report_tables.json',dict(model_table=model_table,utility_table=utility_table,bound_table=bound_table,group_table=group_table))
print('REPORT_COMPLETE',flush=True)
