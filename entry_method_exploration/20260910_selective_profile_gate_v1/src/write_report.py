"""Build the evidence report; does not choose a model or run experiments."""
from common import RUN, DATASETS, read, dump
from analyze import LABELS, METHOD_LABELS

STATUS='SELECTIVITY_NOT_GENERALIZED_NO_FORMAL_GO'


def pct(v):return 'NA' if v is None else f'{100*v:.2f}%'


def main():
    report=read(RUN/'results/analysis.json');costs=read(RUN/'results/costs.json')
    selection=read(RUN/'models/selections.json')
    lines=['# E25：能否留下有效改道、减少受损查询？','',
        f'2026-09-10夜间，状态`{STATUS}`。双数据集、两种搜索前选择规则、全部预定配对标签和60个单线程正式测量点已完成。所有冻结规则原样跑完，未因负结果改阈值。',
        '', '## 1. 结论与问题边界','',
        '**本轮没有得到能在两个数据集稳定保留收益、避免损失并改善端到端性能的选择规则。WebVid有局部质量修复，Yandex的选择能力不稳定；额外路由成本必须单独面对。**',
        '', '这里的“有效”和“受损”都相对同输入的matched Fast20K（A0），新画像为E24早先按cal冻结的A1。不是相对原NSG定义一次改道成功，也不是把原Fast30K的训练输入差异归给本轮门控。',
        '', 'WebVid A1固定GT10软T=0.016201138496398926，Yandex A1固定GT10硬。每条query只在完整A0/A1三入口集合中二选一，再运行一次原NSG；没有在线图probe、搜索重启、top32候选枚举或结果合并。两个版本分别是：',
        '', '- **BaseGate**：先计算旧路由的7个标量特征；选A1时才额外调用新路由。',
        '- **DualGate**：两路都运行，再用13个标量特征选择；需要第二套入口间隔与两套入口重合度。',
        '', '两个版本的模型均不读取L，五档L选择完全一样。主规则是预先在cal选定的报告对象；Yandex的主规则在cal已失败，按协议继续测量是为了反证，不表示建议部署。',
        '', '## 2. 预设目标在新分段是否保持','',
        'R/A按query×L事件计数，Rh/Ah按正命中增量与负命中损失计量。目标为R、Rh≥75%，A、Ah≥25%，且选择后的净命中不低于0和always-A1两者中的较大值。下表L64/128等权合并；完整分母包含中性query。',
        '', '| 数据集 / cal主规则 | 分段 | R有效事件保留 | A受损事件避免 | Rh正命中保留 | Ah负损失避免 | 净命中 vs A0 | always-A1净命中 | 目标 |',
        '|---|---|---:|---:|---:|---:|---:|---:|---|']
    for ds in DATASETS:
        r=report['datasets'][ds];primary=r['primary_frozen_on_cal']
        for stage in ['cal','audit','validation']:
            m=r['splits'][stage]['gates'][primary]['pooled_L64_L128']
            lines.append(f"| {LABELS[ds]} / {METHOD_LABELS[primary]} | {stage} | {pct(m['R'])} | {pct(m['A'])} | {pct(m['Rh'])} | {pct(m['Ah'])} | {m['net_delta_hits']:+d} | {m['always_A1_net_delta_hits']:+d} | {'PASS' if m['target_met'] else 'NOT_MET'} |")
    lines += ['', 'WebVid的DualGate在cal达标，但audit避免的受损事件只有21.95%，不足25%；增加的净命中仅比always-A1多14。Yandex两规则在cal都未达标，主BaseGate在audit保留38.71%的有效事件，同时丢失127个本可得到的正命中、只避免97个负命中，比always-A1还少30个命中。',
              '', 'WebVid DualGate在validation的A=24.77%、Ah=24.62%，距离25%门槛只差约1个受损事件、2个命中损失单位。不能把这样的小差额解释成机制完全无效；真正限制结论的是audit不稳定、收益幅度很小以及端到端变慢。Yandex主规则则明显牺牲了大多数有效改道。',
              '', '这不能用“受损query减少了”单独判成功：回退本身就会减少损失，也会放弃改道的收益。四个比例和净命中要求必须一起看。所有非主规则及失败候选仍在[全部表格](results/tables.md)与[冻结候选](models/selections.json)中。',
              '', '![收益保留与受损避免](figures/retention_harm.svg)',
              '', '## 3. 历史validation五档L的实际质量与速度','',
              '同机、CPU15、实际1线程，每个点独立整批预热及plain wall三次。下表给cal主规则；QPS差比较本轮同时重测的对照中位数。三次原值、范围、全部六方法60点见[数值表](results/tables.md)。',
              '', '| 数据集 / 主规则 | L | ΔRecall vs A0 pp | ΔRecall vs A1 pp | ΔQPS vs A0 % | ΔQPS vs A1 % | A1比较三轮QPS差 % |',
              '|---|---:|---:|---:|---:|---:|---|']
    for ds in DATASETS:
        primary=report['datasets'][ds]['primary_frozen_on_cal']
        for L in [64,128,256,400,800]:
            a=next(c for c in report['comparisons'] if c['dataset']==ds and c['method']==primary and c['reference']=='fast20k' and c['L']==L)
            b=next(c for c in report['comparisons'] if c['dataset']==ds and c['method']==primary and c['reference']=='e24' and c['L']==L)
            q='/'.join(f'{v:+.2f}' for v in b['qps_percent_change_by_repeat'])
            lines.append(f"| {LABELS[ds]} / {METHOD_LABELS[primary]} | {L} | {a['delta_recall_pp']:+.3f} | {b['delta_recall_pp']:+.3f} | {a['qps_percent_change_medians']:+.2f} | {b['qps_percent_change_medians']:+.2f} | {q} |")
    lines += ['', '| 数据集 | 规则 | 相对A1 Recall提高点 / 5 | QPS中位数提高点 / 5 | 同L两者都提高 / 5 | Recall提高且三轮QPS都提高 / 5 |',
              '|---|---|---:|---:|---:|---:|']
    for ds in DATASETS:
        for kind in ['base_gate','dual_gate']:
            c=[v for v in report['comparisons'] if v['dataset']==ds and v['method']==kind and v['reference']=='e24']
            lines.append(f"| {LABELS[ds]} | {METHOD_LABELS[kind]} | {sum(v['delta_recall_pp']>0 for v in c)} | {sum(v['qps_percent_change_medians']>0 for v in c)} | {sum(v['same_L_recall_and_median_qps_strictly_better'] for v in c)} | {sum(v['same_L_recall_better_qps_better_all_three_repeats'] for v in c)} |")
    lines += ['', '两个门控×两个数据集×五L，相对A1的20项Recall差，其描述性95%配对query区间全部跨0；没有任何一点同时满足Recall提高且三轮对应QPS均提高。此处不把未通过正式门槛等同于“真实效果必定为零”。',
              '', '![Recall–QPS](figures/recall_qps.svg)', '', '![相对E24的差值](figures/deltas_vs_e24.svg)',
              '', '曲线上的线仅连接实测L点，未把粗网格插值当成等Recall加速结论。某个门控点在全部30点中未被支配，可能只是多一点Recall、付出更多时间的交换；“观测非支配”“同L双升”“稳定方法更优”分别报告。每轮非支配点名单保留在[analysis.json](results/analysis.json)。',
              '', '## 4. 是否真的学会了分辨收益与损失','',
              '训练不是普通多数类分类。每query的权重为P=sum_L max(d,0)、N=sum_L max(-d,0)，零差权重为0；同一query跨L正负冲突同时进入两项损失。特征只来自路由分数、间隔、fit画像支持/角位移与入口重合度。GT、实际命中和主图NDC只用于离线监督/评价，不能作为部署特征。',
              '', '| 数据集 | fit提供信号的query / 8192 | 总权重ESS | 跨L正负冲突query | 同L免费oracle额外命中 | 固定同一选择的免费oracle额外命中 |',
              '|---|---:|---:|---:|---:|---:|']
    for ds in DATASETS:
        r=report['datasets'][ds]['splits']['fit'];s=read(RUN/'results/mechanism'/ds/'signal_concentration.json');cross=r['cross_L']
        lines.append(f"| {LABELS[ds]} | {s['fit_total_weights']['nonzero_queries']} | {s['fit_total_weights']['weight_ESS']:.1f} | {cross['opposite_signs_across_L']} | {cross['same_L_oracle_delta_hits_non_deployable']} | {cross['L_invariant_oracle_delta_hits_non_deployable']} |")
    lines += ['', 'ESS是本轮正负命中监督权重的集中度，不是新增独立样本数。全部fit query中权重最高的1%（82条）贡献WebVid27.47%、Yandex57.79%的总正负监督权重；尤其Yandex的损失/收益信号受少量query影响很大。分段的符号波动不能仅归因于特征分布变化，也可能包含稀疏效果的抽样波动；本轮没有将二者分离为已证实的因果结论。',
              '', '两个oracle都用了真实答案，只用于判断限制来自哪里，没有在线QPS、不是可部署方法。允许按L各自看答案，相比固定一条query的两L选择，fit的oracle空间仅多WebVid98/Yandex30个命中；因此目前不能把主要失败归因于“模型不能看L”。',
              '', '六个正则化线性模型/数据集均按固定凸目标求解收敛，梯度无穷范数≤1e-8；阈值只有0和fit logit的四个固定分位数。未因audit表现差增加模型容量、阈值或训练轮数。',
              '', '![区分能力迁移](figures/signal_transfer.svg)',
              '', '| 数据集 | 规则 | fit weighted AUC | cal | audit | validation | validation比随机保留同等数量多出的净命中 |',
              '|---|---|---:|---:|---:|---:|---:|']
    for ds in DATASETS:
        for kind in ['base_gate','dual_gate']:
            signals=[report['datasets'][ds]['splits'][stage]['gates'][kind]['signal'] for stage in ['fit','cal','audit','validation']]
            auc=' | '.join(f"{s['weighted_AUC']:.4f}" for s in signals)
            lines.append(f"| {LABELS[ds]} | {METHOD_LABELS[kind]} | {auc} | {signals[-1]['excess_net_hits_over_random_expectation']:+.2f} |")
    lines += ['', 'weighted AUC将正/负命中幅度计入排序质量，0.5对应无区分的参考水平；这里未将小幅偏离0.5当成已证实的泛化能力。随机参考是给同一批query随机保留完全相同数量时净命中的精确期望，不是额外训练的规则；它用于分开“少改道”与“选得更有针对性”。',
              '', '所有特征分层边界只由fit四分位数确定。cal/audit/validation沿相同边界报告，未据分层结果重新选特征或写规则。系数大小只描述相关性；尤其各间隔、ESS和画像位移存在相关，不能把某个系数直接解释成因果修复机制。逐特征原表和事后最大收益/损失案例见[WebVid机制目录](results/mechanism/webvid2_5m_light_v1/)与[Yandex机制目录](results/mechanism/yandex_t2i_official10M_ip_v1/)。',
              '', '## 5. 保留的改道还包括多少没有实际作用的切换','',
              '| 数据集 | 规则 | A0/A1入口相同query | 选择A1但入口仍相同 | 实际改变A0入口query | 回退掉的A1入口变更 |',
              '|---|---|---:|---:|---:|---:|']
    for ds in DATASETS:
        for kind in ['base_gate','dual_gate']:
            m=report['datasets'][ds]['validation_gates'][kind]['entry_mechanism']
            lines.append(f"| {LABELS[ds]} | {METHOD_LABELS[kind]} | {m['A0_A1_identical_entry_sets']} | {m['gate_selected_A1_but_same_entry_sets']} | {m['gate_actual_entry_changes_vs_A0']} | {m['A1_changes_reverted_by_gate']} |")
    lines += ['', '即使入口集合改变，有限L的最终top10命中也经常不变。不能把路由切换率当成有效改道率，也不能删掉这些中性query让Recall分母变小。相同三入口集合的两次配对搜索照常执行，未借缓存少算来扩大实验预算。',
              '', '## 6. 时间与完整成本','',
              '| 数据集 | 方法 | L128路由单测 μs/query | 图单测 μs/query | 独立端到端中位数 μs/query | route NDC | graph NDC |',
              '|---|---|---:|---:|---:|---:|---:|']
    for ds in DATASETS:
        for kind in ['nsg','fast30k','fast20k','e24','base_gate','dual_gate']:
            p=costs['datasets'][ds]['L128'][kind]
            lines.append(f"| {LABELS[ds]} | {METHOD_LABELS[kind]} | {p['route_only_us_per_query']:.3f} | {p['graph_only_us_per_query']:.3f} | {p['end_to_end_median_us_per_query']:.3f} | {p['mean_route_ndc']:.2f} | {p['mean_graph_ndc']:.2f} |")
    lines += ['', '分项各自预热/计时，不相加代替端到端wall。BaseGate每query多付3次画像重评分，选新时再付一次新路由；DualGate固定多付两套原路由和6次重评分。query范数、表查询、标准化、标量预测与结果写入全部处于端到端timer内。',
              '', f"真实NSG调用总计 **{costs['real_graph_calls']:,}**，修复预留使用0；另合成fixture5144次，均未超预算。输入核对/准备{costs['input_prepare_seconds']:.2f}s，全部真实搜索子进程{costs['search_process_wall_seconds']:.2f}s，观测最高RSS {costs['max_observed_search_RSS_bytes']/2**30:.3f}GiB。后者包含加载、建图、预热、计数、核验和I/O，不能换算查询QPS。",
              '', '| 阶段 | 实际NSG调用 | 子进程wall s |', '|---|---:|---:|']
    for phase,p in costs['phases'].items():lines.append(f"| {phase} | {p['calls']:,} | {p['process_seconds']:.2f} |")
    lines += ['', '两规则都需要两套微型图作为部署资产；BaseGate的按需仅指查询时是否调用A1。各模型/图文件大小、每L重建的测量准备成本和12次凸拟合耗时在[costs.json](results/costs.json)。底层exact GT、QGT、原NSG及E24画像的从零成本本轮未新测，保留null和原因。',
              '', '## 7. 可信度、实现验收与不能推出的结论','',
              '- 原base/raw-IP/NSG/QGT seed20260828/H815、821、三个互异真实入口保持不变；matched排序和Micro-HNSW配置冻结，原Fast30K保留历史输入/seed/heap顺序。',
              '- fit为后20K中固定抽取8192；cal为router_train[2048,4096)，audit为[4096,6144)，各2048。它们与画像fit不同段，但全项目有历史开发使用；E24画像见过门控fit query。',
              '- 两数据集全部60候选和四份模型的权重/阈值、输入特征、代码及binary在audit前冻结。audit只报告；其后才复制历史validation前2000条，held-out没有打开。',
              '- 合成的强制旧/新、零query、相同入口、非法线程拒绝均通过。真实恢复40点、fit/cal/audit24点、validation60点；共124点219584个输出独立GT10重评分。每点plain/count全部query匹配，前16条对照原kernel；正式三轮结果逐位一致。',
              '- validation的NSG/Fast30K/Fast20K/E24共40点80000个输出、距离bits、入口与route/graph NDC均与E24冻结结果逐位相同。门控逐query等于所选原策略的结果与graph NDC；新增route成本逐条复核。',
              '- 五L的选择、logit、三入口和同角色微型图一致。完整资产hash及cal选择独立重算见[完整性检查](reviews/immutable_integrity.json)。',
              '- 2000次bootstrap以query为配对单位，并将同一query的两L保留在一起；区间只作未校正的描述性不确定性。三次wall不增加Recall样本数，也不是三个独立构建。',
              '', '模型失败不能外推成“入口效用不可学习”。本轮只检验两个固定策略、这组低成本标量特征、线性模型和有限样本；也不能将优化收敛、cal目标通过、非支配点或oracle空间提升成正式性能GO。',
              '', '## 8. 后续有针对性的判断','',
              '两个问题应分别处理：一是怎样预测改道的正负作用，二是为这种判断多花的时间是否划算。本轮WebVid的局部修复尚不足以抵消双路成本，Yandex连开发区分能力都未稳定。继续盲目增加门控容量或阈值不受现有证据支持。',
              '', '若夜间继续一个独立小探索，较直接的问题是：能否在离线构建时减小E24画像相对A0的偏移，让线上仍只有一套画像、一轮路由？这是固定旧新画像之间的收缩对照，不是已证实的方法，也不能假设搜索收益会随收缩系数线性变化。它会产生新的三入口集合，必须重新统计新增受损，不能套用本轮纯二选一的“所有损失都来自A1”关系。任何实际探索另立协议、split与预算，E25参数表和结果保持封存。',
              '', '历史区别已核对：[E09 utility residual](../../experiment_history/04_utility_and_representation.md)由top32真实single Recall/NDC优势聚合signed query残差；本轮只学习A0/A1三入口配对差。旧probe/restart见[历史05](../../experiment_history/05_probe_reroute.md)，不恢复旧runner。两固定专家的成本敏感选择属于通用已有框架，可参考[Learning to Defer](https://proceedings.mlr.press/v119/mozannar20b.html)；本轮加权logistic定义及全部执行以[协议](protocol.md)为准，不宣称复现该论文或机制本身新颖。',
              '', '## 9. 原始证据与复现入口','',
              '- [锁定协议](protocol.md)、[配置](config.locked.json)、[夜间授权](overnight_authorization.md)、[执行命令](commands.md)、[当前状态](state.json)。',
              '- [输入准备](inputs/preflight.json)、[原资产manifest](reviews/protected_before.json)、[合成验收](reviews/synthetic_gate.json)、[真实恢复](reviews/recovery_gate.json)。',
              '- [固定选择](models/selections.json)、[audit前冻结](models/frozen_before_audit.json)、[优化器数学检查](reviews/learner_selftest.json)、[audit重建](reviews/audit_report.json)、[validation独立核验](reviews/validation_verification.json)。',
              '- [全部原值](results/tables.md)、[配对CSV](results/comparisons.csv)、[分析JSON](results/analysis.json)、[完整成本](results/costs.json)、[调用账](reviews/search_jobs.json)、[最终验收](reviews/final_audit.json)。',
              '']
    (RUN/'report.md').write_text('\n'.join(lines))
    dump(RUN/'results/summary.json',{'status':STATUS,'completed_validation':True,'formal_performance_GO':False,
         'primary_frozen_on_cal':{ds:report['datasets'][ds]['primary_frozen_on_cal'] for ds in DATASETS},
         'primary_target_by_split':{ds:{stage:report['datasets'][ds]['splits'][stage]['gates'][report['datasets'][ds]['primary_frozen_on_cal']]['pooled_L64_L128'] for stage in ['fit','cal','audit','validation']} for ds in DATASETS},
         'real_calls':1089152,'synthetic_calls':5144,'repair_calls':0,
         'all_negative_points_and_failed_candidates_retained':True,'primary_comparisons':[c for c in report['comparisons'] if c['method']==report['datasets'][c['dataset']]['primary_frozen_on_cal']]})
    print('FULL_REPORT_WRITTEN',flush=True)


if __name__=='__main__':main()
