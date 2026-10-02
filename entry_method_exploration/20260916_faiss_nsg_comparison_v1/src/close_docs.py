import pathlib,json,shutil,datetime
D=pathlib.Path(__file__).resolve().parent.parent;R=D.parent.parent
read=lambda p:json.loads(p.read_text())
s=read(D/'results/summary.json');a=read(D/'reviews/results_audit.json');compat=read(D/'compatibility/analysis.json');assert a['status']=='PASS'
assert read(D/'reviews/figures_visual_check.json')['status']=='PASS'
assert read(D/'reviews/actual_batch4_count_audit.json')['status']=='PASS'
rows=s['metrics'];pairs=s['paired_speedups'];combo=[x for x in pairs if x['variant']=='GT10-span-batch4' and x['baseline']=='GT10-current']
def row(v):return next(x for x in rows if x['variant']==v and x['K']==100 and x['L']==1250)
cur,best,native,h=[row(v) for v in ['GT10-current','GT10-span-batch4','Faiss-native','HNSW']]
link='entry_method_exploration/20260916_faiss_nsg_comparison_v1'
range_text=f'{min(x["speedup_percent"] for x in combo):+.2f}%至{max(x["speedup_percent"] for x in combo):+.2f}%'
mismatch=sum(x['mismatched_configurations'] for x in compat['datasets'])
compat_text='其它四集64配置的输出ID/距离bits/入口/逐query NDC全部与E99一致' if not mismatch else f'其它四集64配置中{mismatch}项存在数值或返回不一致，不能视作通用无损替换'
headline=f'E101于2026-09-16完成内置Faiss1.9.0同图比较：WebVid四点、十版本、120轮plain/2000000search；GT10的span+batch4组合相对当前E99四点QPS变化{range_text}，各GT10控制返回和NDC相同。高预算K100/L1250组合{best["qps_mean"]:.2f}QPS、Recall@100 {best["recall"]*100:.4f}%，当前GT10 {cur["qps_mean"]:.2f}QPS；原生Faiss {native["qps_mean"]:.2f}QPS/{native["recall"]*100:.4f}%。另做80000次真实batch4计数核验及496000次四集一致性回归，{compat_text}。'
common=f'[报告与图]({link}/report.md) · [复盘94](experiment_history/94_faiss_nsg_comparison.md)。'
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');snap=D/'reviews'/('closeout_before_'+stamp);snap.mkdir()
for name in ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:
 p=snap/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/name,p)
texts={
 'summary.md':headline+' '+common+' 本轮是独立研究候选，生产源码/默认仍E99、Web软/Y硬；没有重训或新构图，不声称完整前沿或四集新QPS。修改前备份`dba6986e`。',
 'spec.md':'E101独立比较工具已验收：compare.cpp用非拥有视图把同一storage/邻接交给原生Faiss IndexNSG，保留其入口邻居+随机填满L初始化；current实际链接E99库。kernels.hpp实现研究用最小多入口及core/span/预取过滤/batch4，不接入生产。6480组合普通及新代码ASan/UBSan回归、WebVid40点120轮及计数核验完成；原生IP符号/ID转换在plain计时内，native count与自己的public API输出核验，其余与E99对齐。compatibility.cpp真实转发底层batch4，另做496000search，'+compat_text+'。'+common+' 匹配结果只存核验，失败保存raw；新候选的生产接入、trace及通用数值回退尚未实施。',
 's-target.md':'E101比较任务已完成，'+headline+' 下一步优先按本轮收益与跨集兼容性选择小范围共享内核落地；span和batch4应分别保留控制，不能直接用库替换推断加速。预取过滤、纯代码精简的价值按报告实测范围判断，不追加网格追逐小差异。原生Faiss初始化不同，单独命名；后继生产接入需补API/trace、特殊值/未知DC、生命周期和全部共享方法公平性能验收。当前生产仍E99，无自动部署、训练或下一轮查询队列。'+common,
 's-experiment.md':headline+' '+common+' 合计2576000真实搜索，另有两次12960合成搜索；图和模型保持，原生库结果不覆盖历史NSG标签。'
}
replacements={}
for name,para in texts.items():
 p=R/name;text=p.read_text();parts=text.split('\n\n',2)
 assert len(parts)==3 and (parts[1].startswith('E101') or (name=='s-target.md' and parts[1].startswith('用户已授权E101'))),name
 replacements[p]=parts[0]+'\n\n'+para+'\n\n'+parts[2]
