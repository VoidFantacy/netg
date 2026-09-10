# P2/P3 measurement tables — preparation only

Values below are copied from three checksum-bound completed analysis JSON files. No raw data, count rows, GT, labels, search or new statistics were used. This is a report ingredient, not the final overnight report.

QPS uses the source **mean of five round QPS values**. Recall remains a fraction; paired Recall deltas and their pointwise 95% bootstrap intervals remain percentage points. Markdown prints round-trip float values, without rounding or recomputing means/CIs. CSV/JSON retain every original measurement/comparison field and all five round values.

**Semantics:** Fast expanded/rejected/evicted are unmeasured and shown as null. Missing P2 counters are unavailable in the bound analysis. Oracle methods are GT diagnostics and cannot be deployed. P3 cross-model QPS/wall comparisons are descriptive fixed-order results, without paired timing inference. Instrumented routing/graph times are not pure wall latency; routing-only batches are separate descriptive batches. All intervals are exploratory and unadjusted. Historical reused exact-GT time is null/unknown, never zero. P3 frequency/greedy probe-cost pointers are shared per lambda and must not be summed twice.

Nested bootstrap invocation status is copied as source metadata; top-level COMPLETE is the completion status. Analysis gate flags below do not replace the separately managed gate files.

Coverage: 72 measurement rows; 60 fixed-comparison rows; 6 full cost records; 2 full structure records.

## Bound sources

| Source | SHA256 | Path |
| --- | --- | --- |
| P2 | e73a8d8c16a5bebb2404596b63d621b1780b1aab0f9eb29efce5281edfc04c1f | /data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/analysis_v1/analysis.json |
| P3 | 63da6a71425b0dbd6e186db1c608a564b9847c58168b6b56059a9ed2d2f901ae | /data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/analysis_v1/analysis.json |
| P3_structure | 8b0cec717a14382c5917504e560bcffd732146c517ea9a699b0bb1812463088e | /data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/structure_analysis_v1/analysis.json |

## All measurements

### P2: webvid2_5m_light_v1

| Model | Method | L | Recall fraction | QPS mean of five | Routing NDC | Graph NDC | Total NDC | Expanded | Rejected | Evicted | Oracle only |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P2_fixed_model | fast | 64 | 0.6565700000000001 | 32079.80418746254 | 124.7466 | 922.0306 | 1046.7772 | null | null | null | false |
| P2_fixed_model | geom_unified | 64 | 0.6536 | 28779.082506143204 | 188.7466 | 943.3102 | 1132.0568 | null | null | null | false |
| P2_fixed_model | geom_uniform | 64 | 0.59924 | 19547.96347949596 | 188.7466 | 1504.8988 | 1693.6454 | null | null | null | false |
| P2_fixed_model | geom_probability | 64 | 0.59929 | 19573.596983232965 | 188.7466 | 1504.8829 | 1693.6295 | null | null | null | false |
| P2_fixed_model | oracle_unified | 64 | 0.65941 | 30699.093263273746 | 124.7466 | 939.8859 | 1064.6325 | null | null | null | true |
| P2_fixed_model | oracle_probability | 64 | 0.7135400000000001 | 21352.257175200542 | 124.7466 | 1348.9154 | 1473.662 | null | null | null | true |
| P2_fixed_model | fast | 128 | 0.74698 | 17421.79853835503 | 124.7466 | 1652.0904 | 1776.837 | null | null | null | false |
| P2_fixed_model | geom_unified | 128 | 0.74282 | 16530.43902595604 | 188.7466 | 1669.1984 | 1857.945 | null | null | null | false |
| P2_fixed_model | geom_uniform | 128 | 0.70624 | 11632.304166239619 | 188.7466 | 2395.3711 | 2584.1177 | null | null | null | false |
| P2_fixed_model | geom_probability | 128 | 0.70642 | 12003.522174689399 | 188.7466 | 2394.3111 | 2583.0577 | null | null | null | false |
| P2_fixed_model | oracle_unified | 128 | 0.74829 | 16995.31679946392 | 124.7466 | 1667.132 | 1791.8786 | null | null | null | true |
| P2_fixed_model | oracle_probability | 128 | 0.80081 | 13744.240797041663 | 124.7466 | 2084.2423 | 2208.9889 | null | null | null | true |


### P2: yandex_t2i_official10M_ip_v1

| Model | Method | L | Recall fraction | QPS mean of five | Routing NDC | Graph NDC | Total NDC | Expanded | Rejected | Evicted | Oracle only |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P2_fixed_model | fast | 64 | 0.8283200000000001 | 27390.685431392845 | 119.3133 | 1649.6048 | 1768.9181 | null | null | null | false |
| P2_fixed_model | geom_unified | 64 | 0.8251900000000001 | 25327.738680943927 | 183.3133 | 1661.4363 | 1844.7496 | null | null | null | false |
| P2_fixed_model | geom_uniform | 64 | 0.75337 | 16123.879597626667 | 183.3133 | 2684.4897 | 2867.803 | null | null | null | false |
| P2_fixed_model | geom_probability | 64 | 0.7565200000000001 | 16508.936039661567 | 183.3133 | 2681.2101 | 2864.5234 | null | null | null | false |
| P2_fixed_model | oracle_unified | 64 | 0.8309300000000001 | 26677.789904101526 | 119.3133 | 1649.5918 | 1768.9051 | null | null | null | true |
| P2_fixed_model | oracle_probability | 64 | 0.8624800000000001 | 19062.904348596825 | 119.3133 | 2352.7171 | 2472.0304 | null | null | null | true |
| P2_fixed_model | fast | 128 | 0.89655 | 15947.72775718172 | 119.3133 | 2862.0093 | 2981.3226 | null | null | null | false |
| P2_fixed_model | geom_unified | 128 | 0.8946200000000001 | 14633.794052562507 | 183.3133 | 2874.9728 | 3058.2861 | null | null | null | false |
| P2_fixed_model | geom_uniform | 128 | 0.8554299999999999 | 9924.228648751703 | 183.3133 | 4221.596 | 4404.9093 | null | null | null | false |
| P2_fixed_model | geom_probability | 128 | 0.85974 | 10033.053629463746 | 183.3133 | 4214.951 | 4398.2643 | null | null | null | false |
| P2_fixed_model | oracle_unified | 128 | 0.8982400000000001 | 14984.612786406758 | 119.3133 | 2856.2593 | 2975.5726 | null | null | null | true |
| P2_fixed_model | oracle_probability | 128 | 0.9318300000000002 | 11779.953242675456 | 119.3133 | 3635.6719 | 3754.9852 | null | null | null | true |


### P3: webvid2_5m_light_v1

| Model | Method | L | Recall fraction | QPS mean of five | Routing NDC | Graph NDC | Total NDC | Expanded | Rejected | Evicted | Oracle only |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lambda0_frequency3 | fast | 64 | 0.6565699999999917 | 33172.64488724012 | 124.7466 | 922.0306 | 1046.7772 | null | null | null | false |
| lambda0_frequency3 | oracle_unified | 64 | 0.6753499999999905 | 31969.684880103225 | 124.7466 | 906.2807 | 1031.0273 | 71.3477 | 680.1161 | 154.8169 | true |
| lambda0_frequency3 | oracle_probability | 64 | 0.7409599999999869 | 24899.2615895584 | 124.7466 | 1202.7815 | 1327.5281 | 86.8705 | 932.4015 | 183.5095 | true |
| lambda0_frequency3 | fast | 128 | 0.7469799999999859 | 17509.254543569947 | 124.7466 | 1652.0904 | 1776.837 | null | null | null | false |
| lambda0_frequency3 | oracle_unified | 128 | 0.7592299999999826 | 17608.488399091275 | 124.7466 | 1628.6286 | 1753.3752 | 135.9246 | 1229.8949 | 262.8091 | true |
| lambda0_frequency3 | oracle_probability | 128 | 0.8213699999999795 | 14232.130560847716 | 124.7466 | 1918.0531 | 2042.7997 | 150.1627 | 1463.0358 | 304.8546 | true |
| lambda1_frequency3 | fast | 64 | 0.6565699999999917 | 33013.12258296322 | 124.7466 | 922.0306 | 1046.7772 | null | null | null | false |
| lambda1_frequency3 | oracle_unified | 64 | 0.6720299999999918 | 31897.862972333598 | 124.7466 | 905.5982 | 1030.3448 | 71.369 | 679.7894 | 154.4398 | true |
| lambda1_frequency3 | oracle_probability | 64 | 0.7312499999999889 | 24906.696853010333 | 124.7466 | 1207.939 | 1332.6856 | 87.5262 | 937.6061 | 182.8067 | true |
| lambda1_frequency3 | fast | 128 | 0.7469799999999859 | 18230.655095515034 | 124.7466 | 1652.0904 | 1776.837 | null | null | null | false |
| lambda1_frequency3 | oracle_unified | 128 | 0.7567799999999839 | 17852.199480626674 | 124.7466 | 1627.9175 | 1752.6641 | 136.0038 | 1229.2395 | 262.6742 | true |
| lambda1_frequency3 | oracle_probability | 128 | 0.8127399999999823 | 14879.415594322374 | 124.7466 | 1920.6702 | 2045.4168 | 150.9131 | 1465.7417 | 304.0154 | true |
| lambda0_greedy3 | fast | 64 | 0.6565699999999917 | 33174.649600779536 | 124.7466 | 922.0306 | 1046.7772 | null | null | null | false |
| lambda0_greedy3 | oracle_unified | 64 | 0.6744899999999915 | 33112.907294307646 | 124.7466 | 904.7234 | 1029.47 | 71.2568 | 679.5937 | 153.8729 | true |
| lambda0_greedy3 | oracle_probability | 64 | 0.741399999999988 | 24081.446141338474 | 124.7466 | 1200.2483 | 1324.9949 | 86.3491 | 929.2884 | 184.6108 | true |
| lambda0_greedy3 | fast | 128 | 0.7469799999999859 | 17476.257694280637 | 124.7466 | 1652.0904 | 1776.837 | null | null | null | false |
| lambda0_greedy3 | oracle_unified | 128 | 0.7588199999999825 | 17611.635425967565 | 124.7466 | 1626.0572 | 1750.8038 | 135.7554 | 1228.6222 | 261.6796 | true |
| lambda0_greedy3 | oracle_probability | 128 | 0.8211899999999809 | 15054.200331304362 | 124.7466 | 1913.379 | 2038.1256 | 149.5498 | 1457.6744 | 306.1548 | true |
| lambda1_greedy3 | fast | 64 | 0.6565699999999917 | 32898.95964894056 | 124.7466 | 922.0306 | 1046.7772 | null | null | null | false |
| lambda1_greedy3 | oracle_unified | 64 | 0.6720999999999921 | 31529.811576338012 | 124.7466 | 900.8019 | 1025.5485 | 71.1884 | 676.4317 | 153.1818 | true |
| lambda1_greedy3 | oracle_probability | 64 | 0.7327399999999882 | 25354.93105197521 | 124.7466 | 1197.6123 | 1322.3589 | 87.0751 | 928.3915 | 182.1457 | true |
| lambda1_greedy3 | fast | 128 | 0.7469799999999859 | 17422.414802948457 | 124.7466 | 1652.0904 | 1776.837 | null | null | null | false |
| lambda1_greedy3 | oracle_unified | 128 | 0.7567099999999841 | 17931.632801040436 | 124.7466 | 1624.5128 | 1749.2594 | 135.8798 | 1228.031 | 260.602 | true |
| lambda1_greedy3 | oracle_probability | 128 | 0.8132899999999826 | 15156.108668252919 | 124.7466 | 1908.7853 | 2033.5319 | 150.3758 | 1456.0291 | 302.3804 | true |


