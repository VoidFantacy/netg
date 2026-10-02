from common import *
assert read(O/'state.json')['status']=='COMPLETE_UTILITY_PROPOSALS';cost=read(O/'results/cost.json');assert not (O/'root_after').exists()
(R/'experiment_history/76_utility_proposals.md').write_text('''# 76｜完整策略收益提出目标后实际单边筛选（E87）

2026-09-13第9会话，双集预锁门FAIL，停止此效用目标提议/单边筛选版本。Web局部修复保留，Y零更新不称新方法收益。0新QPS。

E86筛选原几何候选，本版只用fit真实P优于compact的完整三入口查询，向P独有hub的最高compact画像slot提出边。源为compact首返回slot，正命中差为提议权重，每源最高票且至少2query支持，最多64/集。完整策略差只提议，不作单边因果信用；候选逐条实际加边测全fit原NSG，再按原全正/两半非负/失败不增/成本门筛选，合并重新实测。在线原compact W、真实H/原NSG/rawIP及原全部边保持，静态图一次路由，无新模型预测。

Web896个P更好query产生1542有效事件/1333票对，53候选，与E84/E86仅6/4重合；Y267产生409事件/384对，9候选，重合0/0。Web53边17正/3负/33平，16接受，独立收益和118、实际合并94，3query非加性；Y9全部命中差0、无接受边，两个最终图逐字等于原compact。完整提议、合法性、权重/支持、目标及近邻控制均独立复算。

| aux7952 | 对P：净命中/失败变化 | 对compact | 对E84 | 对E86 | 对控制 |
|---|---|---|---|---|---|
| Web | −43/+8 | +16/−3 | −26/+1 | −2/0 | +16/−3 |
| Y | +120/−13 | 0/0 | +4/0 | +4/0 | 0/0 |

Web fit并图+94/失败−4、两半41/53；aux对compact两半7/9、救回3/新增0，但不及P/E84/E86。原compact对P正收益820保留809、丢11、新增4；避免原损失26，新增/放大损失3。Y所有相对其它图的改善是回到compact，不是学习增益。原门停止，不扩候选、阈值或按aux重训。

新NSG194718=训练414（111新唯一键plain/count+192回归）+辅助194304；HNSW2914432=训练2720512+辅助193920。6物理导出含4非零边安装（包括2首边回归图）和2个Y零更新副本；0普通构图/编译/GT/梯度。提议进程tool wall0.411s含import/hash/冻结，单独数学时间未知；训练53.401s、辅助150.562s为操作wall，不作QPS。继承GT/P与E86原compact缓存成本分开。

复用同SHA E86 route helper/E69 NSG/E73 evaluator，实际CPU15、进程和各数值库1线程，所有工具退出0。154单边变化patch、111新键、合并图/6图完整bytes、原32三路/首边128真实回归、96960集合/mask、63616四旧对照全字段、80800七slot、384原kernel均通过。413失败并集、173状态变化、2478个六配置全GT/入口/返回单元保存。

fit20K含旧train/monitor；aux7952/两半、cal/audit历史暴露，接受反馈算训练。E34原始query/GT/row未打开，held-out未读。最终准备件只读E34/E74配置、模型及输入stat；查历史23旧汇总在模型冻结后且未回流任何选择。

[报告](../entry_method_exploration/20260913_until2100_v1/stage28_utility_proposals_v1/report.md) · [协议](../entry_method_exploration/20260913_until2100_v1/stage28_utility_proposals_v1/protocol.md) · [提议](../entry_method_exploration/20260913_until2100_v1/stage28_utility_proposals_v1/src/propose.py) · [训练](../entry_method_exploration/20260913_until2100_v1/stage28_utility_proposals_v1/src/train.py) · [门](../entry_method_exploration/20260913_until2100_v1/stage28_utility_proposals_v1/results/gate.json) · [成本](../entry_method_exploration/20260913_until2100_v1/stage28_utility_proposals_v1/results/cost.json) · [独立提议核验](../entry_method_exploration/20260913_until2100_v1/stage28_utility_proposals_v1/reviews/proposals_independent.json) · [训练核验](../entry_method_exploration/20260913_until2100_v1/stage28_utility_proposals_v1/reviews/training_verification.json) · [查询核验](../entry_method_exploration/20260913_until2100_v1/stage28_utility_proposals_v1/reviews/verification.json)
''')
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n[76 E87完整策略收益提议边](76_utility_proposals.md)：实际53/9候选、16/0边合并，Web局部修复、Y零更新，双集门失败。\n')
p=R/'s-experiment.md';s=p.read_text().replace('| E86 真实单边效用筛边','| E87 真实策略收益提议目标 | P优于compact完整策略提议、53/9实际边、16/0合并 | `COMPLETE_UTILITY_PROPOSALS`；Web对compact+16/失败−3仍不及P，Y零更新，194718 NSG/0QPS | [76 效用提议](experiment_history/76_utility_proposals.md) |\n| E86 真实单边效用筛边',1).replace('当前最近完成记录为E86真实单边效用筛边','当前最近完成记录为E87真实策略收益提议边');p.write_text(s)
(R/'summary.md').write_text('''# ACSG 当前结果摘要

2026-09-13第9串行会话完成E86/E87两组离线静态小图改进，双集完整接受门均FAIL；保留Web局部修复，默认未替换。整日21:00目标未完成，E34最终矩阵尚未运行。

| 方法/数据 | 接受边 | fit并图对compact：净命中/失败变化 | aux7952对compact | aux对匹配P |
|---|---:|---|---|---|
| E86 Web | 29 | +191/−13 | +18/−3 | −41/+8 |
| E86 Y | 3 | +13/−1 | −4/0 | +116/−13 |
| E87 Web | 16 | +94/−4 | +16/−3 | −43/+8 |
| E87 Y | 0 | 0/0 | 0/0 | +120/−13，全部继承compact |

E86直接测实际加边的全fit NSG效用后筛选原几何候选；E87改变候选来源，用P优于compact的完整策略响应提出缺失hub目标，再实际测边。策略差只提议，不作单边信用。两版均测合并后的相互作用，线上仍固定小图/三真实入口/原NSG。原画像/全部旧边/base/GT/rawIP不变。

E87 Web aux两半+7/+9，救回3/新增0，但对E84−26命中、对E86−2，均不及P。E86 Web两半+6/+12、救回4/新增1。训练增益不能当泛化或性能结论；Y E87零更新明确不是新方法收益。两版停止固定规则，不扩候选/阈值或读最终反馈调参。

新增365054 NSG/7756544 HNSW、10非零边安装（含4首边回归图）+2零更新副本，4离线筛边拟合，0普通构图/梯度/GT/新增QPS。E86编译13.345s，两版训练/辅助操作合计412.247s，含load/count/cache/I/O，不作QPS。继承GT/P总成本未知。所有ANN实际CPU15、进程与各库1线程、串行；完整集合/mask、缓存/图字节、原kernel与旧对照回归通过。

E87完整六配置失败并集413条、173状态变化，全部GT10/入口/返回保存。P-fit20K含旧train/monitor；aux7952/两半、cal/audit历史使用，接受反馈计训练。E34最终原始query/GT/row和held-out本会话未打开；晚间准备仅配置/模型及输入stat，不是最终选择。

旧局部信号保持：E84 Web对compact+42/失败−4仍不及P；E73/E74 Y五L对P命中+99/+59/+38/+1/+15、失败−10/−7/−4/−1/0，但五轮QPS范围跨零，约1.9%–3.0%只作描述性插值。最近完整QPS仍E74，不与本轮质量点拼接。

[E86报告](entry_method_exploration/20260913_until2100_v1/stage27_edge_utility_v1/report.md) · [E87报告/失败图](entry_method_exploration/20260913_until2100_v1/stage28_utility_proposals_v1/report.md) · [最近完整QPS曲线](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/report.md) · [晚间准备件](entry_method_exploration/20260913_until2100_v1/session9_final_preparation/readme.md) · [下一阶段](s-target.md)。详细旧实验均在s-experiment和experiment_history，根文档前件已快照。
''')
p=R/'s-target.md';s=p.read_text();start=s.index('2. 下一实质方向');end=s.index('3. 优先保证',start);s=s[:start]+'''2. E87已完成：用真实P优于compact提出53/9新候选，16/0接受边；Web aux对compact+16/失败−3，仍不及P/E84/E86；Y零更新。停止固定提议/筛边规则。下一步先从冻结输出做0新query诊断，分清目标在既有七slot/前三hub的排名资格、实际单边是否改入口及NSG收益；不能由返回集推断已访问/扩展路径，也不把几何排名参照当反事实搜索。所有新增方向仍独立前瞻协议。\n'''+s[end:];s += '\n晚间计时/调用预算与兼容接口已核对，见[final preparation](entry_method_exploration/20260913_until2100_v1/session9_final_preparation/readme.md)；只是元数据草稿，无最终选型/输入载荷读取或可执行runner。需实际冻结候选后再生成完整2000行矩阵，勿直接跑旧2048脚本。\n';p.write_text(s)
p=R/'spec.md';p.write_text(p.read_text()+'''\n\n## E87 效用提议与第三旧缓存来源（2026-09-13）

[propose.py](entry_method_exploration/20260913_until2100_v1/stage28_utility_proposals_v1/src/propose.py)在fit真实P命中严格优于compact时，对P独有hub选compact内最高query内积slot，以完整策略差加权提议；保存全事件/source rows/两个完整三入口与hit、合法边/总权重/独立query支持。每源先argmax再support≥2、全局最多64，和旧几何投票不同。此差值不是单边效用，仍复用E86同SHA实际边环境全fit测量。

[train](entry_method_exploration/20260913_until2100_v1/stage28_utility_proposals_v1/src/train.py)的旧source_code=0/1/2为E66 P/mode及E86 compact；3为新完整三入口键。query/GT/namespace/图核/IP/L128/K10/完整入口键与新routeNDC合同保持，输出兼容baseline/变化patch/完整并图。无合格边的导出必须记录为零更新原图副本，不计新构图或非零边安装；在线API和NSG均无变化。实际six-policy接受回归四旧方法，完整wall接口未在本版启动。任何提议/筛边/图/数据改变仍使对应标签与性能失效。\n''')
(O/'root_after').mkdir()
for f in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:shutil.copy2(R/f,O/'root_after'/f)
c86=read(E86/'results/cost.json');state=read(C/'state.json');state.update(status='SESSION9_E86_E87_COMPLETE_DIAGNOSIS_NEXT',stage28_status='COMPLETE_UTILITY_PROPOSALS_NO_GATE',session9_NSG=cost['NSG']+c86['NSG'],session9_HNSW=cost['HNSW']+c86['HNSW'],session9_edge_installs=10,session9_zero_update_copies=2,session9_builds=0,total_new_NSG=5360806+cost['NSG']+c86['NSG'],total_HNSW=5843808+cost['HNSW']+c86['HNSW'],session9_graph_supervised_fits=4,session9_development_QPS_points=0,session9_wall_batches=0,day_goal_complete=False,native_pids=[],pending_tool_sessions=[]);dump(C/'state.json',state)
print('E87_DOCUMENTS_SYNCED')
