# 第4独立串行研究会话安全交接

2026-09-13 13:01:18 +0800。E69–E71完成并封存，所有8个native job及分析/绘图工具已实际terminal exit0，无遗留实验、训练或计时进程。本会话安全完成，**整日用户目标未完成**；监督器管理下一串行会话，不启动并行CLI/子代理。会话截止13:20:37，整日20:00停新训练、20:40停新增query、21:00完整交付（epoch1789304400）。

## 当前结论与完整交付

本次多画像ef10→30没有稳定整体QPS–Recall改善，原默认保持。Web历史2048五L Recall相对匹配P10全正但QPS中位全负；Y有局部质量，且相对mode10四L Recall负。E66双集原门失败、E70 Y质量门过/Web未过保持；不回写历史门或宣称最终方法成功。

| 阶段 | 已完成事实 | 新NSG / HNSW | 原生秒 |
|---|---|---:|---:|
| [E69 精确前三实际NSG](stage10_exact_triple_utility_v1/report.md) | 31808逻辑exact：28102旧复用、3535唯一缺口、171别名；Y对exact P净+132/失败−10，Web−109/失败+7 | 38942 / 0 | 37.904 |
| [E70 固定图宽度控制](stage11_width_control_v1/report.md) | P/duplicate/mode各ef10/30；Y mode30对P10+77/失败−7、对P30+89/失败−7，两半通过；Web对P10+6但失败+5、对P30−100 | 194304 / 193920 | 150.859 |
| [E71 完整wall](stage12_width_wall_v1/report.md) | 65点、325轮；NSG/Fast30K/GT10-hard/Web匹配soft/P30/mode10/mode30，同批五L | 932880 / 788480 | 1324.923 |

按L64/128/256/400/800，E71 mode30相对匹配P10：

| 数据 | ΔRecall pp | QPS中位变化% | 零命中净新增 |
|---|---|---|---|
| WebVid | +.3174/+.0977/+.1611/+.3369/+.1416 | −4.82/−3.42/−1.41/−1.78/−.84 | −7/+1/−2/−3/−2 |
| Yandex | +.4004/+.1123/+.0098/−.0342/+.0635 | −3.76/−2.39/−1.05/−1.13/−.32 | −8/−3/0/0/+1 |

Web2点/Y3点五轮QPS交叉范围全负，其余跨0；交叉范围不是置信区间。共同Recall插值Web两负一正、Y全负，只是描述，不是测得等Recall提速。全部方法使用E71同批wall，没有复用或拼接旧速度。[实测判断](stage12_width_wall_v1/assessment.md)保留局部正信号及损伤。

[QPS–Recall](stage12_width_wall_v1/figures/recall_qps.png) · [QPS–失败率](stage12_width_wall_v1/figures/failure_qps.png) · [按L三指标](stage12_width_wall_v1/figures/three_metrics_by_L.png) · [失败query图](stage12_width_wall_v1/figures/failure_query_cases.png) · [全84条失败转换query](stage12_width_wall_v1/results/failure_query_summary.csv)。84为不同source query，149为跨L转换事件，420五L格全保留；图每集显示24例。Y3645从全五L10命中变全0，Y2769从全0变8/9/10/10/10，正负案例都是真实原NSG；不要事后用GT挑路由。

## 成本、身份与进程

本会话新增**1,166,126 NSG / 982,400 HNSW**，0新训练/构图/GT/梯度，独立编译26.788s，原生总1513.686s；E71纯325wall合计930.101s。E69加载15.892s，E70 plain/count48次、E71 110次源图加载，均不记新图构建；E71源policy plain .900s/count .893s，NSG load和route-only/graph-only未分计，有null原因。E66继承画像训练30.286s及原GT成本不是零。

今日累计3,235,940 NSG / 3,793,056 HNSW、346新构图（旧synthetic1图/15HNSW另列不混），165历史开发性能点/825wall；最终validation点仍0。累计与每阶段成本见[closeout](reviews/session4_closeout.json)及各results/cost.json。当前free **7.231 GiB**；本会话campaign新增约50.67 MiB（相对session3封存前快照）。未来继续>=7GiB门并预留晚间产物，不删任何旧文件。