### P3: yandex_t2i_official10M_ip_v1

| Model | Method | L | Recall fraction | QPS mean of five | Routing NDC | Graph NDC | Total NDC | Expanded | Rejected | Evicted | Oracle only |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lambda0_frequency3 | fast | 64 | 0.828319999999981 | 27145.849461704238 | 119.3133 | 1649.6048 | 1768.9181 | null | null | null | false |
| lambda0_frequency3 | oracle_unified | 64 | 0.8414299999999788 | 27485.0580046178 | 119.3133 | 1615.0096 | 1734.3229 | 69.7037 | 1332.3569 | 212.949 | true |
| lambda0_frequency3 | oracle_probability | 64 | 0.8795499999999696 | 20051.262059946697 | 119.3133 | 2254.1904 | 2373.5037 | 85.7077 | 1897.9047 | 270.578 | true |
| lambda0_frequency3 | fast | 128 | 0.8965499999999774 | 15533.638719079556 | 119.3133 | 2862.0093 | 2981.3226 | null | null | null | false |
| lambda0_frequency3 | oracle_unified | 128 | 0.9042399999999765 | 15271.524876480908 | 119.3133 | 2816.0843 | 2935.3976 | 133.3678 | 2353.2817 | 329.4348 | true |
| lambda0_frequency3 | oracle_probability | 128 | 0.9396599999999711 | 12402.54394041363 | 119.3133 | 3513.4123 | 3632.7256 | 147.7541 | 2941.6041 | 424.0541 | true |
| lambda1_frequency3 | fast | 64 | 0.828319999999981 | 28261.566897260036 | 119.3133 | 1649.6048 | 1768.9181 | null | null | null | false |
| lambda1_frequency3 | oracle_unified | 64 | 0.8408599999999781 | 27794.04284034003 | 119.3133 | 1613.9887 | 1733.302 | 69.7391 | 1331.6159 | 212.6337 | true |
| lambda1_frequency3 | oracle_probability | 64 | 0.8791199999999695 | 19688.397188754163 | 119.3133 | 2245.6644 | 2364.9777 | 86.1242 | 1889.8464 | 269.6938 | true |
| lambda1_frequency3 | fast | 128 | 0.8965499999999774 | 15695.685373229437 | 119.3133 | 2862.0093 | 2981.3226 | null | null | null | false |
| lambda1_frequency3 | oracle_unified | 128 | 0.9036399999999772 | 15489.013734946779 | 119.3133 | 2814.9062 | 2934.2195 | 133.3912 | 2352.4651 | 329.0499 | true |
| lambda1_frequency3 | oracle_probability | 128 | 0.9400399999999703 | 12050.858786177689 | 119.3133 | 3504.2338 | 3623.5471 | 148.1487 | 2932.9888 | 423.0963 | true |
| lambda0_greedy3 | fast | 64 | 0.828319999999981 | 28263.276340746197 | 119.3133 | 1649.6048 | 1768.9181 | null | null | null | false |
| lambda0_greedy3 | oracle_unified | 64 | 0.841409999999978 | 26424.54464647395 | 119.3133 | 1613.1536 | 1732.4669 | 69.6549 | 1332.0468 | 211.4519 | true |
| lambda0_greedy3 | oracle_probability | 64 | 0.8799399999999694 | 19858.059656381352 | 119.3133 | 2232.0376 | 2351.3509 | 85.8904 | 1875.7719 | 270.3753 | true |
| lambda0_greedy3 | fast | 128 | 0.8965499999999774 | 16237.318824414406 | 119.3133 | 2862.0093 | 2981.3226 | null | null | null | false |
| lambda0_greedy3 | oracle_unified | 128 | 0.9045999999999758 | 14954.446690600875 | 119.3133 | 2813.5488 | 2932.8621 | 133.3413 | 2352.8242 | 327.3833 | true |
| lambda0_greedy3 | oracle_probability | 128 | 0.93989999999997 | 12036.244816938744 | 119.3133 | 3490.3924 | 3609.7057 | 147.8882 | 2918.6036 | 423.9006 | true |
| lambda1_greedy3 | fast | 64 | 0.828319999999981 | 27698.88205721983 | 119.3133 | 1649.6048 | 1768.9181 | null | null | null | false |
| lambda1_greedy3 | oracle_unified | 64 | 0.8417099999999788 | 26658.552553833528 | 119.3133 | 1613.0108 | 1732.3241 | 69.7223 | 1331.0231 | 212.2654 | true |
| lambda1_greedy3 | oracle_probability | 64 | 0.8789899999999696 | 19741.67147733025 | 119.3133 | 2248.8166 | 2368.1299 | 86.3242 | 1892.1797 | 270.3127 | true |
| lambda1_greedy3 | fast | 128 | 0.8965499999999774 | 15586.52585457388 | 119.3133 | 2862.0093 | 2981.3226 | null | null | null | false |
| lambda1_greedy3 | oracle_unified | 128 | 0.9050099999999757 | 15098.721732015192 | 119.3133 | 2813.1121 | 2932.4254 | 133.3765 | 2351.3841 | 328.3515 | true |
| lambda1_greedy3 | oracle_probability | 128 | 0.9397299999999699 | 12122.992443969542 | 119.3133 | 3507.6008 | 3626.9141 | 148.3403 | 2935.3108 | 423.9497 | true |


## All fixed comparisons

Every Recall/NDC delta is candidate minus reference. The displayed QPS ratio is the stored ratio of mean candidate QPS to mean reference QPS; no QPS interval is available. Same-model timing-pair details and all saved flags remain in JSON/CSV.

### P2: webvid2_5m_light_v1

