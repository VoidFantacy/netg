import os
os.sched_setaffinity(0, {14})
import hashlib, json, shutil, time
from pathlib import Path

R=Path(__file__).resolve().parent;CAMP=R.parents[1];ROOT=R.parents[3]

def put(p, value):
    with Path(p).open('x') as f:
        f.write(value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def main():
    s=json.loads((R/'results/summary.json').read_text())
    a=json.loads((R/'reviews/independent_audit.json').read_text())
    assert a['status']=='PASS' and s['new_exact_GT_queries']==32768
    gate=a['main_cost_gate_pass'];same=a['both_sample_consumed_ID_identity'];rows=[];raw=[];main=[]
    for ds, v in s['datasets'].items():
        name='Web' if ds.startswith('web') else 'Yandex'
        for c in v['comparisons']:
            rows.append(f'| {name} | {c["name"]} | {c["mean_search_loop_seconds"]:.6f} | {c["mean_seconds_ratio_to_original"]:.6f} | {c["first10_order_changed_queries"]} / {c["first10_set_changed_queries"]} | {c["first10_distance_bit_changed_cells"]} |')
            raw.append(f'- {name} {c["name"]}: '+', '.join(f'{t:.9f}' for t in c['timed_seconds'])+' 秒。')
            if c['name']=='Batch1024K100':main.append({'dataset':ds,'ratio':c['mean_seconds_ratio_to_original'],'prefix_queries_changed':c['first10_order_changed_queries']})
    next_text=('主批处理费用门通过，可进入另行冻结的共享完整构建检查。必须对Default与低标签候选一致应用，并核验完整H/W/小图；本阶段不能直接更新旧总费用或引用旧线上质量为新模型质量。' if gate else '主批处理费用门未过，停止本次共享完整构建接续，不增加批大小、返回k或线程网格来挽救。')
    if gate and not same:
        next_text+=' 样本消费ID已经有差异，先解释数值边界及对下游的影响，不能声称无模型变化的替换。'
    status='COST_SIGNAL_PENDING_FULL_BUILD_IDENTITY' if gate else 'STOP_FIXED_BATCH_COST_GATE'
    report=f'''# 精确标签批处理与返回长度的固定四格检查

2026-09-30，两集历史fit各首1024条，四配置、一次预热和三轮计时均完成，独立实现核验通过。**主比较费用门{'通过' if gate else '未通过'}；这是一项共享离线工程检查，未测新ANN性能，也未改变默认。**

## 全部配置

search-loop时间包含结果内存分配、全部Faiss调用及复制；每集IndexFlat只加载一次。下表每格为1024条的三轮均值，费用比以Batch256K100为1；顺序/集合变化只比较真正消费的前10目标。CPU0–7，Faiss与各库池8，驻留线程数保存在原记录中，不写成实际仅8个线程。

| 数据集 | 配置 | 均值秒 | 原配置费用比 | 有序 / 集合改变query数 | 前10距离bits改变单元数 |
|---|---|---:|---:|---:|---:|
'''+ '\n'.join(rows)+'''

主比较固定为Batch1024K100对Batch256K100。另两格说明返回长度及其与批处理的交互；没有从四格中事后挑最快配置。全部计时如下，保留慢轮且未按结果重测：

'''+ '\n'.join(raw)+f'''

## 身份、数值与范围

原Batch256K100恢复154首1024条全部100个ID及距离bits；每配置预热与所有计时轮的输出hash一致。独立审计核验全部81920个消费距离单元，并对固定16条/集及所有前10有序ID不同的query并集作float64全库top11核验，共{a['additional_full_base_float64_checks']}条。名单在全库审计前形成且未超预定每集64条上限。数值容差不是逐ID相等，独立float64的边界完全并列时可包含任一合法子集。

主比较两集样本消费ID都相同：{same}。即使为True，也不能保证完整20K或最后短批一致。本阶段固定32768次精确query调用，含全部预热和重复；独立float64另记，0 NSG/ANN/模型/图。

控制器完整作业{s['seconds']:.3f}秒，独立核验{a['seconds']:.3f}秒；它们不是ANN QPS，也不等于候选完整构建费用。原154/156完整费用保持其原身份，不能按本微测比率直接缩放。库版本、二进制hash、实际线程池、base全SHA、全部原始输出及各轮hash均保存。

## 决定

{next_text}

[协议](protocol.md) · [源码依据](source_reasoning.md) · [数值与文献合同](../../literature/faiss_exact_contract_scope.md) · [完整结果](results/summary.json) · [核验](reviews/independent_audit.json)。
'''
    card=f'''# 159 精确标签批处理和消费长度的共享工程检查

2026-09-30，固定两集旧fit各1024条、batch256/1024×k100/10，1预热+3轮交错起点。主比较batch1024/k100费用门{'通过' if gate else '未通过'}。Web/Y均值费用比为{main[0]['ratio']:.6f}/{main[1]['ratio']:.6f}，消费前10有序ID改变{main[0]['prefix_queries_changed']}/{main[1]['prefix_queries_changed']}条。

所有四格和计时轮保留；原baseline全100 ID/距离bits恢复154，同配置重复hash一致。全部81920个消费距离单元及{a['additional_full_base_float64_checks']}条独立float64全库top11核验通过。32768精确query调用含预热/重复；独立float64另记，0新NSG/ANN/画像/图。

这是8线程离线标签search-loop，不是ANN QPS或完整构建费用；样本身份不等于完整20K身份。{next_text}

[完整报告](../entry_method_exploration/20260930_theory_until2200_v1/research/exact_label_dispatch_v1/report.md) · [全部结果](../entry_method_exploration/20260930_theory_until2200_v1/research/exact_label_dispatch_v1/results/summary.json) · [核验](../entry_method_exploration/20260930_theory_until2200_v1/research/exact_label_dispatch_v1/reviews/independent_audit.json)。
'''
    files=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md'];old={f:(ROOT/f).read_text() for f in files}
    backup=R/'reviews/root_docs_before';backup.mkdir()
    for f in files:
        p=backup/f;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/f,p)
    shutil.copy2(CAMP/'state.json',backup/'campaign_state.json')
    put(R/'report.md',report);put(ROOT/'experiment_history/159_exact_label_batch_and_rank_dispatch.md',card)
    put(R/'decision.json',{'status':status,'main_cost_gate_pass':gate,'sample_ID_identity':same,'default_changed':False,'new_online_performance':False,'next_boundary':next_text})
    add=f'''[159共享精确标签检查](experiment_history/159_exact_label_batch_and_rank_dispatch.md)已核验：batch1024/k100对原batch256/k100的Web/Y费用比{main[0]['ratio']:.4f}/{main[1]['ratio']:.4f}，消费前10有序ID改变{main[0]['prefix_queries_changed']}/{main[1]['prefix_queries_changed']}条；主费用门{'通过' if gate else '未通过'}。这是各1024条的离线微测，旧完整费用不外推替换，完整模型身份仍需验证。

'''
    summary=old['summary.md'].replace('[158只读连接诊断]',add+'[158只读连接诊断]',1)
    stale='[共享精确标注费用检查](entry_method_exploration/20260930_theory_until2200_v1/research/exact_label_dispatch_v1/protocol.md)已准备、尚未执行，不能提前替换原费用。'
    assert stale in summary;summary=summary.replace(stale,'共享批处理微测已完成，原完整构建费用仍保持实测身份。',1)
    summary=summary.replace('下一步只读分解四模型的分数、实际路由与主搜索吸收，不按曝光query继续补标。','四模型分数到搜索的只读分解已完成，不按曝光query继续补标。',1)
    (ROOT/'summary.md').write_text(summary)
    spec='''[精确标签四格工具](entry_method_exploration/20260930_theory_until2200_v1/research/exact_label_dispatch_v1/protocol.md)已实现并核验：同一IndexFlat按固定batch/k配置运行，保留warm输出和三轮完整hash，调用前预留预算；全base SHA、Faiss/BLAS二进制及线程身份冻结。首10有序/集合/bits分别比较，独立float64审计名单先锁定且有上限；没有W/图或性能接口，完整构建合同未替换。

'''
    (ROOT/'spec.md').write_text(old['spec.md'].replace('# ACSG 代码架构与实现契约\n\n','# ACSG 代码架构与实现契约\n\n'+spec,1))
    target=old['s-target.md'].replace('记录141–158已完成','记录141–159已完成',1)
    left=target.index('下一步运行[固定2×2精确标注检查]');right=target.index('现有154／156双方已同享')
    target=target[:left]+f'''[159固定2×2精确标注检查](experiment_history/159_exact_label_batch_and_rank_dispatch.md)已完成，主费用门{'通过' if gate else '未通过'}。{next_text}

'''+target[right:]
    (ROOT/'s-target.md').write_text(target)
    marker='## 最新记录\n\n| 记录 | 内容与边界 |\n|---|---|\n'
    (ROOT/'s-experiment.md').write_text(old['s-experiment.md'].replace(marker,marker+f'| [159 精确标签批处理四格](experiment_history/159_exact_label_batch_and_rank_dispatch.md) | 固定微测费用比{main[0]["ratio"]:.4f}/{main[1]["ratio"]:.4f}，身份核验；0新ANN，不外推完整构建 |\n',1))
    title='# ACSG 历史实验详细复盘\n\n';assert title in old['experiment_history/README.md']
    (ROOT/'experiment_history/README.md').write_text(old['experiment_history/README.md'].replace(title,title+f'2026-09-30最新[159精确标签四格检查](159_exact_label_batch_and_rank_dispatch.md)完成，主费用门{"通过" if gate else "未通过"}；所有配置与消费身份保留，完整构建尚未替换。\n\n',1))
    state=json.loads((CAMP/'state.json').read_text());assert R.name not in state['completed_stages'];state['completed_stages'].append(R.name)
    state['new_exact_GT_queries']+=s['new_exact_GT_queries'];state['independent_full_base_float64_GT_checks']+=a['additional_full_base_float64_checks']
    state.update(stage=status.lower(),active_process=None,last_updated_unix=time.time());(CAMP/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    files={str(p.relative_to(R)):ident(p) for p in sorted(R.rglob('*')) if p.is_file() and p.name!='seal.json'}
    put(R/'reviews/seal.json',{'status':'AUDITED_COMPLETE','unix':time.time(),'files':files,'default_changed':False})
    print('EXACT_LABEL_DISPATCH_AUDITED_COMPLETE',status,flush=True)

if __name__=='__main__':main()
