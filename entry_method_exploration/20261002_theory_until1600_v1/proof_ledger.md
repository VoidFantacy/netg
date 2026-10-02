# 命题、前件和未闭合问题

本轮的保证均为**明确合同下的解析结论**；没有运行数学程序、模拟或真实实验，没有测真实前件是否满足。交审状态与修正见[review_notes](review_notes.md)，原文位置见各分稿及[literature_manifest](literature_manifest.md)。本表不把未知前件标为已成立，不完成真实性能目标。

用户允许增加训练/离线准备投入；以下“费用”指需要比较的完整线上费用，非省训练门。本轮仍不开始训练/预处理/实验。

| 命题 | 最少关键合同 | 真正能推出什么 | 无法推出什么/当前缺口 |
|---|---|---|---|
| GT10归一化query矩闭式最优 | 固定H、a、unit画像；m_h≠0 | 精确最大化Σ p_hᵀm_h，画像唯一方向 | 不含有限响应、联合动作或完整时间；m=0无唯一方向 |
| 同有序GT10仍可最优动作相反 | 同固定合法图、预算、入口候选；不同query | 目标ID/顺序不普遍定义query不变的response/最优入口 | 不是当前真实图负实验；完整query可见下不是新Shannon信息缺失 |
| 当前画像可以帮助也可以失配 | 固定合法H、实际target归属、理想路由及指定响应图 | hard失配反例；hard/finite-T两hubsoft有非空正面moment模型 | 不证明真实选H器、分布、native路由或完整QPS；有限fit另需误差margin |
| vMF责任到方向 | 真posterior责任、共同κ/等π、连续vMF；或近似moment误差 | weighted query moment沿类中心；扰动/anchor/sample项有方向界 | 现行有限GT10责任不能精确等于非平凡连续vMF posterior；方向仍可能对齐 |
| 目标矩恢复全部advantage的维数 | 固定query不变target response表、任意target分布、线性decoder＋intercept | 给定ψ的行空间判据；可自由选ψ时最少rank(DΠ)维 | 不是一般convex calibration dimension；ordinal loss有rank2但一维校准；不给在线特征或迁移 |
| 三入口top-single失效 | 即使理想无竞争coverage | single全正确仍可因重复覆盖选错joint动作 | 真实beam还可能非单调；不能以单入口结果相加 |
| 可分响应下top-m正确 | 实际命中恰等于所选类GTK分区、费用相同 | 真a^(K)最大m个最优 | raw可达/soft权重不提供分区等式；a10与a1/a100另有失配 |
| 本地封闭C | 满L、完整row boundary、永久visited、潜在展开完整出口、全路径U≤β | 原继续搜索没有新接受ID离开C | 外部点仍可能被评分；取得C/上界/出口在线费用未知 |
| native保留＋任意GT损伤 | 对旧B中W证保留；正确威胁distinct ID计数/FIFO合同 | ΔRecall≥−|B\W|/K，无需GT/native同序 | 加新GT N后的粗界[n−|B\W|]/K因容量永不正；非空strict gain须另知旧nonhits Z或h_B/h_W，GT取得要收费 |
| 有序pool条件汇合 | 同q、有序live pool、共同mixed total preorder、FIFO与等值拒收、C封闭 | 原自然继续返回同有序ID | unordered集合不够；distancebits、visited、NDC及wall不因此相同 |
| 同入口容量展开前缀 | 完全相同ordered实际seeds、L≥seed数/K、永久visited、无padding/cap、自然best-pending/full-row、FIFO及等值拒收；(a)共同mixed比较序，或(b)同地址/路径/FP纯callback保持共有bits | 小L展开row及逻辑请求是大L前缀 | 增加seed不适用；比较序本身不保证bits；完整wall不随请求数自动单调 |
| 容量Recall非降 | 前缀合同＋小执行最终≥K个distinct合法返回ID；大执行GTK对nongt评分弱分离，旧tie先到 | hitcount非降 | native/官方GT不符时无保证；旧正确ID可被新正确ID替换；改变L不证明综合收益 |
| 整原拒收组省dot | 满L、每成员原路径native U≤β；同markvisited/原分组/后续纯callback/控制 | 逐ID与surviving bits保真，任何GT下Recall相同 | 部分组重分路径无保证；physical NDC/wall/FP异常不同；不得把未评分点当known-bits D |
| 已证拒收visited接口 | 整原组已先证保真；完整行/无在途、P有actual bits、永久V=D_phys∪D_cert | A/B/Qloc显式改为C\\V，安全路径仍成立而无需未评分bits | 不改原D定义；任意force-mark、一般响应汇合/虚拟scored历史或费用不继承 |
| ID/严格分数混合匹配 | K个distinct当前槽与旧返回一一匹配；self须保留，异ID严格margin；真GTK；统一ε覆盖旧B、当前C及全部未来可能入topK的原路径 | strict标签随topK替换传递，最终命中数非降，无须全当前ID保留 | 不是strict质量增益；各点不同ε/弱端点/平均误差无保证；统一真实界和旧B/前缀取得收费 |
| pivot/正交残差上界 | 可靠a/r/s/norm区间或真实正交P；原路径及bound运算误差包络 | 非空安全拒收条件；nested exact-P界非增；projection+norm metadata最坏界尖锐 | 已知平均角/误差不是sup界；basis文件不自动orthogonal；真实机会/在线净费用未知 |
| 随机拒收上界的输出risk | 固定原trace独立R；每原请求完整guard事件≤δ，含内部选择；首次差异前原callback耦合 | P_R(不同返回)≤min(1,Σδ)，E_R各K召回损伤≤该界 | 不是逐ID保真/召回非降；选中R和上线QPS无保证，随机默认须另设质量合同；ADSampling为直接前作 |
| 真实utility监督 | 固定实际joint action/full plan、signed幅度、默认差、正确成本单位 | Bayes条件均值排序或正确加权cost-sensitive决策 | teacher-ID/胜率/逐query归一化weights可丢幅度；较小有限MSE不保证当前动作更好 |
| 冻结策略类残差矩 | 同总体、Π选择mask下全部policy value残差≤ε；pathdependent完整T_π整体负责 | 预测chosen value误差≤ε、类内regret≤2ε（再加优化误差）；双坐标各需ε_H/ε_T与对应slack | 不是廉价算法；2ε regret不自动双提高，marginal calibration不够；有限fit/稀有组/费用另计 |
| 换测度策略价值 | Q_F≪P_F、合法ρ；正确weighted masks及coarsened条件response shift上界 | target误差≤ε_weight+ε_shift，类内regret≤2倍＋优化误差 | bounded ratio不能迁移signed取消；固定底图不保证压缩条件response不变 |
| 有限family确认界 | 冻结m个policy/default、独立同分布确认、真实残差已知有界 | 同时总体残差由经验残差＋range-dependent项控制 | 无新确认数据；single-thread不是IID，未知wall尾部不享无条件均值上界 |
| 带费用信息/回退 | Bellman需真实结果联合模型、全state/cache/合法action、prefix＋remaining suffix恰一次；EVPI另需pure-info及固定actions/utility/路径；凸/dual需共同固定响应与费用 | 各自合同下的Bellman、EVPI及两坐标可行域；回退付prefix、best-default完整费用门 | 免费target oracle不等实际访问计划；scalar混合不保证每域/K同时变好 |

## 最值得继续完善的两个对象

第一是**实际联合动作的相对Recall与完整时间，怎样由可便宜上线的表示保留**。可以增加合法离线真实响应监督和训练，但须说明新结构为何超出E04/E25/E36/E118/E133/E164已有对象；loss embedding、decision calibration和真实signed反馈本身都有直接前作。不同K/域与不同费用state不能合并成一份无条件安全标签。

第二是**通过完整事前metadata和数值包络，哪些原计算可在逐ID保真下省去**。原组拒收、原路由memo等只把问题具体化；在线bound/访问费用、覆盖率及共享最快默认仍未知。学习可以更重，但只学平均误差不能继承deterministic证书。球界、FINGER及缓存机制不是新的通用方向。

二者都尚无实现/实验GO。不用调整阈值、seed、候选数、深度或训练名称重开旧失败版本；没有真实完整wall/质量证据时，结论保持理论条件而非可靠综合提高。
