# GT10机制分析：完整补测与辅助表

所有数据均为历史开发/validation，非盲测。真实shuffle每数据集一份、一个固定排列；没有按结果重选。QPS仅出自WebVid两硬画像的独立三次plain wall；其它补测为机制诊断，无QPS。

## WebVid三次硬画像计时

| L | repeat | GT1 Recall% | GT10 Recall% | GT1 QPS | GT10 QPS | 同轮ΔQPS% |
|---|---|---|---|---|---|---|
| 64 | 0 | 64.960 | 65.245 | 3890.76 | 3943.22 | 1.349 |
| 64 | 1 | 64.960 | 65.245 | 3889.94 | 3942.40 | 1.349 |
| 64 | 2 | 64.960 | 65.245 | 3890.30 | 3946.42 | 1.442 |
| 128 | 0 | 74.260 | 74.175 | 2143.83 | 2163.46 | 0.916 |
| 128 | 1 | 74.260 | 74.175 | 2144.54 | 2163.63 | 0.890 |
| 128 | 2 | 74.260 | 74.175 | 2148.19 | 2165.57 | 0.809 |
| 256 | 0 | 81.385 | 81.270 | 1155.01 | 1159.94 | 0.427 |
| 256 | 1 | 81.385 | 81.270 | 1154.99 | 1161.74 | 0.584 |
| 256 | 2 | 81.385 | 81.270 | 1157.20 | 1163.18 | 0.517 |
| 400 | 0 | 85.220 | 85.110 | 755.84 | 759.06 | 0.425 |
| 400 | 1 | 85.220 | 85.110 | 755.80 | 759.50 | 0.488 |
| 400 | 2 | 85.220 | 85.110 | 756.73 | 760.30 | 0.471 |
| 800 | 0 | 89.860 | 89.900 | 384.22 | 385.63 | 0.368 |
| 800 | 1 | 89.860 | 89.900 | 384.33 | 385.62 | 0.337 |
| 800 | 2 | 89.860 | 89.900 | 385.31 | 386.32 | 0.263 |

## 局部正点exact3与HNSW

两点为原WebVid L64和Yandex L128。backend_difference行是同画像exact−HNSW，不能当GT10相对GT1。

| 数据 | L | 比较 | baseline | ΔRecall pp | 正query | 负query | 正/负命中 | 描述性95% pp |
|---|---|---|---|---|---|---|---|---|
| webvid2_5m_light_v1 | 64 | gt10_hard | gt1_hard | 0.435 | 103 | 87 | 301/214 | [-0.060, 0.925] |
| webvid2_5m_light_v1 | 64 | gt1_hard_exact | gt1_hard_HNSW | 0.145 | 25 | 23 | 89/60 | [-0.145, 0.440] |
| webvid2_5m_light_v1 | 64 | gt10_hard_exact | gt10_hard_HNSW | 0.295 | 25 | 18 | 108/49 | [-0.010, 0.610] |
| yandex_t2i_official10M_ip_v1 | 128 | gt10_hard | gt1_hard | 0.310 | 33 | 20 | 120/58 | [0.000, 0.670] |
| yandex_t2i_official10M_ip_v1 | 128 | gt1_hard_exact | gt1_hard_HNSW | -0.015 | 3 | 5 | 19/22 | [-0.205, 0.170] |
| yandex_t2i_official10M_ip_v1 | 128 | gt10_hard_exact | gt10_hard_HNSW | -0.040 | 6 | 6 | 17/25 | [-0.210, 0.130] |

## 打乱第2–10名目标对应关系

下表差值为shuffle−baseline。负数代表原画像更好。每hub总质量固定；ESS、query的GT1/tail重合和画像方向没有匹配。

