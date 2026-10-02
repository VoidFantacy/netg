import datetime,json,pathlib,shutil
D=pathlib.Path(__file__).resolve().parent.parent;R=D.parent.parent
read=lambda p:json.loads(p.read_text())
assert read(D/'reviews/results_audit.json')['status']=='PASS'
assert read(D/'reviews/figures_visual_check.json')['status']=='PASS'
s=read(D/'results/summary.json');rows=s['metrics'];gains=s['speedups']
def row(m,kind,K=100,L=1250):return next(x for x in rows if (x['method'],x['kernel'],x['K'],x['L'])==(m,kind,K,L))
old,new=row('NSG','current'),row('NSG','span-batch4');soft=row('GT10-soft-t1','span-batch4');hard=row('GT10-hard','span-batch4');gate=row('GATE','span-batch4');h=row('HNSW','reference')
ns=[x['speedup_percent'] for x in gains if x['method']=='NSG'];allg=[x['speedup_percent'] for x in gains]
compat='其它四集64配置的ID/距离bits/入口/逐query NDC全部一致' if all(x['status']=='PASS' for x in s['compatibility']) else '其它四集存在不一致，通用无损替换未通过，差异完整保留'
link='entry_method_exploration/20260916_shared_span_batch4_v1'
headline=f'E102于2026-09-16完成统一优化公平比较：NSG、GT10-hard/soft、GATE均使用相同span+batch4，WebVid四预算各新旧内核及同轮HNSW共36配置108plain。NSG自身四点平均QPS变化{min(ns):+.2f}%至{max(ns):+.2f}%；K100/L1250从{old["qps_mean"]:.2f}变为{new["qps_mean"]:.2f}QPS，Recall@100保持{new["recall"]*100:.4f}%。同内核soft为{soft["qps_mean"]:.2f}QPS/{soft["recall"]*100:.4f}%，GATE为{gate["qps_mean"]:.2f}QPS/{gate["recall"]*100:.4f}%；HNSW为{h["qps_mean"]:.2f}QPS/{h["recall"]*100:.4f}%。'
low=[next(x for x in s['shared_kernel_comparisons'] if (x['method'],x['K'],x['L'])==('GT10-soft-t1',K,L)) for K,L in [(1,96),(100,100)]]
gt_readout=f'同内核低预算K1/L96和K100/L100，GT10-soft相对NSG分别增加{low[0]["recall_delta_pp"]:.2f}/{low[1]["recall_delta_pp"]:.2f}pp Recall与{low[0]["qps_delta_percent"]:.2f}%/{low[1]["qps_delta_percent"]:.2f}%平均QPS；高预算速度差缩小，结合三轮范围判断，不支持“GT10无效”或“全面第一”。'
links=f'[报告与图]({link}/report.md) · [复盘95](experiment_history/95_shared_span_batch4_comparison.md)。'
paras={
 'summary.md':headline+' '+gt_readout+' '+compat+'，合计2296000次真实搜索。公共内核加速与入口方法收益分开报告，四点不能代表完整前沿或其它四集新QPS；生产/默认仍E99，修改前备份8afd61cd。'+links,
 'spec.md':f'E102已验收独立统一评测入口`{link}/src/compare.cpp`：四种NSG入口均使用逐字相同E101 ResearchKernel span+batch4，current链接E99库，完整HNSW保持原生搜索；同图/storage、路由/输出均计入plain。新计数包装直接转发Faiss真实batch4，Web36配置108轮和count全部对齐E99输出/入口/NDC；继承E101合成边界验收，本轮0新合成搜索。另四集496000次真实count，'+compat+'。未覆盖主ACSG API/trace/默认库，协议和代码身份分别保存。'+links,
 's-target.md':'E102用户要求的统一优化测试已完成。'+headline+' '+gt_readout+' 下一步若扩大结论，应以相同优化后的NSG作为入口方法基线；公共内核提速不能计为GT10独有优势。当前交付限Web四固定预算、其它四集一致性，无自动追加全网格、重训或生产部署；默认仍Web软/Y硬。若后续合入主API，保留trace、特殊值/未知DC回退与图生命周期。'+links,
 's-experiment.md':headline+' '+compat+'；2296000search、0新训练/构图/GT/合成搜索，原E101封存保持。'+links,
}
newtexts={}
for name,para in paras.items():
 p=R/name;parts=p.read_text().split('\n\n',2);assert len(parts)==3 and parts[1].startswith('E102'),name;newtexts[p]=parts[0]+'\n\n'+para+'\n\n'+parts[2]
