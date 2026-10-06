# 原八方法阶段报告：实际证据、停止边界与未完成要求

**阶段报告 V1；没有可靠新默认替换，原八方向完整探索仍未完成。** 当前默认仍为E99，Web使用GT10-soft-t1，Yandex使用GT10-hard。最终目标是可靠的Recall@1、Recall@100与完整单线程端到端QPS综合改进，构建提速、几何证明、训练误差或局部Recall信号都不能替代这个目标。

本阶段报告来自[冻结草案](original8_plain_report_DRAFT_20261006_v1.md)，Root已全文阅读，并对五点主候选/默认表格及CAL五轮时长与原保存JSON逐字段核对；这不等于重测或独立GT/机器审计。

本稿依据[已封要求→证据矩阵](original8_current_completion_requirements_report_audit_20261006_v2.json)、[原M5全部80行](../report_metrics_M5_saved_all80_20261006_v1.md)及[V75交接](../next_dialog_handoff_20261006_v75.md)。V75保存时点为2026-10-06 06:57:54（上海）；下述最新实际事实归属Root已保存接受记录，本稿没有重新读取运行态、账本、模型、GT、ELF或科学产物。矩阵以V74为基准，其中“被动观察未运行”由V75的真实成功更新；旧失败、旧报告和原费用全部保留。

目前最强的性能证据来自M5：四点SELECT的全部16版本，以及唯一WebK1 CAL的全部16版本，均有原五轮完整wall和Recall。WebK1有局部质量/速度信号，但预锁CAL质量门未过，按原规则NO_CONFIRM；其余三个fresh点是事前停止后的null，不能补测救门。C1已经完成原24项CAL/packet及44格风险准入，且新镜像被动观察成功；这还没有产生正式48模板的Recall–QPS结果。其他方向有成本停止、必要门停止或工程前件进度，完整原范围性能仍缺。

**原要求与证据的对应关系**

| 原要求 | 已有证据 | 仍缺的证据或必须保留的限制 |
|---|---|---|
| 两数据集、两K的可靠Recall–QPS综合改善 | M5原四SELECT及唯一WebK1 CAL；默认未改 | 无可靠默认替换；其他七方向没有完整原范围正式Recall@1/@100+QPS结果 |
| 完整T1 normal-batch计时，保原五轮/联合七轮 | M5保存完整五wall、配对QPS及全部控制 | 不能把TRAIN/BUILD/CAL外墙、probe或必要上界填成QPS；C1正式wall仍未运行 |
| 同监督与全部预锁强控制 | M5全部80行保留；原C1 M0/Bcmp已冻结 | M5复杂主候选的信息优势未建立；B4/JBP生产学习和同监督链未完成，J25/J45完整联合控制未测 |
| 原CAL/confirm质量门、不反馈选参 | M5有限CAL质量失败→NO_CONFIRM；C1原24→44已真实计算 | 不能改阈值、追加样本/seed或开confirm；风险门通过不等于性能收益 |
| 当前image、同child、FP/布局/容量与全生命周期合法 | C1取得新image完整词与静态候选；原各自有限工程审保留 | 新formal Faiss字段/sign/caller语义、五项绑定和实际完整own缺，旧地址/Source PASS不能转授 |
| 每dataset跨全部方法累计TRAIN≤7200秒 | 历史费用完整保留，明确超额并禁止新增TRAIN | 过去超額事实无法由reset/refund或分类改名消除；M2/B4/JBP未完成的学习主链不能继续 |
| 负结果先审工程与范围 | M4/J25/J45有限必要STOP、M5有限NO_CONFIRM、M2/B4成本STOP、C1失败原因分别保留 | 不把工程超时/日志容量/预算STOP或局部必要门外推成全算法NO_GO |

**M5：冻结残差posting补输出的实测结果**

M5用冻结输出补全表给较小搜索预算Lminus的结果补充候选，再与原L0默认方法比较；所有简单频率、joint、global、同U、tiny、几何及诊断控制都保留，不能在看到结果后换主候选。下面只列原主候选`residual_joint@Lminus`与`default_main@L0`，不是从16版本选赢家。每行n=4096；K=1列对应Recall@1，K=100列对应Recall@100。

