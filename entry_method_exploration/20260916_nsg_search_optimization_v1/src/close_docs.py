"""Run after report and manual figure review; publish verified E99 conclusions locally."""
import pathlib,json
D=pathlib.Path(__file__).resolve().parent.parent;R=D.parent.parent
v=json.loads((D/'reviews/report_values.json').read_text())
assert json.loads((D/'reviews/figures_render_check.json').read_text())['status']=='PASS'
assert json.loads((D/'reviews/results_audit.json').read_text())['status']=='PASS'
base='entry_method_exploration/20260916_nsg_search_optimization_v1'
soft=next(x for x in v['web_hnsw_comparison'] if x['K']==100 and x['L']==1250)
common=f'E99于2026-09-16完成共享NSG实现优化：WebVid四个预算、四种NSG入口方法的新旧对照，QPS变化{v["gain_min"]:+.2f}%至{v["gain_max"]:+.2f}%；五集100个组合的返回ID/距离bits/入口和逐query NDC均与E97一致。'
key=f'WebVid K100/L1250优化后soft为{soft["soft_qps"]:.1f} QPS、Recall@100 {soft["soft_recall"]*100:.4f}%；同轮完整HNSW为{soft["hnsw_qps"]:.1f} QPS、{soft["hnsw_recall"]*100:.4f}%。'
links=f'[报告]({base}/report.md) · [Recall–QPS图]({base}/figures/webvid_recall_qps.png) · [复盘92](experiment_history/92_nsg_search_optimization.md)。'
intro={
'summary.md':common+key+' '+links+' 生产源码已优化、独立优化库已验证，原构建库保持；入口模型默认不变。其他四集仅一致性回归，无新QPS结论。本轮2,296,000次真实查询、108轮单线程plain，无训练/新构图；修改前6115个文件已Git备份到`2739b09a`。',
's-target.md':common+' 用户授权的WebVid重点验证、其他四集一致性、绘图分析和修改前Git备份均已完成。'+links+' 本轮仅四个预锁预算，不能代替优化后完整前沿或跨五集吞吐结论；不追加网格、LAION、Recall@10或重训。生产源和可独立链接的优化库已交付，原构建库可继续对照。当前E99无待恢复的查询任务，默认仍Web软/Y硬。',
'spec.md':f'E99已在`ACSG/ACSG.cpp`与`ACSG/detail/CandidatePool.h`实现query局部邻居预取及有效前缀复制。FlatCodes视图从当前DistanceComputer获取，支持NegativeDistanceComputer解包；未知DC只预取visited。保留完整L的原二分定位/等距顺序/重复ID规则，非有限或FLT_MAX分数退出压缩复制。API/对象布局/距离算术不变。`{base}/bin/libACSG.optimized.a`可独立链接，本轮benchmark实际链接该库；原`build/ACSG/libACSG.a`未覆盖。35,856候选池用例、8,656合成查询的普通及新内核ASan/UBSan回归通过；五集100组合、500raw文件及108轮plain通过，source/config SHA固定。'+links,
's-experiment.md':common+' 先Git备份`2739b09a`，再生产源码优化；E98短池控制的等距反例已修复，E98旧证据保留。Web四点公平比较NSG/hard/soft/GATE旧新内核和完整HNSW，其他四集只做完整query回归，原模型默认与历史产物不变。'+links
}
for name,p in intro.items():
 path=R/name;text=path.read_text();paragraphs=text.split('\n\n');hits=[i for i,s in enumerate(paragraphs) if s.startswith('E99进行中')]
 assert len(hits)==1,(name,hits);paragraphs[hits[0]]=p;path.write_text('\n\n'.join(paragraphs))
history=f'''# E99：NSG邻居预取与候选池复制优化

{common}{key}

用户选择先重点验证WebVid Recall@1/100、其他四集一致性，并要求修改前Git备份。备份分支`backup/pre-nsg-optimization-20260916_103846`、提交`2739b09a67f3ca0b6f145d43690d36345df3182c`保存6115个源码/脚本/配置/文档，全部回读一致；main和原index保持。大型数据/模型/构建产物原位保护。

## 机制与修正

将E98的预取信号实现到共享NSG源代码：每query取得当前存储视图，提前一个邻居预取visited及向量首cache line；不更改Faiss算术或入口策略。候选插入沿用完整L的原定位/重复ID逻辑，仅减少未满池的空槽复制，非有限或sentinel分数退回完整复制。原API/对象布局不变，原库保留，独立优化库可链接。

E98整体缩小插入函数K的实现存在等距顺序反例，已由35,856个候选池差分用例定位并规避。8,656次合成图查询验证返回bits、距离调用顺序和trace，覆盖IP/L2/边界/visited轮回。ASan/UBSan检查新内核及测试通过。初次trace validator对NaN的JSON数值比较误报，已保留失败日志并修正测试比较，生产代码未因此改变。

## 测量与证据

WebVid完整10K query，K1/L96和800，K100/L100和1250；同一进程/同一邻接和storage内存，旧新独立scratch，warmup+三轮plain+count。四种NSG方法都得到同一优化，完整HNSW作同轮参考；CPU15，进程和数值库1线程，方法串行。108轮plain计完整route+search wall，QPS为三次N/wall均值。

Yandex、Deep、SIFT、GIST完整公开query，K1/L96和1250、K100/L100和1250，四方法各一次count。计数包装器显式暴露原FlatCodes视图，实际覆盖向量预取。500份返回/入口/NDC文件逐一比对E97，全部一致；其余四集不声称新吞吐收益。启动真实搜索前把E97中不存在的K1/L100改为既有L96，未增点或按结果调参。

## 成本与边界

合计2,296,000次真实search、108轮plain，含加载主调度{v['measurement_minutes']:.2f}分钟。无新训练、GT、索引构建、LAION或Recall@10；Git备份/编译/合成回归/后处理另计。只有Web四个预算点，不构成完整前沿和跨集性能结论；公开测试已有曝光，不称盲测。入口模型默认Web软/Y硬保持，生产源码已优化，旧库及E97/E98结果不覆盖。

[完整报告](../{base}/report.md) · [协议](../{base}/protocol.md) · [全部CSV](../{base}/results/metrics.csv) · [源代码补丁](../{base}/source_changes.patch) · [核验](../{base}/reviews/results_audit.json) · [源码及恢复说明](../{base}/src/README.md)
'''
(R/'experiment_history/92_nsg_search_optimization.md').write_text(history)
p=R/'experiment_history/README.md';text=p.read_text();link='[92 NSG实现优化](92_nsg_search_optimization.md)';assert link not in text;p.write_text(text+'\n- '+link+'：E99，先Git备份、预取与保持等距顺序的有效池复制；Web四点新旧对照、其他四集全query一致性。\n')
print('ROOT_DOCS_AND_HISTORY_UPDATED')
