from control import *

d=read(O/'results/diagnosis.json'); ss=d['contexts']; jobs=read(O/'logs/jobs.json')
v=read(O/'reviews/independent_verification.json');assert v['status']=='PASS'
rel=O.relative_to(R).as_posix();status='COMPLETE_FIXED_PROFILE_BATCH_DIAGNOSIS_STOP_BUDGET_EXPANSION'
table='| 数据集 / 固定点 | 区分命中query / 1024 | 主512方向余弦（data / total） | 35分组中位数（data） | 正余弦比例 | 稳定门 |\n|---|---:|---:|---:|---:|---|\n'
for s in ss:
    ds='WebVid' if s['dataset']==DS[0] else 'Yandex-IP'
    label='初始化' if s['context']=='zero' else '已选μ'
    table+=f"| {ds} / {label} | {s['discriminating_queries']} | {s['primary512_cos_data']:.4f} / {s['primary512_cos_total']:.4f} | {s['balanced512_median_data']:.4f} | {s['balanced512_positive_data']*100:.2f}% | 未过 |\n"
conclusion='固定参数和八个扰动后，将查询池扩大到1024，四个参数点的两组互斥512-query方向仍全部相反，预设稳定门四点均未通过。当前结果不支持继续增加同一训练器的batch/epoch预算；应先检查这些局部动作的收益为何相互抵消。它没有证明离线画像学习不可行，也没有单独证明共享表示不足。'
cost=f"两集共36864个正常返回、1728次parity NSG，合计38592次（硬限40000）；HNSW查询38016、普通构建36、optimizer更新0、新GT0。查询均CPU15/实际线程1，两个进程串行耗时{sum(j['wall_seconds'] for j in jobs):.3f}s，其中索引加载{sum(j['load_seconds'] for j in jobs):.3f}s、构建{sum(j['native']['build_seconds'] for j in jobs):.3f}s；含诊断计数、保存与检查，不是纯wall/QPS。峰值RSS WebVid {jobs[0]['peak_RSS_KiB']/1024/1024:.3f}GiB、Yandex {jobs[1]['peak_RSS_KiB']/1024/1024:.3f}GiB。"
report=f'''# E39 固定参数与查询批次诊断

2026-09-12。状态`{status}`。[冻结协议](protocol.md)、[配置](config.locked.json)、[逐点结果](results/diagnosis.json)、[独立评分](reviews/independent_verification.json)、[最终验收](reviews/final_audit.json)。

## 当前结论

{conclusion}

{table}

主方向在查询前固定为前512对后512；35组是同一1024池的互补重组，彼此相关，不能当35次独立实验。有限池中两半梯度之和固定，整体信号弱时互补方向容易相反；本结果描述该固定池的稳定性，不能用35组负值制造总体显著性。1024只有一个梯度估计，未测两个独立1024批次。

## 实际做了什么

复用E37 cal冻结的WebVid rl_20260921 step140、Yandex rl_20260922 step40，各加本run初始化μ0；沿用各checkpoint后一步的原八个ε/actions，不更新μ、不更换σ/rank。画像为W=normalize(P+0.25(PB)(tanh(X)/4)Bᵀ)，X=0逐字复制P。每份W普通重建HNSW M16/efConstruction200/seed20260828，在线ef10/direct3→真实ID升序→原NSG L128/K10，无query模型或边hook。

两集分别排除253/252个原动作批次行，从剩余3843/3844条E37 train行中以预定PCG64 seed均匀抽1024，顺序切8个128块。抽样决策未解码或使用GT/奖励；前置保护SHA有既有GT字节读取。搜索只加载另存train4096前缀，不加载monitor；所有样本仍有历史训练暴露，μ/P/B也来自历史训练，故这是回顾性训练诊断。旧E37/E38整目录SHA保护包含历史开发产物的字节读取；没有读取/hash新的原validation/held-out，没有新cal/audit评测。

36份W及有序拓扑SHA全部恢复原轨迹/checkpoint。每份小图保存后以16条旧行复核count、serialized plain和原NSG三路，另与旧输出逐位比较ID、distance bits、入口、route/graph NDC。新μ0中心1024条返回也与旧基线逐位一致。

## 批次、奖励与局部差距

128/256/512/1024的query均值方差估计按批量下降，但1024的去噪条件信噪估计仍仅0.161、0.071、0.035、−0.051；没有观察到稳定方向。负估计不是负真实信号，更不证明完整参数空间没有梯度。这只条件于现有八个扰动（中心化张成至多7维），未识别扰动采样噪声。

WebVid两点仅66/1024条query能区分八动作命中，Yandex29/26条；多数入口变化未形成命中变化。最大单query占逐query命中梯度范数和5.78%/6.58%/9.21%/8.80%，比E38小批次集中度减轻；删掉最大query后全量方向余弦仍为0.934/0.895/0.893/0.903。因此此次不稳不能简单归结为一条极端query。该范数和不等于最终参数贡献或收益份额。

全量data梯度范数约0.257/0.243/0.236/0.247，正则约0.0227/0.0204/0.0128/0.0151，命中项仍占主导；加上正则，主512余弦依然全负。不支持先取消惩罚作为直接补救。

八个随机动作平均相对确定中心Recall分别为−0.0024、−0.2930、−0.0134、−0.0208pp；描述性8-block bootstrap区间分别为[−0.2698,0.2698]、[−0.4565,−0.1282]、[−0.1904,0.1587]、[−0.2161,0.1660]pp。这是固定八动作/训练query上的条件差，不代表完整Gaussian期望或泛化结论。WebVid已选μ中心本身相对原画像+0.3125pp，但随机均值只+0.0195pp；局部随机扰动反而稀释中心收益，不支持将E37整体问题直接解释为“采样有效但导出μ损失收益”。Yandex已选中心在这1024上相对原画像0pp。原E37 cal/audit负值和微小QPS变化原样保留。

## 成本、核验和产物

{cost}

主统计约{d['analysis_seconds']:.3f}s、独立复核约{v['seconds']:.3f}s，均单线程；这些不含编写、保护hash、绘图或人工阅读。独立集合评分36864返回，旧结果逐位回归576条，独立LOO公式重建4096逐query梯度，检查428个组方差和1092个互斥组对。首版verify括号笔误及绘图轴标签调整保留在[修正记录](analysis_repair.md)，不增加查询或训练。

[批量表](results/batches.csv)、[全部组](results/groups.csv)、[互斥组对](results/disjoint_pairs.csv)、[query明细](results/queries.csv)、[梯度图](figures/batch_diagnosis.svg)、[固定点图](figures/fixed_contexts.svg)。全部W/物理图/原始返回保留在models/results；输入身份与旧目录保护在reviews，根文档前件在source_before。

## 接续

本版本停止扩大预算，没有追加训练/评测任务。下一步先用这些既有返回比较同一静态动作的净收益与逐query可达改进，检查收益/损伤是否在入口画像或query群之间系统冲突；该分析尚未执行。有限已测动作的最佳值不能叫全局oracle，也不能作为可部署策略。只有证据指向共享联动限制，才设计单项画像自由度修订，并先复盘E22/E28–E32；若已测动作本身几乎无改进，则不继续扩大这组局部扰动。构图策略保留独立备选，不自动重启E33删边。用户“离线训练画像、在线普通HNSW”的目标保持，当前默认未换。

## 复现入口

原目录为一次性不可覆盖产物；以下为实际阶段命令的结构，重新执行须新建独立版本并调整O，不能在当前目录重跑搜索：

```bash
env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 taskset -c 8 timeout 1800 .venv_cpu/bin/python {rel}/src/control.py prepare
env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 taskset -c 15 timeout 1800 .venv_cpu/bin/python {rel}/src/control.py run webvid2_5m_light_v1
env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 taskset -c 15 timeout 1800 .venv_cpu/bin/python {rel}/src/control.py run yandex_t2i_official10M_ip_v1
```

统计、独立复核、绘图分别为src/analyze.py、src/verify.py、src/plot.py，只读已有搜索返回。第一次绘图使用CPU9，后续修正CPU8，实际差异已记录；所有查询保持CPU15单线程串行。
'''
(O/'report.md').write_text(report)
(O/'conclusion.md').write_text(conclusion+'\n\n'+table)
card=f'''# 28. E39 固定参数的大批次方向诊断

2026-09-12，状态`{status}`。[报告](../{rel}/report.md)、[协议](../{rel}/protocol.md)、[配置](../{rel}/config.locked.json)、[验收](../{rel}/reviews/final_audit.json)。用户在E38建议后要求继续，授权执行此前正常36864/硬限40000的最小控制。

## 动机、机制与来源

E38发现batch128反馈稀疏但未证明更大query批量能稳定方向。E39固定WebVid rl_20260921的μ0/step140、Yandex rl_20260922的μ0/step40，并固定对应checkpoint后一步的原八扰动。仅从E37 train4096排除两原批次后另取1024，seed预锁；同名单服务两参数点、8个互斥128块。普通HNSW参数/真实ID/顺序、原NSG/raw IP/L128/K10不变，每个实际静态配置真实搜索；无optimizer、σ/rank/选点更新。

{conclusion}

{table}

## 结果解释与限制

35个互补512分组中正data余弦比例60%/0%/8.57%/25.71%，是同一池相关重组，不是独立重复。全1024去噪条件信噪估计约0.161/0.071/0.035/−0.051；不能据此证明总体或完整256维梯度不存在。1024没有独立另一半。主/辅助门均在查询前写入协议，四点全未过，停止增加同训练器预算。

WebVid66/66、Yandex29/26条query能区分动作命中，正则仍较小。最大query范数份额降为约5.8%–9.2%，删最大后方向保持约0.89–0.93；不稳并非仅由单条记录造成。WebVid已选中心在本训练池比原画像+0.3125pp，八随机动作均值只+0.0195pp；随机−中心−0.293pp，描述性8块区间[−0.4565,−0.1282]。该局部结果保留，但非盲测/新性能优势，也不支持“采样优于导出中心”的简单解释。其它三个随机−中心区间跨0。

## 执行与保护

{cost}

36画像/拓扑恢复、576历史query逐位回归、36864独立集合评分、4096逐query梯度/428组方差/1092组对验收通过。没有新validation/held-out原始读取/hash；旧目录保护会读E37已有开发隔离产物，搜索只加载另存train4096。已有历史暴露不称独立验证。E37/E38目录前后SHA保持，根文档前件独立保存；[verify语法与绘图调整](../{rel}/analysis_repair.md)均0额外搜索。

## 尚未执行接续

先做已测动作净收益/逐query收益损伤与入口变化的缓存归因，区分局部动作无空间与共享联动冲突；不凭此直接换自由W、增大batch或训练epoch。新表示前需复盘E22/E28–E32，图学习保留独立备选。E37开发门/默认保持，无排队任务。详见[s-target](../s-target.md)。

[批量表](../{rel}/results/batches.csv)、[query明细](../{rel}/results/queries.csv)、[方向图](../{rel}/figures/batch_diagnosis.svg)、[独立核验](../{rel}/reviews/independent_verification.json)。
'''
(R/'experiment_history/28_fixed_profile_batch_diagnosis.md').write_text(card)
index=R/'s-experiment.md';text=index.read_text()
row=f'| E39 固定参数批次诊断 | 固定双集两μ/各八扰动，以train另取1024检查互斥批次方向；36静态图真实查询 | `{status}`；四点主512方向全负，扩大批次未过稳定门；38592次NSG、0更新，默认保持 | [28 固定批次](experiment_history/28_fixed_profile_batch_diagnosis.md) |\n'
assert '| E39 ' not in text;text=text.replace('| E38 ',row+'| E38 ',1).replace('最近完成记录已为E38诊断','最近完成记录已为E39诊断').replace('二十七份详细卡片','二十八份详细卡片');index.write_text(text)
index=R/'experiment_history/README.md';text=index.read_text();line='| [27 离线画像反馈诊断](27_offline_profile_diagnosis.md) | E38：0新搜索，真实奖励/梯度分解、query批次噪声、精确μ随机/中心匹配与表示边界 |'
assert line in text;index.write_text(text.replace(line,line+'\n| [28 固定参数批次诊断](28_fixed_profile_batch_diagnosis.md) | E39：固定双集两μ/八扰动，另取1024训练query，四点512方向全负，0更新并停止预算扩大 |'))
(R/'summary.md').write_text(f'''# ACSG 当前结果摘要

2026-09-12。最近完成E39固定参数批次诊断，状态`{status}`。[报告]({rel}/report.md)、[历史28](experiment_history/28_fixed_profile_batch_diagnosis.md)、[验收]({rel}/reviews/final_audit.json)。最近训练/完整性能评测仍为E37，默认WebVid GT10-soft-t1 / Yandex GT10-hard不变。

## 当前判断

{conclusion}

{table}

固定原ε/μ，另取1024训练query，主比较前后两个互斥512；辅助35分组彼此相关，不能计作35次独立证据。1024本身仅一个估计，未验证两个独立1024方向。数据奖励和加正则的方向均失败，不支持先取消惩罚；命中区分仍稀疏，最大query份额降到5.8%–9.2%，删最大后全量方向仍接近，故不稳也不能只归咎一条异常query。

WebVid已选中心在本训练池相对原画像+0.3125pp，随机动作平均只+0.0195pp，随机−中心−0.293pp；此处是扰动损伤确定中心的局部证据。其它三个随机−中心区间跨0，不能将E38有限匹配直接升级为普遍“采样到均值损失”。全部样本有历史训练暴露，不是新的泛化结果。

## 实际执行与边界

{cost}

36份画像/拓扑恢复、576条旧输出逐位回归、36864个新返回独立集合评分和完整梯度/方差重算通过。0新训练/GT/validation/held-out原始读取或hash；E37/E38整目录SHA保护，根文档前件保存。没有新QPS或默认替换。

E37主RL cal/audit Recall变化仍为WebVid−0.1172/−0.0391pp、Yandex−0.0195/+0.0391pp，L128 QPS约+0.069%/+0.078%，双集开发门停止；E24 GT10及E36各自局部正信号保留。用户目标继续为离线学习静态入口画像、在线一次普通HNSW；当前受阻于该具体共享小扰动训练的有效反馈，不能外推整个方向失败。

下一步先分析既有动作收益/损伤与入口画像变化的对应关系，区分局部动作本身空间小和共享联动冲突，再决定是否修订表示。该接续尚未执行，不追加epoch、batch、ANN或新评估；详见[s-target](s-target.md)。无排队任务。
''')
(R/'s-target.md').write_text(f'''# ACSG 下一阶段目标与接续

2026-09-12。E39固定μ/扰动的大批次诊断已完成，四点均未通过预定稳定门，状态`{status}`。[当前结果](summary.md)、[历史28](experiment_history/28_fixed_profile_batch_diagnosis.md)、[报告]({rel}/report.md)。E38原0搜索诊断和E37训练/性能原件保留，不重复运行旧runner。

## 判断与主目标

用户的主目标仍是离线训练入口画像或入口小图，在线只执行普通HNSW→原NSG。E37已实现这一部署形式；E39说明在现有共享低秩、小Gaussian扰动和八方向设置下，更多query未形成稳定更新方向。此处停止的是同设置的预算扩大，不是否定RL、离线画像或图学习的全部可能。

四点前512/后512 data余弦−0.054/−0.239/−0.381/−0.124；辅助分组相关，1024没有独立另一半，真实完整梯度与共享表示能力尚未被单独识别。不能把方差按批量降低当作已经学会，也不再直接以“batch128太小”解释所有失败。

## 第一优先：用已有反馈区分动作空间小与收益冲突

下一项仅为尚未执行的缓存分析，0新NSG/HNSW/构图/训练/GT，不读新评估数据。读取E39固定36份W/图身份、aligned返回、训练query/GT和E37同源基线；不重新执行E39或扩大query池。

先逐点比较确定中心、八个固定动作各自净命中收益、收益/损伤幅度与零命中事件；再计算“这九个已测静态动作的逐query最佳值”对中心的有限集合上界。上界按实际已测组合定义，不能叫全入口/全参数oracle，也不能免费部署逐query最佳动作；所有真实搜索费用仍是E39已付38592次。

沿每次实际三入口变化，检查引入/丢弃哪些真实hub，对应query画像得分边界、收益/损伤与query相似群是否系统冲突。只从输出不能判断HNSW某hub是否被访问，缺trace时不得编造候选覆盖因果。对同一共享变换的正负群给出逐行证据，频率关联不能当解耦画像一定有用的因果证明。

预期产物：每动作净收益与损伤表、有限集合上界、入口变化/画像得分/相似query冲突的可追溯表、一个被证据支持的最小修订或停止理由。若已测动作几乎没有逐query改进，则停止扩大同局部动作；若逐query有空间却无法被同一静态动作兼顾，先定位共享联动或query评分表达的限制，再设计控制。若证据混合，明确缺什么，不自动扩网格。

## 第二优先：证据支持后才修订离线画像训练

自由画像、自由低秩、共享linear/MLP与真实目标此前均有实验。任何新表示先完整复盘E22和E28–E32原协议/源码/结果，明确区别，不能把自由W换名重启。新方案只改一个已诊断因素，保持原画像恢复、固定H/真实ID/大NSG/IP和在线普通HNSW；保留同表示、同总真实调用预算的非RL控制。

进入新训练前锁定目标、参数空间、数据访问、真实反馈和parity调用、资源硬限、独立开发门；不同时改表示/batch/σ/步数。八方向诊断不支持完整256维结论，若拟改方向分配必须单列其与query批次的预算交换。默认与性能结论仍需冻结模型、同机单线程完整Recall–QPS前沿，训练reward或同L Recall不能代替。当前没有新训练或新评估数据访问安排。

## 第三优先：小图构造保留为独立备选

只有证据指向候选覆盖/访问效率，才讨论插入顺序、邻居保留或有限补边。E33的受限删边及E34成本结果保留，E35的“好点已评分但未选中”不能由连通性修复自动解决。新构图动作须说明区别，控制同出度随机改动、同画像普通重建和保分数图变化，完整wall收费；大图/H/真实ID/在线metric保持。

## 接续状态与启动指令

E39已经真实执行并验收，不能再写为未运行计划。E37/E38旧目录保持，当前默认未变，没有排队训练/评测。上述缓存归因尚未执行；它与E39已完成的批次方向检验是不同问题。

> 在/data/netg/ACSG完整阅读AGENTS.md、summary.md、spec.md、s-target.md、s-experiment.md，再由历史28进入E39冻结协议、四点完整结果、原始aligned返回和独立验收。继续第一优先的既有反馈归因：比较固定动作净收益与有限逐query上界，并连接入口画像变化和收益/损伤冲突。仅分析现有训练产物，0新ANN/NSG/构图/训练/GT；不重跑E39，不读新validation/held-out。结论必须区分当前局部动作空间、共享表示联动和HNSW访问证据缺口，然后提出唯一最小可反驳控制。
''')
spec=R/'spec.md';text=spec.read_text().replace('E38既有反馈诊断已验收；E37部署及原Fast/NSG kernel不变','E39固定参数批次诊断已验收；E37部署及原Fast/NSG kernel不变')
text=text.replace('固定大批次搜索控制目前是s-target提案，不属于已执行API。','E38原固定大批次提案保持其历史未执行身份；继任E39已单独实施，见下节。')
text+=f'''

## 固定参数与动作的批次诊断（E39，2026-09-12）

[协议]({rel}/protocol.md)与[control.py]({rel}/src/control.py)复用E37已编译environment.so及native wrapper，不修改原kernel。prepare按冻结cal选定两μ/集与原八扰动逐字恢复W及拓扑身份，从排除两个原批次后的E37 train4096中无标签抽1024行，另存train前缀query/GT/源行；搜索配置num_queries4096、CPU15、threads1、native_call_cap19296。完整预留每dataset19296，失败不释放、不自动重试；总硬限40000，拒绝已有job及输出。

每图build/save→16历史query三路verify→1024正常run，36图实际38592次NSG/38016次HNSW/36build，全部参数固定，0optimizer。verify的count输出同时与旧轨迹或checkpoint逐字比较ID/float distance/入口/route与graph NDC；全部W与物理图、aligned原始输出及source row IDs保存。GT仅由后处理读取，不进入C++搜索。

[analyze.py]({rel}/src/analyze.py)用M=(ε−mean ε)ᵀ/(7σ)构造逐query梯度，单列固定画像漂移正则；主比较预锁前后512，辅助128/256/512的互斥组对及1024单估计。有限总体N使用实际合格3843/3844；互补重组不是独立重复，条件query方差不含方向采样噪声。稳定规则在查询前锁定，不选择新μ/动作部署，不产生QPS。

[verify.py]({rel}/src/verify.py)独立集合评分全部36864返回，以逐动作LOO公式和二阶矩恒等式核验4096逐query梯度、428组方差及1092互斥组对。原verify语法修正/图轴调整见[记录]({rel}/analysis_repair.md)，0额外搜索。前后保护E37/E38目录SHA，原根文档快照位于source_before。改变分析仅重做派生结果；若μ/ε/query/W/图/metric/kernel/L改变，必须新建版本并重新建立真实反馈身份。结果见[summary](summary.md)/[历史28](experiment_history/28_fixed_profile_batch_diagnosis.md)。
'''
spec.write_text(text)
print('Report, history28, indices and four root documents synchronized')
