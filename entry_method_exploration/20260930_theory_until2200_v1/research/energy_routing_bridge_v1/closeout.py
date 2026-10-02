import os
os.sched_setaffinity(0,{14})
import hashlib,json,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parent;CAMP=R.parents[1];ROOT=R.parents[3]

def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def put(p,text):
    with Path(p).open('x') as f:f.write(text)

def main():
    s=json.loads((R/'results/summary.json').read_text());a=json.loads((R/'reviews/independent_audit.json').read_text());assert a['status']=='PASS'
    correction=R.parent/'routing_member_count_clarification_v1';co=json.loads((correction/'results.json').read_text());assert co['status']=='PASS'
    pooled={};rows=[];group_rows=[];risk_rows=[];gains={}
    for ds in ['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']:
        cases=[v for v in s['cases'].values() if v['dataset']==ds];name='Web' if ds.startswith('web') else 'Yandex';pairs=[]
        for pair0 in cases[0]['comparisons']:
            name_m,ref=pair0['method'],pair0['reference']
            ps=[next(x for x in c['comparisons'] if x['method']==name_m and x['reference']==ref) for c in cases]
            assert ps[0]['stored_W_squared_difference_sum']==ps[1]['stored_W_squared_difference_sum']
            p={'method':name_m,'reference':ref,'score_risk':sum(x['score_risk'] for x in ps)/2,
                'stored_W_squared_difference_sum':ps[0]['stored_W_squared_difference_sum'],
                'category_counts':[sum(x['category_counts'][i] for x in ps) for i in range(4)],
                **{key:sum(x[key] for x in ps) for key in ['exact_changes','actual_changes','norm_certificate','posthoc_certificate','near_float_boundary_either']},'points':[]}
            for k in [1,100]:
                groups=[]
                for first in next(x for x in ps[0]['points'] if x['K']==k)['groups']:
                    gs=[next(g for pt in v['points'] if pt['K']==k for g in pt['groups'] if g['category']==first['category'] and g['numeric_group']==first['numeric_group']) for v in ps]
                    combined={key:(first[key] if key in ['category','numeric_group'] else sum(g[key] for g in gs)) for key in first}
                    groups.append(combined)
                p['points'].append({'K':k,'groups':groups})
            pairs.append(p)
            if name_m=='EnergyTree':
                output=[]
                for k in [1,100]:
                    gg=next(x for x in p['points'] if x['K']==k)['groups'];gg=[g for g in gg if g['numeric_group']=='all']
                    output.append(sum(g['ordered_output_changes'] for g in gg))
                    for g in gg:
                        if g['category'] not in [1,3]:continue
                        group_rows.append(f'| {name} / {ref} | {k} | {g["category"]} | {g["n"]} | {g["ordered_output_changes"]} / {g["output_set_changes"]} | {g["rescue_members"]} / {g["damage_members"]} | {g["net_positive_members"]} / {g["net_negative_members"]} |')
                rows.append(f'| {name} / {ref} | {p["exact_changes"]} | {p["actual_changes"]} | {p["category_counts"][1]} | {p["category_counts"][2]} | {output[0]} | {output[1]} |')
        reference=cases[0]['models'][0]['method'];risks={p['method']:p for p in pairs if p['reference']==reference}
        gains[ds]=1-risks['EnergyTree']['score_risk']/risks['Uniform']['score_risk']
        for m in ['Uniform','ShuffledEnergyTree','EnergyTree']:
            p=risks[m];risk_rows.append(f'| {name} | {m} | {p["stored_W_squared_difference_sum"]:.9f} | {p["score_risk"]:.9f} |')
        pooled[ds]={'n':8192,'comparisons':pairs,'energy_score_risk_reduction_vs_uniform':gains[ds]}
    report='''# 能量选择的分数改善与实际搜索之间的连接

2026-09-30，固定157全部四模型、两批新源、六方法对；只读诊断与另一套实现核验通过。**相对默认的分数平方差改善已在新查询上出现，仍不足以得到稳定召回增益。** 本结果缩小了待解释的环节，不把观察性分组称因果归因，不据这些query重训。

## 分数与画像差

每集8192 query等权合并。W为实际存储float32转float64，只对query作正标量单位化，未再次单位化W；以下均以本集Default为参照。

| 数据集 | 方法 | 存储W平方差总和 | query分数平方差均值 |
|---|---|---:|---:|
'''+ '\n'.join(risk_rows)+f'''

Energy的分数平方差相对Uniform下降{100*gains['webvid2_5m_light_v1']:.3f}%／{100*gains['yandex_t2i_official10M_ip_v1']:.3f}%。这是对当前默认画像分数的差，不是真实搜索效用误差；较小平方差不能确定入口边界翻转的方向、实际近似小图路径或有限主搜索的收益。二阶矩恒等式逐项恢复，最大误差{a['maximum_score_risk_identity_error']:.3g}。

## Energy相对三种对照的事件计数

| 数据集 / 对照 | 精确top3变 | 实际top3变 | 精确同而实际变 | 精确变而实际同 | R1有序返回变 | R100有序返回变 |
|---|---:|---:|---:|---:|---:|---:|
'''+ '\n'.join(rows)+'''

相对Uniform，648／772条查询换实际入口，但最终R1返回仅11／24条改变。入口相同者的主搜索返回、距离bits和主NDC全部一致；入口变化者也多数进入相同最终返回。该固定工作点的吸收现象不代表所有预算入口无用，更不否定历史全H余量。

## 成员增损与四格分解

事件1为精确top3相同、实际入口改变；事件3为两者都改变。事件0／2的实际入口相同，净命中变化为0，完整单元仍保存在JSON中。以下真救回／真损伤是正确成员集合差；每query净增加／净减少另列，K100两侧可同时发生并相互抵消。

| 数据集 / 对照 | K | 事件 | query数 | 有序 / 集合返回变 | 真救回 / 真损伤 | query净增加 / 净减少 |
|---|---:|---:|---:|---:|---:|---:|
'''+ '\n'.join(group_rows)+'''

例如Energy对Uniform的Web R100，事件1净−63成员、事件3净+52，总计−11；Y分别+160／−129，总计+31。分数边界与近似路径对应的观察组具有不同符号，不能从“更接近默认分数”推出总召回提升；也不能据此说固定小图拓扑一定能消除损伤，因为尚未实施那项干预。原145已有相关交叉研究，当前不另开图seed／拓扑调优分支。

全方法的精确／实际不一致、浮点近边界、Cauchy范数证书及事后分数证书均按每批保存。充分证书未通过不等于发生排名变化；float64数学精确top3不冒充原生浮点逐位排序。

## 核验、计数澄清与结束边界

'''+f'''分析{s['seconds']:.3f}秒、核验{a['seconds']:.3f}秒；1024条独立标量排名、1536个证书、576个全query组单元、131072个返回query以及197项身份通过。独立指同一agent的另一个标量／编码集合实现。0新GT／NSG／ANN／画像／图／性能。

另补[145旧计数用语](../routing_member_count_clarification_v1/report.md)：旧R100字段是每query净差的正／负累计，已另算真成员增损，120个组单元与20身份通过。旧净Recall和结论保持；未修改旧报告／数据／封存。新工具将有序返回、集合返回、命中集合、真成员差、净成员差分别保存。

157停止本版Energy选择器调参的判断保持。接下来只运行已冻结的共享精确标签四格工程检查，不用新评价query选模型，也不从本分组外推在线速度。

证据：[协议](protocol.md) · [计数和风险推导](theory.md) · [全部每批](results/summary.json) · [合并](results/pooled.json) · [核验](reviews/independent_audit.json)。
'''
    card='''# 158 Energy画像分数到实际搜索的连接诊断

2026-09-30，沿157固定四模型／两批／六方法对只读分析，0新搜索、GT、模型或性能。Energy相对Default的query分数平方差比Uniform低13.291%／27.999%；该几何变化已在新query体现，但157没有稳定召回改善。

| Energy相对Uniform，每集8192条 | Web | Yandex |
|---|---:|---:|
| 精确top3改变 | 428 | 619 |
| 实际top3改变 | 648 | 772 |
| 精确同、实际变 | 297 | 203 |
| 精确变、实际同 | 77 | 50 |
| 最终R1返回改变 | 11 | 24 |
| 最终R100有序返回改变 | 57 | 75 |

相同入口者主返回／距离bits／主NDC全部相同；不同入口者也多数保持最终返回。Web R100在“精确同、实际变”组净−63成员，另一实际改变组+52；Y两组+160／−129。它们是固定模型的观察性事件分解，不能解释成小图拓扑干预的因果效应，不据此调图或继续训练。

按实际float32 W转float64评分，只单位化query；二阶矩而非中心化协方差，最大恒等式误差1.53e−16。所有浮点边界与证书、全部三种控制都保存。R100真实成员救回／损伤与每query净变化分开，有序输出与集合变化分开。

分析7.627秒、另一套实现核验4.596秒；1024标量top3、1536证书、576组单元、131072返回和197身份通过。原145计数用语另附后补，120单元复算；旧净Recall与封存不变。157停止本版Energy调参、保留费用候选的边界保持，下一步只做共享精确标注四格检查。

[完整报告](../entry_method_exploration/20260930_theory_until2200_v1/research/energy_routing_bridge_v1/report.md) · [全部结果](../entry_method_exploration/20260930_theory_until2200_v1/research/energy_routing_bridge_v1/results/summary.json) · [独立核验](../entry_method_exploration/20260930_theory_until2200_v1/research/energy_routing_bridge_v1/reviews/independent_audit.json) · [145用语后补](../entry_method_exploration/20260930_theory_until2200_v1/research/routing_member_count_clarification_v1/report.md)。
'''
    files=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/145_profile_routing_search_bridge.md']
    old={f:(ROOT/f).read_text() for f in files};backup=R/'reviews/root_docs_before';backup.mkdir()
    for f in files:
        p=backup/f;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/f,p)
    shutil.copy2(CAMP/'state.json',backup/'campaign_state.json')
    put(R/'report.md',report);put(R/'results/pooled.json',json.dumps({'status':'AUDITED_REPORT_AGGREGATION','datasets':pooled,'new_searches':0},indent=2)+'\n')
    put(ROOT/'experiment_history/158_energy_profile_routing_search_bridge.md',card)
    # Presentation wording only in the newly generated clarification, never in original record145 artifacts.
    p=correction/'report.md';p.write_text(p.read_text().replace('以下展示原主候选','以下展示原混合候选'))
    add='''[158只读连接诊断](experiment_history/158_energy_profile_routing_search_bridge.md)进一步确认：Energy对默认分数的平方差较Uniform低13.3%／28.0%，但648／772条换入口只改变11／24条R1返回。几何改善在新query上存在，仍非Recall保证；观察性分组不归因于拓扑。另澄清[145旧R100计数](entry_method_exploration/20260930_theory_until2200_v1/research/routing_member_count_clarification_v1/report.md)为每query净差累计，真成员增损已补表，旧净Recall不变。

'''
    marker='Energy相对同2048预算Uniform'
    assert marker in old['summary.md'];(ROOT/'summary.md').write_text(old['summary.md'].replace(marker,add+marker,1))
    spec='''[Energy只读连接工具](entry_method_exploration/20260930_theory_until2200_v1/research/energy_routing_bridge_v1/protocol.md)已实现并核验：直接读取157冻结W/query/返回，按全H数学分数、实际三入口、有序输出／ID集合／命中集合分层；二阶矩字段正确命名。K100真实成员集合差、每query净差及同query抵消分别存储，所有旧方法对／两批总数恢复157；没有新搜索或模型接口。145历史组内rescues/damages只表示每query净差累计，另有[用语后补](entry_method_exploration/20260930_theory_until2200_v1/research/routing_member_count_clarification_v1/report.md)，原数值／seal不改。

'''
    (ROOT/'spec.md').write_text(old['spec.md'].replace('# ACSG 代码架构与实现契约\n\n','# ACSG 代码架构与实现契约\n\n'+spec,1))
    target=old['s-target.md'].replace('记录141–157已完成','记录141–158已完成',1)
    left=target.index('接下来运行已预写的');right=target.index('现有154／156双方已同享')
    target=target[:left]+'''[158只读连接诊断](experiment_history/158_energy_profile_routing_search_bridge.md)已核验：新源上分数平方差减少仍未带来稳定Recall，入口变化多数被主搜索吸收；观察性分组不支持重启图参数扫描。下一步运行[固定2×2精确标注检查](entry_method_exploration/20260930_theory_until2200_v1/research/exact_label_dispatch_v1/protocol.md)，只用旧fit各1024条，核对batch256/1024及k100/10的共享工程费用和消费ID身份。主比较固定为batch1024/k100，所有四格保留；它不是新ANN方法，不把局部吞吐外推完整构建。

'''+target[right:]
    (ROOT/'s-target.md').write_text(target)
    sxmarker='## 最新记录\n\n| 记录 | 内容与边界 |\n|---|---|\n'
    (ROOT/'s-experiment.md').write_text(old['s-experiment.md'].replace(sxmarker,sxmarker+'| [158 Energy分数到搜索连接](experiment_history/158_energy_profile_routing_search_bridge.md) | 新源分数差下降13.3%/28.0%仍无稳定Recall增益；入口吸收与真成员计数核验，0新搜索 |\n',1))
    (ROOT/'experiment_history/README.md').write_text(old['experiment_history/README.md'].replace('# ACSG 历史实验详细复盘\n\n','# ACSG 历史实验详细复盘\n\n2026-09-30最新[158 Energy分数到搜索连接](158_energy_profile_routing_search_bridge.md)完成，0新搜索／性能：新query分数平方差减少，实际入口变化多数未改变最终返回；未支持继续调本版选择器。145旧净计数用语另附澄清，原Recall结论不变。下一步为固定共享精确标注工程检查。\n\n',1))
    (ROOT/'experiment_history/145_profile_routing_search_bridge.md').write_text(old['experiment_history/145_profile_routing_search_bridge.md']+'''\n2026-09-30计数用语后补：原R100组内`rescues`／`damages`是每query净命中差的正／负累计，可能抵消同query内同时救回与损伤的成员。现已对全部120个K100组单元补算真实成员集合差；原净Recall／事件结论及封存保持。[独立说明与成员表](../entry_method_exploration/20260930_theory_until2200_v1/research/routing_member_count_clarification_v1/report.md)。\n''')
    state=json.loads((CAMP/'state.json').read_text());assert R.name not in state['completed_stages'];state['completed_stages'].append(R.name)
    state.update(stage='exact_label_dispatch_prepared',active_process=None,last_updated_unix=time.time())
    (CAMP/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    for directory in [correction,R]:
        files={str(p.relative_to(directory)):ident(p) for p in sorted(directory.rglob('*')) if p.is_file() and p.name!='seal.json'}
        sealpath=directory/'reviews/seal.json' if directory==R else directory/'seal.json'
        put(sealpath,json.dumps({'status':'AUDITED_COMPLETE','unix':time.time(),'files':files,'default_changed':False},indent=2)+'\n')
    print('AUDITED_COMPLETE_ENERGY_ROUTING_DIAGNOSTIC',flush=True)

if __name__=='__main__':main()
