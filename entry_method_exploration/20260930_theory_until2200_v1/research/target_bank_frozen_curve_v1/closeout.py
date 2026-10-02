import hashlib,json,time,zipfile
from pathlib import Path
R=Path(__file__).resolve().parent;CAMP=R.parents[1];ROOT=R.parents[3]
def read(p):return json.loads(Path(p).read_text())
def put(p,x):
    with Path(p).open('x') as f:f.write(x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def iv(v):return '['+', '.join(f'{x:+.6f}' for x in v)+']'
def short(ds):return 'WebVid' if ds.startswith('web') else 'Yandex'
def main():
    a=read(R/'results/analysis.json');audit=read(R/'reviews/independent_audit.json');jobs=read(R/'reviews/jobs_complete.json')
    assert audit['status']==jobs['status']=='PASS' and audit['complete_return_rows']==147456
    for name in ['controller_exit.json','analyze_exit.json','audit_exit.json']:assert read(R/'reviews'/name)['exit_code']==0
    assert jobs['new_NSG']==596160 and jobs['new_ANN']==595584 and jobs['new_graphs']==0
    assert all(j['exit_code']==0 and j['max_threads']==1 and j['stopped'] is None for j in jobs['jobs'])
    assert sum(x['empirical_dominates'] for d in a['datasets'].values() for x in d['all_TargetBank_cross_budget_comparisons'])==0
    mainrows=[];thresholdrows=[]
    for ds,d in a['datasets'].items():
        for p in d['points'].values():
            b=p['methods']['Default3'];m=p['methods']['TargetBank1'];v=m['vs_Default3'];assert v['delta_QPS_pct']<0
            mainrows.append(f'| {short(ds)} R{p["K"]}/L{p["L"]} | {b["recall_pct"]:.6f} / {b["qps_pooled"]:.3f} | {m["recall_pct"]:.6f} / {m["qps_pooled"]:.3f} | {v["delta_recall_pp"]:+.6f} {iv(v["descriptive_interval_pp"])} | {v["delta_QPS_pct"]:+.4f}% |')
        for K,ms in d['fastest_measured_R90'].items():
            b=ms['Default3'];m=ms['TargetBank1'];assert b['L']==m['L']
            thresholdrows.append(f'| {short(ds)} R{K} | {b["L"]} | {b["recall_pct"]:.6f}% / {b["qps_pooled"]:.3f} | {m["recall_pct"]:.6f}% / {m["qps_pooled"]:.3f} |')
    table='| 工作点 | 默认Recall % / QPS | TargetBank Recall % / QPS | ΔRecall pp及95%描述区间 | ΔQPS |\n|---|---:|---:|---|---:|\n'+'\n'.join(mainrows)+'\n'
    threshold='| 组合 | 各自最快实测R90的L | 默认实际Recall / QPS | TargetBank实际Recall / QPS |\n|---|---:|---:|---:|\n'+'\n'.join(thresholdrows)+'\n'
    conclusion='冻结目标库保留WebVid R1的质量/速度取舍，尚无已测点的稳定Recall–QPS综合改善；结束本次有限曲线核验，不扩网格、ef、样本或重复。默认保持Web GT10-soft-t1、Yandex GT10-hard与生产E99。'
    report='''# 冻结目标库曲线：Web R1质量收益保留，综合改进未获证实

2026-09-30完成全部36点、108轮完整wall及独立核验。**'''+conclusion+'''

## 实际结果

固定165原物理目标图、slot映射和ef10；没有重新拟合或构图。三方法为原GT10三入口、完整原路由后仅rank1、相同20K物理目标slot的TargetBank单入口。每个原工作点仅取E105旧网格的前邻/原点/后邻，一次事前固定。两集各4096条历史E105开发query，未使用今日151/157新源或held-out；中心点与165相同查询/返回，不是新独立质量复验。

'''+table+'''
Web R1三个预算的Recall差均值为+0.659180、+0.537109、+0.390625pp，前两个95%描述区间为正，第三个下界为0；对应救回/损伤为63/36、50/28、42/26。三个点都稍慢，因此保留可信的局部质量/速度取舍，而不将其写成方法无信息或已经获得同Recall加速。

Web R100三点接近但均值微负；Y R1三点分别正、零、负，区间均跨零；Y R100三点均值负、区间跨零。不能把区间跨零称为等效或已证明无损。TargetBank全部12个同预算点pooled QPS均低于Default3，约−0.479%至−3.424%。三次完整wall均保留，未删去Y K1/L128较慢的一轮。

预定72项TargetBank与Default3/DefaultRank1的跨预算比较全部完成，没有一项同时满足Recall均值不低与pooled QPS更高。此结论仅针对已测点；网格稀疏，不能据此否定连续预算下的一切可能收益。另一方面，也不能把图中连线或插值当成新的实测优势。

## 唯一预定90%阈值

'''+threshold+'''
三方法在四组合中选中的L均为原中心点。Web TargetBank L800的实际R1为89.843750%，未达到90%；不能四舍五入成达标或事后改阈值。上述实际Recall不同，因此只是同阈值最快实测点比较，不是完全相同Recall。DefaultRank1在Web R100仍有很小的正均值组合，原始区间和全部轮次见完整表；不将它归功于目标库。

![全部冻结点](figures/curves.png)

竖向误差线是三轮QPS范围，非总体速度置信区间；连接线只引导读图。全部36点及72比较、成员增损、原始wall/路由与主图NDC见[完整表](results/tables.md)和[全部CSV](results/metrics.csv)。PDF图见[独立文件](figures/curves.pdf)。

## 机制和证据限制

目标库路由NDC固定为Web234.444/Y304.942；其主图NDC在所有点均低于原默认，但总NDC更高。主图节省只有Web约14–23、Y约65–89次距离，无法在本实现中抵消更昂贵的目标路由。NDC仍不等于wall，精确的成本归因需要单独机制证据；本轮以完整wall为速度结论。

所有区间来自10000次query-paired bootstrap，同一数据集全部K/L共用query重采样，种子事前固定。历史曝光、多重比较、从网格后选最快达标点使它们只适合描述，不是新的盲测确认。不能按本次结果追加一个更有利的L或延长重复。构建成本不是当前优化重点，本轮甚至没有新模型；判断依据始终是完整线上Recall和QPS。

## 实现审计与成本

原生逐位检查全部20K目标向量，所有Default3点的E105五字段恢复；中心点三方法的165六字段恢复。每点16条plain/count/E99、三轮重复与完整count一致；相同L的K1首返回/距离和K100一致。独立集合实现重评分147456返回行，复算真实成员增损、所有72比较、90%选择、整数加权bootstrap；区间最大差0。源、模型、输入冻结hash保持。独立实现由同一agent完成，不冒充另一审查人员。

'''+f'''实际新增596160 NSG、595584 ANN，0新GT/图/画像。原生控制器两集作业{jobs['search_job_seconds']:.6f}秒，编译{jobs['compile_seconds']:.6f}秒；CPU15实际1线程、严格串行，最高观测RSS{max(j['max_observed_rss'] for j in jobs['jobs'])/2**30:.3f}GiB。搜索结束阶段{jobs['stage_bytes']}字节、全日{jobs['campaign_bytes']}字节，文档/图另计入最终封存。作业wall含加载和核验，不替代纯查询QPS。

'''+conclusion+'''

[事前协议](protocol.md) · [全统计](results/analysis.json) · [跨预算CSV](results/all_cross_budget_comparisons.csv) · [作业账](reviews/jobs_complete.json) · [独立核验](reviews/independent_audit.json) · [图表身份](reviews/render_identity.json)。
'''
    # Total NDC statement in the report is verified, not inferred from timing.
    assert all(p['methods']['TargetBank1']['total_NDC']>p['methods']['Default3']['total_NDC'] for d in a['datasets'].values() for p in d['points'].values())
    names=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md'];old={n:(ROOT/n).read_text() for n in names}
    with zipfile.ZipFile(R/'reviews/root_docs_before_closeout.zip','x',zipfile.ZIP_DEFLATED) as z:
        for n in names:z.write(ROOT/n,n)
        z.write(CAMP/'state.json','campaign_state.json')
    with zipfile.ZipFile(R/'reviews/root_docs_before_closeout.zip') as z:assert z.testzip() is None
    put(R/'report.md',report)
    status='COMPLETE_FROZEN_CURVE_RETAIN_WEB_R1_TRADEOFF';rel='entry_method_exploration/20260930_theory_until2200_v1/research/target_bank_frozen_curve_v1'
    put(R/'decision.json',{'status':status,'default_changed':False,'TargetBank_empirical_dominance_count':0,'cross_budget_comparisons':72,'TargetBank_same_L_QPS_negative_points':12,'retain':'Web R1 three L quality/speed tradeoff, historical development only','no_same_Recall_speed_claim':True,'no_interpolation':True,'stop_scope':'fixed target-bank curve; no extra L/ef/sample/repetitions or model tuning','audit':'PASS'})
    card='''# 166 冻结目标库的相邻预算曲线

2026-09-30完成。`COMPLETE_FROZEN_CURVE_RETAIN_WEB_R1_TRADEOFF`；默认与E99保持。165的查询样本迁移仍停止。本项只核对简单TargetBank控制的质量余量能否形成完整线上收益。

原20K物理目标图、映射/ef10不变，原三入口/完整原路由后rank1/目标单入口三方法；每个原点及E105旧网格前后邻一次固定，共36点/108轮wall。E105历史4096条/集，真实K1/K100、CPU15实际1线程、串行。0新GT、训练、图或held-out访问。

'''+threshold+'''
Web R1在L800/1000/1250相对默认分别+0.659180/+0.537109/+0.390625pp，QPS−1.8363/−0.9620/−1.0204%；前两描述区间正、第三下界0，保留局部质量/速度取舍。Web R100微负近似持平；Y无稳定质量优势。目标库12个同预算点都更慢，全部72个预定跨预算比较无经验支配点，四组合最快实测90%点均未加速。网格稀疏，既不外推所有可能预算，也不靠插值称同Recall收益。

147456返回行独立评分、真实成员增损、72比较/R90选择/整数bootstrap通过，最大区间差0。全部原生、Default3历史回归、中心三方法165回归、图/输入/源码身份通过。新增596160 NSG/595584 ANN，作业1010.691秒、编译8.178秒。关闭有限曲线，不扩L/ef/样本/重复调到通过。

'''+f'[报告](../{rel}/report.md) · [协议](../{rel}/protocol.md) · [全部表](../{rel}/results/tables.md) · [统计](../{rel}/results/analysis.json) · [独立核验](../{rel}/reviews/independent_audit.json)。\n'
    put(ROOT/'experiment_history/166_target_bank_frozen_curve.md',card)
    i=old['summary.md'].index('[165查询→真实目标迁移]')
    (ROOT/'summary.md').write_text('# ACSG 当前结果摘要\n\n[166冻结目标库曲线](experiment_history/166_target_bank_frozen_curve.md)已完成36点/108轮完整wall与独立核验。**'+conclusion+'**\n\n'+threshold+'\nWeb R1三个预算的质量差+0.659180/+0.537109/+0.390625pp，QPS−1.8363/−0.9620/−1.0204%；保留局部取舍。12个同预算点目标库均更慢，72个跨预算比较无经验支配，未实测同Recall更快。历史4096开发query/稀疏网格，不外推全预算或独立确认。全部147456返回及统计复算通过。\n\n'+old['summary.md'][i:])
    lo=old['spec.md'].index('[冻结目标库曲线测量器]');hi=old['spec.md'].index('[查询→目标迁移工具]')
    spec=f'[冻结目标库曲线测量器]({rel}/protocol.md)已实现/完成核验：沿165原Kernel/Engine/Route与冻结TargetIndex，三方法在预锁6个K/L点运行完整wall。原生全20K目标bits、全部Default3历史回归、中心三方法165回归通过；模型不变。独立重评分147456返回、72跨预算比较、实际R90选择和整数bootstrap完成。图表只连接实测点，速度误差线为三轮范围，不作插值证据。无生产接口/参数变化；改变图/映射/K/L/数据或核使相应结果失效。\n\n'
    (ROOT/'spec.md').write_text(old['spec.md'][:lo]+spec+old['spec.md'][hi:])
    target=old['s-target.md'].replace('已完成记录141–165保留','已完成记录141–166保留',1)
    lo=target.index('目标侧Web R1取舍值得一次');hi=target.index('## 优先二：')
    target=target[:lo]+'''[166冻结曲线](experiment_history/166_target_bank_frozen_curve.md)已完成并核验：目标库Web R1三个L的正质量均值保留，但12个同预算点均更慢、72跨预算比较无经验支配；四组合最快实测90%点不加速。结束本项，不扩L/ef/样本/重复。原查询迁移不重开，默认不变。

继续完善线上效用条件，并评估一个尚未实现的[目标库粗筛访问机制](entry_method_exploration/20260930_theory_until2200_v1/research/target_bank_coarse_access_design.md)：原GT10路由筛目标桶，再做raw目标精排。训练桶大小已只读核算；粗细/监督分桶已有IVF及学习路由前作，不能包装成独立创新。尚无runner或性能结果，只有在访问费用与最小控制明确后另立冻结小实验。

'''+target[hi:]
    target=target.replace('冻结曲线准备完成，执行前新增80MiB预算至1360MiB（1.328125GiB）；此项编译≤120秒、搜索≤1800秒且20:30前停止，0构图/GT/训练。','冻结曲线已完成并封存，执行前新增80MiB预算至1360MiB（1.328125GiB）；此项0构图/GT/训练，无后台作业。')
    (ROOT/'s-target.md').write_text(target)
    marker='## 最新记录\n\n| 记录 | 内容与边界 |\n|---|---|\n';assert marker in old['s-experiment.md']
    (ROOT/'s-experiment.md').write_text(old['s-experiment.md'].replace(marker,marker+'| [166 冻结目标库曲线](experiment_history/166_target_bank_frozen_curve.md) | 36点/108轮wall；Web R1质量取舍保留，72跨预算比较无经验支配，有限核验结束 |\n',1))
    (ROOT/'experiment_history/README.md').write_text(old['experiment_history/README.md'].replace('# ACSG 历史实验详细复盘\n\n','# ACSG 历史实验详细复盘\n\n2026-09-30最新[166冻结目标库曲线](166_target_bank_frozen_curve.md)已独立核验；Web R1质量/速度取舍保留，尚无已测点综合改善。\n\n',1))
    state=read(CAMP/'state.json');assert state['active_process'] is None and R.name not in state['completed_stages']
    assert (state['new_NSG_calls'],state['new_ANN_calls'])==(3438080,3251072)
    state['completed_stages'].append(R.name);state.update(stage=status.lower(),last_updated_unix=time.time())
    (CAMP/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    files={str(p.relative_to(R)):ident(p) for p in sorted(R.rglob('*')) if p.is_file() and p.name!='seal.json'}
    assert sum(v['bytes'] for v in files.values())<80*2**20
    put(R/'reviews/seal.json',{'status':'AUDITED_COMPLETE_NO_DEFAULT_CHANGE','unix':time.time(),'files':files,'default_changed':False})
    print(status,len(files),flush=True)
if __name__=='__main__':main()
