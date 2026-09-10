# Fast入口选择根因诊断：冻结协议

2026-09-08。用户已明确授权实际实验，目标是查清Fast为何未选到好入口，区分实现/近似误差、画像代理错位和经验上的预测困难。此前C8固定anchor联合选择只是未验证假设，本轮不训练该模型、不恢复旧夜间/区域/Multi-view计划。

## 1. 对象与解释边界

复用WebVid-2.5M和Yandex official 10M的原始IP、原NSG、独立QGT5K raw hubs及同20K paired Fast画像。Fast算法仍是现有公式；采用20K版本是为了将诊断pilot与画像拟合分开，不能与旧30K/validation oracle数值直接相减。

本轮“最优”严格限定为当前H个真实hub（815/821）、指定L、原kernel下最高Recall@10的入口；并列最优全部保留，NDC单列。同一查询在不同L下可以有不同最优集合。它不是全部base节点或全部入口组合的全局最优，也不是可部署路由器。

只读取base/图、QGT和router_train侧query/既有GT；不打开原始validation/held-out，不生成新exact GT，不修改旧模型/图/源码/二进制。原有raw query直接用于Fast HNSW与NSG；单位化只用于几何basin、邻近查询诊断和画像复算。

## 2. 预定查询与预算

- 主样本：每数据集router_train `[0,10000)` 中按 `SHA256(dataset + "|fast_diagnosis_v1|pilot|" + decimal_row_id)` 排序取512条；哈希并列按行ID。该部分是已历史使用的开发pilot，不是新鲜测试集。
- 密度控制：取上述前128条，各自在后20K `[10000,30000)` 中取cosine最近的查询（float64单位向量点积，分数同分按原行ID）；选择只使用query向量，不查看搜索标签。保留距离与GT10交集供事后分层。
- 随机控制：后20K排除已选最近邻，按 `SHA256(dataset + "|fast_diagnosis_v1|random_fit|" + decimal_row_id)` 排序取128条，依次与前128条pilot配对。最近邻去重后，每数据集总行数不超过768，前512行为pilot。
- 所有选中行均穷举H个单入口，K=10，L={64,128}，保存完整hitcount/hitmask/NDC/返回ID矩阵。pilot额外真实运行同一次ef10路由C8内的28个pair和56个triple；不强制anchor。
- 对照包含Fast1/2/3与相同画像的exact1/2/3；Fast3来自同一C8前三个。额外保留旧默认HNSW seed100的路由与三入口结果，主路由seed为paired Fast的20260828。所有HNSW均M16/efConstruction200/ef10，不扫参。
- 配置与结果落盘前绑定行ID、输入SHA、编译器/源码/库身份。验收仅使用辅助fit行，不能根据pilot效果改实现/参数。count/plain、重复与入口顺序核对失败先判实现无效。

全H单入口上限 `768×2×(815+821)=2,512,896` 次；pilot pair/triple加其他固定对照保守上限约18万次，总搜索上限300万（含验收/重复）。单重数据集进程、16线程、RSS上限80GiB、新产物上限2GiB、/data剩余至少10GiB；真实搜索阶段合计最长4小时。到限保留已完成部分并标明未覆盖，不追加参数/样本或训练新模型。本预算是研究成本控制，不是方法部署成本。

## 3. 必须回答的诊断问题

1. **实现是否正确？** 重hash原始图/base及训练侧输入；核对hub与真实base ID、画像/ID一致性，按现有builder完整复算20K画像并比较；验收同入口count/plain/重复结果、实际入口数、raw-IP与GT评分隔离。Fast HNSW和exact画像排序使用相同距离函数，浮点tie/跨累加方式差别单列。
2. **近似检索是否是主要损失？** 比较approx/exact top1/3/8集合与距离；在相同真实kernel下比较approx1/2/3与exact1/2/3的Recall/NDC。单入口精确路由的差异可以从全H矩阵取出；不能把候选ID不同直接当检索质量下降。
3. **画像评分是否对应搜索效用？** 计算每query全H真实Recall与画像排名的关系；exact top{k=1,3,8,32,64}能否包含任一并列最优入口、最高Recall损失多少。报告所有并列最高Recall集合A0，以及少一个GT10命中的A1（容差0.1 Recall，明确不是微小性能差）。
4. **训练标签的几何代理是否合适？** 用该query真实GT1向量到normalized raw hubs的cosine确定原builder标签b(q)，只作为事后oracle诊断。报告 `R*−R(Fast1)=[R*−R(b)]+[R(b)−R(Fast1)]`。后项可为负，不能强行解释成两个非负错误率；对照Fast恢复basin标签的准确率与真正搜索regret。
5. **固定三个入口与anchor是否合理？** 从C8真实single/pair/triple比较最优质量、Fast1/2/3、含Fast rank0的最佳triple与不受anchor限制的最佳triple；比较独立single命中并集的预测与真实联合搜索。不能把单入口oracle−Fast3直接归因于路由准确率。
6. **最优入口是否难预测？** 先看A0/A1集合大小与任意唯一tie-break标签的差别，再看跨L集合交集、最优入口跨L迁移的Recall损失；最后将20K内最近fit查询的A0移到对应pilot，比较随机fit来源。源A0的均值、最小NDC确定选择及目标上最好值分列，目标上最好值仍是oracle。按query相似度和GT10重叠分层，区分样本稀疏、真实目标变化和入口搜索效用变化。该实验只能说明当前表示/样本密度下的局部可迁移性，不能证明一般不可学习或复杂度下界。

## 4. 分析与统计

主描述族为每数据集×两L的：exact1−Fast1、exact3−Fast3、全H单入口最优−exact1、全H最优−exact C8内最优、GT1 basin−exact1、最佳无anchor triple−最佳anchor triple、最佳triple−Fast3，以及最近fit选择−随机fit选择。八种对比×两数据集×两L共32项；先保存全族再解释，给query配对均值、普通95%与Bonferroni全族95%区间，bootstrap 10,000次，固定PCG64 seed20260908。512个query为主统计单位，最近邻对比仅前128条；timing轮、候选数和动作数不是额外独立样本。

其余集合覆盖、分位数、Spearman、GT重叠分层及个例均作描述性证据，不追加检验后声称确认。置信区间描述历史pilot抽样变动，不能代替三独立构建或新测试。关联不能直接称因果；exact替代ANN的同入口数对照只隔离当前评分下的近似检索差别，GT1 oracle不是可部署方法。

本轮以离线instrumented诊断为主，不发布端到端QPS/Pareto改善结论。分列输入校验、画像复算、HNSW构建、路由、全H穷举、组合搜索和分析耗时；旧exactGT/QGT/图构建耗时未知记null+reason，不能记0或免费。

## 5. 交付与下一步

交付复现脚本/隔离二进制身份、冻结输入与行ID、每L完整矩阵、验收、统计JSON、图和报告；同步summary/spec/s-target。报告须分别说明确定的实现问题、受支持的代理/选择瓶颈、仅有相关性的可预测性现象、未证明的理论结论。诊断结束后依据证据决定先改哪一层，不自动训练C8组合模型或重开失败分支。
