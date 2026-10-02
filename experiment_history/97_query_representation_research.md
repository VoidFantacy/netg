# 97｜查询侧表示研究与历史训练样本几何检查

2026-09-20。针对 CCF B 会议的方法贡献问题，用户同意先研究限制与新方案。本记录不是 E104 检索实验；最新正式性能仍 E103，生产 E99、Web soft/Yandex hard 保持。

核对 Legacy Neural Router、E28 和 GATE 作者/本地源码后确认：所查实现将 hub 表示离线导出，不能据这些 MLP 结果否定查询侧非线性。E36 已有查询相关组合网络，但其在线枚举/打分与一次查询编码不同。真实联合效用监督、等价教师和 anchor 早已有先例，不能重复列作新贡献。

方法分析区分三层：静态画像/仿射 query 的精确评分能力，固定 P 的 top3 集合可达性，以及小网络的跨查询迁移和实际小图路由。定向阅读 GATE、ICML 2019 Learning to Route、SIGIR 2024 LTR；查询编码器本身不是新颖性保证，CRINN 只核对摘要以区分研究对象。

实际检查在访问前锁定每集 8 个 E24 fit 行，使用 E24 hard 画像和 E28 已有 teacher slot，解 min-L∞ 查询位移 LP，margin=1e-4，对全部 H 比较。两集均 8/8 得到并重新核验可行 witness；原 query 分别 3/8、2/8 已选中教师。仿射折叠最大误差 1.78e-15/1.22e-15；脚本约 7.82 秒。既有输入前后 SHA 相同。

这只是 16 个旧 K10 教师集合的数值几何检查，不是新 K10 检索、K1/K100 效用、总体可达率或泛化结果。未训练、未执行 ANN/GT/构图/QPS、未读取评估 query/GT 载荷。历史性能与当前研究分开保存。

推荐一次轻量 query 残差 MLP，与等参数线性 query、静态自由 W 共享联合监督比较；先验证 K1/K100 余量，再检验跨查询迁移和完整 wall。最多两集六次训练、明确查询/时间预算与停止门，尚未实现/运行。入口字典协同仅条件备选，多步 RL 暂不投入。不恢复 E95 旧 runner。

证据：[完整研究](../entry_method_exploration/20260920_query_representation_research_v1/report.md) · [最小验证协议](../entry_method_exploration/20260920_query_representation_research_v1/protocol.md) · [只读几何脚本](../entry_method_exploration/20260920_query_representation_research_v1/src/audit_representation.py) · [实际结果](../entry_method_exploration/20260920_query_representation_research_v1/results/representation.json) · [完成核验](../entry_method_exploration/20260920_query_representation_research_v1/reviews/completion_audit.json)。
