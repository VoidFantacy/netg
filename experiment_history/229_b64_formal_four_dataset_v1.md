# E229 四集 B32 与全精算 B64 正式比较

E228 确认 COCO/WebVid K100 的降低主搜索 L 条件收益后，用户授权正式跑测。E229 冻结 E213 的发布 SPAN4、原底库及主图、GT10 路由和原版四集 B32。沿用 COCO/WebVid B64 逐字节原表，Flickr30k/Yandex 用 E226 原编译器从 E183 冻结 token 延伸到 64，保留原有序 B32 前缀并核真实训练覆盖。K1/K100 共用从 K100/L200 token 生成的表，在线分别主搜并返回真实 K。仅做 B32/B64 同期对照。

每集 3,072 条历史公开查询。COCO/WebVid 用 E228 隔离窗，Flickr30k/Yandex 用 E213 前窗。源身份或精确向量核验与画像拟合角色分离。共 109 个数据集/K/L 组合、218 点、436 个完整 CPU15 单线程批次，每点两遍。全部计时结束后绑定行读取封存 GT100，K1 用真值首名，K100 用全部真值集。两遍实际包位级匹配，55,808 条额外原生标量 Top-K 复核。COCO/WebVid 共有配置与 E228、Flickr30k/Yandex 的 B32 与 E213 共 53 份载荷组全匹配。

按双边都达标的预设目标，B64 均值更快数量为 COCO K1/K100 3/5、2/7，Flickr30k 1/5、4/7，WebVid 4/7、9/13，Yandex 0/7、0/8。B64 慢遍仍快为 K1 共 8/24、K100 共 12/35。B64 的 109 个同 L 配对均未丢失 B32 正确成员。Yandex K1 召回持平，K100 同 L 召回增加 0.0146–0.0374 个百分点，速度中位数分别下降 1.74%、2.05%。WebVid K100 的 72% 目标 L168→160、平均 QPS +0.46%，重复区间重叠。75.5% 目标 L224→208、+2.97%，慢遍对快遍仍高 2.72%。COCO K100 97.0% 目标在本轮网格 +0.20%，两遍交叠，E228 的更细网格包含本轮未测的 B64 L204。按数据集、真实 K 与目标召回保留 B64 条件配置，通用基线为原版 B32。

[报告和四集曲线](../entry_method_exploration/20261122_b64_formal_four_dataset_v1/report.md) · [协议](../entry_method_exploration/20261122_b64_formal_four_dataset_v1/protocol.md) · [逐点](../entry_method_exploration/20261122_b64_formal_four_dataset_v1/analysis/points.csv) · [预设目标](../entry_method_exploration/20261122_b64_formal_four_dataset_v1/analysis/targets.csv) · [封存](../entry_method_exploration/20261122_b64_formal_four_dataset_v1/seal.json) · [修改前快照](../entry_method_exploration/20261122_b64_formal_four_dataset_v1/source_before/)
