# P2 fixed pilot evidence

These are historically used development pilot results at fixed L=64/128. Ordinary 95% paired-query intervals are exploratory and unadjusted. Five timing rounds measure timing variation and are not five Recall samples. This report does not automatically pass P2, evaluate the P5/P6/P7 substantial-performance thresholds, or claim matched-Recall/QPS improvement.

## webvid2_5m_light_v1

Count/plain, full route equality, five-round identity, schedule and paired20K provenance checks: PASS.

| Method | L | Recall@10 | Mean QPS | Median QPS | Route / graph / total NDC | Route MAC | Mean actual entries | Scope |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| fast | 64 | 0.656570 | 32079.80 | 32123.33 | 124.75 / 922.03 / 1046.78 | 63870.3 | 3.000 | pilot deployment measurement |
| geom_unified | 64 | 0.653600 | 28779.08 | 28906.35 | 188.75 / 943.31 / 1132.06 | 96638.3 | 9.967 | pilot deployment measurement |
| geom_uniform | 64 | 0.599240 | 19547.96 | 19556.46 | 188.75 / 1504.90 / 1693.65 | 96638.3 | 9.967 | pilot deployment measurement |
| geom_probability | 64 | 0.599290 | 19573.60 | 19532.43 | 188.75 / 1504.88 / 1693.63 | 96638.3 | 9.967 | pilot deployment measurement |
| oracle_unified | 64 | 0.659410 | 30699.09 | 30656.99 | 124.75 / 939.89 / 1064.63 | 63870.3 | 9.971 | oracle diagnostic |
| oracle_probability | 64 | 0.713540 | 21352.26 | 21198.92 | 124.75 / 1348.92 / 1473.66 | 63870.3 | 9.971 | oracle diagnostic |
| fast | 128 | 0.746980 | 17421.80 | 17495.25 | 124.75 / 1652.09 / 1776.84 | 63870.3 | 3.000 | pilot deployment measurement |
| geom_unified | 128 | 0.742820 | 16530.44 | 16490.68 | 188.75 / 1669.20 / 1857.94 | 96638.3 | 9.967 | pilot deployment measurement |
| geom_uniform | 128 | 0.706240 | 11632.30 | 11977.03 | 188.75 / 2395.37 / 2584.12 | 96638.3 | 9.967 | pilot deployment measurement |
| geom_probability | 128 | 0.706420 | 12003.52 | 12008.71 | 188.75 / 2394.31 / 2583.06 | 96638.3 | 9.967 | pilot deployment measurement |
| oracle_unified | 128 | 0.748290 | 16995.32 | 17011.94 | 124.75 / 1667.13 / 1791.88 | 63870.3 | 9.971 | oracle diagnostic |
| oracle_probability | 128 | 0.800810 | 13744.24 | 13988.23 | 124.75 / 2084.24 / 2208.99 | 63870.3 | 9.971 | oracle diagnostic |

| Fixed contrast (candidate minus reference) | L | Recall delta pp | Pointwise bootstrap95% pp | Mean paired QPS ratio | Raw ratios, rounds0..4 |
|---|---:|---:|---|---:|---|
| uniform_protection | 64 | -5.4360 | [-5.8840, -4.9840] | 0.6793 | 0.6745, 0.6888, 0.6779, 0.6791, 0.6761 |
| probability_protection | 64 | -5.4310 | [-5.8780, -4.9800] | 0.6802 | 0.6745, 0.6901, 0.6782, 0.6844, 0.6738 |
| oracle_protection | 64 | +5.4130 | [+5.0100, +5.8260] | 0.6956 | 0.6897, 0.7194, 0.6785, 0.7096, 0.6810 |
| oracle_selection_unified | 64 | +0.5810 | [+0.3540, +0.8050] | 1.0667 | 1.0606, 1.0633, 1.0605, 1.0753, 1.0738 |
| oracle_selection_protected | 64 | +11.4250 | [+11.0710, +11.7850] | 1.0908 | 1.0845, 1.1085, 1.0609, 1.1149, 1.0853 |
| geometric_bundle_vs_fast | 64 | -0.2970 | [-0.6100, +0.0140] | 0.8971 | 0.8983, 0.8891, 0.8981, 0.9022, 0.8977 |
| oracle_bundle_vs_fast | 64 | +0.2840 | [-0.0340, +0.6010] | 0.9569 | 0.9527, 0.9454, 0.9524, 0.9702, 0.9640 |
| uniform_protection | 128 | -3.6580 | [-4.0320, -3.2700] | 0.7037 | 0.7268, 0.7345, 0.6638, 0.6641, 0.7293 |
| probability_protection | 128 | -3.6400 | [-4.0170, -3.2540] | 0.7261 | 0.7247, 0.7296, 0.7253, 0.7218, 0.7293 |
| oracle_protection | 128 | +5.2520 | [+4.9170, +5.5960] | 0.8087 | 0.8222, 0.7524, 0.8262, 0.8204, 0.8223 |
| oracle_selection_unified | 128 | +0.5470 | [+0.3630, +0.7290] | 1.0281 | 1.0324, 1.0290, 1.0354, 1.0308, 1.0131 |
| oracle_selection_protected | 128 | +9.4390 | [+9.1300, +9.7460] | 1.1451 | 1.1713, 1.0611, 1.1796, 1.1716, 1.1422 |
| geometric_bundle_vs_fast | 128 | -0.4160 | [-0.6640, -0.1770] | 0.9490 | 0.9396, 0.9426, 0.9670, 0.9600, 0.9359 |
| oracle_bundle_vs_fast | 128 | +0.1310 | [-0.1100, +0.3720] | 0.9758 | 0.9700, 0.9699, 1.0013, 0.9896, 0.9482 |

