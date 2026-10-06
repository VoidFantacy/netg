# 原八方向最终报告模板（SOURCE ONLY，未填实际结果）

**TEMPLATE / UNRUN / 不可当作已完成报告。** 本文件只提供报告结构、原合同与待填字段；没有读取实际结果JSON、GT、模型、机器、运行态、账本或进程，没有重新计算指标或执行任务。所有 `【Root待填：…】` 都必须来自Root真实结果；未执行写“未执行/性能未知”，不填0、默认值、预测值或Source PASS代替实测。这里不新增审计、参数、确认门或权限。

## 1. 当前结论与范围

本轮原范围是5个单方法 **M2、M5、M4、C1-F2、B4**，以及3个联合 **J25、J45、JBP**。目标是可靠的Recall@1/@100与完整单线程QPS综合改善。[原协议](../protocol.md:3)允许按原明确终止门收口探索；阶段停止、完整流水线验证、性能改善和默认替换是四种不同结论。

【Root待填：截至时间；8方向实际探索覆盖；各固定版本阶段结论；完整原流水线已验证范围；可靠综合改善是否建立；当前默认与是否改变。】

当前报告不因预算停止、必要上界、编译/静态证明或局部支持点而宣称整方法普遍失败。无可靠替换证据时，原E99及Web GT10-soft-t1 / Yandex GT10-hard保持；最终默认判断由Root真实证据填写。

## 2. 八方向逐方法总表

下表的机制与范围来自原冻结合同；“阶段证据/结论”必须填当期事实，不能直接把旧阶段稿当最新结果。

| 方向 | 原机制与实现范围 | 原强简单控制及必要归因比较（全部保留） | Root当期证据、停止边界与性能结论 |
|---|---|---|---|
| M2 | 用完整保序几何/区间证明省略原scalar评分，原搜索状态与输出不变；完整Ω、compiler/check_all、实际helper与费用 | 原匹配默认及三档L；same-site矩形/norm/cone、完整55 endpoint-pair角带、认证CS/projection、单轴COORD/ICOORD、完整affine support hull；同cap各自准入/实际税，metadata-on关闭拒收控制 | 【Root待填：实际完成域、完整证明/原六阶段是否完成、成本STOP或已准性能、Recall/QPS或未知。不得把参考OFF/Jhat/cache成功写成线上失败。】 |
| M5 | 固定128KiB共享双K残差posting表，在原lower-L main正常输出后RESCORE/merge，最多24新候选；不改变原main | empty、真实C触发RESCORE-only、同slot allGTK频率、F_all、独立missing频率、geometry、global allGTK/missing、same-U tiny-HNSW、128KiB U′、Default3与同L0诊断；原16版本逐项引用 | 【Root待填：四SELECT及唯一有限CAL的已测范围、预锁质量/速度门、NO_CONFIRM范围、其它fresh null；不将有限窗口失败推广整个M5。】 |
| M4 | 完整响应证书复用；命中须有合法proof、membership、fork/merge/Q与实际计费 | 同candidate trace/response、同key球形域、同预算byte-exact/普通近似cache、directory-only强制miss、原最佳默认；17尺度与细化均按原机会，缺控制明确未完成 | 【Root待填：固定common20K/max32 RMS peer/17尺度族的必要门与scoped STOP；其它几何/G_global、完整程序与wall欠证。必要门0 hit不是整个M4 NO_GO。】 |
| C1-F2 | 原行末义务图编译；七图、全四图双K回放、原24 CAL→44风险位图，再原48模板/四点正式wall | 下文全部12曲线；原M0、事前Bcmp、共享默认前沿与F1/GLOBAL/普通剪枝；关闭类仍测真实fallback/guard税 | 【Root待填：FIT/lineage/replay/风险与formal结果分别列；Web旧FIT parent87/FITfalse不得改PASS；四点完整后判断主点/局部信号/版本费用提案。】 |
| B4 | 原20K/七计划/三tick教师，有限Π/depth3/17项lex目标的精确生产策略；branch-local seen/pool与score-only memo | 六固定split、2L及matched logical cap、BudgetOnly、PreSearchOnly、StartBudget12计划；原E99、166 span+batch4、同监督Default-Matched均获同等合法优化机会 | 【Root待填：教师/生产fit/modelseal/强控与CAL/confirm范围；预算STOP不等于已完成策略性能失败，合成一致/partial不能代生产模型。】 |
| J25 | 同lower-L M2保序省略后接同M5；保持响应R/候选来源/费用，主点原YK1 L100→128 | 同lower-L/同表D、M2、M5、J25四臂；L0/plus默认、M2全部强界+同post、拒收关闭、allGTK/global/geometry/tiny-index同merge、合法返回分数复用；完整原12因子/43控制不缩 | 【Root待填：same-R/same-U≤24固定定义版本质量债/理想救回界与条件STOP；actual联合是否执行。新U/全库不继承；不得把必要界写成actual程序STOP。】 |
| J45 | M4证书复用与M5普通融合/合法score reuse/cache/miss，保原22冻结模型、四full20K、16×42控制/9caller/完整额外E≤16MiB | D、M4、M5、J45四臂；朴素重复评分串接、同目录强制miss、同candidate trace证书、byte-exact/cache+post、普通合法fusion/reuse；朴素串接不是最强基线 | 【Root待填：原879/986各自前件、缺失阶段、预算依赖停止/原workflow HOLD/性能未知。原冻结TRAINING任务不自动重分类；确定性Source也不证明理论上必须新增拟合。】 |
| JBP | B4+M5原FIT0→FIT1/full40K七计划missing→共享A→真实plan+A→同Π的π1 refit，不能以π0或工程BUILD替代 | 同FIT1/Π重拟empty A，π0+A/π1+A，π0-only residual及allGTK/frequency/global/geometry/tiny-index表后同样refit；split/BudgetOnly/PreSearchOnly/StartBudget/2L/default+A；NoMemo、真实C RESCORE-only；固定π1/A归因四臂 | 【Root待填：有限fixture/archive/compiler/loader工程实际范围与主学习链预算阻断；性能未知。工具事实不解除共享A/π1学习前件，不授原TU/fullsupport或全方法NO_GO。】 |

