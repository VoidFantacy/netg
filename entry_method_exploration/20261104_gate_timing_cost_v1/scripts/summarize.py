from common import *
import collections
def load(n):
    with open(R/'analysis'/n) as f:return list(csv.DictReader(f))
def wide(n,rows):
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with open(R/'analysis'/n,'w') as f:w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
def table(h,rows):return '| '+' | '.join(h)+' |\n| '+' | '.join(['---']*len(h))+' |\n'+''.join('| '+' | '.join(map(str,r))+' |\n' for r in rows)+'\n'
P=load('points.csv');G=load('gates.csv');C=load('stage_costs.csv');RR=load('rerank_costs.csv');F=load('frontier.csv');PL=load('placement.csv')
by=collections.defaultdict(list)
for r in P:
    if r['L']=='200':by[r['dataset'],int(r['K']),r['method']].append(r)
ag=[]
for (ds,K,m),rr in by.items():
    assert len(rr)==2;us=sum(float(r['mean_us']) for r in rr)/2
    ag.append(dict(dataset=ds,K=K,L=200,method=m,recall_pct=100*sum(int(r['hits']) for r in rr)/(1024*K),mean_us=us,qps=1e6/us,n=1024,gate_enabled=sum(int(r['gate_enabled']) for r in rr),
        aux_exact_per_query=sum(float(r['aux_exact_per_query']) for r in rr)/2,rerank_rows_per_query=sum(float(r['rerank_rows_per_query']) for r in rr)/2))
wide('aggregate.csv',ag);lookup={(r['dataset'],r['K'],r['method']):r for r in ag}
by=collections.defaultdict(list)
for r in G:by[r['dataset'],int(r['K']),r['method']].append(r)
ga=[]
for (ds,K,m),rr in by.items():
    row=dict(lookup[ds,K,m]);ref=sum(int(r['always_positive_hits']) for r in rr);kept=sum(int(r['kept_positive_hits']) for r in rr)
    row.update(family=m[0],positive_reference=ref,positive_kept=kept,retention_pct=100*kept/ref if ref else None,enable_pct=100*row['gate_enabled']/1024,
        false_rejected_positive_queries=sum(int(r['false_rejected_positive_queries']) for r in rr),gate_profile_us=sum(float(r['gate_profile_us']) for r in rr)/2,
        measured_saved_vs_always_us=lookup[ds,K,'ALWAYS']['mean_us']-row['mean_us'],replay_estimate_net_saving_us=sum(float(r['replay_estimate_net_saving_us']) for r in rr)/2)
    valid=[float(r['positive_retention_pct']) for r in rr if r['positive_retention_pct']!=''];row['retention_min_window_pct']=min(valid) if valid else None;row['retention_max_window_pct']=max(valid) if valid else None
    ga.append(row)
wide('gate_aggregate.csv',ga)
by=collections.defaultdict(list)
for r in C:by[r['dataset'],int(r['K']),r['method']].append(r)
ca=[]
for (ds,K,m),rr in by.items():
    row=dict(dataset=ds,K=K,method=m)
    for key in rr[0]:
        if key in ['dataset','window','K','L','method']:continue
        values=[float(r[key]) for r in rr if r[key]!=''];row[key]=sum(values)/len(values) if values else None
    ca.append(row)
wide('stage_aggregate.csv',ca)
by=collections.defaultdict(list)
for r in RR:by[r['dataset'],int(r['K']),r['method'],r['reference']].append(r)
ra=[]
for (ds,K,m,ref),rr in by.items():
    row=dict(dataset=ds,K=K,method=m,reference=ref)
    for key in ['recall_gain_pp','formal_extra_us','qps_change_pct','rerank_feature_delta_us','rerank_predict_delta_us','expansion_delta_us','rerank_rows_delta','aux_exact_delta']:row[key]=sum(float(r[key]) for r in rr)/2
    ra.append(row)
wide('rerank_aggregate.csv',ra)
primary=['F-PRE90','F-POST90','N-PRE90','N-POST90','N-CPOST90'];decision=[]
for ds in DS:
 for K,L in STATES:
  for family in ['F','N']:
    a,z=lookup[ds,K,f'{family}-PRE90'],lookup[ds,K,f'{family}-POST90'];pre_dom=a['recall_pct']>=z['recall_pct'] and a['qps']>=z['qps'] and (a['recall_pct']>z['recall_pct'] or a['qps']>z['qps']);post_dom=z['recall_pct']>=a['recall_pct'] and z['qps']>=a['qps'] and (z['recall_pct']>a['recall_pct'] or z['qps']>a['qps'])
    decision.append(dict(dataset=ds,K=K,family=family,pre_recall=a['recall_pct'],post_recall=z['recall_pct'],pre_qps=a['qps'],post_qps=z['qps'],post_gain_pp=z['recall_pct']-a['recall_pct'],post_qps_change_pct=100*(z['qps']/a['qps']-1),pooled_description='POST covers PRE' if post_dom else 'PRE covers POST' if pre_dom else 'tradeoff or equal'))
