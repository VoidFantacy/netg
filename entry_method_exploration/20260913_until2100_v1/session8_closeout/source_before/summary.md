# ACSG 当前结果摘要

第8会话E85路由前query线性选择缓存实验完成，双集接受门FAIL。固定前3976拟合/后3976接受：Web对P−35命中/失败+3，对compact+8/0；Y对P+24/−3、对compact−57/+5，原正收益仅保留57.68%/57.92%。训练收益不迁移，停止固定线性规则。4次岭拟合、0新增ANN/QPS，在线预测尚未实现。接受池历史已暴露，E34最终原始输入未打开。[E85报告](entry_method_exploration/20260913_until2100_v1/stage26_query_gate_feasibility_v1/report.md)。

第8会话E84查询排名缺口补边完成：Web相对compact净+42命中/失败−4、两半非负，保留局部修复；相对P仍−17/失败+7。Y相对compact−4/失败不变。双集完整预锁门FAIL，停止固定投票规则，无新QPS。129536 NSG/209792 HNSW、2图监督训练/4边安装、0普通build/新GT；[完整报告](entry_method_exploration/20260913_until2100_v1/stage25_query_shortcuts_v1/report.md)。

第8会话E83同hub补边完成，双集预锁门FAIL。固定compact原图分别追加1359/1285条边，全部旧边/画像/上层不变；相对compact Web−1命中/失败−1、Y0/0，routeNDC+5.16%/+2.35%。同节点度近邻控制也无净收益，停止固定追加规则，不从NDC推QPS。129536 NSG/129280 HNSW、4静态边安装，0普通构图/新画像训练/GT；准备元数据两错误原件与未知耗时保留。410条失败并集与完整收益保留在[E83报告](entry_method_exploration/20260913_until2100_v1/stage24_sibling_links_v1/report.md)。

2026-09-13 第8会话E82：三种新目标bank完整画像排名对应的真实NSG已完成，六组预锁诊断门均FAIL。Web target相对compact+256命中/失败−22，但相对精确P仅+3/+2；Y target/conditional/joint相对compact分别−89/+9、−104/+5、−45/+3。停止以修近似误差为理由延伸这些新目标bank，原compact局部信号保持。

7762 NSG、3593唯一新键、43800旧复用/319互alias，0HNSW/训练/构图/新增QPS。159040集合评分、256回放/64原kernel通过，517失败并集/343状态变化及精度分组保留。历史aux7952反馈计训练，E34最终/held-out未打开，整日目标未完成。[E82报告](entry_method_exploration/20260913_until2100_v1/stage23_target_exact_utility_v1/report.md)。

2026-09-13 第7会话最新E81：query/条件GT等权联合分组双集未过预锁门，本版本停止。 从E66原Q分配开始，以两视角单位中心共同更新20轮；最终仍仅输出原query聚合画像，在线接口不变。

| E81 aux7952 L128 | 对P：净命中 / 失败变化 | 对compact | 对E80条件目标 |
|---|---|---|---|
| WebVid | -78 / +8 | -19 / -3 | -39 / -9 |
| Yandex | +58 / -11 | -62 / +2 | +70 / -8 |

E79–E81本会话累计388608 NSG/387840 HNSW/8真实build/8离线画像训练，native操作wall 331.417s；0新增QPS，E34最终未打开。E81离线681.920s，构图0.356s。[E81报告](entry_method_exploration/20260913_until2100_v1/stage22_joint_view_partition_v1/report.md)。下述E79/E80结论保留。

2026-09-13，第7串行会话完成E79/E80目标分组改进。E80按每个hub原GT归属的条件权重形成目标特征，最终仍聚合原query画像。E80双集预锁门失败，本条件均值版本停止；E79全局均值原门失败保持。整日21:00目标未完成，E34晚间最终未进入。

| E80 aux7952 L128 | 对P：净命中 / 失败变化 | 对compact | 对E79全局目标 |
|---|---|---|---|
| WebVid | -39 / +17 | +20 / +6 | -28 / +10 |
| Yandex | -12 / -3 | -132 / +10 | -12 / -1 |

E80固定原rank权重/A/P、GT/rawIP/NSG/H815/821，按hub流式条件目标两分组，物理画像Web/Y=1883/2223。beta归一化避免极小soft权重被截断；A=0表示该hub无支持，不作零目标监督。目标语义改变也影响子支持、容量和小图，不能当单中介因果或新颖性结论。

E79主候选对P Web−11命中/失败+7、Y0/−2；对compact Web+48/−4、Y−120/+11；对置换+73/+213但未过原门。目标定义不是全部问题的已定原因。完整旧收益保留/丢失、新收益/新损伤和GT成员得失均保存。

E73/E74 Yandex局部信号保留：五L对P命中+99/+59/+38/+1/+15、失败−10/−7/−4/−1/0；五轮QPS范围均跨零，约1.9%～3.0%仅描述性插值。Web L128−23命中/失败+6。E75/E77/E78各原停止门保持，默认未替换。

E79/E80两阶段新增259072 NSG/258560 HNSW/6真实build，6离线分组训练及2原Q复现，0梯度/新GT/编译/新增QPS。E80离线450.089s、构图0.376s、native110.429s；操作wall含加载/count/I/O不是QPS。继承GT/P成本未知。所有ANN串行CPU15/实际进程与数值库1线程，terminal0后独立评分；E80旧三对照47712行全字段恢复、256原kernel与全7slot/图身份通过。

E80失败并集486个dataset/source-row、其中291个失败状态变化，完整GT/入口/返回ID保存。P-fit含旧train/monitor，aux7952及两半已观察且反馈计训练，cal/audit历史使用；E34最终与held-out未打开。各阶段source_before/root_after和旧seal保持。

资源按E80新前瞻64MiB上限、6.8GiB下限外另64MiB晚间+4MiB交接；旧版本预算不变，禁止清理历史。E79 build计数元数据原件与独立修正保留。

[E80完整报告](entry_method_exploration/20260913_until2100_v1/stage21_hub_conditioned_targets_v1/report.md) · [E79报告](entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/report.md) · [最近E74 QPS–Recall/失败曲线](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/report.md) · [下一阶段](s-target.md)。

第7会话综合汇报：五主方法零命中并集503条、失败状态变化319条，全量GT10/入口/返回保存；E81 Yandex对P+58/失败−11、对条件目标+70/−8是局部修复，仍不及compact且对P两半-30/+88，原门失败。[综合报告](entry_method_exploration/20260913_until2100_v1/session7_report/report.md) · [失败图](entry_method_exploration/20260913_until2100_v1/session7_report/failure_queries.png)。E80封存图的标签留白修正版在综合报告，原图及seal不动。E81独立检查器修正不改任何模型/查询结果。