| 数据/角色/指标 | Lminus→L0 | 默认Recall% / QPS | 主候选Recall% / QPS | ΔRecall pp | 五轮配对QPS比中位 | rescue / damage成员 | 描述95% Δpp |
|---|---:|---:|---:|---:|---:|---:|---|
| Web SELECT @1 | 800→1000 | 90.454102 / 315.446280 | 90.600586 / 390.916050 | +0.146484 | 1.241638 | 55 / 49 | [-0.341797, +0.634766] |
| Web SELECT @100 | 1000→1250 | 90.581543 / 253.031880 | 89.573242 / 311.864153 | -1.008301 | 1.230143 | 1715 / 5845 | [-1.105225, -0.919189] |
| Yandex SELECT @1 | 100→128 | 90.625000 / 1995.753173 | 88.867188 / 2361.232156 | -1.757812 | 1.199034 | 9 / 81 | [-2.221680, -1.318359] |
| Yandex SELECT @100 | 200→256 | 91.044434 / 1074.529875 | 88.804443 / 1299.515098 | -2.239990 | 1.192487 | 86 / 9261 | [-2.404053, -2.090332] |
| Web CAL @1 | 800→1000 | 91.137695 / 308.164659 | 91.381836 / 382.722732 | +0.244141 | 1.237767 | 54 / 44 | [-0.219727, +0.708008] |

数值逐字段复制[全部80行报告](../report_metrics_M5_saved_all80_20261006_v1.md)，未重算GT、bootstrap或EB。QPS是原完整五轮的中位数，配对比是每轮比值的中位数，不能从两个QPS中位数相除替代。rescue/damage是成员数，K100的计数不是查询数。描述区间不是预锁EB门，也不是IID总体保证。

WebK1 SELECT主候选质量增量的描述区间跨零；简单`missing_frequency`控制达到同样90.600586% Recall、392.316306 QPS，主候选为390.916050 QPS，因此复杂机制相对简单控制的信息优势没有建立。其他三个SELECT点虽提速，质量均下降，不能把质量/速度分别改善拼成综合成功。

唯一fresh CAL窗口是WebK1：精确Recall@1分别0.913818359375与默认0.911376953125，救回54/损伤44/净10。原五wall秒数如下，所有初始化、normal主体和释放按原计时口径保留：

- residual_joint：10.699527338、10.702264738、10.738367886、10.715959938、10.698057351。
- default_main：13.378528341、13.203246188、13.291595523、13.294968866、13.211842903。

原EB质量下界为−0.011042298475154892，quality screen=false、speed screen=true，结论为**有限样本CAL_SCREEN_NOT_MET / NO_CONFIRM**。这一冻结窗口的执行和停止规则已闭合；不能开confirm、补另外三点CAL、调阈值或重新学习补救。CAL Recall@100=null；其他三个fresh点Recall/QPS=null。SELECT已曝光，CAL来自同公共源的预锁窗口，没有语义独立/IID总体保证。M5此版本的局部信号不构成可靠默认替换，也不证明整个M5族或全部控制在总体上有害。

**M2：用保序几何证明省略评分**

M2的原目标是用完整几何/区间证明跳过不影响搜索比较与响应的评分，把节省落实到原normal搜索wall；证明、独立检查器和真实helper费用是必要前提。四点完整20K discovery Ω与两full-N缓存/原逐ID工程检查已完成。报告记录四Ω共32,796,290 sites；Web N=2,505,000/d=512、Y N=10,000,000/d=200，缓存96B/ID、非抽样。

Web原累计TRAIN7200.315461338秒、Y7200.343677759秒，均成本STOP。完整geometry/proof/compiler/check_all及原六阶段成功终态未完成，没有完整合格证明可直接送原线上性能入口。原参考价格、Jhat/参考OFF或缓存成功不是实际helper费用/Recall–QPS失败证据。

当前应报告**成本STOP，完整方法性能未知**，保留cache/discovery与所有partial/费用。新增学习或续同proof/geometry学习尝试已被预算关闭；不能改名VALIDATION。若没有已完整接受的原artifact，本稿不建议启动原性能任务，也不把整个M2判算法NO_GO。

**M4：固定共同响应证书族的必要门停止**

M4尝试复用响应证书，只有可证明安全命中时才减少重复工作。已实测的固定common20K/max32 RMS peers/17嵌套尺度族，在两dataset各4096 SELECT、各81,920,000跨key配对上，possible=0、UNKNOWN=0。原Web上界作业389.9241726398468秒，Y157.32236099243164秒；合计547.2465336322784秒是必要门费用，不是QPS。

这足以停止**该固定共同族的keyed/keyfree/proactive SELECT safe-hit版本**，无需重复seed/尺度或为这条必要门再跑整轮在线实验。它不能排除更强G_global、其他几何或整个M4。原G_global完整positive proof、独立checker/native/caller、16MiB及原强控制completewall尚缺；已有checker Source不是完整proof。

