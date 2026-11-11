from common import *
import collections
def table(headers,rows):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(map(str,r))+' |\n' for r in rows)+'\n'
def csvread(name):
    with open(R/'analysis'/name) as f:return list(csv.DictReader(f))
P=csvread('points.csv');C=csvread('comparisons.csv');M=csvread('mechanisms.csv');S=csvread('shortlist.csv')
lookup={(r['dataset'],r['window'],int(r['K']),int(r['L']),r['method']):r for r in P}
comp={(r['dataset'],r['window'],int(r['K']),int(r['L']),r['method']):r for r in C}
learned=['FAST96','FAST384','CASCADE96','CASCADE384','ADAPT','POLICY','TEACHER384']
stats=[]
for m in learned+['OLD-CACHED384','DIST96','DIST384','DIST1-FULL','MODEL1','Q8-B32']:
    rows=[r for r in C if r['method']==m]
    by=collections.defaultdict(list)
    for r in rows:by[r['dataset'],r['K'],r['L']].append(r)
    stats.append(dict(method=m,window_points=len(rows),covered=sum(r['covered']=='True' for r in rows),range_covered=sum(r['range_covered']=='True' for r in rows),
        both_uncovered_configurations=sum(all(r['covered']=='False' for r in rr) for rr in by.values())))
csvwrite(R/'analysis/method_summary.csv',stats)
labels=[read(p) for p in (R/'storage/labels').glob('*/*/complete.json')]
train=[read(p) for p in (R/'storage/models').glob('*/*/training.json')]
cost=dict(label_candidate_rows=sum(x['rows'] for x in labels),executed_single_seed_actions=2*sum(x['rows'] for x in labels),
    label_process_seconds=sum(x['seconds'] for x in read(R/'reviews/labels_complete.json')['records']),
    training_process_seconds=sum(x['seconds'] for x in read(R/'reviews/training_complete.json')['records']),
    training_internal_seconds=sum(x['seconds'] for x in train),
    formal_process_seconds=sum(x['seconds'] for x in read(R/'reviews/formal_complete.json')['records']),
    formal_complete_batch_seconds=read(R/'analysis/analysis_receipt.json')['formal_batch_wall_seconds'],
    formal_archive_seconds=sum(read(p)['seconds'] for p in (R/'storage/results').glob('*/*/packet_archive.json')),
    online_model_artifact_bytes=sum(p.stat().st_size for pat in ['model.json','node_ids.i32','node_embeddings.f64'] for p in (R/'storage/models').rglob(pat)),
    new_evidence_bytes=sum(p.stat().st_size for p in R.rglob('*') if p.is_file()),
    note='Internal training is nested in training processes; batch wall is nested in formal processes. Artifact sizes are not measured resident RAM. Model and shared SQ loading excluded from query wall.')
dump(R/'analysis/cost_ledger.json',cost)
shortnames={'coco':'COCO','webvid2_5m_light_v1':'WebVid'}
name=lambda d:shortnames[d]
learnrows=[r for r in C if r['method'] in learned]
new_uncovered=[r for r in learnrows if r['covered']=='False']
headline=f"完成1,480点、4,440轮完整CPU15/T1测量。7种新学习动作共{len(learnrows)}个窗口点，其中{len(learnrows)-len(new_uncovered)}个被同窗GT10/OPT-B32/REUSE-SQ强控制覆盖。默认保持E99；有限网格未覆盖也不直接成为默认替换证据。"
parts=['# E198 条件残差导航验证报告\n\n2026-11-02。用户授权验证新残差方法并解释GT10之后的流程。\n\n'+headline+'\n\n',
    '具体方法见[方法详解](method_zh.md)。本轮实现前置门、双塔快速选点、至多6点教师重排及0/96/384预算选择。直接C始终精算并保留；只有导航入口被筛选。未修改主图、metric、主核或默认，未实现原主beam续搜。\n\n',
    '## 与完整强前沿比较\n\n“覆盖”指同一数据、K、窗口内有控制Recall不低且中位完整QPS不低，至少一项严格更优。“全三轮范围覆盖”进一步要求该控制最慢QPS仍不低于新方法最快QPS，属于观测范围检查，不是统计置信保证。\n\n',
    table(['方法','窗口点','被覆盖','全三轮范围覆盖','两窗均未覆盖的配置'],[[x['method'],x['window_points'],x['covered'],x['range_covered'],x['both_uncovered_configurations']] for x in stats]),
    '## 最终POLICY逐状态结果\n\n每个窗口512条查询。下表的强控制按达到不低于该方法的Recall门槛后选最快QPS；控制可能有更高Recall，因此不是所有行都叫严格同Recall。A/B保持分开，QPS均重新测量，未拼接旧绝对时间。\n\n']
