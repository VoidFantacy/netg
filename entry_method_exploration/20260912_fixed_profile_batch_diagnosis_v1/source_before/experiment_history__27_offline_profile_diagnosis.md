# 27. E38 离线画像训练反馈诊断

2026-09-12，独立版本`20260912_offline_profile_diagnosis_v1`，状态`COMPLETE_OFFLINE_PROFILE_DIAGNOSIS_NO_NEW_SEARCH`。[报告](../entry_method_exploration/20260912_offline_profile_diagnosis_v1/report.md)、[协议](../entry_method_exploration/20260912_offline_profile_diagnosis_v1/protocol.md)、[最终验收](../entry_method_exploration/20260912_offline_profile_diagnosis_v1/reviews/final_audit.json)。本次是用户要求“诊断一下”后的既有产物分析，未训练新方法。

## 动机与输入

E37已把在线MLP移至离线静态画像构造，但两集cal主RL负值、audit混合，完整曲线未形成稳定跨数据集前沿。其原报告不能区分反馈噪声、共享表示和随机到确定部署差异。本次读取8次训练的1600步/12800动作、88中心、已有fit query/GT与基线、冻结开发结果；不调用原native/evaluate/train，0新搜索/构图/GT/optimizer更新，无新validation/held-out原始输入读取/hash。

## 机制与结论

当前最直接的瓶颈是：真实命中反馈集中在少数查询，batch128给出的更新方向不稳定。两臂同样出现这一现象。它支持优先检查查询批次噪声，但尚不能证明增大batch就一定能学出更好的画像，也不能排除当前共享表示下的真实可改进方向本来就很弱。

RL每步能区分八动作命中质量的query中位数仅WebVid 9/128、Yandex 3/128；相同扰动下两半query梯度的余弦中位数为0.0078/0.0041，约半数步为负。命中梯度远大于成本/漂移项，总梯度与命中梯度余弦约0.999，不支持“惩罚压住学习”作为主要解释。

随机动作转确定均值有局部差距，但严格匹配仅覆盖80组、1188条重复query记录，每run只有126/128个独立query身份；区间包含0，部分差值受单条记录影响很大。共享画像表达不足仍未被单独验证。下一步建议固定μ与扰动，仅检验更多查询是否能稳定方向，暂不追加epoch、改表示或启动新训练。

每动作按真实GT集合交集重算hits/cost/failure/drift，原reward/gradient逐步回归。固定μ与八个扰动，对query作16次64/64二分，检查方向余弦与条件采样方差；这与比较相邻不同扰动方向不同，只识别query噪声。条件信噪估计约0，不能写成真实梯度不存在。

RL动作-query事件中入口变化27.55%/20.00%，命中变化仅2.69%/0.94%；最大单query占逐query命中梯度范数和的中位数30.75%/57.71%。暴露归一化后前41个query仍占约37%–40%/66%–68%。每run只有4086/4088行真正抽到，每行中位6批，未见10/8行不冒充已知零效用。

总梯度/hits余弦约0.999；RL hits范数中位0.667/0.563，drift0.0305/0.0161，cost0.00785/0.00561。μ最大绝对值≤1.047，原限±2，无撞边；B/PB满列秩16。这些反对“惩罚或退化使模型不动”的主解释，但没有排除长期正则影响或表示不足。

随机/确定只匹配checkpoint s与step s+1的精确μ及相同query，共80组1188条重复记录；每run126/128个query身份。WebVid RL随机均值略好但区间跨0且去最大单条记录后明显缩小，Yandex与ES混合。全部中心/选中/末点统计表明小正值可来自极少query和正负幅度差，不能据monitor最高点宣称泛化成功。

## 执行、验收与边界

重算1,773,568条原返回、12800奖励、1600分解、88中心（train/monitor共176统计）；同入口时原NSG输出/graph NDC一致。独立集合评分32768条、复核32个分层step的方差与半批方向、全部1188精确匹配。主分析实际线程1、约8.454s、RSS约168MiB，不含阅读/编写/绘图/最终验收，不能称训练或查询性能。

E37全部2721文件在前后SHA保护；所有原训练/模型/图/标签/结果保持。旧root完成时身份与本轮root变更前件各自保留，不静默改写E37 final_artifact_freeze。结论不构成表示不可学习或新性能GO，原E37开发门与默认不变。

## 产物与未执行接续

[逐步](../entry_method_exploration/20260912_offline_profile_diagnosis_v1/results/steps.csv)、[逐动作](../entry_method_exploration/20260912_offline_profile_diagnosis_v1/results/actions.csv)、[query暴露](../entry_method_exploration/20260912_offline_profile_diagnosis_v1/results/query_exposure.csv)、[匹配记录](../entry_method_exploration/20260912_offline_profile_diagnosis_v1/results/matched_queries.csv)、[全部中心](../entry_method_exploration/20260912_offline_profile_diagnosis_v1/results/centers.csv)、[梯度图](../entry_method_exploration/20260912_offline_profile_diagnosis_v1/figures/gradient_diagnosis.svg)、[独立核验](../entry_method_exploration/20260912_offline_profile_diagnosis_v1/reviews/independent_verification.json)。源代码均在该独立版本src，输入与旧目录保护SHA在reviews；仅复核派生结果，不原地重训或改旧选择。

最小后续是固定μ=0/主RL及各自八个原动作，用已有train另取1024行分块检查方向能否稳定，正常36864次NSG、建议总硬限40000、0optimizer更新。此控制仅为建议，尚未构图/查询/训练；详细范围和停止条件见[s-target](../s-target.md)。若更大批次方向仍不稳，不继续堆epoch；若可稳定，再讨论同总调用预算的microbatch累计，保留预算代价控制。