wide('pre_post_summary.csv',decision)
strong=[r for r in F if r['method'] in primary];rankgain=[r for r in ra if r['method']=='ALWAYS' and r['reference']=='FAST384']
assets=read(R/'reviews/assets_complete.json')['records'];gates=read(R/'reviews/gates_complete.json')['records'];formal=read(R/'reviews/formal_complete.json')['records'];modelpaths=set()
for ds in DS:
    for r in read(R/'configs'/f'{ds}.gate_labels.json')['model_files']:
        p=Path(r['path']);j=read(p);modelpaths.update([p,Path(j['node_ids']),Path(j['node_embeddings'])])
cost=dict(new_label_process_seconds=sum(r['seconds'] for r in assets if '.labels.log' in r['log']),new_model_training_process_seconds=sum(r['seconds'] for r in assets if '.train.log' in r['log']),
    gate_label_process_seconds=sum(r['seconds'] for r in gates if '.gate_labels.log' in r['log']),gate_fit_process_seconds=sum(r['seconds'] for r in gates if '.gate_fit.log' in r['log']),
    formal_complete_batch_seconds=read(R/'analysis/analysis_receipt.json')['formal_complete_batch_seconds'],formal_process_seconds=sum(r['seconds'] for r in formal),
    model_artifact_bytes=sum(p.stat().st_size for p in modelpaths),gate_artifact_bytes=sum(p.stat().st_size for p in (R/'storage/gates').rglob('*.json')),
    profile_extra_percent_min=min(float(r['profile_vs_formal_pct']) for r in C),profile_extra_percent_max=max(float(r['profile_vs_formal_pct']) for r in C),
    new_persistent_bytes=sum(p.stat().st_size for p in R.rglob('*') if p.is_file()),
    inherited_cost_note='COCO/WebVid student and labels reused from E198; inherited cost remains in E198, not zero. Shared graph/router/SQ build cost not regenerated. Profile batch boundary lacks six-array copy/destruction and includes stage clocks; neither profiler delta nor stage sum is formal QPS.')
dump(R/'analysis/cost_ledger.json',cost)
facts=dict(points=len(P),batches=3*len(P),primary_gate_points=len(strong),primary_covered=sum(r['covered']=='True' for r in strong),primary_range_covered=sum(r['range_covered']=='True' for r in strong),
    pre_post_pooled_decisions=collections.Counter(r['pooled_description'] for r in decision),same_gate_placement_max_abs_qps_pct=max(abs(float(r['late_vs_pre_qps_pct'])) for r in PL),
    rerank_vs_fast_positive_pooled=sum(r['recall_gain_pp']>0 for r in rankgain),rerank_vs_fast_pooled_cases=len(rankgain))
dump(R/'analysis/summary_facts.json',facts)
cn={'coco':'COCO','flickr30k':'Flickr','webvid2_5m_light_v1':'WebVid','yandex_t2i_official10M_ip_v1':'Yandex'}
text=['# E199 搜索前/查询阶段残差开关与精排成本\n\n2026-11-04。四个多模态数据集，真实K1/K100、L200；固定强控制网格；两旧曝光窗口A/B各512。\n\n',
 f"完成{facts['points']}点/{facts['batches']}轮完整CPU15/T1。五种主门策略共{facts['primary_gate_points']}窗口点，{facts['primary_covered']}个被同期GT10/完整OPT-B32/REUSE-SQ覆盖，{facts['primary_range_covered']}个通过三轮观测范围覆盖检查。默认不自动替换。\n\n",
 '## 决策含义与公平对照\n\nSTATIC按dataset/K/L在cal选择全开/全关；PRE是query到达、路由已得、主搜索前预测；POST看相同主搜索结果后预测。PRE-LATE使用同一个PRE模型和阈值，只改变执行位置；全部返回/动作一致。主搜索总是完整运行，因此纯粹前移判断不自动节省主搜索费用。\n\n',
 'F全补门：on运行直接C＋CASCADE384，off返回主结果；PRE/POST都能省掉拒绝query的C评分。N导航门：C始终精算合并，只判断是否追加CASCADE384；CPOST还可利用C距离摘要。F与N拒绝后的答案语义不同，不能混表当作时机单变量。\n\n',
 '## 搜索前与搜索后：两窗合并描述\n\nRecall按1024query合并命中计算；QPS由两窗每query时间的平均值取倒数，不直接平均QPS。逐窗原值仍在points/gates，合并行不是新独立确认。\n\n',
 table(['数据','K','语义','PRE Recall/QPS','POST Recall/QPS','POST增量pp','POST速度变化','合并描述'],[[cn[r['dataset']],r['K'],r['family'],f"{r['pre_recall']:.4f}%/{r['pre_qps']:.2f}",f"{r['post_recall']:.4f}%/{r['post_qps']:.2f}",f"{r['post_gain_pp']:+.4f}",f"{r['post_qps_change_pct']:+.2f}%",r['pooled_description']] for r in decision]),
 '## 门启用、收益保留与完整费用\n\n90/75为独立cal中的正增量保留目标，正式窗口可能失守。分母是ALWAYS相对相应off动作的逐query正增量总和，零分母NA；全开/全关不是自动识别成功。保留“合/最低窗”分别是两窗合并值和有定义窗口的最小值；µs/query为正式完整wall。\n\n']