| Contrast | L | Candidate | Reference | Recall delta pp | Saved 95% CI pp | QPS ratio of means | Graph NDC delta | Total NDC delta | Improved/harmed/equal | P3 cross-model wall descriptive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| uniform_protection | 64 | geom_uniform | geom_unified | -5.436000000000001 | [-5.884025000000001,-4.984] | 0.6792420667101962 | 561.5885999999999 | 561.5886 | 1907/4874/3219 | false |
| probability_protection | 64 | geom_probability | geom_unified | -5.431 | [-5.878025000000001,-4.9799999999999995] | 0.6801327658397299 | 561.5727 | 561.5726999999999 | 1908/4872/3220 | false |
| oracle_protection | 64 | oracle_probability | oracle_unified | 5.412999999999999 | [5.009975,5.826] | 0.6955338059038015 | 409.0295000000001 | 409.0295000000001 | 3283/2172/4545 | false |
| oracle_selection_unified | 64 | oracle_unified | geom_unified | 0.581 | [0.35400000000000004,0.8049999999999999] | 1.0667154957674796 | -3.4243000000000166 | -67.42430000000013 | 605/362/9033 | false |
| oracle_selection_protected | 64 | oracle_probability | geom_probability | 11.425 | [11.070975000000002,11.785] | 1.0908703798025066 | -155.96749999999997 | -219.96749999999997 | 5694/808/3498 | false |
| geometric_bundle_vs_fast | 64 | geom_unified | fast | -0.29700000000000004 | [-0.61,0.013999999999999941] | 0.8971090452413257 | 21.27959999999996 | 85.27960000000007 | 874/900/8226 | false |
| oracle_bundle_vs_fast | 64 | oracle_unified | fast | 0.284 | [-0.03399999999999997,0.6010249999999997] | 0.9569601199520911 | 17.855299999999943 | 17.855299999999943 | 1052/844/8104 | false |
| uniform_protection | 128 | geom_uniform | geom_unified | -3.6579999999999995 | [-4.032,-3.27] | 0.7036899714505231 | 726.1726999999998 | 726.1726999999998 | 1702/4183/4115 | false |
| probability_protection | 128 | geom_probability | geom_unified | -3.64 | [-4.0169999999999995,-3.254] | 0.7261466048083484 | 725.1126999999999 | 725.1126999999999 | 1699/4171/4130 | false |
| oracle_protection | 128 | oracle_probability | oracle_unified | 5.252000000000001 | [4.917000000000001,5.596025] | 0.808707537447916 | 417.1102999999998 | 417.1102999999998 | 2943/1395/5662 | false |
| oracle_selection_unified | 128 | oracle_unified | geom_unified | 0.547 | [0.36300000000000004,0.7290000000000001] | 1.0281225303682455 | -2.0663999999999305 | -66.06639999999993 | 473/244/9283 | false |
| oracle_selection_protected | 128 | oracle_probability | geom_probability | 9.439 | [9.13,9.746025000000001] | 1.1450173205013725 | -310.0688 | -374.0688 | 5092/679/4229 | false |
| geometric_bundle_vs_fast | 128 | geom_unified | fast | -0.41600000000000004 | [-0.6640000000000001,-0.177] | 0.9488365388661444 | 17.107999999999947 | 81.10799999999995 | 552/646/8802 | false |
| oracle_bundle_vs_fast | 128 | oracle_unified | fast | 0.13099999999999995 | [-0.11,0.372] | 0.9755202232449085 | 15.041600000000017 | 15.041600000000017 | 734/592/8674 | false |


### P2: yandex_t2i_official10M_ip_v1

| Contrast | L | Candidate | Reference | Recall delta pp | Saved 95% CI pp | QPS ratio of means | Graph NDC delta | Total NDC delta | Improved/harmed/equal | P3 cross-model wall descriptive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| uniform_protection | 64 | geom_uniform | geom_unified | -7.182000000000001 | [-7.6240000000000006,-6.731000000000001] | 0.6366095213134026 | 1023.0534 | 1023.0533999999998 | 1321/5377/3302 | false |
| probability_protection | 64 | geom_probability | geom_unified | -6.866999999999999 | [-7.309,-6.421] | 0.6518124751532813 | 1019.7737999999997 | 1019.7737999999999 | 1325/5299/3376 | false |
| oracle_protection | 64 | oracle_probability | oracle_unified | 3.1550000000000002 | [2.7710000000000004,3.54] | 0.7145608544456689 | 703.1252999999999 | 703.1253000000002 | 2134/2217/5649 | false |
| oracle_selection_unified | 64 | oracle_unified | geom_unified | 0.5740000000000001 | [0.38297499999999995,0.771] | 1.0533032672266691 | -11.844500000000153 | -75.84450000000015 | 211/125/9664 | false |
| oracle_selection_protected | 64 | oracle_probability | geom_probability | 10.595999999999998 | [10.279,10.919] | 1.1547021747979112 | -328.49299999999994 | -392.49299999999994 | 5556/567/3877 | false |
| geometric_bundle_vs_fast | 64 | geom_unified | fast | -0.31299999999999994 | [-0.578025,-0.05] | 0.9246843692314268 | 11.831500000000005 | 75.8315 | 431/461/9108 | false |
| oracle_bundle_vs_fast | 64 | oracle_unified | fast | 0.261 | [-0.0030000000000000074,0.528] | 0.9739730672648936 | -0.013000000000147338 | -0.013000000000147338 | 487/431/9082 | false |
| uniform_protection | 128 | geom_uniform | geom_unified | -3.9189999999999996 | [-4.289,-3.542975] | 0.678171950015511 | 1346.6231999999995 | 1346.6232000000005 | 1078/3975/4947 | false |
| probability_protection | 128 | geom_probability | geom_unified | -3.4879999999999995 | [-3.852025,-3.115] | 0.6856085027181907 | 1339.9782 | 1339.9782 | 1097/3851/5052 | false |
| oracle_protection | 128 | oracle_probability | oracle_unified | 3.359 | [3.045,3.6769999999999996] | 0.7861366463444155 | 779.4125999999997 | 779.4126000000001 | 1687/1088/7225 | false |
| oracle_selection_unified | 128 | oracle_unified | geom_unified | 0.36200000000000004 | [0.19300000000000006,0.5369999999999999] | 1.0239731905877696 | -18.71349999999984 | -82.71349999999984 | 136/88/9776 | false |
| oracle_selection_protected | 128 | oracle_probability | geom_probability | 7.209000000000001 | [6.938999999999999,7.487025] | 1.174114449870142 | -579.2791000000002 | -643.2790999999997 | 4169/424/5407 | false |
| geometric_bundle_vs_fast | 128 | geom_unified | fast | -0.19299999999999998 | [-0.404,0.011999999999999993] | 0.9176099739959813 | 12.96349999999984 | 76.96349999999984 | 224/246/9530 | false |
| oracle_bundle_vs_fast | 128 | oracle_unified | fast | 0.16900000000000004 | [-0.04799999999999998,0.38800000000000007] | 0.9396080127878254 | -5.75 | -5.75 | 264/238/9498 | false |


### P3: webvid2_5m_light_v1

| Contrast | L | Candidate | Reference | Recall delta pp | Saved 95% CI pp | QPS ratio of means | Graph NDC delta | Total NDC delta | Improved/harmed/equal | P3 cross-model wall descriptive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| structure_under_frequency3 | 64 | lambda1_frequency3/oracle_probability | lambda0_frequency3/oracle_probability | -0.971 | [-1.1880000000000002,-0.7559750000000004] | 1.000298613813313 | 5.157500000000027 | 5.157500000000027 | 1578/2183/6239 | true |
| structure_under_greedy3 | 64 | lambda1_greedy3/oracle_probability | lambda0_greedy3/oracle_probability | -0.8660000000000001 | [-1.083,-0.6469999999999999] | 1.0528824100995604 | -2.6359999999999673 | -2.6359999999999673 | 1661/2249/6090 | true |
| portals_under_lambda0 | 64 | lambda0_greedy3/oracle_probability | lambda0_frequency3/oracle_probability | 0.04399999999999993 | [-0.12500000000000006,0.21299999999999994] | 0.9671550320768195 | -2.533200000000079 | -2.533200000000079 | 1199/1168/7633 | true |
| portals_under_lambda1 | 64 | lambda1_greedy3/oracle_probability | lambda1_frequency3/oracle_probability | 0.14899999999999997 | [-0.016999999999999967,0.31599999999999995] | 1.0179965332862155 | -10.326700000000073 | -10.326700000000073 | 1166/1115/7719 | true |
| protection_lambda0_frequency3 | 64 | lambda0_frequency3/oracle_probability | lambda0_frequency3/oracle_unified | 6.561 | [6.182,6.939000000000001] | 0.7788397565674724 | 296.5008 | 296.5008 | 3669/1712/4619 | false |
| protection_lambda1_frequency3 | 64 | lambda1_frequency3/oracle_probability | lambda1_frequency3/oracle_unified | 5.922 | [5.5520000000000005,6.29305] | 0.780826504728953 | 302.34080000000006 | 302.34079999999994 | 3447/1835/4718 | false |
| protection_lambda0_greedy3 | 64 | lambda0_greedy3/oracle_probability | lambda0_greedy3/oracle_unified | 6.691000000000001 | [6.314974999999999,7.07] | 0.7272525461839545 | 295.5249 | 295.5248999999999 | 3759/1701/4540 | false |
| protection_lambda1_greedy3 | 64 | lambda1_greedy3/oracle_probability | lambda1_greedy3/oracle_unified | 6.064000000000001 | [5.687974999999999,6.436] | 0.8041573921425897 | 296.81039999999996 | 296.81039999999985 | 3484/1805/4711 | false |
| structure_under_frequency3 | 128 | lambda1_frequency3/oracle_probability | lambda0_frequency3/oracle_probability | -0.8630000000000001 | [-1.033,-0.693] | 1.0454805435284107 | 2.6170999999999367 | 2.6170999999999367 | 1150/1720/7130 | true |
| structure_under_greedy3 | 128 | lambda1_greedy3/oracle_probability | lambda0_greedy3/oracle_probability | -0.79 | [-0.96,-0.621] | 1.0067694287777373 | -4.593699999999899 | -4.593700000000126 | 1210/1745/7045 | true |
| portals_under_lambda0 | 128 | lambda0_greedy3/oracle_probability | lambda0_frequency3/oracle_probability | -0.017999999999999978 | [-0.12999999999999998,0.09300000000000003] | 1.0577615394225053 | -4.67410000000018 | -4.674099999999953 | 678/724/8598 | true |
| portals_under_lambda1 | 128 | lambda1_greedy3/oracle_probability | lambda1_frequency3/oracle_probability | 0.055 | [-0.06,0.16802499999999967] | 1.0185956949838892 | -11.884900000000016 | -11.884900000000016 | 660/647/8693 | true |
| protection_lambda0_frequency3 | 128 | lambda0_frequency3/oracle_probability | lambda0_frequency3/oracle_unified | 6.214 | [5.887974999999999,6.542000000000001] | 0.8082539646947887 | 289.4245000000001 | 289.4245000000001 | 3371/1133/5496 | false |
| protection_lambda1_frequency3 | 128 | lambda1_frequency3/oracle_probability | lambda1_frequency3/oracle_unified | 5.596 | [5.273974999999999,5.925] | 0.8334780042352549 | 292.7527 | 292.7527 | 3126/1224/5650 | false |
| protection_lambda0_greedy3 | 128 | lambda0_greedy3/oracle_probability | lambda0_greedy3/oracle_unified | 6.237 | [5.92,6.559025] | 0.8547871885371656 | 287.32179999999994 | 287.32180000000017 | 3411/1109/5480 | false |
| protection_lambda1_greedy3 | 128 | lambda1_greedy3/oracle_probability | lambda1_greedy3/oracle_unified | 5.6579999999999995 | [5.343999999999999,5.9799999999999995] | 0.8452163189162297 | 284.27250000000004 | 284.27250000000004 | 3156/1223/5621 | false |


