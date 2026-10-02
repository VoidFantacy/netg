from common import *
assert read(O/'reviews/independent_verification.json')['status']=='PASS'
history=R/'experiment_history/61_distinct_hub_width.md';assert not history.exists();body=(O/'report.md').read_text()
for prefix in ['results/','figures/','reviews/','protocol.md']:body=body.replace(']('+prefix,'](../entry_method_exploration/20260913_until2100_v1/stage13_distinct_hub_width_v1/'+prefix)
history.write_text(body)
p=R/'s-experiment.md';t=p.read_text();pos=t.index('| E71 多画像');t=t[:pos]+'| E72 真实hub计宽 | 原P/duplicate/mode固定图、普通与distinct10六控制 | `COMPLETE_DISTINCT_HUB_CONTROL`；Y相对P局部正，但双集完整接续门失败，194304 NSG/0QPS | [61 distinct控制](experiment_history/61_distinct_hub_width.md) |\n'+t[pos:];t=t.replace('当前最近完成记录为E71多画像加宽完整开发wall','当前最近完成记录为E72真实hub计宽控制');p.write_text(t)
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n- [61 E72 真实hub计宽](61_distinct_hub_width.md)：固定图distinct10，Y局部正与更低于mode30的路由NDC保留，双集原接续门失败。\n')
(R/'summary.md').write_text('''# ACSG 当前结果摘要

2026-09-13，第5串行会话完成E72真实hub计宽控制。Y相对P10有局部质量收益，但双集未过预锁完整wall接续门；本版本停止，无新QPS，原默认保持。整日21:00目标未完成，E34晚间最终对照仍未使用。

固定E66原P/duplicate/mode物理图与画像，以10不同真实hub替代physical node结果宽度，最终仍三入口→原NSG。历史aux7952/L128，固定3976两半；所有选择反馈计训练。

| 数据 | distinct mode相对P10 | 相对mode10 | 相对mode30 |
|---|---|---|---|
| WebVid | −21命中、失败+4、两半−7/−14 | +85、失败−9、两半+31/+54 | −27、失败−1、两半+9/−36 |
| Yandex | +73命中、失败−6、两半+10/+63 | +24、失败−2、两半+24/0 | −4、失败+1、两半+2/−6 |

路由NDC相对mode30 Web−31.26%、Y−25.43%，相对P10仍+28.77%/+57.85%；计数不是完整在线性能。新mode与完整画像前三一致率85.06%/93.80%，平均16.02/18.06物理槽、均10不同hub；更准的画像排名不保证NSG收益。Y小幅未保住mode30的质量不等于全部多画像方向无效。

194304新NSG/193920 HNSW，0新画像训练/实际图构建/GT；合成另4图/512HNSW。原生149.135秒、编译16.616秒。96960集合/mask评分、主批63616原控制及singleton逐位恢复、384原kernel及完整候选/映射/距离核验，另95424独立集合重评分通过。实际CPU15/进程及数值库1线程，四job工具terminal0后分析。

E69–E71局部质量及损伤保留：E71的65点325轮完整wall未形成稳定整体QPS–Recall改善，不能由E72的NDC减少推翻；E66/E70原门不改。下一独立版本测试同hub字节重复画像精简，尚未构建/查询，完整评分集合可保持但新图/近似返回需实测。

P-fit20K含旧train/monitor，cal/audit/aux均历史暴露；E34最终及held-out今日未进入。所有旧产物、根文档前件与封存保留。

[E72报告](entry_method_exploration/20260913_until2100_v1/stage13_distinct_hub_width_v1/report.md) · [E71完整wall](entry_method_exploration/20260913_until2100_v1/stage12_width_wall_v1/report.md) · [下一阶段](s-target.md)。
''')
(R/'s-target.md').write_text('''# ACSG 下一阶段目标与接续

2026-09-13，第5串行会话进行中，E72已完成。整日目标未完成，会话14:17:57前安全交接；唯一写入/实验者，不开并行CLI或子代理。

1. E72 distinct10双集接续门失败，本版本停止，不继续扫宽度/seed。保留Y相对P10 +73命中/失败−6和相对mode30更低路由NDC，但−4命中/失败+1，不能升级为性能GO。
2. 下一独立E73拟只精简同hub字节完全相同的画像（Web674、Y396冗余槽须当前核对）。固定原全部不同向量、真实H/三入口/rawIP/NSG，重建一个小图；新增variable1–3槽校验，旧路径逐位恢复。先锁协议/预算/控制与角色，再构建/预检/全7952辅助。该方法的主要假设是降低在线成本，完整五L五轮wall须另冻结同批NSG/Fast/GT10匹配起点/完整mode/实际compact方法；未过质量也保留其成本反证，不按最终反馈调参。
3. 晚间20:00停新训练、20:40停新增query、21:00完整交付。开发反馈先冻结best_all与真实best_new；E34历史validation2000只用于最终对照，不回流训练/选择，held-out不自动打开。所有候选曲线同机同批单线程、五轮轮换，不拼不同批次方法。

所有ANN CPU15/实际threads1、OMP/BLAS/MKL等1线程；完整路由/去重/原NSG/output在独立wall内，GT/count/hash/JSON/build/load在外。原base/rawIP/NSG/GT/真实H815/821固定。画像/构图学习离线；fit/旧train/monitor/cal/audit/aux历史暴露，辅助选择反馈计训练。每阶段source_before/root_after，free>=7GiB并预留晚间，禁止清理旧产物。

[E72报告](entry_method_exploration/20260913_until2100_v1/stage13_distinct_hub_width_v1/report.md) · [campaign状态](entry_method_exploration/20260913_until2100_v1/state.json) · [监督备注](/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md)。
''')
p=R/'spec.md';t=p.read_text();t=t.replace('下一distinct-hub callback只有设计，尚无该在线API或变长candidate artifact；不可把现有7slot当其完整候选。','E71当时的distinct-hub callback只有设计；继任E72接口见下节，E71七slot仍不能当其完整候选。');p.write_text(t+'''

## 真实hub计宽及完整候选artifact（E72，2026-09-13）

[独立Policy](entry_method_exploration/20260913_until2100_v1/stage13_distinct_hub_width_v1/src/benchmark_with_nsg.cpp)支持distinct_hub_width=10，0保持原路径。BaseSearchStopCondition按external label→hub实际add/remove计引用，忽略移除dist，query开始清空已触及计数；stop/consider/remove按10不同hub工作。未修改原hnswlib/NSG。内部返回ID显式转换external/row；singleton保留原堆截k子集并恢复原外部堆/canonical顺序，mode完整候选按distance/slot去重前三hub。

[evaluate](entry_method_exploration/20260913_until2100_v1/stage13_distinct_hub_width_v1/src/evaluate.cpp)新增distinct_size.u32、distinct_hubs.u32及固定30槽distinct_slots.i32/distinct_distances.f32；只前size为候选，其余0 padding。完整plain/count/repeat按bits核对全部候选；旧7slot另存，不混同。源图引用加载、全部W/label校验、GT后评分/完整wall合同保留；本阶段无wall实测。

两集singleton及旧三控制在主7952全部恢复；合成tie/非同一内外ID/引用移除/复位通过，全96960返回评分/384原kernel通过。接口验收不等于方法通过，E72停止规则见[协议](entry_method_exploration/20260913_until2100_v1/stage13_distinct_hub_width_v1/protocol.md)。改变distinct规则、图、映射、画像、query/metric/kernel须新结果与计时。
''')
s=read(C/'state.json');s.update(status='SESSION5_E72_COMPLETE',stage='E72_COMPLETE',stage13_status='COMPLETE_DISTINCT_HUB_CONTROL_STOP_WALL_GATE',total_new_NSG=3430244,total_HNSW=3986976,session5_NSG=194304,session5_HNSW=193920,session5_builds=0,session5_synthetic_HNSW=512,session5_synthetic_builds=4,native_pids=[],next_action='Independent E73 exact duplicate profile compaction protocol; E72 wall gate failed and no width tuning.');dump(C/'state.json',s)
(C/'handoff.md').write_text('# 第5串行会话进行中\n\nE72完成，原默认不变，整日目标未完成；会话14:17:57前安全边界。E72双集接续门失败，Y相对P10局部+73/失败−6保留，无QPS。下一E73精简同hub完全重复画像尚未实现；E34最终及held-out隔离。当前新增194304 NSG/193920 HNSW，合成另4图/512 HNSW；无native。\n\n[E72](stage13_distinct_hub_width_v1/report.md) · [前会话](handoff_session4.md)。\n')
after=O/'reviews/root_after';after.mkdir()
for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:shutil.copy2(R/x,after/x.replace('/','__'))
dump(O/'reviews/figure_review.json',dict(status='PASS',figure='distinct_control.png',viewed_by='session5',layout_and_values=True))
check(O/'reviews/prequery_freeze.json');resources();freeze(O/'reviews/final_artifact_freeze.json',[p for p in O.rglob('*') if p.is_file() and p.name!='final_artifact_freeze.json']+[history]);print('SEALED_E72')
