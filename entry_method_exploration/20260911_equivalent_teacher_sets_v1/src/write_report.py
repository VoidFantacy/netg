from common import *
from analyze import SHORT,NAMES,DEFAULT

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+
        ['| '+' | '.join(str(v) for v in row)+' |' for row in rows])

def fmt(value,d=3,signed=False):
    if value is None:return '—'
    return f'{value:+.{d}f}' if signed else f'{value:.{d}f}'

assert read(O/'state.json')['status']=='PLOTS_COMPLETE_REPORT_REVIEW_PENDING'
t=read(O/'results/analysis_tables.json');selection=read(O/'results/method_selection.json');gate=read(O/'results/development_gate.json')
verification=read(O/'reviews/output_verification.json');jobs=read(O/'logs/evaluation_jobs.json');training=read(O/'models/training_runs.json')
new_names={'single','multi','single_matched','multi_matched'}
new_win=any(d['recommended'] in new_names for d in selection['decisions'])
any_replacement=any(d['recommended']!=d['default'] for d in selection['decisions'])
status=('EQUIVALENT_TEACHER_SETS_COMPLETE_WITH_LOCAL_REPLACEMENT' if new_win else
        'EQUIVALENT_TEACHER_SETS_COMPLETE_WITH_EXISTING_BASELINE_REPLACEMENT' if any_replacement else
        'EQUIVALENT_TEACHER_SETS_COMPLETE_NO_RELIABLE_REPLACEMENT')
conclusion=dict(status=status,recommendations=selection['decisions'],development_gate=gate['status'],
    new_method_recommended=new_win,
    scope='two historical validation query sets; one fixed H/NSG and optimization seed; five timings; no fresh blind confirmation')
dump(O/'results/conclusion.json',conclusion)
out=['# 等效三入口教师：真实检索、漂移对照与最佳方法选择','']
out += [('本轮新方法在部分数据集达到预设本地替换条件，具体推荐及范围如下。' if new_win else
         '本轮有历史基线达到预设本地替换条件，新方法未达到；具体推荐及范围如下。' if any_replacement else
         '本轮没有产生足以替换原默认方法的可靠证据。')+
        ' 多集合教师、单教师控制、改动幅度匹配和两数据集真实Recall–QPS均已完成。所有正负结果保留，原图/H/kernel及历史产物未覆盖。','']
out += ['## 1. 最后选择什么','']
out += [table(['数据集','本次插值速度几何均值最高','相对原默认','有证据支持的推荐','判定'],[
    [d['dataset'],NAMES[d['descriptive_fastest']],fmt(d['descriptive_fastest_change_pct'],2,True)+'%',NAMES[d['recommended']],
     '通过替换条件' if d['recommended']!=d['default'] else '保留原默认'] for d in selection['decisions']]),'']
out += ['“数值最快”按三个共同Recall参照的插值QPS几何平均排序；“推荐”还要求至少两个目标中位速度≥+3%、五轮对应比值全部>1、其他目标无≥3%退化，并覆盖全部参照。没有符合者就保留默认。它们是不同判断，不能把微小数值领先包装成稳定胜出。','',
        '参照为WebVid Recall 75/80/85%、Yandex 90/95/98%，来自前作已知覆盖范围；本次不是盲设目标。比较只在实测非支配曲线的Recall–logQPS之间插值，不外推，不冒充额外实测的精确等Recall点。','',
        '![主要Recall–QPS曲线](figures/recall_qps_main.png)','',
        '每个点对应实际L64/128/256/400/800，QPS为五次单线程完整warm/plain批次的中位数；误差线为五轮范围。连线没有生成新测量。','',
        '![全部方法](figures/recall_qps_all.png)','',
        '全部12种方法均在本轮重新计时，旧曲线仅用于输出回归，不跨批拼接QPS。图表原值、全部五轮wall、训练及控制记录见[Excel](chart_data.xlsx)和[all_points.csv](results/all_points.csv)。','']