### P3: yandex_t2i_official10M_ip_v1

| Contrast | L | Candidate | Reference | Recall delta pp | Saved 95% CI pp | QPS ratio of means | Graph NDC delta | Total NDC delta | Improved/harmed/equal | P3 cross-model wall descriptive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| structure_under_frequency3 | 64 | lambda1_frequency3/oracle_probability | lambda0_frequency3/oracle_probability | -0.043 | [-0.13699999999999996,0.052] | 0.981903140555059 | -8.52599999999984 | -8.526000000000295 | 547/586/8867 | true |
| structure_under_greedy3 | 64 | lambda1_greedy3/oracle_probability | lambda0_greedy3/oracle_probability | -0.095 | [-0.20700000000000002,0.015999999999999997] | 0.9941389953970804 | 16.778999999999996 | 16.778999999999996 | 748/791/8461 | true |
| portals_under_lambda0 | 64 | lambda0_greedy3/oracle_probability | lambda0_frequency3/oracle_probability | 0.03900000000000001 | [-0.06999999999999999,0.14400000000000002] | 0.9903645764048301 | -22.152799999999843 | -22.152800000000298 | 688/652/8660 | true |
| portals_under_lambda1 | 64 | lambda1_greedy3/oracle_probability | lambda1_frequency3/oracle_probability | -0.013000000000000001 | [-0.117,0.09102499999999966] | 1.0027058722995752 | 3.1521999999999935 | 3.1521999999999935 | 645/626/8729 | true |
| protection_lambda0_frequency3 | 64 | lambda0_frequency3/oracle_probability | lambda0_frequency3/oracle_unified | 3.8120000000000003 | [3.468000000000001,4.161] | 0.7295331906004294 | 639.1807999999999 | 639.1808000000003 | 2471/1763/5766 | false |
| protection_lambda1_frequency3 | 64 | lambda1_frequency3/oracle_probability | lambda1_frequency3/oracle_unified | 3.826 | [3.4829749999999993,4.173] | 0.7083675196822607 | 631.6757 | 631.6757 | 2439/1764/5797 | false |
| protection_lambda0_greedy3 | 64 | lambda0_greedy3/oracle_probability | lambda0_greedy3/oracle_unified | 3.853 | [3.512,4.194] | 0.7515005432281378 | 618.884 | 618.884 | 2453/1747/5800 | false |
| protection_lambda1_greedy3 | 64 | lambda1_greedy3/oracle_probability | lambda1_greedy3/oracle_unified | 3.728 | [3.3889749999999994,4.073025] | 0.7405380107364972 | 635.8058000000001 | 635.8057999999999 | 2432/1778/5790 | false |
| structure_under_frequency3 | 128 | lambda1_frequency3/oracle_probability | lambda0_frequency3/oracle_probability | 0.038 | [-0.021000000000000005,0.09699999999999999] | 0.9716441114076623 | -9.178499999999985 | -9.17850000000044 | 297/282/9421 | true |
| structure_under_greedy3 | 128 | lambda1_greedy3/oracle_probability | lambda0_greedy3/oracle_probability | -0.017000000000000008 | [-0.08,0.04799999999999998] | 1.00720720028133 | 17.208399999999983 | 17.208399999999983 | 334/365/9301 | true |
| portals_under_lambda0 | 128 | lambda0_greedy3/oracle_probability | lambda0_frequency3/oracle_probability | 0.024000000000000004 | [-0.04299999999999999,0.092] | 0.9704658072380375 | -23.01989999999978 | -23.019900000000234 | 290/268/9442 | true |
| portals_under_lambda1 | 128 | lambda1_greedy3/oracle_probability | lambda1_frequency3/oracle_probability | -0.03099999999999999 | [-0.09000000000000002,0.029999999999999992] | 1.005985769070217 | 3.367000000000189 | 3.367000000000189 | 258/284/9458 | true |
| protection_lambda0_frequency3 | 128 | lambda0_frequency3/oracle_probability | lambda0_frequency3/oracle_unified | 3.5420000000000007 | [3.2649999999999997,3.8290000000000006] | 0.812135267481659 | 697.328 | 697.3280000000004 | 1899/847/7254 | false |
| protection_lambda1_frequency3 | 128 | lambda1_frequency3/oracle_probability | lambda1_frequency3/oracle_unified | 3.6399999999999997 | [3.3589999999999995,3.9360249999999994] | 0.7780262186086244 | 689.3276000000001 | 689.3275999999996 | 1904/837/7259 | false |
| protection_lambda0_greedy3 | 128 | lambda0_greedy3/oracle_probability | lambda0_greedy3/oracle_unified | 3.53 | [3.244975,3.819] | 0.8048605920340557 | 676.8436000000002 | 676.8436000000002 | 1905/859/7236 | false |
| protection_lambda1_greedy3 | 128 | lambda1_greedy3/oracle_probability | lambda1_greedy3/oracle_unified | 3.472 | [3.2,3.7570000000000006] | 0.8029151513047664 | 694.4887000000003 | 694.4886999999999 | 1885/851/7264 | false |


## Costs and structure

The following cost cells preserve the source field names and numeric values exactly. Thread-seconds are not wall-seconds; phase subtotals and repeated shared pointers are not additive training totals. Unknown full initializer and exact-GT times remain null. No cost cells are fetched from outside the three sources.

### P2: webvid2_5m_light_v1 cost

| Source cost field | Value |
| --- | --- |
| /model/initialization_validation_seconds | 0.01612643499902333 |
| /model/total_model_command_work_seconds | 0.22929895199922612 |
| /model/load_seconds | 0.1081544849985221 |
| /model/profile_and_portal_compute_seconds | 0.10035995600264869 |
| /model/post_existing_partition_and_GT_wall_seconds | 0.21317295400149305 |
| /model/exact_GT_seconds | null |
| /model/exact_GT_reason | Audited existing GT reused; this task did not compute exact GT |
| /paired_fast20k/exact_train_GT_seconds | null |
| /paired_fast20k/exact_train_GT_reason | Compatible preexisting exact GT reused; historical compute time unavailable in this invocation |
| /paired_fast20k/qgt_hub_seconds | null |
| /paired_fast20k/qgt_hub_reason | Audited independent 5K QGT raw hubs reused |
| /paired_fast20k/prototype_seconds | 0.18310917299822904 |
| /paired_fast20k/router_index_seconds | null |
| /paired_fast20k/router_index_reason | Measured separately by evaluator during index initialization |
| /count_peak_rss_kib | 6166472 |
| /timing_peak_rss_kib | 6020724 |
| /index_bytes | 5791560103 |
| /router_index_build_seconds | 0.0526557 |
| /routing_only_plain/0/batch_wall_us | 10075.414 |
| /routing_only_plain/0/method | fast |
| /routing_only_plain/0/num_queries | 10000 |
| /routing_only_plain/1/batch_wall_us | 27203.774 |
| /routing_only_plain/1/method | geom_unified |
| /routing_only_plain/1/num_queries | 10000 |
| /routing_only_plain/2/batch_wall_us | 27005.382 |
| /routing_only_plain/2/method | geom_uniform |
| /routing_only_plain/2/num_queries | 10000 |
| /routing_only_plain/3/batch_wall_us | 27129.614 |
| /routing_only_plain/3/method | geom_probability |
| /routing_only_plain/3/num_queries | 10000 |
| /routing_only_plain/4/batch_wall_us | 9975.773 |
| /routing_only_plain/4/method | oracle_unified |
| /routing_only_plain/4/num_queries | 10000 |
| /routing_only_plain/5/batch_wall_us | 9960.724 |
| /routing_only_plain/5/method | oracle_probability |
| /routing_only_plain/5/num_queries | 10000 |
| /partition | null |
| /partition_reason | Read the checksum-bound model partition_report separately; this analysis does not invent missing offline timings |


