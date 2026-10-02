# 124 E120 目标预算响应与查询信息审查

日期：2026-09-22。版本 `entry_method_exploration/20260922_target_budget_response_v1/`。状态 `STOP_TARGET_LOCAL_INFORMATION`。完成用户授权的下一阶段及其条件信息对照，没有可部署提升；Web GT10-soft-t1 / Yandex GT10-hard 与生产 E99 保持。

## 问题与理论

记录123发现 L128 不是统一的高召回工作区间，但不能因此直接重做全 H 标签或换评分器。本轮把问题拆成有限策略的事后余量、低预算决策迁移和在线查询信息可预测性。理论目标为预算条件化的动作相对默认条件均值；低预算最优动作的目标预算遗憾不超过两倍最大响应漂移。这是简单界，不是新颖性或有效性证明。6000 个合成不等式检查和单调响应仍可反转偏好的抽象例子通过，不冒充真实 NSG 构造。

PAC 算法选择、ICML2020 图搜索理论及 ICLR2026 动态随机游走论文帮助界定动作族、分布和假设，未提供对当前 raw-IP 确定性有限 beam 的直接收益保证。预算条件化和 kNN 本身不是论文贡献。具体论文链接及条件见版本 theory.md / literature_addendum.md。

## 冻结输入与实际执行

复用 E107 同两集各4096条历史曝光 E105 query、GT100、原 raw-IP/base/NSG、画像、实际入口及顺序。八策略为 NSGFixed1、UnitHub1/3、GT11/13、GT101/103、DefaultANN；选择域仅默认加六精确策略，NSGFixed1 不纳入 oracle。底图、主搜索、固定 L 的展开和停止规则不变。

复用144旧点，仅新增 Web K1/L640、K100/L1120/1250 和 Y K1/L96、K100/L200 的八策略，共40点。预算来自 E103 另一批 query 的90%区域，未声称新样本所有主点恰好达到90%。主点冻结为 Web K1/L800、K100/L1250，Y K1/L128、K100/L256。

四主点的七策略 oracle 增益都至少.25pp且至少一个非L128主点的低预算选择保留率不足80%，才触发信息对照。四折fit3072/outer1024，单位raw-query余弦、55近邻、float64、源行打破邻居同分；唯一主规则 TargetKNN 与 LowKNN、TargetFixed、ShuffleKNN 比较。各规则共享动作族和角色，只有标签预算或查询条件化不同；默认优先打破效用同分，未以外折标签选择邻居或训练。门要求两集主规则自身正区间、两K非负、胜过固定和置换控制的正区间、胜过低预算控制的正均值。

## 完整结果

| 主点 | 默认Recall % | oracle增益pp | L128选择迁移增益pp | 保留率 |
|---|---:|---:|---:|---:|
| Web K1/L800 | 89.1846 | 1.7578 | 1.6113 | 91.67% |
| Web K100/L1250 | 90.5815 | .4272 | .1851 | 43.31% |
| Y K1/L128 | 90.6250 | 2.3193 | 2.3193 | 100%（同预算） |
| Y K100/L256 | 91.0444 | .8125 | .5728 | 70.49% |

K100预算迁移不足80%，信息对照按门触发。K100主点最优动作集合有交集比例仍为94.41%/96.80%，不能把所有winner变化当成冲突；但迁移动作损伤70/62条query。Web K1未达严格90%，不得把本表称90%完整曲线。所有下端和旧预算结果保留，不追加结果驱动的L点。

| 规则 | Web等K召回增益pp | Y等K召回增益pp |
|---|---:|---:|
| TargetKNN | +.1637 | +.1368 |
| LowKNN | +.1912 | +.1848 |
| TargetFixed | +.3134 | -.0078 |
| ShuffleKNN | +.1591 | -.0336 |

TargetKNN的描述性95%区间为Web[+.0079,+.3180]、Y[-.0918,+.3721]pp；两K均值分别Web+.2197/+.1077、Y+.1953/+.0784pp。两集都没有超过固定和置换控制的正差值区间，且均值低于LowKNN。信息门两集失败，不换控制当主方法，不调k/特征/seed/动作池。预算错配得到证据支持，但“改用目标预算标签便能由当前局部几何可靠预测收益”未获支持。

有限动作oracle和L128真实响应均为事后特权信息，不是在线方法或全H上界。全部query历史曝光，bootstrap5000按query、K成对，信息分析折内重采样，仅描述性。没有成本门、端到端QPS或新鲜测试收益，未触发廉价实现分支；不否定所有表示/高预算入口选择。

## 成本、错误与审计

331136次实际NSG，其中327680完整样本、3456原核smoke；查询作业648.55秒，成功构建8.61秒，原生峰值9.920GiB。响应分析8.38秒、四规则双集8外折的非参数标签估计4.43秒；有新预算响应标签和学习估计，0优化器步骤，0新GT/画像/图/K10/新测试payload。成本为研究作业wall，不是候选QPS。

初次编译遗漏原.h依赖，0搜索失败；原失败日志/源/冻结留档，按原字节补齐8个头文件再构建，未改方法或kernel。完整count/plain、smoke链接E99逐位一致，所有新默认恢复E105，入口身份恢复E107，CPU15实际1线程且串行。

独立成员循环重算184点/753664条query输出、23个预算迁移、全部信息动作/收益及128条邻居边界，88.79秒；另独立重算14个描述区间。690个旧消费文件、8个原头文件、协议/冻结源码/二进制身份保持。base在准备时全SHA复验；大图沿用stat并抽验嵌入向量，不宣称新全图hash。同会话独立数值实现，不是独立人员审查；未发现足以解释本结果的实现错误。

## 判断与接续

本阶段按停止分支完成，无待运行训练/搜索。默认与生产不变，E103仍最新完整五集前沿，E118仍最新候选完整性能曲线。本版目标预算加raw-query局部均值路线停止，不以加大模型或全H重标注续跑。后继须先给实质新的在线廉价收益信息、前作区别、可证伪条件及同监督简单控制，没有这种依据就停止该分支。

## 原始证据

- [报告](../entry_method_exploration/20260922_target_budget_response_v1/report.md)、[理论](../entry_method_exploration/20260922_target_budget_response_v1/theory.md)、[论文全文核查](../entry_method_exploration/20260922_target_budget_response_v1/literature_addendum.md)。
- [协议](../entry_method_exploration/20260922_target_budget_response_v1/protocol.md)、[配置](../entry_method_exploration/20260922_target_budget_response_v1/config.locked.json)、[状态](../entry_method_exploration/20260922_target_budget_response_v1/state.json)。
- [全部响应](../entry_method_exploration/20260922_target_budget_response_v1/analysis/response.json)、[方法表](../entry_method_exploration/20260922_target_budget_response_v1/analysis/metrics.csv)、[条件信息门](../entry_method_exploration/20260922_target_budget_response_v1/analysis/information.json)。
- [作业账](../entry_method_exploration/20260922_target_budget_response_v1/reviews/jobs_v2.json)、[原始输出独立审计](../entry_method_exploration/20260922_target_budget_response_v1/reviews/independent_audit.json)、[统计复核](../entry_method_exploration/20260922_target_budget_response_v1/reviews/statistics_audit.json)、[成本](../entry_method_exploration/20260922_target_budget_response_v1/reviews/cost.json)。