out += ['## 2. 新方法究竟改了什么','',table(['方法','可接受教师','部署画像','作用'],[
    ['single','原唯一T0','共享linear原生W','相同新损失/已知竞争域的单教师控制'],
    ['multi','最高hits且最少graph NDC的全部并列三元组G','共享linear原生W','移除G内部的身份区分'],
    ['multi_matched','沿用multi训练','向GT10锚点缩放到single的均方位移','固定整体改动幅度'],
    ['single_matched','沿用single','与single字节相同，alias','同一实际测量，不伪装成独立第四模型']]),'',
    '两集都由multi具有稍大的原生位移，因此本轮各有3份唯一W。在线仍是原始query→一份Micro-HNSW top3→三个真实hub→原NSG，无在线网络或组合重排。E29 CE/margin、E28 MLP及GT画像/NSG/Fast共同作为历史基线。','',
    '共同训练为GT10 hard锚点、无偏置共享linear、零残差初始化、float64、λ100、τ=.05、μ=.1、Adam .003、全fit20k累积、80轮最后epoch、同seed20260911。只训练4次，所有画像及控制系数在新开发query前冻结，没有通过开发/validation调参。','',
    '目标为`max_C(F+.1×非接受指示)−max_接受F`，C始终是已标注56个完整三元组。它只对C内“是否选中可接受集合”给上界；未知全H组合不被当作已知负例，完整NSG效果必须实际测量。E29→single同时改变竞争域与损失形式，所以该差异不是多教师的单因素效果。方法推导、已有理论及限制见[research.md](research.md)。','']
out += ['## 3. 三个预设召回处的完整比较','',table(['数据集','方法','覆盖目标','插值QPS几何均变','通过+3%且五轮均快的目标','≥3%退化目标'],[
    [r['dataset'],NAMES[r['method']],r['covered_targets'],fmt(r['geomean_change_pct'],2,True)+'%',r['passing_targets'],r['regression_targets']]
    for r in t['method_ranking']]),'',
    '![预设召回处的速度变化](figures/selection_targets.png)','',
    '范围线使用中位前沿确定的相同插值段，再代入五轮原始速度比；不是统计置信区间，也未传播Recall采样不确定性。QPS轮次与query bootstrap分别解释，未删除慢轮或追加择优计时。','']
out += ['各目标的描述性最快点如下。它用于比较曲线，不是根据query/GT选择方法的在线策略，也没有实现跨方法的自动切换：','',
    table(['数据集','Recall参照','数值最快方法','插值QPS','相对原默认'],[
      [r['dataset'],fmt(r['recall_pct'],0)+'%',NAMES[r['descriptive_fastest']],fmt(r['qps'],1),fmt(r['change_vs_default_pct'],2,True)+'%'] for r in t['target_winners']]),'']
out += ['在同样的预设召回范围内，分段插值曲线的数值最高者如下。分界由实测曲线之间的交点计算，边界附近的细小优势受计时波动影响；这不改变上面的默认替换规则：','',
    table(['数据集','Recall区间','描述性最快曲线'],[
        [r['dataset'],fmt(r['recall_low_pct'],3)+'%–'+fmt(r['recall_high_pct'],3)+'%',NAMES[r['method']]] for r in t['frontier_intervals']]),'',
    '每个固定L中，同时考虑Recall较高和QPS较高的非支配方法如下；同L筛选不等于最终跨L前沿。跨全部方法和L的非支配标记另存于[all_points.csv](results/all_points.csv)的`pareto_all_methods_and_L`列：','',
    table(['数据集','L','同L非支配方法'],[
        [SHORT[ds],L,', '.join(NAMES[r['method']] for r in t['all_points'] if r['dataset']==SHORT[ds] and r['stage']=='validation' and r['L']==L and r['pareto_same_L'])]
        for ds in DS for L in [64,128,256,400,800]]),'']
spread=[]
for ds in DS:
    rows=[r for r in t['all_points'] if r['dataset']==SHORT[ds] and r['stage']=='validation'];values=sorted(r['timing_spread_pct'] for r in rows)
    import statistics
    spread.append([SHORT[ds],len(rows),fmt(statistics.median(values),2)+'%',fmt(max(values),2)+'%',sum(v>3 for v in values)])