| 数据 | 段 | 后端 | baseline | ΔRecall pp | 正query | 负query | 净命中 | 描述性95% pp |
|---|---|---|---|---|---|---|---|---|
| webvid2_5m_light_v1 | cal | HNSW | gt1_hard | 0.518 | 70 | 57 | 53 | [-0.215, 1.260] |
| webvid2_5m_light_v1 | cal | HNSW | gt10_hard | -0.273 | 58 | 68 | -28 | [-0.996, 0.449] |
| webvid2_5m_light_v1 | cal | exact | gt1_hard | 0.283 | 60 | 43 | 29 | [-0.430, 0.977] |
| webvid2_5m_light_v1 | cal | exact | gt10_hard | -0.205 | 54 | 53 | -21 | [-0.889, 0.479] |
| webvid2_5m_light_v1 | audit | HNSW | gt1_hard | -0.479 | 67 | 82 | -49 | [-1.250, 0.264] |
| webvid2_5m_light_v1 | audit | HNSW | gt10_hard | -0.566 | 66 | 84 | -58 | [-1.299, 0.166] |
| webvid2_5m_light_v1 | audit | exact | gt1_hard | -0.469 | 59 | 73 | -48 | [-1.201, 0.312] |
| webvid2_5m_light_v1 | audit | exact | gt10_hard | -0.664 | 58 | 68 | -68 | [-1.377, 0.020] |
| yandex_t2i_official10M_ip_v1 | cal | HNSW | gt1_hard | -0.811 | 41 | 48 | -83 | [-1.699, 0.068] |
| yandex_t2i_official10M_ip_v1 | cal | HNSW | gt10_hard | -0.859 | 44 | 47 | -88 | [-1.778, 0.088] |
| yandex_t2i_official10M_ip_v1 | cal | exact | gt1_hard | -0.215 | 43 | 43 | -22 | [-1.143, 0.713] |
| yandex_t2i_official10M_ip_v1 | cal | exact | gt10_hard | -0.215 | 43 | 43 | -22 | [-1.133, 0.723] |
| yandex_t2i_official10M_ip_v1 | audit | HNSW | gt1_hard | -0.264 | 34 | 40 | -27 | [-1.036, 0.489] |
| yandex_t2i_official10M_ip_v1 | audit | HNSW | gt10_hard | -0.186 | 38 | 44 | -19 | [-1.065, 0.664] |
| yandex_t2i_official10M_ip_v1 | audit | exact | gt1_hard | -0.127 | 41 | 41 | -13 | [-0.879, 0.654] |
| yandex_t2i_official10M_ip_v1 | audit | exact | gt10_hard | 0.049 | 44 | 42 | 5 | [-0.742, 0.869] |

## shuffle支持与画像

| 数据 | 固定点/20K | mass最大误差 | 真实GT10 ESS中位 | shuffle ESS中位 | shuffle方向集中度中位 | 相对GT1角度中位° |
|---|---|---|---|---|---|---|
| webvid2_5m_light_v1 | 0 | 9.09e-13 | 67.361 | 77.358 | 0.646 | 24.17 |
| yandex_t2i_official10M_ip_v1 | 0 | 1.56e-13 | 60.082 | 70.251 | 0.420 | 42.19 |

## 分项成本（仅WebVid新重复）

NDC为全部query均值；wall微秒/query。route/graph分别独立预热和计时，不相加代替独立端到端wall。非L128分项未排测，留空。

| L | 画像 | route NDC | graph NDC | 总wall μs | route-only μs | graph-only μs |
|---|---|---|---|---|---|---|
| 64 | gt1_hard | 128.549 | 925.289 | 257.049 | 未测 | 未测 |
| 64 | gt10_hard | 118.317 | 914.265 | 253.600 | 未测 | 未测 |
| 128 | gt1_hard | 128.549 | 1658.169 | 466.300 | 6.964 | 450.165 |
| 128 | gt10_hard | 118.317 | 1646.149 | 462.185 | 6.597 | 446.603 |
| 256 | gt1_hard | 128.549 | 3024.938 | 865.796 | 未测 | 未测 |
| 256 | gt10_hard | 118.317 | 3009.849 | 860.778 | 未测 | 未测 |
| 400 | gt1_hard | 128.549 | 4489.208 | 1323.030 | 未测 | 未测 |
| 400 | gt10_hard | 118.317 | 4476.185 | 1316.663 | 未测 | 未测 |
| 800 | gt1_hard | 128.549 | 8337.665 | 2601.942 | 未测 | 未测 |
| 800 | gt10_hard | 118.317 | 8328.050 | 2593.146 | 未测 | 未测 |

## E24所有温度的原cal消融

原始选择已冻结。保留同温度GT1/GT10对照，不按本分析结果替换主画像。

