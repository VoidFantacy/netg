# E1b routing-cost report

Decision: **NO_GO_ROUTING_COST**. Artifact checks passed; the method gate failed. No held-out query or GT was read.

## Equal-total-NDC gate

| Dataset | Fast target | Fast NDC | Fast R@10 | Matched L | Matched NDC | Matched R@10 | Delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| WebVid | Fast L64 | 1039.041 | 0.65938 | 22 | 1017.778 | 0.51241 | -14.697 pp |
| WebVid | Fast L128 | 1768.466 | 0.74830 | 80 | 1718.644 | 0.69870 | -4.960 pp |
| Yandex | Fast L64 | 1759.520 | 0.82798 | 44 | 1753.074 | 0.78695 | -4.103 pp |
| Yandex | Fast L128 | 2971.207 | 0.89630 | 104 | 2931.855 | 0.88167 | -1.463 pp |

All four legal matched points are below Fast Recall. Because equal-total-NDC and equal-wall are conjunctive requirements, wall-time runs were omitted: they cannot reverse the failed NDC gate.

## Router diagnostics

| Dataset | exact top-8 recall v1/v2/v3 | dense -> HNSW routing NDC | final-route change | anchor mismatch |
| --- | --- | ---: | ---: | ---: |
| WebVid | 0.92010 / 0.98731 / 0.98834 | 1760.299 -> 642.337 | 2.47% | 0 |
| Yandex | 0.96105 / 0.99719 / 0.99757 | 1766.112 -> 549.376 | 0.31% | 0 |

The fixed secondary Micro-HNSW removes most dense-routing distance cost and preserves the anchor, but the remaining routing cost forces graph-search L low enough that total Recall is worse than Fast at every paired budget.

E2--E4 and tail analysis are `NOT_RUN` by the preregistered stopping rule. Fast v1 remains the selected method; no parameter scan or fallback branch was opened.

Cost curve: `../../figures/e1b_recall_vs_total_ndc.png`.
