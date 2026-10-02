# 后继候选的最小可证伪合同

2026-10-02，理论研究提案。这里给出具体可审查版本和停止条件，**没有授权、实现或启动任何后继性能实验**。本轮仅完成论文/源码/旧数组研究，默认不变。所有真实执行都需后续用户明确授权；旧164–166停止版本不回改。

## 当前优先级

| 候选 | 实质改变 | 首个必须解决的问题 | 当前状态 |
|---|---|---|---|
| A：原路由内native距离memo | 保物理图、队列与实际入口；复用同query同key的原距离bits | 有多少实际重复请求；扣除默认同优化与全部缓存费用后能否越过完整wall缺口 | HOLD_MEMO_MISSING_NATIVE_TRACE_AND_MATCHED_FULL_WALL |
| B：原阈值下确定性提前拒绝 | 保原逻辑路由决策；只省原本会拒绝者的完整dot | bound是否包住native浮点值、是否足够紧且比full-dot便宜 | HOLD_BOUND_MISSING_NATIVE_ERROR_AND_COST |
| C：GT10固定三桶raw目标精排 | 改候选集合及实际单入口 | 三桶旧slot覆盖低，现无新选点/响应；旧局部质量不能继承 | HOLD_COARSE_ACCESS_MISSING_SELECTION_RESPONSE_AND_FULL_WALL |
| D：动态H外target+原rank1/2 | 改实际三入口联合动作 | 访问是否便宜；完整联合响应会不会挤掉有用桥 | HOLD_MIXED_TARGET_MISSING_JOINT_RESPONSE_AND_ACCESS_COST |

排序依据是问题是否能被隔离和反驳，不是预期成功率或论文新意。A保留原选点质量，最易隔离成本；B的浮点/元数据问题更大；C已有明确覆盖风险；D还依赖目标访问与联合响应。没有候选满足可靠替换条件。

## A：输出保真memo

**可见输入与监督。**原query、原bank字节/slot映射、原距离请求；不新增GT、训练或动作选择监督。缓存状态限定一次完整router query，上层和底层同epoch。TargetBank相同raw目标ID只有byte/kernel一致才合并；默认画像只共享同一真实评分对象。所有物理slot保留。

**冻结动作。**Default3、TargetBank1均保持旧动作。基础四控制：Default3原版/memo、TargetBank原版/real-target memo。若解释跨slot重复收益，加TargetBank slot memo，另立因果控制而不据反馈挑cache方式。源码另确定上层终点在base会再评分一次；原版/同memo默认之外须保留直接传原curdist bits的UpperHandoff简单控制，两路都获得同机会，通用memo不得用增加全R lookup替代这一更简单控制。因此最低为两路各自原版/UpperHandoff/full memo共六臂；按已冻简单实现比较，不能据反馈调版本。接口、namespace/epoch和静态payload条件见[复用接口审查](memo_interface_note.md)。原ef10、图/层级/邻接顺序/tie、K/L、NSG主核保持；只包原路由评分回调。

**第一反证门。**逐位核验原版与memo的最终路由slot/分数、映射入口、NSG返回/距离、主图NDC、逻辑请求数；不得以Recall相同代替。任何变化先查实现/身份/FP/epoch错误，修复前不归给方法。函数有状态或不同kernel不可合并时，缩回合法cache key或停止该版本。

**费用门。**query epoch/reset、key映射、lookup/store与路由/输出全部放在同一timer内；计数模式与plain计时模式分开并作parity。记录逻辑请求R、unique physical slot、unique有效real-target key、actual native-dot调用、hit/miss，不把少dot记作少逻辑图访问。先用历史query作实现/费用辨识；不把它当独立确认。

最低固定成本窗口可取旧四中心：Web K1/L1000、K100/L1250；Y K1/L128、K100/L256。四点均保留。实际执行前应新锁上限、角色、重复顺序、最低可用增益和停止门；这里的窗口不是运行命令或性能授权。判定相对原版/UpperHandoff/同memo Default3中更快版本，见[完整成本条件](full_cost_conditions.md)；缓存若让默认变慢，不能据此降低门槛。若缓存不能越过缺口或默认净收益更大，结束这一版本，不调cache容量/ef/样本追正值。

最小成本辨识若沿E166，应明确冻结其实际span+batch4研究核，各臂相同；原E99输出回归不等于生产时钟相同。若改用生产E99，重新冻结/测全部控制，不能沿用旧D或旧QPS作速度证书。

**后续质量门。**严格保真继承旧目标库的正负质量。只有开发成本及适用范围事先明确后，才能安排未参与本轮方向选择的新来源确认；held-out继续封存。不能因为旧Web R1较好就给两集双K替换GO。

## B：确定性提前拒绝

