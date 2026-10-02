import hashlib,json,time,zipfile
from pathlib import Path
R=Path(__file__).resolve().parent;CAMP=R.parents[1];ROOT=R.parents[3]
def put(p,x):
    with Path(p).open('x') as f:f.write(x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
    s=json.loads((R/'results.json').read_text());a=json.loads((R/'independent_audit.json').read_text());assert a['status']=='PASS'
    for d in s['datasets'].values():
        for v in d['comparisons'].values():assert v['strict_positive']==v['positive_outside_buffer']==v['buffer_band']==0 and v['negative_outside_buffer']==20000
    names=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md'];old={n:(ROOT/n).read_text() for n in names}
    marker='## 最新记录\n\n| 记录 | 内容与边界 |\n|---|---|\n';assert marker in old['s-experiment.md']
    assert '[161完整hard质量条件]' in old['summary.md'] and '下一步运行[单hub球/半空间训练侧机会检查]' in old['s-target.md']
    with zipfile.ZipFile(R/'root_docs_before.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in names:z.write(ROOT/n,n)
        z.write(CAMP/'state.json','campaign_state.json')
    with zipfile.ZipFile(R/'root_docs_before.zip') as z:
        for n in names:assert z.read(n)==(ROOT/n).read_bytes()
    put(R/'exit_status.json',{'main_exit':0,'audit_first_launch_exit':127,'audit_actual_exit':0,'first_launch_reason':'python command absent; numerical program did not start','first_log':'../../logs/single_hub_certificate_opportunity_audit_v1.log','actual_log':'../../logs/single_hub_certificate_opportunity_audit_v2.log','numerical_rerun':False})
    rows=[]
    for ds,d in s['datasets'].items():
        x=d['comparisons']['exact'];p=d['comparisons']['approx']
        rows.append(f'| {ds} | {d["M_outward"]:.9f} | {d["delta"]["median"]:.6f} | {d["u"]["median"]:.6f} | {x["t"]["median"]:.6f} | {p["t"]["median"]:.6f} | {x["slack"]["max"]:.6f} | 0 / 20000 |')
    report='''# 单球/单hub质量证书：两集均无通过机会

2026-09-30，固定训练侧检查与独立实现全部通过。**当前单球/单hub证书版本停止；两集各20K query，无论使用旧精确目标还是近似教师目标作阈值，全部离通过边界明确为负。默认不变。**

公式预先固定：最近hub与其余hub的归一化最小分类间隔δ，全球范数上界M，球与任一跨类半空间的内积上界u=√(1−δ²)。以已有10个不同候选的最小内积τ构造t=τ/(M||q||)，只有t>u才可认证完整top10均属最近hub。M完整覆盖base，不是近邻子集的最大范数。这里仅核验数学机会，不能替换原float32标签实现。

| 数据集 | M | δ中位 | u中位 | exact t中位 | approx t中位 | exact最佳余量t−u | 正值数 |
|---|---:|---:|---:|---:|---:|---:|---:|
'''+ '\n'.join(rows)+f'''

两集exact和approx各20K余量均小于−1e−10，没有缓冲带样本。Web的M仅略大于1，因此其失败不能归为少数超大范数离群点；查询到hub边界的间隔很小，排除其他类别所需的球冠相似度接近1，而候选阈值远低于该值。这只否定本固定界的可用性，不是否定完整质量可早于ID稳定，也不说明所有更精细几何界均无效。遵守已冻停止条件：不调M、不删离群点、不添加分块或改变教师预算继续本版。

Yandex对应现有hard目标；Web是反事实hard几何参照，不是其soft默认的质量证书。已有exact目标来自原float32精确实现，未称无限精度oracle。主实现和审计都使用固定原float32单位hub转float64后的数学几何，没有覆盖原生累计、并列或所有操作的形式化误差证明。

## 核验与费用

主程序{s['seconds']:.3f}秒，独立审计{a['seconds']:.3f}秒，CPU0–7、BLAS最多8线程；这是诊断成本，不是构建器或线上QPS。主范数扫描Web6.454秒/Y12.034秒；审计重扫全部2,505,000/10,000,000向量，采用另一块大小和einsum归约，逐query核全部hub分数、边界及候选阈值。两集400,000个候选点积各自复算，47/48条固定及近界query另作直接差向量内积；最大阈值差≤5.56e−16，直接δ差≤3.89e−16。输入SHA/大文件stat和全部保存数组hash一致。

第一次审计启动因不存在`python`命令退出127，数值程序未启动；原日志保留。随后用同一冻结代码和项目`.venv_cpu/bin/python`执行一次，退出0。主执行一次退出0，没有数值重跑、后改公式或筛选样本。0新GT/NSG/ANN/模型/图，无确认或held-out读取。同会话独立实现复核，不称独立人员审查。

下一步回到既有条件理论和旧方法边界整理。旧E121上层状态表已经实际失败，不能依据更早的E126提案摘要误认为仍未实现；先读原协议/结果，再判断是否存在未解决的新问题。

[协议](protocol.md) · [主结果](results.json) · [独立审计](independent_audit.json) · [数学推导](../hard_mass_certificate_v1/cone_bound.md) · [执行退出](exit_status.json)。
'''
    card='''# 162 单球/单hub质量证书训练侧机会检查

2026-09-30，沿161推导的固定球/半空间公式，在Web/Yandex原fit各20K完整检查。两集旧exact与approx候选阈值均0/20000可通过；归一化最佳余量分别−0.568694/−0.358309，全部远离1e−10缓冲。Web仅为反事实hard参照，Y为实际hard目标。没有原生float32标签替换或soft证书。

全base范数扫描、全query/hub几何与40万候选点积/集由另一归约实现复算通过；47/48条直接差向量边界审查。主26.069秒、审计13.489秒，CPU0–7/池8。第一次审计启动127只因python命令不存在，未执行数值；原日志与后续同码一次成功均保留。0新GT/NSG/ANN/模型/图/测试数据。

状态STOP_SINGLE_BALL_SINGLE_HUB_CERTIFICATE。原因是这份全局球界过松，不泛化为所有标签认证无用；不改M/删离群点/分块/调教师续跑。默认仍Web soft/Y hard、E99。旧E121已经运行并失败，后续不将更早E126提案当尚待实现的新分支。

[报告](../entry_method_exploration/20260930_theory_until2200_v1/research/single_hub_certificate_opportunity_v1/report.md) · [协议](../entry_method_exploration/20260930_theory_until2200_v1/research/single_hub_certificate_opportunity_v1/protocol.md) · [审计](../entry_method_exploration/20260930_theory_until2200_v1/research/single_hub_certificate_opportunity_v1/independent_audit.json)。
'''
    put(R/'report.md',report);put(ROOT/'experiment_history/162_single_hub_geometric_certificate_opportunity.md',card)
    put(R/'decision.json',{'status':'STOP_SINGLE_BALL_SINGLE_HUB_CERTIFICATE','default_changed':False,'new_search_calls':0,'reason':'No positive opportunity in exact or approximate modes on either complete fit20K set; independently verified far from boundary'})
    (ROOT/'summary.md').write_text(old['summary.md'].replace('[161完整hard质量条件]','[162单球/单hub证书](experiment_history/162_single_hub_geometric_certificate_opportunity.md)在两集各20K训练query均0通过，exact阈值也远低于上界；全量独立核验通过，停止这份过松的固定球界，不调参续跑。0新搜索/模型，默认不变。\n\n[161完整hard质量条件]',1))
    title='# ACSG 代码架构与实现契约\n\n';assert title in old['spec.md']
    (ROOT/'spec.md').write_text(old['spec.md'].replace(title,title+'[单hub几何机会工具](entry_method_exploration/20260930_theory_until2200_v1/research/single_hub_certificate_opportunity_v1/protocol.md)已实现/核验：完整base范数、固定float32单位H转float64的分类边界、旧候选前10原始内积；保存全query数组并以不同归约核验。仅数学hard机会诊断，无原生替换证书、soft支持或搜索接口；不改变默认。\n\n',1))
    target=old['s-target.md'].replace('记录141–161已完成','记录141–162已完成',1)
    target=target.replace('已通过，下一步运行[单hub球/半空间训练侧机会检查]','已通过；[单hub球/半空间训练侧机会检查]',1)
    target=target.replace('它们不改底图或线上停止规则','两集各20K均0通过、独立核验完成，固定单球版本停止，不调阈值/范数/分块/教师续跑。接下来整理条件理论与旧方法边界；E121状态表已失败，不因更早E126提案摘要重复实现。它们不改底图或线上停止规则',1)
    (ROOT/'s-target.md').write_text(target)
    (ROOT/'s-experiment.md').write_text(old['s-experiment.md'].replace(marker,marker+'| [162 单hub球界机会](experiment_history/162_single_hub_geometric_certificate_opportunity.md) | 双集fit20K均0通过、完整独立核验；停止固定球界，0新搜索/模型 |\n',1))
    title='# ACSG 历史实验详细复盘\n\n';assert title in old['experiment_history/README.md']
    (ROOT/'experiment_history/README.md').write_text(old['experiment_history/README.md'].replace(title,title+'2026-09-30最新[162单hub球界机会](162_single_hub_geometric_certificate_opportunity.md)双集完整训练检查与独立审计完成，0通过，固定版本停止，0新搜索/模型。\n\n',1))
    state=json.loads((CAMP/'state.json').read_text());assert R.name not in state['completed_stages'];state['completed_stages'].append(R.name)
    state.update(stage='single_hub_certificate_stopped_theory_continues',active_process=None,last_updated_unix=time.time());(CAMP/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<2*1024**2-16384
    assert sum(p.stat().st_size for p in CAMP.rglob('*') if p.is_file())<1024**3-16384
    put(R/'seal.json',{'status':'AUDITED_COMPLETE_FIXED_VERSION_STOPPED','unix':time.time(),'files':{str(p.relative_to(R)):ident(p) for p in sorted(R.rglob('*')) if p.is_file()}})
    print('STOP_SINGLE_BALL_SINGLE_HUB_CERTIFICATE',flush=True)
if __name__=='__main__':main()
