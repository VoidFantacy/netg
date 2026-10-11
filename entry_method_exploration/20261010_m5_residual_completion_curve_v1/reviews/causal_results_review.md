# E176 独立结果解释：有监督补全、成本优化与因果边界

状态：实际独立整数、完整 wall、候选 trace 审计 PASS；160 点、480 批次、800 比较、60 机制、40 OPT 原包身份核验。此附件独立读取已保存 metrics/CSV、模型 manifest 和补充字段，不读取作者报告来决定结论。没有读取 raw/GT/返回/向量、重新搜索/拟合/距离计算或重算 bootstrap 端点。

主结论：M5RES12 比原 M5 提高 Recall，并在部分同 L 点同时更快；但对复用 R 分数的公平 M5OPT 基线，20 个同 L 点没有严格 Recall–QPS 双升。成本优化和新残差表的贡献必须分开。所有补全方法的跨 L 双升预算组合仍只有原 M5 已有的两个 Web K1 组合；保持 GT10 默认与原 M5 研究基线。

公共窗口是既有已曝光 public_test 前 10K 单角色，不能称为新确认或可靠默认替换。下面的统计均是事先冻结点及比较上的观察；跨 L 速度只按 round index 描述性配对。

## 两种速度口径

原端点为保存的 median_r(QPS_A,r / QPS_B,r)；曲线口径为保存的 median_r(QPS_A,r) / median_r(QPS_B,r)。二者通常不等。补充 interpretation 完整保留了全部 800 个原比较字段；本次逐字段检查一致，并核每个追加比值只取两个已保存点中位数，未改原 endpoint。

| 同 L 比较 | Recall 升/平/降 | paired QPS 升/降 | paired 严格双升 | 点中位数严格双升 | 两口径均双升 |
| --- | ---: | ---: | ---: | ---: | ---: |
| M5RES12−M5 | 14/6/0 | 10/10 | 9 | 8 | 8 |
| M5RES12−M5OPT | 14/6/0 | 2/18 | 0 | 0 | 0 |
| REGOPT96−M5OPT | 17/3/0 | 0/20 | 0 | 0 | 0 |
| M5RES12−WIDE12 | 1/5/14 | 15/5 | 0 | 0 | 0 |
| M5OPT−M5 | 0/20/0 | 12/8 | 0 | 0 | 0 |
| REGOPT96−M5REG96 | 0/20/0 | 19/1 | 0 | 0 | 0 |
| M5RES12−REGOPT96 | 5/3/12 | 19/1 | 5 | 5 | 5 |
| M5RES12−GT | 20/0/0 | 1/19 | 1 | 1 | 1 |

M5RES12−M5 的 9 个 paired 双升与 8 个点中位数双升之差，来自 Yandex K100 L800：Recall +0.0034 pp、paired QPS +0.125102%，但点中位数 QPS −0.294856%。应保留分歧，不能用曲线坐标替换冻结统计或反过来。

M5OPT 与原 M5 的最终返回身份相同，20 点 rescue=damage=0；REGOPT96 与原 REG96 同样如此。该身份还通过实际 native 全量未计时 word oracle/reference 检查。完整 timed output 未保留，固定 256 CountDC parity 不能扩写成所有 timed packet 再次核验。

K100 的 R 复用节省评分在完整 wall 中有可见收益，K1 的优化幅度很小且符号混合：M5OPT−M5 的 Web K100 五 L paired QPS 为 +2.620953/+1.464280/+0.763405/+0.618026/+0.550636%；Yandex 为 +1.112205/+0.607262/+0.341548/+0.084077/+0.329511%。不能把操作数减少当成任何 K/L 上必然更快的保证。

## 主补全的全部同 L 工作点

ΔR 与 rescue/damage 均相对原 M5；M5OPT 包身份相同，因此同样的质量差适用 M5OPT。QPS 列各给 paired / 点中位数百分比。

