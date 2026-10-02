import os
os.sched_setaffinity(0,{14})
import hashlib,json,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[3];CAMP=R.parents[1]
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def write(p,s):
    with Path(p).open('x') as f:f.write(s)
def main():
    s=json.loads((R/'results/cost_summary.json').read_text());a=json.loads((R/'reviews/independent_audit.json').read_text());outer=json.loads((R/'reviews/audit_outer_cost.json').read_text())
    assert a['status']=='PASS' and s['gate_pass'];rows=[]
    for ds,label in [('webvid2_5m_light_v1','WebVid'),('yandex_t2i_official10M_ip_v1','Yandex')]:
        r=s['datasets'][ds];rows.append(f'| {label} | {r["complete_build_wall_seconds"]:.6f} | {r["default_complete_build_wall_seconds"]:.6f} | {100*(1-r["ratio_to_default_complete_wall"]):.3f}% | {r["control_incremental_wall_seconds"]:.6f} |')
    report='''# 固定r0能量补标的完整真实构建

2026-09-30，两集主构建和打乱监督控制完成，选行／画像身份与新图内部有效性全部核验通过。主完整wall低于共享按需QGT优化的原默认，因此具备冻结新query检验的条件；本记录没有新增Recall／QPS，不改变默认。

| 数据集 | Energy完整wall(s) | 默认完整wall(s) | 单次描述性节省 | Shuffled增量wall(s) |
|---|---:|---:|---:|---:|
'''+ '\n'.join(rows)+'''

Energy主费用从无目标标签输入开始，依次包含QGT聚类和精确目标、pilot1024精确目标、全20K单线程NSG教师、近似温度／八特征／一棵树、第二次载入base与1024追加精确目标、2048覆盖的画像、小图和所有进程启动／输出。Web原r0温度0.01631888747215271完全由本次新近似目标重算；Y-hard。没有读取旧GT、旧温度、W、模拟特征或选行作为构建输入。

Shuffled重新计算选择并追加1024精确目标，但共享本集新H／教师／pilot，表中只是控制增量。不能把它当独立完整构建，也不能由该增量推Energy相对Uniform的完整成本差。所有每批GT、载入、树、画像／构图及教师线程计量见原始cost_summary。单次每方法测量、OS缓存未清且未随机重复；这些是描述性wall比较，不是统计显著加速或冷缓存费用。公共底图原始构建、嵌入／下载、工具准备、事后审计另计。

## 身份与核验

QGT消费轨迹、实际生成GT、H和聚类计划与已审计按需版本相同；全20K近似教师ID／距离bits恢复E125，所有pilot／追加标签ID和距离bits恢复原精确fit参照。该结论不抹去记录148相对原5000全批QGT未使用尾部的浮点／并列差异。

四个方法的温度、八特征、pilot能量、树、全部预测及2048选行均逐位恢复记录155的固定r0；没有从16组挑最优。旧冻结模拟以原训练GT重新聚合，四份V／W逐位相同；另以独立逐query修正公式验证64个hub。新图不是历史图恢复：独立解析全部节点、向量、层和边范围，再比较每图256条训练query的plain/count返回和距离bits，并以float64内积核对所有返回分数。不称精确top3一致或检索性能。

'''+f'''核验手工前向{a['manual_tree_predictions']}条预测、{a['identities']}项身份；独立修正合力最大差{a['max_correction_error']:.3g}。事后核验外层完整wall {outer['seconds']:.6f}秒（其中Python核验{a['seconds']:.6f}秒），全部从构建wall中分开。

新精确GT{s['new_exact_GT']}、教师NSG{s['new_NSG']}、审计ANN{s['new_audit_ANN']}，4份画像／4图／4树／2次QGT聚类。数据仍是历史曝光训练池；实际重新标注证明流水费用和身份，不把它称新训练分布确认。

## 接续

下一阶段在读新源之前固定Default、同预算Uniform、ShuffledEnergy与Energy四模型，双集两批真实K1/K100，CPU15单线程完整wall；同时报告三种比较、跨批方向和查询配对不确定性。源必须排除记录151整个已曝光候选窗口。若无可转移收益，不再通过seed／温度／树深／追加标签量搜索重启本版；默认保持。

额外理论说明：[选择误差和交叉项](../energy_selection_regret_v1/theory.md)、[画像使用周期费用](../lifetime_cost_accounting_v1/theory.md)。[主动蒸馏前作核查](../../literature/active_distillation_scope.md)说明pilot后选样本身已有重合；尚未建立方法新颖性。

证据：[协议](protocol.md)、[完整费用](results/cost_summary.json)、[核验](reviews/independent_audit.json)、[GT逐批记账](reviews/gt_ledger.json)、[运行冻结](reviews/run_frozen.json)。
'''
    write(R/'report.md',report)
    write(R/'results/decision.json',json.dumps({'status':'PASS_ACTUAL_FIXED_ENERGY_BUILD_COST_AND_IDENTITY_SEARCH_UNMEASURED','gate_pass':True,'default_changed':False,'next':'freeze_four_models_before_new_query_source','new_online_performance':False},indent=2)+'\n')
    card='''# 156 固定r0 Energy完整构建

2026-09-30，主完整费用与同预算打乱监督控制均完成并通过身份核验。Energy从无目标标签输入开始，包含全20K单线程教师、pilot1024、特征／树、第二次base载入和追加1024 GT、画像／小图与输出。

| 数据集 | Energy完整wall(s) | 默认完整wall(s) | 单次描述性节省 | Shuffled增量wall(s) |
|---|---:|---:|---:|---:|
'''+ '\n'.join(rows)+f'''

四个选样器的特征、树、全部预测／选行恢复155固定r0，四份V/W与冻结模拟真值重建逐位相同；原生plain/count及独立新图／分数核验通过。GT7780、NSG40064、ANN2048，4W/4图/4树、2QGT聚类。单次缓存条件比较，控制增量不冒充独立完整成本。

费用和身份门通过，下一步先冻结四模型与新来源再测真实K1/K100。本记录0新线上性能、默认不变。主动蒸馏已有pilot后选样框架；新颖性和搜索收益尚未证明。

证据：[报告](../{R.relative_to(ROOT)}/report.md)、[协议](../{R.relative_to(ROOT)}/protocol.md)、[费用](../{R.relative_to(ROOT)}/results/cost_summary.json)、[审计](../{R.relative_to(ROOT)}/reviews/independent_audit.json)。
'''
    write(ROOT/'experiment_history/156_energy_selection_actual_full_build.md',card)
    backup=R/'reviews/root_docs_before';backup.mkdir()
    for name in ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:
        p=backup/name;p.parent.mkdir(exist_ok=True);shutil.copy2(ROOT/name,p)
    w,y=[s['datasets'][ds] for ds in ['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']]
    p=ROOT/'summary.md';t=p.read_text();old=next(line for line in t.splitlines() if line.startswith('[155无旧精确温度选样]'))
    new=f'[156固定r0实际Energy构建](experiment_history/156_energy_selection_actual_full_build.md)已通过费用与身份门：完整wall {w["complete_build_wall_seconds"]:.3f}／{y["complete_build_wall_seconds"]:.3f}秒，较同享QGT的默认单次少{100*(1-w["ratio_to_default_complete_wall"]):.2f}%／{100*(1-y["ratio_to_default_complete_wall"]):.2f}%；包含全20K教师、选样、两次载入和补标。四份特征／树／选行／V/W恢复155固定r0，打乱控制增量单列。尚无新线上性能，接下来冻结四模型与新源真实K1/K100。[155训练信息门](experiment_history/155_energy_selection_without_exact_temperature.md)的双集均值方向误差少6.811%／23.330%仍仅训练信号，Web有3/16组更差；[153复杂LOO](experiment_history/153_replacement_alignment_and_simple_control.md)原失败保持，不按曝光查询补标。'
    p.write_text(t.replace(old,new,1))
    p=ROOT/'spec.md';t=p.read_text();line=f'[实际Energy构建器]({R.relative_to(ROOT)}/protocol.md)已实现／核验：配置隔离旧标签与模拟参照，原按需QGT后pilot1024，原无router教师处理全20K；choose.py仅本次新近似标签／pilot生成八特征、能量树和追加源行；additional.py重新载入Flat生成1024目标，profile.py按2048实际批覆盖再归一化，原参数构图。GT逐批预留／完成记账，完整主wall与共享Shuffled控制增量分离；参考数据只在全构建后审计读取。四模型恢复固定r0选行／画像，新图全节点／边与plain-count/float64分数核验，0新线上性能。\n\n'
    p.write_text(t.replace('# ACSG 代码架构与实现契约\n\n','# ACSG 代码架构与实现契约\n\n'+line,1))
    p=ROOT/'s-target.md';t=p.read_text().replace('记录141–155已完成。','记录141–156已完成。',1).replace('155无旧温度Energy训练门已通过，下一步按原r0真实构建并计全部费用。','156原r0真实Energy构建与费用／身份核验已通过，下一步冻结四模型及新源真实K1/K100。',1)
    old=next(line for line in t.splitlines() if line.startswith('简单Energy控制已在[155]'))
    new='[156原r0 Energy实际构建](experiment_history/156_energy_selection_actual_full_build.md)已计入全20K教师、选样、两次base加载和追加GT，费用仍低于完整默认，四份选行／V/W逐位恢复155固定r0。下一步在读新源前冻结Default／同预算Uniform／Shuffled／Energy、两集各两批4096、真实K1/K100和全部完整wall；不选16组最好者，排除151整个已曝光源窗口。费用、相对随机改善、相对打乱的信息作用、相对默认取舍各自报告，不能互代；一次打乱模型不构成置乱检验。受整日1GiB和21:30边界约束；完成预定两批即结束，不追加至显著，复杂LOO原失败及默认不变。'
    p.write_text(t.replace(old,new,1))
    p=ROOT/'s-experiment.md';t=p.read_text();at=t.index('| [155 无旧温度能量选样]');p.write_text(t[:at]+'| [156 Energy实际完整构建](experiment_history/156_energy_selection_actual_full_build.md) | 原r0费用131.133/259.137秒，选择与四份画像恢复；0新线上性能，待四模型新源验证 |\n'+t[at:])
    p=ROOT/'experiment_history/README.md';t=p.read_text();at=t.index('2026-09-30最新');end=t.index('\n\n',at)
    p.write_text(t[:at]+'2026-09-30最新[156 原r0 Energy实际构建](156_energy_selection_actual_full_build.md)完成并核验：完整131.133/259.137秒，低于同享按需QGT的默认，四份选行／画像恢复；尚无新线上性能。接下来先冻四模型及新源真实K1/K100；默认不变。'+t[end:])
    p=CAMP/'state.json';state=json.loads(p.read_text());assert R.name not in state['completed_stages'];state['completed_stages'].append(R.name)
    for key,add in [('new_NSG_calls',s['new_NSG']),('new_ANN_calls',s['new_audit_ANN']),('new_exact_GT_queries',s['new_exact_GT']),('new_profiles',4),('new_graphs',4),('new_qgt_kmeans_fits',2)]:state[key]+=add
    state.update(stage='fixed_energy_build_pass_next_frozen_search',active_process=None,small_trees_energy_actual=4,last_updated_unix=time.time());p.write_text(json.dumps(state,indent=2)+'\n')
    files={str(p.relative_to(R)):ident(p) for p in R.rglob('*') if p.is_file() and p.name!='seal.json'}
    write(R/'reviews/seal.json',json.dumps({'status':'AUDITED_COMPLETE','unix':time.time(),'files':files},indent=2)+'\n');print('CLOSED156',flush=True)
if __name__=='__main__':main()