### P2: yandex_t2i_official10M_ip_v1 cost

| Source cost field | Value |
| --- | --- |
| /model/initialization_validation_seconds | 0.058827602999372175 |
| /model/total_model_command_work_seconds | 0.18144935300006182 |
| /model/load_seconds | 0.05576302299959934 |
| /model/profile_and_portal_compute_seconds | 0.052214855000784155 |
| /model/post_existing_partition_and_GT_wall_seconds | 0.1226220819989976 |
| /model/exact_GT_seconds | null |
| /model/exact_GT_reason | Audited existing GT reused; this task did not compute exact GT |
| /paired_fast20k/exact_train_GT_seconds | null |
| /paired_fast20k/exact_train_GT_reason | Compatible preexisting exact GT reused; historical compute time unavailable in this invocation |
| /paired_fast20k/qgt_hub_seconds | null |
| /paired_fast20k/qgt_hub_reason | Audited independent 5K QGT raw hubs reused |
| /paired_fast20k/prototype_seconds | 0.06592642900068313 |
| /paired_fast20k/router_index_seconds | null |
| /paired_fast20k/router_index_reason | Measured separately by evaluator during index initialization |
| /count_peak_rss_kib | 11052300 |
| /timing_peak_rss_kib | 10906596 |
| /index_bytes | 10640000103 |
| /router_index_build_seconds | 0.044810059 |
| /routing_only_plain/0/batch_wall_us | 10416.432 |
| /routing_only_plain/0/method | fast |
| /routing_only_plain/0/num_queries | 10000 |
| /routing_only_plain/1/batch_wall_us | 13009.89 |
| /routing_only_plain/1/method | geom_unified |
| /routing_only_plain/1/num_queries | 10000 |
| /routing_only_plain/2/batch_wall_us | 13003.998 |
| /routing_only_plain/2/method | geom_uniform |
| /routing_only_plain/2/num_queries | 10000 |
| /routing_only_plain/3/batch_wall_us | 13205.38 |
| /routing_only_plain/3/method | geom_probability |
| /routing_only_plain/3/num_queries | 10000 |
| /routing_only_plain/4/batch_wall_us | 10406.418 |
| /routing_only_plain/4/method | oracle_unified |
| /routing_only_plain/4/num_queries | 10000 |
| /routing_only_plain/5/batch_wall_us | 10353.309 |
| /routing_only_plain/5/method | oracle_probability |
| /routing_only_plain/5/num_queries | 10000 |
| /partition | null |
| /partition_reason | Read the checksum-bound model partition_report separately; this analysis does not invent missing offline timings |


### P3: webvid2_5m_light_v1 cost

| Source cost field | Value |
| --- | --- |
| /lambda0_frequency3/count_peak_rss_kib | 6007936 |
| /lambda0_frequency3/timing_peak_rss_kib | 5929700 |
| /lambda0_frequency3/count_router_index_build_seconds | 0.04881893 |
| /lambda0_frequency3/timing_router_index_build_seconds | 0.048506912 |
| /lambda0_frequency3/portal_probe_cost_seconds/GT_score_thread_seconds_sum | 0.10458690899999996 |
| /lambda0_frequency3/portal_probe_cost_seconds/artifact_write_before_final_manifest | 0.8663284479999999 |
| /lambda0_frequency3/portal_probe_cost_seconds/greedy_wall | 0.0034006949999999996 |
| /lambda0_frequency3/portal_probe_cost_seconds/independent_candidate_query_verification | 0.128980327 |
| /lambda0_frequency3/portal_probe_cost_seconds/index_load | 4.135857275 |
| /lambda0_frequency3/portal_probe_cost_seconds/input_read_hash_validation | 0.434673326 |
| /lambda0_frequency3/portal_probe_cost_seconds/probe_and_score_batch_wall | 3.6996703790000014 |
| /lambda0_frequency3/portal_probe_cost_seconds/probe_thread_seconds_sum | 53.840721617999996 |
| /lambda0_frequency3/portal_probe_cost_seconds/program_wall_before_final_manifest | 9.343434265 |
| /lambda0_frequency3/portal_probe_cost_seconds/upstream/candidate_query_selection | 0.24840296099864645 |
| /lambda0_frequency3/portal_probe_cost_seconds/upstream/fit_extraction | 0.1577927729995281 |
| /lambda0_frequency3/portal_probe_cost_seconds/workspace_allocation | 0.012043474 |
| /lambda0_frequency3/probe_cost_shared_between_portal_rules | true |
| /lambda1_frequency3/count_peak_rss_kib | 6007892 |
| /lambda1_frequency3/timing_peak_rss_kib | 5929712 |
| /lambda1_frequency3/count_router_index_build_seconds | 0.048585534 |
| /lambda1_frequency3/timing_router_index_build_seconds | 0.04855919 |
| /lambda1_frequency3/portal_probe_cost_seconds/GT_score_thread_seconds_sum | 0.08208817900000001 |
| /lambda1_frequency3/portal_probe_cost_seconds/artifact_write_before_final_manifest | 0.841145867 |
| /lambda1_frequency3/portal_probe_cost_seconds/greedy_wall | 0.002648021999999998 |
| /lambda1_frequency3/portal_probe_cost_seconds/independent_candidate_query_verification | 0.10551065 |
| /lambda1_frequency3/portal_probe_cost_seconds/index_load | 4.136462816 |
| /lambda1_frequency3/portal_probe_cost_seconds/input_read_hash_validation | 0.431122181 |
| /lambda1_frequency3/portal_probe_cost_seconds/probe_and_score_batch_wall | 2.8509801979999985 |
| /lambda1_frequency3/portal_probe_cost_seconds/probe_thread_seconds_sum | 38.547307334 |
| /lambda1_frequency3/portal_probe_cost_seconds/program_wall_before_final_manifest | 8.432664678 |
| /lambda1_frequency3/portal_probe_cost_seconds/upstream/candidate_query_selection | 0.2153762860034476 |
| /lambda1_frequency3/portal_probe_cost_seconds/upstream/fit_extraction | 0.1577927729995281 |
| /lambda1_frequency3/portal_probe_cost_seconds/workspace_allocation | 0.011940488 |
| /lambda1_frequency3/probe_cost_shared_between_portal_rules | true |
| /lambda0_greedy3/count_peak_rss_kib | 6007856 |
| /lambda0_greedy3/timing_peak_rss_kib | 5929752 |
| /lambda0_greedy3/count_router_index_build_seconds | 0.04892824 |
| /lambda0_greedy3/timing_router_index_build_seconds | 0.04859584 |
| /lambda0_greedy3/portal_probe_cost_seconds/GT_score_thread_seconds_sum | 0.10458690899999996 |
| /lambda0_greedy3/portal_probe_cost_seconds/artifact_write_before_final_manifest | 0.8663284479999999 |
| /lambda0_greedy3/portal_probe_cost_seconds/greedy_wall | 0.0034006949999999996 |
| /lambda0_greedy3/portal_probe_cost_seconds/independent_candidate_query_verification | 0.128980327 |
| /lambda0_greedy3/portal_probe_cost_seconds/index_load | 4.135857275 |
| /lambda0_greedy3/portal_probe_cost_seconds/input_read_hash_validation | 0.434673326 |
| /lambda0_greedy3/portal_probe_cost_seconds/probe_and_score_batch_wall | 3.6996703790000014 |
| /lambda0_greedy3/portal_probe_cost_seconds/probe_thread_seconds_sum | 53.840721617999996 |
| /lambda0_greedy3/portal_probe_cost_seconds/program_wall_before_final_manifest | 9.343434265 |
| /lambda0_greedy3/portal_probe_cost_seconds/upstream/candidate_query_selection | 0.24840296099864645 |
| /lambda0_greedy3/portal_probe_cost_seconds/upstream/fit_extraction | 0.1577927729995281 |
| /lambda0_greedy3/portal_probe_cost_seconds/workspace_allocation | 0.012043474 |
| /lambda0_greedy3/probe_cost_shared_between_portal_rules | true |
| /lambda1_greedy3/count_peak_rss_kib | 6007852 |
| /lambda1_greedy3/timing_peak_rss_kib | 5929728 |
| /lambda1_greedy3/count_router_index_build_seconds | 0.048812376 |
| /lambda1_greedy3/timing_router_index_build_seconds | 0.04873477 |
| /lambda1_greedy3/portal_probe_cost_seconds/GT_score_thread_seconds_sum | 0.08208817900000001 |
| /lambda1_greedy3/portal_probe_cost_seconds/artifact_write_before_final_manifest | 0.841145867 |
| /lambda1_greedy3/portal_probe_cost_seconds/greedy_wall | 0.002648021999999998 |
| /lambda1_greedy3/portal_probe_cost_seconds/independent_candidate_query_verification | 0.10551065 |
| /lambda1_greedy3/portal_probe_cost_seconds/index_load | 4.136462816 |
| /lambda1_greedy3/portal_probe_cost_seconds/input_read_hash_validation | 0.431122181 |
| /lambda1_greedy3/portal_probe_cost_seconds/probe_and_score_batch_wall | 2.8509801979999985 |
| /lambda1_greedy3/portal_probe_cost_seconds/probe_thread_seconds_sum | 38.547307334 |
| /lambda1_greedy3/portal_probe_cost_seconds/program_wall_before_final_manifest | 8.432664678 |
| /lambda1_greedy3/portal_probe_cost_seconds/upstream/candidate_query_selection | 0.2153762860034476 |
| /lambda1_greedy3/portal_probe_cost_seconds/upstream/fit_extraction | 0.1577927729995281 |
| /lambda1_greedy3/portal_probe_cost_seconds/workspace_allocation | 0.011940488 |
| /lambda1_greedy3/probe_cost_shared_between_portal_rules | true |