只读resume已通过4770项身份，旧阶段1–12/历史封存和24候选均可核验。E71独立133120集合/mask、1040原kernel、全部plain/count、55源图、71680旧基线/20480 mode10/16384 L128回归、325轮顺序恒等通过。监督至12:57已独立验收E69/E70最终封存和E71原始/计时/图表，不需等待许可或重复已通过项。

每个stage的logs/active.json是最后一次历史采样，可能保留RUNNING文字和sandbox PID4；**不能据此认定进程仍活跃**。logs/jobs.json COMPLETE、工具terminal0及/proc共同确认退出；当前native_pids=[]。所有ANN CPU15、实际进程1线程及OMP/OpenBLAS/MKL/NUMEXPR/BLIS1。性能测量期间只有一个被测方法，两个native都退出后才数值分析/画图。

## 下一会话的具体入口

先完整阅读AGENTS/summary/spec/s-target/s-experiment，由历史58/59/60进入原协议/配置/source/results；[监督备注](/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md)在主要阶段后再读。然后运行**只读**检查：

```bash
cd /data/netg/ACSG
env PYTHONDONTWRITEBYTECODE=1 .venv_cpu/bin/python entry_method_exploration/20260913_until2100_v1/src/resume_inspect_v4.py
```

**不要重跑阶段1–12任何runner。** 下一新版本建议stage13_distinct_hub_width_v1，尚未创建/实现/运行。完整方案、候选停止条件、六policy、128预检/7952两半、预算草案194304 NSG及停止规则见[next_stage_design_session4.md](next_stage_design_session4.md)。已有新授权可独立实现评测，无需重新问批准；必须在新增调用前建立独立前瞻协议和资源预算。

第一优先是固定原图/W、以10个不同真实hub计小图保留宽度的单个控制，不继续扫ef。local BaseSearchStopCondition已有相关概念，不宣称新概念；callback接收external、最终结果internal、移除dist不可靠、旧MultiVectorSpace字节格式不兼容。singleton tie恢复还必须保持原堆截k子集，不能先按external标签重排整个ef池再截3。细节和未验收条件见[源码记录](reviews/session4_local_stop_semantics.md)。先合成/非同一ID/tie/引用计数/状态复位/128控制，再全量；新mode排序与旧singleton恢复合同分开。没有实现或合成测试遗留。

Web表示损伤为第二优先；既有exact-mode对exact-P负值不能都归因近似搜索。监督12:55提出同hub字节相同fallback槽精简作备选（Web674/Y396槽），没有新模型/图/查询；需先复核源W，新variable1–3槽接口和构图可能改变近似行为。不要与distinct控制并行展开。完整原生扫描也仅未来备选，E69离线注入没有在线性能证据。

## 角色、最终评估与保护边界

固定原base/rawIP/NSG/GT；Micro-HNSW真实H815/821、mode物理2445/2463，绝不是10M底层大图。画像/构图学习离线，在线轻量。P-fit20K含旧4096train/1024monitor；旧cal/audit/aux7952均历史使用，E69/E70全部反馈与E71历史2048都已观察，动作选择辅助反馈计训练。仅元数据余行不证明全项目未使用。E34历史validation2000今日尚未打开，可留晚间最终同批对照，不回流训练/选型；held-out不自动打开。

[candidate_inventory_v4](candidate_inventory_v4.json)保留旧18条原字节并加6个ef30配置，明确evaluator/graph/W/mapping/tie/physical/uniqueH。E71字段best_new=mode30只是展示别名，晚间best_all与真实best_new尚未最终冻结。最终须含NSG/Fast/当前GT10匹配起点/实际新方法，同机五L五轮完整在线wall及aligned集合评分/失败/成本；没有稳定改善就诚实交付，不用最终反馈找阳性。

四主文档已同步；E69/E70/E71 root source_before及root_after均保留，历史58/59/60和原始results不覆盖。当前根文档可由下一会话推进，封存核验指向历史快照，不应为旧封存把当前根文档回滚。保护全部脏工作区/旧artifact/GT/图/日志，不清理、不外发、不发布推送、不改Codex配置；大文件只在/data，主环境.venv_cpu CPU-only。
