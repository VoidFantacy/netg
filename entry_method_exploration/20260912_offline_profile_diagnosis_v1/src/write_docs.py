from common import *

for doc in ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:
 assert (R/doc).read_text()==(O/'source_before'/doc.replace('/','__')).read_text(),doc
path='entry_method_exploration/20260912_offline_profile_diagnosis_v1';e37='entry_method_exploration/20260912_offline_profile_rl_v1';conclusion=(O/'conclusion.md').read_text()
(R/'summary.md').write_text(f'''# ACSG 当前结果摘要

2026-09-12。最近完成E38既有反馈诊断，状态`COMPLETE_OFFLINE_PROFILE_DIAGNOSIS_NO_NEW_SEARCH`。[报告]({path}/report.md)、[历史27](experiment_history/27_offline_profile_diagnosis.md)、[验收]({path}/reviews/final_audit.json)。最近训练与性能评测仍为[E37]({e37}/report.md)，原模型、开发门和默认均未改变。

## 诊断结论

{conclusion}
| 主RL诊断项（合并双seed） | WebVid | Yandex-IP |
|---|---:|---:|
| 每步能区分8动作命中的query中位数 | 9/128 | 3/128 |
| 动作-query事件中入口变化 | 27.55% | 20.00% |
| 动作-query事件中命中变化 | 2.69% | 0.94% |
| 两半query梯度余弦中位数 | 0.0078 | 0.0041 |
| 最大单query占逐query命中梯度范数和的中位数 | 30.75% | 57.71% |

这些是实际重复观测的诊断，不能当独立query总体质量。暴露校正后最集中约1%的query仍占RL逐query梯度范数和约37%–40%/66%–68%，不是占最终参数或收益的比例。参数无撞边、B/PB无秩塌缩；表示是否足够尚未因果验证。[诊断图]({path}/figures/gradient_diagnosis.svg)、[完整逐步统计]({path}/results/steps.csv)。

## 实际执行与保留边界

重算E37的1,773,568条已有返回、12800奖励、1600梯度分解与88确定中心；独立集合评分复核32768个动作返回、32步条件方差/半批方向，以及全部1188条相同μ和query匹配。分析实际单线程约8.454s，峰值约168MiB；此时间不含人工阅读/编写/绘图，也不是训练成本或QPS。0新NSG/HNSW/构图/训练/GT，无新validation/held-out原始输入读取/hash。E37全部2721文件SHA保护，文档前件独立保存。

E37主RL的cal/audit Recall变化仍为WebVid−0.1172/−0.0391pp、Yandex−0.0195/+0.0391pp，L128 QPS约+0.069%/+0.078%，双集开发门停止。离线画像→普通HNSW的部署形式已实现，未取得稳定跨数据集前沿优势。E24原GT10及E36 Yandex各自局部正信号保留。

下一步为固定μ/扰动、改变query批量的最小诊断，建议正常36864次NSG、0optimizer更新，尚未执行；若方向可稳定，再设计预算匹配的训练修订，详见[s-target](s-target.md)。无排队任务，默认未换。
''')
old=(O/'source_before/s-target.md').read_text();rest=old[old.index('## 第二优先：'):old.index('## 接续状态和启动指令')]
(R/'s-target.md').write_text(f'''# ACSG 下一阶段方向与实验接续

2026-09-12。E38已完成此前第一优先的既有反馈诊断；[历史27](experiment_history/27_offline_profile_diagnosis.md)、[报告]({path}/report.md)。E37训练/曲线原件不改，用户主意图仍是离线学习画像、在线一次普通HNSW。本文件以下新增搜索/训练均未执行。

## 当前依据

{conclusion}
条件query噪声检查和表示能力判断分开。RL/ES同参数空间均有方向不稳；实际收益集中性、惩罚项尺度、参数未撞边有直接证据，增大batch必然改善与共享表示不足没有因果证据。E37历史数据暴露仍保留，不能把此次复算称为新的独立性能验证。

'''+(O/'next_control.md').read_text()+'\n'+rest+f'''## 接续状态与新对话指令

E38诊断已完成；E37目录、模型、cal选择和完整wall保持原件。尚未运行固定参数的大批次诊断，没有追加训练、QPS或新评估数据访问，也没有排队任务。E24/GT10及E36局部正信号不被E38解释覆盖。

> 在/data/netg/ACSG，完整阅读AGENTS.md、summary.md、spec.md、s-target.md、s-experiment.md，由历史27进入E38协议、诊断源码、全部逐步/逐query结果和独立验收，并核对E37原协议与冻结模型。当前诊断0新搜索已完成，不重复做一遍。先审查s-target第一优先的固定μ/固定动作/独立query批次控制，落实正常36864、总硬限40000的真实调用账与来源/线程/parity合同；此次只完善新协议，不自动启动搜索、训练或读取新的validation/held-out。清楚区分query采样噪声、扰动噪声和共享表示限制。
''')
p=R/'spec.md';t=p.read_text();t=t.replace('（E37离线画像训练、普通HNSW重建及部署已验收；原Fast/NSG kernel不变）','（E38既有反馈诊断已验收；E37部署及原Fast/NSG kernel不变）',1)
t+=f'''
## 既有静态画像训练反馈诊断（E38，2026-09-12）

[独立协议]({path}/protocol.md)及[analyze.py]({path}/src/analyze.py)只读取E37已有numpy/JSON/CSV，不导入native/evaluate/train、不执行HNSW或NSG、不构图或更新参数。GT评分从E37的已隔离fit输入与实际返回重算；动作-query未观测项不补零。输出按dataset/arm/seed/step与原source row ID对齐，记录实际暴露次数。

RL逐query条件梯度矩阵为(ε−mean ε)ᵀU/(7σ)，ES为ε正方向ᵀ(U+−U−)/(8σ)，与原8候选估计器等价；四个reward项分别分解并对原梯度回归。固定μ/方向下16次query二分仅估计query批次稳定性；有限总体修正方差与去噪信号估计不包含方向采样噪声。少数query贡献按逐query梯度范数和定义，不等于参数或检索收益占比。

随机/确定对比仅允许checkpoint s与step s+1的mu_before逐字相同，且query属于该中心已测train512；每query先平均八动作。80匹配组的1188条记录包含重复query，bootstrap按checkpoint块作描述区间，不作为独立因果验证。全部中心与选中/末点只作原结果分析，不回选cal/audit模型。

[summarize.py]({path}/src/summarize.py)导出分组、暴露校正、逐步/逐queryCSV、JSON及PNG/SVG/PDF；[verify.py]({path}/src/verify.py)以集合交集/逐项梯度公式复核32个分层step及全部精确匹配。E37整目录SHA保持，根文档变更前件在独立source_before。修改诊断公式或分组只重做派生分析，不能覆盖旧原始反馈/模型或自动产生新查询；固定大批次搜索控制目前是s-target提案，不属于已执行API。当前解释见[summary](summary.md)/[历史27](experiment_history/27_offline_profile_diagnosis.md)。
''';p.write_text(t)
card=f'''# 27. E38 离线画像训练反馈诊断

2026-09-12，独立版本`20260912_offline_profile_diagnosis_v1`，状态`COMPLETE_OFFLINE_PROFILE_DIAGNOSIS_NO_NEW_SEARCH`。[报告](../{path}/report.md)、[协议](../{path}/protocol.md)、[最终验收](../{path}/reviews/final_audit.json)。本次是用户要求“诊断一下”后的既有产物分析，未训练新方法。

## 动机与输入

E37已把在线MLP移至离线静态画像构造，但两集cal主RL负值、audit混合，完整曲线未形成稳定跨数据集前沿。其原报告不能区分反馈噪声、共享表示和随机到确定部署差异。本次读取8次训练的1600步/12800动作、88中心、已有fit query/GT与基线、冻结开发结果；不调用原native/evaluate/train，0新搜索/构图/GT/optimizer更新，无新validation/held-out原始输入读取/hash。

## 机制与结论

{conclusion}
每动作按真实GT集合交集重算hits/cost/failure/drift，原reward/gradient逐步回归。固定μ与八个扰动，对query作16次64/64二分，检查方向余弦与条件采样方差；这与比较相邻不同扰动方向不同，只识别query噪声。条件信噪估计约0，不能写成真实梯度不存在。

RL动作-query事件中入口变化27.55%/20.00%，命中变化仅2.69%/0.94%；最大单query占逐query命中梯度范数和的中位数30.75%/57.71%。暴露归一化后前41个query仍占约37%–40%/66%–68%。每run只有4086/4088行真正抽到，每行中位6批，未见10/8行不冒充已知零效用。

总梯度/hits余弦约0.999；RL hits范数中位0.667/0.563，drift0.0305/0.0161，cost0.00785/0.00561。μ最大绝对值≤1.047，原限±2，无撞边；B/PB满列秩16。这些反对“惩罚或退化使模型不动”的主解释，但没有排除长期正则影响或表示不足。

随机/确定只匹配checkpoint s与step s+1的精确μ及相同query，共80组1188条重复记录；每run126/128个query身份。WebVid RL随机均值略好但区间跨0且去最大单条记录后明显缩小，Yandex与ES混合。全部中心/选中/末点统计表明小正值可来自极少query和正负幅度差，不能据monitor最高点宣称泛化成功。

## 执行、验收与边界

重算1,773,568条原返回、12800奖励、1600分解、88中心（train/monitor共176统计）；同入口时原NSG输出/graph NDC一致。独立集合评分32768条、复核32个分层step的方差与半批方向、全部1188精确匹配。主分析实际线程1、约8.454s、RSS约168MiB，不含阅读/编写/绘图/最终验收，不能称训练或查询性能。

E37全部2721文件在前后SHA保护；所有原训练/模型/图/标签/结果保持。旧root完成时身份与本轮root变更前件各自保留，不静默改写E37 final_artifact_freeze。结论不构成表示不可学习或新性能GO，原E37开发门与默认不变。

## 产物与未执行接续

[逐步](../{path}/results/steps.csv)、[逐动作](../{path}/results/actions.csv)、[query暴露](../{path}/results/query_exposure.csv)、[匹配记录](../{path}/results/matched_queries.csv)、[全部中心](../{path}/results/centers.csv)、[梯度图](../{path}/figures/gradient_diagnosis.svg)、[独立核验](../{path}/reviews/independent_verification.json)。源代码均在该独立版本src，输入与旧目录保护SHA在reviews；仅复核派生结果，不原地重训或改旧选择。

最小后续是固定μ=0/主RL及各自八个原动作，用已有train另取1024行分块检查方向能否稳定，正常36864次NSG、建议总硬限40000、0optimizer更新。此控制仅为建议，尚未构图/查询/训练；详细范围和停止条件见[s-target](../s-target.md)。若更大批次方向仍不稳，不继续堆epoch；若可稳定，再讨论同总调用预算的microbatch累计，保留预算代价控制。
'''
assert not (R/'experiment_history/27_offline_profile_diagnosis.md').exists();(R/'experiment_history/27_offline_profile_diagnosis.md').write_text(card)
p=R/'experiment_history/README.md';t=p.read_text();t=t.replace('\n\n## 写入规则','\n| [27 离线画像反馈诊断](27_offline_profile_diagnosis.md) | E38：0新搜索，真实奖励/梯度分解、query批次噪声、精确μ随机/中心匹配与表示边界 |\n\n## 写入规则',1);p.write_text(t)
p=R/'s-experiment.md';t=p.read_text();row='| E38 离线画像反馈诊断 | 复算E37全部反馈/梯度，固定方向query二分、贡献集中性、80组精确μ匹配及全部中心 | `COMPLETE_OFFLINE_PROFILE_DIAGNOSIS_NO_NEW_SEARCH`；反馈稀疏/批次方向不稳，惩罚非主导，表示与部署失配未定因；0新搜索/训练 | [27 反馈诊断](experiment_history/27_offline_profile_diagnosis.md) |\n'
t=t.replace('| E37 离线画像策略优化 |',row+'| E37 离线画像策略优化 |',1).replace('当前最近完成实验已为E37','当前最近完成记录已为E38诊断').replace('二十六份详细卡片','二十七份详细卡片');p.write_text(t)
print('DOCS_WRITTEN',flush=True)