全部“未完成”控制都写明证据缺口，不能当作候选已击败；这些名称是原合同要求，不是新增实验清单。跨caller、不同可见信息或资源的绝对QPS不直接拼接。联合四臂交互只按同一配对轮wall计算，不对四个中位数相减或相加QPS比；普通fusion/reuse解释收益时保留事实并收缩创新归因。

## 3. 两数据集、两K、角色和结果字段

| 原工作点 | 维度/底库规模（冻结Source声明） | 默认L0 / lower-L / Lplus | C1及B4/JBP原L |
|---|---:|---:|---:|
| Web Recall@1 | d512 / N2,505,000 | 1000 / 800 / 1200 | 1000 |
| Web Recall@100 | d512 / N2,505,000 | 1250 / 1000 / 1500 | 1250 |
| Yandex Recall@1 | d200 / N10,000,000 | 128 / 100 / 156 | 128 |
| Yandex Recall@100 | d200 / N10,000,000 | 256 / 200 / 312 | 256 |

原M5/J25/J45部署lower-L，L0诊断不能替代lower-L产物。一般/联合原primary为YK1；C1专项唯一primary为WebK100/L1250，其它三点仅局部支持。比较身份不能在结果后改。

每个已测方向/工作点填写：`dataset、role、n、K、L、冻结候选/参照及控制身份、Recall@K、rescue/damage/净成员差、质量描述区间、逐轮完整wall与QPS、median/pooled QPS、逐轮配对速度比、计费与来源`。未测格写“未测”，不从K100首项推K1、插值或将构建费用转成QPS。

角色沿原冻结：FIT0/discovery20K、SELECT4096历史曝光、FIT1预锁20K；C1 fit16384、CAL32768，其它原方法/联合CAL4096；confirm-A/B各4096。Source-row/字节不重叠不自动保证语义独立或IID。基础正式五轮及联合确认七轮、原caller/轮转与释放边界保持；C1原Qconfirm另依专项五轮×8192合同，不混为联合七轮。