| 数据 | K | L | ΔR pp | rescue/damage | QPS % vs M5（paired / point） | QPS % vs M5OPT（paired / point） |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Web | 1 | 200 | 0.1100 | 11/0 | -0.280543 / -0.264863 | -0.175696 / -0.148832 |
| Web | 1 | 400 | 0.0500 | 5/0 | -0.138037 / -0.152916 | -0.115291 / -0.066243 |
| Web | 1 | 800 | 0.0100 | 1/0 | -0.050380 / -0.027147 | -0.034141 / -0.010904 |
| Web | 1 | 1000 | 0.0100 | 1/0 | -0.104955 / -0.052296 | -0.059734 / -0.048007 |
| Web | 1 | 1200 | 0.0000 | 0/0 | -0.162644 / -0.174737 | -0.133341 / -0.133341 |
| Web | 100 | 200 | 0.4168 | 4168/0 | +1.926020 / +1.887235 | -0.740166 / -0.699269 |
| Web | 100 | 400 | 0.2875 | 2875/0 | +1.066901 / +1.360893 | -0.374892 / -0.314645 |
| Web | 100 | 800 | 0.1904 | 1904/0 | +0.556825 / +0.553225 | -0.211113 / -0.208588 |
| Web | 100 | 1000 | 0.1679 | 1679/0 | +0.449944 / +0.440489 | -0.176633 / -0.176633 |
| Web | 100 | 1200 | 0.1543 | 1543/0 | +0.376863 / +0.376863 | -0.172821 / -0.172821 |
| Yandex | 1 | 200 | 0.0000 | 0/0 | -0.014290 / -0.034763 | -0.015665 / -0.048223 |
| Yandex | 1 | 400 | 0.0000 | 0/0 | -0.031621 / +0.030404 | +0.032057 / +0.032057 |
| Yandex | 1 | 800 | 0.0000 | 0/0 | -0.065172 / -0.015679 | -0.024551 / -0.003365 |
| Yandex | 1 | 1000 | 0.0000 | 0/0 | +0.012630 / +0.012630 | +0.010033 / +0.010033 |
| Yandex | 1 | 1200 | 0.0000 | 0/0 | -0.074670 / -0.074670 | -0.082154 / -0.060854 |
| Yandex | 100 | 200 | 0.0120 | 120/0 | +0.526754 / +0.529482 | -0.599532 / -0.599532 |
| Yandex | 100 | 400 | 0.0070 | 70/0 | +0.351643 / +0.351643 | -0.254076 / -0.254076 |
| Yandex | 100 | 800 | 0.0034 | 34/0 | +0.125102 / -0.294856 | -0.215709 / -0.467435 |
| Yandex | 100 | 1000 | 0.0027 | 27/0 | -0.097715 / -0.097715 | -0.127231 / -0.039235 |
| Yandex | 100 | 1200 | 0.0022 | 22/0 | +0.089398 / +0.180289 | -0.307502 / -0.148732 |

Web K100 是残差补全最明确的质量增益，但相对公平 M5OPT 五 L 均更慢。它相对原 M5 的同 L 双升不能全归因于小表：R 复用提供成本余量，补全又消耗其中一部分。本轮比较分离了是否优化与是否补全，仍不能仅凭 CountDC 把完整 wall 分摊为某一因果开销百分比。

REGOPT96−M5OPT 17 点 Recall 升、3 点平、20 点速度下降，两个速度口径均无双升。修剪 padding 与保存 C 行映射改善了旧 REG 的成本（对原 REG19/20点更快），但没有消除扩展相对公平直接补全的速度税。M5RES12−REGOPT96 在 Web K100 的五 L 双升，说明有监督小表在这些工作点比这一跳图扩展更有效；不等于所有区域方法失败。

## X 的有效密度和支持范围

以下密度 = 最终实际 new_rescues_vs_M5 / 已实际评分 X_total。它不是任意候选命中率、唯一 ID 比率、独立样本均值或 wall 因果份额；五 L 重复查询和 K 的事件被分别相加。所有这三方法对原 M5 的实际损伤总数均为0；这是本轮测量，不能从保留 C 的实现结构推出普遍单调性。

| 数据 | K | 方法 | 五 L X 事件 | 最终救回 | 救回 / X % |
| --- | ---: | --- | ---: | ---: | ---: |
| Web | 1 | M5REG96 | 595057 | 30 | 0.005042 |
| Web | 1 | WIDE12 | 180970 | 39 | 0.021551 |
| Web | 1 | M5RES12 | 72523 | 18 | 0.024820 |
| Web | 100 | M5REG96 | 634391 | 3499 | 0.551553 |
| Web | 100 | WIDE12 | 578279 | 13457 | 2.327077 |
| Web | 100 | M5RES12 | 567517 | 12169 | 2.144253 |
| Yandex | 1 | M5REG96 | 3066914 | 4 | 0.000130 |
| Yandex | 1 | WIDE12 | 2531 | 0 | 0.000000 |
| Yandex | 1 | M5RES12 | 562 | 0 | 0.000000 |
| Yandex | 100 | M5REG96 | 3111341 | 605 | 0.019445 |
| Yandex | 100 | WIDE12 | 598169 | 319 | 0.053329 |
| Yandex | 100 | M5RES12 | 525162 | 273 | 0.051984 |

