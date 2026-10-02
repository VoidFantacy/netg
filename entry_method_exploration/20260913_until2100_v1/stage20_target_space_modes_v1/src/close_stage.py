from pathlib import Path
import json,shutil,time,hashlib
R=Path('/data/netg/ACSG');C=R/'entry_method_exploration/20260913_until2100_v1';O=C/'stage20_target_space_modes_v1'
r=lambda p:json.loads(p.read_text())
cost=r(O/'results/cost.json');gate=r(O/'results/gate.json');offs=r(O/'results/offline.json');union=r(O/'results/failure_union.json')
passed=gate['wall_measurement_allowed'];report=(O/'report.md').read_text()
history=R/'experiment_history/68_target_space_modes.md';assert not history.exists()
# History is self-contained and uses original relative evidence links reanchored.
body=report.replace('](results/','](../entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/results/').replace('](reviews/','](../entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/reviews/').replace('](figures/','](../entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/figures/').replace('](../stage15_compact_wall_v1/','](../entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/')
history.write_text(body+'\n[前瞻协议](../entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/protocol.md)。\n')
p=R/'s-experiment.md';s=p.read_text();marker='|---|---|---|---|\n';entry='| E79 GT10目标空间分组 | 原A/P/Q全复现、目标/固定置换两分组、双集aux7952 | `COMPLETE_TARGET_SPACE_MODES`；'+('至少一集预锁门通过，尚无完整性能结论' if passed else '两集预锁门失败，停止本目标分组版本')+'；129536 NSG/0QPS | [68 目标空间分组](experiment_history/68_target_space_modes.md) |\n';s=s.replace(marker,marker+entry,1).replace('当前最近完成记录为E78固定图子质量范数','当前最近完成记录为E79目标空间分组');p.write_text(s)
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n- [68 GT10目标空间分组画像](68_target_space_modes.md)：E79，目标/置换对照与完整双集辅助反馈、原A/P/Q恢复及失败查询。\n')
import csv
with (O/'results/paired.csv').open() as f:rows=list(csv.DictReader(f))
brief=[]
for ds in [x['dataset'] for x in offs['datasets']]:
 rr={x['reference']:x for x in rows if x['dataset']==ds and x['candidate']=='target10' and x['split']=='all'}
 brief.append(f"| {'WebVid' if ds.startswith('web') else 'Yandex'} | {int(rr['baseline10']['net_hits']):+d} / {int(rr['baseline10']['failure_change']):+d} | {int(rr['compact10']['net_hits']):+d} / {int(rr['compact10']['failure_change']):+d} | {int(rr['permuted10']['net_hits']):+d} / {int(rr['permuted10']['failure_change']):+d} |")