## 4. M5已保存80行：引用完整表，不复制未经本模板复核的数字

完整引用[原M5全部80行报告](../report_metrics_M5_saved_all80_20261006_v1.md)，保留四SELECT点×16版本和唯一WebK1有限CAL×16版本。这里不重算、不复制数值，也不从控制中事后选赢家。

| M5窗口 | Root最终报告应给出的信息 |
|---|---|
| 四SELECT工作点 | 【Root待填：原主residual_joint@Lminus对default_main@L0的四点摘要，引用80行表；全部强控/16版本保留；历史曝光与描述区间限制。】 |
| 唯一WebK1有限CAL | 【Root待填：真实Recall/wall、rescue/damage、原预锁EB质量下界/quality screen/speed screen、最终有限NO_CONFIRM状态与证据。】 |
| 其余三个fresh点及确认 | 【Root待填：事前固定范围/停止后的null与确认未执行；不能追加点、阈值、U、seed或重新学习救门。】 |
| 机制与可靠性 | 【Root待填：复杂主候选是否胜最强简单频率控制；提升/取舍/不确定范围；不赋IID总体保证或可靠默认替换。】 |

M5的预锁EB门与C1 CP风险/实用门不是同一门。成员数不是查询数，K100 rescue/damage不能按query数解释；配对速度比中位数不等于两个QPS中位数之比。

## 5. C1四组正式结果与全部12曲线

CAL32768与原48模板、两K、五固定左旋、round0 warm128、独立audit、全部强控和disabled类真实开销不变。原24→44使用epsilon=.001、delta=.05/44、同class两K AND；F2_all_closed=true时按原规则停止，不开wall/confirm。风险准入不证明Recall非劣、速度或默认收益。

| 原C1组 | 角色/n/K/L | 正式normal与audit/compact/merge/evaluation范围 | Root结果段 |
|---|---|---|---|
| WebK1（支持点） | cal/32768/1/1000 | 12曲线×5normal；12独立audit/compact；merge；M0与预锁Bcmp评价 | 【Root待填：完整12曲线、配对质量/速度、有限支持点结论与结果出处；不推整个C1 NO_GO。】 |
| WebK100（唯一primary） | cal/32768/100/1250 | 同完整流程；首轮/部分成功不当完整质量或五轮结果 | 【Root待填：完成范围、主点实用门、强控与实际前沿；未完成时明确未完成。】 |
| YK1（支持点） | cal/32768/1/128 | 同完整流程 | 【Root待填：完整结果及局部经验结论。】 |
| YK100（支持点） | cal/32768/100/256 | 同完整流程 | 【Root待填：完整结果及局部经验结论。】 |

下表在**每个工作点完整展开一份**；以Root真实结果填满，不能只放F2和默认。原12 methods包含anchor自比，不强行删除成11；同一输出对M0/Bcmp的两份评价不是两个独立实验。

| 原曲线标签（各K对应冻结label/dir） | 定义/比较限制 | Root Recall/质量字段 | Root五轮完整速度字段 |
|---|---|---|---|
| M0 | 原冻结风险比较核/默认图 | 【Root待填】 | 【Root待填】 |
| SHAM | 原SHAM控制，不能删除或免计开销 | 【Root待填】 | 【Root待填】 |
| F2 | 主行末义务收紧保护版本 | 【Root待填】 | 【Root待填】 |
| F1 | 原未收紧保护版本/关键机制控制 | 【Root待填】 | 【Root待填】 |
| GLOBAL | 不分组的全局控制 | 【Root待填】 | 【Root待填】 |
| random | 原随机剪枝控制，不改seed | 【Root待填】 | 【Root待填】 |
| first-score | 原first-score剪枝控制 | 【Root待填】 | 【Root待填】 |
| mean-native | 原mean-native剪枝控制 | 【Root待填】 | 【Root待填】 |
| strong166 | 原span-batch4强参照；Bcmp取事前冻结身份 | 【Root待填】 | 【Root待填】 |
| DefaultMatched | 同监督M8/匹配默认；与strong166的原alias共享一证据身份 | 【Root待填】 | 【Root待填】 |
| strong166_fused | 额外强fused曲线；caller差异不归因C1机制 | 【Root待填】 | 【Root待填】 |
| A0 | 原共享默认实现前沿控制；保全部实际冻结点 | 【Root待填】 | 【Root待填】 |

