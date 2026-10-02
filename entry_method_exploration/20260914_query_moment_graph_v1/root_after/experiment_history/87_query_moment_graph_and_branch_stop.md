# 87｜查询二阶统计构图与当前分支停止（E95）

2026-09-14。用户要求持续推进直到得到更好方法或停止当前分支。本轮定向研究后执行E95，四个候选–数据集组合均未过冻结开发门，决定`STOP_CURRENT_FIXED_H_PROFILE_GRAPH_BRANCH`。默认保持Web GT10-soft-t1 / Yandex GT10-hard；不是所有RL/入口学习的不可行性结论。

## 方法与对照

固定P/H/真实ID/raw-IP/原NSG，以P-fit20K raw query的未中心化二阶矩M/平均对角尺度构造full对称平方根（主）和diag平方根（备）。离线C=P A在原M16/efConstruction200/seed20260828上普通建图，图中C逐字恢复原P；线上仍原HNSW3→原NSG，无变换/MLP/多画像。与E56局部有界rank16扰动训练不同，本轮是全维闭式统计；与E78不同，评分恒P；从P出发也不同于compact修补。

identity完整重建恢复原图SHA。两集各128预检后，完整7952历史aux×两L64/128×三模型；固定两半3976，fit源行10000–29999与aux2048–9999不交叠但有历史使用。模型和门先冻结，未使用E94最终载荷/失败例或held-out。aux接受反馈计开发/训练信息，不称盲验证。

## 真实结果

| 数据集 / 构造 | L64 / L128 Recall变化pp | L64 / L128失败净新增 |
|---|---:|---:|
| Web full | −2.3868 / −1.4940 | +225 / +130 |
| Web diag | −3.8556 / −2.0297 | +359 / +165 |
| Y full | −0.0553 / −0.2364 | +23 / +28 |
| Y diag | −0.0478 / −0.0666 | +3 / +3 |

八全量与16半集Recall差全部负。路由NDC分别下降35.49/52.82/13.96/5.50%，但L128总NDC分别+1.85/+3.03/+2.00/−0.21%。不能把便宜路由当总搜索收益，QPS未测；条件wall阶段依门未启动。完整P评分保持不保证原近似路由行为，主/备已真实改变入口，不是全空动作。

本轮统计构图失败，加上既有更新控制/动作支持/组合迁移/最终前沿证据，已无足够依据继续相同固定H画像/小图增强分支。停止当前参数扰动RL、多画像和局部修补及本轮两闭式变体；不再扩大相同网格或恢复9月13日会话。GT10与历史局部正信号保留。

## 成本与核验

194304 NSG、193920 HNSW、6普通build含2 identity、4画像恢复安装；统计0.389s、native build0.270s、4查询进程操作182.810s，0新GT/梯度/依赖/编译/QPS。完整原GT/P成本未知，aux选择信息不能称零训练信息。2 identity图全bytes回归，4新图P/label/nonvector保持，96960集合评分、16160基线八字段回归、384原kernel样本、跨L入口及预检前缀回归通过。全部CPU15/实际1线程、串行、无原生重启；原资产SHA/大图stat保护与根文档前件保存。

[完整报告](../entry_method_exploration/20260914_query_moment_graph_v1/report.md) · [停止决定](../entry_method_exploration/20260914_query_moment_graph_v1/decision.md) · [方法比较](../entry_method_exploration/20260914_query_moment_graph_v1/research.md) · [协议](../entry_method_exploration/20260914_query_moment_graph_v1/protocol.md) · [门](../entry_method_exploration/20260914_query_moment_graph_v1/results/gate.json) · [原表](../entry_method_exploration/20260914_query_moment_graph_v1/results/aux_paired.csv) · [实际进程/命令](../entry_method_exploration/20260914_query_moment_graph_v1/logs/jobs.json) · [验证](../entry_method_exploration/20260914_query_moment_graph_v1/reviews/aux_verification.json) · [最终验收](../entry_method_exploration/20260914_query_moment_graph_v1/reviews/completion_audit.json)。旧86、E94和9月13日封存原件不回写。
