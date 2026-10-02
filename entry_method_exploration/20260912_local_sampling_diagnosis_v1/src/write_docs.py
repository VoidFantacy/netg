from shared import *
threads(8);assert read(O/'reviews/verification.json')['status']=='PASS'
rr=read(O/'results/analysis.json');gate=read(O/'results/gate.json');cost=read(O/'results/cost.json')
assert gate['status']=='STOP_THIS_WEIGHTED_SAMPLER'
status='COMPLETE_LOCAL_SAMPLING_DIAGNOSIS_STOP_STRATIFIED_SAMPLER'
headline='全池参照证实反馈遗漏，同时显示动作影响仍局部稀疏；原入口相关分层未降低足够方差，停止该采样修订。'
rows=['| 数据集 | 全池有命中变化状态/10 | 原128可见状态/10 | 全池有变化动作/80 | 原128可见动作/80 | 同一动作兼有收益损伤 | 分层/均匀U方差 | 不变差状态比例 |','|---|---:|---:|---:|---:|---:|---:|---:|']
for ds,name in zip(DS,['WebVid','Yandex']):
 d=next(x for x in rr['datasets'] if x['dataset']==ds)
 rows.append(f'| {name} | {d["full_hit_contexts"]} | {d["old_hit_contexts"]} | {d["full_hit_actions"]} | {d["old_hit_actions"]} | {d["mixed_gain_loss_actions"]} | {d["U_variance_ratio"]:.4f} | {d["nonworse_fraction"]:.0%} |')
