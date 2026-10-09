# E173: NSG / GT10 / M5 public-test retest

User authorization on 2026-10-09 (UTC+8): rerun NSG, GT and M5 at L=200,
400, 800, 1000, 1200 on WebVid and Yandex, using actual test queries rather
than the previous SELECT/CAL acceptance process.

This is a new fixed-model benchmark. It does not revise E172's original
protocol, saved results or NO_CONFIRM decision. No training, table tuning,
router rebuilding, graph rebuilding or performance-based sample selection
is part of this test.

## Fixed comparison

- Datasets: WebVid 2,505,000 x 512, and official Yandex first-10M x 200.
- Queries: WebVid public test all 10,000; Yandex public test first 10,000
  of 100,000, matching the project's existing 10K benchmark scope.
- Metrics: actual top-1 and top-100 searches, reported separately as
  Recall@1 and Recall@100. Every method uses the same L at each point.
- L: exactly [200, 400, 800, 1000, 1200] for both K values.
- NSG: original fixed index enterpoint (NSG_Medoid), with no GT router.
- GT10: existing Web GT10-soft-t1 / Yandex GT10-hard router and original
  three-entry heap-pop order, followed by the original scalar NSG kernel.
- M5: exactly that GT10 search plus the original frozen residual_joint.bin
  posting lookup, deduplication, raw-IP rescoring and top-K merge.
- Same raw base, metric, normalization, graph and scalar search_new kernel
  across all three methods; no mix of scalar and span/batch4 timings.

## Measurement

- CPU-only, one actual thread, fixed CPU affinity; OMP, BLAS and MKL pools
  explicitly limited to one. Real benchmarks run sequentially.
- One warm-up batch per method/L; three complete batch timings, with
  method order rotated across rounds.
- Timer includes query-loop setup/teardown, route, main search and all M5
  lookup/deduplication/rescoring/merge costs. No saved route substitution.
- Index/model loading, exact-GT evaluation, hashes, audits and file output
  are outside the query timer. Their job cost is reported separately.
- Save aligned IDs/distances for every method/L and all timing repeats.
  Check independently executed untimed plain/count output equality and
  the original independent linear merge oracle. Normal timed outputs are
  released before the timer stops and are not retained for per-round bit
  comparisons. Report QPS median and repeat range.
- Recall is exact top-K set intersection divided by K, averaged over
  queries; Recall@1 uses the actual top-1 output and exact GT1.
- Report all 60 method/K/L points, including regressions. Compare equal-L
  differences and observed Recall-QPS point dominance without interpolated
  matching-Recall claims or selecting another deployment point.

## Evidence limits

The public test queries have been evaluated in earlier project work. This
is a frozen-model public-test rerun, not an untouched project-wide blind
test. Yandex results cover the first 10K public queries, not all 100K.
Timing repetitions do not create independent quality samples. Data identity
and training/test overlap checks are recorded before benchmark execution.

The old E172 campaign was moved to /root/acsg-e172-storage-v2/campaign.
Its historical bind mount is absent after restart. This test reads that
physical location directly without restoring the old campaign runner.