rows=[]
for d in DS:
  for K,L in STATES:
    for w in ['A','B']:
      p=lookup[d,w,K,L,'POLICY'];c=comp[d,w,K,L,'POLICY'];base=lookup[d,w,K,L,'Q8-B32']
      rows.append([name(d),w,K,L,f"{float(p['recall_pct']):.4f}%",f"{float(p['qps']):.2f}",f"{float(p['mean_us']):.2f}",
        f"{float(p['gain_vs_Q8_pp']):+.4f}",c['quality_threshold_control'],f"{float(c['quality_threshold_QPS_gain_pct']):+.2f}%",p['failed_lt10']])
parts.append(table(['数据','窗','K','L','Recall','QPS','µs/query','较Q8增量pp','质量门槛强控制','QPS变化','K100命中<10条数'],rows))
parts.append('## 相同状态、候选池与展开预算的机制比较\n\n下面每行按A/B给出Recall与QPS；TEACHER384是可部署的学习教师，不是GT逐query最优oracle。其增量不能当作候选池上界。\n\n')
for d in DS:
  for K,L in STATES:
    rows=[]
    for m in ['OPT-B32','REUSE-SQ','Q8-B32','DIST96','FAST96','CASCADE96','DIST384','FAST384','CASCADE384','TEACHER384','ADAPT','POLICY','MODEL1','OLD-CACHED384']:
      a,b=[lookup[d,w,K,L,m] for w in ['A','B']]
      rows.append([m,f"{float(a['recall_pct']):.4f} / {float(b['recall_pct']):.4f}",f"{float(a['qps']):.2f} / {float(b['qps']):.2f}",
        f"{float(a['gain_vs_Q8_pp']):+.4f} / {float(b['gain_vs_Q8_pp']):+.4f}",f"{float(a['aux_exact_per_query']):.1f} / {float(b['aux_exact_per_query']):.1f}"])
    parts.append(f'### {name(d)} K{K}/L{L}\n\n'+table(['方法','Recall% A/B','QPS A/B','相对Q8增量pp A/B','辅助精算/query A/B'],rows))
parts.append('## 门的泛化与短名单\n\n门的90%目标只在独立校准512query选择；正式两窗必须另看实际保留。分母为ADAPT比Q8产生的逐query正增量之和，零分母记NA。门全关或全开不是自动学会有效识别。\n\n')
parts.append(table(['数据','窗','K/L','过门/512','实际动作/512','96/384动作数','保留正增量','误拒正收益query'],
    [[name(r['dataset']),r['window'],f"{r['K']}/{r['L']}",r['gate_entered'],r['action_enabled'],f"{r['budget96']}/{r['budget384']}",f"{100*float(r['retention']):.2f}%" if r['retention'] else 'NA',r['wrong_rejected_positive_queries']] for r in M]))
parts.append(table(['数据','窗','K/L','平均C','平均384短名单','学习全C教师所选入口保留'],
    [[name(r['dataset']),r['window'],f"{r['K']}/{r['L']}",f"{float(r['mean_C']):.2f}",f"{float(r['mean_shortlist_384']):.2f}",f"{float(r['learned_full_teacher_seed_retention_pct']):.2f}%"] for r in S]))
