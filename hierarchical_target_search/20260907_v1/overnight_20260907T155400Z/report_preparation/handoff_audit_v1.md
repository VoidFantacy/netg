# 当前交接状态一致性审计

审计截点：2026-09-07 18:46 UTC / 北京时间 2026-09-08 02:46。**首要修正是把前部仍停留在“尚未测试/实现验收中/P2初测”的文字统一为：P0/P1/P2及P3新P1已通过，P3完整pilot完成后搜索收益gate为NOPASS，P4–P8未启动。** 本报告只读三份交接文件、版本state和下列既有小型汇总，不打开原始向量、GT、标签、count行、trace行、图或ANN，不修改交接文件、模型、gate或最终报告。局部尺度诊断由root另行执行；本审计没有其实际结果。

## 应修正的当前状态

| 优先级与精确位置 | 当前问题 | 建议当前措辞或处理 |
| --- | --- | --- |
| 高：[spec.md:47](/data/netg/ACSG/spec.md:47) | 同段称P0/P1通过，又称“测试target已编译但尚未运行”“分层区域、路由、区域池和新计时器尚未完成验收”，与state:33–40、后文spec:239–247和P3 gate冲突。 | “本轮搜索实现、纯计时/独立计数与P0/P1验收通过；P2的64区域模型及P3的16×16结构/门户模型已完成评测，P3新增256叶区P1复验通过。P3完整pilot未通过搜索收益gate，状态为NOPASS；P4层次预测尚未实现和启动。实现正确不等于方法有效。” |
| 高：[summary.md:9](/data/netg/ACSG/summary.md:9)、[summary.md:11](/data/netg/ACSG/summary.md:11) | “接续P3结构诊断”“搜索测试与P2初测已完成”滞后于完整P2/P3及两项诊断。 | “P0/P1/P2通过；P3结构与门户完整pilot完成但搜索收益gate为NOPASS。门户暴露和目标泛化诊断已完成，当前只执行另行冻结的局部尺度只读诊断并综合证据；P4–P8未启动。当前没有有效端到端性能改善证据。” 保留依赖准备轮与实验轮的区分。 |
| 高：[spec.md:212](/data/netg/ACSG/spec.md:212) | 标题“研究已恢复，实现验收中”作为当前阶段已过时。 | “新分层搜索协议（P0/P1验收通过，P3完整pilot为NOPASS）”。不要将P3性能失败写成程序错误、验收阻塞或未运行。 |
| 中：[spec.md:226](/data/netg/ACSG/spec.md:226)、[s-target.md:11](/data/netg/ACSG/s-target.md:11)、[s-target.md:140](/data/netg/ACSG/s-target.md:140) | 显式引用旧子状态`P3_NOPASS_DIAGNOSIS`，而当前[state.json:5](/data/netg/ACSG/hierarchical_target_search/20260907_v1/state.json:5)是`P3_NOPASS_LOCAL_SCALE_DIAGNOSIS`。大阶段一致，精确状态字符串不一致。 | 截点时统一为“P3 NOPASS；门户暴露、目标泛化已完成，冻结局部尺度诊断处于验收/执行阶段”。root完成最后诊断后，依据完成标记更新精确子状态，不机械沿用此pending措辞。 |
| 中：[s-target.md:141](/data/netg/ACSG/s-target.md:141)、[s-target.md:143](/data/netg/ACSG/s-target.md:143)、[s-target.md:144](/data/netg/ACSG/s-target.md:144)、[summary.md:78](/data/netg/ACSG/summary.md:78) | 已完成列表漏列目标泛化；next-action正确指向局部尺度，但活跃任务文字是随时会过期的实现中快照；当前决策段的“补全已有机制证据”容易被误读成尚欠trace。 | 已完成列补“门户暴露、目标泛化及完整23查询trace”。下一行动保留冻结局部尺度诊断的有限范围；最终合并时按root实际完成状态更新，并核对已有实时控制台账。已完成trace不能继续作为补跑授权，P4不是下一行动。 |
| 中：[summary.md:13](/data/netg/ACSG/summary.md:13)、[s-target.md:25](/data/netg/ACSG/s-target.md:25)、[s-target.md:29](/data/netg/ACSG/s-target.md:29)、[s-target.md:31](/data/netg/ACSG/s-target.md:31) | 64区域和16×16仍主要按将来设计叙述；长期2–4门户及层次线性预测容易与已运行实现混读。不是要求删除长期计划。 | 增加范围标签：“P2已运行64区域、2门户/区；P3固定16×16、3门户/叶区、总768，每次oracle全局选4叶区。层次线性预测为P4计划，尚未启动。” 保留原长期设计并指向冻结P3协议。 |
| 低：[summary.md:51](/data/netg/ACSG/summary.md:51)、[spec.md:39](/data/netg/ACSG/spec.md:39)、[spec.md:43](/data/netg/ACSG/spec.md:43) | 已终止Multi-view段落仍称“当前路由”“当前validation版本”；“当前部署方法”超出本次只核验研究基线的范围。 | 改为“该历史三view配置”“该历史validation版本”“当前已验证基线为Fast v1”。这一历史分支仍保持NO_GO_ROUTING_COST，不把它混称为当前新方法。 |

