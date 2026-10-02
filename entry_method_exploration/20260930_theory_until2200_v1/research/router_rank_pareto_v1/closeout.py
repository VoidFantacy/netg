import csv,hashlib,io,json,os,time,zipfile
from pathlib import Path
os.sched_setaffinity(0,{14})
R=Path(__file__).resolve().parent;CAMP=R.parents[1];ROOT=R.parents[3]

def read(p):return json.loads(Path(p).read_text())
def put(p,x):
    with Path(p).open('x') as f:f.write(x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def short(ds):return 'WebVid' if ds.startswith('web') else 'Yandex'
def interval(a):return '['+', '.join(f'{v:+.6f}' for v in a)+']'

def main():
    a=read(R/'results/analysis.json');audit=read(R/'reviews/independent_audit.json');jobs=read(R/'reviews/jobs_complete.json')
    assert audit['status']=='PASS' and jobs['status']=='PASS'
    for f in ['controller_exit.json','analyze_exit.json','audit_exit.json']:assert read(R/'reviews'/f)['exit_code']==0
    assert (jobs['new_NSG'],jobs['new_ANN'])==(594688,610816)
    assert all(v['exit_code']==0 and v['max_threads']==1 and v['stopped'] is None for v in jobs['jobs'])
    main_rows=[];full=[];controls=[];actions=[];fits=[];export=[];oracle=[];csvrows=[]
    for ds,d in a['datasets'].items():
        fm=read(R/'models'/ds/'fit_metrics.json')
        for k,p in d['points'].items():
            b=p['methods']['Default'];s=p['methods']['StatePareto'];label=f'{short(ds)} R{k}/L{p["L"]}'
            assert s['delta_recall_pp']<0
            main_rows.append(f'| {label} | {b["recall_pct"]:.6f}% / {b["qps_pooled"]:.3f} | {s["recall_pct"]:.6f}% / {s["qps_pooled"]:.3f} | {s["delta_recall_pp"]:+.6f} {interval(s["delta_recall_95pct_descriptive_interval_pp"])} | {s["delta_qps_pooled_pct"]:+.4f}% |')
            for name,m in p['methods'].items():
                full.append(f'| {label} | {name} | {m["recall_pct"]:.6f} | {m["delta_recall_pp"]:+.6f} | {interval(m["delta_recall_95pct_descriptive_interval_pp"])} | {m["qps_pooled"]:.3f} | '+', '.join(f'{v:.3f}' for v in m['qps_each'])+' |')
                csvrows.append(dict(dataset=ds,K=p['K'],L=p['L'],method=name,recall_pct=m['recall_pct'],delta_recall_pp=m['delta_recall_pp'],interval_lo_pp=m['delta_recall_95pct_descriptive_interval_pp'][0],interval_hi_pp=m['delta_recall_95pct_descriptive_interval_pp'][1],QPS=m['qps_pooled'],delta_QPS_pct=m['delta_qps_pooled_pct'],seconds0=m['seconds'][0],seconds1=m['seconds'][1],seconds2=m['seconds'][2],rescued_queries=m['rescued_queries'],damaged_queries=m['damaged_queries'],rescued_hits=m['rescued_hits'],damaged_hits=m['damaged_hits']))
            for name,c in p['State_vs_controls'].items():
                controls.append(f'| {label} | {name} | {c["State_minus_control_recall_pp"]:+.6f} {interval(c["State_minus_control_recall_interval_pp"])} | {c["State_relative_pooled_QPS_pct"]:+.4f}% |')
            actions.append(f'| {label} | '+ ' / '.join(map(str,s['actions']))+f' | {s["rescued_queries"]} / {s["damaged_queries"]} | {s["rescued_hits"]} / {s["damaged_hits"]} |')
            train=[x for x in fm if x['K']==p['K'] and x['method']=='StatePareto' and x['role']=='train']
            outer=[x for x in fm if x['K']==p['K'] and x['method']=='StatePareto' and x['role']=='outer']
            fits.append(f'| {label} | '+', '.join(f'{x["delta_recall_pp"]:+.6f}' for x in train)+' | '+', '.join(f'{x["delta_recall_pp"]:+.6f}' for x in outer)+' |')
            g=p['gate_forced_default'];oracle.append(f'{label}：+{p["four_action_oracle_gain_pp"]:.6f}pp')
            export.append(f'| {label} | {g["delta_pooled_QPS_pct"]:+.4f}% | {g["extra_us_per_query"]:+.6f} | {p["methods"]["ForcedDefault"]["delta_qps_pooled_pct"]:+.4f}% |')
    title='| 数据集/工作点 | Default Recall / QPS | StatePareto Recall / QPS | ΔRecall pp及95%描述区间 | ΔQPS |\n|---|---:|---:|---|---:|\n'
    table=title+'\n'.join(main_rows)+'\n'
    conclusion='本固定状态/rank版本没有形成稳定的Recall–QPS综合改善，停止继续调状态、trace、支持阈值、深度、L、样本或seed。默认仍为Web GT10-soft-t1、Yandex GT10-hard与生产E99。'
    report='''# 状态到相对rank：完整在线验证未形成综合提升

2026-09-30，原生测量、统计与独立实现核验全部完成。**'''+conclusion+'''

## 主要结果

两集各4096条历史曝光开发query，原四折3072拟合/1024外折。每K独立规则，固定原base、图、主搜索及L。完整wall包含原路由、实际模型推理、入口选择、主搜索和输出，CPU15实际单线程、方法串行、各三重复。QPS为3N/三次wall总和。

'''+table+'''
四点召回均值都为负；两K1区间跨零，不能写成已证明总体有害。两K100配对描述区间均低于零，同时QPS均值小幅上升，是实测质量/速度取舍，未证明相同Recall下更快。所有已曝光query、重叠训练折与单次四折选择使区间仅供描述，不能当独立确认。三次wall不构成总体QPS置信区间。

## 同监督控制与完整三轮

GlobalPareto、ShufflePareto、FeaturePareto和StatePareto使用相同四动作、角色与经验召回约束；Feature采用原六特征、深度2/min-leaf512。Global在Web两点和Y K100全部返回默认动作，Y K1两折rank1、两折默认。ForcedDefault确实导出状态、查表并保持原三入口。相同动作仍有代码路径及测量波动，不能把其QPS差冒充决策质量收益。

| 工作点 | 方法 | Recall % | ΔRecall pp | 95%描述区间 pp | pooled QPS | 三次实际QPS |
|---|---|---:|---:|---|---:|---|
'''+ '\n'.join(full)+'''

| 工作点 | 控制 | State减控制 ΔRecall pp及区间 | State相对QPS |
|---|---|---|---:|
'''+ '\n'.join(controls)+'''

State没有在任何点得到超过打乱状态控制的正召回均值。Y K1相对六特征有+0.146484pp局部均值，但区间跨零且速度略低；不能由此说状态一般无信息，也不能当可部署增益。Y K100强制默认的QPS还高于State且返回召回不变，说明不足1%的速度差尤其需要谨慎归因。

## 救回、损伤与经验约束的外折失效

| 工作点 | 动作0/1/2/3查询数 | 净召回提高/降低query | 增加/损失命中数 |
|---|---|---:|---:|
'''+ '\n'.join(actions)+'''

K100最后两列按每query命中数的正负净差计；不是返回成员集合的全部新增/移除ID。所有原始返回均保留，未混淆净命中与真实成员变动。

| 工作点 | 四折训练ΔRecall pp | 四折外折ΔRecall pp |
|---|---|---|
'''+ '\n'.join(fits)+'''

训练经验约束使每格选择后训练总命中不降且代理时间下降，但没有把这个性质传到外折。两集K100四个外折分别均为负。Web51/Y52个状态格内的稀疏增损与多格动作选择是可解释的泛化风险；本结果不识别唯一失败原因。逐query标签时间仅是拟合代理，不拿其加总替代真实策略wall。

四动作事后oracle仍为：'''+ '；'.join(oracle)+'''。它说明这四动作存在逐query差异，不是可部署收益，也不证明原状态能够预测。Web此前256-query诊断的K1零余量不能推广到全部4096；本轮完整余量已明确纠正这一外推风险。

## 状态导出费用及实现核验

| 工作点 | 独立gate强制默认ΔQPS | gate额外微秒/query | 最终wall强制默认ΔQPS |
|---|---:|---:|---:|
'''+ '\n'.join(export)+'''

导出gate与最终wall均全返回逐位相同，小幅费用差在轮次间变化；状态导出不能被宣称严格零费用，也没有证据把此次全部损伤归因于导出费用。

两集各4096条原/观察接口heap ID、distance bits、NDC、状态、旧rank及六特征恢复；各动作/K固定16条plain/count/E99的ID、距离与NDC一致。全部标签重复输出一致、全部完整wall在线动作匹配冻结OOF规则、返回逐位等于所选动作记录。独立实现对65536行返回逐项集合评分，重算全部64份规则及树的全部候选分裂；恢复19456条历史返回向量，并用整数权重bootstrap恢复全部区间，最大误差0。原源/模型/消费文件保持身份。独立实现由同一agent完成，不冒充独立人员；共享quantile原语如实记录。

## 成本、边界及原始材料

'''+f'''六个原生作业（含各自加载/输出）共{jobs['search_job_seconds']:.6f}秒，编译{read(R/'reviews/build.json')['seconds']:.6f}秒，拟合{read(R/'reviews/fit_job.json')['seconds']:.6f}秒，分析{read(R/'reviews/analyze_exit.json')['seconds']:.6f}秒，独立核验{read(R/'reviews/audit_exit.json')['seconds']:.6f}秒。上述作业费用不是查询QPS。新增594688次NSG、610816次ANN，0新GT/画像/图；64份规则属OOF开发模型，不是一个部署模型。最高观测RSS {max(j['max_observed_rss'] for j in jobs['jobs'])/2**30:.3f}GiB；两集原生getrusage峰值另在complete.json保存。测量结束阶段产物{jobs['stage_bytes']}字节，未删旧产物。

'''+conclusion+''' 今天仍继续理论研究至22:00；后继须有不同的信息来源和独立协议，不能把此版本增加状态细分后重新命名。构建成本属于附属结果，主目标仍是完整在线收益。

[冻结协议](protocol.md) · [理论](theory.md) · [全部统计](results/analysis.json) · [便于复查的CSV](results/metrics.csv) · [原生作业](reviews/jobs_complete.json) · [独立核验](reviews/independent_audit.json) · [新前作核对](../online_prior_work_2026.md)。
'''
    names=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']
    old={n:(ROOT/n).read_text() for n in names}
    with zipfile.ZipFile(R/'reviews/root_docs_before_closeout.zip','x',zipfile.ZIP_DEFLATED) as z:
        for n in names:z.write(ROOT/n,n)
        z.write(CAMP/'state.json','campaign_state.json')
    with zipfile.ZipFile(R/'reviews/root_docs_before_closeout.zip') as z:assert z.testzip() is None
    put(R/'report.md',report)
    out=io.StringIO();w=csv.DictWriter(out,fieldnames=list(csvrows[0]));w.writeheader();w.writerows(csvrows);put(R/'results/metrics.csv',out.getvalue())
    status='STOP_ROUTER_RANK_PARETO_V1'
    put(R/'decision.json',{'status':status,'default_changed':False,'four_point_recall_means_negative':True,'K100_descriptive_intervals_negative_both_datasets':True,'K1_intervals_cross_zero':True,'historical_development_only':True,'joint_improvement_not_demonstrated':True,'stop_scope':'This fixed state-to-relative-rank version; no trace/state/depth/support/L/seed/sample extension','audit':'PASS','continuing_until':'2026-09-30T22:00:00+08:00'})
    rel='entry_method_exploration/20260930_theory_until2200_v1/research/router_rank_pareto_v1'
    card='''# 164 目标预算的状态到查询相对rank表

2026-09-30完成六方法四工作点、三次完整wall及独立核验，状态`STOP_ROUTER_RANK_PARETO_V1`。默认与生产E99不变。

E121按状态输出全H中的固定真实ID；本版按状态输出当前query实际rank1/2/3或默认三入口，两类规则不包含对方。两集E118历史fit4096、原四折3072/1024，目标L为Web1000/1250、Y128/256；每格经验召回不降条件下选最快动作，默认优先。State与全局、训练状态置换、原六特征浅树同监督；所有冻结规则均测完整wall，不按质量删点。

'''+table+'''
两K1均值为负但描述区间跨零；两K100召回区间负且QPS略升，未证明相同Recall更快。State四点召回均未超过置换控制；停止本固定版本的状态/trace/阈值/深度/L/样本/seed扩展。训练经验非降不是外折无损证书，不能把oracle余量当可迁移信息。

全路由、原生核、旧rank/六特征逐位一致；全部在线规则/返回恢复。65536返回行独立集合评分、64规则/所有树分裂复算、19456历史向量恢复、整数bootstrap区间误差0。独立实现为同一agent，非独立人员。594688 NSG、610816 ANN、0新GT/画像/图，原生作业1017.597秒（含加载），查询QPS单独计。全部query历史曝光；四折模型切换不是最终单模型部署，三次wall不构成总体速度区间。

'''+f'[完整报告](../{rel}/report.md) · [冻结协议](../{rel}/protocol.md) · [全部统计](../{rel}/results/analysis.json) · [独立核验](../{rel}/reviews/independent_audit.json)。\n'
    put(ROOT/'experiment_history/164_router_rank_pareto_online.md',card)
    end=old['summary.md'].index('用户于2026-09-30 17:44明确')
    summary='# ACSG 当前结果摘要\n\n'+f'[164状态/rank完整在线验证](experiment_history/164_router_rank_pareto_online.md)已核验。**{conclusion}**\n\n'+table+'\n两K1区间跨零、两K100区间负；K100轻微提速伴随召回下降，未证明相同Recall更快。State四点召回均未超过置换控制。完整在线/原生/64规则与全部统计复算通过；历史开发数据和OOF模型切换不冒充独立确认。\n\n'+old['summary.md'][end:]
    (ROOT/'summary.md').write_text(summary)
    specadd=f'''[状态/rank在线工具]({rel}/protocol.md)已实现并核验：沿E121原生观察接口导出上层状态，完整原路由返回后按(distance,real-ID)确定相对rank；四动作使用原三入口或对应单入口，不改底图/主核/L。四折同监督状态表/全局/训练置换/六特征浅树一次拟合并冻结，原生wall真正执行推理，所有动作及返回匹配保存的逐动作响应。标签插桩费用与完整wall分离，K1/K100各自真实K；CPU15实际1线程串行。独立集合评分/规则/树全部分裂/整数bootstrap及历史响应回归完成。工具输出原始标签ID/距离、规则、动作、timings与统计；未接入生产。改变原图内部ID、H、rank/tie、query/GT/K/L或主核时不得复用状态表与响应。\n\n'''
    (ROOT/'spec.md').write_text(old['spec.md'].replace('# ACSG 代码架构与实现契约\n\n','# ACSG 代码架构与实现契约\n\n'+specadd,1))
    target=old['s-target.md'].replace('已完成记录141–163保留','已完成记录141–164保留',1)
    lo=target.index('E117的六关系特征');hi=target.index('## 优先二：')
    target=target[:lo]+f'''[164状态到相对rank版本](experiment_history/164_router_rank_pareto_online.md)已结束并通过实现审计：四点Recall均值负、两个K100描述区间负，State未形成相对固定/置换/六特征的稳定综合增量。按冻结协议停止本版，不增状态/trace/支持阈值/深度/L/样本/seed继续调。它关闭E126原目标预算/完整wall缺口，不支持默认替换，也不证明所有入口信息都无用。\n\n接下来先核对[查询结果复用等2026年前作](entry_method_exploration/20260930_theory_until2200_v1/research/online_prior_work_2026.md)与内部原协议/源码：廉价信息是否受固定H或画像聚合限制，是否存在真实不同的可迁移信息来源。查询—目标实例对应目前只是理论问题，尚未冻结或启动实验；不能以已有查询缓存思想重新命名为创新。\n\n'''+target[hi:]
    target=target.replace('当前唯一性能runner为状态/rank版本，按协议串行执行。','状态/rank版本已全部结束，当前无性能runner运行。')
    (ROOT/'s-target.md').write_text(target)
    marker='## 最新记录\n\n| 记录 | 内容与边界 |\n|---|---|\n';assert marker in old['s-experiment.md']
    (ROOT/'s-experiment.md').write_text(old['s-experiment.md'].replace(marker,marker+'| [164 状态/rank完整在线验证](experiment_history/164_router_rank_pareto_online.md) | 四点Recall均值负、K100小幅提速但质量损失；独立核验完成，停止本固定版本，默认不变 |\n',1))
    (ROOT/'experiment_history/README.md').write_text(old['experiment_history/README.md'].replace('# ACSG 历史实验详细复盘\n\n','# ACSG 历史实验详细复盘\n\n2026-09-30最新[164状态/rank完整在线验证](164_router_rank_pareto_online.md)完成并独立核验；四点召回均值负、未形成稳定综合增量，停止本固定版本。\n\n',1))
    state=read(CAMP/'state.json');assert R.name not in state['completed_stages'];assert state['active_process'] is None
    assert state['new_NSG_calls']==2444480 and state['new_ANN_calls']==2258432
    state['completed_stages'].append(R.name);state['small_rules_router_rank']=64
    state.update(stage=status.lower(),last_updated_unix=time.time());(CAMP/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    files={str(p.relative_to(R)):ident(p) for p in sorted(R.rglob('*')) if p.is_file() and p.name!='seal.json'}
    put(R/'reviews/seal.json',{'status':'AUDITED_COMPLETE_NO_DEFAULT_CHANGE','unix':time.time(),'files':files,'default_changed':False})
    print(status,flush=True)

if __name__=='__main__':main()