质量字段：`Recall@K、anchor_recall、delta、rescue、damage、query wins/losses、paired bootstrap描述区间`。速度字段：`wall_seconds[5]、qps_each[5]、median/pooled_qps、paired_speed_ratio_each[5]及中位/pooled比、each_round_gt_one`；`pooled_qps = n×repeats / sum(wall_seconds)`。完整计时包含分配/初始化、route/main/post、guard/cache/membership、失败/fallback、helper、输出和释放；加载/启动/完整绑定及独立audit另列，不从查询wall扣真实查询工作。

C1原P937/P938专项实用门对**事前Bcmp**二择一：pooled QPS≥1.03×Bcmp且Recall均值不低；或Recall净增≥.0025且QPS不低。唯一WebK100 primary未过则主假设未支持；其它点过只记局部经验改善，无点过则按原规定结束本版费用提案。质量区间跨0或五轮速度跨1记不确定候选。一升一降是取舍；A0/A1/A2/M8任何实际默认点支配C1时，即使对Bcmp过门也不声称新增前沿。不插值或事后换primary、参照、控制、参数。

【Root待填：四点相对M0与Bcmp完整比较；F1/GLOBAL/普通剪枝是否解释F2信号；全部共享默认实际前沿；主点/局部/不确定/版本停止的精确结论。】

通用协议预锁median速度比≥1.03、每轮>1及该K质量要求按其原适用版本分别报告；不能把median冒充pooled，也不把它拼成C1专项合同未写的新AND门。当前CAL evaluator冻结bootstrap20000/seed20261003172；原Qconfirm P937为10000/seed2026100302，全部描述性。两角色分别列其实际冻结身份，披露原DOCX/后继CAL差异，不据结果修改旧CAL配置。确认未实际准入/运行就写未准入/未运行，CAL不得冒Qconfirm。

## 6. 成本、训练超限与失败保留

历史阶段报告已记录两dataset跨全部方法TRAIN超过7200秒；本模板不读取账本聚合。Root须以真实接受记录填写精确整数ns及统计时点，保留GENESIS历史，不能把新增TRAIN0写成历史预算满足。禁止新fit/refit/shared-A/学习型grid或反馈cache学习；不reset/refund、拆key、换dataset或将学习改名BUILD/VALIDATION。原冻结计为TRAINING的geometry/proof任务也不能自动重分类，确定性Source不等于原成功产物已存在。

| 成本项 | Root精确填写 | 报告边界 |
|---|---|---|
| Web / Y跨方法累计TRAIN | 【Root待填：整数ns、秒、限额及超额；来源/时点】 | 已超限历史永久保留；方法旧key余额不重开学习 |
| 各方法/联合TRAIN、LABEL、BUILD、VALIDATION、ADMIN | 【Root待填：已执行实际scope及分类总额，未知写未知】 | 不混成查询QPS；不凭Source推费用 |
| C1四组normal / audit / compact / merge / M0+Bcmp评价 | 【Root待填：逐组/分类费用与原组计费总额】 | normal查询clock与其whole计费/审计/存储/评价外墙分列 |
| 旧失败与工程修正 | 【Root待填：失败stage、exit/原因、charged fee/outer/cleanup；保留原件】 | 超时/日志容量/迁卷/metadata-cap等工程故障不作方法NO_GO；修正不回写旧失败 |
| pre-BEGIN失败与cleanup | 【Root待填：未发生BEGIN/child的事实及外墙，或实际BEGIN–END费用】 | 未入账窗口单列，不伪造账本费用；清理/reap成本不丢 |
| 额外resident、RSS、bytes与资源限制 | 【Root待填：实际测量范围与未覆盖区间】 | 单次/端点RSS不证明峰值；请求bytes/sizeof不等于uniform fullE |

方法间只能比较原匹配caller与同等合法优化机会下的真实工作点，不把历史工程成本、另测callback价格或组件QPS相加当收益。原无时限条款已被用户后来的dataset累计训练限制覆盖；科学范围、角色和阈值仍保留。

