# 14｜固定旧/新画像的选择性改道

2026-09-10夜间，E25。状态`SELECTIVITY_NOT_GENERALIZED_NO_FORMAL_GO`。用户要求保留有效改道、减少受损query，并授权夜间深入分析、提前完成可适当探索；本卡记录已经完整执行的E25，不把后续探索计入此版本。

## 问题、固定策略与监督

A0为E24 matched Fast20K/GT1硬画像，A1为E24按旧cal冻结的主画像：WebVid GT10软T0.016201138496398926、Yandex GT10硬。原base/raw-IP/NSG/QGT seed20260828/H815、821、三个互异真实ID保持不变。每query在搜索前选择完整A0/A1三元组，之后只执行一次原NSG，不使用图probe、restart、top32重排或结果合并。

BaseGate用旧路由7个特征，选新时才执行A1路由；DualGate用两路13个特征，每query执行两路。特征为query范数、归一化画像分数/间隔、fit ESS与画像角位移、两路间隔差及入口重合度。GT、实际Recall、graph NDC和trace不是部署特征。

fit从router_train后20K中按seed20260910取8192，cal为[2048,4096)，audit为[4096,6144)，各2048；配对L64/128真实三入口结果。E24画像见过fit query；这些池都有历史开发使用。正/负标签权重为同query两L的正命中增量P与负命中损失N；零差不当负类，跨L冲突同时进入两项logistic损失。

每信息版本三λ={.01,.1,1}，每模型阈值只取0及fit logit的10/25/50/75分位数，每数据集30候选。fit标准化、clip±6、确定性float64凸求解，截距不惩罚。cal要求R/Rh≥75%、A/Ah≥25%及净命中≥max(0,always-A1净命中)，按预先固定ties选规则；未达标时冻结最接近的非恒定规则作反证。全部模型/输入/候选/代码/binary在audit前冻结，audit只报告，之后才读取历史validation前2000；held-out未打开。

## 主结果与不稳定性

WebVid cal选DualGate并达标；Yandex cal两规则都失败，主BaseGate仅是按协议冻结的反证对象。

| 数据集 / cal主规则 | 分段 | 有效事件保留R | 受损事件避免A | 正命中保留Rh | 负损失避免Ah | 净命中 vs A0 / always-A1 |
|---|---|---:|---:|---:|---:|---:|
| WebVid / DualGate | cal | 86.88% | 25.44% | 87.26% | 29.62% | +84 / −20 |
| WebVid / DualGate | audit | 79.48% | 21.95% | 80.12% | 27.12% | +141 / +127 |
| WebVid / DualGate | validation | 80.66% | 24.77% | 84.17% | 24.62% | +123 / +91 |
| Yandex / BaseGate | cal | 61.43% | 44.05% | 69.83% | 40.94% | −40 / −110 |
| Yandex / BaseGate | audit | 38.71% | 47.14% | 48.58% | 32.55% | −81 / −51 |
| Yandex / BaseGate | validation | 31.08% | 62.90% | 38.41% | 54.05% | +21 / +91 |

表中L64/128合并，全部query保留分母。WebVid validation门槛只差约1个受损事件/2个命中损失单位，不能因此断言机制完全无效；主要限制是audit波动与额外成本。Yandex主规则减少损失时放弃大多数收益。

两数据集各2K×六方法×五L，共60个正式点，独立plain wall各3次。WebVid DualGate相对A1五L的Recall变化为+0.070/+0.090/+0.025/+0.070/+0.025pp，QPS中位数为−6.50/−4.08/−2.24/−1.36/−1.01%。Yandex BaseGate分别−0.115/−0.235/−0.130/−0.090/−0.075pp，QPS为−1.15/−1.35/−0.62/−0.91/+0.69%。非主DualGate在Yandex也有小正负点，保留全部原值，不按validation提升为主规则。

两个门控×两数据集×五L相对A1的20项Recall差，描述性95%配对query区间全部跨0；没有任何点同时Recall提高且三轮对应QPS都提高。观测非支配点、同L双升与稳定方法GO分别报告，粗L曲线未作等Recall性能保证。

