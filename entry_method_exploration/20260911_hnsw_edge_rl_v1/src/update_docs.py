from common import *
P='entry_method_exploration/20260911_hnsw_edge_rl_v1'
C='HNSW_EDGE_RL_COMPLETE_WEBVID_SIGNAL_NO_DUAL_GAIN'
assert read(O/'state.json')['conclusion']==C
card=R/'experiment_history/22_hnsw_edge_rl.md';assert not card.exists()
card.write_text(f'''# 22 强化学习直接训练HNSW图边（E33）

2026-09-11完成，状态`{C}`。用户明确希望训练改变HNSW图，并授权推进小实验。本轮完成真正的图边RL闭环及真实开发评测；WebVid主图过局部门，Yandex失败，双集门停止，未开展新validation/QPS。

## 问题、机制和旧版本区别

[E32](21_direct_reward_policy.md)在固定C8内选择完整三入口，不训练HNSW边。E33固定当前默认画像、H815/821、映射和原NSG，给Micro-HNSW底层原边设置独立Bernoulli logit。真实HNSW遍历时抽样keep/remove，输出三个真实入口进入原NSG；GT在搜索返回后评分，REINFORCE用终局命中和总NDC更新边概率。不是PPO、神经网络教师或坐标变换；不会改变原NSG大图。

奖励`hits−hits_base−.1(totalNDC/totalNDC_base−1)`，每query此前奖励EMA基线、熵系数.001、Adam600步、lr.025余弦到.0025、batch128、clip1/logit±4。策略不依赖query，导出概率≥.5边的静态图后，线上只需原hnswlib，不含采样/网络或C8全H填充。方法依据及与原TRPO论文区别见[研究说明](../{P}/literature/method_basis.md)。

固定出树/入树和每节点min(2,原出度)条最近边，保持强连通；节点画像、外部ID、层级、上层邻接逐位不变。首版预检过严要求原出度≥2，WebVid38个合法单边节点导致训练前停止；保留原协议/源码/binary，以v2修正结构条件，未调整奖励、seed、split或开发门。首次失败NSG/HNSW查询及optimizer均0，[修正](../{P}/structural_preflight_repair.md)。

## 数据、训练与图结构

原fit20K固定排列为train16K/monitor4K，monitor本轮不参与更新，全部样本有历史使用。两集×RL seed20260911/20260912各600步，共307200条新反馈；每100步导出静态图，按最高monitor奖励选非零checkpoint。各seed另有逐节点保留边数匹配的随机控制。cal只选主seed，audit不选模型。

WebVid两个seed选step600/400，monitor ΔRecall +.0600/−.0300pp；Yandex选step300/100，为−.0675/+.0500pp。cal最终选WebVid seed20260912、Yandex seed20260911，分别删除2301/7530=30.56%、3090/9055=34.12%的底层边。正信号与负信号分开保留，训练末段采样奖励仍均低于原图，不能说已经稳定收敛到更优图。

## 开发结果与随机控制

每集cal/audit各1024query，原图、两个RL、对应两个随机图，20个L128点。主图相对原图：

| 数据集/split | ΔRecall pp | 总NDC变化 | RL−匹配随机 pp |
|---|---|---|---|
| WebVid cal | +0.3418 | −0.978% | +0.2832 |
| WebVid audit | +0.1270 | −0.985% | −0.0684 |
| Yandex cal | −0.1660 | −0.424% | +0.1465 |
| Yandex audit | −0.2734 | −0.350% | −0.3125 |

WebVid两点均满足质量/成本门，合并奖励胜对应随机，保留单集线索；但audit随机图本身+0.1953pp，不能归因全部改善于学习。Yandex两个RL seed在两个split四点皆负，主seed还未胜合并随机奖励，双集门失败。RL−随机的全部配对区间覆盖0；WebVid cal参与了seed选择，其相对原图正区间未校正选择，不是独立显著性结果。

路由NDC约降低18%–19%，NSG NDC增加约.19%–.38%，总成本仅减少不足1%；无wall，不换算QPS。依原门停止后续validation，没有只为WebVid追加性能矩阵。当前默认仍是WebVid GT10-soft-t1、Yandex GT10-hard的原HNSW，未替换索引。

## 成本、验收和边界

实际NSG500736调用、预留500992/1200000；HNSW508608查询单列；旧C8标签0。四次训练含monitor共218.20s，训练总进程255.41s含加载/基线/保存等，线程1/RSS约10.25GiB。所有开发评测CPU15、实际进程/OMP线程1、OMP/BLAS/MKL1。

all-keep/骨架/随机mask的hook与物理删边HNSW一致；原NSG/计数和完整开发plain/count通过。16种小图枚举/有限差分/基线不变性通过；独立NumPy重放2400次更新，24个非零checkpoint最大误差<2.4e−15。36份导出图的坐标/映射/层级/上层保持、底层mask/连通验证通过；479680保存输出独立GT复算，原默认完整回归E32。

原E32完整目录及实际依赖SHA保护，更早9211文件只stat身份保护；旧validation原始输入未hash/解码，新validation未评测，held-out未读/hash。只有一个原HNSW建图seed与两个RL seed、全部split重复历史使用，无正式性能GO。本轮只能评价保骨架、只删底层原边的静态策略；加边、重连、坐标偏移和在线逐跳网络均未测试。

- [完整报告](../{P}/report.md)、[协议](../{P}/protocol.md)、[开发门](../{P}/results/development_gate.json)、[状态](../{P}/state.json)、[调用账](../{P}/logs/jobs.json)。
- [训练与静态图](../{P}/figures/training_and_static_graphs.svg)、[开发/成本图](../{P}/figures/development_and_cost.svg)、[结构图](../{P}/figures/graph_structure.svg)、[Excel](../{P}/chart_data.xlsx)。
- [环境](../{P}/src/environment_v2.cpp)、[训练](../{P}/src/train_v2.py)、[开发控制器](../{P}/src/development.py)、[训练独立复核](../{P}/reviews/training_independent_verification.json)、[最终验收](../{P}/reviews/final_audit.json)。

预算已收口。后续先区分局部删边信号与学习相对随机的增益；若另行研究坐标位移，需要独立协议和重建HNSW/真实奖励闭环。新目标见根[s-target](../s-target.md)，不重启此冻结runner。
''')
p=R/'experiment_history/README.md';s=p.read_text();anchor='| [21 直接收益策略]';lines=s.splitlines();idx=next(i for i,x in enumerate(lines) if x.startswith(anchor));lines.insert(idx+1,'| [22 HNSW图边RL](22_hnsw_edge_rl.md) | E33：真实轨迹REINFORCE、固定静态删边图、双seed与逐节点同出度随机控制；WebVid局部信号/Yandex开发失败，无QPS |');p.write_text('\n'.join(lines)+'\n')
p=R/'s-experiment.md';s=p.read_text();anchor='| E32 直接真实收益策略';idx=s.index(anchor);s=s[:idx]+f'| E33 HNSW图边强化学习 | 两集双RL seed、4×600更新，真实HNSW→NSG奖励与静态图导出；20开发点含逐节点同出度随机控制 | `{C}`；WebVid主图局部门通过、audit未胜随机，Yandex失败；无新validation/QPS | [22 HNSW图边RL](experiment_history/22_hnsw_edge_rl.md) |\n'+s[idx:];s=s.replace('当前最近完成实验已为E32','当前最近完成实验已为E33').replace('二十一份详细卡片','二十二份详细卡片');p.write_text(s)
(R/'summary.md').write_text(f'''# ACSG 当前实验总结

2026-09-11。最近完成E33，状态`{C}`。[完整报告]({P}/report.md)、[历史22](experiment_history/22_hnsw_edge_rl.md)、[状态]({P}/state.json)。

## 当前结论

本轮已实现用户希望的“训练改变HNSW图、再直接遍历”之边结构版本：REINFORCE在真实HNSW→NSG轨迹上学习底层边的保留概率，最后导出静态图。WebVid有局部收益，Yandex两seed四个开发点均下降；学习相对匹配随机删边的稳定优势未建立。双集开发门失败，未开展新validation/QPS。

当前默认仍为WebVid GT10-soft-t1/Yandex GT10-hard的原HNSW。原GT10/E28局部前沿及E32同C8直接收益信号保留；E33只评价此次保骨架删边，不否定全部RL、重连或坐标训练。

## 实际训练与图变化

固定H815/821、默认画像、真实映射、HNSW M16/efConstruction200/efSearch10/seed20260828和原NSG/raw-IP。非保护边独立Bernoulli logit；终局奖励为真实命中差减.1倍相对总NDC变化，每query历史奖励EMA基线、熵正则和Adam600步。4次×600更新、batch128，共307200条新反馈，没有复用C8标签。

原fit20K分train16K/monitor4K，每100步导出静态图选checkpoint；全部样本有历史使用。两个seed的monitor ΔRecall为WebVid+.060/−.030pp、Yandex−.0675/+.050pp，未稳定改善。cal再选主seed后冻结，audit不选模型。

主图WebVid删2301/7530条边，Yandex删3090/9055条边；保留强连通骨架。全部36份checkpoint/selected/随机图已核对，坐标、映射、层级和上层邻接不变。线上只需加载静态图，无策略网络或C8全H扫描。[图结构]({P}/figures/graph_structure.svg)。

## 开发与控制

每split1024query，下表为cal选主图；完整两个seed和逐节点同出度随机控制均见报告。

| 数据集/split | RL−原图 ΔRecall pp | 总NDC变化 | RL−随机 ΔRecall pp |
|---|---|---|---|
| WebVid cal | +0.3418 | −0.978% | +0.2832 |
| WebVid audit | +0.1270 | −0.985% | −0.0684 |
| Yandex cal | −0.1660 | −0.424% | +0.1465 |
| Yandex audit | −0.2734 | −0.350% | −0.3125 |

WebVid主图过局部质量/成本门，合并奖励胜随机，保留信号；但audit随机删边+0.1953pp，高于学习图+.1270pp。Yandex门失败，未追加WebVid单集性能矩阵。RL相对随机的全部区间覆盖0；WebVid cal参与seed选择，正区间不能作为独立显著性结论。[开发门]({P}/results/development_gate.json)、[开发/成本图]({P}/figures/development_and_cost.svg)。

路由NDC约减少18%–19%，NSG NDC增加.19%–.38%，总节省不到1%；没有wall，不能换算QPS。当前结果没有稳定默认替换或端到端性能GO。

## 成本、验收与修正

实际NSG500736、预留500992/1200000，HNSW508608查询单列；20开发点、479680保存输出独立GT复算。训练含固定monitor218.20s，训练总进程255.41s包含加载/基线/保存，线程1；开发CPU15、进程/OMP/BLAS/MKL1。NumPy独立重放全部2400次更新，最大checkpoint误差<2.4e−15；hook/物理删边、原NSG、plain/count与旧默认回归通过。

首版结构预检在任何query/优化前因38个合法单边节点停止，v2将保留最近边数修正为min(2,原出度)，全部原件保留，奖励/收益门不变。[修正]({P}/structural_preflight_repair.md)。旧E32和实际依赖SHA保护；更早9211文件仅stat保护，未把它称新SHA验证。旧validation原始输入未hash/解码，held-out未读/hash。

[报告]({P}/report.md)、[Excel]({P}/chart_data.xlsx)、[最终验收]({P}/reviews/final_audit.json)齐备；下一阶段见[s-target](s-target.md)。本轮预算收口，没有排队的训练/ANN任务。
''')
(R/'s-target.md').write_text(f'''# ACSG 下一阶段方向与实验接续

2026-09-11。E33已完成，状态`{C}`。[报告]({P}/report.md)、[历史22](experiment_history/22_hnsw_edge_rl.md)、[开发门]({P}/results/development_gate.json)。用户授权的本次HNSW图训练小实验已收口，无排队训练/ANN/validation任务。

## 当前判断与保留信号

本轮是实际REINFORCE图边训练：当前Micro-HNSW底层删边，原画像/上层/真实ID/NSG固定。WebVid主图相对原图cal/audit +.3418/+.1270pp，路由成本降低但总NDC只约−.98%；audit未超过同出度随机图。Yandex两seed四个开发点均负，双集门停止。不能把此轮结论扩大成全部图结构/坐标RL无效。

默认继续WebVid GT10-soft-t1/Yandex GT10-hard的原HNSW。GT10/E28已有局部前沿、E32同C8目标收益和E33单集删边信号分别保留；三个问题的作用位置不同，不能混称同一方法或互相代替性能证据。

## 优先一：确定学习相对简单删边的增量

E33已提供逐节点同出度随机控制、完整两个seed、训练轨迹和paired区间。先完整核对[控制表]({P}/results/csv/rl_vs_random.csv)与[策略诊断]({P}/results/csv/policy_diagnostics.csv)：WebVid audit RL−随机−.0684pp，Yandex主图audit−.3125pp；全部RL−随机区间覆盖0。多数边有数百至上千次暴露，约41%–60%保留概率仍在.45–.55，不能直接把失败解释成“没训练”或用更多epoch保证成功。

若另立复现，应锁定主图/提取阈值/奖励/样本，使用未参与选择的开发数据和多个预定匹配随机图；至少比较原图、冻结学习图、同逐节点出度随机及简单几何删边。分别检查质量、路由/NSG/总成本和跨seed稳定性。样本GT与新query来源须先核验；历史cal/audit/validation不能重新称盲测。先要求学习稳定胜简单控制，再决定是否值得完整同机单线程前沿；无增量则停止此删边表示。

## 优先二：若研究“导航坐标偏移”，建立真正闭环

本轮没有改坐标、加边或重连。坐标路线应明确仅修改入口的导航画像，原base向量、真实IP检索目标、H/映射和NSG不变；每个训练动作后重建/修复HNSW，运行真实遍历→三个入口→原NSG，再反馈收益。不能只训练一个不经过实际HNSW的代理目标，却称为图偏移RL。

最小设计宜把动作限制在低维、带半径约束的共享位移或少量局部边交换，记录构图耗时和真实反馈调用。对照应包含原图、同预算随机扰动/无学习结构搜索、E33删边，以及有相同表示的监督训练；明确与E28–E32监督画像/候选重排的实质差异。不可直接向离散HNSW构图反传；若采用策略梯度/黑盒估计，须核验估计与真实图变化，并单列方差与训练成本。

这只是尚未实施的候选方向，不能据E33的接口通过认定方法可用。下一份协议需在新实验前锁定唯一主变量、奖励单位、信赖域、候选动作、query split、标签兼容范围、优化与构建预算、模型选点和退出规则。已有C8标签不覆盖一般新图返回的全部三元组；新组合必须实际搜索，不当作零效用。

## 优先三：收益通过后的单线程性能验证

路由只占当前总计算的一小部分：E33主图路由约−18%至−19%，NSG约+.19%至+.38%，总NDC不足−1%。因此任何新方法须明确改善最终入口质量还是减少路由工作；正式结论依赖完整端到端wall，不能只以删边数、路由NDC或同L Recall认定性能GO。

质量/成本和控制门通过后，才能按新协议执行相同CPU15、进程/OMP/BLAS/MKL1、一次一个方法、无训练并发的Recall–QPS曲线。预锁L、完整warmup/轮换重复、共同Recall区间、输入/图/模型身份、调用/时间/内存/磁盘cap；记录GT-inclusive离线成本的已知与缺项。held-out不属于本轮访问范围。

## 接续要求

完整读AGENTS→summary→spec→本文件→s-experiment，再进入[历史22](experiment_history/22_hnsw_edge_rl.md)及原协议/修正/模型/开发门。有效训练实现是`environment_v2.cpp/native_v2.py/train_v2.py`；第一版只是保留的结构预检停止原件。冻结产物不得覆盖重跑。

接续指令示例：先只读核对E33两seed完整训练/monitor/开发与随机控制，明确要验证学习增量、坐标变化还是结构交换，提出一个含对照、数据/GT依赖、构图和反馈成本、选点与停止规则的最小新协议。当前方向均未自动追加训练/ANN/validation；有新用户授权后在独立版本执行，不凭旧NO_GO额外制造确认流程。
''')
p=R/'spec.md';s=p.read_text();old='架构与实现事实核对至2026-09-11（E32完整动作期望收益、同C8在线策略与真实开发验收已实现；原Fast/kernel不变）';new='架构与实现事实核对至2026-09-11（E33真实轨迹HNSW底层边RL、静态图导出与开发验收已实现；原Fast/NSG kernel不变）';assert old in s;s=s.replace(old,new,1)
s+=f'''

## HNSW底层边强化学习 v1（E33，2026-09-11）

独立[协议]({P}/protocol.md)固定当前默认画像、H/真实ID、原NSG/IP，只改变Micro-HNSW底层已有有向边。初始结构预检的≥2出度要求被[修正]({P}/structural_preflight_repair.md)为min(2,原出度)，原件保留。有效实现为[environment_v2.cpp]({P}/src/environment_v2.cpp)、[native_v2.py]({P}/src/native_v2.py)、[train_v2.py]({P}/src/train_v2.py)，不修改主hnswlib或ACSG源码。

- `Environment`序列化原M16/efConstruction200/efSearch10/seed20260828小图，按原邻接顺序给底层边编号；保护原入口BFS出树/入树及最近原边。原图必须强连通，导出不得增边或变更画像/ID/上层。
- 训练编译独立hnswlib副本，`searchBaseLayerST`仅在未visited目标上调用keep/remove hook；删除不标visited、不计算距离。保存每episode实际暴露edge/action/offset、三入口、NSG返回ID/距离/route与graph NDC。概率策略只依赖边ID，GT由Python在真实输出返回后评分，不进入遍历。
- C接口`e33_run`提供采样或固定mask轨迹；`e33_static`加载物理删边图并关闭hook，供真实monitor；`e33_export`导出静态HNSW。`e33_parity`核对hook与物理图的入口/计数及原NSG IDs/float bits/NDC。原/新原始API不具备坐标RL或新增边动作。
- REINFORCE训练独立边logit，每query历史奖励EMA基线和熵正则；train16K/monitor4K只来自原fit20K，4×600步。实际完整轨迹、logit/optimizer/query-baseline checkpoint、静态图和逐节点出度匹配随机图均冻结。独立NumPy重放2400更新和36图结构校验已通过。
- [Policy]({P}/src/benchmark_with_nsg.cpp)新增`graph_file`：加载外部静态HNSW并验证每内部节点的画像bytes/外部ID与W/mapping相同，plain/count从同一序列化图加载。正式[评测器]({P}/src/evaluate.cpp)编译原hnswlib，不含训练hook；原NSG、GT后评分、CPU15/线程1和完整wall合同保持。
- [开发控制器]({P}/src/development.py)冻结全部模型后运行cal5方法/集、按cal奖励选seed后冻结、再audit全部模型；20点20480输出已独立评分/原默认回归、plain/count/reference通过。条件五L×5轮wall接口已实现，但本轮双集门失败，未执行validation/QPS。

图边、画像、H/映射、构图参数、split或NSG/L/K/metric改变均需重建相关环境/轨迹/选点和评测。旧C8/独立入口标签不能当新图三入口完整反馈；本轮新增307200真实训练反馈，C8缓存复用0。旧资产保护区分当前E32/实际依赖SHA与更早链stat；旧validation仅stat核对，未hash/解码，held-out未读/hash。结果由[summary](summary.md)和[历史22](experiment_history/22_hnsw_edge_rl.md)维护，接口通过不升级为性能GO。
''';p.write_text(s)
dump(O/'reviews/document_update.json',dict(status='WRITTEN_PENDING_REVIEW',files=[str(x) for x in [card,R/'experiment_history/README.md',R/'s-experiment.md',R/'summary.md',R/'s-target.md',R/'spec.md']],order='history -> index -> summary -> target -> spec',source_before=str(O/'source_before')))
print('ROOT_DOCUMENTS_UPDATED',flush=True)
