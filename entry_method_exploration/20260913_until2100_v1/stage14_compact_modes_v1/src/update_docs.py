from common import *
assert read(O/'reviews/verification.json')['status']=='PASS';history=R/'experiment_history/62_compact_modes.md';assert not history.exists();body=(O/'report.md').read_text()
for prefix in ['results/','figures/','reviews/','protocol.md']:body=body.replace(']('+prefix,'](../entry_method_exploration/20260913_until2100_v1/stage14_compact_modes_v1/'+prefix)
history.write_text(body)
p=R/'s-experiment.md';t=p.read_text();pos=t.index('| E72 真实hub');t=t[:pos]+'| E73 同hub重复画像精简 | 原mode字节去重、1–3槽/真实hub、两小图、aux7952 | `COMPLETE_COMPACT_MODE_DEVELOPMENT`；Y质量门过，Web相对P负、相对完整mode正，97152 NSG/无QPS | [62 精简画像](experiment_history/62_compact_modes.md) |\n'+t[pos:];t=t.replace('当前最近完成记录为E72真实hub计宽控制','当前最近完成记录为E73同hub重复画像精简');p.write_text(t)
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n- [62 E73 同hub重复画像精简](62_compact_modes.md)：完整每hub画像分数集合保持，Y辅助质量正、Web迁移反证，完整wall接续。\n')
(R/'summary.md').write_text('''# ACSG 当前结果摘要

2026-09-13，第5串行会话完成E72/E73。E73精简版在Yandex历史辅助质量门通过；WebVid仍低于P10。尚未测本候选完整QPS，不替换默认；整日21:00目标未完成，E34晚间最终反馈未使用。

E73只删除同一hub的字节完全相同画像，Web2445→1771、Y2463→2067，保留全部不同模式向量与真实H815/821。源bank能由保留slot精确恢复，故每hub完整max评分集合不变；普通重建小图改变近似遍历，仍ef10/7slot去重3入口→原NSG。

| 数据 | compact对P10 | compact对完整mode10 |
|---|---|---|
| WebVid | −59命中、失败+11、两半−16/−43 | +47、失败−2、两半+22/+25 |
| Yandex | +120命中、失败−13、两半+39/+81 | +71、失败−9、两半+53/+18 |

路由NDC相对完整mode只降低Web0.649%/Y0.098%，总NDC−0.092%/−0.165%；相对P10路由仍+3.63%/+20.22%。删除节点比例不能换算QPS。E73按预锁协议进入独立E74同批五L五轮，以实际compact为唯一新候选，保留完整mode和规定基线，不按新反馈调参。

E73新增97152 NSG/96960 HNSW/2小图，0新画像训练/GT；精简.031秒、build .348秒、编译25.432秒、四native90.132秒。48480集合/mask及47712独立标量评分、31808旧控制返回/距离/入口/两NDC、192原kernel、全部图W/label及七slot验证通过。实际CPU15/进程与数值库1线程，全部工具terminal0后分析。

E72 distinct10本版本按双集原门停止，0QPS。Y对P10 +73命中/失败−6，Web−21/失败+4；相对mode30路由NDC−25%～31%，但质量未保住，局部信号保留。E71完整65点325wall没有稳定整体前沿改善，E66/E70旧门保持。

本会话累计291456 NSG/290880 HNSW/2实际build，合成另4图/512HNSW。P-fit含旧train/monitor，cal/audit/aux均历史暴露，辅助选择计训练；E34最终与held-out今日未进入。全部旧产物、source_before与root_after封存保留。

[E73报告](entry_method_exploration/20260913_until2100_v1/stage14_compact_modes_v1/report.md) · [E72](entry_method_exploration/20260913_until2100_v1/stage13_distinct_hub_width_v1/report.md) · [下一阶段](s-target.md)。
''')
p=R/'s-target.md';t=p.read_text();a=t.index('2. ');b=t.index('3. ');t=t[:a]+'''2. E73已完成：仅同hub字节重复画像精简，Web1771/Y2067画像，完整分数集合保持。Y相对P +120/失败−13、对完整mode+71/失败−9，固定两半均正，质量门通过；Web相对P−59/失败+11但对mode+47/失败−2，反证保留。下一E74固定compact唯一新候选，NSG/Fast30K/GT10-hard/Web匹配soft/fullmode10/compact10同历史开发2048五L五轮；实际完整路由/原NSG/output收费，不扫参数、不拼旧速度。该测量按E73前瞻协议执行，不把Web质量门回写通过。
'''+t[b:];t=t.replace('E72已完成','E72/E73已完成');p.write_text(t)
p=R/'spec.md';p.write_text(p.read_text()+'''

## 同hub字节精简与variable画像数（E73，2026-09-13）

[prepare](entry_method_exploration/20260913_until2100_v1/stage14_compact_modes_v1/src/prepare.py)按(real hub,float32 row bytes)保留首次slot，输出新W/mapping/tie_ids、original_slots与old_to_compact，完整重构原bank字节。每hub完整max分数集合保持，不保证新近似图/NSG结果保持；原P作为单画像字节控制，原duplicate图不冒充压缩图。

[Policy](entry_method_exploration/20260913_until2100_v1/stage14_compact_modes_v1/src/benchmark_with_nsg.cpp)的variable_profiles=true允许每hub1–3槽并验证unique_hub_count；false沿原恰3槽，七slot排序/去重三入口及原kernel/计时循环不变。[build_graph](entry_method_exploration/20260913_until2100_v1/stage14_compact_modes_v1/src/build_graph.cpp)用原M16/efConstruction200/seed普通重建两张小图，序列化加载全W/slot labels核验。真实辅助全量与两旧控制逐位恢复通过，完整输入/源/图冻结。

compact候选的物理画像数与unique H分列，完整原模式监督来源不变；改变保留规则、顺序、tie/mapping、图、ef或NSG/query/GT须新建依赖结果。E73无完整QPS，方法判断由summary与历史62维护。
''')
s=read(C/'state.json');s.update(status='SESSION5_E73_COMPLETE',stage='E73_COMPLETE',stage14_status='COMPLETE_COMPACT_MODE_DEVELOPMENT_Y_QUALITY_PASS',total_new_NSG=3527396,total_HNSW=4083936,total_builds=348,session5_NSG=291456,session5_HNSW=290880,session5_builds=2,native_pids=[],next_action='Freeze E74 complete development wall with NSG/Fast/GT10/full mode/compact mode, no parameter changes or final data.');dump(C/'state.json',s)
(C/'handoff.md').write_text('# 第5串行会话进行中\n\nE72/E73完成，整日目标未完成；14:17:57前安全交接。E73 Y质量门通过，Web相对P损伤保留。下一E74完整同批wall尚未执行。当前291456 NSG/290880 HNSW/2图，合成另4图/512HNSW，无native。E34最终及held-out仍未读取。\n\n[E73](stage14_compact_modes_v1/report.md) · [E72](stage13_distinct_hub_width_v1/report.md)。\n')
after=O/'reviews/root_after';after.mkdir()
for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:shutil.copy2(R/x,after/x.replace('/','__'))
dump(O/'reviews/figure_review.json',dict(status='PASS',figure='compact_control.png',viewed_by='session5',layout_and_values=True));check(O/'reviews/prequery_freeze.json');resources();freeze(O/'reviews/final_artifact_freeze.json',[p for p in O.rglob('*') if p.is_file() and p.name!='final_artifact_freeze.json']+[history]);print('SEALED_E73')