下一步以该族scoped STOP收口报告。若以后有真实完整且非学习的proof，才能另行准备原checker验证；当前五份基准报告没有建立这样的ready入口，也没有成本依据承诺其可短时完成。

**C1-F2：图编译、风险准入与正式计时之间的缺口**

C1把原双K见证约束编译到候选图与对照，并用原回放检查行为，再由CAL风险门决定可启用的类。Y七图/full4链已有完整实际证据；Web通过既存14组件/fullG0、composed生成lineage/受托custody以及原全四图回放接续。Web旧FIT parent87/FITfalse仍保留，不能把后续验证写成FIT成功；Y自身TRAIN933.099832124秒没有单独超2小时。

原Web12+Y12全部24项CAL及五流packet、exact44 CP(.001、.05/44、同class两K AND)已真实完成，不重跑。Web各class关闭；Y F2仅class0启用，F2_all_closed=false，因此原整体门没有要求全F2 STOP。这个bitmap只说明风险准入范围，不能当Recall@1/@100或QPS；Web关闭类的真实fallback/guard开销仍须按原模板计量，不能填默认值免测。

正式镜像BUILD4的编译器、nm、objdump均exit0，整步因保存objdump日志43,927,949B超过原32MiB而失败。原费用和失败不回改。后续一次新付费只读观察成功，在不重编、不执行image主程序的条件下取得own_v3完整身份、128词表、三完整vtable/RTTI、九scalar别名和94函数记录。一个E8直接caller候选不等于所有caller完整性，`caller_set_completeness_accepted=false`。

仍缺的是当前Faiss storage/index/raw布局、负号实际指令引用及语义、完整caller来源，以及Python V5的五项当前image绑定、同child startup/factory/FP/容量和全生命周期own资格。128词POD表不能推出Faiss私有布局；机器完整词不能自动证明ABI、对象或科学语义；旧CAL地址/FP不转授新formal image。

Source设计保持startup在原warm和normal batch Clock之前；factory使用immediate-post-return、在VT/set_query/route/score之前的有界检查，费用留在原Clock里。它不冒称旧before-RET观察，completion Clock96不移动。实际资格闭合后，才可执行原48模板、两K、全部强控制、原warm128与五轮完整轮转，再按原门决定确认。**当前原完整正式Recall/QPS仍缺，不能用CAL或工程外墙补齐。**

**B4：有限预算精确策略拟合没有完成生产模型**

B4原路线用完整20K、七计划和三tick教师，在有限Π/depth3、17项lex目标下得到精确生产策略，再与同监督强控制比较。原first128/c-B冻结、部分原教师和固定T1/T8合成一致工程验证已完成；Y tasks0–10完成，task11成本STOP，12–35未跑。合成一致或部分teacher不等于生产模型合格。

Web累计TRAIN7200.460543358秒、Y7200.506343722秒。完整生产fit/modelseal、原强控制、两K CAL/confirm和完整五wall未完成。当前没有已封完整生产策略可直接验证，新fit/refit/grid-presearch学习/shared-A都禁止，不能删17目标/动作或缩20K。

因此B4结论是**生产拟合成本STOP，策略性能未知**；不是一个完成策略已测Recall/QPS失败。下一步整理完整成本、已做教师/工程域和未完成模型范围，不能用另一个简化模型代替原目标。

**J25：M2+M5的同R/同U定义版本受到质量必要界限制**

J25将M2评分省略与M5补输出联动，原要求lower搜索、candidate-source、响应R和所有控制/费用逐字保持。对primary YK1 SELECT4096、L100→128，原质量债为83；若main有效ID仍为同R、补全仅来自固定同U且最多24，理想零损伤full-U救回上限14，净差最多−69；原A上限11，净最多−72。

这是可报告的**固定same-R/same-U≤24定义版本scoped STOP**，没有必要先实现一个无机会补债的joint程序来证明这条不等式。它不涵盖新U、全库/tiny/global控制，也不等于actual_J25_program_STOP或整个J25算法NO_GO。

原四lower全Ω/geometry/full48/check_all、20K×3route/currentproviders、12因子和43强控制、own机器及完整联合wall仍缺。原M2full6/all4硬链不因C1的composed验证而取消，L0产物不能改名lower。预算禁止新学习补足geometry；当前没有已准入可立即产生完整联合Recall/QPS的短任务。