out += ['五轮计时波动以`(最大QPS−最小QPS)/中位QPS`描述：','',table(['数据集','正式点数','中位波动','最大波动','波动>3%的点'],spread),'',
    '该范围描述本机这些轮次的变化，不能直接当成方法效果的置信区间，也不能把较小的正负速度比解释为稳定差异。','']
out += ['## 4. 新模型与桥接对照的全部五L正负','',
    '下表均相对同批GT10 hard；Recall变化为百分点，QPS为同L比值。两者同时给出也不等于精确等Recall加速。95%区间来自2000次配对query bootstrap，未作多重比较校正。','']
for ds in DS:
    rows=[r for r in t['delta_gt10'] if r['dataset']==SHORT[ds] and r['stage']=='validation' and r['method'] in new_names|{'e29_cost_margin'}]
    out += ['### '+SHORT[ds],'',table(['L','方法','ΔRecall pp','95%区间','Δ同L QPS','Δgraph NDC','获益/受损query'],[
        [r['L'],NAMES[r['method']],fmt(r['delta_recall_pp'],3,True),f"[{fmt(r['ci_low_pp'],3,True)}, {fmt(r['ci_high_pp'],3,True)}]",
         fmt(r['same_L_qps_change_pct'],2,True)+'%',fmt(r['delta_graph_ndc_pct'],2,True)+'%',f"{r['improved_queries']}/{r['harmed_queries']}"] for r in rows]),'']
out += ['## 5. 教师是否确实有多个等效答案','',table(['数据集','组','query数','G数量中位数','多个G比例','原Recall','教师Recall','原graph NDC','教师graph NDC'],[
    [r['dataset'],r['group'],r['queries'],fmt(r['equivalent_median'],0),fmt(r['multiple_fraction']*100,2)+'%',fmt(r['baseline_recall_pct'],3)+'%',
     fmt(r['teacher_recall_pct'],3)+'%',fmt(r['baseline_graph_ndc'],2),fmt(r['teacher_graph_ndc'],2)] for r in t['teacher_sets']]),'',
    '![严格等效组合数量分布](figures/label_equivalence.png)','',
    'G保留了原cost教师的最高hits和最少graph NDC，没有放宽成本标准。它只描述C8内教师；不代表全H上界、相同wall或可部署oracle。不同G成员可以命中不同GT成员，等效针对本协议的命中计数与graph NDC。','']
out += ['## 6. 拟合、组合结构与实际推动','',
    '![共同G上的训练接受率](figures/training_acceptance.png)','',
    '所有曲线用同一G评价。候选内选择、全H精确top3和HNSW实际入口分别报告，不能把三者的接受率混为一谈。','']
align=[]
for ds in DS:
    for cell in CELLS:
        rows=[r for r in t['training_alignment'] if r['dataset']==SHORT[ds] and r['method']==cell and r['teacher']=='multi' and r['group']=='all']
        a,b=rows[0],rows[-1]
        align.append([SHORT[ds],NAMES[cell],f"{a['candidate_acceptance']*100:.3f}%→{b['candidate_acceptance']*100:.3f}%",
            f"{a['full_exact_accepted_fraction']*100:.3f}%→{b['full_exact_accepted_fraction']*100:.3f}%",
            fmt(b['full_exact_known_fraction']*100,3)+'%'])
out += [table(['数据集','训练模型','C8最优属于G 初→末','全H精确top3属于G 初→末','末期全H预测仍在C8'],align),'',
    table(['数据集','模型','本格loss初→末','目标初→末','末期梯度范数','训练秒'],[
    [r['dataset'],NAMES[r['method']],f"{r['first_loss']:.4f}→{r['last_loss']:.4f}",f"{r['first_objective']:.4f}→{r['last_objective']:.4f}",
     fmt(r['final_gradient_norm'],4),fmt(r['training_seconds'],2)] for r in t['model_summary']]),'',
    '固定80轮和同优化器不构成收敛证书，且两目标的数值尺度/有效梯度未被归一化为同一种风险。最终梯度和完整轨迹保留；不据有限预算失败推导不可学习。','']
