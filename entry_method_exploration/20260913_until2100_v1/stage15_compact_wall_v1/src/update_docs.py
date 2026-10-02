"""One-shot E74 documentation and immutable artifact seal; no queries."""
from common import *
assert read(O/'reviews/verification.json')['status']=='PASS'
assert read(O/'reviews/independent_verification.json')['status']=='PASS'
assert all(j['status']=='COMPLETE' for j in read(O/'logs/jobs.json'))
history=R/'experiment_history/63_compact_wall.md'
assert not history.exists()
body=(O/'assessment.md').read_text()+'\n\n'+(O/'report.md').read_text()
import re
def relocate(match):
    target=match.group(1)
    if target.startswith(('/', 'http', '#')):return match.group(0)
    return ']('+os.path.relpath((O/target).resolve(),history.parent)+')'
history.write_text(re.sub(r'\]\(([^)]+)\)',relocate,body))
p=R/'s-experiment.md';t=p.read_text();pos=t.index('| E73 同hub')
t=t[:pos]+'| E74 精简画像完整开发wall | compact/fullmode及规定基线、同批五L五轮 | `COMPLETE_DEVELOPMENT_WALL_VERIFIED`；55点275wall，Y局部前沿信号、Web损伤，无稳定整体结论 | [63 精简wall](experiment_history/63_compact_wall.md) |\n'+t[pos:]
t=t.replace('当前最近完成记录为E73同hub重复画像精简','当前最近完成记录为E74精简画像完整开发wall')
marker='## 3. 容易误读的版本与证据\n'
t=t.replace(marker,marker+'\nE72协议列有“不足3hub拒绝”合成负例，但实际只测引用计数下溢；运行时有检查不等于已覆盖。原封存保持，见[独立更正](entry_method_exploration/20260913_until2100_v1/reviews/e72_synthetic_scope_correction_session5.md)。E73/E74使用普通variable画像路径，不含distinct回调。\n')
p.write_text(t)
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n- [63 E74 精简画像完整wall](63_compact_wall.md)：55点275轮，Y局部召回/失败及描述性前沿正值，Web损伤，91个失败转换query；未最终验证。\n')
(R/'summary.md').write_text('''# ACSG 当前结果摘要

2026-09-13，第5串行会话完成E72–E74。精简多画像在Yandex保留局部前沿信号，尚未形成稳定整体改善或默认替换结论。E74已完成规定基线和fullmode/compact同批55点、275轮单线程完整wall；整日21:00目标未完成，E34晚间最终仍待执行。

精简仅去掉同hub字节完全相同画像，Web2445→1771、Y2463→2067，真实H815/821不变，每hub完整max评分集合保持；普通重建小图改变近似遍历，仍ef10/7slot去重3入口→原NSG。

| E74历史开发2048，相对匹配P10 | L64/128/256/400/800净命中变化 | 零命中失败净新增 | QPS中位变化% |
|---|---|---|---|
| WebVid（GT10-soft） | +9/−23/+2/+28/+2 | +2/+6/0/−1/+1 | −1.44/−.81/−.53/−.60/−.15 |
| Yandex（GT10-hard） | +99/+59/+38/+1/+15 | −10/−7/−4/−1/0 | −1.56/−.96/−1.20/−.04/−.19 |

两集十个QPS五轮交叉范围均跨零（不是置信区间）。Y共同Recall三个内部点的log-QPS插值+1.873/+2.455/+2.965%，只保留为描述性开发前沿信号，不称实测等Recall提速或独立泛化。Web L128召回−.1123pp且失败+6，明确保留损伤。相对完整mode，Y四L召回正/L800负；不能将节点减少比例当速度增量。

E73完整aux7952原门保持：Y相对P +120命中/失败−13、对fullmode+71/−9，两半均正；Web对P−59/失败+11、对fullmode+47/−2，未过门。E72 distinct10双集接续门失败，保留Y局部质量正与比mode30低的路由NDC，该版本停止且0QPS；其合成“不足3hub拒绝”未实际覆盖，独立更正保留原封存。E66/E70/E71历史结论不由本开发子集回写。

E74保存91个独立失败转换query、174个跨L事件及455个五L格。Y row2769全零变8/9/10/10/10，row3846全10变全零；Web row3524全零变全7，row2391变全零。图每集展示24例，CSV全量保留。失败严格零GT10命中，成员找回/丢失与逐query净值另列。

E74新增789360 NSG/645120 HNSW，0构图/训练/GT；原生1101.761秒，275轮纯完整wall合计772.446秒。会话E72–E74共1080816 NSG/936000 HNSW/2实际小图，合成另4图/512HNSW；编译42.049秒，精简.031秒、构图.348秒，继承E66画像训练30.286秒及早期GT成本未重测、不记零。CPU15/实际进程和数值库1线程，方法串行；112640集合/mask、880原kernel、全部slot/源图/旧返回和计时轮换独立核验通过，主监督13:56另独立验收原物/计时/五图。

P-fit含旧train/monitor，cal/audit/aux均历史暴露，辅助选择计训练；E74的2048包含于已用aux7952，E34最终与held-out今日未进入。旧产物与source_before/root_after均保留。下一方向与晚间冻结/最终评估门见s-target，不由这些诊断直接宣告方法成功。

[完整报告](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/report.md) · [判断](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/assessment.md) · [QPS–Recall](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/figures/recall_qps.png) · [失败query图](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/figures/failure_query_cases.png) · [下一阶段](s-target.md)。
''')
(R/'s-target.md').write_text('''# ACSG 下一阶段目标与接续

2026-09-13，第5串行会话E72–E74已完成，正在安全交接，整日21:00目标未完成。唯一写入/实验者，不开并行CLI或子代理；后继由监督器串行开启。详细方法、控制、预算与停进门见[会话5接续设计](entry_method_exploration/20260913_until2100_v1/next_stage_design_session5.md)。

1. 保留E73/E74 Yandex局部收益，停止E72 distinct10本版本。下一项优先检验“精简重建时保留原slot随机层级”单个离线构图控制：先0ANN核对原图层级与随机流；通过后再以独立协议/两新小图比较P10、compact及新控制，固定aux7952/两半/zero失败门。源码level=0不能强制零层，不能直接照名调用；不得扫seed/宽度，原层级恢复不代表原邻接恢复。该方向尚未运行，不写入已实现API。
2. WebVid完整辅助质量门失败、E74 L128进一步损伤，表示问题仍在。必要时沿E66/E69原证据只做父子支持/完整评分三入口真实损益的缓存分析；监督已完成compact排序/效用分组，不重复同一诊断。事后排名关联不是单画像因果信用或在线门控。无可检验实质区别不扩网格。
3. 晚间20:00停新训练、20:40停新增query、21:00交付。只用已暴露开发反馈先冻结best_all与真实best_new；inventory_v5共32配置保留旧24，E74展示compact不是最终全局重选。E34历史validation2000只用于最终对照，不回流训练/选择，held-out不自动打开。规定基线和候选同机同批五L五轮完整wall，不能拼不同批次曲线。

所有ANN CPU15/实际threads1、OMP/BLAS/MKL等1线程；完整路由/去重/原NSG/output在独立wall内，GT/count/hash/JSON/build/load在外。原base/rawIP/NSG/GT/真实H815/821固定。画像/构图学习离线；fit/旧train/monitor/cal/audit/aux历史暴露，辅助选择计训练。每阶段source_before/root_after，新版本预算<=64MiB并现场检查累计free>=7GiB、预留晚间，禁止清理旧产物。

[E74报告](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/report.md) · [campaign状态](entry_method_exploration/20260913_until2100_v1/state.json) · [监督备注](/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md)。
''')
p=R/'spec.md';t=p.read_text()
t=t.replace('两集singleton及旧三控制在主7952全部恢复；合成tie/非同一内外ID/引用移除/复位通过，全96960返回评分/384原kernel通过。','两集singleton及旧三控制在主7952全部恢复；合成tie/非同一内外ID/引用移除/复位通过，全96960返回评分/384原kernel通过。协议列的不足3hub拒绝没有实际执行，末尾仅测引用下溢；见[独立覆盖更正](entry_method_exploration/20260913_until2100_v1/reviews/e72_synthetic_scope_correction_session5.md)，原E72封存不改。')
t+='''

## 精简画像完整wall与候选身份（E74，2026-09-13）

[prepare](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/src/prepare.py)逐字复制E73 evaluator，引用冻结compact/fullmode及规定基线小图，历史开发2048五L五轮。没有新编译/构图/训练/GT，45个方法点plain源图加载和45次count加载，0物理小图副本。variable 1–3槽/7slot去重/原kernel和完整计时合同沿E73，不含E72 distinct回调。

[analyze](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/src/analyze.py)和[独立复核](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/src/independent_verify.py)核验112640集合/mask、40960整行slot距离、55点275wall轮换/恒等、原基线/完整mode/L128回归。route与graph分项wall未另测为null+reason；772.446秒是纯275次完整独立wall合计，1101.761秒native另含load/count/I/O，不能互换。failure_query_summary保存91条独立query的全五L共455格，174跨L事件分列；图每集24例而全表不截断。

[candidate_inventory_v5](entry_method_exploration/20260913_until2100_v1/candidate_inventory_v5.json)逐项保留v4旧24配置，新增6个E72 distinct配置及2个E73 compact配置，共32且包含控制；保存对应evaluator/config/W/graph/mapping/tie/physical/uniqueH/ef/variable/distinct合同。E74展示best_new=compact不代表晚间最终选择；E72缺失合成负例链接随候选保存。任何图/层级/映射/画像/ef/数据或kernel改变必须新评测，本节不将后继层级控制设计写为现有功能。
'''
p.write_text(t)
after=O/'reviews/root_after';after.mkdir()
for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:
    shutil.copy2(R/x,after/x.replace('/','__'))
dump(O/'reviews/figure_review.json',dict(status='PASS',viewed_by='session5',figures=['recall_qps','failure_qps','three_metrics_by_L','paired_deltas','failure_query_cases'],all_five_viewed=True,axes_units_legends_and_layout=True,development_scope_and_24_display_full_91_csv=True,supervisor='review_080 also viewed all five'))
check(O/'reviews/prequery_freeze.json');check(O/'reviews/preanalysis_addendum_freeze.json');resources()
seal=O/'reviews/final_artifact_freeze.json';assert not seal.exists()
paths=sorted(p for p in O.rglob('*') if p.is_file())+[history]
dump(seal,dict(status='FROZEN_E74_COMPLETE',epoch=time.time(),files=[identity(p) for p in paths]))
print('SEALED_E74',len(paths),sum(p.stat().st_size for p in paths))