**J45：冻结模型的普通融合仍是非学习路线，但完整E和全控制欠证**

J45尝试将M4证书复用与M5补输出/普通融合共享一次评分，并处理合法cache/miss调用。原22冻结模型的ordinary fusion/residual_joint路线不是JBP共享-A重新学习，不能仅因TRAINban就判整条J45不可能。

已保存旧160普通BUILD/n0、四full20K q/S/R/RowID provenance和有限p0/p20000 typed端点；共同证书族SELECT命中机会有scoped STOP。新mapped180的ownership/lifecycle/lookup Source已有，但这些事实不能让旧160资格转授新image或全42控制。

核心缺口是uniform额外E≤16MiB的完整证明和真实绑定：allocator retention、foreign/libc/loader、stack/TLS、parent/FD均要计，不能只报请求bytes、端点RSS或sizeof。还缺新image/ABI/allpath、9caller、首次唯一freeze、JOIN_R/NUM-BSIM，以及四full20K、16×42控制和原五/七轮完整wall。原879/986硬门仍保留，不能自动跳过。

下一步可准备冻结ordinaryfusion的必要非学习工程、当前image和全E producer，但现报告没有ready的完整性能入口。不要重跑已做的四20Kprovenance/有限typed或借Source PASS补全E；新模型/refit/cache反馈选择仍禁止。J45当前是有限共同族STOP、完整普通融合HOLD，尚无原完整Recall–QPS实测。

**JBP：工具前件有实际进展，原共享A重拟主实验被训练禁令阻断**

JBP原B4+M5联合链是FIT0→FIT1七missing plans/full40K两K采集→共享A→真实plan+A→同Π的π1 refit，再比较同机会五强控制与原SELECT/CAL/confirm/完整wall。这条主产品科学路线实需新增学习，不能以π0、单独B4或一项工程BUILD代替。

工具身份、精确官方archive关联、actual137 vendor Source以及有限loader DISCOVERY/REPLAY已有Root工程事实。两loader charged BUILD10.156322883秒仅是这两个窗口，不是JBP累计全部BUILD，也不是QPS。原TU90、实际compiler trace/grammar/fullsupport、own prefix/capture与完整E/σ/Γ仍缺。

最近的非学习工程前沿是既有canonical dash/true两round fixture，须按原合同有限tracer/runtime/kernel/filesystem前件和四gap实际处置，再考虑同ENV/cwd/TMPDIR到原TU的有限转移。不能把loader事实改名tracer接受，不能新增通用大证明门；即使fixture成功，也不会解除shared-A/π1必须学习的主线阻断。

当前应明确**工程前件部分完成、主学习实验未完成且禁止新TRAIN，完整性能未知**，不能写整个JBP算法NO_GO或八方法实验已完成。

**成本与预算：已经超过训练上限，后续不能再学习**

用户当前要求每dataset跨全部方法累计TRAIN≤7200秒。保存Root历史合计Web21,724.972836322秒（21,724,972,836,322ns）、Y15,589.205719895秒（15,589,205,719,895ns），都已超过上限。这是历史不满足预算的事实，不因停止后续训练而变成已满足；新TRAIN为禁止，包括fit/refit/shared-A学习、学习型grid/presearch，以及将学习改名BUILD/VALIDATION。不得reset/refund、拆key或换dataset。C1:Y自身933.099832124秒没有单独超2小时，但Y跨方法总额已超额。

| 成本窗口 | 已保存费用 | 解释与限制 |
|---|---:|---|
| M2 Web / Y累计TRAIN | 7200.315461338 / 7200.343677759秒 | 成本STOP；完整证明/性能缺 |
| B4 Web / Y累计TRAIN | 7200.460543358 / 7200.506343722秒 | fitSTOP；没有完整生产模型 |
| C1 Web / Y累计TRAIN | 7200.329183977 / 933.099832124秒 | WebFIT87false，后续验证不回写成功FIT |
| C1 OWN1失败VALIDATION | 1803.608489290秒 | 原工程window超时，费用永久保留；不作算法NO_GO |
| C1 OWN2原full4 VALIDATION | 4502.862928584秒 | 原全四图回放/own窗口，不是正式QPS |
| C1 Web12 CAL VALIDATION | 3080.518588604秒 | 风险采样/packet前原CAL费，不是wall性能 |
| C1正式BUILD4失败 | BUILD19.132550548秒；outer20.612599466秒 | compile/nm/objdump均0，日志容量失败；不回写PASS |
| C1新current-image passive成功 | BUILD4.806675644秒；outer6.161558212秒 | 新TRAIN0；准备1.188848432秒另列，launch/post另列；不充全own资格 |
| M4共同族上界两作业 | 547.2465336322784秒 | 必要门费用，不是QPS |
| J45四provenance / 四finite typed | outer13.718122720718384 / 8.139649391174316秒 | 只适用有限工程范围，不是完整E或all42成本 |
| JBP两个loader BUILD | 10.156322883秒 | 仅该两窗口；其他旧工程费用仍保留，完整JBP总费本稿未知 |

