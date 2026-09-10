# Standalone GATE / WebVid frozen-graph analysis

## Decision

The adapted GATE entry layer is effective relative to the fixed Medoid, but is
strictly dominated by Fast Prototype on all 12 validation points while using
more graph distance computations.  The preregistered decision is therefore to
stop before the Yandex replication and retain this run as the WebVid standalone
strong baseline.

## Contract

- frozen ACSG NSG: `R64/L_build100/C512`, no edge repair or rebuild;
- metric: raw inner product end to end;
- hubs: 512 balanced HBKM hubs with exact base IDs;
- topology: 512 topology-only subgraphs, exactly 1,000 nodes each;
- Graph2Vec: deterministic WL(2)+PV-DBOW, 512d, seed 42;
- train: independent prototype-train first 10K, exact-IP top-1 GT;
- checkpoint selection: independent validation 10K only;
- evaluation: validation 10K, three graph-search runs per point, exact dense
  cosine top-3 routing for GATE and the same frozen graph for all methods.

GATE upstream leaves Graph2Vec as an external step, and its paper presents a
sequential balanced assignment.  This adapter uses a documented scalable
Sinkhorn assignment and a standard WL+Doc2Vec implementation.  It is a complete
reproducible baseline, not a claim of bitwise identity with private author
artifacts.

## Training

- train samples: 10,000 queries, 915 no-hit, 8,150 usable, 652,600 triplets;
- validation samples: 10,000 queries, 904 no-hit, 8,146 usable;
- max epochs 200, patience 20, best epoch 68, stopped after epoch 88;
- best usable-validation RouteAcc: `0.0963663`;
- raw-hub cosine RouteAcc on the same usable validation queries: `0.2048858`;
- training wall time: `46m41.73s` on the current 16-vCPU CPU host.

## Frozen-graph results

All values below are GATE minus the named baseline. Recall values are absolute
percentage points; NDC values are relative percentages versus Fast.

| Recall | L | vs Fast | vs Medoid | graph NDC vs Fast |
| --- | ---: | ---: | ---: | ---: |
| @1 | 64 | -3.230 | +2.580 | +16.59% |
| @1 | 128 | -2.560 | +2.080 | +8.77% |
| @1 | 200 | -1.970 | +1.300 | +5.79% |
| @1 | 400 | -1.360 | +0.910 | +2.83% |
| @10 | 64 | -2.219 | +1.993 | +16.59% |
| @10 | 128 | -1.899 | +1.513 | +8.77% |
| @10 | 200 | -1.336 | +1.015 | +5.79% |
| @10 | 400 | -0.802 | +0.785 | +2.83% |
| @100 | 100 | -0.828 | +0.908 | +11.06% |
| @100 | 128 | -0.817 | +0.835 | +8.77% |
| @100 | 200 | -0.563 | +0.577 | +5.79% |
| @100 | 400 | -0.330 | +0.485 | +2.83% |

Machine-readable results:

- `eval_gate_max200_best_validation10k_r1_r10_3run_v1/results.json`
- `eval_gate_max200_best_validation10k_r100_3run_v1/results.json`
- `models_webvid_gate_uniquehub_max200_patience20_v4/training_report.json`
- `routes_webvid_gate_max200_best_validation10k_top3_v1/manifest.json`

This result does not imply that query-aware entry selection is exhausted:
current-hub true-search oracle headroom remains large.  It shows that GATE's
static topology/triplet embedding does not recover that headroom under this
frozen raw-IP contract.
