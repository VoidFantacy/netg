# E119: Response-Defined Entry Capability

Status: **STOP_CAPABILITY_PILOT**. Default unchanged. No new search, GT, graph, or QPS.

## Main Results

Historical-development, whole-query four-fold OOF. All values compare with the original GT10 policy.
Recall is in percentage points. Cached time is main-search-only relative change, not full online cost.
U = delta Recall - 0.1 * normalized search-time delta, averaged equally over K1/K100.

| Dataset | Method | R1 pp | R100 pp | Cached time K1 / K100 % | U x100 [descriptive 95% CI] |
|---|---|---:|---:|---:|---:|
| webvid2 | BestFixed | +0.0000 | +0.0000 | +0.000 / +0.000 | +0.0000 [+0.0000, +0.0000] |
| webvid2 | ClusterMean | -1.3672 | -0.1694 | +6.314 / +1.756 | -1.1718 [-1.4823, -0.8672] |
| webvid2 | E118Additive | +0.0000 | +0.0020 | +0.042 / +0.001 | -0.0012 [-0.0046, +0.0022] |
| webvid2 | GeomMSE | -1.0742 | -0.4331 | +6.710 / +6.149 | -1.3966 [-1.7693, -1.0256] |
| webvid2 | CapMSE | -1.7822 | -0.4355 | +7.623 / +6.172 | -1.7986 [-2.1490, -1.4535] |
| webvid2 | GeomRank | -1.7334 | -0.7314 | +4.604 / +5.139 | -1.7196 [-2.1751, -1.2793] |
| webvid2 | CapRank | -1.8555 | -0.8367 | +5.369 / +6.717 | -1.9503 [-2.4095, -1.4963] |
| webvid2 | GBDT | -0.0488 | -0.1631 | +2.100 / +0.774 | -0.2496 [-0.4492, -0.0533] |
| webvid2 | TabM | -0.2441 | -0.0151 | +3.179 / +0.190 | -0.2981 [-0.5345, -0.0668] |
| yandex | BestFixed | +0.0000 | +0.0000 | +0.000 / +0.000 | +0.0000 [+0.0000, +0.0000] |
| yandex | ClusterMean | -0.5371 | +0.1135 | +10.396 / +3.136 | -0.8884 [-1.2082, -0.5673] |
| yandex | E118Additive | +0.0977 | -0.0027 | +0.938 / +0.028 | -0.0008 [-0.0745, +0.0749] |
| yandex | GeomMSE | +0.0244 | -0.0542 | +8.025 / +5.966 | -0.7145 [-1.0129, -0.4214] |
| yandex | CapMSE | -0.3662 | -0.1611 | +9.638 / +8.149 | -1.1530 [-1.4638, -0.8346] |
| yandex | GeomRank | -0.5859 | -0.3274 | +4.726 / +6.050 | -0.9955 [-1.3988, -0.5986] |
| yandex | CapRank | -0.0488 | -0.3501 | +4.075 / +6.102 | -0.7083 [-1.0675, -0.3558] |
| yandex | GBDT | +0.0488 | +0.0183 | +2.789 / +1.585 | -0.1851 [-0.3791, +0.0179] |
| yandex | TabM | -0.1709 | -0.0305 | +2.439 / +0.765 | -0.2609 [-0.4297, -0.0933] |

## Decision and Interpretation

Frozen primary candidate: `None`. Strong-control passes: `[]`.
H1 capability contrast: `{'CapMSE': False, 'CapRank': False}`. H2 mean contrast versus additive reference: `{'CapMSE': False, 'CapRank': False}`.
A representation contrast is separate from absolute net gain and from paid deployment performance.
No model, threshold, lambda, seed, cluster count, depth, or candidate set was selected from outer failures.

The version stops at its query-out gate. The conditional native/fresh-query/performance stage is not triggered.
This bounds the fixed support representation and fixed scorer runs, not all response-based routing or all neural models.

## Fit Versus Transfer

| Dataset | Method | Mean fit U x100 | Mean monitor U x100 | OOF U x100 |
|---|---|---:|---:|---:|
| webvid2 | GeomMSE | +1.3588 | -1.2731 | -1.3966 |
| webvid2 | CapMSE | +1.0897 | -1.3104 | -1.7986 |
| webvid2 | GeomRank | +0.1306 | -0.8541 | -1.7196 |
| webvid2 | CapRank | +1.5377 | -0.8020 | -1.9503 |
| webvid2 | GBDT | +2.2392 | -0.3517 | -0.2496 |
| webvid2 | TabM | +2.4314 | -0.2824 | -0.2981 |
| yandex | GeomMSE | +0.8403 | -0.3615 | -0.7145 |
| yandex | CapMSE | +0.5780 | -0.4849 | -1.1530 |
| yandex | GeomRank | +0.0925 | -0.2130 | -0.9955 |
| yandex | CapRank | +0.2192 | -0.0353 | -0.7083 |
| yandex | GBDT | +2.0720 | -0.2556 | -0.1851 |
| yandex | TabM | +2.1452 | +0.2008 | -0.2609 |