### P3: yandex_t2i_official10M_ip_v1 cost

| Source cost field | Value |
| --- | --- |
| /lambda0_frequency3/count_peak_rss_kib | 10894192 |
| /lambda0_frequency3/timing_peak_rss_kib | 10815824 |
| /lambda0_frequency3/count_router_index_build_seconds | 0.043963368 |
| /lambda0_frequency3/timing_router_index_build_seconds | 0.043587691 |
| /lambda0_frequency3/portal_probe_cost_seconds/GT_score_thread_seconds_sum | 0.10037696199999994 |
| /lambda0_frequency3/portal_probe_cost_seconds/artifact_write_before_final_manifest | 0.8807343040000007 |
| /lambda0_frequency3/portal_probe_cost_seconds/greedy_wall | 0.003503128999999999 |
| /lambda0_frequency3/portal_probe_cost_seconds/independent_candidate_query_verification | 0.217526164 |
| /lambda0_frequency3/portal_probe_cost_seconds/index_load | 10.972568193 |
| /lambda0_frequency3/portal_probe_cost_seconds/input_read_hash_validation | 0.284887994 |
| /lambda0_frequency3/portal_probe_cost_seconds/probe_and_score_batch_wall | 4.669691774000004 |
| /lambda0_frequency3/portal_probe_cost_seconds/probe_thread_seconds_sum | 67.37036810899998 |
| /lambda0_frequency3/portal_probe_cost_seconds/program_wall_before_final_manifest | 17.143767482 |
| /lambda0_frequency3/portal_probe_cost_seconds/upstream/candidate_query_selection | 0.2580252740008291 |
| /lambda0_frequency3/portal_probe_cost_seconds/upstream/fit_extraction | 0.06746959200245328 |
| /lambda0_frequency3/portal_probe_cost_seconds/workspace_allocation | 0.050013607 |
| /lambda0_frequency3/probe_cost_shared_between_portal_rules | true |
| /lambda1_frequency3/count_peak_rss_kib | 10894332 |
| /lambda1_frequency3/timing_peak_rss_kib | 10815880 |
| /lambda1_frequency3/count_router_index_build_seconds | 0.043871347 |
| /lambda1_frequency3/timing_router_index_build_seconds | 0.043703007 |
| /lambda1_frequency3/portal_probe_cost_seconds/GT_score_thread_seconds_sum | 0.09314120599999995 |
| /lambda1_frequency3/portal_probe_cost_seconds/artifact_write_before_final_manifest | 0.8553921030000006 |
| /lambda1_frequency3/portal_probe_cost_seconds/greedy_wall | 0.0031431039999999986 |
| /lambda1_frequency3/portal_probe_cost_seconds/independent_candidate_query_verification | 0.220239356 |
| /lambda1_frequency3/portal_probe_cost_seconds/index_load | 10.976583615 |
| /lambda1_frequency3/portal_probe_cost_seconds/input_read_hash_validation | 0.283341902 |
| /lambda1_frequency3/portal_probe_cost_seconds/probe_and_score_batch_wall | 4.093215366 |
| /lambda1_frequency3/portal_probe_cost_seconds/probe_thread_seconds_sum | 57.818941125000016 |
| /lambda1_frequency3/portal_probe_cost_seconds/program_wall_before_final_manifest | 16.541720277 |
| /lambda1_frequency3/portal_probe_cost_seconds/upstream/candidate_query_selection | 0.23500386500381865 |
| /lambda1_frequency3/portal_probe_cost_seconds/upstream/fit_extraction | 0.06746959200245328 |
| /lambda1_frequency3/portal_probe_cost_seconds/workspace_allocation | 0.050136003 |
| /lambda1_frequency3/probe_cost_shared_between_portal_rules | true |
| /lambda0_greedy3/count_peak_rss_kib | 10894276 |
| /lambda0_greedy3/timing_peak_rss_kib | 10815868 |
| /lambda0_greedy3/count_router_index_build_seconds | 0.044264222 |
| /lambda0_greedy3/timing_router_index_build_seconds | 0.043567758 |
| /lambda0_greedy3/portal_probe_cost_seconds/GT_score_thread_seconds_sum | 0.10037696199999994 |
| /lambda0_greedy3/portal_probe_cost_seconds/artifact_write_before_final_manifest | 0.8807343040000007 |
| /lambda0_greedy3/portal_probe_cost_seconds/greedy_wall | 0.003503128999999999 |
| /lambda0_greedy3/portal_probe_cost_seconds/independent_candidate_query_verification | 0.217526164 |
| /lambda0_greedy3/portal_probe_cost_seconds/index_load | 10.972568193 |
| /lambda0_greedy3/portal_probe_cost_seconds/input_read_hash_validation | 0.284887994 |
| /lambda0_greedy3/portal_probe_cost_seconds/probe_and_score_batch_wall | 4.669691774000004 |
| /lambda0_greedy3/portal_probe_cost_seconds/probe_thread_seconds_sum | 67.37036810899998 |
| /lambda0_greedy3/portal_probe_cost_seconds/program_wall_before_final_manifest | 17.143767482 |
| /lambda0_greedy3/portal_probe_cost_seconds/upstream/candidate_query_selection | 0.2580252740008291 |
| /lambda0_greedy3/portal_probe_cost_seconds/upstream/fit_extraction | 0.06746959200245328 |
| /lambda0_greedy3/portal_probe_cost_seconds/workspace_allocation | 0.050013607 |
| /lambda0_greedy3/probe_cost_shared_between_portal_rules | true |
| /lambda1_greedy3/count_peak_rss_kib | 10894252 |
| /lambda1_greedy3/timing_peak_rss_kib | 10815872 |
| /lambda1_greedy3/count_router_index_build_seconds | 0.044253142 |
| /lambda1_greedy3/timing_router_index_build_seconds | 0.043601637 |
| /lambda1_greedy3/portal_probe_cost_seconds/GT_score_thread_seconds_sum | 0.09314120599999995 |
| /lambda1_greedy3/portal_probe_cost_seconds/artifact_write_before_final_manifest | 0.8553921030000006 |
| /lambda1_greedy3/portal_probe_cost_seconds/greedy_wall | 0.0031431039999999986 |
| /lambda1_greedy3/portal_probe_cost_seconds/independent_candidate_query_verification | 0.220239356 |
| /lambda1_greedy3/portal_probe_cost_seconds/index_load | 10.976583615 |
| /lambda1_greedy3/portal_probe_cost_seconds/input_read_hash_validation | 0.283341902 |
| /lambda1_greedy3/portal_probe_cost_seconds/probe_and_score_batch_wall | 4.093215366 |
| /lambda1_greedy3/portal_probe_cost_seconds/probe_thread_seconds_sum | 57.818941125000016 |
| /lambda1_greedy3/portal_probe_cost_seconds/program_wall_before_final_manifest | 16.541720277 |
| /lambda1_greedy3/portal_probe_cost_seconds/upstream/candidate_query_selection | 0.23500386500381865 |
| /lambda1_greedy3/portal_probe_cost_seconds/upstream/fit_extraction | 0.06746959200245328 |
| /lambda1_greedy3/portal_probe_cost_seconds/workspace_allocation | 0.050136003 |
| /lambda1_greedy3/probe_cost_shared_between_portal_rules | true |


### P3_structure: webvid2_5m_light_v1 cost

