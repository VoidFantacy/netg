# P3 固定 2×2 pilot 证据

四个模型和全部八类预定对照均完整报告。每项区间是普通、未校正的 95% 配对查询 bootstrap，供开发阶段诊断；五轮计时不是五个 Recall 样本。本报告不自动通过 P3，不启动 P4，也不声称部署性能改善。

## webvid2_5m_light_v1

完整性核验：PASS。包含 count/plain 全结果、完整实际 route、五轮身份、固定 AB/BA 顺序，以及四格一致的 Fast 控制。

| 模型 | 方法 | L | Recall@10 | 平均 QPS | 图 / 总 NDC | 平均实际入口数 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| lambda0_frequency3 | fast | 64 | 0.656570 | 33172.64 | 922.03 / 1046.78 | 3.000 |
| lambda0_frequency3 | oracle_unified | 64 | 0.675350 | 31969.68 | 906.28 / 1031.03 | 13.945 |
| lambda0_frequency3 | oracle_probability | 64 | 0.740960 | 24899.26 | 1202.78 / 1327.53 | 13.945 |
| lambda0_frequency3 | fast | 128 | 0.746980 | 17509.25 | 1652.09 / 1776.84 | 3.000 |
| lambda0_frequency3 | oracle_unified | 128 | 0.759230 | 17608.49 | 1628.63 / 1753.38 | 13.945 |
| lambda0_frequency3 | oracle_probability | 128 | 0.821370 | 14232.13 | 1918.05 / 2042.80 | 13.945 |
| lambda1_frequency3 | fast | 64 | 0.656570 | 33013.12 | 922.03 / 1046.78 | 3.000 |
| lambda1_frequency3 | oracle_unified | 64 | 0.672030 | 31897.86 | 905.60 / 1030.34 | 13.956 |
| lambda1_frequency3 | oracle_probability | 64 | 0.731250 | 24906.70 | 1207.94 / 1332.69 | 13.956 |
| lambda1_frequency3 | fast | 128 | 0.746980 | 18230.66 | 1652.09 / 1776.84 | 3.000 |
| lambda1_frequency3 | oracle_unified | 128 | 0.756780 | 17852.20 | 1627.92 / 1752.66 | 13.956 |
| lambda1_frequency3 | oracle_probability | 128 | 0.812740 | 14879.42 | 1920.67 / 2045.42 | 13.956 |
| lambda0_greedy3 | fast | 64 | 0.656570 | 33174.65 | 922.03 / 1046.78 | 3.000 |
| lambda0_greedy3 | oracle_unified | 64 | 0.674490 | 33112.91 | 904.72 / 1029.47 | 13.954 |
| lambda0_greedy3 | oracle_probability | 64 | 0.741400 | 24081.45 | 1200.25 / 1324.99 | 13.954 |
| lambda0_greedy3 | fast | 128 | 0.746980 | 17476.26 | 1652.09 / 1776.84 | 3.000 |
| lambda0_greedy3 | oracle_unified | 128 | 0.758820 | 17611.64 | 1626.06 / 1750.80 | 13.954 |
| lambda0_greedy3 | oracle_probability | 128 | 0.821190 | 15054.20 | 1913.38 / 2038.13 | 13.954 |
| lambda1_greedy3 | fast | 64 | 0.656570 | 32898.96 | 922.03 / 1046.78 | 3.000 |
| lambda1_greedy3 | oracle_unified | 64 | 0.672100 | 31529.81 | 900.80 / 1025.55 | 13.978 |
| lambda1_greedy3 | oracle_probability | 64 | 0.732740 | 25354.93 | 1197.61 / 1322.36 | 13.978 |
| lambda1_greedy3 | fast | 128 | 0.746980 | 17422.41 | 1652.09 / 1776.84 | 3.000 |
| lambda1_greedy3 | oracle_unified | 128 | 0.756710 | 17931.63 | 1624.51 / 1749.26 | 13.978 |
| lambda1_greedy3 | oracle_probability | 128 | 0.813290 | 15156.11 | 1908.79 / 2033.53 | 13.978 |

除 Fast 外均为 oracle 诊断。原始五轮 QPS/wall、路由 wall、NDC/MAC 和计数器完整保存在 JSON/CSV。路由单独计时来自额外的一次 warmed batch，不能与图时间相加重建整体 QPS。

