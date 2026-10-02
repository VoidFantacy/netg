from common import *
history=R/'experiment_history/58_exact_triple_utility.md'
assert not history.exists()
body=(O/'report.md').read_text().replace('# E69 完整画像前三的真实NSG效用','# 58. E69 完整画像前三的真实NSG效用')
for prefix in ['results/','figures/','reviews/','protocol.md']:
 body=body.replace(']('+prefix,'](../entry_method_exploration/20260913_until2100_v1/stage10_exact_triple_utility_v1/'+prefix)
history.write_text(body)
p=R/'s-experiment.md';t=p.read_text();marker='| E68 完整画像排序诊断';pos=t.index(marker);t=t[:pos]+'| E69 精确画像三入口真实NSG | 同入口缓存补缺、原P全回放、两半效用 | `COMPLETE_EXACT_TRIPLE_UTILITY`；Y有限质量门通过、Web未过，38942 NSG/0QPS | [58 精确三入口](experiment_history/58_exact_triple_utility.md) |\n'+t[pos:];p.write_text(t)
p=R/'experiment_history/README.md';t=p.read_text();t+='\n- [58 E69 精确画像三入口真实NSG](58_exact_triple_utility.md)：Yandex局部效用通过、Web未过；完整缓存/回放、38942新NSG，无QPS。\n';p.write_text(t)
(R/'summary.md').write_text('''# ACSG 当前结果摘要

2026-09-13，第4串行会话完成E69精确画像前三真实NSG诊断。Yandex通过有限辅助质量接续门，WebVid未通过；原默认未替换，整日21:00目标未完成，E34最终validation仍待晚间冻结对照。

E69固定历史aux7952/L128。精确mode相对精确P：Web净−109命中（−0.1371pp）、失败+7，两半−86/−23；Y净+132（+0.1660pp）、失败−10，两半+32/+100。相对原approx P：Web+85/失败−6、Y+97/失败−8。相对原approx mode：Web+191、Y+48。精确P本身Web改善194而Y损失35，画像排序更准不保证NSG更好。

38,942新NSG含全baseline plain/count回放、3535唯一补缺plain/count与64原kernel对照；31808逻辑精确结果中28102复用旧缓存、171别名。79520返回独立集合与mask评分、15904原baseline字节恢复、全部plain/count/reference及线程1验收通过。0HNSW/构图/新GT/梯度/QPS，原生操作37.904秒不是完整在线wall。后继仅一次ef10→30受控比较尚未运行。

E66双集原开发门失败保持；Y fit/aux局部正值保留。E67同批55点275wall：Y五L有4个Recall正点且失败不增，L64 QPS−2.298%；Web质量混合且QPS中位五点均负。其余多数QPS交叉范围跨0，无稳定整体改善证据。E65另45点225wall保留，今日100个历史开发性能点不得跨批拼方法曲线。

P-fit含旧train/monitor；cal/audit/aux均历史暴露，辅助选择反馈计训练。E69没有使用E34最终validation或held-out。E68近似缺口及两条相反失败案例的事实保持，E69只为L128新增反事实，不推断其余L。

[E69报告与图](entry_method_exploration/20260913_until2100_v1/stage10_exact_triple_utility_v1/report.md) · [E67完整wall](entry_method_exploration/20260913_until2100_v1/stage8_multimode_wall_v1/report.md) · [下一阶段](s-target.md)。
''')
(R/'s-target.md').write_text('''# ACSG 下一阶段目标与接续

2026-09-13，第4串行会话已完成E69。唯一写入/实验者，不开并行CLI或子代理；本会话最迟13:20:37安全交接，整日目标未完成。

1. E69精确mode在Yandex胜精确P和approx P，固定两半/失败/graph成本门通过；Web未胜精确P。下一独立E70仅测试同一冻结小图ef10→30，P/duplicate/mode各两档，固定aux7952/L128、原两半。单画像ef30用于区分通用搜索宽度收益，Web作为同设置迁移反证。完整查询前锁预算/门，不扫ef/seed。
2. 现场源码发现E66 Policy硬编码setEf(10)，旧接续中“可配置修改ef”的说法不成立。E70须独立实现只允许10/30的显式参数、按SHA直接引用冻结小图避免重复物理副本，并验收原ef10返回/7slot/plain/count/kernel。尚未实现的后继不写现有API。若质量支持，另冻结同批NSG/Fast/GT10匹配起点/P30/实际mode候选五L五轮完整wall。
3. 20:00停新训练、20:40停新增查询、21:00完整交付。晚间冻结best_all与今日实际best_new，再E34历史validation2000同批最终对照；最终反馈不回流训练/选型，held-out不自动打开。无稳定改善时如实展示新候选与损伤。

原base/raw-IP/NSG/GT/H固定，全部旧字节保护，每阶段root source_before。free>=7GiB并预留累计输出和晚间曲线空间；所有ANN CPU15/threads1/数值库1，单方法串行，完整在线wall与GT/count/hash/build/load分开。P-fit/旧cal/audit/aux均历史暴露，辅助选择反馈计训练。

[E69报告](entry_method_exploration/20260913_until2100_v1/stage10_exact_triple_utility_v1/report.md) · [campaign状态](entry_method_exploration/20260913_until2100_v1/state.json) · [交接](entry_method_exploration/20260913_until2100_v1/handoff.md)。
''')
p=R/'spec.md';t=p.read_text();t+='''

## 冻结精确三入口注入与缓存诊断（E69，2026-09-13）

[独立inject.cpp](entry_method_exploration/20260913_until2100_v1/stage10_exact_triple_utility_v1/src/inject.cpp)包含E46/E37原环境，新增e69_search对同一显式row/升序唯一H三入口执行plain或原Work reference；count沿e46_search。整批先验证后查询，0长度保持正确空类型；不建HNSW且不调用route，固定L128/K10/rawIP/原NSG。原kernel不变，39K真实调用与全原baseline恢复通过。

[prepare](entry_method_exploration/20260913_until2100_v1/stage10_exact_triple_utility_v1/src/prepare.py)以namespace/source query bytes、row、canonical三入口、base/图/kernel/L/K/GT建立复用键；E66三方法碰撞逐字段相同，E68完整P/mode排名只补3535唯一缺口，route NDC不复用。[run](entry_method_exploration/20260913_until2100_v1/stage10_exact_triple_utility_v1/src/run.py)全baseline回放、missing plain/count和64原wrapper，CPU15实际1线程；[分析](entry_method_exploration/20260913_until2100_v1/stage10_exact_triple_utility_v1/src/analyze.py)保存完整exact aligned输出及source_method/source_index和strict zero失败。0HNSW/构图/训练/新GT，计数和查表wall不是QPS；接口仅供离线诊断，不新增线上完整扫描策略。
''';p.write_text(t)
s=read(C/'state.json');s.update(status='SESSION4_E69_COMPLETE',stage='E69_COMPLETE',stage10_status='COMPLETE_EXACT_TRIPLE_UTILITY',total_new_NSG=2108756,session4_NSG=38942,session4_HNSW=0,session4_builds=0,native_pids=[],next_action='Prepare independent E70 width control, all three policies ef10/30; no E34 final feedback.');dump(C/'state.json',s)
(C/'handoff.md').write_text('# 第4串行会话进行中\n\nE69完成；整日目标未完成。本会话最迟13:20:37安全交接。原会话3完整交接保存在[handoff_session3.md](handoff_session3.md)。\n\n[E69报告](stage10_exact_triple_utility_v1/report.md)：Yandex精确mode相对精确P+132命中/失败−10，Web−109/失败+7。38942 NSG，0HNSW/构图/QPS，无遗留native。下一步独立E70单次ef10→30完整控制，P/duplicate/mode保留。E34最终和held-out未进入，所有aux反馈计训练。\n')
root_after=O/'reviews/root_after';root_after.mkdir()
for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:shutil.copy2(R/x,root_after/x.replace('/','__'))
check(O/'reviews/prequery_freeze.json');resources()
freeze(O/'reviews/final_artifact_freeze.json',[p for p in O.rglob('*') if p.is_file() and p.name!='final_artifact_freeze.json']+[history])
print('SEALED_E69')