parts.append('最后一列是学习教师所选ID是否被短名单保留，并非GT遗漏目标覆盖率，也不是GT最优导航入口保留率。最终实际救回、损伤、C精算、额外精算及辅助展开的邻接槽访问均在[points.csv](analysis/points.csv)。邻接槽计数不含主搜索和教师特征扫描，额外精算不是总NDC，六数组包的零NDC为占位；这些过程耗时仍包含在完整wall。主visited命中或seen重复会减少实际精算，预算是上限而非每query固定用满。\n\n')
parts.append('## 训练、成本和证据边界\n\n')
parts.append(table(['项目','实测或定义'],[
    ['标签候选行 / 两预算动作数',f"{cost['label_candidate_rows']:,} / {cost['executed_single_seed_actions']:,}"],
    ['标签进程累计秒',f"{cost['label_process_seconds']:.2f}"],['训练进程累计秒',f"{cost['training_process_seconds']:.2f}"],
    ['正式完整batch wall秒',f"{cost['formal_complete_batch_seconds']:.2f}"],['正式进程累计秒（含加载、warmup、核验等）',f"{cost['formal_process_seconds']:.2f}"],
    ['八状态模型及节点表示文件MiB',f"{cost['online_model_artifact_bytes']/2**20:.2f}"],['本目录新增证据GiB（报告生成时）',f"{cost['new_evidence_bytes']/2**30:.3f}"]]))
parts.append('过程内耗时与过程总耗时有嵌套，不相加成项目总耗时；文件大小不是驻留内存。原共享SQ后端只为相关控制使用，公共benchmark加载全部后端的RAM不能全部归因于新策略。\n\n')
parts.append('每集2048fit、512模型/λ开发兼门fit、512独立阈值及费用cal；Q8银行来自前8K，模型角色沿后8K合法选择，原画像监督身份交叠已在E197披露。每个K/L单独训练，未把L迁移当状态匹配。两正式窗口均旧曝光查询，不能叫盲测；只有COCO/WebVid、单图/画像、固定候选源与单入口96/384后端，K1少量事件和未校正多比较区间限制保留。未展开到其他五集或额外参数。\n\n')
parts.append('native/NumPy模型推断、实际返回与三轮包SHA/工作/决策、native线性merge及NumPy全排序、独立Python策略决策、stdlib整数/完整wall/强前沿和旧兼容包核验均有收据。独审为同执行者不同实现，不是独立人员复现，也未重跑所有图标签或独立复算bootstrap。归档逐payload校验，全部证据在持久磁盘，原gzip容器字节不宣称保留。\n\n')
parts.append('独立决策审计首版在COCO B/K1/L200第42条query发现NumPy float32数组比较把树的double阈值隐式降精度，误判96而原生正确选择384。审计v2将比较输入转float64后重新核验全部窗口；原冻结analyze.py、失败日志及收据保留，模型、正式二进制、实际返回和wall均未改。详见[修正收据](reviews/analysis_precision_correction.json)和[审计v2](scripts/analyze_v2.py)。\n\n')
parts.append('本轮局部结论不推翻历史E173/E191/E194条件有效的M5/B32/SQ；最强适用的完整B32/SQ已作为本轮实测控制。旧科学文件、seal及PDF保留，根文档由source_before精确桥接；无新PDF、无默认替换。\n\n')
parts.append('## 证据入口\n\n[协议](protocol.md) · [正式冻结](formal_freeze.json) · [方法详解](method_zh.md) · [全部点](analysis/points.csv) · [强控制比较](analysis/comparisons.csv) · [跨窗](analysis/stability.csv) · [门机制](analysis/mechanisms.csv) · [选点质量](analysis/selection_quality.csv) · [短名单](analysis/shortlist.csv) · [成本](analysis/cost_ledger.json) · [主核验](analysis/analysis_receipt.json) · [stdlib核验](analysis/stdlib_audit.json) · [交付](delivery_validation.json)。\n')
(R/'report_zh.md').write_text(''.join(parts))
dump(R/'analysis/summary_facts.json',dict(headline=headline,learned_points=len(learnrows),learned_uncovered_points=len(new_uncovered),method_summary=stats))
print(headline,flush=True)