| Source cost field | Value |
| --- | --- |
| /total_partition_wall_seconds | 40.033169924 |
| /peak_rss_kib | 6401504 |
| /nonoverlapping_measured_phase_seconds/symmetric_CSR_measured_subtotal | 1.396349945 |
| /nonoverlapping_measured_phase_seconds/coarse_METIS_and_cut_verification | 18.351234173 |
| /nonoverlapping_measured_phase_seconds/children_METIS_and_cut_verification_sum | 10.288798558 |
| /nonoverlapping_measured_phase_seconds/incoming_CSR | 1.910748161 |
| /nonoverlapping_measured_phase_seconds/fit_GT10_load_and_validation | 0.006140075 |
| /nonoverlapping_measured_phase_seconds/initial_full_objective | 0.393703758 |
| /nonoverlapping_measured_phase_seconds/lambda0_branch | 2.417139968 |
| /nonoverlapping_measured_phase_seconds/GT_incidence_build_for_lambda1 | 0.005012027 |
| /nonoverlapping_measured_phase_seconds/lambda1_branch | 2.503564959 |
| /symmetric_CSR_detail_seconds/count_seconds | 0.367579656 |
| /symmetric_CSR_detail_seconds/fill_seconds | 0.847608036 |
| /symmetric_CSR_detail_seconds/sort_unique_seconds | 0.114386614 |
| /symmetric_CSR_detail_seconds/compact_seconds | 0.066775639 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/0 | 0.373471298 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/1 | 0.23467599 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/2 | 0.864678531 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/3 | 0.74037775 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/4 | 0.801322769 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/5 | 0.754652003 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/6 | 0.797090876 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/7 | 0.375665228 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/8 | 0.895378442 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/9 | 0.696828648 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/10 | 0.479434725 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/11 | 0.86063435 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/12 | 0.853854942 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/13 | 0.484718635 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/14 | 0.571955347 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/15 | 0.504059024 |
| /branch_detail/0/lambda | 0 |
| /branch_detail/0/branch_wall_seconds | 2.417139968 |
| /branch_detail/0/refinement_seconds | 1.444453352 |
| /branch_detail/0/full_recompute_and_label_snapshot_seconds | 0.9149092839999999 |
| /branch_detail/0/other_branch_recording_seconds_by_subtraction | 0.057777331999999904 |
| /branch_detail/1/lambda | 1 |
| /branch_detail/1/branch_wall_seconds | 2.503564959 |
| /branch_detail/1/refinement_seconds | 1.533123379 |
| /branch_detail/1/full_recompute_and_label_snapshot_seconds | 0.915260849 |
| /branch_detail/1/other_branch_recording_seconds_by_subtraction | 0.055180731000000094 |
| /full_initializer_wall_seconds | null |
| /full_initializer_missing_reason | Induced CSR construction, initial canonicalization and label/report writes were not separately timed. |
| /unitemized_total_seconds_by_subtraction | 2.7604782999999955 |
| /unitemized_includes/0 | induced CSR construction |
| /unitemized_includes/1 | initial canonicalization/labels/JSON |
| /unitemized_includes/2 | branch initial copies/hashes and lambda1 GT-count setup |
| /unitemized_includes/3 | metadata/source/binary IO and other setup |
| /reused_exact_GT_cost_seconds | null |
| /reused_exact_GT_cost_reason | Not measured by this partition invocation; not zero. |
| /complete_training_cost_claimed | false |


### P3_structure: yandex_t2i_official10M_ip_v1 cost

| Source cost field | Value |
| --- | --- |
| /total_partition_wall_seconds | 262.250181346 |
| /peak_rss_kib | 37355416 |
| /nonoverlapping_measured_phase_seconds/symmetric_CSR_measured_subtotal | 9.957602082 |
| /nonoverlapping_measured_phase_seconds/coarse_METIS_and_cut_verification | 124.342736055 |
| /nonoverlapping_measured_phase_seconds/children_METIS_and_cut_verification_sum | 69.54501769000001 |
| /nonoverlapping_measured_phase_seconds/incoming_CSR | 13.098918925 |
| /nonoverlapping_measured_phase_seconds/fit_GT10_load_and_validation | 0.00596729 |
| /nonoverlapping_measured_phase_seconds/initial_full_objective | 2.629438602 |
| /nonoverlapping_measured_phase_seconds/lambda0_branch | 13.64655889 |
| /nonoverlapping_measured_phase_seconds/GT_incidence_build_for_lambda1 | 0.014684218 |
| /nonoverlapping_measured_phase_seconds/lambda1_branch | 13.703657142 |
| /symmetric_CSR_detail_seconds/count_seconds | 2.315892626 |
| /symmetric_CSR_detail_seconds/fill_seconds | 6.466127931 |
| /symmetric_CSR_detail_seconds/sort_unique_seconds | 0.81476874 |
| /symmetric_CSR_detail_seconds/compact_seconds | 0.360812785 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/0 | 2.892544954 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/1 | 6.498405177 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/2 | 4.016690393 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/3 | 4.622050035 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/4 | 4.755342667 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/5 | 6.504171845 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/6 | 5.234981653 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/7 | 2.138186406 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/8 | 3.727146427 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/9 | 3.382953765 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/10 | 2.752843074 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/11 | 6.247003534 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/12 | 5.964997619 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/13 | 3.095421449 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/14 | 2.668461069 |
| /child_METIS_and_cut_verification_seconds_in_coarse_ID_order/15 | 5.043817623 |
| /branch_detail/0/lambda | 0 |
| /branch_detail/0/branch_wall_seconds | 13.64655889 |
| /branch_detail/0/refinement_seconds | 7.632496252999999 |
| /branch_detail/0/full_recompute_and_label_snapshot_seconds | 5.793398152 |
| /branch_detail/0/other_branch_recording_seconds_by_subtraction | 0.22066448500000035 |
| /branch_detail/1/lambda | 1 |
| /branch_detail/1/branch_wall_seconds | 13.703657142 |
| /branch_detail/1/refinement_seconds | 7.715514002 |
| /branch_detail/1/full_recompute_and_label_snapshot_seconds | 5.773208662 |
| /branch_detail/1/other_branch_recording_seconds_by_subtraction | 0.21493447800000087 |
| /full_initializer_wall_seconds | null |
| /full_initializer_missing_reason | Induced CSR construction, initial canonicalization and label/report writes were not separately timed. |
| /unitemized_total_seconds_by_subtraction | 15.305600451999965 |
| /unitemized_includes/0 | induced CSR construction |
| /unitemized_includes/1 | initial canonicalization/labels/JSON |
| /unitemized_includes/2 | branch initial copies/hashes and lambda1 GT-count setup |
| /unitemized_includes/3 | metadata/source/binary IO and other setup |
| /reused_exact_GT_cost_seconds | null |
| /reused_exact_GT_cost_reason | Not measured by this partition invocation; not zero. |
| /complete_training_cost_claimed | false |


### P3: webvid2_5m_light_v1 structure

| Source structure field | Value |
| --- | --- |
| /initial/M | 49611457 |
| /initial/C | 19781976 |
| /initial/S | 68627 |
| /initial/Q | 20000 |
| /initial/coarse_C | 8268073 |
| /initial/coarse_S | 34383 |
| /initial/numerator0 | 3560755680000 |
| /initial/numerator1 | 6965441139539 |
| /initial/denominator | 8930062260000 |
| /branches/0/lambda | 0 |
| /branches/0/final/M | 49611457 |
| /branches/0/final/C | 19156978 |
| /branches/0/final/S | 66657 |
| /branches/0/final/Q | 20000 |
| /branches/0/final/coarse_C | 8439720 |
| /branches/0/final/coarse_S | 34119 |
| /branches/0/final/numerator0 | 3448256040000 |
| /branches/0/final/numerator1 | 6755206929249 |
| /branches/0/final/denominator | 8930062260000 |
| /branches/0/passes/0/pass | 1 |
| /branches/0/passes/0/accepted_moves | 91586 |
| /branches/0/passes/0/cross_coarse_moves | 64110 |
| /branches/0/passes/0/labels_sha256 | f5eeb94c11fd08bc97ae4752893f0b6393169db352e430b48a9ce3a49ae57976 |
| /branches/0/passes/0/C | 19276987 |
| /branches/0/passes/0/S | 67052 |
| /branches/0/passes/0/J_at_lambda1 | 0.7610702900926919 |
| /branches/0/passes/0/exact_delta_numerator | -90898020000 |
| /branches/0/passes/0/refinement_seconds | 0.725905541 |
| /branches/0/passes/0/full_recompute_and_label_snapshot_seconds | 0.456833955 |
| /branches/0/passes/1/pass | 2 |
| /branches/0/passes/1/accepted_moves | 34043 |
| /branches/0/passes/1/cross_coarse_moves | 23900 |
| /branches/0/passes/1/labels_sha256 | 25405e70f68a5856fda36de75054e120ec95ee7f231af040e9bacd128e4ca348 |
| /branches/0/passes/1/C | 19156978 |
| /branches/0/passes/1/S | 66657 |
| /branches/0/passes/1/J_at_lambda1 | 0.7564568681124738 |
| /branches/0/passes/1/exact_delta_numerator | -21601620000 |
| /branches/0/passes/1/refinement_seconds | 0.718547811 |
| /branches/0/passes/1/full_recompute_and_label_snapshot_seconds | 0.458075329 |
| /branches/0/wall_seconds | 2.417139968 |
| /branches/0/final_labels_sha256 | 25405e70f68a5856fda36de75054e120ec95ee7f231af040e9bacd128e4ca348 |
| /branches/1/lambda | 1 |
| /branches/1/final/M | 49611457 |
| /branches/1/final/C | 19348257 |
| /branches/1/final/S | 32055 |
| /branches/1/final/Q | 20000 |
| /branches/1/final/coarse_C | 8645109 |
| /branches/1/final/coarse_S | 19108 |
| /branches/1/final/numerator0 | 3482686260000 |
| /branches/1/final/numerator1 | 5072981514135 |
| /branches/1/final/denominator | 8930062260000 |
| /branches/1/passes/0/pass | 1 |
| /branches/1/passes/0/accepted_moves | 121871 |
| /branches/1/passes/0/cross_coarse_moves | 82438 |
| /branches/1/passes/0/labels_sha256 | 38efedb5e707c92cb0b2ef2333a46b9990f9ce8d49f9288ce3f89b225441af70 |
| /branches/1/passes/0/C | 19470606 |
| /branches/1/passes/0/S | 34863 |
| /branches/1/passes/0/J_at_lambda1 | 0.5861452197076843 |
| /branches/1/passes/0/exact_delta_numerator | -1731127834148 |
| /branches/1/passes/0/refinement_seconds | 0.770247891 |
| /branches/1/passes/0/full_recompute_and_label_snapshot_seconds | 0.458762906 |
| /branches/1/passes/1/pass | 2 |
| /branches/1/passes/1/accepted_moves | 40758 |
| /branches/1/passes/1/cross_coarse_moves | 27917 |
| /branches/1/passes/1/labels_sha256 | 0773916bc8da59de451cebc8cb4ba66d911e9fe9c67467d2be4449145ea9e4ce |
| /branches/1/passes/1/C | 19348257 |
| /branches/1/passes/1/S | 32055 |
| /branches/1/passes/1/J_at_lambda1 | 0.5680790756474524 |
| /branches/1/passes/1/exact_delta_numerator | -161331791256 |
| /branches/1/passes/1/refinement_seconds | 0.762875488 |
| /branches/1/passes/1/full_recompute_and_label_snapshot_seconds | 0.456497943 |
| /branches/1/wall_seconds | 2.503564959 |
| /branches/1/final_labels_sha256 | 0773916bc8da59de451cebc8cb4ba66d911e9fe9c67467d2be4449145ea9e4ce |
| /lambda1_minus_lambda0_final/exact_J_at_lambda1_numerator_difference | -1682225415114 |
| /lambda1_minus_lambda0_final/common_denominator | 8930062260000 |
| /lambda1_minus_lambda0_final/J_at_lambda1_difference | -0.1883777924650214 |
| /lambda1_minus_lambda0_final/C_difference | 191279 |
| /lambda1_minus_lambda0_final/leaf_cut_fraction_difference | 0.0038555408683119304 |
| /lambda1_minus_lambda0_final/S_fit_fragmentation_difference | -34602 |
| /lambda1_minus_lambda0_final/normalized_fit_fragmentation_difference | -0.19223333333333334 |
| /lambda1_minus_lambda0_final/mean_distinct_fit_leaf_regions_difference | -1.7301 |
| /lambda1_minus_lambda0_final/J_at_lambda1_strictly_lower | true |
| /lambda1_minus_lambda0_final/fit_fragmentation_strictly_lower | true |
| /lambda1_minus_lambda0_final/registered_structure_condition_met | true |