M5RES12 的 Web K100 X_mean 随 L 为 11.2561/11.3318/11.3834/11.3952/11.3852，救回密度 3.702881/2.537108/1.672611/1.473427/1.355268%；Yandex K100 X_mean 为 11.6961/11.4317/10.4192/9.8016/9.1676，密度仅 0.102598/0.061233/0.032632/0.027547/0.023998%。这支持“本轮 Yandex 的静态残差支持转化成实际救回很少”，不能单独区分 teacher ID 支持、合法 route/key 命中、残差漂移或表容量哪个是唯一原因。

Yandex K1 的 M5RES12 五 L 只实际评分 217/115/98/69/63 个 X，全部救回0。对应 TRAIN manifest 的 L200 residual_members=14、pair 仅12行；这里不是实际打满12预算却毫无有效输出，首先存在稀疏可用支持。TRAIN 的 covered_residual_tokens 是编译整数目标覆盖，不能称为 TRAIN 或 test Recall。

| 方法 | 二十点 X 事件 | 救回vsM5 | 旧M5 U外真救回 | 旧TRAIN GT100 U外真救回 |
| --- | ---: | ---: | ---: | ---: |
| M5REG96 | 7407703 | 4138 | 3259 | 308 |
| WIDE12 | 1359949 | 13815 | 9414 | 0 |
| M5RES12 | 1165764 | 12460 | 8924 | 0 |

RES12 的救回中 8924 个事件在旧 M5 表支持 U 外，证明实际突破旧表固定 ID 支持；但其 X 及救回均未越过旧 TRAIN GT100 ID union。新表仍是 TRAIN 标签内的定向记忆，不是已证明全库支持或跨模态语义结构。原 REG 的308个教师 U 外真救回与大量教师 U 外候选 incidence 必须分开：例如 Yandex K100 L200 原 REG 有505574个教师 U外X，只真救126个。表外访问能力本身不足以保证双升。

## WIDE 控制与离线容量

WIDE12 同样使用 GT_K−原 M5_final_K 残差、support≥2、b4与整数联合 greedy；仅 key 从(route,Cwinner)改为route。它并非无监督控制。M5RES12−WIDE12 为1点质量升、5平、14降，严格双升0；Web K100 五 L 分别少救286/232/247/239/284个成员。当前结果不支持 winner 条件键的整体质量优势。

| 数据 | 十 KL PAIR 行 / bytes / 选中pair数 | 十 KL WIDE 行 / bytes / 选中pair数 |
| --- | ---: | ---: |
| Web | 26582 / 744296 / 101280 | 4847 / 135716 / 17964 |
| Yandex | 24020 / 672560 / 87986 | 4122 / 115416 / 16375 |

这只是十 KL 表存储清单的和，不是一个 KL 的固定容量，也不含旧表和全部 native resident 开销。PAIR 明显比 WIDE 大：Web K100 L200 为4938行/138264B vs769行/21532B；Yandex为5448行/152544B vs820行/22960B。同在线 cap≤12 不等于相同离线容量，实际评分 X 数也不相等。因此既不能把 PAIR 劣势全归因于条件键碎片化，也不能把任何局部优势当成等容量因果优势。

## 事先固定的跨 L 比较

每方法40个 smallL<bigL vsGT 比较；六方法合计240，未根据结果新选 L。每方法 paired 与 point 两口径均只有以下两个 Web K1 双升，全部都已由本次 fresh 原 M5 控制实现，没有新增预算组合。

| 方法 | small→big L | ΔR pp | paired QPS % | point QPS % | 原M5已有 |
| --- | --- | ---: | ---: | ---: | --- |
| M5 | 800→1000 | 0.2800 | +23.921026 | +23.861235 | 是 |
| M5 | 1000→1200 | 0.3500 | +19.076934 | +19.136994 | 是 |
| M5OPT | 800→1000 | 0.2800 | +23.919378 | +23.841115 | 是 |
| M5OPT | 1000→1200 | 0.3500 | +19.108092 | +19.131882 | 是 |
| M5REG96 | 800→1000 | 0.3000 | +23.632818 | +23.614367 | 是 |
| M5REG96 | 1000→1200 | 0.3700 | +18.934309 | +18.950153 | 是 |
| REGOPT96 | 800→1000 | 0.3000 | +23.691725 | +23.658052 | 是 |
| REGOPT96 | 1000→1200 | 0.3700 | +18.930047 | +18.990033 | 是 |
| WIDE12 | 800→1000 | 0.3000 | +23.785613 | +23.785613 | 是 |
| WIDE12 | 1000→1200 | 0.3800 | +19.091938 | +19.070855 | 是 |
| M5RES12 | 800→1000 | 0.2900 | +23.819823 | +23.827611 | 是 |
| M5RES12 | 1000→1200 | 0.3600 | +19.108287 | +19.074690 | 是 |