## 7. 可靠性、确认和默认判断

SELECT是历史曝光开发证据；冻结CAL/确认来自同公共源的不同窗口，Source-row/字节去重不自动证明IID。paired bootstrap、rescue/damage与固定窗口差异描述其实际样本，不赋总体保证。五轮速度是同一角色的重复计时，不是五份独立质量样本；双参照、自比、alias不增加独立证据数。经验Bernstein/CP各自只在原前件与声明族内使用，44格CP不传递Recall–QPS或多点/多控显著性。

【Root待填：预锁CAL质量/风险及速度结果；按各原合同是否停止/保留不确定候选/允许提出确认；确认A/B实际是否获准及执行、原五/七轮与角色参数、全部不利端点/控制；可靠性与可迁移性限制。】

本模板不启动确认，不新增held-out授权，不要求新的额外质量脚本或全平台证明。强控制未完成就是缺口；不能从审计/Source身份或全域候选推性能。各原实际前件已接受的事实按其窄scope引用，避免重复执行已完成工程步骤或把新Source版本当新方法。

【Root待填最终中文结论：8方向各为何停止或继续；哪一固定版本/工作点有局部信号；哪些完整主张未被支持/性能未知；是否建立可靠Recall@1/@100–QPS综合改善、是否改变默认；完整原范围及未执行阶段如实保留。不得把“7阶段停止”写成“7个可靠性能成功”，不得把“完整流水线未完”写成“未探索”。】

## 8. 证据索引与历史正文

最终当前报告应以当期总表、M5完整引用及C1四点实测为正文，原report.md第12行以后及原阶段稿整体保留为带日期的历史快照，并明确链接。旧“当前约束/CAL未执行/编图待执行”不得未经日期标签成为当期结论；如该段仍被保护，则不改旧正文，以另存完整当前报告作明确顶部入口。历史失败、原协议、冻结配置和旧seal不覆盖。

Root逐段绑定实际配置、输出、完整费用与原独立核验引用；本模板只引用Source/文字，不预造结果、receipt hash或运行资格。

原依据：[协议](../protocol.md)、[冻结配置](../config.locked.json)、[原八方向阶段稿](original8_progress_report_20261006_v1.md)、[M5原80行](../report_metrics_M5_saved_all80_20261006_v1.md)。控制合同：M2 first_artifact165–169；M4 proposal90；M5 comparison74；B4 complete_method337–343；joint_frozen_validation53–71；C1原P936–P938。最终数值及当前状态由Root另填，不从这些Source推实际完成。

作者关系：模板作者参与原C1 Python consumer/wall及部分有限工程Source；这是报告结构与原合同整理，不是独立重算自己的实现或Root科学/机器结果。本模板STOP_EDIT，不授actual执行、性能、确认或默认资格。

### 本模板明确安全输入身份（仅Source与历史报告文字）

以下完整SHA与Python整数stat5在模板生成前后闭合；不跟随文件中的任何数据/机器/运行态/实际产物引用。详细原合同只定点用于机制/控制/角色字段，不声称本次重做完整科学审计。

