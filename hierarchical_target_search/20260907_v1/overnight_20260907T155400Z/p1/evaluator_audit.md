# P1 evaluator implementation audit

Updated: 2026-09-07 16:11 UTC. This record covers implementation, synthetic checks and CLI rejection checks. It does not establish real-data parity, measurement acceptance or P2 mechanism performance; those require the root runner's later evidence.

## Implementation and ownership

- Added `benches/bench_hierarchical_eval.cpp` and its target in `benches/CMakeLists.txt`. No legacy search or Fast source was changed by this evaluator task. `RegionalSearch.h` belongs to the separate P1 search task.
- Inputs are explicit `--stage`, `--split`, `--measurement`, `--output`, dataset/index and paired Fast files. `--model` is optional for `fast` (legacy top-3) and `fast_unified` (new pool consuming all requested 1..8 entries).
- `pilot` means router_train `[0,10000)` and `fit` means `[10000,30000)`. `--query-offset` is relative to that selected interval, while output query IDs and `source_query_range` are absolute within the router_train file. Validation/heldout are separate loader keys. Upstream stage gates remain the outer runner's responsibility.
- Heldout requires P7/P8 plus a P6 gate JSON with `stage=P6,status=PASS,method_frozen=true`. Oracle is rejected on validation and heldout. K>L and legacy m!=3 are rejected before loading data.
- P2 model schema: version 1, dim, 64 regions, active_regions=4, portals_per_region=2, temperature=1.0, fit_range=[10000,30000], labels_file (raw uint16 N), prototypes_file (raw float32 64×dim), portals_file (raw int32 64×2). Relative files resolve against the model JSON directory. Portal IDs must be distinct real nodes in their own region; prototypes must have finite unit norm.

## Online contract

`route_online` and `online_query` do not accept GT pointers. Geometric routing includes raw-query paired Fast top-m HNSW, preservation of its rank-0 anchor, query normalization, 64 scalar-float prototype dot products, softmax at fixed temperature 1, deterministic top-4 selection, portal assembly and explicit seed deduplication. All geometric/oracle ablations use the frozen default entry as a shared seed; paired Fast parity uses the same Fast entries without that extra seed.

The oracle adapter converts GT10 into region masses before any timer, then passes only region IDs/weights to the diagnostic route. It is explicitly excluded from deployment performance claims.

Thread workspaces, normalized query vectors, legacy pool capacity, visited state and output arrays are allocated before `batch`. The batch timer encloses OpenMP execution, real routing, necessary resets, graph search, scheduling, and writes into existing result/route buffers. GT scoring, result/route hashes, trace association, JSON construction and all file I/O occur after `batch` returns. HNSW's own online queue allocations are actual routing costs and remain inside wall timing; they are not claimed to have been removed.

The plain executable path uses ordinary FAISS distance computers and ordinary HNSW IP spaces. The separate count path uses `CountDC` and a counting HNSW space; the new regional kernel's own NDC is checked against `CountDC` before recording it. Routing, graph and total NDC/MAC are exported. MAC denotes one multiply-accumulate per dimension of each measured IP distance; normalization/softmax/scalar scheduling are timed but not included in that dot-product MAC figure.

The default protocol warms 128 queries for every method and L before five recorded rounds. Entire single-method batches run in forward/reverse method order on alternating rounds, with the schedule saved before experiments. At the default 16 threads this warms every active worker. Non-default `warmup < min(threads,nq)` should not be interpreted as full-worker warmup.

Main QPS comes only from the plain single-method batch wall. Count timing is never published as QPS. A separate routing-only wall batch is exported after the main measurements as explanatory evidence; it must not be added to a per-query graph mean to construct total QPS. The separate routing-only batch is one measurement, not a five-round latency confidence interval.

Only round 0 stores aligned per-query IDs/recalls/routes. Later rounds record summaries and matching hashes; an exact repeat hash assertion rejects route/result changes. Timing rounds therefore do not generate independent Recall samples. Every completed batch is also written to a new `<output>.parts/batch_N.json`, followed by an append-only checkpoint. `started.json` and checkpoints remain `INCOMPLETE` until both final output and `complete.json` exist. Interrupted current batches may lack a result; earlier chunks remain available.

`--measurement trace --rounds 1 --max-queries <=32` runs an independent instrumented process and rejects legacy `fast`. It separately replays each selected new-search route, verifies trace result IDs and NDC against the count pass, and writes discover/accept/reject/evict/expand events. GT10 association happens only after trace search returns. Trace JSON is never inside the wall timer.

## Verification already run

| Check | Result | Evidence |
|---|---|---|
| CPU compilation, final evaluator | PASS; 12.1 s; compiler child peak RSS 741,336 KiB | `../control/jobs/p1_evaluator_build_v4.json`, `../logs/p1_evaluator_build_v4.log` |
| Synthetic count/plain parity across seven methods ×40 queries | PASS, 280 comparisons of result IDs/distances and complete route fields | `../logs/p1_evaluator_selftest_v2.log` |
| Same-entry legacy/unified parity | PASS on 40 synthetic queries: IDs, distances, NDC and routes | Same self-test |
| Geometric three-way and oracle two-way route matching | PASS on 40 synthetic queries | Same self-test |
| Fast m=3/4/6/8 actual consumption | PASS on a graph with no edges: graph NDC=m and every reported seed appears in results | Same self-test |
| Required arguments and safety rejection | PASS, 11 checks; no dataset loaded; existing marker unchanged | `evaluator_cli_audit_v2/report.json` |
| Independent source audit | No timer-boundary blocker reported by P1 search agent | Separate P1 search review artifact |

The first build launcher failed because `cmake` was absent from its PATH (`p1_evaluator_build_v1`). It did not run a compiler. Subsequent builds use `/data/netg/ACSG/.venv_cpu/bin/cmake`; the failed launcher record/log is retained. Builds v2/v3 and the earlier self-test/CLI audit remain historical implementation evidence.

Final evaluator source SHA256: `ec770d5921831ac3937ab117b87a1750164f51164b48f3461183192c6d8e2079`.

Final evaluator binary SHA256: `80082b52af916ac1d0b869b711ed18a564641c5dfedaebec6dfe21df9c6fb57e`.

Linked regional header SHA256: `320e29c9407d5907ece7ef64113edeb8b2d5157fa8796aaf94e470eb6771e14e`.

## Remaining P1 acceptance work

The root runner must compare legacy/unified result IDs and NDC on preselected real pilot queries, compare independent count/plain result and route hashes, and inspect actual five-round pure wall output/parts. The real-data model is intentionally unnecessary for this P1 check. Real trace reconstruction and paired P2 comparisons remain later tasks, subject to P0/P1 gates. No real dataset experiment was started by this evaluator subtask.
