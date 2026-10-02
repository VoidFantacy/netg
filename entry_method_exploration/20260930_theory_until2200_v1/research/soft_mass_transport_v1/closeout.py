import hashlib,json,time,zipfile
from pathlib import Path
R=Path(__file__).resolve().parent;CAMP=R.parents[1];ROOT=R.parents[3]
def put(p,x):
    with Path(p).open('x') as f:f.write(x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
    s=json.loads((R/'results.json').read_text());a=json.loads((R/'independent_audit.json').read_text());assert a['status']=='PASS' and a['input_sha256']==s['input_sha256']
    names=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md'];old={n:(ROOT/n).read_text() for n in names}
    marker='## 最新记录\n\n| 记录 | 内容与边界 |\n|---|---|\n';assert marker in old['s-experiment.md'] and '[162单球/单hub证书]' in old['summary.md']
    with zipfile.ZipFile(R/'root_docs_before.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in names:z.write(ROOT/n,n)
        z.write(CAMP/'state.json','campaign_state.json')
    with zipfile.ZipFile(R/'root_docs_before.zip') as z:
        for n in names:assert z.read(n)==(ROOT/n).read_bytes()
    put(R/'exit_status.json',{'original_main_exit':1,'corrected_full_main_exit':0,'audit_exit':0,'correction':'correction_v2.locked.json','numeric_main_attempts':2,'successful_numeric_mains':1,'audits':1})
    report=f'''# Soft质量到默认行为稳定性的条件链：数学核验完成

2026-09-30，**补全“目标/温度→平均归属→归一化画像→评分/间隔→实际入口→有限主搜索”的条件链**。全部数学小核验通过；没有新真实数据或候选，没有新的Recall/QPS结论，默认保持。

对目标预处理f和温度T使用联合变量z=f(x)/T，hub logit差的振幅d=osc(B(z−z′))给已有锐界||softmax(Bz)−softmax(Bz′)||₁≤2tanh(d/4)。集合平均误差可由最优运输上界控制；hard情形最小跨组费恰等于完整计数L1，soft情形可能因均值抵消而严格小于运输费。相同ID异温度不再自动零误差。

query合力要保留跨query抵消、径向分母和反向/零合力情况；再以真实评分二阶矩D_Q与top-r间隔分布F_Q得到P(精确集合改变)≤F_Q(τ)+2D_Q/τ²。到真实小图还必须加两套图各自的近似误差事件，之后才有固定NSG下的绝对Recall差界。它解释的是对参考行为的保真，不给收益符号、真实分布幂律、原生浮点认证或完整wall保证。

## 固定核验及纠错

| 检查 | 完整数目 | 结论 |
|---|---:|---|
| 不同H/d/K/两侧T的soft运输 | 2592 | 均值L1≤概率L1指派≤tanh指派≤Jensen界；移位/三角成立 |
| 三类别hard全部有序标签对，K1至4 | 7380 | 最优跨类费=计数L1 |
| 合力和归一化 | 512 | 矩阵/逐项累加、精确弦长和有条件切向界相符 |
| 评分与top-r倒置 | 3072 | m²≤2S及9个固定τ分解界通过 |
| 高精度 | 32运输实例+7二类等号 | Decimal 60位独立核对 |

主成功作业{s['seconds']:.3f}秒，独立审计{a['seconds']:.3f}秒，CPU0/数值库1线程。运输结果两实现最大差{a['max_transport_comparison_error']:.3g}，合力比较{a['max_aggregate_comparison_error']:.3g}，Decimal概率L1最大float差{a['decimal_probability_l1_max_float_error']:.3g}。有限数值检查不能代替全实数证明，完整证明/条件在[推导](pipeline_conditions.md)。

第一次主作业在最后的固定均值抵消夹具失败：scalar 0.5广播产生2×1矩阵，指派需要2×2。原run.py、协议、锁和失败日志均保留；run_v2.py只将该处写成两份显式(0.5,0.5)，冻结修正后完整重跑。理论、数据域、种子、门和容差未改；独立审计一次通过。两实现共享输入生成器，算术分别采用稳定指数/排列枚举和直接指数/线性指派/逐hub累加，固定例另用Decimal；这不称完全独立软件栈或人员审查。

反例也保留：soft均值误差0而最小运输费0.8；同一目标温度改变后L1差0.299477；纯径向反向时切向误差0、弦长平方4；零间隔可以被任意小评分误差改变。这些都禁止把较低ID/均方误差直接升级为搜索增益。

通用softmax界来自[Cohen与Fausti](https://arxiv.org/html/2309.02413v2)；分类margin理论已有[Audibert与Tsybakov](https://imagine.enpc.fr/~audibert/AudTsy_AOS0231.pdf)，但本页没有借用其Bayes风险速率。运输耦合、矩阵/归一化代数、倒置与Markov界在本设定中逐项写明；不主张新的通用定理或最优运输搜索算法。

[原协议](protocol.md) · [主结果](results.json) · [独立审计](independent_audit.json) · [修正冻结](correction_v2.locked.json) · [全比较数组](all_comparisons.npz)。0真实base/query/GT读取、0NSG/ANN/模型/图；构建费用和新源质量仍以记录157/160为准。
'''
    put(R/'report.md',report)
    card='''# 163 Soft目标运输、归一化与入口稳定条件

2026-09-30，纯数学/合成检查，0真实数据/搜索/模型。将目标与温度写为z=f(x)/T，用已有Hilbert-softmax L1锐界和耦合控制平均归属误差；hard跨组运输等于计数L1，soft均值可抵消。接续径向/切向精确式、评分二阶矩与top-r间隔，再保留两套物理小图的近似误差事件，得到对默认Recall的绝对偏差条件界，不给提升符号或wall保证。

2592运输、7380hard标签对、512合力、3072top-r及9阈值全部核验；独立指派/归约加32例Decimal和7个锐界等号。成功主1.340秒、审计4.127秒，CPU0/单线程。第一次主夹具误造2×1费用矩阵，原件保留，v2只修成原协议的2×2并完整重跑；域/公式/门未改。共享输入生成器、独立算术，非独立人员。

状态MATHEMATICAL_TRANSPORT_CHAIN_VERIFIED_NO_DEPLOYMENT。运输/单行能量上界可能很松，不据此重启Energy选样、温度扫描或状态表；默认不变。已有数学工具及其条件明确归属前作。

[完整推导](../entry_method_exploration/20260930_theory_until2200_v1/research/soft_mass_transport_v1/pipeline_conditions.md) · [报告](../entry_method_exploration/20260930_theory_until2200_v1/research/soft_mass_transport_v1/report.md) · [审计](../entry_method_exploration/20260930_theory_until2200_v1/research/soft_mass_transport_v1/independent_audit.json)。
'''
    put(ROOT/'experiment_history/163_soft_mass_transport_pipeline_conditions.md',card)
    put(R/'decision.json',{'status':'MATHEMATICAL_TRANSPORT_CHAIN_VERIFIED_NO_DEPLOYMENT','default_changed':False,'new_search_calls':0,'new_models':0})
    (ROOT/'summary.md').write_text(old['summary.md'].replace('[162单球/单hub证书]','[163误差条件链](experiment_history/163_soft_mass_transport_pipeline_conditions.md)已补齐目标/温度、平均归属、归一化、评分间隔、实际入口到固定搜索的保真条件，并通过独立合成核验；不能推出召回提升或费用保证，0新真实数据/模型。\n\n[162单球/单hub证书]',1))
    title='# ACSG 代码架构与实现契约\n\n';assert title in old['spec.md']
    (ROOT/'spec.md').write_text(old['spec.md'].replace(title,title+'[Soft运输数学检查器](entry_method_exploration/20260930_theory_until2200_v1/research/soft_mass_transport_v1/protocol.md)已实现/核验：固定合成输入、枚举指派与独立线性指派、归一化/评分倒置检查、Decimal固定例；完整比较数组与源锁保留。v1夹具形状错误原件与v2单行修正分存；没有真实数据/画像构建/搜索接口。\n\n',1))
    target=old['s-target.md'].replace('记录141–162已完成','记录141–163已完成',1)
    target=target.replace('接下来整理条件理论与旧方法边界','[Soft误差条件链](experiment_history/163_soft_mass_transport_pipeline_conditions.md)与独立合成核验已完成。接下来继续核对理论假设、前作边界与整日证据',1)
    (ROOT/'s-target.md').write_text(target)
    (ROOT/'s-experiment.md').write_text(old['s-experiment.md'].replace(marker,marker+'| [163 Soft质量条件链](experiment_history/163_soft_mass_transport_pipeline_conditions.md) | 目标/温度→归一化→评分间隔→实际路由的保真条件；独立合成核验，0真实搜索/模型 |\n',1))
    title='# ACSG 历史实验详细复盘\n\n';assert title in old['experiment_history/README.md']
    (ROOT/'experiment_history/README.md').write_text(old['experiment_history/README.md'].replace(title,title+'2026-09-30最新[163Soft质量条件链](163_soft_mass_transport_pipeline_conditions.md)完成理论与独立合成核验；保真条件不是Recall增益/费用保证。\n\n',1))
    state=json.loads((CAMP/'state.json').read_text());assert R.name not in state['completed_stages'];state['completed_stages'].append(R.name)
    state.update(stage='soft_transport_conditions_verified_theory_continues',active_process=None,last_updated_unix=time.time());(CAMP/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<384*1024-16384
    assert sum(p.stat().st_size for p in CAMP.rglob('*') if p.is_file())<1024**3-16384
    put(R/'seal.json',{'status':'AUDITED_COMPLETE_MATHEMATICAL_ONLY','unix':time.time(),'files':{str(p.relative_to(R)):ident(p) for p in sorted(R.rglob('*')) if p.is_file()}})
    print('MATHEMATICAL_TRANSPORT_CHAIN_VERIFIED_NO_DEPLOYMENT',flush=True)
if __name__=='__main__':main()