## 需保留并可略作澄清的正确边界

- **23条trace当前已写对。** [summary.md:105](/data/netg/ACSG/summary.md:105)、[spec.md:241](/data/netg/ACSG/spec.md:241)、[s-target.md:156](/data/netg/ACSG/s-target.md:156)均明确23查询、460条trace、276配对，并解释初批16条和后补7条。`p2/trace_completion_addendum_v1.json`同值。原`gates/P2.json`保留16/23及320条的决策时证据，是有时间戳的历史gate；不要为“统一当前状态”覆写它。当前入口同时链接该gate与completion addendum即可。23条固定trace仍是描述性机制证据，不能当成随机代表性样本或代替完整10K分析。
- **P3是完成的负结果。** [summary.md:109](/data/netg/ACSG/summary.md:109)、[spec.md:245](/data/netg/ACSG/spec.md:245)、[s-target.md:160](/data/netg/ACSG/s-target.md:160)及`gates/P3.json`一致。主对照始终是oracle_probability下λ1_greedy3−λ0_greedy3：WebVid −0.866/−0.790 pp，Yandex −0.095/−0.017 pp；四格正下界条件均失败。结构子条件通过不抵消搜索gate失败。保持修订计数1、P4–P8和validation/held-out未启动、无辅助图触发证据。
- **M4不是Recall上界，seen不是查询泄漏。** [summary.md:119](/data/netg/ACSG/summary.md:119)、[spec.md:255](/data/netg/ACSG/spec.md:255)、[s-target.md:170](/data/netg/ACSG/s-target.md:170)现有M4及seen/unseen结论正确。建议首次出现再明示：“seen是目标base ID曾在fit GT10中出现；槽位占比不是独立节点占比或查询重叠率。” WebVid pilot M4确有+1.808 pp，不能写“集中度完全未传递”；Yandex为−0.004 pp，不能写等效或所有子组完全不变。WebVid主Recall损失主要来自seen目标贡献，不能把退化全部解释为unseen，也不能据此证明记忆化、过拟合或图连接因果。三份文档已有“无新CI或因果结论”，应保留。
- **oracle必须明确是诊断。** [summary.md:13](/data/netg/ACSG/summary.md:13)、[spec.md:216](/data/netg/ACSG/spec.md:216)、[s-target.md:45](/data/netg/ACSG/s-target.md:45)中的“train-only/仅训练”与train来源的开发pilot并不冲突，但易与20K拟合混淆。建议写：“真实路由API无GT；oracle由评测层读取该开发pilot的真实GT区域占比，仅用于机制诊断，不是可部署路由，不进入正式方法性能frontier或held-out确认。” 保留真实方法全部在线成本、oracle不同颜色/单独列示的边界。
- **实际split数值正确，旧30K表需标范围。** [summary.md:15](/data/netg/ACSG/summary.md:15)、[spec.md:214](/data/netg/ACSG/spec.md:214)、[s-target.md:79](/data/netg/ACSG/s-target.md:79)一致：原router_train后20K `[10000,30000)`拟合，前10K `[0,10000)`是历史已用开发pilot，paired Fast重建20K；独立QGT仍5K。不要把pilot叫未见测试集，也不要将旧30K prototype接回新拟合链。[spec.md:92](/data/netg/ACSG/spec.md:92)的5K/30K/10K是历史Fast完整数据契约，应加“本轮从原30K再划20K fit/10K pilot，见第13节”，无需改写历史表的正确数值。
- **不显著不等于等效。** [summary.md:111](/data/netg/ACSG/summary.md:111)、[spec.md:247](/data/netg/ACSG/spec.md:247)、[s-target.md:162](/data/netg/ACSG/s-target.md:162)可将“8个门户pilot对照均不显著”收紧为“全部8个固定对照的普通95%区间含0，未证实收益；不构成等效证明”。纯wall五轮不是五个独立Recall样本；跨模型固定顺序wall只作描述，这些现有边界均保留。
- **相同输出不等于相同轨迹。** [summary.md:117](/data/netg/ACSG/summary.md:117)、[spec.md:253](/data/netg/ACSG/spec.md:253)、[s-target.md:168](/data/netg/ACSG/s-target.md:168)已正确排除“门户没有改变实际入口集合”，并明示同route实测检验无样本。68.34%–93.36%返回集合相同，不能推出visited、扩展、距离或路径相同；不要新增无joint-summary支持的分组NDC归因。
- **局部尺度是充分条件审计。** [summary.md:121](/data/netg/ACSG/summary.md:121)、[spec.md:257](/data/netg/ACSG/spec.md:257)、[s-target.md:172](/data/netg/ACSG/s-target.md:172)与冻结协议一致：`D(u)·9Q<M`仅保证该节点一个可行且净GT区域数下降的移动必降固定λ1目标J，不保证该移动存在、被选择或解释搜索退化。D为原有向有效非自边入出槽位总数，不能替换成全局平均度；終态标签差不重建单步历史。root取得真实结果后再更新结论，不能用本审计预写覆盖率或成功结论。

