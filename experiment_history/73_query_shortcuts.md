# 73｜训练查询排名缺口补边

E84，2026-09-13第8串行会话，`COMPLETE_QUERY_SHORTCUTS`，双集预锁门FAIL，固定首返回slot/最高票/至少2票/每源1边规则停止。E84 WebVid对compact局部修复保留，不能被完整门失败抹去；没有新增QPS。

## 机制、区别与数据

固定E73 compact画像与原图全部旧边；P-fit20K raw query真实ef10路由首返回slot为源，完整float64 per-hub max前三中漏选的目标slot投票，每源只追加最高票且>=2的一个跨hub目标。源不是实际遍历路径。控制在同源各添一条最近其他hub非邻居，逐节点度匹配、边长不匹配。原H815/821、NSG/base/rawIP/GT、W/labels/上层/层级/入口不变；在线无新计算模块、原E73 evaluator同SHA。

E83基于同hub关系，本版基于fit查询的近似排名缺口；它仍是几何监督，未使用GT/NSG收益投票。历史E33原边效用删除不同，本次新增跨hub边且保留全部旧边。两普通静态图监督训练，不是梯度训练或普通HNSW构图。Web/Y分别254/47条/臂，支持2..41/2..3票。fit20K namespace router_train[10000:30000]含旧train/monitor；原画像仍有GT监督。aux128只回归既有路由，不入票；aux7952及两半均历史暴露且选择反馈算训练，cal/audit历史使用，最终E34/held-out未读。

## 实测与限制

| 数据/参考 | 主净命中 | 救回/新增失败 | 判定 |
|---|---:|---|---|
| Web/P | -17 | 44/51 | 仍有损伤 |
| Web/compact | +42 | 9/5 | 两半非负，局部修复 |
| Web/nearest控制 | +43 | 8/5 | 两半非负 |
| Y/P | +116 | 41/28 | 主要继承compact |
| Y/compact | -4 | 0/0 | 没有新增收益 |
| Y/nearest控制 | +4 | 0/0 | 不满足完整门 |

Web对compact routeNDC+1.075%、graph -0.120%、total -0.041%；Y+0.178%/+0.00086%/+0.00847%。这是计算计数，不是QPS。Web+42来自114正向与72负向净query命中，GT成员151增/109失；并非只发生救回。完整旧收益保留/丢失/新损伤和固定两半见原表。没有因为局部阳性扩大阈值、图边数或启动原协议禁止的wall。

## 成本、验收与补充

129536 NSG、209792 HNSW（fit/回归80512+查询129280）、4边安装、2图监督训练，0普通build/画像训练/新GT。编译12.743730s；离线图监督阶段4.989s、各项含关系见cost，不能相加成端到端。训练路由子进程RSS轮询较稀，样本不是实际峰值；没有用4KiB样本证明内存上限。全部native实际terminal0，CPU15实测1线程。继承GT/P成本未知。

独立40000完整排名/全部7006票对/所有控制排名、图所有旧边和非邻接字节/可达性通过；完整fit plain/count，只有aux256与旧路由回归。64,640行集合/mask、31,808旧P/compact全字段、原kernel256和全部7slot核验。近tie Web55/Y20保留，不声称SIMD bit parity。独立补充明确协议A的回归措辞，冻结common累计目录漏E83由外部补充checker包含三阶段，实际未超资源预算，原源/seal不改。

[完整报告](../entry_method_exploration/20260913_until2100_v1/stage25_query_shortcuts_v1/report.md) · [协议](../entry_method_exploration/20260913_until2100_v1/stage25_query_shortcuts_v1/protocol.md) · [补充](../entry_method_exploration/20260913_until2100_v1/stage25_query_shortcuts_v1/reviews/protocol_clarification.md) · [训练源码](../entry_method_exploration/20260913_until2100_v1/stage25_query_shortcuts_v1/src/train.py) · [固定配置](../entry_method_exploration/20260913_until2100_v1/stage25_query_shortcuts_v1/config.locked.json) · [门](../entry_method_exploration/20260913_until2100_v1/stage25_query_shortcuts_v1/results/gate.json) · [配对](../entry_method_exploration/20260913_until2100_v1/stage25_query_shortcuts_v1/results/paired.csv) · [成本](../entry_method_exploration/20260913_until2100_v1/stage25_query_shortcuts_v1/results/cost.json) · [失败查询](../entry_method_exploration/20260913_until2100_v1/stage25_query_shortcuts_v1/results/failure_queries.csv)
