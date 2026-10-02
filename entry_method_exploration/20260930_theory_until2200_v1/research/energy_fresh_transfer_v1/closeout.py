import os
os.sched_setaffinity(0,{14})
import hashlib,json,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parent;CAMP=R.parents[1];ROOT=R.parents[3]

def write_new(path,text):
    with Path(path).open('x') as f:f.write(text)

def ident(path):
    p=Path(path);h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(16<<20),b''):h.update(b)
    return {'bytes':p.stat().st_size,'sha256':h.hexdigest()}

def main():
    s=json.loads((R/'results/summary.json').read_text());audit=json.loads((R/'reviews/independent_audit.json').read_text())
    gap=json.loads((R/'reviews/small_gap_float64_audit.json').read_text());run=json.loads((R/'reviews/run_complete.json').read_text())
    assert audit['status']==gap['status']=='PASS' and run['status']=='COMPUTED_PENDING_INDEPENDENT_AUDIT'
    assert json.loads((R/'reviews/active_process.json').read_text())['pid'] is None
    assert gap['additional_full_base_float64_checks']==0
    methods=['GT10-soft-t1','Uniform','ShuffledEnergyTree','EnergyTree']
    status='COMPLETED_NO_STABLE_ENERGY_RECALL_GAIN_RETAIN_COST_CANDIDATE'
    decision={'status':status,'default_changed':False,'energy_selection_parameter_exploration':'STOP_THIS_FIXED_VERSION',
        'cost_candidate':'RETAIN_MEASURED_COST_QUALITY_TRADEOFF','next':'read-only score/router/search decomposition; then fixed shared exact-label dispatch check',
        'not_claimed':['noninferiority','familywise statistical significance','seed-general selection improvement','automatic default replacement']}
    def label(ds):return 'WebVid' if ds.startswith('web') else 'Yandex'
    def ci(x):return '['+', '.join(f'{v:+.6f}' for v in x)+']'
    lines=['# 固定Energy选样的两批新源检索验证','',
        '2026-09-30，全部原生、GT、返回、费用与区间核验通过。**能量选择未获得稳定的新源召回改善；停止本版选择器调参，保留已测构建成本候选，默认保持。** 训练方向误差下降6.811%／23.330%没有等比例转成检索收益，不能据此回改记录155的训练门或将其当Recall门。','',
        '每集两批各4096条，四模型／全部图／来源／K与L在第一次源向量读取之前冻结。Default为原GT10-soft-t1／GT10-hard；Uniform是同2048精确fit预算的固定均匀选行；Shuffled与Energy使用共同1024 pilot、再选1024的原r0模型。没有挑16组最好seed或利用151曝光查询补标。','',
        '## 合并绝对指标','',
        '| 数据集 | K / L | 方法 | Recall (%) | 完整QPS | 命中成员 |',
        '|---|---|---|---:|---:|---:|']
    for ds,group in s['pooled_equal_batches'].items():
        for p in group['points']:
            for m in p['methods']:
                lines.append(f'| {label(ds)} | {p["K"]} / {p["L"]} | {m["method"]} | {100*m["recall"]:.6f} | {m["QPS"]:.3f} | {m["hits"]} |')
    lines += ['', '合并QPS为8192除以两批完整query-loop wall之和的三轮均值，不取两批QPS的算术平均。query loop含路由、原主搜索和返回数组写入；加载与落盘单列。CPU15实际1线程、各库池1，方法串行；性能期间无训练／GT／编译或其他性能作业，CPU14有轻量源码、论文和文档工作。','',
        '## Energy的三种比较','',
        '| 数据集 / K | 对照 | ΔRecall (pp) | 分层描述95%区间 | 两批ΔRecall (pp) | 真救回 / 真损伤 | ΔQPS (%) |',
        '|---|---|---:|---|---|---:|---:|']
    for ds,group in s['pooled_equal_batches'].items():
        for p in group['points']:
            for x in p['comparisons']:
                if x['method']!='EnergyTree':continue
                batch=' / '.join(f'{v:+.6f}' for v in x['batch_delta_recall_pp'])
                lines.append(f'| {label(ds)} / {p["K"]} | {x["reference"]} | {x["delta_recall_pp"]:+.6f} | {ci(x["stratified_descriptive_95_interval_pp"])} | {batch} | {x["rescue_members"]} / {x["damage_members"]} | {x["QPS_change_pct"]:+.3f} |')
    lines += ['',
        'Energy相对Uniform的Web R1仅净多1次命中，两个批次+3／−2；Y R1净少5次，两批−2／−3。R100分别净−11／+31成员，两集均跨批异号；这四个描述区间都跨0。相对Shuffled，Web均值略正但两批反向，Y R1两批均负；一次打乱模型不是随机化检验分布。不能将这些结果写成跨种子的选择信息优势。',
        '',
        '相对当前Default，Web R1净少9次、R100净少214成员，两批方向均负，两个未作多重校正的描述区间也均在0以下；这是需要保留的质量损失。Y R1净少4次、R100净少26成员，区间跨0。Energy相对Default的QPS均值变化约+0.172%／+0.182%（Web）和+0.140%／−0.205%（Y），幅度小且未形成整体线上优势。相对Uniform的QPS均值四点均略高，全部原始轮次保留，不能把固定点的描述均值替代完整曲线或统计速度保证。','',
        '所有6方法对均在原始JSON中保留，单批及两批分层配对bootstrap为20000次。区间只条件于这组固定模型和固定来源，未作家族校正，也不涵盖训练种子不确定性。没有用户给出的可接受质量损失，不自动宣称非劣或切默认。','',
        '## 每批绝对指标和全部计时轮','',
        '| 数据集 / 批 | K / L | 方法 | Recall (%) | 完整QPS | 三轮完整wall (s) |',
        '|---|---|---|---:|---:|---|']
    for case,group in s['cases'].items():
        for p in group['points']:
            for m in p['methods']:
                seconds=' / '.join(f'{v:.9f}' for v in m['seconds'])
                lines.append(f'| {label(group["dataset"])} / {group["batch"]} | {p["K"]} / {p["L"]} | {m["method"]} | {100*m["recall"]:.6f} | {m["QPS"]:.3f} | {seconds} |')
    lines += ['', '所有96个plain计时轮均保留，没有去掉慢轮。各点还有独立warm与count返回逐位恢复，以及16条原E99返回／NDC检查。固定底图、E99等价核、入口3个真实ID排序、ef10、主L／停止不变。','',
        '## 构建成本、来源和核验','',
        '沿记录154／156，原默认完整wall为Web336.051／Y1519.754秒，Energy为131.133／259.137秒，单次少60.98%／82.95%；已计入全20K近似教师、选样、两次载入与追加GT。未清缓存、非随机重复，不称统计显著或冷缓存加速。Uniform的Web控制来自共享构建，Shuffled也是共享增量，不能拼出未实测的独立完整成本。共享Faiss批处理因素已列为另一项待测工程检查；尚未修改这些已测费用。',
        '',
        '新源窗口：Web[2370000,2390000)、[2390000,2410000)，Y[2060000,2080000)、[2080000,2100000)。按源行顺序取4096个合法、非零、字节互异query，排除所有登记split、fit、旧E105／Web9月22日及151整候选窗口，并在新批之间排除整个候选窗口。Web跳过105／84个重复，Y为0；固定邻接源窗口不代表全源随机或语义独立。上述源现在已曝光，不能再用来挑选后继模型。',
        '',
        f'控制器总wall {run["seconds"]:.3f}秒；GT阶段{run["jobs"]["exact_gt"]["seconds"]:.3f}秒，四原生作业按执行顺序'+ ' / '.join(f'{run["jobs"][case]["seconds"]:.3f}' for case in s['cases'])+'秒。新精确GT16384，32条预定float64全库检查；全部改变R1且GT间隔≤2e−5的追加名单为空，因此没有追加全库GT。没有改标签、删query或改模型。',
        '',
        f'131072个返回query向量重评分、256组返回分数核验、72个bootstrap离散分布检查和{audit["identities"]}项身份通过；最大bootstrap CDF偏差{audit["maximum_bootstrap_CDF_KS_difference"]:.6f}。分析{s["seconds"]:.3f}秒，主核验{audit["seconds"]:.3f}秒，低间隔名单核验{gap["seconds"]:.3f}秒。独立指同一agent的另一套实现，不是独立人员。',
        '',
        '新增NSG655872（含512 E99检查）、ANN655360；0新训练、画像、小图。计数包含warm、三轮plain和count，不能将它们当新增独立query。','',
        '## 后继边界','',
        '本版Energy不继续扫特征、深度、种子、温度、精确预算或教师L。低标签混合的费用—质量取舍继续保留，尚非默认替换。下一项只读诊断按已冻结协议分解分数、实际入口、主搜索吸收和真实成员救回／损伤，不据曝光新query重训。随后固定四格检查共享精确标注实现因素，不把共享工程收益归Energy独占。整日理论任务继续至22:00。','',
        '证据：[协议](protocol.md) · [完整每批／配对结果](results/summary.json) · [绝对CSV](results/metrics.csv) · [主核验](reviews/independent_audit.json) · [低间隔核验](reviews/small_gap_float64_audit.json) · [原生作业与成本](reviews/run_complete.json)。','']
    report='\n'.join(lines)
    card='''# 157 固定Energy选样的两批新源检索验证

2026-09-30，`COMPLETED_NO_STABLE_ENERGY_RECALL_GAIN_RETAIN_COST_CANDIDATE`。每集2×4096新query，Default／同预算Uniform／Shuffled／Energy及参数在源读取前冻结；真实K1/K100、CPU15实际单线程、全部96轮完整wall和输出核验通过。

| Energy相对 | Web ΔR1 / ΔR100 (pp) | Y ΔR1 / ΔR100 (pp) |
|---|---:|---:|
| Uniform | +0.012207 / −0.001343 | −0.061035 / +0.003784 |
| Shuffled | +0.036621 / +0.005127 | −0.048828 / −0.004639 |
| Default | −0.109863 / −0.026123 | −0.048828 / −0.003174 |

Energy相对Uniform四个描述区间均跨0；Web R1仅净+1、Y净−5，R100两集都跨批异号。相对Default的Web两点、两批均负，合并未校正95%区间分别[−0.219727,−0.012207]／[−0.039185,−0.014526]。不能把训练方向改善写成稳定召回增益。停止本版选择器参数探索，保留低成本候选，默认不变。

合并Default R1/QPS1、R100/QPS100：Web91.198730%/412.839、90.605103%/334.329；Y91.516113%/2335.782、91.037231%/1306.000。Energy分别Web91.088867%/413.549、90.578979%/334.938；Y91.467285%/2339.041、91.034058%/1303.324。Energy对Uniform四点QPS均值略高，但全部轮次保留、固定点非完整曲线或统计速度保证。每方法／每批绝对表见完整报告。

完整构建沿154／156：Default336.051/1519.754秒，Energy131.133/259.137秒，单次少60.98%/82.95%；原默认已同享QGT按需优化。共享Faiss计算路径另列待测，不外推新费用。Uniform的Web控制和Shuffled共享增量不合成独立完整成本。

全部GT、mask、返回、E99、线程、身份和区间先核验再解释。新GT16384、32条float64全库检查；全部命中变化且小间隔名单为空，没有额外GT、删行或改标签。131072返回、256组分数、72个分布检查及37身份通过；分析3.649秒、主审计16.915秒。原生NSG655872含512 E99、ANN655360；0新模型／图。

固定来源不是全源随机／语义独立；72个描述比较未作家族校正，一个Shuffled模型不构成置乱检验，query区间不含训练种子不确定性。下一步只读分解画像→实际入口→主返回，然后检查共享精确标注工程费用；不按已曝光query补标或调参。

[完整报告](../entry_method_exploration/20260930_theory_until2200_v1/research/energy_fresh_transfer_v1/report.md) · [协议](../entry_method_exploration/20260930_theory_until2200_v1/research/energy_fresh_transfer_v1/protocol.md) · [全部结果](../entry_method_exploration/20260930_theory_until2200_v1/research/energy_fresh_transfer_v1/results/summary.json) · [主核验](../entry_method_exploration/20260930_theory_until2200_v1/research/energy_fresh_transfer_v1/reviews/independent_audit.json)。
'''
    files=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']
    before={name:(ROOT/name).read_text() for name in files}
    history_marker='2026-09-22晚间。**原默认保持；ApproxTarget10保留为低成本候选'
    assert history_marker in before['summary.md'] and '## 最新记录\n\n| 记录 | 内容与边界 |\n|---|---|\n' in before['s-experiment.md']
    new_summary='''# ACSG 当前结果摘要

2026-09-30理论研究继续至22:00。**默认保持Web GT10-soft-t1／Yandex GT10-hard、生产E99；Energy选样未获得稳定新源召回改善，停止本版调参，低标签成本候选继续保留。** [157四模型两批新源验证](experiment_history/157_energy_selection_two_source_batches.md)已全部核验，每集8192 query、真实K1/K100、CPU15实际单线程：

| 数据集／点 | 默认Recall／QPS | Energy Recall／QPS | ΔRecall (pp)及描述95%区间 |
|---|---|---|---|
'''
    for ds,g in s['pooled_equal_batches'].items():
        for p in g['points']:
            b=p['methods'][0];e=p['methods'][3];x=next(x for x in p['comparisons'] if x['method']=='EnergyTree' and x['reference']==b['method'])
            new_summary+=f'| {label(ds)} R{p["K"]}/L{p["L"]} | {100*b["recall"]:.6f}%／{b["QPS"]:.3f} | {100*e["recall"]:.6f}%／{e["QPS"]:.3f} | {x["delta_recall_pp"]:+.6f} {ci(x["stratified_descriptive_95_interval_pp"])} |\n'
    new_summary+='''
Energy相对同2048预算Uniform的ΔR1/R100为Web+0.012207/−0.001343pp、Y−0.061035/+0.003784pp，四区间均跨0；Web R1净+1／Y净−5，R100都跨批异号。Web相对Default两点两批均负，质量损失保留；Y仍有较大不确定性。相对Shuffled也未形成稳定信息优势，一个打乱模型不是随机化检验。完整QPS、全部轮次、两批与全部6方法对均保留，不自动称非劣／线上更快或切默认。

[156固定r0完整构建](experiment_history/156_energy_selection_actual_full_build.md)Energy131.133／259.137秒，对[154同享按需QGT的默认](experiment_history/154_fair_default_demand_build_cost.md)336.051／1519.754秒，单次少60.98%／82.95%；包含教师、选择、两次载入和补标，未清缓存、非随机重复。[148原均匀混合](experiment_history/148_demand_qgt_full_build_cost.md)114.023／243.072秒及[151原主混合新源质量](experiment_history/151_frozen_hybrid_two_source_batches.md)保留各自身份，不把不同Web温度候选的费用拼接。[共享精确标注费用检查](entry_method_exploration/20260930_theory_until2200_v1/research/exact_label_dispatch_v1/protocol.md)已准备、尚未执行，不能提前替换原费用。

[155训练信息门](experiment_history/155_energy_selection_without_exact_temperature.md)的方向误差均值少6.811%／23.330%仍成立，但没有保证检索收益；复杂LOO原153失败不回改。下一步只读分解四模型的分数、实际路由与主搜索吸收，不按曝光query继续补标。[145二阶矩用语澄清](entry_method_exploration/20260930_theory_until2200_v1/research/routing_bridge_clarification_v1/theory.md)和[152温度／标签交叉项](experiment_history/152_temperature_label_error_interaction.md)保留理论边界。

'''+before['summary.md'][before['summary.md'].index(history_marker):]
    target_marker='2026-09-22用户修订：'
    assert target_marker in before['s-target.md']
    new_target='''# ACSG 下一阶段目标

2026-09-30用户授权理论、论文与小实验研究至22:00。记录141–157已完成。[157四模型新源验证](experiment_history/157_energy_selection_two_source_batches.md)表明Energy相对同预算Uniform没有稳定召回改善；Web对Default两点两批均负。停止这版选择器的特征／深度／seed／温度／预算探索，保留低标签构建费用候选，默认不变；这不是将“不确定”一概认定有害。

接下来运行已预写的[只读连接诊断](entry_method_exploration/20260930_theory_until2200_v1/research/energy_routing_bridge_v1/protocol.md)：全部四模型／六方法对、两批真实返回，分解精确分数／实际入口／主搜索吸收，区分R100成员救回损伤与每query净变化；0新搜索／训练，不据其重训。随后[固定2×2精确标注检查](entry_method_exploration/20260930_theory_until2200_v1/research/exact_label_dispatch_v1/protocol.md)只用旧fit各1024条，核对batch256/1024及k100/10的共享工程费用和消费ID身份。它不是新ANN方法，不把局部吞吐外推完整构建。

现有154／156双方已同享按需QGT。新检查若值得接续，必须另冻对默认与低标签候选一致的完整构建、保留QGT去重和短尾数值合同，并核验完整H/W/图身份。不得给Energy独占共享优化，不增加参数网格或追加新源直到通过。整日新增1GiB、空余6GiB、21:30后不启重作业、22:00结束。

'''+before['s-target.md'][before['s-target.md'].index(target_marker):]
    spec_intro='''[四模型新源评价器](entry_method_exploration/20260930_theory_until2200_v1/research/energy_fresh_transfer_v1/protocol.md)已完成并核验：沿151原E99等价核，只扩为固定四模型约束并在实际GT／原生调用前检查预算；四批全部源／模型先锁定，真实K1/K100、CPU15实际1线程、warm/plain/count及16 E99一致性。完整返回、6方法对、两批分层区间和全部96轮wall保存；低间隔追加审计名单为空，0新训练／画像／图。评价源现已曝光，不能参与后继模型选择。

'''
    newspec=before['spec.md'].replace('# ACSG 代码架构与实现契约\n\n','# ACSG 代码架构与实现契约\n\n'+spec_intro,1)
    marker='## 最新记录\n\n| 记录 | 内容与边界 |\n|---|---|\n'
    newsx=before['s-experiment.md'].replace(marker,marker+'| [157 Energy两批新源验证](experiment_history/157_energy_selection_two_source_batches.md) | 同预算Uniform无稳定召回改善；Web对Default两点两批负，停止本版调参，保留成本候选 |\n',1)
    newreadme=before['experiment_history/README.md'].replace('# ACSG 历史实验详细复盘\n\n','# ACSG 历史实验详细复盘\n\n2026-09-30最新[157 Energy四模型两批新源验证](157_energy_selection_two_source_batches.md)已核验：相对同预算Uniform未获稳定召回改善，Web对Default两点两批负；停止本版选样器调参，保留构建成本候选，默认不变。下一步只读连接诊断及共享精确标注工程检查。\n\n',1)
    changes={'summary.md':new_summary,'s-target.md':new_target,'spec.md':newspec,'s-experiment.md':newsx,'experiment_history/README.md':newreadme}
    backup=R/'reviews/root_docs_before';backup.mkdir()
    for name in files:
        p=backup/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,p)
    shutil.copy2(CAMP/'state.json',backup/'campaign_state.json')
    write_new(R/'report.md',report);write_new(R/'results/decision.json',json.dumps(decision,ensure_ascii=False,indent=2)+'\n')
    write_new(ROOT/'experiment_history/157_energy_selection_two_source_batches.md',card)
    for name,text in changes.items():(ROOT/name).write_text(text)
    state=json.loads((CAMP/'state.json').read_text());assert 'energy_fresh_transfer_v1' not in state['completed_stages']
    state['completed_stages'].append('energy_fresh_transfer_v1');state['new_NSG_calls']+=655872;state['new_ANN_calls']+=655360
    state['new_exact_GT_queries']+=16384;state['independent_full_base_float64_GT_checks']+=32
    state.update(stage='energy_routing_bridge_prepared',active_process=None,last_updated_unix=time.time(),default_changed=False)
    (CAMP/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    seal={str(p.relative_to(R)):ident(p) for p in sorted(R.rglob('*')) if p.is_file() and p.name!='seal.json'}
    write_new(R/'reviews/seal.json',json.dumps({'status':'AUDITED_COMPLETE','unix':time.time(),'files':seal,'decision':decision},ensure_ascii=False,indent=2)+'\n')
    assert sum(p.stat().st_size for p in CAMP.rglob('*') if p.is_file())<1024**3
    print(status,'SEALED',len(seal),'FILES',flush=True)

if __name__=='__main__':main()