tab='\n'.join(rows)+'\n'
finding='''WebVid在完整4096训练池中9/10状态有命中变化，而原128只见1/10；Yandex则全池3/10、原128为0。前者说明小批次遗漏明显，后者同时保留已测局部动作质量响应稀疏的证据。每状态仅影响WebVid 0–15/Yandex 0–8条query；这些固定状态/方向不能证明全局改进空间小。

WebVid 80个动作累计198个收益命中事件、215个损失，其中补集占166/171（83.8%/79.5%）；Yandex收益62、损失78，补集36/58（58.1%/74.4%）。这些是跨动作重复计数的事件，不能当成独立query数量或某一张部署图的净收益。原anchor三入口含目标hub只定义GT无关近组，不能代表完整影响集；未进入该hub原入口集合的query也会受新评分或HNSW重建影响，本轮未隔离两机制。

原入口分层条件方差比为WebVid1.0738、Yandex0.9775，远未达到≤0.5；两集均只有20%非零U状态不变差，Yandex质量变化状态也不足4/10。因近组全量只需9–43条，本方案实际全查近组并减少补集抽样；大部分质量变化在补集，不能指望相关性名称代替真实反馈覆盖。按预锁门停止该采样方案，不扫近组名额、不扩epoch/σ，不进入新开发或QPS。

共享一个动作确会同时产生收益和损伤，但目前不是“所有好处都必须以损伤交换”的证据。按每个独立context的既有九选一（含不动）事后最优：WebVid逐query有限oracle累计63个额外命中，最佳固定动作累计净35，其中24是未覆盖收益、4是该最佳动作自带损伤；Yandex有限oracle与最佳固定动作均累计26，三个有质量响应的状态各有无损动作覆盖全部已观察收益。这些跨状态相加只作诊断，不能拼成可部署W；更不能把有限动作中无法同时达到oracle推广为共享画像表示不可能。
'''
next_text='''下一明确问题是：把同一状态、同一八方向的128估计替换为完整4096条件梯度，原确定均值的一次Adam更新能否转化为真实命中收益？这一步直接检查“反馈正确后，实际更新是否有效”，不重启已失败的分层训练。固定同20个context，保留动作前μ/动量/局部计数/步长，只构造原批次更新与全池梯度更新两条确定行，再真实查询完整训练池；没有新方向、额外幅度网格或连续训练。该新控制需另立E45协议，当前尚未查询。若单步也无响应，再隔离画像评分变化与HNSW邻接重建，避免继续调采样解释所有问题。'''
body=f'''# E44 固定局部动作的全池反馈与采样诊断

2026-09-12，`{status}`；门`{gate['status']}`。{headline}

{tab}
{finding}
## 方法与边界

预先固定E43 RL第一seed20260921，双集step20/40/…/200动作前W与原八候选，各9张普通HNSW；所有图真实查询原train4096，0新训练。W逐行重放原checkpoint/trajectory，目标/ε/近组均在新结果前冻结。GT只在原始返回后评分，候选与当前W/方向保持固定。

近组为旧anchor三入口含目标hub的query，全体N4096，近组抽min(64,N1)、补集补足128，按总体权重(N组/N)估计；uniform同128无放回。逐query LOO梯度按原σ.3计算，原anchor总NDC分母与失败惩罚保留，固定漂移梯度单列。有限总体条件均值方差以逐维二阶矩精确计算，独立标量公式复核；不含方向抽样或迭代噪声，不是等成本方法或QPS比较。

## 成本与验收

真实737280全池NSG+1728三路parity=739008 NSG，738432 HNSW，180构图，0连续训练/optimizer/新GT/开发/QPS。两个query进程共{sum(x['seconds'] for x in cost['datasets']):.3f}s，含加载/构图/计数/写盘/parity，不作纯查询速度；CPU15实际进程/OMP/BLAS/MKL1线程，双集串行。峰值RSS分别{cost['datasets'][0]['peak_RSS_KiB']/1048576:.3f}/{cost['datasets'][1]['peak_RSS_KiB']/1048576:.3f}GiB。

独立集合评分737280返回，180完整图/W/topology身份，23040原128输出逐位回归，36物理代表图×16query三路parity（576条），全部20旧梯度及两种条件方差核验通过。其余144图保存完整拓扑和raw，不声称物理序列化parity。E37–E43原目录、原native/NSG依赖和查询前冻结保持；根文档前件另存。没有读取/hash新的原validation/held-out；保护历史隔离产物的字节读取不混为新评测。

## 接续

{next_text}

默认仍WebVid GT10-soft-t1 / Yandex GT10-hard；E43 WebVid ES局部正值、E41/E42反事实证据保留。阶段完成不结束20:00持续研究目标。

[协议](protocol.md)、[预锁配置](config.locked.json)、[完整动作表](results/actions.csv)、[状态表](results/contexts.csv)、[门](results/gate.json)、[成本](results/cost.json)、[独立核验](reviews/verification.json)、[图](figures/sampling_diagnosis.svg)。
'''
(O/'report.md').write_text(body);(O/'conclusion.md').write_text(headline+'\n\n'+finding+'\n'+next_text+'\n')
dump(O/'reviews/visual_review.json',dict(status='PASS',files=['figures/sampling_diagnosis.png'],method='Viewed rendered PNG; labels, signed event counts and variance axes readable'))
hist=body.replace('# E44 固定局部动作的全池反馈与采样诊断','# 33. E44 固定局部动作全池与采样诊断')
import re
hist=re.sub(r'\]\(([^)]+)\)',lambda m:'](../entry_method_exploration/20260912_local_sampling_diagnosis_v1/'+m.group(1)+')',hist)
(R/'experiment_history/33_local_sampling_diagnosis.md').write_text(hist)
p=R/'s-experiment.md';s=p.read_text();marker='| E43 局部画像RL/ES';i=s.index(marker)
s=s[:i]+'| E44 局部动作全池/采样诊断 | 固定20状态/原八方向，180图完整train4096；原128回归与精确条件方差 | `COMPLETE_LOCAL_SAMPLING_DIAGNOSIS_STOP_STRATIFIED_SAMPLER`；漏反馈与稀疏并存，方差比1.074/0.978，停止原入口分层；739008 NSG，0训练 | [33 全池与采样](experiment_history/33_local_sampling_diagnosis.md) |\n'+s[i:]
s=s.replace('三十二份详细卡片','三十三份详细卡片');p.write_text(s)
p=R/'experiment_history/README.md';s=p.read_text();s+='\n- [33 局部动作全池/采样诊断](33_local_sampling_diagnosis.md)：E44完整反馈证实遗漏，原入口分层未过方差门，停止该采样修订。\n';p.write_text(s)
(R/'summary.md').write_text(f'''# ACSG 当前结果摘要

2026-09-12，最近完成E44，`{status}`，门`{gate['status']}`。[报告](entry_method_exploration/20260912_local_sampling_diagnosis_v1/report.md)、[历史33](experiment_history/33_local_sampling_diagnosis.md)、[核验](entry_method_exploration/20260912_local_sampling_diagnosis_v1/reviews/verification.json)。20:00持续研究目标仍在推进；默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。

{headline}

{tab}
{finding}
真实739008 NSG、738432 HNSW、180构图；737280集合评分/23040旧输出逐位回归/576条代表图三路parity及梯度方差通过。CPU15实际单线程、双集串行，0新optimizer/GT/开发/QPS；进程wall不是QPS。E37–E43原件保留。

E43局部训练未过Yandex monitor门，WebVid ES+0.0781pp局部正值保留；没有RL额外优势或默认替换。E41无损局部动作和E42必要/充分的背景依赖仍成立。最近完整Recall–QPS为E37。

{next_text} 详细接续见[s-target](s-target.md)。
''')
(R/'s-target.md').write_text(f'''# ACSG 下一阶段目标与接续

2026-09-12，E44全池诊断已完成，[历史33](experiment_history/33_local_sampling_diagnosis.md)、[报告](entry_method_exploration/20260912_local_sampling_diagnosis_v1/report.md)。用户授权持续推进至北京时间20:00，总目标继续。

## 证据与首要问题

WebVid全池9/10状态有命中变化、原批次1/10；Yandex全池3/10、原批次0。分层方差比1.074/0.978、均仅20%状态不变差，停止原入口分层。多数收益损伤在补集，不扫近组网格、不扩E43 epoch/σ。有限动作最佳与逐query上界：WebVid差28命中中24未覆盖/4自带损伤，Yandex三状态均可无损达到已观察上界；不推成部署/表示不可能。

{next_text}

## E45最小控制，待独立预锁

沿用全部20固定context，不能按新GT挑正状态。由E43完整checkpoint及后续行更新恢复动作前μ/m/v/count/W；用原batch梯度复算下一行必须逐位恢复原next_row，再用E44全池梯度替换g、其它Adam输入及步长不变。记录20次反事实单步计算，无连续训练、候选选优或monitor选择。

每context保存原下一行N_batch和全池下一行N_full，普通HNSW→真实train4096；当前C复用已验完整返回并做同kernel/序列化/旧结果恢复。完整G/L/零命中/U/NDC、行位移、相对原批次的差与原八候选反馈分别列出。完整梯度只消除这八方向下的query采样误差，不能称精确检索目标导数、免费标签或低成本训练。新协议锁预算和进退条件后才查询。

## 后续优先与截止

若全池单步在双集均有命中及U正值、相对原步总体质量不差，再讨论能支付的反馈方案；未达到就停止用采样修订解释当前学习失效，先隔离同画像评分/不同邻接及同邻接/不同画像评分。即便达到也不是直接加训练预算或QPS GO，必须保留实际全池费用。

第三优先为已测有限动作的收益覆盖与冲突结构，只在缓存上分析，不据oracle直接扩模型/候选网格。用户20:00截止，19:35后不训，19:40后不查询，留出独立核验与文档；不因观察超时重启旧job。默认保持，E37–E44保护。全部E43/E44进程已采集exit0，无遗留查询。

> 接续先读四主文档及AGENTS，从历史33进入完整矩阵与门；E44分层已停止，不重跑。先独立冻结同20状态的原梯度/全池梯度确定单步反事实，验证反馈到实际均值更新的转化；根据真实结果再选下一有证据问题，20:00前收口。
''')
p=R/'spec.md';s=p.read_text().replace('E43局部画像训练已验收','E44全池采样诊断已验收').replace('## 固定局部动作完整训练池诊断（E44，查询进行中）','## 固定局部动作完整训练池诊断（E44，已验收）')
s+='\nE44 [analyze.py](entry_method_exploration/20260912_local_sampling_diagnosis_v1/src/analyze.py)保存逐query四梯度分量、条件均值/方差、全/原batch响应、近/补集G/L和有限动作oracle差分；漂移不计query噪声。[verify.py](entry_method_exploration/20260912_local_sampling_diagnosis_v1/src/verify.py)独立集合评分737280结果，以逐动作LOO与逐维标量方差核对20梯度/640方差坐标，另验23040旧返回与576条物理图parity。180图与739008次NSG已完成，0optimizer；query/方向/背景/分层规则变化需新版本，不能沿用本条件方差结论。后继确定单步控制仍是s-target中的待执行方案。\n';p.write_text(s)
dump(O/'state.json',dict(status=status,gate=gate['status'],NSG_calls=739008,optimizer_updates=0,campaign_complete=False))
print('E44 report/history/root docs written',flush=True)