同 L M5RES12−GT 有一处小幅观察双升：Yandex K100 L1200，Recall +0.0064pp（救64损0），paired QPS +0.176726%，point QPS +0.082284%。该点 all_rounds_faster=false、speed_ranges_separated=false；它只是原 endpoint 上一次观察，不能当新确认。相同工作点 M5OPT−GT 的 paired QPS −0.002459%，但 point QPS +0.231360%，也说明微小速度符号受两种中位数定义影响。这里没有新加科学资格门。

## 费用与最终边界

新增 FIT 实际预算计时为 Web469.143609736s、Yandex472.986267977s，合计942.129877713s，各自低于授权900s。旧 TRAIN债21724.972836322s/15589.205719895s保留；原formal no_training不代表本轮0FIT。补充 ledger 的已计量不重叠区间小计15287.986158221s，不是完整活动总价；未计量行政/FIT budget后manifest哈希等保持null，完整supplement自身费用需另取实际外层收据。

本轮最稳妥的机制判断是：合法的原 R 分数复用确实减少重复评分；监督残差补全在 Web K100 对旧一跳扩展提高实际有效密度；不过相对同样优化的直接 M5 仍付速度税。WIDE结果并未支持必须用Cwinner条件键。Yandex 的低净救回与可用监督支持不足相符，但未识别唯一原因。不能扩展为跨模态 gap 已证、所有 region 失败、收益可普遍转移或已满足默认替换。

后续仍遵守原冻结 scope/stop 与用户授权边界；本附件不提出新调参、训练或实验，也不改变原结果或协议。

## 可复核键与绑定

`metrics.points` 用(dataset,K,L,method)查 qps_median/recall_pct/stats；`metrics.comparisons` 用(role,dataset,K,L,method,reference_L,reference)查原paired比值、rescue/damage、CI；`metrics.mechanisms` 查 X_total 与 new_rescues/new_damage 及 U 外字段。补充 interpretation 保留同一800键与全部原字段。

本次文件 SHA：

- [metrics.json](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/metrics.json)：`9e9d34ca9a4e388ed9f0fb352710f079f78a5128a63189e2cd5bce7e684b7baf`
- [points.csv](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/points.csv)：`ef3d93bd1196a2efe29989fa4fdd985cd07456a8116c345d9a804c27b28256e7`
- [comparisons.csv](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/comparisons.csv)：`e6ce1077e95e463d51788324b10fb40407f66e3924ece2ad82c9d2313e276aff`
- [report.json](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/independent_result_audit/report.json)：`34aa70872d64a97ca565bf9ceae1c93f7dd4eaa69c9c2b09acdaa43cddf60af3`
- [interpretation.json](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/interpretation.json)：`79459de3a7ad911e0f7f1337b2883dec07abbd5a4d4d70a5a8b2f3cd974e46af`
- [interpretation.csv](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/interpretation.csv)：`405ce18319f4cfaf9e3433d2ad5bb3beca18b0000fcf26a929c212a5fc695225`
- [cost_ledger_supplement.json](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/cost_ledger_supplement.json)：`bda053f482e57104f5cca7c2c240f3168350a75ef8a08fa08d4b48bbba442a2b`
- [compile_manifest.json](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/models/webvid2_5m_light_v1/compile_manifest.json)：`3b632b79324169a82a0e8c1f1434bef4a5e2141c9726ec4e09680f0b8ff80dd8`
- [compile_manifest.json](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/models/yandex_t2i_official10M_ip_v1/compile_manifest.json)：`3c16a3434e545caf29008ad13e4f987eff6005e72a4b14cddc8e8ce4f355146d`

独审本身范围：独立整数/member/trace/完整wall检查实际PASS；随机bootstrap端点仅核保存值与seed/count/scope、CSV身份，不独立重新生成。CountDC仅固定256；正常全量只有一次未计时plain/oracle，timed包未保留。
