import os
os.sched_setaffinity(0,{14})
import hashlib,json,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[3];CAMP=R.parents[1]
def write(p,text):
    with Path(p).open('x') as f:f.write(text)
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
    s=json.loads((R/'results/summary.json').read_text());a=json.loads((R/'reviews/independent_audit.json').read_text());assert s['gate_pass'] and a['status']=='PASS'
    rows=[]
    for ds,label in [('webvid2_5m_light_v1','WebVid'),('yandex_t2i_official10M_ip_v1','Yandex')]:
        for name in ['EnergyTree','ShuffledEnergyTree']:
            m=s['datasets'][ds]['methods'][name];r=m['ratio_of_mean_chord2_to_Uniform'];halves=m['halves_ratio_to_Uniform']
            rows.append(f'| {label} {name} | {r[0]:.6f} | {r[1]:.6f} | {halves[0][0]:.6f} / {halves[1][0]:.6f} | {m["replicates_better_than_Uniform"][0]}/16 | {m["r0_ratio_to_Uniform"][0]:.6f} |')
    report='''# 仅用近似标签定温度的简单能量选样复核

2026-09-30，冻结门全部通过、独立核验PASS；身份为训练侧信息信号，不是线上性能或默认替换。Web用全20K近似GT1与H的top2分数差中位数T=0.01631888747215271；Y保持hard。未读旧精确温度来构造特征、能量标签或选行。

每集16个原固定排列，1024 pilot标注训练一棵depth2树，从剩余池选1024；同2048预算Uniform与打乱同一pilot能量的ShuffledEnergy均保留。没有换特征、样本量、树深、seed或选各集最优方法。pilot归属按实际1024行形状单独计算，所选2048行按未来构建合同重新打分。所有预测与选行先保存并冻结，随后才读取完整训练真值和当前默认合力用于评分。

| 方法 | 平均chord²比／原默认参照 | 平均chord²比／同温度全精确参照 | 默认参照前8／后8比 | 优于随机次数 | 固定r0比 |
|---|---:|---:|---:|---:|---:|
'''+ '\n'.join(rows)+'''

表中分母均为同温度、同精确预算Uniform，数值越低越好。Energy对原默认参照平均误差少6.811%／23.330%，对同温度全精确参照少6.797%／23.330%；两集均超过预定5%门，两个半组均较好，并优于打乱监督。Web 3/16组仍差于Uniform，范围0.804618–1.043914，不能称逐样本或逐种子必优。Shuffled在Web也平均少1.832%，不能称它完全没有变化；这更强调必须报告完整控制。

Web、Y的r0 Uniform单位方向转float32后都逐位恢复已核验的HybridApproxMedian／HybridFixedTemperature。Y全部16组Energy选行与153相同，1024批归属合同没有改变其选择。所有方法均未出现径向反转。Web两种参照的差异很小但完整保留，未据此重新选择温度。

## 核验与范围

'''+f'''分析{s['seconds']:.6f}秒、独立代码核验{a['seconds']:.6f}秒；{a['manual_tree_predictions']}个树前向标量、{a['explicit_residual_energy_checks']}个显式残差投影能量、{a['leaf_target_mean_checks']}个叶目标均值、{a['independent_correction_aggregations']}个独立修正聚合及{a['identities']}项身份通过。两种聚合公式的chord²最大差{a['maximum_chord2_difference']:.3g}。

64棵小树、96个RAM混合合力，0新GT／NSG／ANN／部署W／图／线上性能。历史20K真值已曝光，各模拟构建器受2048条标签预算约束，但16种子不是16个独立数据集，也不是未曝光训练确认；全部真值在预测冻结后参与几何评分。

## 下一条必须得到的证据

按既定r0进行真实构建，保留同预算Uniform和Shuffled控制，计入全20K近似教师、QGT、1024 pilot、特征／树、第二轮1024精确标注、画像和小图。两次Flat载入若采用就全部收费。只有模型和身份通过后才另冻新源真实K1/K100评价；不将本方向误差门当成Recall门，也不读取151损伤query来补标。复杂LOO原版仍停止，本结果没有回改153的原门。

证据：[协议](protocol.md)、[理论](theory.md)、[统计](results/summary.json)、[独立核验](reviews/independent_audit.json)、[后继构建设计](next_build_design.md)。
'''
    write(R/'report.md',report)
    write(R/'results/decision.json',json.dumps({'status':'PASS_FIXED_ENERGY_INFORMATION_GATE_BUILD_COST_AND_SEARCH_UNMEASURED','predeclared_gate_pass':True,
        'next_seed':'original_r0_only','same_supervision_controls':['Uniform','ShuffledEnergyTree'],'default_changed':False,'new_GT':0,'new_NSG':0,'new_ANN':0,'new_exported_profiles':0,'new_graphs':0},indent=2)+'\n')
    card=f'''# 155 无旧精确温度的能量选样

2026-09-30，同2048精确预算，1024 pilot＋1024选择，16原固定排列。Web仅全近似GT1中位差定温度、Y-hard；Energy对随机的原默认方向误差均值少6.811%／23.330%，同温度全精确参照也少6.797%／23.330%，前后八组均较好、超过打乱监督，冻结门全过。Web仅13/16胜且最差比1.043914，不称必优。

r0 Uniform两集W bits恢复旧模型；Y全16 Energy选择与153一致。独立128万树前向、128显式能量、216叶均值、24聚合及21身份通过，最大chord差6.66e−16。分析26.019秒、审计11.015秒；64树／96 RAM合力，0新GT／搜索／部署W／图／性能。原20K训练真值已曝光，不冒充独立确认。

下一步只用原r0真实重建并测完整费用，再冻结真实K1/K100评价；同预算Uniform／Shuffled仍必须保留。复杂LOO原失败不改、默认不变。

证据：[报告](../{R.relative_to(ROOT)}/report.md)、[协议](../{R.relative_to(ROOT)}/protocol.md)、[统计](../{R.relative_to(ROOT)}/results/summary.json)、[审计](../{R.relative_to(ROOT)}/reviews/independent_audit.json)。
'''
    write(ROOT/'experiment_history/155_energy_selection_without_exact_temperature.md',card)
    backup=R/'reviews/root_docs_before';backup.mkdir()
    for name in ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:
        p=backup/name;p.parent.mkdir(exist_ok=True);shutil.copy2(ROOT/name,p)
    p=ROOT/'summary.md';t=p.read_text();old=next(x for x in t.splitlines() if x.startswith('[153方向收益选样]'))
    new='[155无旧精确温度选样](experiment_history/155_energy_selection_without_exact_temperature.md)已通过训练侧信息门：同2048预算Energy相对随机平均方向误差少6.811%／23.330%，双参照及前后半组均通过、胜打乱监督；Web仍有3/16组更差。原r0随机模型逐位恢复，0新线上性能，接下来只用原r0实测完整构建和搜索。[153复杂LOO](experiment_history/153_replacement_alignment_and_simple_control.md)原失败保持，不能按已曝光新源损伤行补标。[145](experiment_history/145_profile_routing_search_bridge.md)与[143](experiment_history/143_partial_exact_target_replacement.md)保留方向到搜索及有偏替换的边界。'
    p.write_text(t.replace(old,new,1))
    p=ROOT/'spec.md';t=p.read_text();line=f'[无旧精确温度选样工具]({R.relative_to(ROOT)}/protocol.md)已实现／核验：只用全近似标签、query、H构造Web中位差T和八特征，1024 pilot实际归属计算能量；depth2树／固定打乱对照各16组预测与选行先冻结，再以完整训练真值评分。选2048行按实际批合同重算混合贡献；保存树、特征、源行与审计用r0合力，不导出新部署W／图。r0随机W bits恢复旧Uniform；本工具0新搜索，统计秒数不是QPS。\n\n'
    p.write_text(t.replace('# ACSG 代码架构与实现契约\n\n','# ACSG 代码架构与实现契约\n\n'+line,1))
    p=ROOT/'s-target.md';t=p.read_text().replace('记录141–154已完成。','记录141–155已完成。',1).replace('下一步运行已冻结的无旧温度Energy诊断。','155无旧温度Energy训练门已通过，下一步按原r0真实构建并计全部费用。',1)
    old=next(x for x in t.splitlines() if x.startswith('另一条训练侧接续是简单Energy控制：'))
    new='简单Energy控制已在[155](experiment_history/155_energy_selection_without_exact_temperature.md)去掉旧精确温度依赖，双集／双参照／前后半组及打乱监督门全过。后继固定原r0，先从无标签输入实测完整构建：全20K近似教师、QGT、pilot1024、特征／树、追加1024 GT、画像／图及两次载入全部计入。Uniform使用已恢复的同预算冻结模型，Shuffled作为同监督信息控制并单列增量费用；不把增量冒充完整构建。身份审计通过后另冻真实K1/K100与新来源，受整日1GiB和21:30边界约束。记录151已曝光，不再作新确认，也不按损伤行补标；复杂LOO原失败保持，默认不变。'
    p.write_text(t.replace(old,new,1))
    p=ROOT/'s-experiment.md';t=p.read_text();mark='| [154 公平默认按需构建]';idx=t.index(mark)
    p.write_text(t[:idx]+'| [155 无旧温度能量选样](experiment_history/155_energy_selection_without_exact_temperature.md) | 同预算训练方向误差少6.811%/23.330%，冻结信息门通过；0新性能，原r0完整构建待测 |\n'+t[idx:])
    p=ROOT/'experiment_history/README.md';t=p.read_text();start=t.index('2026-09-30最新');end=t.index('\n\n',start)
    p.write_text(t[:start]+'2026-09-30最新[155 无旧精确温度能量选样](155_energy_selection_without_exact_temperature.md)通过双集训练信息门，同预算方向误差少6.811%/23.330%，尚无新性能；原r0真实构建为下一步。[154 公平默认构建](154_fair_default_demand_build_cost.md)已恢复原默认并补费用参照，混合仍有成本优势和质量取舍，默认不变。'+t[end:])
    p=CAMP/'state.json';state=json.loads(p.read_text());assert R.name not in state['completed_stages'];state['completed_stages'].append(R.name)
    state.update(stage='energy_clean_gate_pass_next_actual_build',active_process=None,simulated_hybrid_resultants_energy_clean=96,small_trees_energy_clean=64,last_updated_unix=time.time());p.write_text(json.dumps(state,indent=2)+'\n')
    files={str(p.relative_to(R)):ident(p) for p in R.rglob('*') if p.is_file() and p.name!='seal.json'}
    write(R/'reviews/seal.json',json.dumps({'status':'AUDITED_COMPLETE','unix':time.time(),'files':files},indent=2)+'\n');print('CLOSED155',flush=True)
if __name__=='__main__':main()
