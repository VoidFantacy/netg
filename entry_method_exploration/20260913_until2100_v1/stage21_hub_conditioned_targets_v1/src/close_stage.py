from common import *
import csv
cost=read(O/'results/cost.json');gate=read(O/'results/gate.json');off=read(O/'results/offline.json');union=read(O/'results/failure_union.json');passed=gate['wall_measurement_allowed'];assert read(O/'state.json')['builds']==2
with (O/'results/paired.csv').open() as f:rows=list(csv.DictReader(f))
hist=R/'experiment_history/69_hub_conditioned_targets.md';assert not hist.exists();body=(O/'report.md').read_text();prefix='../entry_method_exploration/20260913_until2100_v1/stage21_hub_conditioned_targets_v1/'
for sub in ['results/','reviews/','figures/']:body=body.replace(']('+sub,']('+prefix+sub)
body=body.replace('](protocol.md)',']('+prefix+'protocol.md)').replace('](../stage15_compact_wall_v1/','](../entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/')
hist.write_text(body)
p=R/'s-experiment.md';s=p.read_text();marker='|---|---|---|---|\n';s=s.replace(marker,marker+'| E80 同hub条件GT目标分组 | 原rank权重/A/P恢复、条件目标逐hub流式分组、双集aux7952 | `COMPLETE_HUB_CONDITIONED_TARGETS`；'+('至少一集原门通过，待完整wall' if passed else '双集原门失败，本条件均值版本停止')+'；129536 NSG/2build/0QPS | [69 条件目标](experiment_history/69_hub_conditioned_targets.md) |\n',1).replace('当前最近完成记录为E79目标空间分组','当前最近完成记录为E80同hub条件目标分组');p.write_text(s)
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n- [69 同hub条件GT目标分组](69_hub_conditioned_targets.md)：E80，条件权重/流式目标特征与原P、compact、全局目标分组完整对照。\n')
brief=[]
for ds in DS:
 rr={x['reference']:x for x in rows if x['dataset']==ds and x['candidate']=='conditional10' and x['split']=='all'};brief.append(f"| {'WebVid' if ds==DS[0] else 'Yandex'} | {int(rr['baseline10']['net_hits']):+d} / {int(rr['baseline10']['failure_change']):+d} | {int(rr['compact10']['net_hits']):+d} / {int(rr['compact10']['failure_change']):+d} | {int(rr['global10']['net_hits']):+d} / {int(rr['global10']['failure_change']):+d} |")