本稿没有读取当前账本重新聚合，不能补造其他方法或全campaign的BUILD/VALIDATION总费。所有失败、超额小数、pre-BEGIN bootstrap和cleanup按原真实窗口披露，不能混把BEGIN–finish、monitor wall和含回收outer当同一指标。新passive采样RSS仅4096B未覆盖峰值，不能宣称实际内存只有4KB或据此证明strict cap。非学习工程并不意味着免费，也不承诺整个接续≤2小时。

**接续顺序与停止点**

1. 已完成的M5唯一CAL/全部80行、C1原24CAL/packet/44门、BUILD4和新passive观察不重复。保留旧失败和已取得新image完整身份。
2. C1当前最接近性能主线：先新image Faiss字段/sign/完整caller的有限付费静态证据，再五项绑定和同child fullown/FP；条件真满足后才原48模板/两K/强控制/五轮完整wall。不得从静态候选直接运行正式wall或把Webclosed类填默认免测。
3. M4共同族、J25同R/U定义版本和M5有限CAL可据现证据分别收口scoped STOP/NO_CONFIRM；M2/B4报告成本STOP和生产欠证据，不作全算法负判。
4. J45冻结普通fusion可评估必要非学习全E/current-image接口，但原hard gates与全范围不放宽。JBP仅有限fixture工程可继续准备；共享A/π1主学习实验在预算禁令下停，不以工程数量充最终方法进展。
5. 当前整体完成时间unknown：没有全own/完整wall的实测速度依据，不能承诺整项八方向时长。每30分钟真实核实进度、费用、失败和阶段ETA；等待或计划不算核查。此前3–4天是M2全量精确证明/复核估计，不能当实测训练时长或当前路线承诺。

这份阶段报告是用户可读的证据整理，不新增签字流程、任务、权限或科学结果。它允许逐个固定版本有停止结论，但原八方向完整要求尚未全部闭合，可靠Recall@1/@100–QPS默认替换仍未建立。

**来源、作者关系与冻结身份**

本稿作者参与历史C1 Python consumer/wall、JBP有限fixture/archive观察和M5 costSTOP helper；是相关部分C++/reader Source非作者审者。这里复用已保存报告字段及Root实际声明，不能称独立重做我的实现或Root机器/科学审计。完整80行/原评估SHA在M5附录；所有原主文档、report.md、state及数据未修改。

本稿只读下列三份明确安全输入，全文SHA与完整Python stat5前后等值（mode为完整st_mode，mtime_ns为整数）；不跟随其中机器/科学/运行态引用。原草案处于STOP_EDIT/DRAFT并完整保留。本阶段报告已由Root全文阅读及保存指标查表，后续修正另存新版本；原八方向实验仍未完成。

- [original8_current_completion_requirements_report_audit_20261006_v2.json](original8_current_completion_requirements_report_audit_20261006_v2.json)：SHA `a5738278a94c4cbd2fdf1b7509cf1bedf4d80a56750f3729758e9e5956c447c9`；bytes=82582；stat5 before=after `{"device":66309,"inode":1211841,"bytes":82582,"mtime_ns":1791239251910478491,"mode":33188}`。
- [report_metrics_M5_saved_all80_20261006_v1.md](../report_metrics_M5_saved_all80_20261006_v1.md)：SHA `ec3570d444a78771f945f6b1dc3f21842a64aacde04f4e342fb6a771390ea02a`；bytes=12154；stat5 before=after `{"device":66309,"inode":1211688,"bytes":12154,"mtime_ns":1791230270045905683,"mode":33188}`。
- [next_dialog_handoff_20261006_v75.md](../next_dialog_handoff_20261006_v75.md)：SHA `575312b5fc3240aa4b14d49d7af4118a75c36281bf35eb7a98367ee3adc4615a`；bytes=13713；stat5 before=after `{"device":66309,"inode":1211846,"bytes":13713,"mtime_ns":1791241074294513067,"mode":33188}`。
