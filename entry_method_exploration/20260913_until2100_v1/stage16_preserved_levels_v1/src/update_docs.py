from common import *
import csv
assert read(O/'reviews/verification.json')['status']=='PASS';gate=read(O/'results/gate.json');cost=read(O/'results/cost.json');paired=list(csv.DictReader((O/'results/paired.csv').open()))
history=R/'experiment_history/64_preserved_compact_levels.md';assert not history.exists();body=(O/'report.md').read_text()
for prefix in ['results/','figures/','reviews/','protocol.md']:body=body.replace(']('+prefix,'](../entry_method_exploration/20260913_until2100_v1/stage16_preserved_levels_v1/'+prefix)
history.write_text(body)
p=R/'s-experiment.md';t=p.read_text();pos=t.index('| E74 ');t=t[:pos]+'| E75 精简保留原随机层级 | 固定compact画像/顺序，原slot随机流跳过、两新图、aux7952 | `COMPLETE_PRESERVED_LEVEL_DEVELOPMENT`；全部层级恢复，质量接续门见历史64，97152 NSG/0QPS | [64 层级保留](experiment_history/64_preserved_compact_levels.md) |\n'+t[pos:];t=t.replace('当前最近完成记录为E74精简画像完整开发wall','当前最近完成记录为E75精简原层级控制');p.write_text(t)
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n- [64 E75 精简保留原层级](64_preserved_compact_levels.md)：随机流/完整保留层级验收及真实NSG效用、固定接续门。\n')
lines=['# ACSG 当前结果摘要','','2026-09-13，第6串行会话完成E75精简原层级控制。新图全部保留节点恢复原full随机层级，旧P/compact返回逐位恢复；方法判断以真实辅助NSG效用为准。整日21:00目标未完成，晚间E34最终仍未进入。','','| 数据 | 新图对P：净命中/失败净新增 | 新图对compact：净命中/失败净新增 | 原门 |','|---|---|---|---|']
for ds in DS:
 rr=[next(x for x in paired if x['dataset']==ds and x['reference']==ref and x['split']=='all') for ref in ['baseline10','compact10']]
 lines.append('| '+('WebVid' if ds==DS[0] else 'Yandex')+' | '+' | '.join(f"{int(x['net_hits']):+d}/{int(x['failure_change']):+d}" for x in rr)+' | '+('通过' if gate['datasets'][ds]['passed'] else '未通过')+' |')