sp=R/'s-experiment.md';marker='|---|---|---|---|\n';assert marker in newtexts[sp] and '| E102 ' not in newtexts[sp]
newtexts[sp]=newtexts[sp].replace(marker,marker+'| E102 统一span+batch4方法比较 | NSG/hard/soft/GATE各新旧内核，Web36点108plain及四集64一致性 | 2296000search；共同内核收益与入口差异分列，生产保持 | [95 共享优化公平比较](experiment_history/95_shared_span_batch4_comparison.md) |\n',1)
hp=R/'experiment_history/README.md';t=hp.read_text();marker='|---|---|\n';assert marker in t and '95_shared_span_batch4' not in t
newtexts[hp]=t.replace(marker,marker+'| [95 统一优化后的方法比较](95_shared_span_batch4_comparison.md) | E102统一span+batch4用于NSG、GT10、GATE，新旧36配置108plain，四集一致性及公平方法差异 |\n',1)
snap=D/'reviews'/('closeout_before_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));snap.mkdir()
for p in newtexts:
 dest=snap/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
for p,t in newtexts.items():p.write_text(t)
card=f'''# E102：共享span+batch4的统一方法比较

用户在E101之后要求“NSG、GT10、GATE都应用之后测试一下”，本轮补齐共同优化后的NSG基线，区分实现收益与入口方法收益。{headline}

四种入口策略使用同一E101 span+batch4研究内核、同一冻结图和向量storage，原入口模型/路由小图保持。NSG为项目固定单入口，GT10-hard/soft为原画像三入口，GATE为原修正标签模型的三入口，不将其改称原生Faiss搜索。每种方法同时测E99 current；HNSW作同轮完整图参照。新内核未合入生产API/trace，默认Web软/Y硬保持。

WebVid完整10K query，K1/L96、K100/L100、K1/L800、K100/L1250，36配置各warm1+plain3+count1，1800000次搜索。CPU15，进程及数值库线程1，方法串行，完整路由/search/output计时，GT、加载、校验、写盘外置。所有warm/plain输出和count逐query NDC对齐E99；新count直接转发Faiss真实batch4，不拆回scalar。所有180份raw文件独立哈希与GT评分验收。

16项方法内新旧平均QPS变化{min(allg):+.2f}%至{max(allg):+.2f}%，全部原始三轮范围保留。高预算优化后hard {hard['qps_mean']:.2f}QPS/{hard['recall']*100:.4f}%，soft {soft['qps_mean']:.2f}/{soft['recall']*100:.4f}%，GATE {gate['qps_mean']:.2f}/{gate['recall']*100:.4f}%，NSG {new['qps_mean']:.2f}/{new['recall']*100:.4f}%。同L质量/时间差不能称等Recall加速，四点不能替代完整前沿；小差异须结合重复范围。公共优化收益不能归为GT10独有方法收益。

{gt_readout}一种与结果相符但未经独立因果消融确认的解释是：有限预算下入口选择更关键，预算增大后固定入口NSG能通过充分探索缩小差距。不能用公开点重新挑模型或将此解释写成已证明机制。

主性能之后串行重做其它四集完整10K/10K/10K/1K、四入口×四预算的真实batch4 count，496000次，{compat}；该阶段0正式QPS。内核与E101逐字相同，继承6480配对普通及ASan/UBSan结果，本轮新合成搜索0。查询总2296000，无训练、新图、新GT、LAION、Recall@10或新held-out；当前公开query已有历史曝光。

修改前Git备份8afd61cd5dae388f15e26890ce75109ffffd0f2f，原main/index、ACSG源和库、旧图/模型/结果均保持。运行成本、输入/源码身份、逐轮指标和失败保留规则见独立报告。本轮验收完成，不自动扩网格或部署。

[报告与图](../{link}/report.md) · [协议](../{link}/protocol.md) · [指标](../{link}/results/metrics.csv) · [共同内核的方法差异](../{link}/results/shared_kernel_comparison.csv) · [输入身份](../{link}/reviews/assets.json) · [最终验收](../{link}/reviews/final_review.json)
'''
(R/'experiment_history/95_shared_span_batch4_comparison.md').write_text(card)
print('Root docs and history card 95 synchronized')
