# 113｜E115 GT10评分与小图交叉机制

2026-09-20，STOP_CROSS_SCORE_TOPOLOGY_CANDIDATE。E108评分/图共同变化，本次预锁P/U×GP/GU四格，只有B=(U,GP)可进质量门，C只作机制控制；复核E54/E56/E95，不声称新方法。

两集各4096曝光query、完整72个真实K1/K100点。B−A在L128的Web K1/K100为−0.0977/−0.1482pp、Yandex−0.2930/−0.3481pp，四个98.75%配对区间均跨0；双集预锁门均失败，不测条件wall、不追加网格、不改选C。默认Web soft/Y hard及生产E99保持。

固定评分，GP均减少路由NDC；Yandex U评分215.711→129.309，Web165.168→129.278。但质量存在评分与图交互，低NDC不能推出完整wall/Recall改善。原GP与GU层级/入口也不同，作用是完整图状态；旧E108同层级重建对照仍支持成本方向。原/重建GP第0层全部边相同；GP静态平均度较低只作解释线索。

混合索引所有非向量字节不变、全行W/ID核验；A/D全部旧结果恢复，smoke三内核一致，独立评分/前缀/同入口/整数分解均通过。295680真实NSG、33024ANN、4混合副本、0普通构图/GT/训练/正式QPS；搜索进程含加载327.357980秒，编译8.528秒，RSS约9.917GiB。完整负点保留。

[完整报告](../entry_method_exploration/20260920_until1900_theory_v1/stages/e115_score_topology_factorial/report.md) · [协议](../entry_method_exploration/20260920_until1900_theory_v1/stages/e115_score_topology_factorial/protocol.md) · [门](../entry_method_exploration/20260920_until1900_theory_v1/stages/e115_score_topology_factorial/results/gate.json)。