| 固定对照（候选减参考） | L | Recall 差 pp | 普通 95% 区间 pp | QPS 均值比 | 计时范围 |
| --- | ---: | ---: | --- | ---: | --- |
| structure_under_frequency3 | 64 | -0.9710 | [-1.1880, -0.7560] | 1.0003 | 跨模型固定顺序，仅描述 |
| structure_under_greedy3 | 64 | -0.8660 | [-1.0830, -0.6470] | 1.0529 | 跨模型固定顺序，仅描述 |
| portals_under_lambda0 | 64 | +0.0440 | [-0.1250, +0.2130] | 0.9672 | 跨模型固定顺序，仅描述 |
| portals_under_lambda1 | 64 | +0.1490 | [-0.0170, +0.3160] | 1.0180 | 跨模型固定顺序，仅描述 |
| protection_lambda0_frequency3 | 64 | +6.5610 | [+6.1820, +6.9390] | 0.7788 | 同模型 AB/BA |
| protection_lambda1_frequency3 | 64 | +5.9220 | [+5.5520, +6.2931] | 0.7808 | 同模型 AB/BA |
| protection_lambda0_greedy3 | 64 | +6.6910 | [+6.3150, +7.0700] | 0.7273 | 同模型 AB/BA |
| protection_lambda1_greedy3 | 64 | +6.0640 | [+5.6880, +6.4360] | 0.8042 | 同模型 AB/BA |
| structure_under_frequency3 | 128 | -0.8630 | [-1.0330, -0.6930] | 1.0455 | 跨模型固定顺序，仅描述 |
| structure_under_greedy3 | 128 | -0.7900 | [-0.9600, -0.6210] | 1.0068 | 跨模型固定顺序，仅描述 |
| portals_under_lambda0 | 128 | -0.0180 | [-0.1300, +0.0930] | 1.0578 | 跨模型固定顺序，仅描述 |
| portals_under_lambda1 | 128 | +0.0550 | [-0.0600, +0.1680] | 1.0186 | 跨模型固定顺序，仅描述 |
| protection_lambda0_frequency3 | 128 | +6.2140 | [+5.8880, +6.5420] | 0.8083 | 同模型 AB/BA |
| protection_lambda1_frequency3 | 128 | +5.5960 | [+5.2740, +5.9250] | 0.8335 | 同模型 AB/BA |
| protection_lambda0_greedy3 | 128 | +6.2370 | [+5.9200, +6.5590] | 0.8548 | 同模型 AB/BA |
| protection_lambda1_greedy3 | 128 | +5.6580 | [+5.3440, +5.9800] | 0.8452 | 同模型 AB/BA |

原始运行和模型绑定：[execution.json](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/eval_webvid/execution.json)。Bootstrap 差值样本：[NPZ](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/analysis_v1/bootstrap_webvid2_5m_light_v1.npz)。

## yandex_t2i_official10M_ip_v1

完整性核验：PASS。包含 count/plain 全结果、完整实际 route、五轮身份、固定 AB/BA 顺序，以及四格一致的 Fast 控制。

| 模型 | 方法 | L | Recall@10 | 平均 QPS | 图 / 总 NDC | 平均实际入口数 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| lambda0_frequency3 | fast | 64 | 0.828320 | 27145.85 | 1649.60 / 1768.92 | 3.000 |
| lambda0_frequency3 | oracle_unified | 64 | 0.841430 | 27485.06 | 1615.01 / 1734.32 | 13.999 |
| lambda0_frequency3 | oracle_probability | 64 | 0.879550 | 20051.26 | 2254.19 / 2373.50 | 13.999 |
| lambda0_frequency3 | fast | 128 | 0.896550 | 15533.64 | 2862.01 / 2981.32 | 3.000 |
| lambda0_frequency3 | oracle_unified | 128 | 0.904240 | 15271.52 | 2816.08 / 2935.40 | 13.999 |
| lambda0_frequency3 | oracle_probability | 128 | 0.939660 | 12402.54 | 3513.41 / 3632.73 | 13.999 |
| lambda1_frequency3 | fast | 64 | 0.828320 | 28261.57 | 1649.60 / 1768.92 | 3.000 |
| lambda1_frequency3 | oracle_unified | 64 | 0.840860 | 27794.04 | 1613.99 / 1733.30 | 13.999 |
| lambda1_frequency3 | oracle_probability | 64 | 0.879120 | 19688.40 | 2245.66 / 2364.98 | 13.999 |
| lambda1_frequency3 | fast | 128 | 0.896550 | 15695.69 | 2862.01 / 2981.32 | 3.000 |
| lambda1_frequency3 | oracle_unified | 128 | 0.903640 | 15489.01 | 2814.91 / 2934.22 | 13.999 |
| lambda1_frequency3 | oracle_probability | 128 | 0.940040 | 12050.86 | 3504.23 / 3623.55 | 13.999 |
| lambda0_greedy3 | fast | 64 | 0.828320 | 28263.28 | 1649.60 / 1768.92 | 3.000 |
| lambda0_greedy3 | oracle_unified | 64 | 0.841410 | 26424.54 | 1613.15 / 1732.47 | 13.999 |
| lambda0_greedy3 | oracle_probability | 64 | 0.879940 | 19858.06 | 2232.04 / 2351.35 | 13.999 |
| lambda0_greedy3 | fast | 128 | 0.896550 | 16237.32 | 2862.01 / 2981.32 | 3.000 |
| lambda0_greedy3 | oracle_unified | 128 | 0.904600 | 14954.45 | 2813.55 / 2932.86 | 13.999 |
| lambda0_greedy3 | oracle_probability | 128 | 0.939900 | 12036.24 | 3490.39 / 3609.71 | 13.999 |
| lambda1_greedy3 | fast | 64 | 0.828320 | 27698.88 | 1649.60 / 1768.92 | 3.000 |
| lambda1_greedy3 | oracle_unified | 64 | 0.841710 | 26658.55 | 1613.01 / 1732.32 | 13.999 |
| lambda1_greedy3 | oracle_probability | 64 | 0.878990 | 19741.67 | 2248.82 / 2368.13 | 13.999 |
| lambda1_greedy3 | fast | 128 | 0.896550 | 15586.53 | 2862.01 / 2981.32 | 3.000 |
| lambda1_greedy3 | oracle_unified | 128 | 0.905010 | 15098.72 | 2813.11 / 2932.43 | 13.999 |
| lambda1_greedy3 | oracle_probability | 128 | 0.939730 | 12122.99 | 3507.60 / 3626.91 | 13.999 |