lines+=['','层级控制固定Web1771/Y2067画像、H815/821、原seed/顺序/ef10/7slot去重3入口/NSG/rawIP；删除slot仍消耗原随机数。普通精简改变207/235个保留节点层级、入口对应原slot222/204，新图层级全部恢复且入口回原slot166。邻接仍改变，不能称恢复原full拓扑或性能。', '', 'E75原门要求同时胜P与compact、固定两半非负且失败不增。'+('至少一集通过，下一独立E76同批完整wall检验成本并保留另一集迁移对照。' if gate['wall_measurement_allowed'] else '双集未过，停止本层级控制，不追加其wall或扫seed/ef。')+' 辅助反馈计训练，NDC不是QPS。','',f"E75新增97152 NSG/96960 HNSW/2真实小图，合成另4图/512 HNSW；构图{cost['micro_graph_build_seconds']:.3f}秒，四native{cost['native_job_seconds']:.3f}秒。48480集合/mask与47712逐行set评分、31808旧控制回归、192原kernel和全部七slot/图字节/层级验收通过。首次编译失败原件及修订保留，0额外查询；无新画像训练/GT，继承成本未重测不记零。",'', 'E73/E74 Yandex精简多画像局部前沿信号保留：E74对P五L净命中+99/+59/+38/+1/+15、失败−10/−7/−4/−1/0；QPS五轮范围均跨零、描述性插值+1.9%～3.0%，尚未稳定改善或默认替换。Web L128损伤−23命中/失败+6保留。E72仍按旧门停止，合成覆盖更正不抹去。','', 'P-fit包含旧train/monitor，cal/audit/aux均历史暴露。当前aux7952不是盲集；E34历史validation2000只留晚间冻结后最终对照，held-out未打开。全部ANN串行CPU15/实际进程及数值库1线程，任务terminal0后评分；旧字节与source_before/root_after保留。','','[E75报告](entry_method_exploration/20260913_until2100_v1/stage16_preserved_levels_v1/report.md) · [E74完整QPS与失败报告](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/report.md) · [下一阶段](s-target.md)。']
(R/'summary.md').write_text('\n'.join(lines)+'\n')
next_text='另建E76同批五L五轮完整wall，原NSG/Fast30K/GT10-hard/Web匹配soft/compact及新层级候选同批；预先固定两数据集，未过门者只作迁移对照。' if gate['wall_measurement_allowed'] else '本层级候选双集未过接续门，停止其wall/seed/ef扩展；下一步先沿E66/E69既有证据复盘Web模式损伤，再锁定有明确区别的表示控制。'
(R/'s-target.md').write_text('# ACSG 下一阶段目标与接续\n\n2026-09-13，第6串行会话E75完成；整日21:00目标未完成。唯一写入/实验者，不开并行CLI或子代理，本会话15:21:01前安全交接。\n\n1. '+next_text+' 当前原层级控制全部节点层级与原slot身份已验收，不能据此推导效用或QPS。\n2. 保留E73/E74 Yandex精简局部信号与Web损伤，E72旧门及覆盖更正保持。Web exact-mode低于exact-P是已测事实，单靠更准排名不能修复全部表示损伤；必要的缓存支持分析另立0ANN版本，不把组合收益归给单一画像。\n3. 晚间20:00停新训练、20:40停新增query、21:00完整报告；开发先冻结best_all和实际best_new，再开E34历史validation2000，不能回流训练/选型，held-out不自动打开。规定基线和候选同批五L五轮完整wall与三指标/失败query图，不拼旧批次。\n\n所有ANN CPU15/threads1/数值库1线程串行，固定原base/NSG/rawIP/GT/H815或821。fit/cal/audit/aux历史暴露，辅助选择计训练。阶段source_before/root_after封存；新输出<=64MiB并现场free>=7GiB，保留晚间空间，不清理旧产物。\n\n[E75报告](entry_method_exploration/20260913_until2100_v1/stage16_preserved_levels_v1/report.md) · [campaign状态](entry_method_exploration/20260913_until2100_v1/state.json) · [监督备注](/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md)。\n')
p=R/'spec.md';p.write_text(p.read_text()+'''

## 精简图保留原slot随机层级（E75，2026-09-13）

[build_levels](entry_method_exploration/20260913_until2100_v1/stage16_preserved_levels_v1/src/build_levels.cpp)提供inspect/build/synthetic三个独立入口。inspect不创建HNSW图，用同std随机流恢复原full序列化external slot层级；build对原slot顺序中删除项调用同一图getRandomLevel一次，保留项普通addPoint自行消费一次，避免level=0参数不覆盖的陷阱。W/mapping/tie/保留顺序完全引用E73，新物理图每节点层级等于原slot层级，包括零层；源最高入口删除的合成路径实际覆盖，入口由剩余节点合法决定。原hnswlib/NSG不改。

在线直接引用E73同SHA evaluator及普通variable 1–3槽/ef10/7slot去重3入口，原kernel与计时合同不变。全aux原P/compact返回恢复、plain/count/原kernel、独立图W/label/邻接和层级解析已验收。原层级恢复不保持邻接，也不等于效用改善。改变原slot/随机流/图/画像/映射/ef或query/GT/NSG身份须独立重建/重测；所有源图与失败编译原件保留。方法结果见summary/历史64。
''')
s=read(C/'state.json');s.update(status='SESSION6_E75_COMPLETE',stage='E75_COMPLETE',stage16_status='COMPLETE_PRESERVED_LEVEL_DEVELOPMENT',total_new_NSG=4316756+97152,total_HNSW=4729056+96960,total_builds=350,session6_NSG=97152,session6_HNSW=96960,session6_builds=2,session6_synthetic_builds=4,session6_synthetic_HNSW=512,native_pids=[],next_action=next_text);dump(C/'state.json',s)
(C/'handoff.md').write_text('# 第6串行会话进行中\n\nE75完成，整日目标未完成；15:21:01前安全交接。'+next_text+'\n\n当前新增97152 NSG/96960 HNSW/2真实图，合成4图/512HNSW。全部native exit0、无遗留任务；E34最终和held-out仍未打开。\n\n[E75结果和固定门](stage16_preserved_levels_v1/report.md)。\n')
after=O/'reviews/root_after';after.mkdir()
for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:shutil.copy2(R/x,after/x.replace('/','__'))
check(O/'reviews/prequery_freeze.json');resources();freeze(O/'reviews/final_artifact_freeze.json',[p for p in O.rglob('*') if p.is_file() and p.name!='final_artifact_freeze.json']+[history]);print('SEALED_E75')