for ds in DS:
    rows=[]
    for K,L in STATES:
        for m in ['F-STATIC','F-PRE90','F-POST90','N-STATIC','N-PRE90','N-POST90','N-CPOST90']:
            r=next(x for x in ga if (x['dataset'],x['K'],x['method'])==(ds,K,m));rows.append([K,m,f"{r['enable_pct']:.1f}%",(f"{r['retention_pct']:.2f}/{r['retention_min_window_pct']:.2f}%" if r['retention_pct'] is not None else 'NA'),f"{r['recall_pct']:.4f}%",f"{r['qps']:.2f}",f"{r['mean_us']:.2f}",f"{r['gate_profile_us']:.2f}",f"{r['measured_saved_vs_always_us']:+.2f}"])
    text.append(f"### {cn[ds]}\n\n"+table(['K','方法','启用','保留 合/最低窗','Recall','QPS','完整µs','门诊断µs','较全开省µs'],rows))
text.append('## 精排成本与实际展开\n\nALWAYS=同池CASCADE384。FAST384用学生直接选1；TEACHER384全C运行相同重模型。局部精排成本拆成特征与树预测，完整差值还包含不同入口引起的实际扩展费用。\n\n')
text.append(table(['数据','K','方法/参照','Recall增量pp','完整增加µs','特征增加µs','预测增加µs','扩展变化µs','精算变化/query'],[[cn[r['dataset']],r['K'],r['method']+'/'+r['reference'],f"{r['recall_gain_pp']:+.4f}",f"{r['formal_extra_us']:+.2f}",f"{r['rerank_feature_delta_us']:+.2f}",f"{r['rerank_predict_delta_us']:+.2f}",f"{r['expansion_delta_us']:+.2f}",f"{r['aux_exact_delta']:+.1f}"] for r in ra]))
text.append('## 成本计量与离线账\n\n正式未插阶段时钟；profile独立重放，全部结果/动作与正式相同。profile_batch包含阶段时钟但没有正式六数组复制与正常销毁的完整边界，所以profile差值不能全部命名为插钟开销。阶段均摊/启用条件均值/P50/P95及未分配差额分别保存，不以阶段和替换正式QPS。门策略normal/profile沿同一模板查询逻辑；GT10/OPT-B32/Q8分段采用返回等价逐query适配层，分配/调度与原优化batch不同，不能当作基线原批次的严格分解。off分支返回对齐基线也不意味着具有相同开销；包装/复制成本均计正式wall。cal标记全关时，当前PRE/POST仍构造对应特征再短路预测，STATIC不构造；这属于可优化的全关快路径差异，不是离线天然优于在线的证明。门特征在启用后可能被学生复用，分段归属迁移不等于同额新增开销。辅助精算与辅助邻接槽、重特征邻接槽分别计，不是总NDC或全部主搜索工作。\n\n')
text.append(table(['项目','数值'],[['新Flickr/Yandex标签进程秒',f"{cost['new_label_process_seconds']:.2f}"],['新Flickr/Yandex模型训练进程秒',f"{cost['new_model_training_process_seconds']:.2f}"],['四集实际门标签进程秒',f"{cost['gate_label_process_seconds']:.2f}"],['四集门拟合进程秒',f"{cost['gate_fit_process_seconds']:.2f}"],['正式完整batch wall秒',f"{cost['formal_complete_batch_seconds']:.2f}"],['正式进程秒（包含warmup、profile、核验等）',f"{cost['formal_process_seconds']:.2f}"],['八状态模型文件MiB（非RSS）',f"{cost['model_artifact_bytes']/2**20:.2f}"],['门模型文件KiB',f"{cost['gate_artifact_bytes']/2**10:.2f}"]]))
text.append('COCO/WebVid复用E198，不把继承训练债记成零；共同benchmark加载SQ/全图静态数组不等于默认或新门的独立部署RAM。正式batch wall包含于正式进程，不重复相加。\n\n')
text.append('## 证据边界与交付\n\n四多模态集、单图/画像、固定Q8来源与单入口384、L200门研究、两曝光窗口、共享开发512、K1稀疏事件与多比较限制保留。未测试主图循环内动态早停或主beam续搜。未把STATIC称离线逐query最优；未把学习教师当GT oracle。历史有效M5/B32/SQ继续保留原身份。\n\n')
text.append('[协议](protocol.md) · [冻结](formal_freeze.json) · [全部点](analysis/points.csv) · [门逐窗](analysis/gates.csv) · [阶段均值/P50/P95](analysis/stage_costs.csv) · [精排成本](analysis/rerank_costs.csv) · [同门位置](analysis/placement.csv) · [强控制](analysis/frontier.csv) · [成本账](analysis/cost_ledger.json) · [主核验](analysis/analysis_receipt.json) · [stdlib](analysis/stdlib_audit.json) · [PDF](E199_残差门控时机与精排成本_20261104.pdf)。\n')
(R/'report_zh.md').write_text(''.join(text));print(json.dumps(facts,ensure_ascii=False),flush=True)