physical='/'.join(str(x['physical_profiles']) for x in off['datasets'])
(R/'summary.md').write_text('''# ACSG 当前结果摘要

2026-09-13，第7串行会话完成E79/E80目标分组改进。E80按每个hub原GT归属的条件权重形成目标特征，最终仍聚合原query画像。'''+('至少一集通过E80预锁质量门，待独立完整wall，尚非性能GO。' if passed else 'E80双集预锁门失败，本条件均值版本停止；E79全局均值原门失败保持。')+'''整日21:00目标未完成，E34晚间最终未进入。

| E80 aux7952 L128 | 对P：净命中 / 失败变化 | 对compact | 对E79全局目标 |
|---|---|---|---|
'''+ '\n'.join(brief)+f'''

E80固定原rank权重/A/P、GT/rawIP/NSG/H815/821，按hub流式条件目标两分组，物理画像Web/Y={physical}。beta归一化避免极小soft权重被截断；A=0表示该hub无支持，不作零目标监督。目标语义改变也影响子支持、容量和小图，不能当单中介因果或新颖性结论。

E79主候选对P Web−11命中/失败+7、Y0/−2；对compact Web+48/−4、Y−120/+11；对置换+73/+213但未过原门。目标定义不是全部问题的已定原因。完整旧收益保留/丢失、新收益/新损伤和GT成员得失均保存。

E73/E74 Yandex局部信号保留：五L对P命中+99/+59/+38/+1/+15、失败−10/−7/−4/−1/0；五轮QPS范围均跨零，约1.9%～3.0%仅描述性插值。Web L128−23命中/失败+6。E75/E77/E78各原停止门保持，默认未替换。

本会话两阶段新增259072 NSG/258560 HNSW/6真实build，6离线分组训练及2原Q复现，0梯度/新GT/编译/新增QPS。E80离线{cost['offline_total_seconds']:.3f}s、构图{cost['micro_graph_build_seconds']:.3f}s、native{cost['native_job_seconds']:.3f}s；操作wall含加载/count/I/O不是QPS。继承GT/P成本未知。所有ANN串行CPU15/实际进程与数值库1线程，terminal0后独立评分；E80旧三对照47712行全字段恢复、256原kernel与全7slot/图身份通过。

E80失败并集{sum(x['any_zero'] for x in union.values())}个dataset/source-row、其中{sum(x['changed_zero'] for x in union.values())}个失败状态变化，完整GT/入口/返回ID保存。P-fit含旧train/monitor，aux7952及两半已观察且反馈计训练，cal/audit历史使用；E34最终与held-out未打开。各阶段source_before/root_after和旧seal保持。

资源按E80新前瞻64MiB上限、6.8GiB下限外另64MiB晚间+4MiB交接；旧版本预算不变，禁止清理历史。E79 build计数元数据原件与独立修正保留。

[E80完整报告](entry_method_exploration/20260913_until2100_v1/stage21_hub_conditioned_targets_v1/report.md) · [E79报告](entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/report.md) · [最近E74 QPS–Recall/失败曲线](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/report.md) · [下一阶段](s-target.md)。
''')
(R/'s-target.md').write_text('''# ACSG 下一阶段目标与接续

2026-09-13，第7串行会话完成E79/E80；整日21:00目标未完成。唯一写入/实验者，本会话16:21:50前安全交接，不开并行CLI/子代理。

1. '''+('E80至少一集通过原质量门，下一步独立冻结conditional双集同批完整wall；含原NSG/Fast/GT10匹配P/compact/conditional，五L五轮。' if passed else 'E79全局GT均值及E80同hub条件均值都未过各自预锁门，不扫目标rank数、簇数、seed、权重或改选置换。先从已测损益及分区证据判断下一实质机制，不把目标几何差异当NSG效用。')+'''
2. 保留E73/E74 Yandex局部正信号及Web损伤。所有改进必须同时计算旧收益丢失、旧损失修复与新损伤；只改变分组目标没有保证保留有用改道。原E75/E77/E78门、S/T/uniform/permuted机制控制身份不改。
3. 晚间20:00停新训练、20:40停新增查询、21:00完整报告。先在已观察开发反馈上冻结best_all/best_new和规则，再读E34历史validation2000；不得反馈训练或选型，held-out不自动打开。原NSG/Fast/GT10匹配起点/实际新方法同批五L五轮完整在线wall，aligned集合评分、zero救回/新增、QPS–Recall/QPS–失败率/按L三指标/失败查询图齐备，不拼旧批次。

E80资源预算64MiB，free6.8GiB外额外64MiB晚间+4MiB交接；旧E79及更早各版本门保持。下阶段先现场核算累计新输出，保护原图/GT/脏源/全部旧artifact，不复制大输入/binary、不清理文件。原H815/821/NSG/base/rawIP固定，新增画像学习均离线，所有ANN CPU15/实际进程及数值库1线程串行。

P-fit20K含旧train/monitor，aux7952/两半及cal/audit历史暴露，任何用于动作/模型选择的反馈算训练；元数据余行不证明项目未使用。各阶段source_before/root_after及seal保持，库存主候选与控制分开，未过门的实际新方法只在独立最终比较协议中诚实展示。

[E80报告](entry_method_exploration/20260913_until2100_v1/stage21_hub_conditioned_targets_v1/report.md) · [campaign状态](entry_method_exploration/20260913_until2100_v1/state.json) · [监督备注](/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md)。
''')
p=R/'spec.md';p.write_text(p.read_text()+'''

## 同hub条件GT10分组画像（E80，2026-09-13）

[offline](entry_method_exploration/20260913_until2100_v1/stage21_hub_conditioned_targets_v1/src/offline.py)恢复原逐rank hard/soft权重a及A/P字节，以beta_r=a_r/sum a_r构造每query、每hub条件目标F=unit(sum beta_r unit(raw GT target))。A=0行无该hub支持；正支持零目标整hub回退。目标与rank权重仅RAM，逐hub流式，避免持久化N×H×d。固定20轮加权球面二分/同父子门，最后按A与原Q聚合子画像/P首槽保持，再同hub精确字节去重。新增artifact为每hubF digest、条件有效目标数/目标漂移/无标签分区差异及完整support/最后分配bits/source axes；不用于在线路由。

两物理新图仍由E73同SHA普通builder构建，在线evaluator/kernel/7slot去重3/ef10/variable1–3合同不变。原P、compact、E79global物理图全字段回归，新preflight_v2显式核验第三旧控制；完整plain/count/原kernel及图W/label/邻接和集合/mask保持。E80查询无wall，rank/条件定义、画像/图/映射/数据/metric/kernel改变使相关反馈与计时依赖失效；接口/构造通过不构成质量或性能GO。
''')
for n in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:shutil.copy2(R/n,O/'root_after'/n)
shutil.copy2(R/'experiment_history/README.md',O/'root_after/history_README.md');shutil.copy2(hist,O/'root_after/69_hub_conditioned_targets.md')
s=read(C/'state.json');s.update(status='SESSION7_E80_COMPLETE',stage='E80_COMPLETE',stage21_status='COMPLETE_HUB_CONDITIONED_TARGETS',session7_NSG=259072,session7_HNSW=258560,session7_builds=6,session7_offline_fits=6,total_new_NSG=4705364+259072,total_HNSW=5116896+258560,total_builds=352+6,session7_native_job_seconds=read(C/'stage20_target_space_modes_v1/results/cost.json')['native_job_seconds']+cost['native_job_seconds'],native_pids=[],day_goal_complete=False,session7_final_feedback_used=False,next_action='E79/E80 complete. '+('Freeze new full development wall.' if passed else 'Both target-mean definitions stopped; new mechanism requires prospective protocol; evening E34 pending.'));dump(C/'state.json',s)
freeze(O/'reviews/final_artifact_freeze.json',[p for p in sorted(O.rglob('*')) if p.is_file() and p.name!='final_artifact_freeze.json']);print('E80_CLOSED',passed)
