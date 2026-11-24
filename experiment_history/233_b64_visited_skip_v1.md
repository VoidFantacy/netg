# E233 WebVid B64 复用主搜索已打分标记

在发布 SPAN4 的同一原生 raw-IP 路径，只读本查询 visited。主结果由现已打分且能入池的结点选择。已访问而未在主 Top-K 的候选不能凭相同分数严格胜过原截止值。保留原 B64 候选源和行顺序，跳过已打分候选、剩余候选一次散列查插。OnePass64 只改散列查插并使用原 Main Top-K 填集合，分开比较实际距离复用。另以 Far52 同期核 Visited52。真 K100 两窗 132 点、264 个 CPU15 单线程完整批次。

22 组 L/窗的 OnePass64、Visited64 与老 B64 输出逐字一致，Visited52 与 Far52 也逐字一致。33,792 条额外标量排序资格检查逐个比较剪掉的候选与同一阈值。两窗同 L 速度中位数 +0.45% 和 +0.53%，OnePass64 为 +0.09% 和 +0.06%。75.5% 确认窗 L204，Visited64 与老 B64 的 75.5150% 相同，精算少 6.81 个/条，完整 QPS 1,670.8 对 1,663.6，+0.43%，慢遍对快遍仍 +0.38%。开发窗对应门槛 L196 减 0.22%。保留为结果等价的实现候选。生产接口及默认仍按已有发布合同。

[完整报告](../entry_method_exploration/20261123_b64_visited_skip_v1/report.md) · [协议](../entry_method_exploration/20261123_b64_visited_skip_v1/protocol.md) · [同期逐点](../entry_method_exploration/20261123_b64_visited_skip_v1/analysis/points.csv) · [封存](../entry_method_exploration/20261123_b64_visited_skip_v1/seal.json)