for p,text in replacements.items():p.write_text(text)
p=R/'s-experiment.md';text=p.read_text();marker='|---|---|---|---|\n';assert marker in text;text=text.replace(marker,marker+'| E101 原生Faiss同图与实现控制 | Web四点十版本120plain；另四集共享入口兼容性 | 2576000search；组合本地提速，生产默认保持，跨集边界见报告 | [94 库与内核比较](experiment_history/94_faiss_nsg_comparison.md) |\n',1);p.write_text(text)
p=R/'experiment_history/README.md';text=p.read_text();marker='|---|---|\n';assert marker in text;text=text.replace(marker,marker+'| [94 原生Faiss与实现控制](94_faiss_nsg_comparison.md) | E101同图库基线、空槽/预取/batch4十版本40点120plain，四集64配置兼容性，生产保持E99 |\n',1);p.write_text(text)
card=f'''# E101：原生 Faiss NSG 同图比较与优化价值

用户要求比较库与项目实现、判断哪里值得优化。本轮完成，{headline}

本轮原生基线为内置Faiss1.9.0，直接调用IndexNSG.search，借用同一storage和邻接，不重构图；它使用入口邻居加随机点填满L，与项目固定一个/GT10三个初始点不同。native不能与项目版本强求返回一致，也不能只按同L时间判断。当前NSG/GT10实际链接E99库。研究用minimal/core及span、prefetch-filter、batch4、span-batch4是独立适配，不冒称原生库；所有代码和模型原件保持。

WebVid锁定K1/L96、K100/L100、K1/L800、K100/L1250，10K原public query，CPU15/单线程/方法串行。每配置warm+3plain+count，共40点120plain/2000000search；6480组合差分普通与ASan/UBSan均通过。每个GT10控制的ID、距离bits、入口与逐query NDC同E99；原生返回与自己的public API对齐并检查合法性，GT独立严格ID评分。少NDC不必更快，而相同NDC下批量计算与邻接组织可以改变wall；收益不能全归于SIMD，也不能把空槽比例当节省时间。

主count的batch4默认scalar转发局限另以80000次真实batch4包装核验补齐，原计时不改，细节见补充协议。

高预算GT10组合从{cur['mean_ms']:.4f}降至{best['mean_ms']:.4f}ms/query，Recall不变；完整HNSW为{h['qps_mean']:.2f}QPS、Recall@100 {h['recall']*100:.4f}%。span额外{ s['layout']['span_bytes'] }字节辅助空间，加载阶段生成。最小适配/预取过滤等全部正负点与三轮波动保留，未按最好一轮选结论。主比较查询阶段{s['cost']['seconds_excluding_load']/60:.3f}分钟，精确加载/身份核验成本见报告。

按用户之前的四集一致性范围，预锁相同组合在Yandex/Deep/SIFT/GIST完整10K/10K/10K/1K query、各四预算和NSG/hard/soft/GATE真实入口核验，计数包装真正转发Faiss batch4。另496000search/64配置，{compat_text}。完整成功与失败、距离bits/ID/NDC差异均保留；该阶段0正式QPS，不能宣称四集提速。

未训练、构图或生成GT，未打开新的held-out，没有生产替换或默认更改。修改前Git备份dba6986eb9baa645e9ad1231f9d112bb06550c5d，main/index保持。后续生产改造须结合跨集数值边界，补trace、特殊值与未知DC回退，再公平验证全部共享NSG方法；本轮不自动追加参数网格或部署。

[报告](../{link}/report.md) · [主协议](../{link}/protocol.md) · [兼容性补充](../{link}/compatibility/protocol.md) · [40点指标](../{link}/results/metrics.csv) · [控制收益](../{link}/results/paired_speedup.csv) · [兼容性分析](../{link}/compatibility/analysis.json)
'''
(R/'experiment_history/94_faiss_nsg_comparison.md').write_text(card)
print('Synchronized four root docs and history card 94')