除 Fast 外均为 oracle 诊断。原始五轮 QPS/wall、路由 wall、NDC/MAC 和计数器完整保存在 JSON/CSV。路由单独计时来自额外的一次 warmed batch，不能与图时间相加重建整体 QPS。

| 固定对照（候选减参考） | L | Recall 差 pp | 普通 95% 区间 pp | QPS 均值比 | 计时范围 |
| --- | ---: | ---: | --- | ---: | --- |
| structure_under_frequency3 | 64 | -0.0430 | [-0.1370, +0.0520] | 0.9819 | 跨模型固定顺序，仅描述 |
| structure_under_greedy3 | 64 | -0.0950 | [-0.2070, +0.0160] | 0.9941 | 跨模型固定顺序，仅描述 |
| portals_under_lambda0 | 64 | +0.0390 | [-0.0700, +0.1440] | 0.9904 | 跨模型固定顺序，仅描述 |
| portals_under_lambda1 | 64 | -0.0130 | [-0.1170, +0.0910] | 1.0027 | 跨模型固定顺序，仅描述 |
| protection_lambda0_frequency3 | 64 | +3.8120 | [+3.4680, +4.1610] | 0.7295 | 同模型 AB/BA |
| protection_lambda1_frequency3 | 64 | +3.8260 | [+3.4830, +4.1730] | 0.7084 | 同模型 AB/BA |
| protection_lambda0_greedy3 | 64 | +3.8530 | [+3.5120, +4.1940] | 0.7515 | 同模型 AB/BA |
| protection_lambda1_greedy3 | 64 | +3.7280 | [+3.3890, +4.0730] | 0.7405 | 同模型 AB/BA |
| structure_under_frequency3 | 128 | +0.0380 | [-0.0210, +0.0970] | 0.9716 | 跨模型固定顺序，仅描述 |
| structure_under_greedy3 | 128 | -0.0170 | [-0.0800, +0.0480] | 1.0072 | 跨模型固定顺序，仅描述 |
| portals_under_lambda0 | 128 | +0.0240 | [-0.0430, +0.0920] | 0.9705 | 跨模型固定顺序，仅描述 |
| portals_under_lambda1 | 128 | -0.0310 | [-0.0900, +0.0300] | 1.0060 | 跨模型固定顺序，仅描述 |
| protection_lambda0_frequency3 | 128 | +3.5420 | [+3.2650, +3.8290] | 0.8121 | 同模型 AB/BA |
| protection_lambda1_frequency3 | 128 | +3.6400 | [+3.3590, +3.9360] | 0.7780 | 同模型 AB/BA |
| protection_lambda0_greedy3 | 128 | +3.5300 | [+3.2450, +3.8190] | 0.8049 | 同模型 AB/BA |
| protection_lambda1_greedy3 | 128 | +3.4720 | [+3.2000, +3.7570] | 0.8029 | 同模型 AB/BA |

原始运行和模型绑定：[execution.json](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/eval_yandex/execution.json)。Bootstrap 差值样本：[NPZ](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/analysis_v1/bootstrap_yandex_t2i_official10M_ip_v1.npz)。

## 主对照与解释边界

主对照固定为 oracle_probability 下 λ1_greedy3 − λ0_greedy3；两个数据集的 L64/128 共四格都需普通 95% 下界大于零，才满足预定的搜索子条件。

当前四格下界均大于零：False。这只是搜索子条件的描述，结构目标、容量、完整重算和共同初始化仍由主控独立检查。P3 gate：REQUIRES_ROOT_STRUCTURE_AND_SEARCH_REVIEW。

同 L 的 Recall 改变不等于同成本收益。跨模型没有交错 ABBA 调度，只报告 QPS 均值比和双方原始轮次；不能把相同轮次编号当作跨模型配对证据。所有固定对照均展示，不选择最好模型或最有利工作点。

该分析不读取 query、GT、base 或图向量内容；读取既有评估行、JSON 元数据和小型模型/路由器 artifact，核验 checksum。原图 SHA 继承 P0，图本体不重复扫描。开发 pilot 曾用于研究，普通区间未经多重比较校正；不构造部署 frontier，不替代 P5/P6/P7 验收。
