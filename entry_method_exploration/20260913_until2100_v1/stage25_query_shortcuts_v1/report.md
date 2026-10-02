# E84 训练查询排名缺口补边

双集固定监督补边实验完成。双集未通过预锁质量门，停止固定首返回画像投票补边规则，不扫票数阈值、边数或依据辅助反馈改票。 原 compact 局部信号保留；整日目标未完成。

| 数据 | 主方法相对 | 净命中 | 救回 / 新增失败 | 两半净命中 | 路由 / 总 NDC变化 |
|---|---|---:|---|---|---|
| WebVid | baseline10 | -17 | 44 / 51 | [6, -23] | +4.75% / +0.15% |
| WebVid | compact10 | +42 | 9 / 5 | [22, 20] | +1.08% / -0.04% |
| WebVid | neighbor10 | +43 | 8 / 5 | [15, 28] | +0.65% / -0.06% |
| Yandex | baseline10 | +116 | 41 / 28 | [35, 81] | +20.43% / +0.73% |
| Yandex | compact10 | -4 | 0 / 0 | [-4, 0] | +0.18% / +0.01% |
| Yandex | neighbor10 | +4 | 0 / 0 | [4, 0] | +0.14% / +0.01% |

固定原 E73 compact 画像和图。以 P-fit20K 原查询的实际首返回 slot 为源，对未进入实际三入口的完整画像 per-hub max 前三入口投票；每源只追加最高票目标且至少2票。源是返回排名首位画像，并非记录的遍历路径。WebVid/Yandex 分别254/47条边，最高支持41/3票。对照在相同节点各追加一条最相近的其他 hub 非邻居；两臂节点度一致，边长不匹配，不能单凭此作语义因果归因。

新增图监督只读 fit20K raw query，不读 GT 或 NSG 命中。原画像仍有历史 GT 监督。fit namespace 为 router_train[10000:30000]，包含旧 train4096/monitor1024。aux128 只回归旧 compact 路由且不进入投票；全 fit20K 验证新 plain/count 一致，不声称存在旧全 fit 路由回归。完整 float64 排名与 E68 hub集合一致；Web55/Y20近tie保留，未声称 SIMD bit parity。

独立逐查询排名/全部票数、全部受影响节点控制排序、图的每条旧边与其顺序/未改字节、原图可达集合均通过。图 header、上层、入口、层级、W/labels 和原底层 NSG/base/rawIP 不变。在线使用原 E73 同 SHA evaluator、ef10、七 slot 去重三真实入口。

实际 129,536 NSG / 209,792 HNSW，其中训练路由80,512，查询129,280；2次图监督训练、4静态图边安装、0普通 HNSW build/梯度更新/画像训练/新GT。编译 12.744s、图监督阶段 4.989s、边安装/核验 0.105s、查询 native 操作 111.272s。阶段耗时有包含关系，不能简单相加或当 QPS；继承画像与 GT 成本未知。

全部 ANN 串行 CPU15，实测进程及数值库1线程。集合/mask 64,640行、历史 P/compact 全字段31,808行、原 kernel 256行、完整7slot/距离/三入口及同三入口返回56,131行核验。失败严格 GT10 零命中；并集413条，状态变化173条，全 GT/入口/返回 ID 保留。

aux7952及固定两半是已暴露的选择训练反馈；cal/audit 有历史暴露。E34历史 validation2000 最终对照与 held-out 均未打开，不把辅助结果作为最终性能结论。此阶段未计正式 QPS，最近完整开发 wall 仍为 E74。

补充资源检查纳入 E82/E83/E84 全部输出；原 frozen common.py 累计列表漏掉 E83，未改原封存，实际未超192MiB。协议 A 的旧输出回归措辞已在独立补充中明确，仅 aux128 有旧路由逐字段回归。

[协议](protocol.md) · [措辞/资源补充](reviews/protocol_clarification.md) · [配对](results/paired.csv) · [原值](results/points.csv) · [收益保留](results/gain_retention.json) · [门](results/gate.json) · [完整失败查询](results/failure_queries.csv) · [三指标图](figures/query_shortcuts.png) · [失败图](figures/failure_queries.png) · [训练核验](reviews/training_independent.json) · [查询核验](reviews/verification.json) · [成本](results/cost.json)
