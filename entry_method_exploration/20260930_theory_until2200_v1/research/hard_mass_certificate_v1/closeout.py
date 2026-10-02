import hashlib,json,time,zipfile
from pathlib import Path
R=Path(__file__).resolve().parent;CAMP=R.parents[1];ROOT=R.parents[3]
def put(p,x):
    with Path(p).open('x') as f:f.write(x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
    s=json.loads((R/'results.json').read_text());a=json.loads((R/'independent_audit.json').read_text());assert a['status']=='PASS'
    assert json.loads((R/'exit_status.json').read_text())=={'main_exit':0,'audit_exit':0}
    rows=[]
    for mode,v in s['modes'].items():
        rows.append(f'| {mode} | {v["k_problems"]} | {v["candidate_counts_checked"]} | {v["stable_histogram"]} | {v["stable_histogram_uncertain_members"]} | {v["stable_majority_uncertain_histogram"]} |')
    report='''# 完整hard质量的区间证书：数学条件通过，实际费用未证

2026-09-30固定主全集和解释实例全部完成，两套实现逐实例摘要hash一致。**独立区间盒内的跨组条件得到验证；没有真实数据或加速结果，默认不变。**

主全集4个目标、全部二元分组、端点{0,1,2}的全部闭区间、K=1至4。20736个区间/标签实例；160000个带标签的整数补全（底层10000个分数补全复用于16组标签），不是160000次搜索或独立query。每个K检查全部合法计数，不只检查预报为真的项。三组情况仅有冻结的解释实例，通式依据文字证明，不能把它称为三组全空间穷举。

| 并列合同 | K问题 | 计数向量检查 | 计数稳定 | 计数定但成员不定 | 多数唯一且稳定但计数不定 |
|---|---:|---:|---:|---:|---:|
'''+ '\n'.join(rows)+f'''

全部充要性检查0反例；独立审计不调用主证书函数，改为枚举全部K子集，检验选中上端点是否能压过未选中下端点。该参照覆盖连续盒中的所有可实现成员集合，与整数枚举完全一致，因为每个可行集合都能在区间端点处实现。

具体例子：三个A目标区间[9,11]、[8,10]、[8,10]，一个B固定7，K2。A的具体两名可变，但质量恒为(1,0)。另三个A分数10、9、[0,8]，B固定7，K3；多数A不变，质量可为(2/3,1/3)或(1,0)。这说明认证完整质量既不必认证全部ID，也不能只认证赢家。

## 适用条件与前作

充要性需要各点分数独立取遍闭区间，且组标签固定；一般不紧名次界只有充分性，真实几何相关性可使盒条件过保守。任意并列合同需要跨组严格分离；固定ID合同使用(score,−ID)全序，但不是Faiss通用tie规则。原生浮点累计、soft质量、温度和最终W/图身份仍另核验。

标签比ID更早稳定已有公开方法动机；球界、原型区域鲁棒性及不确定排名都有前作，详见[文献关系](../../literature/label_certificate_prior_work.md)。本项是当前问题的条件推导和固定核验，不宣称首创普遍定理或新ANN算法。

主程序{s['seconds']:.3f}秒，独立审计{a['seconds']:.3f}秒，单进程绑定CPU0。0真实GT/NSG/ANN/训练/画像/图。下一步仅运行已冻结的单hub球/半空间训练侧机会检查；若可靠界无通过机会，停止这个版本，不按结果添加分块或调阈值。

[协议](protocol.md) · [理论及证明](theory.md) · [原始结果](results.json) · [独立审计](independent_audit.json) · [单hub特例](cone_bound.md)。
'''
    card='''# 161 GT10-hard完整质量的区间条件与穷举核验

2026-09-30，仅数学与合成枚举，0真实GT/NSG/ANN/训练/模型。独立分数区间盒、固定组标签下，以各组第c_h项下界严格超过其他组第c_g+1项上界认证完整计数；对紧端点盒及全并列语义也是必要条件。固定ID并列另用全序键，未冒充原生Faiss规则。

4目标全部二元标签/端点{0,1,2}区间/K1至4，两种并列合同各82944个K问题、145152个计数向量，0充要性反例。独立全子集端点可行性实现逐实例hash恢复。存在大量ID不定但计数固定，以及多数类别固定但计数不定的实例；三组通式有证明及固定例子，不是三组全空间穷举。

主3.173秒、审计1.635秒，CPU0。真实高维界/成本、浮点标签身份和Web soft仍未解决。已有标签稳定提前终止等前作，不主张凭该概念创新。后继单hub球/半空间机会检查已另冻，不自动构建新索引，默认不变。

[报告](../entry_method_exploration/20260930_theory_until2200_v1/research/hard_mass_certificate_v1/report.md) · [理论](../entry_method_exploration/20260930_theory_until2200_v1/research/hard_mass_certificate_v1/theory.md) · [核验](../entry_method_exploration/20260930_theory_until2200_v1/research/hard_mass_certificate_v1/independent_audit.json)。
'''
    names=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md'];old={n:(ROOT/n).read_text() for n in names}
    with zipfile.ZipFile(R/'root_docs_before.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in names:z.write(ROOT/n,n)
        z.write(CAMP/'state.json','campaign_state.json')
    with zipfile.ZipFile(R/'root_docs_before.zip') as z:
        for n in names:assert z.read(n)==(ROOT/n).read_bytes()
    put(R/'report.md',report);put(ROOT/'experiment_history/161_hard_mass_interval_certificate.md',card)
    put(R/'decision.json',{'status':'BOX_CERTIFICATE_VERIFIED_REAL_COST_UNKNOWN','real_search_calls':0,'default_changed':False})
    marker='[159共享精确标签检查]';assert marker in old['summary.md']
    (ROOT/'summary.md').write_text(old['summary.md'].replace(marker,'[161完整hard质量条件](experiment_history/161_hard_mass_interval_certificate.md)的固定枚举与独立子集核验通过：ID不定仍可计数固定，多数类别稳定则不足够。这只是数学条件，真实界/成本未证；没有新模型或搜索。\n\n'+marker,1))
    title='# ACSG 代码架构与实现契约\n\n';assert title in old['spec.md']
    (ROOT/'spec.md').write_text(old['spec.md'].replace(title,title+'[hard区间检查器](entry_method_exploration/20260930_theory_until2200_v1/research/hard_mass_certificate_v1/protocol.md)已实现/核验：固定有限输入、两种tie语义、全部候选计数与独立子集端点参照，流式摘要hash一致；不读真实query/base，无原生标签或模型接口。\n\n',1))
    t=old['s-target.md'].replace('记录141–160已完成','记录141–161已完成',1)
    t=t.replace('后续先完成[hard质量区间固定枚举]','[hard质量区间固定枚举]',1).replace('，再作[单hub球/半空间训练侧机会检查]','已通过，下一步运行[单hub球/半空间训练侧机会检查]',1)
    (ROOT/'s-target.md').write_text(t)
    marker='## 最新记录\n\n| 记录 | 内容与边界 |\n|---|---|---|\n';assert marker in old['s-experiment.md']
    (ROOT/'s-experiment.md').write_text(old['s-experiment.md'].replace(marker,marker+'| [161 hard质量区间证书](experiment_history/161_hard_mass_interval_certificate.md) | 独立盒内充要条件/两种tie穷举核验；0真实搜索，界与费用未知 |\n',1))
    title='# ACSG 历史实验详细复盘\n\n'
    (ROOT/'experiment_history/README.md').write_text(old['experiment_history/README.md'].replace(title,title+'2026-09-30最新[161完整hard质量区间条件](161_hard_mass_interval_certificate.md)完成数学核验，0真实搜索/模型，实际费用未知。\n\n',1))
    state=json.loads((CAMP/'state.json').read_text());assert R.name not in state['completed_stages'];state['completed_stages'].append(R.name)
    state.update(stage='box_certificate_verified_real_cost_unknown',active_process=None,last_updated_unix=time.time());(CAMP/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file()) < 240*1024
    put(R/'seal.json',{'status':'AUDITED_COMPLETE_MATHEMATICAL_ONLY','unix':time.time(),'files':{str(p.relative_to(R)):ident(p) for p in sorted(R.rglob('*')) if p.is_file()}})
    print('BOX_CERTIFICATE_VERIFIED_REAL_COST_UNKNOWN',flush=True)
if __name__=='__main__':main()