The first three contrasts hold the real route fixed and test queue changes. Oracle selection contrasts diagnose a region-selection plus selected-portal gap. Fast bundle contrasts also change entry count and shared-default seeding. A positive oracle selection gap does not prove that candidate protection is effective, and a same-L Recall/QPS tradeoff is not a matched-cost improvement.

Gate: **REQUIRES_MECHANISM_REVIEW**. Inspect the predefined competition traces and both L values on both datasets. Intervals crossing zero are inconclusive for direction, not proof of equivalence. Do not choose a favorable point and reuse its interval as a selected-best guarantee.

Input evidence: [count](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/webvid_eval/count.json), [timing](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/webvid_eval/timing.json), [model](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/webvid_model/model.json), [paired_fast20k](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p1/paired_fast20k/webvid2_5m_light_v1/manifest.json).

## yandex_t2i_official10M_ip_v1

Count/plain, full route equality, five-round identity, schedule and paired20K provenance checks: PASS.

| Method | L | Recall@10 | Mean QPS | Median QPS | Route / graph / total NDC | Route MAC | Mean actual entries | Scope |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| fast | 64 | 0.828320 | 27390.69 | 27694.22 | 119.31 / 1649.60 / 1768.92 | 23862.7 | 3.000 | pilot deployment measurement |
| geom_unified | 64 | 0.825190 | 25327.74 | 25860.47 | 183.31 / 1661.44 / 1844.75 | 36662.7 | 9.998 | pilot deployment measurement |
| geom_uniform | 64 | 0.753370 | 16123.88 | 16408.63 | 183.31 / 2684.49 / 2867.80 | 36662.7 | 9.998 | pilot deployment measurement |
| geom_probability | 64 | 0.756520 | 16508.94 | 16466.77 | 183.31 / 2681.21 / 2864.52 | 36662.7 | 9.998 | pilot deployment measurement |
| oracle_unified | 64 | 0.830930 | 26677.79 | 26724.07 | 119.31 / 1649.59 / 1768.91 | 23862.7 | 9.999 | oracle diagnostic |
| oracle_probability | 64 | 0.862480 | 19062.90 | 19047.86 | 119.31 / 2352.72 / 2472.03 | 23862.7 | 9.999 | oracle diagnostic |
| fast | 128 | 0.896550 | 15947.73 | 15920.08 | 119.31 / 2862.01 / 2981.32 | 23862.7 | 3.000 | pilot deployment measurement |
| geom_unified | 128 | 0.894620 | 14633.79 | 14900.81 | 183.31 / 2874.97 / 3058.29 | 36662.7 | 9.998 | pilot deployment measurement |
| geom_uniform | 128 | 0.855430 | 9924.23 | 10115.94 | 183.31 / 4221.60 / 4404.91 | 36662.7 | 9.998 | pilot deployment measurement |
| geom_probability | 128 | 0.859740 | 10033.05 | 10118.97 | 183.31 / 4214.95 / 4398.26 | 36662.7 | 9.998 | pilot deployment measurement |
| oracle_unified | 128 | 0.898240 | 14984.61 | 15283.04 | 119.31 / 2856.26 / 2975.57 | 23862.7 | 9.999 | oracle diagnostic |
| oracle_probability | 128 | 0.931830 | 11779.95 | 11833.66 | 119.31 / 3635.67 / 3754.99 | 23862.7 | 9.999 | oracle diagnostic |

