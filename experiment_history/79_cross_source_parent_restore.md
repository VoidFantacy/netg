# 79｜双来源支持的局部父画像恢复（E90）

固定E89原fit通过的13/8个动作，不扩候选/调强度；aux前3976加入训练，对各动作真实NSG支持筛选，保留5/0个。支持3976和fit20K都重测合并，后3976只评估预冻整体模型；所有aux历史暴露，接受不是盲验证。它检验E89损益能否跨来源保留，和E60的40背景稀疏小半径RL不同，跨源支持概念本身不新。

Web支持单项和51→实并49（3非加性query），fit71→61（13非加性），失败−5/−8；随机支持+30/fit+60。接受后半对compact+21命中、救回4/新增3；对P−22、24/26；对E89+7、4/2；对随机+4、1/2。完整门FAIL，P损失与随机/分半不稳保留。Y0个通过筛选，两模型逐字等于compact；接受相对P+81/失败−8全部继承compact，非新方法收益。两集停止固定筛选规则，不据接受反馈重选。

新增163858NSG=1938训练+161920辅助，616304HNSW=454704训练+161600辅助。4物理导出含2非零Web、2零更新Y；2离线效用筛选拟合，0构图/编译/梯度/GT/QPS。准备0.188s、训练42.228s、辅助130.915s含load/count/cache/I/O，不作QPS；继承P/GT总成本未知。所有ANN串行CPU15、实际及库1线程。

完整缓存来源、source row、21动作、真实合并与随机、非向量图bytes、plain/count/原kernel、支持前缀/旧P与compact和E89逐字回归、全部集合/mask和7slot入口核验。421失败并集/185状态变化/2105五配置单元保存，角色逐行区分。P-fit含旧train/monitor，辅助全部历史暴露；E34最终query/GT/row及held-out未打开。

[报告](../entry_method_exploration/20260913_until2100_v1/stage31_cross_source_restore_v1/report.md) · [协议](../entry_method_exploration/20260913_until2100_v1/stage31_cross_source_restore_v1/protocol.md) · [源代码](../entry_method_exploration/20260913_until2100_v1/stage31_cross_source_restore_v1/src/train.py) · [门](../entry_method_exploration/20260913_until2100_v1/stage31_cross_source_restore_v1/results/gate.json) · [成本](../entry_method_exploration/20260913_until2100_v1/stage31_cross_source_restore_v1/results/cost.json) · [训练核验](../entry_method_exploration/20260913_until2100_v1/stage31_cross_source_restore_v1/reviews/training_verification.json) · [辅助核验](../entry_method_exploration/20260913_until2100_v1/stage31_cross_source_restore_v1/reviews/verification.json)