out += ['同一份分数下，两种教师是否真的改变每query对hub分数的梯度：','',
    table(['数据集','检查点','组','分数梯度不同','最佳好组合变化','最强竞争组合变化','single−multi平均loss'],[
    [r['dataset'],r['checkpoint'],r['group'],fmt(r['score_gradient_changed_fraction']*100,2)+'%',
     fmt(r['accepted_winner_changed_fraction']*100,2)+'%',fmt(r['loss_augmented_winner_changed_fraction']*100,2)+'%',fmt(r['single_minus_multi_loss'],5)]
    for r in t['objective_disagreement'] if r['checkpoint'] in ['initial','multi']]),'',
    '这是冻结后对既有fit的只读分解，没有optimizer step或新搜索。G多不意味着每条训练约束都变化：只有当前最强竞争组合或最佳接受组合改变时才可能影响梯度。上表是对hub logits的逐query梯度，不是参数梯度冲突或验证性能的因果证明。','',
    '具体地，原T0已经在严格并列组内按原锚点分数择优；初始化时，两集所有query的最高分可接受组合均仍是T0。因此，起点的多教师差异来自去掉其它G成员作为“错误竞争者”的margin，而不是找到一个分数更高的新正例。真实有命中空间组的分数梯度改变比例仅WebVid 1.04%、Yandex 0.65%，没有空间组则为15.06%、12.11%。在最终multi分数下，有空间组升至6.40%、3.42%，仍低于没有空间组的19.01%、14.01%。这是对初始与最终两个已检查分数面的描述，不能覆盖整个优化轨迹或证明性能因果。','',
    '结合单/多教师实际收益很接近，这组证据削弱了“唯一教师身份是当前主要瓶颈”的判断。等效答案的数量本身不足以说明训练中有同样多的有害约束。它也没有排除不同目标、优化方式或表达能力的可能性。','',
    '完整组合不能任意拆成成员软标签。下表检查G的共同必需入口及其成员频率top3；频率使用了真实教师标签，只是结构诊断，不是学习方法或可部署对照。即使该诊断接受率高，也不能推出query到这些入口的映射容易学习。','',
    table(['数据集','组','共同必需入口均数','由共同核心和成员并集完整描述的比例','成员频率top3仍属于G','频率top3损失Recall pp'],[
    [r['dataset'],r['group'],fmt(r['mean_mandatory_entries'],2),fmt(r['core_union_closed_fraction']*100,2)+'%',
     fmt(r['teacher_member_frequency_top3_accepted_fraction']*100,2)+'%',fmt(r['frequency_top3_loss_recall_pp'],3)] for r in t['set_anatomy']]),'']
out += ['## 7. 控制画像改动幅度','',table(['数据集','single位移','multi位移','目标位移','multi缩放t','导出相对误差'],[
    [r['dataset'],fmt(r['single_raw_drift'],9),fmt(r['multi_raw_drift'],9),fmt(r['target_drift'],9),fmt(r['alpha'],6),f"{r['relative_error']:.2e}"] for r in t['drift_match']]),'',
    '![漂移控制及实际fit表现](figures/drift_control.png)','',
    '位移是全H的平均平方弦长。缩放系数只由fit模型得到，single_matched与single逐位相同，直接引用同一测量；multi_matched独立构建微型图并执行原NSG。该控制不保证逐hub改动或入口变化数量相同，也不能用缩放前输出模拟缩放后的QPS。','',
    '共同位移下multi−single的实际差值：','',
    table(['数据集','阶段','L','ΔRecall pp','95%区间','Δgraph NDC','Δ同L QPS'],[
    [r['dataset'],r['stage'],r['L'],fmt(r['delta_recall_pp'],3,True),f"[{fmt(r['ci_low_pp'],3,True)}, {fmt(r['ci_high_pp'],3,True)}]",
     fmt(r['delta_graph_ndc_pct'],2,True)+'%',fmt(r['same_L_qps_change_pct'],2,True)+'%' if r['same_L_qps_change_pct'] is not None else '未计时']
    for r in t['contrasts'] if r['contrast']=='matched_multi_minus_single' and not r['exact'] and r['stage'] in ['fit','validation']]),'']