| 数据 | 画像 | exact | Recall% | route NDC | graph NDC |
|---|---|---|---|---|---|
| webvid2_5m_light_v1 | gt1_hard | False | 74.5312 | 127.249 | 1657.158 |
| webvid2_5m_light_v1 | gt1_hard | True | 74.7363 | 815.000 | 1652.433 |
| webvid2_5m_light_v1 | gt1_soft_t0 | False | 74.8242 | 126.774 | 1649.438 |
| webvid2_5m_light_v1 | gt1_soft_t0 | True | 75.0586 | 815.000 | 1649.179 |
| webvid2_5m_light_v1 | gt1_soft_t1 | False | 75.1562 | 116.682 | 1654.741 |
| webvid2_5m_light_v1 | gt1_soft_t1 | True | 75.0879 | 815.000 | 1648.884 |
| webvid2_5m_light_v1 | gt1_soft_t2 | False | 75.1758 | 95.320 | 1665.048 |
| webvid2_5m_light_v1 | gt1_soft_t2 | True | 75.6934 | 815.000 | 1656.507 |
| webvid2_5m_light_v1 | gt10_hard | False | 75.3223 | 117.903 | 1651.391 |
| webvid2_5m_light_v1 | gt10_hard | True | 75.2246 | 815.000 | 1639.625 |
| webvid2_5m_light_v1 | gt10_soft_t0 | False | 75.3418 | 117.088 | 1651.149 |
| webvid2_5m_light_v1 | gt10_soft_t0 | True | 75.3418 | 815.000 | 1641.854 |
| webvid2_5m_light_v1 | gt10_soft_t1 | False | 75.3516 | 111.575 | 1645.975 |
| webvid2_5m_light_v1 | gt10_soft_t1 | True | 75.5469 | 815.000 | 1638.760 |
| webvid2_5m_light_v1 | gt10_soft_t2 | False | 75.2930 | 95.027 | 1659.626 |
| webvid2_5m_light_v1 | gt10_soft_t2 | True | 75.6152 | 815.000 | 1655.654 |
| yandex_t2i_official10M_ip_v1 | gt1_hard | False | 89.6875 | 111.107 | 2873.235 |
| yandex_t2i_official10M_ip_v1 | gt1_hard | True | 89.6484 | 821.000 | 2873.200 |
| yandex_t2i_official10M_ip_v1 | gt1_soft_t0 | False | 89.5117 | 108.673 | 2870.871 |
| yandex_t2i_official10M_ip_v1 | gt1_soft_t0 | True | 89.5703 | 821.000 | 2871.813 |
| yandex_t2i_official10M_ip_v1 | gt1_soft_t1 | False | 89.2871 | 100.915 | 2880.143 |
| yandex_t2i_official10M_ip_v1 | gt1_soft_t1 | True | 89.5215 | 821.000 | 2875.367 |
| yandex_t2i_official10M_ip_v1 | gt1_soft_t2 | False | 89.2090 | 90.109 | 2902.908 |
| yandex_t2i_official10M_ip_v1 | gt1_soft_t2 | True | 89.6777 | 821.000 | 2898.111 |
| yandex_t2i_official10M_ip_v1 | gt10_hard | False | 89.7363 | 106.991 | 2864.538 |
| yandex_t2i_official10M_ip_v1 | gt10_hard | True | 89.6484 | 821.000 | 2866.929 |
| yandex_t2i_official10M_ip_v1 | gt10_soft_t0 | False | 89.6973 | 106.063 | 2864.021 |
| yandex_t2i_official10M_ip_v1 | gt10_soft_t0 | True | 89.6387 | 821.000 | 2866.230 |
| yandex_t2i_official10M_ip_v1 | gt10_soft_t1 | False | 89.4238 | 97.226 | 2881.020 |
| yandex_t2i_official10M_ip_v1 | gt10_soft_t1 | True | 89.5215 | 821.000 | 2871.916 |
| yandex_t2i_official10M_ip_v1 | gt10_soft_t2 | False | 89.0820 | 88.705 | 2908.910 |
| yandex_t2i_official10M_ip_v1 | gt10_soft_t2 | True | 89.6289 | 821.000 | 2895.977 |

## 全量证据入口

- [已有A–C表](../existing_report.md)、[所有既有点](all_metrics.csv)、[所有配对](all_pairs.csv)、[按query分层](query_groups.csv)。
- [GT名次命中变化](GT_rank_hit_changes.csv)、[目标hub与入口的几何联系](target_region_links.csv)、[每hub入口频次](entry_frequencies.csv)、[舍入控制](numeric_control.csv)。
- [所有旧重复](repetition.csv)、[后来开发段](later_development.csv)、[旧实测前沿](hard_frontier.csv)、[新逐轮前沿](../supplement/results/repeat_frontier.csv)。
- [规则选取的正负案例](cases.json)、`*_paired.npz`保存全部query与row IDs，不按结果筛掉query。
- [新逐queryexact/HNSW](../supplement/results/analysis.json)、[补测执行与成本](../supplement/reviews/execution_complete.json)。