- /data/netg/ACSG/entry_method_exploration/20261003_all_methods_experiments_v1/protocol.md；SHA `000d48a96ef122f263148d128f3d9c5b3803230ca1526125192b17c9a4b102d7`；stat5 before=after `{"device":66309,"inode":1200686,"bytes":3866,"mtime_ns":1790997924023721451,"mode":33188}`。
- /data/netg/ACSG/entry_method_exploration/20261003_all_methods_experiments_v1/config.locked.json；SHA `5f1df2e43cebd519538989813839a83d8bf5c1c288808732f98315d4b9661bf1`；stat5 before=after `{"device":66309,"inode":1207818,"bytes":11350,"mtime_ns":1790997924051721573,"mode":33188}`。
- /data/netg/ACSG/entry_method_exploration/20261003_all_methods_experiments_v1/reviews/original8_progress_report_20261006_v1.md；SHA `9c2224476b688d9b23bbcff523deec6e3c5a74f051609f600c2ec0bdbfe4afe9`；stat5 before=after `{"device":66309,"inode":1211847,"bytes":20829,"mtime_ns":1791241874838016791,"mode":33188}`。
- /data/netg/ACSG/entry_method_exploration/20261003_all_methods_experiments_v1/c1/wall_jobs.py；SHA `be70f03b3309cb7fc9c0036c63d06bfba83ce823a91ba7dac362b11199e5329d`；stat5 before=after `{"device":66309,"inode":1202506,"bytes":5421,"mtime_ns":1791004886030326998,"mode":33188}`。
- /data/netg/ACSG/entry_method_exploration/20261003_all_methods_experiments_v1/c1/wall_jobs_bcmp_v1.py；SHA `96ff46b595729be8c26786af727b74343757edba91b2f27555b1ca83acb3011c`；stat5 before=after `{"device":66309,"inode":1209767,"bytes":6541,"mtime_ns":1791009746683718472,"mode":33188}`。
- /data/netg/ACSG/entry_method_exploration/20261002_overnight_algorithm_audit_v1/m2_first_artifact_contract.md；SHA `182fd5ce3d3dc0eac84715dd1a167b866036cf5a4108d6a63be72a501789776d`；stat5 before=after `{"device":66305,"inode":8676762,"bytes":22027,"mtime_ns":1790964757589206908,"mode":33188}`。
- /data/netg/ACSG/entry_method_exploration/20261002_overnight_algorithm_audit_v1/m4_region_proposal_and_admission.md；SHA `8d2174f8752f94d80217ddae39789474302c9ef129f53568bd86fa9b7c62f52d`；stat5 before=after `{"device":66305,"inode":8676729,"bytes":14996,"mtime_ns":1790984734297897314,"mode":33188}`。
- /data/netg/ACSG/entry_method_exploration/20261002_overnight_algorithm_audit_v1/m5_comparison_selection_contract.md；SHA `f5dde63f4a1a6a025a2cdd977d69e0c9450666b7014792a2653530eab329d0f7`；stat5 before=after `{"device":66305,"inode":8676769,"bytes":18951,"mtime_ns":1790965535088638146,"mode":33188}`。
- /data/netg/ACSG/entry_method_exploration/20261002_overnight_algorithm_audit_v1/docx_b4_complete_method.md；SHA `05741255e571e17788cd5274612d261d24c7a4c528d901df9a57fd20b240a8b7`；stat5 before=after `{"device":66305,"inode":8676821,"bytes":39768,"mtime_ns":1790985412204833266,"mode":33188}`。
- /data/netg/ACSG/entry_method_exploration/20261002_overnight_algorithm_audit_v1/joint_frozen_validation.md；SHA `cf6fde1a62d33cb4f756bfe190a4441be1e6fea1db8493f9242e2f6a53d3c4d8`；stat5 before=after `{"device":66305,"inode":8676827,"bytes":13578,"mtime_ns":1790983638773152701,"mode":33188}`。
- /data/netg/ACSG/entry_method_exploration/20261002_overnight_algorithm_audit_v1/joint_policy_posting_two_pass.md；SHA `0522229421dc42ed0d1604213bd038f60f6a47717bb5b77285a91fb124dacc98`；stat5 before=after `{"device":66305,"inode":8676822,"bytes":21093,"mtime_ns":1790983638769152684,"mode":33188}`。
- /data/netg/ACSG/entry_method_exploration/20261002_overnight_algorithm_audit_v1/docx_c1_graph_comparison.md；SHA `937d74f4d28c96a06f516c3a3109d6ecbc589fa8bd9721206488dfe5b898476c`；stat5 before=after `{"device":66305,"inode":8676823,"bytes":79867,"mtime_ns":1790983426452225203,"mode":33188}`。
- /data/netg/ACSG/entry_method_exploration/20261002_overnight_algorithm_audit_v1/docx_review_source.md；SHA `4f3894c1975524ca08011f4c9515a337cac1c96223ce6af9674fa28bd732ba19`；stat5 before=after `{"device":66305,"inode":8676817,"bytes":324775,"mtime_ns":1790975356613294274,"mode":33188}`。