out += ['## 8. 从完整fit到开发与最终验证','',
    '![完整fit到验证的实际变化](figures/fit_to_validation.png)','',
    table(['数据集','模型','fit L128 Recall','cal L128 Recall','audit L128 Recall','validation L128 Recall'],[
    [SHORT[ds],NAMES[key]]+[fmt(next(r['recall_pct'] for r in t['all_points'] if r['dataset']==SHORT[ds] and r['method']==key and r['stage']==stage and r['L']==128 and not r['exact']),3)+'%'
     for stage in ['fit','cal','audit','validation']] for ds in DS for key in ['gt10_hard','e29_cost_margin','single','multi','multi_matched']]),'',
    '每个split内对照同一baseline，各split难度不同，不把绝对Recall差直接解释为过拟合。以下分组依据原C8标签，不能在部署时用GT决定是否改道：','',
    table(['数据集','模型','组','ΔRecall pp','净增命中','增加/丢失命中','获益/受损query','教师正空间保留','Δgraph NDC'],[
    [r['dataset'],NAMES[r['method']],r['group'],fmt(r['delta_recall_pp'],3,True),r['net_hits'],f"{r['gained_hits']}/{r['lost_hits']}",
     f"{r['improved_queries']}/{r['harmed_queries']}",fmt(r['teacher_gain_retained_pct'],2)+'%' if r['teacher_gain_retained_pct'] is not None else '不适用',
     fmt(r['delta_graph_ndc_pct'],2,True)+'%'] for r in t['fit_groups'] if r['method'] in new_names and r['group']!='all']),'',
    '空间保留分子为逐query实际正增命中与教师增量的较小者之和，分母为教师正增量总和；它只描述已有候选教师的训练侧迁移。完整fit统计包括C8外预测的实际搜索结果，未把条件子集当作全量。','']
out += ['实际HNSW入口接受情况：','',table(['数据集','方法','实际入口仍在C8','唯一教师匹配','任一G匹配','不同于唯一教师但同属G','C8外query'],[
    [r['dataset'],NAMES[r['method']],fmt(r['known_fraction']*100,3)+'%',fmt(r['unique_teacher_match']*100,3)+'%',fmt(r['equivalent_acceptance']*100,3)+'%',
     r['different_but_equivalent_queries'],r['outside_C8_queries']] for r in t['fit_acceptance'] if r['group']=='all']),'',
    'audit上的精确入口诊断只看同一画像的全H分数，不是按真实搜索效用选优的oracle，也没有正式QPS：','']
exact_rows=[]
for ds in DS:
    for key in ['gt10_hard','e29_cost_margin','single','multi','multi_matched']:
        get=lambda exact:next(r for r in t['all_points'] if r['dataset']==SHORT[ds] and r['stage']=='audit' and r['method']==key and r['L']==128 and r['exact']==exact)
        a,b=get(False),get(True)
        exact_rows.append([SHORT[ds],NAMES[key],fmt(a['recall_pct'],3)+'%',fmt(b['recall_pct'],3)+'%',fmt(b['recall_pct']-a['recall_pct'],3,True)])
out += [table(['数据集','方法','HNSW Recall','exact Recall','exact−HNSW pp'],exact_rows),'']
out += ['## 9. 预设推进门与收口','',table(['数据集','multi fit净增pp','fit成本增幅','同漂移multi−single pp','cal均增pp','audit均增pp','未满足条件'],[
    [r['dataset'],fmt(r['fit_gain_pp'],3,True),fmt(r['fit_graph_ndc_pct'],2,True)+'%',fmt(r['matched_multi_minus_single_pp'],3,True),
     fmt(r['dev_mean_gain_pp']['cal'],3,True),fmt(r['dev_mean_gain_pp']['audit'],3,True),', '.join(k for k,v in r['conditions'].items() if not v) or '全部满足'] for r in gate['datasets']]),'',
    '推进条件事先锁定为两集fit各≥+0.20pp、图NDC增幅≤1%、同漂移multi优于single、cal/audit各自平均L64/128均正。该条件控制是否继续扩大研究，不能替代最终性能判断。','',
    ('本轮达到推进条件，但后续任何扩展仍需新版本与明确范围。' if gate['status']=='PASS_CONTINUATION_SIGNAL' else
     '本轮未达到推进条件，停止这套共享linear/固定目标的进一步优化和容量扩展。按照用户要求，已冻结有效模型仍完成最终曲线和择优，不因开发负值省略最终交付。'),'',
    '这不否定所有多教师学习、其它优化器或表达形式，也不抹去原GT10和E28 MLP的历史局部正信号。当前能支持的结论限定于本轮G定义、已知C8竞争域、共享linear、固定正则/80轮和一套H/原图。','']
