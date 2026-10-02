"""Documentation only, after successful independent identity audit."""
import os
os.sched_setaffinity(0,{14})
import hashlib,json,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[3];CAMPAIGN=R.parents[1]
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def write_new(p,text):
    with Path(p).open('x') as f:f.write(text)
def main():
    audit=json.loads((R/'reviews/independent_audit.json').read_text());assert audit['status']=='PASS'
    cost=json.loads((R/'results/cost_summary.json').read_text());hybrid=json.loads((R.parent/'demand_qgt_full_build_v1/results/cost_summary.json').read_text())
    comparisons={};rows=[];detail=[]
    for ds,label in [('webvid2_5m_light_v1','WebVid'),('yandex_t2i_official10M_ip_v1','Yandex')]:
        a=cost['datasets'][ds];b=hybrid['datasets'][ds];dc=a['complete_build_wall_seconds'];hc=b['complete_build_wall_seconds'];saved=1-hc/dc
        comparisons[ds]={'default_build_seconds':dc,'hybrid_build_seconds':hc,'hybrid_fraction_of_default':hc/dc,'descriptive_wall_reduction_fraction':saved,'saved_build_seconds':dc-hc}
        rows.append(f'| {label} | {dc:.6f} | {hc:.6f} | {100*saved:.3f}% |')
        detail.append(f'- {label}：QGT精确{a["qgt_computed_queries"]}条，fit精确20000条；QGT搜索{a["qgt_search_seconds"]:.6f}秒，fit搜索{a["fit20000_search_seconds"]:.6f}秒，载入及Flat构建{a["base_load_flat_seconds"]:.6f}秒。')
    w=comparisons['webvid2_5m_light_v1'];y=comparisons['yandex_t2i_official10M_ip_v1']
    report='''# 默认与混合同时采用按需QGT的完整构建费用

2026-09-30，独立核验通过，默认保持Web GT10-soft-t1／Yandex GT10-hard、生产E99。补齐了记录148缺少的公平参照：按需QGT适用于原默认，低标签候选只比较除此之外的监督和构建费用。

| 数据集 | 原默认＋按需QGT完整wall (s) | 冻结混合＋按需QGT完整wall (s) | 本次描述性wall减少 |
|---|---:|---:|---:|
'''+ '\n'.join(rows)+'''

混合数据来自本日已核验记录148，默认是本次新增完整重建。两者从没有缓存目标标签的输入开始，保留原公共底图和嵌入；都包含base／索引载入、精确标签、H选择、画像、路由图、输出以及子进程启动与轮询。混合额外包含近似教师；默认不需要近似教师。工具准备、底图原始构建、嵌入／下载和事后审计均不在该核心wall内。

这是同机同日、操作系统缓存未清除的单次完整作业比较，执行顺序未随机化。上述比例是测量描述，不能称冷缓存结果、重复试验统计显著加速或相同CPU数的线上QPS。精确标签和画像使用CPU0–7、库池8，混合近似教师使用CPU15单线程；资源构成已计入实际串行wall。

## 默认身份与输入依赖

构建器只接收base、公共底图身份、原QGT query、fit query、H数量与soft/hard规则；未读取旧GT、温度、W或图。Web温度从新算的完整20K精确GT1按原float32分数、batch4096中位差重新计算；Y保持hard。H选择原算法通过已核验的惰性标签接口执行，新增标签如下：

'''+ '\n'.join(detail)+f'''

两集fit20K全部GT100 ID及距离bits恢复记录135；新QGT数据／消费轨迹／cluster计划恢复记录148；默认H和W逐位相同，小图全部节点／层／边语义相同。原生小图审计使用两集各256 query新旧配对，入口、距离bits和NDC恢复。Web QGT未用尾部相对旧5000批的差异仍沿记录148原披露，本次没有把“与按需版一致”改写成所有旧QGT bits一致。

独立Python核验{audit['seconds']:.6f}秒，检查{audit['identities']}项身份；新增精确GT共{cost['new_exact_GT']}条、审计ANN {cost['new_audit_ANN']}次、2次画像／2次图／2次QGT聚类，0新NSG、0新线上性能。原默认得到身份恢复，不产生新Recall或QPS点。

## 方法判断

共享QGT优化计入默认后，低标签混合仍有完整构建费用优势。但其质量边界不变：记录151两批新源共8192 query/集，混合相对默认R1/R100均值Web−0.073242/−0.022949pp、Y−0.097656/−0.023193pp，Y跨批不一致，完整QPS没有稳定提升。因此保留“费用—质量取舍候选”，不宣布无损替代或默认切换。

下一步仅复核记录153简单Energy控制在无旧精确温度条件下是否仍优于同预算Uniform及打乱监督。复杂LOO原门失败保持；不因费用优势回改质量结果、温度或新源数据角色。

证据：[协议](protocol.md)、[成本](results/cost_summary.json)、[比较](results/comparison.json)、[独立核验](reviews/independent_audit.json)、[完整作业](reviews/run_complete.json)。
'''
    write_new(R/'report.md',report);write_new(R/'results/comparison.json',json.dumps({'status':'AUDITED_DESCRIPTIVE_FULL_COST_COMPARISON','datasets':comparisons,'randomized_repeated_timing':False,'default_changed':False},indent=2)+'\n')
    card=f'''# 154 共享按需QGT后的公平默认构建费用

2026-09-30，完整重建／独立身份审计通过。原默认同样采用记录148的按需QGT，完整wall Web {w['default_build_seconds']:.6f}秒、Y {y['default_build_seconds']:.6f}秒；冻结混合114.023233/243.072318秒，描述性减少{100*w['descriptive_wall_reduction_fraction']:.3f}%/{100*y['descriptive_wall_reduction_fraction']:.3f}%。同机同日单次、未清缓存、非随机重复，不称冷缓存或统计显著加速。

从无GT／温度／W输入重算；全20K精确ID／距离bits、H／W与原默认恢复，小图语义和两集512原生新旧query配对一致。GT {cost['new_exact_GT']}、审计ANN {cost['new_audit_ANN']}、2W／2图／2聚类，0新NSG／线上性能。Web QGT旧尾部浮点差沿148披露，未掩盖。

共享工程优化不是混合独占，扣除此项仍有费用优势；记录151的小幅质量损失和Y跨批异质性保持，默认不变。后继简单Energy须先去掉旧精确温度依赖。

证据：[完整报告](../{R.relative_to(ROOT)}/report.md)、[成本](../{R.relative_to(ROOT)}/results/cost_summary.json)、[审计](../{R.relative_to(ROOT)}/reviews/independent_audit.json)。
'''
    write_new(ROOT/'experiment_history/154_fair_default_demand_build_cost.md',card)
    saved=R/'reviews/root_docs_before';saved.mkdir()
    for name in ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:
        dest=saved/name;dest.parent.mkdir(exist_ok=True);shutil.copy2(ROOT/name,dest)
    p=ROOT/'summary.md';s=p.read_text();old=next(line for line in s.splitlines() if line.startswith('[148按需QGT完整构建]'))
    new=f'[154公平默认构建](experiment_history/154_fair_default_demand_build_cost.md)已补齐共享优化参照：原默认同享按需QGT后，完整wall {w["default_build_seconds"]:.3f}／{y["default_build_seconds"]:.3f}秒；[148冻结混合](experiment_history/148_demand_qgt_full_build_cost.md)114.023／243.072秒，单次描述性减少{100*w["descriptive_wall_reduction_fraction"]:.2f}%／{100*y["descriptive_wall_reduction_fraction"]:.2f}%。两边H/W/图身份核验，均从无标签输入开始；未清缓存、非随机重复，不称统计显著或冷缓存加速。费用优势仍成立，质量取舍不变。[150](experiment_history/150_temperature_candidates_full_build.md)CDF完整121.432秒、简单控制增量3.007秒保留。'
    p.write_text(s.replace(old,new,1))
    p=ROOT/'spec.md';s=p.read_text();line=f'2026-09-30新增[原默认按需QGT构建器]({R.relative_to(ROOT)}/protocol.md)：只消费base／QGT query／fit query与原H、soft/hard规则，惰性QGT共1636条及全fit40K精确标签；Web从新GT1重算温度。两集原H/W逐位恢复、路由图语义和原生入口／NDC一致，完整串行wall含加载／输出／启动。该接口与148共享QGT优化，不能把其费用收益归混合独占；审计费用另计。\n\n'
    p.write_text(s.replace('# ACSG 代码架构与实现契约\n\n','# ACSG 代码架构与实现契约\n\n'+line,1))
    p=ROOT/'s-target.md';s=p.read_text();s=s.replace('记录141–153已完成。','记录141–154已完成。',1)
    s=s.replace('下一步先让原默认同样采用按需QGT，补公平构建费用参照。','[154](experiment_history/154_fair_default_demand_build_cost.md)已让原默认同享按需QGT并恢复原身份，公平完整费用参照已补齐；下一步运行已冻结的无旧温度Energy诊断。',1)
    p.write_text(s)
    p=ROOT/'s-experiment.md';s=p.read_text();mark='| [153 方向收益选样与简单控制]';idx=s.index(mark)
    s=s[:idx]+f'| [154 公平默认按需构建](experiment_history/154_fair_default_demand_build_cost.md) | 默认完整{w["default_build_seconds"]:.3f}/{y["default_build_seconds"]:.3f}秒，同享QGT后混合仍省{100*w["descriptive_wall_reduction_fraction"]:.2f}%/{100*y["descriptive_wall_reduction_fraction"]:.2f}%；单次描述、身份恢复、0新性能 |\n'+s[idx:];p.write_text(s)
    p=ROOT/'experiment_history/README.md';s=p.read_text();at=s.index('2026-09-30理论研究进行中：')
    s=s[:at]+f'2026-09-30最新[154 公平默认构建](154_fair_default_demand_build_cost.md)已补同享按需QGT的参照，默认完整{w["default_build_seconds"]:.3f}/{y["default_build_seconds"]:.3f}秒、身份恢复；混合仍有描述性费用优势，质量取舍与默认不变。下一步无旧温度Energy诊断。\n\n'+s[at:]
    s=s.replace('下一步补同享按需QGT的默认费用参照。','该参照现已由154补齐。',1);p.write_text(s)
    p=CAMPAIGN/'state.json';state=json.loads(p.read_text());assert 'default_demand_full_build_v1' not in state['completed_stages']
    state['completed_stages'].append('default_demand_full_build_v1');state['new_exact_GT_queries']+=cost['new_exact_GT'];state['new_ANN_calls']+=cost['new_audit_ANN']
    for dst,src in [('new_profiles','new_profiles'),('new_graphs','new_graphs'),('new_qgt_kmeans_fits','new_qgt_kmeans_fits')]:state[dst]+=cost[src]
    state.update(stage='fair_default_cost_audited_energy_clean_prepared',active_process=None,last_updated_unix=time.time());p.write_text(json.dumps(state,indent=2)+'\n')
    write_new(R/'results/decision.json',json.dumps({'status':'FAIR_DEFAULT_BUILD_COST_AUDITED_NO_DEFAULT_CHANGE','default_changed':False,'new_online_performance':False},indent=2)+'\n')
    files={str(p.relative_to(R)):ident(p) for p in R.rglob('*') if p.is_file() and p.name!='seal.json'}
    write_new(R/'reviews/seal.json',json.dumps({'status':'AUDITED_COMPLETE','unix':time.time(),'files':files},indent=2)+'\n')
    print('CLOSED154',comparisons,flush=True)
if __name__=='__main__':main()
