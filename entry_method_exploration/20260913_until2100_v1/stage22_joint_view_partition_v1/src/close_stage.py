from common import *
import csv
cost=read(O/'results/cost.json');gate=read(O/'results/gate.json');off=read(O/'results/offline.json');passed=gate['wall_measurement_allowed'];assert read(O/'state.json')['builds']==2
hist=R/'experiment_history/70_joint_view_partition.md';assert not hist.exists();body=(O/'report.md').read_text();prefix='../entry_method_exploration/20260913_until2100_v1/stage22_joint_view_partition_v1/'
for sub in ['results/','reviews/','figures/']:body=body.replace(']('+sub,']('+prefix+sub)
body=body.replace('](protocol.md)',']('+prefix+'protocol.md)').replace('](../stage15_compact_wall_v1/','](../entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/');hist.write_text(body)
p=R/'s-experiment.md';s=p.read_text();marker='|---|---|---|---|\n';s=s.replace(marker,marker+'| E81 query/条件GT联合分组 | 从原Q分配出发、等权双视角20轮、双集aux7952 | `COMPLETE_JOINT_VIEW_PARTITION`；'+('至少一集原门通过，完整wall待做' if passed else '双集原门失败，停止本等权版本')+'；129536 NSG/2build/0QPS | [70 联合分组](experiment_history/70_joint_view_partition.md) |\n',1).replace('当前最近完成记录为E80同hub条件目标分组','当前最近完成记录为E81 query/条件GT联合分组');p.write_text(s)
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n- [70 query与条件GT联合分组](70_joint_view_partition.md)：E81，原Q初始化、等权联合目标与原P/compact/E80条件分组同批对照。\n')
with (O/'results/paired.csv').open() as f:rows=list(csv.DictReader(f))
brief=[]
for ds in DS:
 rr={x['reference']:x for x in rows if x['dataset']==ds and x['candidate']=='joint10' and x['split']=='all'};brief.append(f"| {'WebVid' if ds==DS[0] else 'Yandex'} | {int(rr['baseline10']['net_hits']):+d} / {int(rr['baseline10']['failure_change']):+d} | {int(rr['compact10']['net_hits']):+d} / {int(rr['compact10']['failure_change']):+d} | {int(rr['conditional10']['net_hits']):+d} / {int(rr['conditional10']['failure_change']):+d} |")
prev=[read(C/x/'results/cost.json') for x in ['stage20_target_space_modes_v1','stage21_hub_conditioned_targets_v1']];ns=sum(x['NSG'] for x in prev)+cost['NSG'];hs=sum(x['HNSW'] for x in prev)+cost['HNSW'];bs=sum(x['builds'] for x in prev)+cost['builds'];nt=sum(x['native_job_seconds'] for x in prev)+cost['native_job_seconds']
p=R/'summary.md';s=p.read_text();s=s.replace('# ACSG 当前结果摘要\n','# ACSG 当前结果摘要\n\n2026-09-13 第7会话最新E81：'+('至少一集预锁质量门通过，完整独立wall待做，尚非性能GO。' if passed else 'query/条件GT等权联合分组双集未过预锁门，本版本停止。')+' 从E66原Q分配开始，以两视角单位中心共同更新20轮；最终仍仅输出原query聚合画像，在线接口不变。\n\n| E81 aux7952 L128 | 对P：净命中 / 失败变化 | 对compact | 对E80条件目标 |\n|---|---|---|---|\n'+'\n'.join(brief)+f'\n\nE79–E81本会话累计{ns} NSG/{hs} HNSW/{bs}真实build/8离线画像训练，native操作wall {nt:.3f}s；0新增QPS，E34最终未打开。E81离线{cost["offline_total_seconds"]:.3f}s，构图{cost["micro_graph_build_seconds"]:.3f}s。[E81报告](entry_method_exploration/20260913_until2100_v1/stage22_joint_view_partition_v1/report.md)。下述E79/E80结论保留。\n',1).replace('本会话两阶段新增259072','E79/E80两阶段新增259072');p.write_text(s)
p=R/'s-target.md';s=p.read_text();s=s.replace('第7串行会话完成E79/E80；','第7串行会话完成E79–E81；',1);s=s.replace('1. E79全局GT均值及E80同hub条件均值都未过各自预锁门，','1. E81 query/条件GT联合分组'+('至少一集通过原门；下一阶段须另冻结完整双集wall，不用历史不同批点拼曲线。E79/E80旧门不变。\n\nE79全局GT均值及E80同hub条件均值都未过各自预锁门，' if passed else '也未过各自预锁门；三个单次目标分组版本均停止。下一实质方案须先对照三版收益丢失/新损伤与原compact局部信号，不从最终反馈找参数。E79/E80旧门不变，'));p.write_text(s)
p=R/'spec.md';p.write_text(p.read_text()+'''

## query与条件GT10联合分组（E81，2026-09-13）

[offline](entry_method_exploration/20260913_until2100_v1/stage22_joint_view_partition_v1/src/offline.py)精确恢复E66原Q assignment_bits及A/P、E80所有逐hub条件F digest。共享二类分配从原Q分区初始化；两视角各自计算加权和单位中心，固定等权J=sum_modes(||sum A Q||+||sum A F||)，20轮按query余弦分数与条件目标余弦分数之和更新，平局归0。记录完整21步目标轨迹及初末各视角范数，任一候选/最终出现空类或零视角中心都置整hub fallback，检查J非下降。复用前步已计算moments，不改变归约/更新。最终按原Q与rho rawhub先验聚合，父P首槽、同hub字节compact、普通小图构建和原在线kernel均保持。

新增objectives.npz、joint_support.csv及最后分区bits，纯离线数据；所有条件F/GT仅训练角色。父画像/原NSG/H815/821/rawIP不变，不加在线第二视角。实际两套新bank及两图、P/compact/E80条件三旧对照回归；目标/分区/输出W改变需重建相应图并重跑下游，不构成性能GO。
''')
for n in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:shutil.copy2(R/n,O/'root_after'/n)
shutil.copy2(R/'experiment_history/README.md',O/'root_after/history_README.md');shutil.copy2(hist,O/'root_after/70_joint_view_partition.md')
s=read(C/'state.json');s.update(status='SESSION7_E81_COMPLETE',stage='E81_COMPLETE',stage22_status='COMPLETE_JOINT_VIEW_PARTITION',session7_NSG=ns,session7_HNSW=hs,session7_builds=bs,session7_offline_fits=8,total_new_NSG=4705364+ns,total_HNSW=5116896+hs,total_builds=352+bs,session7_native_job_seconds=nt,native_pids=[],day_goal_complete=False,next_action='E81 complete. '+('Prospectively freeze a complete independent development wall.' if passed else 'Three target/joint definitions stopped; inspect session7 report and propose substantive next mechanism. Evening E34 pending.'));dump(C/'state.json',s)
resources();freeze(O/'reviews/final_artifact_freeze.json',[p for p in sorted(O.rglob('*')) if p.is_file() and p.name!='final_artifact_freeze.json']);print('E81_CLOSED',passed)