**冻结对象。**保原TargetBank近似HNSW输出，不是恢复全bank精确argmax。底层只有原ef队列已满且可证明原接纳比较为假时才省full-dot；上层也必须证明原移步比较为假。其余节点算完整原距离并按原顺序参与队列，不用估计分数重排候选。

**新增输入。**便宜上界或partial dot、残差/边差元数据、query范数；全部需要计费。raw-IP不能直接套L2三角不等式。实数分数界需包住native dot及`float32(1-dot)`误差和ties，不能拿理论数值相等代替decision保真。visited/其他用途也要按源码逐项检查。

**最小反证。**若证明不了native interval及所有使用上下文，就停在理论层。若证明成功，未来必须含原版、bound版及同默认优化，核验所有实际决策/输出，再看full wall。密集旋转的query费用、随机界误拒概率与改变heap的实现不是这个版本。FEXIPRO、Tribase、Panorama已有直接组件前作；本项目的可审查差异是具体原生队列保真合同，不宣称新剪枝原理。

## C：三桶单目标

**冻结对象。**20000原训练GT1 slot、原归属、原GT10三入口、raw-IP桶内扫描；空桶fallback、去重、tie、布局必须在执行前固定。原slot覆盖33.765%/45.728%不够继承近似目标路由的行为，见[只读反证](bucket_feasibility.md)。今天不增加桶数/target数或重分桶。

**最低控制。**Default3、完整同次路由后rank1、原TargetBank1、CoarseTarget1。若要把收益归给语义分桶，需要同桶数/匹配访问预算的普通raw目标几何索引或固定置换归属控制；标准粗细检索已是前作。免费使用原TargetBank选择slot或GT作gate不合法。

**第一反证门。**新桶内实际选择和固定NSG完整响应；覆盖、最高IP或均匀M估计均不能补齐。再看全部费用的同L及冻结预算点比较。即便偶然修复Web R1，也不能消除Y/K100或对照更好的证据。当前HOLD，不生成新反馈。

## D：动态目标联合三入口

**可见输入。**同一次原GT10得到query相对rank1/2/3，加本query实际访问得到的t(q)。目标不能从已保存或GT响应免费读取；slot/ID重复按预定规则回退原Default3。保持canonical seed传入、≤3实际消耗、固定原主核。

**最低动作控制。**Default3={h1,h2,h3}、Default2={h1,h2}、TargetSingle={t}、Mixed={h1,h2,t}；wrapper未来需先验收两入口，当前E166评估器只验收1或3。必要投回H/置换target控制需同费用。必须取得各动作真实联合响应，不能把三个single标签相加。

**共享成本。**若t来自完整TargetBank路由，Mixed需两条路由：原GT10与TargetBank，原请求均值相加为Web约346.703、Y约411.957，尚未含控制/主搜索。若t来自三桶扫描，GT10可与保留h1/h2共享，新增请求是M或M_unique；不能重复收费，也不能省略它。两条实现不同，不能在反馈后任选表现较好的访问机制拼成方法。

**最强反证。**保留h1/h2不能保证原路径不丢：较高IP的target可诱发诱饵展开，淘汰尚未展开的低分桥；替掉h3也可能删有效路径。[历史审查](history_gap_audit.md)给出同三入口强连通环解析例。[安全前沿定理](search_effect_theory.md)只保护满足global rank条件的路径，不能为全体原路径背书。

**停止门。**访问成本前件没有支持时不先训练联合模型。若后续有授权且固定简单Mixed无法超过Default3/Default2/TargetSingle的完整共同质量/速度基线，就停止这一动作版本；不升级RL、MLP、双塔或加seed来替换同一失败机制。未覆盖的具体组合是直接在固定20K raw-target bank按本query访问t，再与原rank1/2联合；不能称首次query-specific H外混合，E116的固定slot→H外ID绑定也会随query选择slot而变化。差异落在更大的候选域、实际访问及联合动作；组合学习/目标监督/保两入口均有本地或跨领域前作。

## 共同执行边界

未来正式性能必须遵循根AGENTS：CPU15、实际单线程、串行完整wall、Recall@1/@100、K100的L≥100、原图/metric/核及冻结query角色。所有新增费用计入，输出校验与计数/计时一致性、救回/损伤、配对不确定性、重复与确认源均保留。负结果先排身份/GT-mask/消费入口/线程/计费等实验错误，并取得独立实现或审稿核验，再判断方法；不因一个弱负点永久封死不同机制，也不靠反馈调参延续已停止固定版本。

主目标仍是可靠完整Recall–QPS改进。理论命题、原论文理解、一次只读反证或实现parity均不能代替该目标。本文件的完成只表示后继工作已具体可审查。
