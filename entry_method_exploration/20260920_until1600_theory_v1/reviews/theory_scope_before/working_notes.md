# 限时理论研究工作记录

2026-09-20 13:05:42–16:00（北京时间），当前目标是持续推进研究，不保证截止时找到正收益方法。E106已完成且不重跑。

当前已把GT10相对固定NSG入口的系统收益、相对GT1的多目标增量、小图恢复自身排名的能力和有限beam入口交互分开检验。E107/E108/E109已验收，E110全矩阵运行中。没有新训练或held-out访问，原默认保持；最终状态以16:00验收为准。

已复核E104 set_ce：使用实测优集合的总概率损失，并非简单丢掉联合信息的逐hub标签；不能把其失败误诊为未用联合监督。历史finite-beam trace含额外信息但压缩成本/泛化未过门；不重开同64NN Atlas。

拟研究的进一步理论：固定raw-IP搜索的决策由距离排序及有限候选池状态共同决定；完整确定性轨迹在严格比较符号不变的query区域内保持，而画像分数改进没有独立的搜索收益保证。此观点须在当前kernel上验证具体比较语义，不能直接宣称新定理或可部署改进。

原论文线索：Oguri/Matsui 2024 adaptive entry; Al-Jazzazi et al. 2025 distance-adaptive beam; Avi/Musco 2026 almost navigability。均需核对其图、距离、OOD、beam条件，不把欧氏可导航保证直接套到原raw-IP底图。

## 已完成证据

- [E107初始化因素](../stages/e107_initialization_factorial/report.md)：两集各4096曝光query，144真实K1/K100点；单位原hub单入口已经获得对固定NSG的大部分均值收益。GT10增加两入口的18个K/L均值17负/1正，多数区间跨0；另有实际kernel合成反例，入口增加无一般单调保证。1,181,184真实NSG，2合成调用，无QPS。
- [E108普通小图与完整wall](../stages/e108_unit_hub_online/report.md)：三控制54点、162轮；单位hub在Web有质量信号，Y K100均值负且速度总体更低，没有跨集默认替换。GT10小图对自身精确top3入口成员召回高于Unit，路由NDC少。精确与ANN两层质量差值恒等式逐query验证，ANN项可正可负。1,106,688 NSG、4新小图、0新GT/训练。
- [E109完美代理信息门](../stages/e109_perfect_proxy_gate/report.md)：预锁fit2048/集，真实目标均值、区域覆盖两个不可部署代理对两个exact强控制。Yandex均正而Web未转化；Web覆盖35.42%→68.93%，R1反而−0.6836pp。两代理均未过跨集训练门，不训练、不调门。66,304 NSG、0新GT/图/训练/QPS。
- [首节点诊断](initial_seed_order_v1/initial_order.csv)：0新NSG/ANN，全4096行原始距离与旧输出对齐。GT10三入口重排使Web47.85%、Y42.41%改变首展开节点；单位hub为0%、7.37%。完整各K/L与两预定义组保留。这是关联，E110正在作同集合反事实干预。

## 已推导、未冒充性能结论

- [目标几何](target_geometry_derivation.md)：均值回归损失分解、代理top3后悔界及不能省略的搜索桥接误差δ。
- [区域后验](coverage_posterior_derivation.md)：真实GT10区域质量、交叉熵/KL到覆盖后悔界，同样不能自动推出有限beam Recall。
- [保分数导航等价性](score_preserving_navigation_equivalence.md)：同一有序图上严格保查询分数的双侧变换，与图内恢复P的普通HNSW轨迹等价。结合E95避免同A加在线逆变换的重复投入；未运行新变换。
- [学习目标与搜索合同](learning_objective_and_search_contract.md)：GT10的条件query均值解释、闭式最优对象、不同误差层、动作margin证书、单调候选合并保证及成本前提。固定q/图的结果是确定函数，有限样本未学会不等于固有随机不可预测。

## 当前执行与边界

[E110](../stages/e110_first_expansion_intervention/protocol.md)固定GT10同三入口，只强制画像top1第一次展开一次，然后恢复原循环；原1/3入口控制、真实K1五L/K100四L。预计442,880 NSG；第一次编译签名遗漏2.02秒失败，0搜索，前件完整保留后机械修正。两集smoke通过，控制输出、同首节点no-op、真实首展开、count/plain验证均嵌入全量执行。当前尚未做最终质量判定。

预算台账以[状态](../state.json)为准；已完成2,354,176真实NSG，E110另预留442,880；全时段4M/2GiB、15:50禁止新搜索、16:00交付，均不因还有时间而扩大旧方法网格。余下研究按结果决定，不预先排网络/seed/ef试验队列。