## 机制与成本

fit真正有非零配对权重的query只有WebVid1081/8192、Yandex401/8192；总权重ESS约556.85/190.96。权重最大1% query贡献27.47%/57.79%的监督。分段波动可能含稀疏效果抽样和画像fit偏差，本轮未分离为因果结论。

WebVid DualGate的weighted AUC为fit/cal/audit/validation=0.6064/0.6132/0.4923/0.5693；Yandex BaseGate为0.5524/0.5552/0.3754/0.4962。Yandex DualGate则0.6553/0.3958/0.3365/0.6118，不能据单一好分段宣称可迁移。所有凸模型已收敛；失败不是因求解器没跑完。

固定同一query两L选择的免费oracle，fit仍保留2217/1137额外命中，相比按L分别看答案仅少98/30；不能把主要缺口归因于模型不读L。oracle无部署QPS。特征四分位数只从fit确定；后续分层及最大的收益/损失query只作解释，不重选规则。

L128路由单测，A1→Base/Dual：WebVid6.532→16.076/19.140μs/query，Yandex4.368→6.542/10.223。Base每query另收3次画像内积、选新再收费A1；Dual固定两路和6次额外内积。query范数、特征、预测等都进端到端wall；两图是实际部署资产，分项wall不相加作QPS。

真实调用1,089,152，修复预留0；合成5144。实际搜索子进程1227.50s，含加载/建图/预热/计数/核验/I/O；最高观测RSS10.193GiB，全部实际线程1、CPU15。原GT/QGT/NSG/E24从零成本未新测。

## 验收、修正与收口

124点219584原搜索输出独立GT10评分；validation四条原曲线80000输出与E24的ID、距离bits、入口及route/graph NDC逐位相同。全部门控输出逐query等于被选策略，新增route收费复核通过；五L的选择/logit/入口和相应微型图一致。63项原资产hash、全部冻结文件、cal候选/目标/阈值和选择顺序独立重算通过。

初次准备因`Path`导入遗漏在创建数据集输入前失败，修复后日志另存，协议未变、无真实调用；预检编译后补真实ID范围检查，在任何真实搜索前重编译，初版bin保留。所有真实job一次成功。E25协议全部结束，不扩模型、阈值或调用上限。若夜间继续离线单路画像收缩等直接相关探索，必须另立协议/目录/预算；不恢复旧C/probe或自动启动2A大标签链。

## 原始证据

- [完整报告](../entry_method_exploration/20260910_selective_profile_gate_v1/report.md)、[协议](../entry_method_exploration/20260910_selective_profile_gate_v1/protocol.md)、[命令](../entry_method_exploration/20260910_selective_profile_gate_v1/commands.md)、[状态](../entry_method_exploration/20260910_selective_profile_gate_v1/state.json)。
- [全部表格](../entry_method_exploration/20260910_selective_profile_gate_v1/results/tables.md)、[分析JSON](../entry_method_exploration/20260910_selective_profile_gate_v1/results/analysis.json)、[成本](../entry_method_exploration/20260910_selective_profile_gate_v1/results/costs.json)、[曲线](../entry_method_exploration/20260910_selective_profile_gate_v1/figures/recall_qps.svg)。
- [候选与选择](../entry_method_exploration/20260910_selective_profile_gate_v1/models/selections.json)、[audit前冻结](../entry_method_exploration/20260910_selective_profile_gate_v1/models/frozen_before_audit.json)、[audit](../entry_method_exploration/20260910_selective_profile_gate_v1/reviews/audit_report.json)、[validation核验](../entry_method_exploration/20260910_selective_profile_gate_v1/reviews/validation_verification.json)、[资产/选择审计](../entry_method_exploration/20260910_selective_profile_gate_v1/reviews/immutable_integrity.json)、[最终验收](../entry_method_exploration/20260910_selective_profile_gate_v1/reviews/final_audit.json)。
