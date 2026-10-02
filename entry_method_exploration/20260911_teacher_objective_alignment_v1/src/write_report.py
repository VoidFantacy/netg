from analyze import *

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+
                     ['| '+' | '.join(str(v) for v in row)+' |' for row in rows])

def num(value,digits=3,sign=False):
    if value is None:return '未测/未覆盖'
    return f'{value:+.{digits}f}' if sign else f'{value:.{digits}f}'

def main():
    t=read(O/'results/analysis_tables.json')
    gates=read(O/'results/performance_gate.json')['methods']
    ver=read(O/'reviews/output_verification.json')
    teacher=read(O/'reviews/teacher_verification.json')['datasets']
    train=read(O/'models/training_runs.json')
    gradient=read(O/'results/gradient_diagnostics.json')
    jobs=read(O/'logs/evaluation_jobs.json')
    successful=[g['method'] for g in gates if g['dual_dataset_GO']]
    verdict='本轮建立预设的本地双数据性能条件：'+', '.join(successful) if successful else '本轮未建立优于原GT10的稳定双数据Recall–QPS优势。'
    conclusion='TEACHER_OBJECTIVE_ALIGNMENT_LOCAL_GO' if successful else 'TEACHER_OBJECTIVE_ALIGNMENT_COMPLETE_NO_STABLE_DUAL_GAIN'
    recommendation=('通过预设条件的候选仍需和原冻结GT10 soft及历史使用限制一起判断。' if successful else
        '当前建议继续保留WebVid已冻结GT10 soft、Yandex GT10 hard；本轮四格均没有足够证据支持替换。')
    report=['# 教师标签与训练目标对齐：2×2真实检索研究',
        verdict+' '+recommendation+' 所有教师/损失对照均已训练、冻结并完成真实查询，下面分别报告监督拟合、实际命中和端到端速度。',
        '两数据集、8次共享linear训练、11种方法×5个L，共110个正式点，每点3次单线程完整warm/plain计时。另对完整fit20k、cal1024、audit1024执行真实检索；旧模型逐位恢复后同批重新计时。这里沿用历史验证查询，不能称为新的盲测。',
        '## 1. 主Recall–QPS图',
        '![四格与原GT10的完整曲线](figures/recall_qps_main.png)',
        '每个点均为实际L64/128/256/400/800测试；QPS为三轮中位数，误差线为三轮最小/最大值，纵轴对数。连线不是新增测量。原始数据见[all_points.csv](results/all_points.csv)，全部图表数据及训练记录见[chart_data.xlsx](chart_data.xlsx)。',
        '## 2. 四个模型究竟改了什么',
        table(['名称','教师','损失','与原对照的实质区别'],[
            ['cost_ce','原max-hits/min-NDC完整三入口','全H集合CE','E28 linear λ100恢复对照'],
            ['keep_ce','无额外hits空间时保留原入口','相同集合CE','只改教师'],
            ['cost_margin','原完整三入口教师','结构化top3 margin','只改损失'],
            ['keep_margin','无额外hits空间时保留原入口','相同margin','两轴同时改变，交互单列']]),
        '共同设置：GT10 hard锚点，W=normalize(P+AP)，无偏置共享linear；λ100、τ=.05、80epoch、Adam .003、全fit梯度累积、固定seed20260911。margin μ=.1，对应单位query分数差.005。所有模型在新开发查询前冻结，没有根据cal/audit/validation换超参数或epoch。原cost_ce在两集都逐位恢复E28 linear_r100。',
        '在线始终是raw query→一份microHNSW top3→三个真实hub→原NSG。microHNSW为M16/efConstruction200/efSearch10、seed20260828，按真实ID升序注入；原Fast30K保留seed100/legacy顺序。没有在线网络前向、GT、重排或额外搜索。',
        '## 3. 哪个更好：完整前沿与预设参照',
        '下表在预设WebVid 75/80/85%、Yandex 90/95/98%召回处，对各自实测非支配曲线作Recall–logQPS插值，汇总相对原GT10 hard的速度比。只有实际共同覆盖的点参与；不外推。这是有前作信息的粗网格比较，不是额外实测的精确等Recall点。',
        table(['方法','数据集','覆盖点','插值QPS几何平均变化','满足≥3%且三轮均更快的点','≥3%退化点'],[
            [g['method'],d['dataset'],d['covered_targets'],num(d['geometric_mean_qps_change_pct'],2,True)+'%',d['passing_targets'],d['regression_targets']]
            for g in gates for d in g['datasets']]),
        '![预设召回处的插值QPS变化](figures/interpolated_qps.png)',
        '色带是三个对应计时轮次的插值比值范围，不是统计置信区间；使用中位前沿确定的相同插值段。预设本地性能条件要求两集各至少两个覆盖点≥3%，三个比值均>1且没有约定的退化点；覆盖不足单独记录。全部判定见[performance_gate.json](results/performance_gate.json)。',
        '本轮Yandex计时波动较大，小幅负速度比也不能写成稳定退化。以每点(max QPS−min QPS)/median QPS计，WebVid的55点中位波动为0.27%、最大4.01%，2点超过3%；Yandex分别为1.45%、12.69%，19点超过3%。全部轮次原值保留在CSV/Excel，并画出范围；没有删慢轮、追加择优计时或凭一个正点宣称提升。该波动限制了细微速度排序的可信度，未将其原因归给未测量的系统因素。',
        '原正式画像仍分别是WebVid已冻结GT10 soft和Yandex GT10 hard，另保留E28 MLP局部信号。下图把这些基线与NSG/Fast/GT1同时列出，不能仅在四格内部选一个相对较好者就声称替代原方法。',
        '![全部11种方法](figures/recall_qps_all.png)',
        'L128绝对值作为量级参照：',
        table(['数据集','方法','Recall@10','QPS中位数','三轮QPS范围'],[
            [r['dataset'],r['method'],num(r['recall_pct'])+'%',num(r['qps'],1),num(r['qps_min'],1)+'–'+num(r['qps_max'],1)]
            for r in t['all_points'] if r['stage']=='validation' and r['L']==128 and r['method'] in ['gt10_hard','gt10_soft','e28_mlp']+CELLS]),
        '## 4. 全部五L正负变化',
        '以下相对本批GT10 hard，pp为百分点，QPS列是同L比值，不是等Recall加速。95%区间来自相同query的2000次配对bootstrap，未做多重比较校正；三轮计时不增加Recall样本。']
    for ds in DS:
        report += ['### '+SHORT[ds],table(['L','方法','ΔRecall pp','95%区间','Δ同L QPS','Δgraph NDC','获益/受损query'],[
            [r['L'],r['method'],num(r['delta_recall_pp'],3,True),'['+num(r['ci_low_pp'],3,True)+', '+num(r['ci_high_pp'],3,True)+']',
             num(r['delta_qps_pct'],2,True)+'%',num(r['delta_graph_ndc_pct'],2,True)+'%',str(r['improved_queries'])+'/'+str(r['harmed_queries'])]
            for r in t['differences'] if r['dataset']==SHORT[ds] and r['stage']=='validation' and r['method'] in CELLS])]
    report += ['## 5. 教师与损失各自的作用',
        '![两个因素与交互的逐L变化](figures/factor_effects.png)',
        '第一行在相同损失下比较keep−cost，第二行在相同教师下比较margin−CE，第三行是两项教师效应之差。色带为配对query的未校正95%区间，全部基于真实HNSW→NSG输出。若交互存在，不能把同时改两项后的结果全归给其中一项；同L Recall效应仍不能替代完整性能判断。',
        'L128的因素差值为：',
        table(['数据集','对照','ΔRecall pp','95%区间','Δgraph NDC'],[
            [r['dataset'],r['contrast'],num(r['delta_recall_pp'],3,True),'['+num(r['ci_low_pp'],3,True)+', '+num(r['ci_high_pp'],3,True)+']',num(r['delta_graph_ndc'],2,True)]
            for r in t['factor_contrasts'] if r['stage']=='validation' and r['L']==128]),
        '## 6. 新教师保留了多少空间、付出什么代价',
        table(['数据集','有额外hits空间的query','两教师改变的query','原GT10 fit Recall','共同教师Recall','原graph NDC','成本教师NDC','保留教师NDC'],[
            [SHORT[r['dataset']],f"{r['headroom_queries']}/20000",r['changed_teacher_queries'],num(r['original_hits']*10)+'%',num(r['teacher_hits']*10)+'%',
             num(r['graph_ndc']['baseline'],2),num(r['graph_ndc']['cost'],2),num(r['graph_ndc']['keep'],2)] for r in teacher]),
        '两教师逐query最高hits相同，但keep教师放弃了无额外命中组的成本选优，因此平均图工作高于cost教师。候选教师每query使用GT从56个真实三元组中选优，不能部署，也不是全H上界或等工作/端到端QPS收益。',
        '## 7. 损失下降是否真的修复top3',
        '![训练期间对同一固定教师的精确top3重合](figures/training_alignment.png)',
        '每个子图固定同一套教师，因此可比较四个模型；两行教师不同，绝对重合率不能跨行当作任务难度不变的排名。虚线为零残差初始模型。这里用float64全H精确评分，不代表HNSW查询结果。',
        table(['数据集','模型','本格损失 初→末','本格教师入口重合 初→末','完整集合匹配 初→末','最终W漂移'],[
            [SHORT[m['dataset']],m['cell'],num(m['first']['data_loss'])+'→'+num(m['last']['data_loss']),
             num(read(O/'models'/m['dataset']/m['cell']/'alignment_curve.json')[0]['metrics'][m['teacher']]['all']['entry_overlap']*100,2)+'%→'+num(read(O/'models'/m['dataset']/m['cell']/'alignment_curve.json')[-1]['metrics'][m['teacher']]['all']['entry_overlap']*100,2)+'%',
             num(read(O/'models'/m['dataset']/m['cell']/'alignment_curve.json')[0]['metrics'][m['teacher']]['all']['set_match']*100,2)+'%→'+num(read(O/'models'/m['dataset']/m['cell']/'alignment_curve.json')[-1]['metrics'][m['teacher']]['all']['set_match']*100,2)+'%',
             num(m['last']['drift'],6)] for m in train]),
        'margin通过在非教师分数上加μ寻找最难竞争集合，显式上界μ×教师漏选数。其零损失条件和梯度已由独立全枚举/有限差分检验；8份模型的NumPy导出、最终损失和重合统计全部复核。数学保证针对教师成员错误，不保证NSG命中，更不保证80轮有限优化后的每个query都改善。',
        'CE与margin的loss单位和有效梯度不同，不能从较小损失值给不同目标排序。固定λ也没有固定最终漂移；保守改动与目标方向变化仍须区别。以下几何比较只用于说明两种变换关系，不给未执行的漂移匹配控制填写QPS：',
        '另外，keep教师保留的是原HNSW实际集合，精确评分训练并不自动复现近似路由决策。零残差时，精确top3与原HNSW实际三入口完全一致的比例为'+ '、'.join(SHORT[ds]+' '+num(read(O/'models'/ds/'cost_ce/alignment_curve.json')[0]['metrics']['baseline']['all']['set_match']*100,2)+'%' for ds in DS)+'。该差异不改变原线上规则，但要求将精确对齐与部署入口分别核对。',
        table(['数据集','教师','margin/CE漂移向量范数比','漂移方向cosine','最佳缩放后未解释能量比例'],[
            [SHORT[r['dataset']],r['teacher'],num(r['margin_to_ce_norm_ratio']),num(r['ce_margin_direction_cosine']),num(r['unexplained_margin_displacement_fraction']*100,2)+'%'] for r in gradient['geometry']]),
        '## 8. 从训练对齐到真实检索与开发段',
        '![同一split内相对GT10的真实Recall差](figures/fit_to_validation.png)',
        '每列均相对该split原GT10，同L128；不同split的query难度不同，不能把列间绝对Recall差都当成过拟合。完整fit20k使训练侧真实效用有全量证据，不再只依赖少量probe或C8内预测子集。',
        table(['数据集','模型','fit Recall','cal Recall','audit Recall','validation Recall'],[
            [SHORT[ds],cell]+[num(next(r for r in t['all_points'] if r['dataset']==SHORT[ds] and r['method']==cell and r['stage']==stage and r['L']==128 and not r['exact'])['recall_pct'])+'%' for stage in ['fit','cal','audit','validation']]
            for ds in DS for cell in ['gt10_hard']+CELLS]),
        '完整fit的有/无额外hits空间分组如下。分组由原C8标签预先定义，结果来自本轮每条query的真实搜索，包括C8外预测；这些分组不是在线可用条件。',
        table(['数据集','模型','组','ΔRecall pp','Δ平均graph NDC','获益/受损query','教师正命中空间保留'],[
            [r['dataset'],r['method'],r['group'],num(r['delta_recall_pp'],3,True),num(r['delta_graph_ndc_pct'],2,True)+'%',
             str(r['improved_queries'])+'/'+str(r['harmed_queries']),num(r['C8_teacher_gain_retention_pct'],2)+'%' if r['C8_teacher_gain_retention_pct'] is not None else '不适用']
            for r in t['fit_groups'] if r['method'] in CELLS and r['group']!='all']),
        '保留比例的分子为每query实际正命中增量与C8教师增量的较小者之和，分母为对应教师正增量；它只描述训练侧已知空间的迁移。C8外实际改善可以存在，不能把C8称为全局oracle。总均值之比与逐query相对变化均值另存CSV，不混用。',
        '本轮margin对照呈现清楚的训练侧取舍：WebVid有空间组的净增命中由cost教师的512降到keep教师的378，同时无空间组的损失由242降到130，整体净增由270降到248。Yandex对应为104→32、损失118→33，整体−14→−1。保留规则确实减少损伤，也减少了获益；正式曲线并未整体改善，因此“去掉同命中成本改道目标会更好”的猜想未获这轮支持。',
        'audit L128的精确入口与实际HNSW结果：',
        table(['数据集','方法','HNSW Recall','exact Recall','exact−HNSW pp'],[
            [SHORT[ds],cell,num(next(r for r in t['all_points'] if r['dataset']==SHORT[ds] and r['stage']=='audit' and r['method']==cell and r['L']==128 and not r['exact'])['recall_pct']),
             num(next(r for r in t['all_points'] if r['dataset']==SHORT[ds] and r['stage']=='audit' and r['method']==cell and r['L']==128 and r['exact'])['recall_pct']),
             num(next(r for r in t['all_points'] if r['dataset']==SHORT[ds] and r['stage']=='audit' and r['method']==cell and r['L']==128 and r['exact'])['recall_pct']-next(r for r in t['all_points'] if r['dataset']==SHORT[ds] and r['stage']=='audit' and r['method']==cell and r['L']==128 and not r['exact'])['recall_pct'],3,True)]
            for ds in DS for cell in ['gt10_hard']+CELLS]),
        'exact按画像分数精确选入口，仍不是按有限L搜索效用选择的oracle。它不带正式QPS；若精确画像排名没有提高最终Recall，也不能把差异全归于微型HNSW近似。',
        '## 9. 梯度分组：解释监督，不替代性能归因',
        '冻结模型后另对fit做一次只读梯度分解，未进行optimizer step或新搜索。headroom/no_headroom的梯度都按总query数归一化，因此是原目标的实际组贡献；每组单独均值也保留。cosine<0表示两组对当前参数的局部推动方向有冲突；它不证明某组造成了验证性能变化。',
        table(['数据集','模型','检查点','有空间梯度范数','无空间梯度范数','两组cosine','有空间对总梯度投影比例'],[
            [SHORT[r['dataset']],r['cell'],r['checkpoint'],num(r['groups']['headroom']['parameter_gradient_norm'],4),num(r['groups']['no_headroom']['parameter_gradient_norm'],4),
             num(r['gradient_cosine'],3),num(r['headroom_projection_fraction'],3)] for r in gradient['records'] if r['checkpoint']=='initial']),
        '梯度投影比例因相消可超出[0,1]，不是概率；表中不含锚定正则。初始及最终全部数据见[gradient_diagnostics.json](results/gradient_diagnostics.json)。本轮没有漂移匹配的新搜索控制，不能据梯度方向单独认定因果机制。',
        '初始cost教师下，两组参数梯度cosine在CE约0.93、margin约0.70/0.78，都为正；没有证据把无额外命中组整体称为与有空间组对抗的梯度噪声。keep＋margin明显降低了无空间组的梯度份额，但这并未带来稳定前沿改善。另一个确定的几何事实是margin位移不是CE位移的简单缩放：cost教师下两者cosine为−0.17/−0.26，最佳标量缩放仍不能解释约97%/93%的margin位移能量。该事实与“未做漂移匹配性能控制”的限制同时成立。',
        '## 10. 成本、计时与独立核验',
        table(['项目','本轮实际'],[
            ['兼容逻辑三入口标签复核','2,240,000；新增标注调用0'],
            ['训练',f"8次，合计{sum(m['training_seconds'] for m in train):.2f}s，CPU8，含训练对齐诊断"],
            ['原NSG真实调用',f"{ver['physical_calls']:,}；正常上限2,085,120；修复0；合成0"],
            ['开发/正式输出',f"{ver['total_points']}点，{ver['total_query_outputs']:,}个query输出独立评分"],
            ['正式输出','110点，各3次warm/plain；220,000个不同方法/query输出'],
            ['历史原模型输出回归',f"{ver['historical_regression_outputs']:,}个query输出，含E28 linear/MLP"],
            ['fit缓存与本轮原生输出一致',f"{ver['fit_native_cache_parity_outputs']:,}个同入口已知三元组"],
            ['查询进程总wall',f"{sum(j['seconds'] for j in jobs):.2f}s，含加载/构建/核验，不能充作QPS"],
            ['精确GT/QGT/主图从零成本','未新测；已有依赖不隐去'],
            ['保护/标签准备总wall','未单独完整仪表化，不补造秒数']]),
        '机器为Intel Xeon 6982P-C，CPU-only；正式CPU15/实际进程和OpenMP线程1、OMP/OpenBLAS/MKL1。binary与E28逐位相同，原源码/kernel/build/图/base/H只读。计时包含raw query、入口路由、排序、原NSG和预分配输出写入；GT/count/hash/I/O/加载建图均在计时外。route/graph组件在L128另测，不能相加当作独立端到端wall。',
        '所有三轮warm/plain、全批count与前16条原wrapper的ID/距离bits/入口一致；五L同模型入口及微型图一致。原标签全部ID→GT重新评分，T0/T1规则核验、模型NumPy导出/损失、实际新输出和历史回归分别通过。保护与冻结最终状态见[final_audit.json](reviews/final_audit.json)。',
        '## 11. 结论的适用范围与下一步',
        verdict+' '+recommendation,
        '原教师＋margin有局部正点：Yandex L64的Recall较GT10 hard高0.060pp、同L中位QPS高约1.50%；WebVid L256高0.055pp但QPS约持平。这些点不构成整条曲线胜出；本轮原教师＋margin在预设三召回点的插值速度平均为WebVid+0.16%、Yandex−0.83%，且Yandex轮次波动限制了精细排序。保留教师＋margin在WebVid五L的Recall均低于原GT10。',
        '结论限定于本轮两套历史query、一个H/主图、共享linear、固定λ100/μ.1/80轮。它不证明所有教师设计或margin都无效，也不把小幅局部正值抹去。优化并非收敛证书：梯度和完整训练轨迹已保留，同epoch不等于两种损失达到相同最优程度。',
        '下一步应由本轮完整图和分组证据决定，不自动新增实验。若教师对齐提高而真实fit收益有限，优先研究“多个近似等效好集合如何作为监督”，而不是继续追唯一教师的入口身份；若fit有收益但开发不稳，应先验证可迁移信号和保护原决策的约束。漂移匹配控制可分清更保守的变换与损失方向作用；这些均未在本轮执行。',
        'E24/原GT10以及E28 MLP的历史局部信号继续保留。一次新增强未产生稳定整体优势不能倒推出原方法没有价值。',
        '## 12. 复现与证据入口',
        '- [冻结协议](protocol.md)、[方法推导与一手来源](research.md)、[源码](src/common.py)、[状态](state.json)。\n- [教师复核](reviews/teacher_verification.json)、[损失全枚举测试](reviews/objective_tests.json)、[模型独立复核](reviews/model_verification.json)。\n- [原始点表](results/all_points.csv)、[因素差值](results/factor_contrasts.csv)、[fit分组](results/fit_groups.csv)、[全部训练轨迹](results/training_curves.csv)。\n- [调用账](logs/evaluation_jobs.json)、[模型冻结](models/frozen_before_validation.json)、[输出复核](reviews/output_verification.json)、[图表工作簿](chart_data.xlsx)。',
        '重跑必须创建新的独立输出版本；原脚本拒绝覆盖。既有cal/audit/validation结果不得用来改本轮冻结配置。完整启动链是prepare→prepare_additional→test_objective→train→verify_models→run_evaluation→gradient_diagnostics→analyze→plot→write_report→update_docs→图表人工检查→final_audit；原图和数据路径由已冻结配置绑定，不复制大数据或访问held-out。补充资产检查在本轮首次查询前以相同内联代码执行，后来整理为prepare_additional.py，原冻结prepare.py字节保留。']
    dump(O/'results/conclusion.json',dict(status=conclusion,verdict=verdict,recommendation=recommendation,successful_methods=successful))
    (O/'report.md').write_text('\n\n'.join(report)+'\n')
    print(conclusion,flush=True)

if __name__=='__main__':main()
