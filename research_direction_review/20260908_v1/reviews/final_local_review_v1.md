# 最终文档本地独立复核 v1

状态：**局部数值、因果边界与旧版本停止边界 PASS；整体待完成一项成本匹配澄清及一组历史措辞修正。** 本文是初审记录，不把尚待修订的设计记为已执行或已通过实验。

只读复核了综合报告及当前 summary/spec/s-target 全文，并用已绑定的小型 P2 分析、P3 gate 和目标泛化摘要检查报告中的本地数字。没有打开原始 GT、query、base、图、逐查询 count 或 NPZ，没有实验/编译/模型变更；唯一输出为本文件。论文事实与整体文件保护由主审另行检查，本报告不代替该项复核。

## 初审发现

| 编号/等级 | 问题位置 | 发现与影响 | 修正建议/当前状态 |
| --- | --- | --- | --- |
| F1，中：执行前必须澄清 | s-target.md:27–28；综合 report.md:41–43 的“匹配实际 QPS”表述 | 仅选择 QPS 不低于区域池的离散统一池点，允许双方实际耗时相差很大；粗网格下统一池未用完的时间预算可能被当成区域策略的效率空间。bootstrap 重选只能处理选择不确定性，不能填补缺失成本点。这处缝隙也存在于本地审查者的最初建议中。 | 主审已接受：将统一池/区域池 QPS 比的匹配窗固定为 [1.00,1.02]，只称约2%容差的近似匹配；超差/无匹配 INCONCLUSIVE，不追加点。bootstrap 无匹配重复不得丢弃，如何计入决策及 timing 不确定性必须在新执行协议预注册。**本次快照仍待写入并复核**。不声称严格数学等成本或所有策略的最优上界。 |
| F2，低：历史与当前措辞 | summary.md:86；spec.md:199、226 | 新首部正确注明 DESIGN_REVIEWED_NOT_RUN 和旧执行关闭，但后面的“用户已恢复夜间授权”“当前 s-target 已替换为另获授权的长期分层计划”“本次恢复授权已生效”仍使用当前时态。spec:199 对当前文件内容的描述也已经过时。它们未实际打开 gate，但可让后续读者混淆。 | summary 改为已结束夜间版本的过去事实并指其冻结协议；spec:199 指当前方向复审/旧计划历史正文；spec:226 明确夜间授权已随截止结束。**待修**。 |
| F3，低：已修复，不再开放 | 综合 report.md:35；s-target.md:9 | 首次 GT 命中不是无 GT 在线策略可直接读取的信号。初读“可观测标记”缺少离线限定。 | 当前已明确“独立 trace 结束后关联 GT 得到的离线诊断标记”，不代表到达其余答案的可搜索邻域；已核对修订，**关闭**。 |

F1的条件例子：若未来统一池 L192 比区域池 L128 慢，原规则可能退回统一池 L128，将已知同L质量/成本差再次作为“匹配后收益”。这里没有预测新 L192 的实际性能；它只说明旧判据容许这种选择。固定近成本窗后若网格没有相近点，应结束为 INCONCLUSIVE，不能因之前已投入工作而放宽。

## 已通过的检查

- 综合 report.md:9–11 的本地数值正确：训练跨区数4.333→2.603；WebVid主Recall下降0.866/0.790 pp；Yandex未证实改善；P2 WebVid oracle统一池/区域池约30699/21352 QPS。均与小JSON对应，无新计算性能结果。
- 未把当前P3负结果概括为所有查询感知图搜索或所有层次预测无效。P4未运行、λ分支改变候选生成/区域/门户/路由、局部尺度不是因果证明的边界均明确。
- 新计划只是 DESIGN_REVIEWED_NOT_RUN；R0–R2未执行，baseline验收、统计规则、输入绑定、资源和新隔离版本仍为执行前条件。未暗示同实际成本空间已被发现。
- 新筛查固定原P2预注册表示和同route，用更多普通搜索预算补齐成本证据；没有重选P3 λ0、重分区、调λ/种子/门户或恢复原P4。旧Multi-view、静态utility/probe-reroute的停止边界保留。
- R0a前置paired Fast、同入口统一池和GATE受约束适配契约；PyANNS为待验收对象。综合report:45已明确GATE需通过新契约验收，不把历史适配、库安装或论文QPS当成本地新结果。
- 新候选只在有限控制家族内解释；失败不否定全部固定图控制，通过不算可部署oracle胜利，也不直接恢复P3/P4。改变拓扑须另有受控具体路径证据与成本/空间对照。
- s-target.md:41–43把旧P0–P8标成已停止历史协议，并禁止以旧授权/周次作为新执行入口。新最终门槛仍为双数据集、相邻工作点、校正区间、三构建及冻结后held-out 10K×3，没有降低正式要求。
- split表述准确：20K fit与历史10K pilot分开；validation只做过输入完整性审计，没有性能选择；held-out冻结。没有把首次命中诊断作为在线GT特征。
- 旧P3 gate与CLOSED保护在所审文档中保持；本审查未修改原报告/gate/state或任何实验数据。实际字节保护校验和全部进程核验由主审负责，不能从文档措辞推导整机保护已验收。

## 复核输入身份

以下SHA对应本初审快照；修正完成后应追加闭环记录并绑定新SHA，不能只把初审状态改成无问题。

| 文件 | SHA256 | 字节 |
| --- | --- | ---: |
| research_direction_review/20260908_v1/report.md | `a85e0b7068fd6ae1b4cc59c9768b537c204df4ac6c3e2647f4b7397566618608` | 8653 |
| s-target.md | `d659ed420f58eb20402c24435c5ed4aa52b49394efe2f463c2dd86303b9a2902` | 24676 |
| summary.md | `2cde371d58f9188cd2c4119ab356b9581bcc7923fd7dec4c3c724de106440092` | 15104 |
| spec.md | `d388edd849cfb233a630e6bf129660092a5d1c9646410494b20318c6358f6d5c` | 26462 |

本地机器证据：

- `hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/analysis_v1/analysis.json`：`/datasets/0/measurements/4/qps_mean_of_five` 与 `/datasets/0/measurements/5/qps_mean_of_five`。
- 同根 `gates/P3.json`：`/status`、`/structure_condition_met`、`/primary_search_condition/cells`。
- 同根 `p3/target_generalization_interpretation_review_v1.json`：`/datasets/0/fit_and_pilot_concentration/fit` 与 `/datasets/0/main_greedy_search_difference`。
- 更详细的本地假设、成本和归因边界在 `reviews/local_hypothesis_audit.md/.json`，含18个来源SHA与54个已解析JSON指针；其中最初成本匹配建议需按本次F1修正解释。