## Rescue and Harm

| Dataset | Method | K1 rescue / harm | K100 improved / worsened queries | K1 / K100 switches |
|---|---|---:|---:|---:|
| webvid2 | GeomMSE | 68 / 112 | 573 / 584 | 2445 / 2401 |
| webvid2 | CapMSE | 46 / 119 | 566 / 604 | 2634 / 2505 |
| webvid2 | GeomRank | 97 / 168 | 886 / 959 | 4078 / 4048 |
| webvid2 | CapRank | 102 / 178 | 929 / 990 | 4090 / 4093 |
| webvid2 | GBDT | 29 / 31 | 152 / 157 | 1086 / 689 |
| webvid2 | TabM | 40 / 50 | 16 / 34 | 1161 / 92 |
| yandex | GeomMSE | 45 / 44 | 403 / 349 | 2654 / 2221 |
| yandex | CapMSE | 44 / 59 | 467 / 429 | 2820 / 2685 |
| yandex | GeomRank | 54 / 78 | 619 / 603 | 3918 / 4053 |
| yandex | CapRank | 60 / 62 | 651 / 607 | 3836 / 4063 |
| yandex | GBDT | 25 / 23 | 163 / 154 | 1649 / 1192 |
| yandex | TabM | 14 / 21 | 40 / 39 | 558 / 157 |

## Theory and Literature

The systematic chain is: oracle opportunity -> observable service descriptor -> query-out selection -> paid online cost.
[Research and prior-work differences](research.md) links UniRoute, decision-focused ranking, DCNv2, TabM and RouteLLM.
[Algorithm-selection prior work](prior_work_addendum.md) records ALORS and bilinear ranking, including their overlap with the proposed framing.
[Theoretical conditions and counterexamples](theory_bounds.md) separates representation error, finite support, estimation and deployment overhead.
The gated shared scorer is our bounded diagnostic parameterization, not a DCNv2 or UniRoute reproduction.
No general OOD guarantee or paper novelty is claimed.

## Validation and Limits

Independent numerical audit PASS; 920 inherited source files remain unchanged.
All original top1 labels and K100 masks, four query roles, representation isolation, objective gradient, scalar forward,
model reloads, selected monitor checkpoints, every saved action and realized payoff were checked.
Independent here means a separate numerical implementation, not a separate human or agent reviewer.
The old GT10 profile bank and historical queries were previously exposed. OOF intervals are descriptive;
training folds overlap and the 4 configurations were compared. They are not a substitute for a new blind test.
Equal allocated parameters do not equalize the effective capacity of zeroed versus nonzero capability inputs.
The additive reference uses inherited direction features; its comparison does not isolate the interaction layer causally.
All strong controls share the fixed information set; they do not bound every possible cheap geometry or graph feature.
Support+fit/monitor per fold are 1024/1792/256 queries; H paired labels do not multiply the independent sample count.
Strong controls are fixed-budget configurations, not optimally tuned upper bounds on their model families.
The negative-result interpretation must retain these limits and the full fit/monitor learning curves.

## Cost and Data Boundary

Training controller: 87.98 minutes; peak RSS 20.009 GiB; offline numerical threads <=8.
New search/GT/graph/K10/full-wall calls: zero. E118 response acquisition is inherited, not free from-scratch supervision.
Inherited label-only loops: 4.776 hours, 46,964,928 search calls; graph/GT/profile acquisition has additional inherited cost.
No fresh test query payload was materialized. [Source audit](reviews/source_audit.json) identifies candidate source windows
but requires complete byte deduplication, identity checks, model freeze and power-based sample size before any final test.
Original data, labels, graphs, code, models and production E99 remain unchanged.

## Artifacts

- [Frozen protocol](protocol.md), [lock](config.locked.json), [preflight](reviews/preflight.json).
- [All metrics](analysis/metrics.csv), [full gate and contrasts](analysis/results.json), query-aligned NPZ in analysis/.
- [Independent audit](reviews/independent_audit.json), [training cost](reviews/training_complete.json).
- [Numerical determinism correction](reviews/preflight_correction.md), [metadata schema correction](reviews/source_schema_correction.md).
- [Cost scope](reviews/cost_scope.md), [source audit](reviews/source_audit.json), [training log](training.log).
