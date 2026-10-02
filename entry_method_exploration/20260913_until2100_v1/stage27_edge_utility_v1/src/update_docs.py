from common import *
assert read(O/'state.json')['status']=='COMPLETE_EDGE_UTILITY';cost=read(O/'results/cost.json');assert not (O/'root_after').exists()
card='''# 75｜真实单边效用筛选静态小图（E86）

2026-09-13第9串行会话，双集预锁接受门FAIL，本固定64/47几何候选与筛边版本停止，0新QPS。Web对compact局部修复保留，训练收益不当性能结论。

固定E73 compact全部W/真实H/映射/原边/上层及原NSG/rawIP，取E84按票数排序前64/47边。每条独立实际加边、全fit20K真实HNSW→原NSG响应；全量净命中正、两半非负、失败不增、总NDC≤1.01筛选。合格边合并后重新实际测量，并在相同源节点加最近其他hub边作度匹配控制。E33是原边删除，E84是几何投票，本版直接测加边效果；候选来源仍受几何排名限制，不能把完整三入口教师直接当单边信用。

Web64边31正/13负/20平，29条接受，单边相对原compact净命中之和235、合并实测191；16query非加性，含重复作用与交互。Y47边3正/1负/43平，3条接受，单边和/合并均13。并图fit两半Web97/94、Y9/4；失败−13/−1。训练全池筛选及继承画像都有历史暴露。

| aux7952 | 对P：净命中/失败变化 | 对compact | 对E84 | 对度匹配控制 |
|---|---|---|---|---|
| Web | −41/+8 | +18/−3 | −24/+1 | +18/−3 |
| Y | +116/−13 | −4/0 | 0/0 | 0/0 |

Web对compact救回4/新增1；小幅修复不足超过原P/E84。Y主要继承原compact收益，训练新增正值未迁移。全部GT成员增损、query净增损、原收益保留/丢失、新损伤与各半门保留，不扫阈值/边数。完整413失败并集、173状态变化、2065个五方法完整GT/入口/返回单元保存。

新NSG170336=训练8416+辅助161920；HNSW4842112=训练4680512+辅助161600。6静态安装含2首边回归图，2离线筛边拟合，0普通构图/梯度/新GT。编译13.345s，训练操作77.107s、辅助操作131.177s，均不当QPS；继承GT/P总成本未知。原kernel不改，CPU15/实际进程及各库1线程，完整真实工具terminal0。

effective native_training.json使用既有exact20K文件，与E66前缀query/GT/rows逐字一致；原准备native.json的22048容器模板未执行且保留。111候选全route plain/count、合法缓存完整键/全部新增4112唯一三入口、合并图和6图字节恢复/旧边可达性、原32三路与首边128物理回归通过；独立集合/mask、全部7slot、47712旧P/compact/E84输出恢复通过。图初版负值标签留白修正保存initial源/图，不改raw。

P-fit20K=router_train[10000:30000]含旧train/monitor；aux=[2048:10000]、两半、cal/audit历史暴露，接受反馈计训练。E34最终原始输入/held-out本版未打开。原E86门保持，后续若改变候选来源必须独立前瞻协议，不扩本版候选。

[完整报告](../entry_method_exploration/20260913_until2100_v1/stage27_edge_utility_v1/report.md) · [协议](../entry_method_exploration/20260913_until2100_v1/stage27_edge_utility_v1/protocol.md) · [训练源码](../entry_method_exploration/20260913_until2100_v1/stage27_edge_utility_v1/src/train.py) · [原配置](../entry_method_exploration/20260913_until2100_v1/stage27_edge_utility_v1/config.locked.json) · [门](../entry_method_exploration/20260913_until2100_v1/stage27_edge_utility_v1/results/gate.json) · [训练核验](../entry_method_exploration/20260913_until2100_v1/stage27_edge_utility_v1/reviews/training_verification.json) · [查询核验](../entry_method_exploration/20260913_until2100_v1/stage27_edge_utility_v1/reviews/verification.json) · [成本](../entry_method_exploration/20260913_until2100_v1/stage27_edge_utility_v1/results/cost.json)
'''
(R/'experiment_history/75_edge_utility.md').write_text(card)
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n第9串行会话：[75 E86真实单边效用筛边](75_edge_utility.md)，训练正值与Web局部迁移保留，双集完整门失败。\n')
p=R/'s-experiment.md';s=p.read_text().replace('| E85 query向量路由前选择', '| E86 真实单边效用筛边 | 固定64/47边全fit真实响应、29/3边合并与双集aux | `COMPLETE_EDGE_UTILITY`；Web对compact+18/失败−3、Y−4/0，双集门FAIL，170336 NSG/0QPS | [75 单边效用](experiment_history/75_edge_utility.md) |\n| E85 query向量路由前选择',1).replace('当前最近完成记录为E83同hub补边','当前最近完成记录为E86真实单边效用筛边');p.write_text(s)
p=R/'summary.md';s=p.read_text();p.write_text(s.replace('# ACSG 当前结果摘要\n','# ACSG 当前结果摘要\n\n第9会话E86真实单边效用筛边完成，双集完整接受门FAIL。Web29条接受边的fit并图+191命中/失败−13，aux对compact+18/−3但对P−41/+8、对E84−24/+1；Y3条fit+13/−1，aux对compact−4/0。保留Web局部修复，训练收益不作性能结论；固定几何候选/筛边版本停止。新增170336 NSG/4842112 HNSW，6静态安装/0普通build/0新QPS，413失败并集与完整返回保存。[E86报告](entry_method_exploration/20260913_until2100_v1/stage27_edge_utility_v1/report.md)。整日目标未完成，E34最终未打开。\n',1))
(R/'s-target.md').write_text('''# ACSG 下一阶段目标与接续

2026-09-13第9唯一串行会话，18:23:29前安全交接，整日21:00目标未完成。不启并行CLI/子代理。

1. E86已完成：真实单边训练筛选得到Web29/Y3边；Web aux对compact+18命中/失败−3仍不及P/E84，Y−4/0。原固定几何候选与筛边门失败，不扩64/47边、阈值/顺序。E84 Web+42/−4及E73/E74 Y局部信号保留。
2. 下一实质方向为候选生成使用真实完整三入口效用：仅从fit中P确实优于compact的查询提出缺失真实hub目标，完整三元组差只用于提议，不能作单边信用；仍必须实际加边测全池收益/损伤、冻结并图后独立辅助接受。另建E87协议/预算后才执行，当前只是设计。避免把E86筛几何候选的局部修复扩大成普遍学习结论。
3. 优先保证晚间最终完整矩阵。20:00停新训练、20:40停新query、21:00交付。在已暴露开发反馈冻结best_all/best_new及选择规则，再打开E34历史validation2000；最终反馈禁止回流训练/选型，held-out不自动开放。原NSG/Fast/GT10-hard及Web匹配soft/实际新方法，同批五L五轮CPU15/实际与各库1线程，完整独立route+NSG+output wall与逐query集合评分、zero失败救回/新增和三指标图。

第9资源：全部新输出192MiB，晚间64MiB/交接8MiB，新floor6.55GiB，初始6.869GiB；每新阶段前扣未用预算再核验，禁止清理历史。所有旧E82–E85门/产物保持。P-fit含旧train/monitor，aux7952及两半、cal/audit历史暴露，接受反馈算训练；元数据余行不证明项目未用。

[E86报告](entry_method_exploration/20260913_until2100_v1/stage27_edge_utility_v1/report.md) · [campaign](entry_method_exploration/20260913_until2100_v1/state.json) · [监督备注](/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md)。最近完整QPS仍[E74](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/report.md)，不能拼后续质量批次。最终候选尚未冻结。
''')
p=R/'spec.md';p.write_text(p.read_text()+'''\n\n## E86 独立单边干预与真实效用筛选（2026-09-13）

[routes.cpp](entry_method_exploration/20260913_until2100_v1/stage27_edge_utility_v1/src/routes.cpp)通过原E73 Policy仅public可见性副本，离线追加一个合法跨hub底层缺边；原全部邻接bytes保存、调用后恢复。全20K plain/count入口、labels、7slots/距离bits一致，输出route arrays/真实NDC；无NSG加载。最终物理图从原序列化文件只改degree和空槽，原W/labels/上层保持，在线直接用原E73 evaluator，无新在线模块/原kernel变化。

[train.py](entry_method_exploration/20260913_until2100_v1/stage27_edge_utility_v1/src/train.py)按冻结候选逐条从原图干预，复用E69同SHA显式三入口NSG。缓存键为dataset/namespace/row/query字节/完整canonical三入口/原NSG/kernel/rawIP/L128/K10/GT；新原生返回plain/count核验。baseline及并图完整aligned NPZ，单边保存变化rows/返回/来源码和完整routeNDC，另保存7slot变化patch及全route hashes；非变化结果精确重构，不填零或复用旧路由成本。E66双源与新键的source_code/index记录完整。

训练按全fit与固定两半/失败/成本门筛边后冻结并图，实际测量交互；同源同度近邻控制独立保存。effective native_training.json引用原exact20K文件，旧22048容器准备模板未执行且保留。辅助在全部训练模型冻结后执行，GT后评分/完整wall接口沿E73，本阶段timing_repeats=0。新边/筛选/候选来源/图/映射/数据或NSG身份变化均需新协议和真实反馈，不能复用旧单边响应模拟连续更图。\n''')
(O/'root_after').mkdir()
for f in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:shutil.copy2(R/f,O/'root_after'/f)
state=read(C/'state.json');state.update(status='SESSION9_E86_COMPLETE_NEXT_DESIGN',stage27_status='COMPLETE_EDGE_UTILITY_NO_GATE',session9_NSG=cost['NSG'],session9_HNSW=cost['HNSW'],session9_edge_installs=6,session9_builds=0,total_new_NSG=5360806+cost['NSG'],total_HNSW=5843808+cost['HNSW'],session9_final_feedback_used=False,session9_graph_supervised_fits=2,session9_development_QPS_points=0,session9_wall_batches=0,day_goal_complete=False,native_pids=[],offline_pids=[],pending_tool_sessions=[]);dump(C/'state.json',state)
print('E86_DOCUMENTS_SYNCED')
