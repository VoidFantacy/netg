import os
os.sched_setaffinity(0,{14})
import csv,hashlib,json,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parent;CAMP=R.parents[1];ROOT=R.parents[3]

def put(p,x):
    with Path(p).open('x') as f:f.write(x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def main():
    s=json.loads((R/'results/cost_summary.json').read_text());a=json.loads((R/'reviews/independent_audit.json').read_text())
    run=json.loads((R/'reviews/run_complete.json').read_text());why=json.loads((R/'reviews/id_difference_explanation.json').read_text())
    assert a['status']=='PASS' and all(json.loads((R/'reviews'/f).read_text())['exit_code']==0 for f in ['controller_exit.json','audit_exit.json'])
    assert (s['new_GT'],s['new_NSG'],s['new_ANN'])==(53100,78080,3072)
    restored=[k for k,v in s['cases'].items() if v['deployment_identity_restored']]
    failed=[k for k,v in s['cases'].items() if not v['deployment_identity_restored']]
    assert failed==['yandex_t2i_official10M_ip_v1__Default'] and len(restored)==5
    assert why['old_V_plus_only_identified_mass_changes_W_bits_identity'] and why['changed_W_hub_slots']==[246,307]
    rows=[];identity=[]
    for ds,methods in s['datasets'].items():
        short='WebVid' if ds.startswith('web') else 'Yandex'
        for m in ['Default','Uniform','EnergyTree']:
            v=methods[m];z=s['cases'][ds+'__'+m];co=z['exact_prefix_comparison']
            rows.append(f'| {short} | {m} | {v["complete_wall_seconds"]:.6f} | {v["ratio_to_default"]:.6f} | {"是" if v["deployment_identity_restored"] else "否，旧质量不可复用"} |')
            identity.append(f'| {short} | {m} | {co["ordered_first10_changed_queries"]} / {co["set_first10_changed_queries"]} | {co["first10_distance_bits_changed_cells"]} | {z["W_changed_float32_cells"]} | {z["graph"]["semantic_identity_to_old_model"]} |')
    quality=[]
    with (R.parent/'energy_fresh_transfer_v1/results/metrics.csv').open() as f:
        for v in csv.DictReader(f):
            if v['scope']!='pooled_equal_batches' or v['method']=='ShuffledEnergyTree':continue
            method='Default' if v['method'].startswith('GT10') else v['method'];ds=v['dataset'];z=s['cases'][ds+'__'+method]
            if not z['deployment_identity_restored']:continue
            quality.append(f'| {"WebVid" if ds.startswith("web") else "Yandex"} | {v["K"]} / {v["L"]} | {method} | {100*float(v["recall"]):.6f} | {float(v["QPS"]):.3f} |')
    status='AUDITED_FIVE_IDENTITIES_YANDEX_DEFAULT_CHANGED'
    next_text='五份模型可连接157原质量证据；Yandex新Default的完整费用有效，但未恢复原模型身份，禁止挂接旧Recall或自动切默认。不修补这条已发现标签、不追加新源矩阵；后续仅做已冻结的质量区间数学枚举和单hub几何机会检查。'
    report='''# 共享批处理三方完整构建：五份身份恢复，一份数值边界例外

2026-09-30六格全部结束，原生及独立数值核验通过。**Web三份、Yandex两个低标签候选恢复完整H/W/图身份；Yandex新Default没有恢复，当前默认不变。**

## 本轮完整构建费用

每格从无目标标签独立开始，均含自己的QGT、加载、精确/近似标签、必要选样与二次加载、画像、hash、输出及小图。每格只测一次；Web按Default→Uniform→Energy、Yandex反向，未清缓存，不称随机重复或冷缓存加速。比值只比较本轮费用，Yandex比值不能与原Default质量拼成同模型性能取舍。

| 数据集 | 方法 | 完整wall秒 | 对本轮Default费用比 | 完整部署身份恢复 |
|---|---|---:|---:|---|
'''+ '\n'.join(rows)+'''

Web同质量身份的Uniform/Energy构建费用分别少63.965%/60.942%。Yandex候选仍有各自质量对应，但新Default质量未知；仅费用比为0.247671/0.271982。原154默认336.051/1519.754秒和156 Energy131.133/259.137秒仍保留原合同，不能删去。除batch外，本轮统一前缀持久化和hash输出，Yandex Uniform还只读教师必要源行，故相对旧费用的全部变化不能都归因于批大小。159才是隔离批处理因素的微测。

## 消费标签与完整模型身份

| 数据集 | 方法 | 前10有序 / 集合改变query | 前10分数bits改变单元 | W改变f32单元 | 图完整语义同一 |
|---|---|---:|---:|---:|---|
'''+ '\n'.join(identity)+f'''

所有H、QGT实际消费ID/分数、原聚类结果、教师全100 ID/分数hash均恢复。Web三温度恢复；Energy两集的树和选行都恢复。非消费分数bits变化不是画像变化，但消费目标集合变化可以成为画像变化。

Yandex源行6141原rank10为1422685，新rank10为6713583。独立float64全库第10/11分差6.4282587e−8，原前者更高；新float32输出在预定数值误差包络内，却不等于原目标身份。两个目标分到不同hub，分别使hub 3823364质量减少约0.1、hub 3141433增加0.1。仅把这项质量差加到原合力，已逐位恢复本次全部W；恰有2行/400个f32单元改变，最大绝对差0.0002987944。图有1个节点的有序邻接记录不同。源行13980只交换同一集合中的第9/10项，两目标同属hub1128043，不改hard质量，故Uniform/Energy身份恢复。

这是真实批形状引起的浮点边界差异，不能因为距离误差很小就省去模型身份门；也不说明所有批处理都不可用。没有替换标签或重跑以让它通过。

独立审计包含34条float64全库top11（32固定+2个消费ID差异query）、全部保存消费距离重评分、192个独立hub合力、40000条手工树遍历、六图全部节点/向量/真实ID/层/边检查及3072次原生plain/count ANN。数值核验PASS与完整身份True是分开的结论。独立指同一agent的另一套实现，不是另一位人员。

## 可按完整身份连接的已有质量

以下仍是记录157两批共8192条/集、三轮完整wall、CPU15实际1线程的原测量，**本轮0新线上性能**。只列已恢复身份的模型；不是重新测得这些QPS。Yandex新Default刻意不在表中，原Default历史91.516113%/2335.782及91.037231%/1306.000仍属于旧模型。

| 数据集 | K / L | 方法 | 原Recall (%) | 原完整QPS |
|---|---|---|---:|---:|
'''+ '\n'.join(quality)+f'''

Energy相对同预算Uniform没有稳定新源Recall优势、Web相对Default有小幅损失的157结论不变。不因构建更便宜将其称为无损替代，不重开特征/深度/seed调参。

## 计量与决定

六构建与原生审计控制器{run['seconds']:.3f}秒；独立审计{a['seconds']:.3f}秒，后补差异归因{why['seconds']:.3f}秒。输入检查/编译和事后审计不计入单格完整构建。精确query53100、教师NSG78080、图审计ANN3072；另34次float64全库检查。6画像/图、6次QGT聚类、2棵Energy树；没有新确认query或线上质量矩阵。

{next_text}

[协议](protocol.md) · [全部费用与身份](results/cost_summary.json) · [独立核验](reviews/independent_audit.json) · [差异归因](reviews/id_difference_explanation.json) · [已有质量157](../energy_fresh_transfer_v1/report.md)。
'''
    card='''# 160 共享批处理后的三方完整构建

2026-09-30，Default／Uniform／Energy各两集、从无目标标签独立开始、六格单次完整wall均结束。Web分别332.954／119.980／130.046秒；Yandex602.533／149.230／163.878秒。QGT、完整教师、选样、两次载入、hash／输出和图计费；原旧费用保留，新旧输出合同不同，不能把全部差值都归batch。

独立核验PASS，但完整部署身份仅5/6恢复。Yandex Default有1条query在约6.43e−8的第10/11名边界换目标，跨hub质量改变导致W两行400单元和一节点有序邻接改变；仅这一质量差已解释并逐位恢复新W。另1条仅交换同hub的第9/10名，Uniform/Energy不受影响。禁止把新Yandex Default费用挂接旧质量；Web三方可以按身份连接157原质量，未测新线上性能。

全部H/QGT/教师全100 hash、Energy树／选行恢复。34条全库float64、192个hub合力、40000条树遍历、六图全结构及3072原生ANN核验；53100精确query、78080教师NSG、6画像／图、6次QGT聚类、2棵树。默认不变，不修补已发现标签重跑、不追加新源矩阵。

[完整报告](../entry_method_exploration/20260930_theory_until2200_v1/research/shared_batch_full_build_v1/report.md) · [全部费用/身份](../entry_method_exploration/20260930_theory_until2200_v1/research/shared_batch_full_build_v1/results/cost_summary.json) · [核验](../entry_method_exploration/20260930_theory_until2200_v1/research/shared_batch_full_build_v1/reviews/independent_audit.json)。
'''
    names=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md'];old={n:(ROOT/n).read_text() for n in names}
    backup=R/'reviews/root_docs_before_closeout';backup.mkdir()
    for n in names:
        p=backup/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,p)
    shutil.copy2(CAMP/'state.json',backup/'campaign_state.json')
    put(R/'report.md',report);put(ROOT/'experiment_history/160_shared_batch_full_build_identity.md',card)
    put(R/'decision.json',{'status':status,'restored_cases':restored,'changed_cases':failed,'default_changed':False,'new_online_performance':False,'next_boundary':next_text})
    start=old['summary.md'].index('[共享批处理三方完整构建]');end=old['summary.md'].index('[159共享精确标签检查]')
    summary=old['summary.md'][:start]+'''[160共享三方完整构建](experiment_history/160_shared_batch_full_build_identity.md)已审计：Web Default／Uniform／Energy为332.954／119.980／130.046秒，完整身份都恢复；Yandex为602.533／149.230／163.878秒，但新Default因1条近并列目标跨hub变化，W两行及图改变，不能沿用旧质量。两份Y候选身份恢复；本轮0新线上性能。原默认不变，费用与身份不合并判定。

'''+old['summary.md'][end:]
    (ROOT/'summary.md').write_text(summary)
    start=old['spec.md'].index('[共享批处理构建工具]');end=old['spec.md'].index('[精确标签四格工具]')
    spec=old['spec.md'][:start]+'''[共享批处理构建工具](entry_method_exploration/20260930_theory_until2200_v1/research/shared_batch_full_build_v1/protocol.md)六格已完成/审计：fit真实K100/batch1024、保存前11与全100 hash；QGT调用/去重不改。教师主体保持、可按固定源行读取；GT/NSG/审计ANN先预留后完成，全部构建后统一核验H/W/图。五份恢复完整身份，Yandex Default的近并列消费集合改变造成W/图变化；数值PASS不等于身份恢复，不自动替换旧实现或沿用旧质量。

'''+old['spec.md'][end:]
    (ROOT/'spec.md').write_text(spec)
    t=old['s-target.md'].replace('记录141–159已完成','记录141–160已完成',1)
    left=t.index('[159固定2×2精确标注检查]');right=t.index('2026-09-22用户修订：')
    t=t[:left]+'''[159微测](experiment_history/159_exact_label_batch_and_rank_dispatch.md)与[160共享完整构建](experiment_history/160_shared_batch_full_build_identity.md)已结束。五份模型身份恢复，Yandex新Default在一条近并列目标处改变W/图；其602.533秒不能配旧Recall。原默认保留，不定点修补已发现标签、不追加新源矩阵；Energy本版调参继续停止。

后续先完成[hard质量区间固定枚举](entry_method_exploration/20260930_theory_until2200_v1/research/hard_mass_certificate_v1/protocol.md)，再作[单hub球/半空间训练侧机会检查](entry_method_exploration/20260930_theory_until2200_v1/research/single_hub_certificate_opportunity_v1/protocol.md)。它们不改底图或线上停止规则，不能把多数类别/历史直方图稳定当完整质量认证；无真实数值/费用证据则不造新索引。整日新增1GiB、空余6GiB、21:30后不启可能超时作业、22:00结束。

'''+t[right:]
    (ROOT/'s-target.md').write_text(t)
    marker='## 最新记录\n\n| 记录 | 内容与边界 |\n|---|---|\n';assert marker in old['s-experiment.md']
    (ROOT/'s-experiment.md').write_text(old['s-experiment.md'].replace(marker,marker+'| [160 共享完整构建身份](experiment_history/160_shared_batch_full_build_identity.md) | 六格实际费用、5/6身份恢复；Y新Default近并列跨hub改变W/图，旧质量不可拼接 |\n',1))
    title='# ACSG 历史实验详细复盘\n\n';assert title in old['experiment_history/README.md']
    (ROOT/'experiment_history/README.md').write_text(old['experiment_history/README.md'].replace(title,title+'2026-09-30最新[160共享三方完整构建](160_shared_batch_full_build_identity.md)完成，五份身份恢复；Yandex新Default费用有效、旧质量不可复用，默认不变。\n\n',1))
    state=json.loads((CAMP/'state.json').read_text());assert R.name not in state['completed_stages'];state['completed_stages'].append(R.name)
    state['new_NSG_calls']+=78080;state['new_ANN_calls']+=3072;state['new_exact_GT_queries']+=53100
    state['independent_full_base_float64_GT_checks']+=34;state['new_profiles']+=6;state['new_graphs']+=6;state['new_qgt_kmeans_fits']+=6;state['small_trees_shared_batch_actual']=2
    state.update(stage=status.lower(),active_process=None,last_updated_unix=time.time());(CAMP/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    files={str(p.relative_to(R)):ident(p) for p in sorted(R.rglob('*')) if p.is_file() and p.name!='seal.json'}
    put(R/'reviews/seal.json',{'status':'AUDITED_COMPLETE_WITH_IDENTITY_EXCEPTION','unix':time.time(),'files':files,'default_changed':False})
    print(status,flush=True)

if __name__=='__main__':main()
