from common import *
history=R/'experiment_history/59_width_control.md';assert not history.exists();body=(O/'report.md').read_text()
for prefix in ['results/','figures/','reviews/','protocol.md']:body=body.replace(']('+prefix,'](../entry_method_exploration/20260913_until2100_v1/stage11_width_control_v1/'+prefix)
history.write_text(body)
p=R/'s-experiment.md';t=p.read_text();pos=t.index('| E69 精确画像');t=t[:pos]+'| E70 固定图单次ef宽度控制 | P/duplicate/mode各ef10/30，aux7952/L128 | `COMPLETE_WIDTH_CONTROL`；Y辅助质量门过、Web未过，路由成本明显增加，194304 NSG/0QPS | [59 width控制](experiment_history/59_width_control.md) |\n'+t[pos:];p.write_text(t)
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n- [59 E70 固定小图搜索宽度](59_width_control.md)：单个ef10→30，Y质量门通过、Web反证，完整wall待测。\n')
p=R/'summary.md';t=p.read_text();t=t.replace('第4串行会话完成E69精确画像前三真实NSG诊断','第4串行会话完成E69精确入口诊断及E70固定图ef宽度控制');t=t.replace('后继仅一次ef10→30受控比较尚未运行。','后继E70已执行，见下。');pos=t.index('\nE66双集');t=t[:pos]+'''\nE70仅ef10→30，P/duplicate/mode六policy固定：Web mode30相对P10净+6/失败+5，两半−16/+22；相对P30净−100/失败+10，未过门。Y相对P10净+77（+.0968pp）/失败−7，两半+8/+69；相对P30+89/失败−7，两半+28/+61，过有限质量接续门。相对P10 routing NDC Web+87.32%/Y+111.69%，total+5.26%/+3.93%，尚无完整效率结论。194304 NSG/193920 HNSW/0构图，原生四job150.859秒；96960集合评分及ef10原返回、7slot和kernel回归通过。下一独立E71同批加入mode10/mode30/P30与全部基线五L五轮，未运行。\n'''+t[pos:];t=t.replace('[E69报告与图]','[E70报告](entry_method_exploration/20260913_until2100_v1/stage11_width_control_v1/report.md) · [E69报告与图]');p.write_text(t)
p=R/'s-target.md';t=p.read_text();a=t.index('1. ');b=t.index('3. ');t=t[:a]+'''1. E70完成：Yandex mode30相对P10/P30均净命中正、两半非负且失败下降，WebVid仍未过门；原E66门保持。下一独立E71冻结NSG/Fast30K/GT10-hard/Web匹配soft/P30/mode10/mode30，同历史开发2048、五L五轮。mode10与mode30在同批直接比较收益及路由代价，不拼旧曲线；至少报告QPS–Recall/QPS–失败/按L三指标和全量失败query。
2. E70已实现仅10/30的ef_search和reference_graph冻结图直接加载，源/全ef10回归通过。完整wall必须包含真实路由/去重/NSG/output，GT/count/hash/build/load在外，CPU15实际线程1、串行，参数/选择不得依最终反馈修改。
'''+t[b:];p.write_text(t)
p=R/'spec.md';p.write_text(p.read_text()+'''

## 固定图显式ef与直接引用加载（E70，2026-09-13）

[E70 Policy](entry_method_exploration/20260913_until2100_v1/stage11_width_control_v1/src/benchmark_with_nsg.cpp)增加ef_search白名单10/30（缺省10），保持原k3或多画像k7/去重3合同。reference_graph=true时plain和count从同一graph_file直接加载、全W/slot或真实标签memcmp验收，不复制小图。旧源图/NSG/hnswlib不改；其[evaluate](entry_method_exploration/20260913_until2100_v1/stage11_width_control_v1/src/evaluate.cpp)与E66逐字相同，完整wall接口不变。eff参数不是等工作量或真实hub数量。

[预检与完整开发runner](entry_method_exploration/20260913_until2100_v1/stage11_width_control_v1/src/run.py)锁四job/194304 NSG，显式绑核后exec并监控/proc线程/RSS，原ef10全部回归E66。统计/图依赖graph_file路径与SHA，不可期待每point目录都有新.hnsw副本。源图/参数/映射改变需新结果；现有原kernel/plain/count/slot/源图全bytes验收通过，方法质量由summary维护。
''')
s=read(C/'state.json');s.update(status='SESSION4_E70_COMPLETE',stage='E70_COMPLETE',stage11_status='COMPLETE_WIDTH_CONTROL',total_new_NSG=2303060,total_HNSW=3004576,session4_NSG=233246,session4_HNSW=193920,native_pids=[],next_action='Prepare independent E71 full development wall including mode10/mode30/P30 and all original baselines.');dump(C/'state.json',s)
(C/'handoff.md').write_text('# 第4串行会话进行中\n\nE69/E70完成，原默认不变，整日目标未完成；会话13:20:37前安全边界。E70 Y质量门通过，Web未过。下一E71完整wall（mode10/mode30/P30及全部规定基线）尚未运行；E34最终及held-out仍隔离。成本233246NSG/193920HNSW/0新图，当前无native。\n\n[E69](stage10_exact_triple_utility_v1/report.md) · [E70](stage11_width_control_v1/report.md) · [前会话](handoff_session3.md)。\n')
after=O/'reviews/root_after';after.mkdir()
for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:shutil.copy2(R/x,after/x.replace('/','__'))
check(O/'reviews/prequery_freeze.json');resources();freeze(O/'reviews/final_artifact_freeze.json',[p for p in O.rglob('*') if p.is_file() and p.name!='final_artifact_freeze.json']+[history]);print('SEALED_E70')
