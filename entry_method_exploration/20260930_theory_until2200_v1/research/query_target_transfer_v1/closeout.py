import csv,hashlib,io,json,time,zipfile
from pathlib import Path
R=Path(__file__).resolve().parent; CAMP=R.parents[1]; ROOT=R.parents[3]

def read(p):return json.loads(Path(p).read_text())
def put(p,x):
    with Path(p).open('x') as f:f.write(x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def short(ds):return 'WebVid' if ds.startswith('web') else 'Yandex'
def iv(v):return '['+', '.join(f'{x:+.6f}' for x in v)+']'

def main():
    a=read(R/'results/analysis.json');audit=read(R/'reviews/independent_audit.json');jobs=read(R/'reviews/jobs_complete.json')
    assert audit['status']=='PASS' and jobs['status']=='PASS' and read(R/'reviews/diagnostic_audit.json')['status']=='PASS'
    for name in ['controller_exit.json','analyze_exit.json','audit_exit.json','diagnostic_audit_exit.json']:assert read(R/'reviews'/name)['exit_code']==0
    assert (jobs['new_NSG'],jobs['new_ANN'])==(397440,397056)
    assert all(x['exit_code']==0 and x['max_threads']==1 and x['stopped'] is None for x in jobs['jobs'])
    mainrows=[];full=[];control=[];gain=[];geo=[];ndc=[];csvrows=[];bankrows=[]
    for ds,d in a['datasets'].items():
        for k,p in d['points'].items():
            label=f'{short(ds)} R{k}/L{p["L"]}';b=p['methods']['Default3'];m=p['methods']['QueryTarget1'];t=p['methods']['TargetBank1']
            assert m['delta_qps_pooled_pct']<0
            mainrows.append(f'| {label} | {b["recall_pct"]:.6f}% / {b["qps_pooled"]:.3f} | {m["recall_pct"]:.6f}% / {m["qps_pooled"]:.3f} | {m["delta_recall_pp"]:+.6f} {iv(m["delta_recall_95pct_descriptive_interval_pp"])} | {m["delta_qps_pooled_pct"]:+.4f}% |')
            bankrows.append(f'| {label} | {t["recall_pct"]:.6f}% / {t["qps_pooled"]:.3f} | {t["delta_recall_pp"]:+.6f} {iv(t["delta_recall_95pct_descriptive_interval_pp"])} | {t["delta_qps_pooled_pct"]:+.4f}% |')
            gain.append(f'| {label} | {m["rescued_queries"]} / {m["damaged_queries"]} | {m["net_positive_hits"]} / {m["net_negative_hits"]} | {m["true_member_added"]} / {m["true_member_lost"]} |')
            for name,v in p['methods'].items():
                full.append(f'| {label} | {name} | {v["recall_pct"]:.6f} | {v["delta_recall_pp"]:+.6f} {iv(v["delta_recall_95pct_descriptive_interval_pp"])} | {v["qps_pooled"]:.3f} | '+', '.join(f'{x:.3f}' for x in v['qps_each'])+' |')
                ndc.append(f'| {label} | {name} | {v["route_ndc_mean"]:.3f} | {v["graph_ndc_mean"]:.3f} | {v["total_ndc_mean"]:.3f} | {v["extra_us_per_query"]:+.3f} |')
                csvrows.append(dict(dataset=ds,K=p['K'],L=p['L'],method=name,Recall_pct=v['recall_pct'],delta_Recall_pp=v['delta_recall_pp'],CI_lo_pp=v['delta_recall_95pct_descriptive_interval_pp'][0],CI_hi_pp=v['delta_recall_95pct_descriptive_interval_pp'][1],QPS=v['qps_pooled'],delta_QPS_pct=v['delta_qps_pooled_pct'],seconds0=v['seconds'][0],seconds1=v['seconds'][1],seconds2=v['seconds'][2],rescued_queries=v['rescued_queries'],damaged_queries=v['damaged_queries'],net_positive_hits=v['net_positive_hits'],net_negative_hits=v['net_negative_hits'],true_member_added=v['true_member_added'],true_member_lost=v['true_member_lost'],route_NDC=v['route_ndc_mean'],graph_NDC=v['graph_ndc_mean']))
            for name,v in p['main_vs_controls'].items():
                control.append(f'| {label} | {name} | {v["main_minus_control_recall_pp"]:+.6f} {iv(v["interval_pp"])} | {v["main_relative_QPS_pct"]:+.4f}% |')
        for name,v in d['mechanism'].items():
            geo.append(f'| {short(ds)} | {name} | {v["max_raw_IP_entry_score_mean"]:.6f} | {v["entries_inside_H"]}/{v["valid_entries"]} | {v["unique_real_entries"]} |')
    table='| 工作点 | Default3 Recall / QPS | QueryTarget1 Recall / QPS | ΔRecall pp及95%描述区间 | ΔQPS |\n|---|---:|---:|---|---:|\n'+'\n'.join(mainrows)+'\n'
    banktable='| 工作点 | TargetBank1 Recall / QPS | 相对Default3 ΔRecall pp及区间 | ΔQPS |\n|---|---:|---|---:|\n'+'\n'.join(bankrows)+'\n'
    conclusion='直接查询→GT1迁移未形成相对默认的稳定Recall–QPS综合提高，停止本固定迁移版本；保留目标侧简单对照的Web R1质量/速度取舍。默认仍为Web GT10-soft-t1、Yandex GT10-hard与生产E99。'
    report='''# 查询到真实目标迁移：完整成本下没有稳定综合提高

2026-09-30，全部原生测量和独立实现核验完成。**'''+conclusion+'''

## 主候选的四个完整工作点

固定每集原20K训练query及GT1，训练/评价向量字节无交集。评价为历史E105的4096条/集，已经曝光的开发数据；不使用今日151/157新源及held-out。固定原base、底图、主搜索、真实K/L。四图均在任何评价前构建并统一冻结。每点六方法、CPU15实际单线程、串行、三次完整wall，包含真实路由、slot/入口映射、NSG及输出。QPS为3N/三轮wall总和，不能与其它数据窗口的默认Recall拼接。

'''+table+'''
四点QPS均值都下降。Web两点Recall均值微正、描述区间跨零，不能称已证明改善或伤害；Y R1负均值且区间跨零，Y R100区间低于零。主候选对默认没有一个点同时呈现Recall非负和QPS正的均值组合，更没有跨集稳定收益。三次wall为观测重复，非总体速度置信区间；成对bootstrap区间未校正多重比较，且数据历史曝光，只用于描述。

## 简单控制揭示的有效信息和边界

QueryHub1与主候选使用同一个检索slot，仅把真实GT1投回原H。ShuffledQueryTarget1使用同一个QueryIndex与slot，只置换训练query—GT1配对。TargetBank1直接索引相同20K物理slot的raw目标向量，含原目标重复。DefaultRank1仍完整执行原top3路由，再只用rank1，不能把它称为减少路由计算。

| 工作点 | 控制 | QueryTarget1减控制 ΔRecall pp及区间 | 主候选相对QPS |
|---|---|---|---:|
'''+ '\n'.join(control)+'''

Web两K相对配对打乱的Recall区间为正，说明本地存在query—目标对应的信息；Y两K没有相应稳定质量优势。主候选四点均比QueryHub1的召回均值高，但只有Web R1描述区间为正。不能从这些局部差异推导“所有画像压缩都有害”，因为GT10还使用十目标权重和另一种表示。

目标侧控制的结果须单独归功：

'''+banktable+'''
Web R1的+0.537109pp和−0.8156%QPS是一项应保留的开发取舍：50条救回、28条损伤，区间为正；它仍未实测同Recall更快，不能仅因速度下降就忽略质量收益，也不能以插值宣称前沿改善。Web R100约持平；Y R1质量均值相同但稍慢，Y R100负均值且稍慢、质量区间跨零。这些结果不支持跨集替换。

DefaultRank1在Web R100呈现+0.010498pp与+1.3058%QPS的均值组合，但质量区间跨零、三轮速度范围与默认重叠，其它点未显示稳定联合收益；单入口并非新发现，历史E107/108因素证据保持。主候选四点都没有同时超过目标侧控制的质量与速度，不能将目标库收益归于查询条件配对。

## 全部方法及三次wall

| 工作点 | 方法 | Recall % | ΔRecall pp及区间 | pooled QPS | 三次QPS |
|---|---|---:|---|---:|---|
'''+ '\n'.join(full)+'''

## 救回与损伤

| 主候选工作点 | 命中数提高/降低的query | 正/负净命中数 | 真实命中成员新增/移除 |
|---|---:|---:|---:|
'''+ '\n'.join(gain)+'''

K100可在同一query同时新增和移除正确成员，因此净命中数与真实成员变动明确分列。主候选Y R100新增3426、移除4885，净−1459；不能只看救回query数或相似度得出成功。

## 几何信息、近似遗漏与完整成本

| 数据集 | 方法 | 最好入口raw-IP均值 | H内入口数/有效入口数 | 唯一真实入口数 |
|---|---|---:|---:|---:|
'''+ '\n'.join(geo)+'''

训练目标唯一数Web15789/Y19671；主候选实际入口大多在原H外，但这并不构成Recall保证。最近训练query的真实cosine中位数为Web0.756530/Y0.695909。目标侧入口raw-IP明显更高，仍没有跨工作点转化为稳定收益。固定pool的搜索响应不具备按入口raw-IP单调改善的保证，已有145原生反例解释了为什么几何上界不能替代实测。

全部搜索结束后，预定前16条全20K float64扫描：QueryIndex达到数学最优分数Web14/16、Y16/16；TargetIndex达到最优分数Web12/16、Y14/16。Web目标库argmax slot只相同10/16，另两例为目标重复导致的最优分数同分。此小诊断只说明实际近似遗漏存在，不能外推完整近邻Recall；不据此提高ef或更换线上路由。

旧分析JSON字段`best_entry_cosine_query_scaled_mean`实际为max(raw-IP)/query范数，未除base范数。字段名不够准确；原文件/源码不改，正式表使用raw-IP。真正的最近case cosine已对双方单位化。字段用语后补见reviews/field_semantics_note.md，补充算术核验已恢复所有值、H计数及预定扫描。

| 工作点 | 方法 | 路由NDC | 主图NDC | 总NDC | 相对默认完整额外微秒/query |
|---|---|---:|---:|---:|---:|
'''+ '\n'.join(ndc)+'''

主候选在四点的主图NDC均未节省，查询索引还比原路由多计算约155/159次距离，因而缺少“主搜索省下足够费用”的支持。目标侧控制的主图NDC较低，但更贵的路由抵消大部分收益；NDC不是wall的线性换算。本轮没有额外分项timer，将完整wall作为速度证据。

## 理论与前作

标准最优性和Cauchy界给出单位查询u、所选训练query v_j的目标分数损失不超过diam(B)||u−v_j||，近似训练目标另加误差。投回H再加训练目标对hub的分数损失。这是几何分数界，不是最终Recall、搜索步数或wall界。相同目标库的精确raw-IP最优选择在入口分数上支配任意实例迁移目标；实际TargetBank是近似索引，费用也真实计入。

查询结果复用已见CatapultDB、EDBT2026 Adaptive Query-Aware Hybrid Search以及批查询MST复用，不能以kNN/HNSW或本地监督身份宣称新颖。原08/117/124/125及164分别迁移H内事后入口、固定16槽、七策略或相对rank；本版用实际GT1目标且可在H外，是受控机制区别，不是足够的论文创新证明。前作文献与源码版本差异见上一层online_prior_work_2026.md。

## 实现与资源核验

原Default3的E105完整返回ID、距离bits、入口、主图及路由NDC恢复；各点16条plain/count/E99核验，全部重复/count返回一致。两套独立解析/算术检查训练GT1、置换、全40K hub映射、四图80K节点的向量/label/边/level、数据无重复、跨K与三个查询侧控制的slot、完整98304返回行的GT集合评分及全部成对区间。整数权重bootstrap与原区间最大差2.78e−17pp。额外几何诊断最大算术差2.23e−16。原源码/输入/图hash保持。独立实现由同一agent完成，不冒充独立人员；原GT来源身份复用。

'''+f'''编译及两次构图合计{jobs['compile_and_build_seconds']:.6f}秒，两套原生作业含加载/输出共{jobs['search_job_seconds']:.6f}秒。构图作业Web9.403210/Y6.215917秒；新标签为0，已有GT1的历史取得费用不能说成免费。新4图、397440 NSG、397056 ANN；峰值观测RSS {max(x['max_observed_rss'] for x in jobs['jobs'])/2**30:.3f}GiB。测量结束阶段{jobs['stage_bytes']}字节、全日{jobs['campaign_bytes']}字节，未删旧产物。作业秒数不当查询QPS；构建费用仅附属信息。

'''+conclusion+''' 不扩案例数/ef/近邻数、不改GT数/模型、不追加新源把本版调到通过。目标侧Web R1局部取舍单独保留，不自动进入held-out或切默认。今天继续理论研究至22:00。

[冻结协议](protocol.md) · [推导](theory.md) · [全部统计](results/analysis.json) · [CSV](results/metrics.csv) · [作业账](reviews/jobs_complete.json) · [独立核验](reviews/independent_audit.json) · [几何核验](reviews/diagnostic_audit.json)。
'''
    names=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md'];old={n:(ROOT/n).read_text() for n in names}
    with zipfile.ZipFile(R/'reviews/root_docs_before_closeout.zip','x',zipfile.ZIP_DEFLATED) as z:
        for n in names:z.write(ROOT/n,n)
        z.write(CAMP/'state.json','campaign_state.json')
    with zipfile.ZipFile(R/'reviews/root_docs_before_closeout.zip') as z:assert z.testzip() is None
    put(R/'report.md',report)
    s=io.StringIO();w=csv.DictWriter(s,fieldnames=list(csvrows[0]));w.writeheader();w.writerows(csvrows);put(R/'results/metrics.csv',s.getvalue())
    status='STOP_QUERY_TARGET_TRANSFER_V1'
    put(R/'decision.json',{'status':status,'default_changed':False,'main_joint_improvement_not_demonstrated':True,'main_QPS_means_negative_all_four':True,'Web_pairing_information_local':True,'target_bank_Web_R1':'RETAIN_LOCAL_QUALITY_SPEED_TRADEOFF','historical_development_only':True,'stop_scope':'fixed query-target transfer; no sample/ef/neighbor/GT-count/model tuning or automatic fresh evaluation','audit':'PASS','continuing_until':'2026-09-30T22:00:00+08:00'})
    rel='entry_method_exploration/20260930_theory_until2200_v1/research/query_target_transfer_v1'
    card='''# 165 查询→真实目标迁移与同容量目标侧控制

2026-09-30完成。`STOP_QUERY_TARGET_TRANSFER_V1`；原默认与生产E99保持。主目标为完整线上Recall–QPS综合收益。

原20K训练query/GT1与E105历史4096评价向量字节分离。相似训练query的GT1作入口，可落在原H外；配投回H、同20K目标HNSW、配对置换、原三入口/原rank1五控制。四普通图在任何评价前构建冻结，真实K1/K100、原L/底图/主搜索不变，CPU15实际单线程、三轮完整wall。没有读今日151/157新源或held-out。

'''+table+'''
四点主候选均更慢；Web质量微正但不确定，Y两点均值负、K100描述区间负。Web配对相对置换有局部信息，仍不足以超过默认和目标侧控制。目标侧Web R1为90.991211%/420.254 QPS，相对默认+0.537109pp [0.122070,0.952148]、−0.8156%QPS，50救回/28损伤，保留质量/速度取舍；未证同Recall更快或跨集稳定。

完整98304返回行独立集合评分、全40K训练GT1/hub映射、四图80K向量/结构、历史Default3/全部重复/plain/count/E99、slot/区间及额外几何诊断通过。独立实现为同一agent，非独立人员。三轮速度与历史开发bootstrap均有适用边界。QueryTarget主图NDC四点均未减少，额外路由没有被主搜索节省抵消。

新397440 NSG/397056 ANN/4小图，0新GT/画像；原生测量作业674.300秒，编译构图24.047秒。全部原件保留。停止固定迁移版本的实例数、ef、近邻数、GT数量和模型调参；局部控制收益归控制，不认领为query条件信息。

'''+f'[完整报告](../{rel}/report.md) · [协议](../{rel}/protocol.md) · [理论](../{rel}/theory.md) · [统计](../{rel}/results/analysis.json) · [核验](../{rel}/reviews/independent_audit.json)。\n'
    put(ROOT/'experiment_history/165_query_target_transfer_online.md',card)
    end=old['summary.md'].index('[164状态/rank完整在线验证]')
    (ROOT/'summary.md').write_text('# ACSG 当前结果摘要\n\n'+f'[165查询→真实目标迁移](experiment_history/165_query_target_transfer_online.md)已完成独立核验。**{conclusion}**\n\n'+table+'\n目标侧简单控制在Web R1为90.991211%/420.254 QPS，相对默认+0.537109pp [0.122070,0.952148]、QPS−0.8156%，保留局部质量/速度取舍；未证明同Recall更快或跨集稳定。Web查询配对相对打乱有局部信息，仍不足以超过默认与简单控制。全98304返回/映射/四图/原生/统计核验通过，停止本版扩实例/ef/近邻/GT数/模型。\n\n'+old['summary.md'][end:])
    lo=old['spec.md'].index('[查询→目标迁移工具]');hi=old['spec.md'].index('[状态/rank在线工具]')
    spec=f'''[查询→目标迁移工具]({rel}/protocol.md)已实现/核验：原20K训练query单位化构普通HNSW，slot映射真实GT1或原H最近hub；相同物理slot的raw目标图与一次配对置换为控制。四图先构建统一冻结，再运行六方法完整路由/映射/原NSG/输出wall；真实K1/K100、原图/主核/L不变。全量重复/count/历史Default3和E99恢复，独立二进制解析全部图向量/结构/label，完整返回GT评分、映射/配对bootstrap及几何诊断核验通过。旧JSON字段best_entry_cosine_query_scaled_mean实际为单位query的raw-IP，另存语义说明，不能称base归一化cosine。工具隔离、不接入生产；训练行/GT/slot/归一化/H或图变化均使相关索引/映射失效。\n\n'''
    (ROOT/'spec.md').write_text(old['spec.md'][:lo]+spec+old['spec.md'][hi:])
    target=old['s-target.md'].replace('已完成记录141–164保留','已完成记录141–165保留',1)
    lo=target.index('已核对[查询结果复用');hi=target.index('## 优先二：')
    target=target[:lo]+'''[165查询→真实目标迁移](experiment_history/165_query_target_transfer_online.md)已完成六方法完整wall及独立核验：主候选四点QPS都降，Web召回微正不确定、Y均值负；停止固定版本的案例数/ef/近邻数/GT数/模型调参。Web配对信息相对打乱有效，但没有超过默认和目标侧控制。目标侧Web R1的+0.537109pp/−0.8156%QPS取舍独立保留，未证明同Recall更快，不自动追加新源或切默认。\n\n下一步继续核对几何信息、搜索响应与完整wall之间的条件，梳理本日可复现结论和前作边界。只有不同信息来源且能被简单控制证伪的具体假设，才另立小实验；目前无新性能runner排队。\n\n'''+target[hi:]
    target=target.replace('164已封存；迁移阶段准备完成、等待四图统一冻结后执行。','164/165已完成核验并封存；当前无性能runner运行。')
    (ROOT/'s-target.md').write_text(target)
    marker='## 最新记录\n\n| 记录 | 内容与边界 |\n|---|---|\n';assert marker in old['s-experiment.md']
    (ROOT/'s-experiment.md').write_text(old['s-experiment.md'].replace(marker,marker+'| [165 查询→真实目标迁移](experiment_history/165_query_target_transfer_online.md) | 主候选四点更慢、未获稳定综合收益；目标侧Web R1局部质量/速度取舍保留，独立核验完成 |\n',1))
    (ROOT/'experiment_history/README.md').write_text(old['experiment_history/README.md'].replace('# ACSG 历史实验详细复盘\n\n','# ACSG 历史实验详细复盘\n\n2026-09-30最新[165查询→真实目标迁移](165_query_target_transfer_online.md)完成并独立核验；主候选无稳定综合收益，目标侧Web R1质量/速度取舍单独保留。\n\n',1))
    state=read(CAMP/'state.json');assert R.name not in state['completed_stages'] and state['active_process'] is None
    assert state['new_NSG_calls']==2841920 and state['new_ANN_calls']==2655488
    state['completed_stages'].append(R.name);state.update(stage=status.lower(),last_updated_unix=time.time())
    (CAMP/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    files={str(p.relative_to(R)):ident(p) for p in sorted(R.rglob('*')) if p.is_file() and p.name!='seal.json'}
    assert sum(v['bytes'] for v in files.values())<192*2**20
    put(R/'reviews/seal.json',{'status':'AUDITED_COMPLETE_NO_DEFAULT_CHANGE','unix':time.time(),'files':files,'default_changed':False})
    print(status,len(files),flush=True)

if __name__=='__main__':main()