### P3: yandex_t2i_official10M_ip_v1 structure

| Source structure field | Value |
| --- | --- |
| /initial/M | 294844794 |
| /initial/C | 101893518 |
| /initial/S | 42281 |
| /initial/Q | 20000 |
| /initial/coarse_C | 41172735 |
| /initial/coarse_S | 16098 |
| /initial/numerator0 | 18340833240000 |
| /initial/numerator1 | 30807165975114 |
| /initial/denominator | 53072062920000 |
| /branches/0/lambda | 0 |
| /branches/0/final/M | 294844794 |
| /branches/0/final/C | 97237126 |
| /branches/0/final/S | 40185 |
| /branches/0/final/Q | 20000 |
| /branches/0/final/coarse_C | 41829426 |
| /branches/0/final/coarse_S | 16026 |
| /branches/0/final/numerator0 | 17502682680000 |
| /branches/0/final/numerator1 | 29351020726890 |
| /branches/0/final/denominator | 53072062920000 |
| /branches/0/passes/0/pass | 1 |
| /branches/0/passes/0/accepted_moves | 335701 |
| /branches/0/passes/0/cross_coarse_moves | 220804 |
| /branches/0/passes/0/labels_sha256 | edb15b24c728dbb527e512da76aeed44e70578943b340281f4a8cddea7110c14 |
| /branches/0/passes/0/C | 97990291 |
| /branches/0/passes/0/S | 40478 |
| /branches/0/passes/0/J_at_lambda1 | 0.5572231099459964 |
| /branches/0/passes/0/exact_delta_numerator | -702580860000 |
| /branches/0/passes/0/refinement_seconds | 3.84879196 |
| /branches/0/passes/0/full_recompute_and_label_snapshot_seconds | 2.908729299 |
| /branches/0/passes/1/pass | 2 |
| /branches/0/passes/1/accepted_moves | 129038 |
| /branches/0/passes/1/cross_coarse_moves | 87438 |
| /branches/0/passes/1/labels_sha256 | efcbdd333cec86759907a6af7f5a363c4c1ecb4af8d16fdabbb7f0b56526f19c |
| /branches/0/passes/1/C | 97237126 |
| /branches/0/passes/1/S | 40185 |
| /branches/0/passes/1/J_at_lambda1 | 0.5530408865231652 |
| /branches/0/passes/1/exact_delta_numerator | -135569700000 |
| /branches/0/passes/1/refinement_seconds | 3.783704293 |
| /branches/0/passes/1/full_recompute_and_label_snapshot_seconds | 2.884668853 |
| /branches/0/wall_seconds | 13.64655889 |
| /branches/0/final_labels_sha256 | efcbdd333cec86759907a6af7f5a363c4c1ecb4af8d16fdabbb7f0b56526f19c |
| /branches/1/lambda | 1 |
| /branches/1/final/M | 294844794 |
| /branches/1/final/C | 97587173 |
| /branches/1/final/S | 19296 |
| /branches/1/final/Q | 20000 |
| /branches/1/final/coarse_C | 42111836 |
| /branches/1/final/coarse_S | 8037 |
| /branches/1/final/numerator0 | 17565691140000 |
| /branches/1/final/numerator1 | 23255016285024 |
| /branches/1/final/denominator | 53072062920000 |
| /branches/1/passes/0/pass | 1 |
| /branches/1/passes/0/accepted_moves | 359393 |
| /branches/1/passes/0/cross_coarse_moves | 231396 |
| /branches/1/passes/0/labels_sha256 | 4ebefa41fbfbc35b023e7cbb1b6272fdfc1a72a1593745cef9416fc8cded01bb |
| /branches/1/passes/0/C | 98327901 |
| /branches/1/passes/0/S | 20184 |
| /branches/1/passes/0/J_at_lambda1 | 0.44562370861192824 |
| /branches/1/passes/0/exact_delta_numerator | -7156996473018 |
| /branches/1/passes/0/refinement_seconds | 3.866390563 |
| /branches/1/passes/0/full_recompute_and_label_snapshot_seconds | 2.888215028 |
| /branches/1/passes/1/pass | 2 |
| /branches/1/passes/1/accepted_moves | 131164 |
| /branches/1/passes/1/cross_coarse_moves | 87795 |
| /branches/1/passes/1/labels_sha256 | e6d36a21adef6bce7a8e7ec146f3a1a1bf223c04b81f8d21c6538716889a04c7 |
| /branches/1/passes/1/C | 97587173 |
| /branches/1/passes/1/S | 19296 |
| /branches/1/passes/1/J_at_lambda1 | 0.43817811114819954 |
| /branches/1/passes/1/exact_delta_numerator | -395153217072 |
| /branches/1/passes/1/refinement_seconds | 3.849123439 |
| /branches/1/passes/1/full_recompute_and_label_snapshot_seconds | 2.884993634 |
| /branches/1/wall_seconds | 13.703657142 |
| /branches/1/final_labels_sha256 | e6d36a21adef6bce7a8e7ec146f3a1a1bf223c04b81f8d21c6538716889a04c7 |
| /lambda1_minus_lambda0_final/exact_J_at_lambda1_numerator_difference | -6096004441866 |
| /lambda1_minus_lambda0_final/common_denominator | 53072062920000 |
| /lambda1_minus_lambda0_final/J_at_lambda1_difference | -0.11486277537496559 |
| /lambda1_minus_lambda0_final/C_difference | 350047 |
| /lambda1_minus_lambda0_final/leaf_cut_fraction_difference | 0.0011872246250344172 |
| /lambda1_minus_lambda0_final/S_fit_fragmentation_difference | -20889 |
| /lambda1_minus_lambda0_final/normalized_fit_fragmentation_difference | -0.11605 |
| /lambda1_minus_lambda0_final/mean_distinct_fit_leaf_regions_difference | -1.04445 |
| /lambda1_minus_lambda0_final/J_at_lambda1_strictly_lower | true |
| /lambda1_minus_lambda0_final/fit_fragmentation_strictly_lower | true |
| /lambda1_minus_lambda0_final/registered_structure_condition_met | true |


## Reproduce and machine-readable artifacts

Generator: `/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/generate_measurement_tables.py`; SHA256 `206986958fc0f4f7eb8d9cea4bfe4488d20982dd337e4463871df9ed11dd5523`. The command must target a new prefix.

```bash
.venv_cpu/bin/python hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/generate_measurement_tables.py --output-prefix /absolute/new/prefix
```

| Artifact | Path |
| --- | --- |
| json | /data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/measurement_tables_v1.json |
| markdown | /data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/measurement_tables_v1.md |
| measurements_csv | /data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/measurement_tables_v1.csv |
| comparisons_csv | /data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/measurement_tables_v1_comparisons.csv |
| costs_csv | /data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/measurement_tables_v1_costs.csv |
| structure_csv | /data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/measurement_tables_v1_structure.csv |

The JSON preserves full measurement/comparison objects and the source flags; all references carry source SHA256 plus JSON Pointer. The CSV files flatten measurements, comparisons, individual cost cells, and individual structure cells for later excerpting.
