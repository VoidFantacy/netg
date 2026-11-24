# E251 四集 GT10+B32、老 B64 与 Mixed64 正式复测

COCO、Flickr30k、WebVid 2.5M、Yandex first10M 各复用 E229 3,072 个公开查询身份、原 raw-IP 底库、图、GT10 三入口、B32 和老 B64。真 K1 与 K100 各自独立搜索、返回与评分。COCO 和 WebVid 直接复用 E245/E243 封存 Mixed64。Flickr30k 额外使用原 profile 的 4,096 个排重源组并重算 exact raw-IP GT100，Yandex 使用原 router_train 中与全部拟合、公开测试及 validation 精确字节隔离的 8,192 个查询。两个新表按同一个原生联合贪心编译器把原有序 B32 前缀扩到 64，使用 L176/192/208 的真实 K100 遗漏。Flickr 新增训练与原路由画像角色重用，与正式查询及原残差训练分离。

原 E229 的全网格及 46 个预先加密的 K/L 档，现为 155 个数据集/K/L 组合、三方法 465 点与 930 个 CPU15 单线程完整批次。每点两遍轮转并逆序，保留耗时及等价原生输出。全部计时后统一评分，核对历史对应载荷 231 组、标量排序 119,040 条。正式先后与训练隔离。结果按各法在同期固定召回门槛上的最快达标实点记录。

| 数据集 | K | 代表召回门槛 | 新版 QPS 对 B32 | 对老 B64 | 慢遍对老版快遍 |
|---|---:|---:|---:|---:|---:|
| COCO | 1 | 99% | +3.53% | −0.76% | −0.91% |
| COCO | 100 | 97% | +4.14% | +3.19% | +2.73% |
| Flickr30k | 1 | 99.5% | −2.61% | −0.60% | −0.84% |
| Flickr30k | 100 | 97.5% | +1.21% | −0.48% | −0.59% |
| WebVid | 1 | 84% | +15.65% | +6.43% | +5.75% |
| WebVid | 100 | 75.5% | +4.81% | +1.12% | +0.67% |
| Yandex | 1 | 92% | −2.43% | +0.65% | −0.40% |
| Yandex | 100 | 90% | −1.67% | +0.15% | −0.38% |

同 L 相对 B32 149/155 个比较召回提高，6 个持平。同期双方都达标的 63 个固定目标中，35 个均值更快，32 个慢遍仍更快。WebVid 两种 K 和 COCO K100 在主要门槛以更小 L 实现速度优势。Flickr30k K100 有相对 B32 的局部速度收益，对老 B64 候选质量提高但达标速度优势零散。Yandex K1 每个 L 只多一个正确查询，K100 同 L 增加 0.0257–0.0703 个百分点，B32 在两种 K 的 15 个双边达标固定目标均更快。已测前沿按各数据集、K、查询窗和召回门槛适用。

[完整报告](../entry_method_exploration/20261123_b64_four_dataset_retest_v1/report.md) · [协议](../entry_method_exploration/20261123_b64_four_dataset_retest_v1/protocol.md) · [逐点](../entry_method_exploration/20261123_b64_four_dataset_retest_v1/analysis/points.csv) · [两遍](../entry_method_exploration/20261123_b64_four_dataset_retest_v1/analysis/rounds.csv) · [固定目标](../entry_method_exploration/20261123_b64_four_dataset_retest_v1/analysis/targets.csv) · [封存](../entry_method_exploration/20261123_b64_four_dataset_retest_v1/seal.json)