summary='''# ACSG 当前结果摘要

2026-09-13，第7串行会话完成E79。GT10目标方向分组画像与固定行置换控制已经完整双集辅助查询。'''+('至少一集通过原门，只允许另立完整wall协议，尚非性能GO。' if passed else '两集均未通过预锁门，停止本目标分组版本，不选置换控制或扫参数。')+'''整日21:00目标未完成，E34晚间最终尚未进入。

原A归属、P画像、E66完整Q分区/子质量/ESS/聚合/W字节恢复。新分组按unit(sum GT10 unit target)，仍聚合原query生成子画像，原P首槽不变；去重后target画像Web1957/Y2239，置换控制1873/2239，真实H815/821/原NSG/raw-IP固定。置换同时影响支持与图，不能只归因于目标身份。

| aux7952主候选 | 对P：净命中 / 失败变化 | 对compact | 对permuted |
|---|---|---|---|
'''+ '\n'.join(brief)+f'''

完整旧收益保留/丢失、避免旧损失与新损伤、GT成员增损和原门见[E79报告](entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/report.md)。失败严格GT10零命中：完整并集{sum(x['any_zero'] for x in union.values())}个dataset/source-row，其中{sum(x['changed_zero'] for x in union.values())}个失败状态变化，全表保留入口/GT/返回ID。

E73/E74 Yandex局部信号保留：五L相对P命中+99/+59/+38/+1/+15、失败−10/−7/−4/−1/0；五轮QPS范围均跨零，约1.9%～3.0%仅描述性插值。Web L128−23命中/失败+6损伤保留。E75/E77/E78原门失败保持，默认未替换。

E79新增129536 NSG/129280 HNSW/4真实build；4新离线分组、2旧Q复现，0梯度/新GT/编译/QPS。离线{cost['offline_total_seconds']:.3f}s，构图{cost['micro_graph_build_seconds']:.3f}s，native{cost['native_job_seconds']:.3f}s含加载/count/I/O不当QPS，继承GT/P成本未重测。CPU15/进程及数值库1线程串行，四工具terminal0后独立集合评分，P/C31808行全字段回归、256原kernel与全部7slot/图身份通过。

P-fit20K含旧train/monitor；aux7952及两半已暴露且反馈计训练，cal/audit历史使用。E34最终只留冻结后对照，held-out未打开。E79在实验前另锁6.9GiB下限、64MiB上限和额外36MiB晚间/交接预留，旧版本7GiB及全部seal不改。所有主文档前后快照保持。

[E79失败查询图](entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/figures/failure_queries.png) · [E74完整QPS图](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/report.md) · [下一阶段](s-target.md)。
'''
(R/'summary.md').write_text(summary)
(R/'s-target.md').write_text('''# ACSG 下一阶段目标与接续

2026-09-13，第7串行会话E79完成；整日21:00目标未完成。唯一写入/实验者，不开并行CLI或子代理，本会话16:21:50前安全交接。

1. '''+('E79至少一集通过预锁质量门：下一步独立冻结target的双集完整开发wall，含原NSG/Fast/GT10匹配P、compact和target；同批五L五轮，不能提前称性能改善。' if passed else 'E79目标空间分组两集原门失败，停止本公式版本，不扫分组参数或改选置换控制。后续先从完整损益与支持证据确定有实质区别的新方向；无依据则完成晚间最终协议和报告准备。')+'''
2. 保留E73/E74 Yandex局部召回/失败正信号及Web损伤。所有后续方法同时报告旧收益丢失、旧损失修复与新损伤；GT几何/分组/有限oracle、NDC和同LRecall不等于端到端改善。E75/E77/E78原停止门与机制控制身份保持。
3. 晚间20:00停新训练、20:40停新增query、21:00完整报告。按已观察开发反馈预锁best_all/best_new及规则，再读E34历史validation2000，不能回流训练/选型；held-out不自动打开。原NSG/Fast/GT10匹配起点/真实新方法同批五L五轮完整wall，独立aligned集合评分、零GT10救回新增、QPS–Recall/QPS–失败率/按L三指标/失败query图齐备。

本轮资源按新前瞻协议分配：E79目录64MiB、free6.9GiB外另保留32MiB晚间与4MiB交接；旧各版本7GiB门不改。下一阶段须现场累计新输出，不复制大输入、原图或binary，不清理任何旧产物。新目标特征只在RAM处理，原NSG/raw-IP/GT/真实H固定；全部ANN CPU15/threads1/数值库1串行。

fit/cal/audit/aux及两半历史暴露，辅助选择计训练；元数据余行不证明全项目未使用。各阶段source_before/root_after和原seal保持；库存中的机制控制不自动晋升为最终新方法。E79模型已冻结、是否进入后继以原gate为准，不按晚间最终反馈改变模型。

[E79报告](entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/report.md) · [campaign状态](entry_method_exploration/20260913_until2100_v1/state.json) · [监督备注](/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md)。
''')
p=R/'spec.md';p.write_text(p.read_text()+'''

## GT10目标空间分组画像（E79，2026-09-13）

[offline](entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/src/offline.py)在P-fit20K上先完整恢复E66原A/P/Q分配/质量/ESS/聚合/W，再以t=unit(sum_GT10 unit(raw target))替换组内分组特征；目标只在RAM，原fvecs头/ID/范数校验。GT目标单位化float32、十rank和及最终unit float64，最终画像仍聚合原Q。A/Q/源行不动的固定目标行置换仅机制控制；支持与物理容量可能改变。父P、raw-prior分配和父/子门沿E66，20轮、mode0 tie，保存最后分配bits、source_rows/active轴、支持/sums/compact原slot映射；分区比较消除二元标签互换。

[prepare_queries](entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/src/prepare_queries.py)在离线验收及完整资源预算后冻结prebuild，引用E73同SHA builder/evaluator，普通构建四物理图，独立解析全W/slot标签/邻接。线上仍variable1–3画像/真实hub、ef10/7slot去重3、原NSG/rawIP；无新在线模型或kernel。原始plain/count/16原kernel、旧P/compact全字段恢复与独立集合评分沿原合同；timing_repeats0不输出QPS。

[分析](entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/src/analyze.py)保存全量/固定两半质量门、成员增损、旧收益保留与新损伤；[报告](entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/src/report.py)保留任何主/控制配置零命中的完整query并集、GT/入口/返回ID。目标定义/归属/分组/映射/图/ef/query/GT/NSG改变均须新身份与真实反馈；分组几何和NDC不可代替效用/完整wall。模型实现验收不等于门或性能通过。
''')
for n in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:shutil.copy2(R/n,O/'root_after'/n)
shutil.copy2(R/'experiment_history/README.md',O/'root_after/history_README.md');shutil.copy2(history,O/'root_after/68_target_space_modes.md')
s=r(C/'state.json');s.update(status='SESSION7_E79_COMPLETE',stage='E79_COMPLETE',stage20_status='COMPLETE_TARGET_SPACE_MODES',session7_NSG=129536,session7_HNSW=129280,session7_builds=4,session7_offline_fits=4,total_new_NSG=4705364+129536,total_HNSW=5116896+129280,total_builds=352+4,session7_native_job_seconds=cost['native_job_seconds'],native_pids=[],day_goal_complete=False,session7_final_feedback_used=False,next_action='E79 complete. '+('Freeze new full development wall.' if passed else 'Stop target mean split version; use loss evidence for next mechanism or final preparation.'))
(C/'state.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
files=[]
for p in sorted(O.rglob('*')):
 if p.is_file() and p.name!='final_artifact_freeze.json':files.append(dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(O/'reviews/final_artifact_freeze.json').write_text(json.dumps(dict(epoch=time.time(),files=files,root_scope='root_after snapshots only',day_goal_complete=False),indent=2)+'\n')
print('E79_CLOSED',len(files),'wall gate',passed)
