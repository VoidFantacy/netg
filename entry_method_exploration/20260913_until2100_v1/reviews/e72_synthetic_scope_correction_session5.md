# E72 合成验收范围更正（不改旧封存）

2026-09-13，第5会话，接续supervisor_notes 13:37 / review_071。

E72协议列出的“候选不足3个真实hub时拒绝”没有被实际合成测试调用。synthetic.cpp末尾验证的是引用计数下溢拒绝，不能替代路由的不足三入口负例。运行时存在distinct==10及selected==3检查，只属于源码保护事实，不登记成已执行合成覆盖。

实际已验收范围保持：4图、512 HNSW、0 NSG；ties、内部/外部ID不同、singleton截k返回与NDC恢复、重复候选/每query复位、add/remove引用计数及忽略不可靠移除dist。真实128/7952输入的plain/count/原kernel、singleton与旧三控制回归保持。

本更正不改变E72查询、结果、费用或双集接续门失败，不重跑合成图/真实query，不修改已封存的E72协议/source/report/manifest/历史61字节。E74使用独立E73普通HNSW接口，不包含E72 callback；不受此覆盖缺口影响。下次若继续该callback接口，应在新的技术验收版本实际调用不足三hub的路由拒绝路径，而不能继承“已验证”标签。

来源：[E72合成源码](../stage13_distinct_hub_width_v1/src/synthetic.cpp)、[E72协议](../stage13_distinct_hub_width_v1/protocol.md)、[监督备注](/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md)。