## 台账与时间戳建议

[state.json:32](/data/netg/ACSG/hierarchical_target_search/20260907_v1/state.json:32)的implementation_state与P3 gate一致，不应因性能NOPASS改成实现失败。`evidence`数组目前主要止于P2和P3协议，虽P3 gate、完整trace、两项诊断已有分散字段，建议将P3 gate/analysis、trace addendum和已完成诊断汇总的规范路径加入当前证据入口。现有路径有版本目录相对和repo相对两种写法，后续统一新字段的解析基准；不更改旧不可变产物。`dependency_status=READY_FOR_PLAN_RESUMPTION`仍反映旧阶段，可写为`READY`以免被当作需要再次申请恢复研究。

三个夜间追加块标题仍标北京时间02:06（summary:99、spec:235、s-target:150），但包含之后完成的诊断。root最终整理时更新为真实核对时间并标时区；不要沿用这份审计截点充当未来完成时间。`active_job=null`及“无重任务”只是state快照，本审计未另读实时控制状态；应由root在最终整理时核对实际控制台账。

## 输入身份

本报告所有行号对应如下快照；若root随后编辑，应按所引原句定位。仅报告文件是本任务新写入内容。

| 文件 | SHA256 |
| --- | --- |
| `summary.md`（121行） | `e0f7b840ea8a9b2d069b54177c38567c0de3e16cf20648b32627930e9de0fc80` |
| `spec.md`（257行） | `73525e3454d463fecb6c3ba102cd32265bbfd4031da48bf9890064f02a67b750` |
| `s-target.md`（172行） | `db0860673fe9fae0bd22f18f25782d62b841fb0fd0485128364bf63ebf4a5a25` |
| 版本`state.json`（63行） | `af0e3e4f2d0a23efd0c37a1ee01c14bedbeac09bb203a7ac0c03b5f2d5616a6d` |
| RUN/`gates/P2.json` | `6240cea60d790d030e0fdaf560b95d9e951260d4ba3d6701863b06c1c4cc895e` |
| RUN/`gates/P3.json` | `3e154f9db332ec9a404b85d85061459967911be797e4350c191b1d9774dbc4f2` |
| RUN/`p2/trace_completion_addendum_v1.json` | `995dae5027b9c7137a677a6f8b219324b5b44560b0f992e11768749d18a44b4d` |
| RUN/`p3/objective_local_scale_protocol_v1.json` | `abae80a4a2bbf6366e413b21a948a6fa4f27166e1160973cc223681e75cfff91` |
| RUN/`p3/target_generalization_interpretation_review_v1.md` | `2d4d5a86caf539e0b1c999c66d6fed7119b6f906df4c1ab3ece827c0be3eb45a` |

RUN为`hierarchical_target_search/20260907_v1/overnight_20260907T155400Z`。本报告未核验或改写这些汇总所指向的原始数据，也未新增统计检验。