out += ['## 10. 实际成本与核验','',table(['项目','实际'],[
    ['复用训练标签','2,240,000个逻辑三元组；原始IDs全量重评分'],['新增训练标签 / 合成NSG','0 / 0'],
    ['训练',f"{len(training)}次，CPU8，共{sum(r['training_seconds'] for r in training):.2f}s，包含对齐诊断"],
    ['漂移控制','每集1个新W，额外optimizer step=0，系数仅来自fit'],
    ['原NSG调用',f"{sum(j['reserved_calls'] for j in jobs):,}，repair=0"],
    ['真实输出',f"{verification['total_points']}点，{verification['total_query_outputs']:,}个query输出独立评分"],
    ['正式曲线',f"{verification['formal_points']}点，每点5次独立warm/plain单线程wall"],
    ['旧方法逐位回归',f"{verification['historical_regression_outputs']:,}个输出，含ID/距离bits/入口/图与路由NDC"],
    ['完整fit与已知标签一致',f"{verification['fit_native_cache_parity_outputs']:,}个实际相同三入口结果"],
    ['评测进程总wall',f"{sum(j['seconds'] for j in jobs):.2f}s，含加载/构建/count/核验，不能当成QPS"],
    ['准备及保护',f"{read(O/'reviews/teacher_verification.json')['seconds']:.2f}s"],
    ['独立编译',f"{read(O/'bin/evaluate.build.json')['seconds']:.2f}s，仅修改3→5计时重复合同"],
    ['从零GT/QGT/主图成本','本轮未新测；既有依赖不隐去']]),'',
    '机器为CPU-only Intel Xeon 6982P-C；正式固定CPU15，实际进程/OMP线程1，OMP/OpenBLAS/MKL1。query阶段没有并发训练或矩阵分析。数据/图/旧源及模型通过完整身份保护，所有训练画像在开发前冻结。最终核验入口见[final_audit.json](reviews/final_audit.json)。','',
    'fit/cal/audit/validation均有历史使用；只测试一个优化种子、一个H/图、固定80轮与目标。五轮计时不构成独立query样本。held-out未读取/hash，本轮选择是有前作信息的本地探索，不是新的盲测或论文充分性确认。','',
    '## 11. 原始产物与复现入口','',
    '- [冻结协议](protocol.md)、[方法研究](research.md)、[标签检查](reviews/teacher_verification.json)、[损失测试](reviews/objective_tests.json)。',
    '- [模型独立核验](reviews/model_verification.json)、[开发门](results/development_gate.json)、[选择判定](results/method_selection.json)、[所有原始点](results/all_points.csv)。',
    '- [同漂移差值](results/contrasts.csv)、[完整fit分组](results/fit_groups.csv)、[梯度差异解释](results/objective_disagreement.csv)、[Excel](chart_data.xlsx)。',
    '- [调用账](logs/evaluation_jobs.json)、[输出验收](reviews/output_verification.json)、[状态](state.json)。','',
    '启动顺序为prepare→build/test_objective→train→match_drift→verify_models→run_evaluation→analyze→diagnose_sets→plot→write_report→文档同步→图表/数据人工复核→final_audit。新执行必须创建独立目录；本版本原runner拒绝已有输出，不能为了更好结果覆盖记录。','']
(O/'report.md').write_text('\n'.join(out))
dump(O/'state.json',dict(status='REPORT_COMPLETE_FINAL_AUDIT_PENDING',training_runs=4,real_search_calls=NORMAL_CAP,heldout_access=False))
print(status,flush=True)