| Fixed contrast (candidate minus reference) | L | Recall delta pp | Pointwise bootstrap95% pp | Mean paired QPS ratio | Raw ratios, rounds0..4 |
|---|---:|---:|---|---:|---|
| uniform_protection | 64 | -7.1820 | [-7.6240, -6.7310] | 0.6385 | 0.7134, 0.6357, 0.6376, 0.5764, 0.6295 |
| probability_protection | 64 | -6.8670 | [-7.3090, -6.4210] | 0.6536 | 0.7232, 0.6337, 0.6368, 0.6401, 0.6342 |
| oracle_protection | 64 | +3.1550 | [+2.7710, +3.5400] | 0.7146 | 0.7199, 0.7208, 0.7159, 0.7070, 0.7095 |
| oracle_selection_unified | 64 | +0.5740 | [+0.3830, +0.7710] | 1.0560 | 1.1601, 1.0188, 1.0334, 1.0402, 1.0273 |
| oracle_selection_protected | 64 | +10.5960 | [+10.2790, +10.9190] | 1.1547 | 1.1549, 1.1587, 1.1618, 1.1489, 1.1493 |
| geometric_bundle_vs_fast | 64 | -0.3130 | [-0.5780, -0.0500] | 0.9254 | 0.8288, 0.9944, 0.9273, 0.9264, 0.9500 |
| oracle_bundle_vs_fast | 64 | +0.2610 | [-0.0030, +0.5280] | 0.9745 | 0.9615, 1.0131, 0.9583, 0.9637, 0.9759 |
| uniform_protection | 128 | -3.9190 | [-4.2890, -3.5430] | 0.6796 | 0.7581, 0.6773, 0.6333, 0.6873, 0.6419 |
| probability_protection | 128 | -3.4880 | [-3.8520, -3.1150] | 0.6870 | 0.7627, 0.6860, 0.6627, 0.6398, 0.6837 |
| oracle_protection | 128 | +3.3590 | [+3.0450, +3.6770] | 0.7874 | 0.7775, 0.8559, 0.7702, 0.7736, 0.7600 |
| oracle_selection_unified | 128 | +0.3620 | [+0.1930, +0.5370] | 1.0259 | 1.1261, 0.9272, 1.0167, 1.0266, 1.0327 |
| oracle_selection_protected | 128 | +7.2090 | [+6.9390, +7.4870] | 1.1751 | 1.1478, 1.1568, 1.1817, 1.2412, 1.1479 |
| geometric_bundle_vs_fast | 128 | -0.1930 | [-0.4040, +0.0120] | 0.9176 | 0.8527, 0.9332, 0.9398, 0.9296, 0.9326 |
| oracle_bundle_vs_fast | 128 | +0.1690 | [-0.0480, +0.3880] | 0.9397 | 0.9603, 0.8653, 0.9555, 0.9544, 0.9630 |

The first three contrasts hold the real route fixed and test queue changes. Oracle selection contrasts diagnose a region-selection plus selected-portal gap. Fast bundle contrasts also change entry count and shared-default seeding. A positive oracle selection gap does not prove that candidate protection is effective, and a same-L Recall/QPS tradeoff is not a matched-cost improvement.

Gate: **REQUIRES_MECHANISM_REVIEW**. Inspect the predefined competition traces and both L values on both datasets. Intervals crossing zero are inconclusive for direction, not proof of equivalence. Do not choose a favorable point and reuse its interval as a selected-best guarantee.

Input evidence: [count](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/yandex_eval/count.json), [timing](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/yandex_eval/timing.json), [model](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/yandex_model/model.json), [paired_fast20k](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p1/paired_fast20k/yandex_t2i_official10M_ip_v1/manifest.json).

## Evidence limits and next decision

No validation or heldout query/GT data were read. Region labels, model profiles/portals, and paired Fast files were checked by checksum. The frozen graph checksum is inherited from the audited model; this small analysis does not rescan the multi-gigabyte graph. The full query/GT-independent evaluator contract and upstream P0/P1 checks remain part of the evidence chain.

The next decision belongs to the P2 gate review: separate fixed-route protection evidence from oracle/portal potential, inspect causal competition traces, then follow the preregistered failure action. P3/P4 learning cannot be authorized by this script. P5/P6/P7 require their original matched-point selection-inside-bootstrap, corrected intervals, two adjacent anchors and independent-build/frozen-test evidence.
