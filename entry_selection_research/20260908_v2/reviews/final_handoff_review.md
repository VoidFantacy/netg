# 最终细化与三份交接同步复核

2026-09-08。状态：**PASS_DESIGN_ONLY**。本次增量复核未发现调研交付阻断；不代表实现验收、实验授权或性能GO。任务到调研报告与交接结束，不启动实验。

本文件承接[前次设计复核](final_design_review.md)，只核对其后的小范围细化和三份交接的当前首部/末节，没有重做全文审计。原 `final_design_review.md` 及其历史SHA保持原样。本次只新增此审阅文件，未修改任何主文档、方法源码或旧状态，也未运行实验或打开原始query/GT。

## 本次检查的内容身份

路径相对 `/data/netg/ACSG`。

| 文件 | 最新 SHA-256 |
| --- | --- |
| `entry_selection_research/20260908_v2/report.md` | `b5630baf17f5f7d847ff1e0ac774fe399cfb8c66fa2a4c1d15f000248385a351` |
| `entry_selection_research/20260908_v2/recommendation.md` | `6ff880f0936051d08061f5bed10364fdc3cb236115f33118503e5fc09f68ba34` |
| `entry_selection_research/20260908_v2/minimum_gate.md` | `f3ca89761496a5de608ba85c529ddb71db5ff76ce61537ac5d04c17350691dd6` |
| `summary.md` | `82e93fe92b269a875843b34fe40573390d6053d1dff1005265c04973bd97e94f` |
| `spec.md` | `6afc054b18896392abf604a8fb039e87ecb098459d07619c2140bf9a3e9a49ad` |
| `s-target.md` | `0049d8b96811f968ebbc53d5fb0769339a275bfd43b78dff64453409b03e201f` |

## 增量复核结果

| 检查项 | 结果 | 核对说明 |
| --- | --- | --- |
| QPS估计器 | PASS | G3固定`10000/mean(五轮wall_seconds)`，bootstrap使用相同估计器，明确不使用五个QPS的平均。此前的执行前歧义已消除。 |
| bootstrap复现细节 | PASS | G1/G2/G3分别锁定PCG64种子202609081/202609082/202609083、10,000重复、线性分位插值、ddof=1及numpy版本；dataset之间分开抽query，同dataset method/L共享抽样。 |
| G3选择与同时区间 | PASS | 继续先为96个固定质量/成本比较建同时区间，再在预定候选中选点；原成本方向、C−Fast/C−B阈值、UNMATCHED及99.5%稳定性边界没有被细化削弱。 |
| B-triple-additive成本缺口 | PASS | G3明确没有测该模型wall，不能声称胜过全部可加方法；正式阶段明确补齐两种可加模型和Fast1/2/3完整成本曲线。 |
| 2026论文补充 | PASS，摘要一致性核对 | report新增段落与[独立补充](recent_2026_entry_addendum.md)一致：公开range路径的当前GT在搜索后更新后续状态；没有误称用当前query自身GT选择初始入口。该工作仍作为相关工作/成本边界，不被升级为本地性能证据。本增量复核未重审其全部8个源码文件。 |
| summary当前研究判断 | PASS | 当前状态为RESEARCH_COMPLETE_DESIGN_ONLY，唯一优先证伪推荐固定单view C8/anchor/m3，40维模型尚未实现；旧池oracle、真实single监督和新组合标签的差别及证据限制保留。 |
| spec实现/复现契约 | PASS | 首部指向新增第17节，明确无新方法实现；第17节记录真实入口消费、40维/16点积、D1/D2、有限动作、300万调用/4小时及96项同时区间。具体公式以minimum_gate为准，无旧runner执行入口。 |
| s-target当前优先级 | PASS | 首部将调研标为完成、下一步为方案审阅；未来执行须新任务/新目录冻结。R0–R2和旧分层协议被明确标为历史、已替代/停止，不自动排队。 |
| 三份交接历史末节 | PASS | 旧P3 NOPASS、P4–P8未启动、截止/停止核验作为历史证据保留；当前首部明确覆盖历史“下一步”。旧v1 pending记录及state/gate/CLOSED不被改写为新实验授权。 |
| 最终门槛与范围 | PASS | 保持CPU双数据集raw-IP、冻结图/base/GT、20K fit与历史pilot、三独立构建、强基线、完整成本/tail、相邻工作点+10%QPS或+1ppRecall及校正区间、冻结后held-out10K×3。新pilot不替代正式验收。 |

## 保留的限制

bootstrap仍是有限重复的近似开发检查，**不是最终统计保证或有限样本精确覆盖证明**。历史pilot的使用、五轮整批wall的不确定性、无法把重采样query组合映射为实际纯wall等限制仍须随未来结果披露。现有命令/API均为未实现草案，调用数与四小时上限不是实测吞吐/完成时间。

本次核对没有改变唯一推荐，也没有新算法收益结论。三份交接与已保存方案一致，可以结束本轮调研交付。
